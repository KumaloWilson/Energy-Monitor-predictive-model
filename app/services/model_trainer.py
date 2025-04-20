from app.controllers.prediction_controller import PredictionController
from app.models.device import Device
import logging
import requests

logger = logging.getLogger(__name__)

class ModelTrainer:
    # API URL for devices
    DEVICES_API_URL = "https://sereneinv.co.zw/minimeter/all-devices-registered/"
    
    @staticmethod
    def train_all_models():
        """Train prediction models for all devices and peak demand"""
        try:
            # Get devices from API
            response = requests.get(ModelTrainer.DEVICES_API_URL)
            response.raise_for_status()
            devices_data = response.json()
            
            # Train peak demand model
            logger.info("Training peak demand model")
            peak_success = PredictionController.train_peak_demand_model()
            
            # Train device-specific models
            device_success = True
            for device in devices_data:
                device_id = device['id']
                logger.info(f"Training energy prediction model for device {device_id}")
                if not PredictionController.train_energy_prediction_model(device_id):
                    device_success = False
                    logger.warning(f"Failed to train model for device {device_id}")
            
            return peak_success and device_success
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return False
    
    @staticmethod
    def generate_predictions(days_ahead=1):
        """Generate predictions for the specified number of days ahead"""
        try:
            logger.info(f"Generating predictions for {days_ahead} days ahead")
            return PredictionController.generate_predictions(days_ahead)
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return False
