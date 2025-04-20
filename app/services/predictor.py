from app.controllers.prediction_controller import PredictionController
from app.models.device import Device
from app.models.prediction import EnergyPrediction, PeakDemandPrediction
from datetime import datetime, timedelta
import joblib
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class Predictor:
    @staticmethod
    def predict_device_energy(device_id, prediction_date=None, prediction_hour=None):
        """Get energy prediction for a specific device, date, and hour"""
        if prediction_date is None:
            prediction_date = datetime.now().date()
        
        # Check if prediction already exists in database
        query = EnergyPrediction.query.filter_by(
            device_id=device_id,
            prediction_date=prediction_date
        )
        
        if prediction_hour is not None:
            query = query.filter_by(prediction_hour=prediction_hour)
        
        existing_predictions = query.all()
        
        if existing_predictions:
            return [pred.to_dict() for pred in existing_predictions]
        
        # If no predictions exist, generate them
        model_path = f'models/energy_model_device_{device_id}.pkl'
        if not os.path.exists(model_path):
            # Train model if it doesn't exist
            logger.info(f"Model for device {device_id} not found, training now")
            PredictionController.train_energy_prediction_model(device_id)
            if not os.path.exists(model_path):
                logger.error(f"Failed to train model for device {device_id}")
                return []
        
        # Generate predictions
        PredictionController.generate_predictions(days_ahead=1)
        
        # Fetch newly generated predictions
        query = EnergyPrediction.query.filter_by(
            device_id=device_id,
            prediction_date=prediction_date
        )
        
        if prediction_hour is not None:
            query = query.filter_by(prediction_hour=prediction_hour)
        
        new_predictions = query.all()
        return [pred.to_dict() for pred in new_predictions]
    
    @staticmethod
    def predict_peak_demand(prediction_date=None, prediction_hour=None):
        """Get peak demand prediction for a specific date and hour"""
        if prediction_date is None:
            prediction_date = datetime.now().date()
        
        # Check if prediction already exists in database
        query = PeakDemandPrediction.query.filter_by(
            prediction_date=prediction_date
        )
        
        if prediction_hour is not None:
            query = query.filter_by(prediction_hour=prediction_hour)
        
        existing_predictions = query.all()
        
        if existing_predictions:
            return [pred.to_dict() for pred in existing_predictions]
        
        # If no predictions exist, generate them
        model_path = 'models/peak_demand_model.pkl'
        if not os.path.exists(model_path):
            # Train model if it doesn't exist
            logger.info("Peak demand model not found, training now")
            PredictionController.train_peak_demand_model()
            if not os.path.exists(model_path):
                logger.error("Failed to train peak demand model")
                return []
        
        # Generate predictions
        PredictionController.generate_predictions(days_ahead=1)
        
        # Fetch newly generated predictions
        query = PeakDemandPrediction.query.filter_by(
            prediction_date=prediction_date
        )
        
        if prediction_hour is not None:
            query = query.filter_by(prediction_hour=prediction_hour)
        
        new_predictions = query.all()
        return [pred.to_dict() for pred in new_predictions]
