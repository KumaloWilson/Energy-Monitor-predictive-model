from app.models.prediction import EnergyPrediction, PeakDemandPrediction
from app.models.consumption import ConsumptionRecord
from app.models.device import Device
from app.services.data_collector import DataCollector
from app import db
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
import requests
import logging

logger = logging.getLogger(__name__)

class PredictionController:
    # Define feature names for consistency between training and prediction
    ENERGY_FEATURE_NAMES = ['hour', 'day_of_week', 'month', 'time_on', 'current', 'voltage']
    PEAK_FEATURE_NAMES = ['hour', 'day_of_week', 'month']
    
    @staticmethod
    def get_energy_predictions(device_id=None, prediction_date=None):
        """Get energy predictions with optional filtering"""
        query = EnergyPrediction.query
        
        if device_id:
            query = query.filter_by(device_id=device_id)
        if prediction_date:
            query = query.filter_by(prediction_date=prediction_date)
        
        predictions = query.order_by(EnergyPrediction.prediction_date, 
                                     EnergyPrediction.prediction_hour).all()
        return [prediction.to_dict() for prediction in predictions]
    
    @staticmethod
    def get_peak_demand_predictions(prediction_date=None):
        """Get peak demand predictions with optional date filtering"""
        query = PeakDemandPrediction.query
        
        if prediction_date:
            query = query.filter_by(prediction_date=prediction_date)
        
        predictions = query.order_by(PeakDemandPrediction.prediction_date, 
                                     PeakDemandPrediction.prediction_hour).all()
        return [prediction.to_dict() for prediction in predictions]
    
    @staticmethod
    def fetch_device_consumption_data(device_id):
        """Fetch consumption data for a device directly from the API"""
        try:
            api_url = f"{DataCollector.CONSUMPTION_API_BASE_URL}/{device_id}"
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching consumption data for device {device_id}: {str(e)}")
            return []
    
    @staticmethod
    def train_energy_prediction_model(device_id):
        """Train energy prediction model for a specific device using API data"""
        # Fetch data directly from API
        records_data = PredictionController.fetch_device_consumption_data(device_id)
        
        if len(records_data) < 24:  # Need enough data to train
            logger.warning(f"Not enough data to train model for device {device_id}")
            return False
        
        # Prepare data for training
        data = []
        for record in records_data:
            try:
                timestamp = datetime.fromisoformat(record.get('Reading_Time_Stamp').replace('Z', '+00:00'))
                data.append({
                    'device_id': device_id,
                    'hour': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'month': timestamp.month,
                    'active_energy': float(record.get('ActiveEnergy')),
                    'time_on': float(record.get('TimeOn')),
                    'current': float(record.get('Current')),
                    'voltage': float(record.get('Voltage'))
                })
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"Error processing record: {e}")
                continue
        
        if len(data) < 24:
            logger.warning(f"Not enough valid data points to train model for device {device_id}")
            return False
            
        df = pd.DataFrame(data)
        
        # Feature engineering - use consistent feature names
        X = df[PredictionController.ENERGY_FEATURE_NAMES]
        y = df['active_energy']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(model, f'models/energy_model_device_{device_id}.pkl')
        
        return True
    
    @staticmethod
    def train_peak_demand_model():
        """Train peak demand prediction model using API data"""
        # Get all devices
        try:
            response = requests.get(DataCollector.DEVICES_API_URL)
            response.raise_for_status()
            devices_data = response.json()
            device_ids = [device['id'] for device in devices_data]
        except Exception as e:
            logger.error(f"Error fetching devices: {str(e)}")
            return False
        
        # Prepare data for training
        all_data = []
        
        for device_id in device_ids:
            records_data = PredictionController.fetch_device_consumption_data(device_id)
            
            for record in records_data:
                try:
                    timestamp = datetime.fromisoformat(record.get('Reading_Time_Stamp').replace('Z', '+00:00'))
                    # Calculate power in kW (P = V * I)
                    voltage = float(record.get('Voltage'))
                    current = float(record.get('Current'))
                    power = (voltage * current) / 1000
                    
                    all_data.append({
                        'device_id': device_id,
                        'hour': timestamp.hour,
                        'day_of_week': timestamp.weekday(),
                        'month': timestamp.month,
                        'power': power
                    })
                except (ValueError, TypeError, AttributeError) as e:
                    logger.error(f"Error processing record: {e}")
                    continue
        
        if len(all_data) < 48:  # Need enough data to train
            logger.warning("Not enough data to train peak demand model")
            return False
        
        df = pd.DataFrame(all_data)
        
        # Aggregate by hour to get total power
        df_hourly = df.groupby(['hour', 'day_of_week', 'month'])['power'].sum().reset_index()
        
        # Feature engineering - use consistent feature names
        X = df_hourly[PredictionController.PEAK_FEATURE_NAMES]
        y = df_hourly['power']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(model, 'models/peak_demand_model.pkl')
        
        return True
    
    @staticmethod
    def generate_predictions(days_ahead=1):
        """Generate predictions for the next few days"""
        # Get all devices from API
        try:
            response = requests.get(DataCollector.DEVICES_API_URL)
            response.raise_for_status()
            devices_data = response.json()
        except Exception as e:
            logger.error(f"Error fetching devices: {str(e)}")
            return False
        
        # Generate predictions for each device
        for device_data in devices_data:
            device_id = device_data['id']
            
            # Check if model exists
            model_path = f'models/energy_model_device_{device_id}.pkl'
            if not os.path.exists(model_path):
                # Train model if it doesn't exist
                PredictionController.train_energy_prediction_model(device_id)
                if not os.path.exists(model_path):
                    continue  # Skip if training failed
            
            # Load model
            model = joblib.load(model_path)
            
            # Generate predictions for next few days
            for day in range(days_ahead):
                prediction_date = (datetime.now() + timedelta(days=day)).date()
                
                # Delete existing predictions for this date and device
                EnergyPrediction.query.filter_by(
                    device_id=device_id,
                    prediction_date=prediction_date
                ).delete()
                
                # Generate hourly predictions
                for hour in range(24):
                    # Create feature DataFrame with proper column names
                    features_dict = {
                        'hour': [hour],
                        'day_of_week': [prediction_date.weekday()],
                        'month': [prediction_date.month],
                        'time_on': [120],  # Assume average time_on of 120 minutes
                        'current': [0.5],  # Assume average current of 0.5A
                        'voltage': [220]   # Assume average voltage of 220V
                    }
                    features_df = pd.DataFrame(features_dict)
                    
                    # Make prediction
                    predicted_energy = float(model.predict(features_df)[0])
                    
                    # Save prediction
                    prediction = EnergyPrediction(
                        device_id=device_id,
                        predicted_energy=predicted_energy,
                        prediction_date=prediction_date,
                        prediction_hour=hour
                    )
                    db.session.add(prediction)
        
        # Generate peak demand predictions
        model_path = 'models/peak_demand_model.pkl'
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            
            for day in range(days_ahead):
                prediction_date = (datetime.now() + timedelta(days=day)).date()
                
                # Delete existing predictions for this date
                PeakDemandPrediction.query.filter_by(
                    prediction_date=prediction_date
                ).delete()
                
                # Generate hourly predictions
                for hour in range(24):
                    # Create feature DataFrame with proper column names
                    features_dict = {
                        'hour': [hour],
                        'day_of_week': [prediction_date.weekday()],
                        'month': [prediction_date.month]
                    }
                    features_df = pd.DataFrame(features_dict)
                    
                    # Make prediction
                    predicted_peak = float(model.predict(features_df)[0])
                    
                    # Save prediction
                    prediction = PeakDemandPrediction(
                        predicted_peak_demand=predicted_peak,
                        prediction_date=prediction_date,
                        prediction_hour=hour
                    )
                    db.session.add(prediction)
        
        db.session.commit()
        return True

    @staticmethod
    def get_all_predictions(start_date=None, end_date=None, device_ids=None):
        """Get all predictions (energy and peak demand) for a date range and devices"""
        if start_date is None:
            start_date = datetime.now().date()
        if end_date is None:
            end_date = start_date + timedelta(days=7)  # Default to a week ahead
            
        # Get energy predictions
        energy_query = EnergyPrediction.query.filter(
            EnergyPrediction.prediction_date >= start_date,
            EnergyPrediction.prediction_date <= end_date
        )
        
        if device_ids:
            energy_query = energy_query.filter(EnergyPrediction.device_id.in_(device_ids))
            
        energy_predictions = energy_query.order_by(
            EnergyPrediction.prediction_date,
            EnergyPrediction.prediction_hour,
            EnergyPrediction.device_id
        ).all()
        
        # Get peak demand predictions
        peak_query = PeakDemandPrediction.query.filter(
            PeakDemandPrediction.prediction_date >= start_date,
            PeakDemandPrediction.prediction_date <= end_date
        )
        
        peak_predictions = peak_query.order_by(
            PeakDemandPrediction.prediction_date,
            PeakDemandPrediction.prediction_hour
        ).all()
        
        # Get device information for mapping
        devices = {}
        for device in Device.query.all():
            devices[device.id] = device.to_dict()
        
        # Format data for mobile app
        result = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'devices': devices,
            'energy_predictions': {},
            'peak_demand_predictions': {},
            'daily_summaries': {}
        }
        
        # Process energy predictions
        for pred in energy_predictions:
            date_str = pred.prediction_date.isoformat()
            if date_str not in result['energy_predictions']:
                result['energy_predictions'][date_str] = {}
                
            if pred.device_id not in result['energy_predictions'][date_str]:
                result['energy_predictions'][date_str][pred.device_id] = {}
                
            result['energy_predictions'][date_str][pred.device_id][pred.prediction_hour] = {
                'predicted_energy': pred.predicted_energy,
                'created_at': pred.created_at.isoformat() + 'Z'
            }
        
        # Process peak demand predictions
        for pred in peak_predictions:
            date_str = pred.prediction_date.isoformat()
            if date_str not in result['peak_demand_predictions']:
                result['peak_demand_predictions'][date_str] = {}
                
            result['peak_demand_predictions'][date_str][pred.prediction_hour] = {
                'predicted_peak_demand': pred.predicted_peak_demand,
                'created_at': pred.created_at.isoformat() + 'Z'
            }
        
        # Generate daily summaries
        for date_str in result['energy_predictions']:
            result['daily_summaries'][date_str] = {
                'total_energy': {},
                'peak_demand': 0,
                'peak_hour': 0
            }
            
            # Calculate total energy per device
            for device_id in result['energy_predictions'][date_str]:
                device_total = sum(
                    hour_data['predicted_energy'] 
                    for hour_data in result['energy_predictions'][date_str][device_id].values()
                )
                result['daily_summaries'][date_str]['total_energy'][device_id] = device_total
            
            # Find peak demand hour
            if date_str in result['peak_demand_predictions']:
                peak_hour = max(
                    result['peak_demand_predictions'][date_str].items(),
                    key=lambda x: x[1]['predicted_peak_demand'],
                    default=(0, {'predicted_peak_demand': 0})
                )
                result['daily_summaries'][date_str]['peak_demand'] = peak_hour[1]['predicted_peak_demand']
                result['daily_summaries'][date_str]['peak_hour'] = int(peak_hour[0])
        
        return result
    
    @staticmethod
    def get_device_predictions_summary(device_id, start_date=None, end_date=None):
        """Get a summary of predictions for a specific device"""
        if start_date is None:
            start_date = datetime.now().date()
        if end_date is None:
            end_date = start_date + timedelta(days=7)  # Default to a week ahead
            
        # Get device information
        device = Device.query.get(device_id)
        if not device:
            return None
            
        # Get energy predictions for the device
        energy_predictions = EnergyPrediction.query.filter(
            EnergyPrediction.device_id == device_id,
            EnergyPrediction.prediction_date >= start_date,
            EnergyPrediction.prediction_date <= end_date
        ).order_by(
            EnergyPrediction.prediction_date,
            EnergyPrediction.prediction_hour
        ).all()
        
        # Format data for mobile app
        result = {
            'device': device.to_dict(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_predictions': {},
            'hourly_patterns': {hour: 0 for hour in range(24)},
            'total_predicted_energy': 0
        }
        
        # Process predictions
        for pred in energy_predictions:
            date_str = pred.prediction_date.isoformat()
            if date_str not in result['daily_predictions']:
                result['daily_predictions'][date_str] = {
                    'total': 0,
                    'hourly': {}
                }
                
            result['daily_predictions'][date_str]['hourly'][pred.prediction_hour] = pred.predicted_energy
            result['daily_predictions'][date_str]['total'] += pred.predicted_energy
            result['hourly_patterns'][pred.prediction_hour] += pred.predicted_energy
            result['total_predicted_energy'] += pred.predicted_energy
        
        # Calculate average hourly patterns
        days_count = (end_date - start_date).days + 1
        for hour in result['hourly_patterns']:
            result['hourly_patterns'][hour] /= max(days_count, 1)
        
        return result
    
    @staticmethod
    def get_peak_demand_summary(start_date=None, end_date=None):
        """Get a summary of peak demand predictions"""
        if start_date is None:
            start_date = datetime.now().date()
        if end_date is None:
            end_date = start_date + timedelta(days=7)  # Default to a week ahead
            
        # Get peak demand predictions
        peak_predictions = PeakDemandPrediction.query.filter(
            PeakDemandPrediction.prediction_date >= start_date,
            PeakDemandPrediction.prediction_date <= end_date
        ).order_by(
            PeakDemandPrediction.prediction_date,
            PeakDemandPrediction.prediction_hour
        ).all()
        
        # Format data for mobile app
        result = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_peaks': {},
            'hourly_patterns': {hour: 0 for hour in range(24)},
            'overall_peak': {
                'demand': 0,
                'date': None,
                'hour': None
            }
        }
        
        # Process predictions
        for pred in peak_predictions:
            date_str = pred.prediction_date.isoformat()
            if date_str not in result['daily_peaks']:
                result['daily_peaks'][date_str] = {
                    'peak_demand': 0,
                    'peak_hour': 0,
                    'hourly': {}
                }
                
            result['daily_peaks'][date_str]['hourly'][pred.prediction_hour] = pred.predicted_peak_demand
            result['hourly_patterns'][pred.prediction_hour] += pred.predicted_peak_demand
            
            # Update daily peak
            if pred.predicted_peak_demand > result['daily_peaks'][date_str]['peak_demand']:
                result['daily_peaks'][date_str]['peak_demand'] = pred.predicted_peak_demand
                result['daily_peaks'][date_str]['peak_hour'] = pred.prediction_hour
            
            # Update overall peak
            if pred.predicted_peak_demand > result['overall_peak']['demand']:
                result['overall_peak']['demand'] = pred.predicted_peak_demand
                result['overall_peak']['date'] = date_str
                result['overall_peak']['hour'] = pred.prediction_hour
        
        # Calculate average hourly patterns
        days_count = (end_date - start_date).days + 1
        for hour in result['hourly_patterns']:
            result['hourly_patterns'][hour] /= max(days_count, 1)
        
        return result
