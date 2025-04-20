from apscheduler.schedulers.background import BackgroundScheduler
from app.services.data_collector import DataCollector
from app.services.model_trainer import ModelTrainer
from app.models.device import Device
from app import create_app, db
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_scheduler(app):
    """Set up the background scheduler for automated tasks"""
    scheduler = BackgroundScheduler()
    
    # Add jobs with app context
    with app.app_context():
        # Sync devices every day at 1:00 AM
        scheduler.add_job(
            sync_devices_job,
            'cron',
            hour=1,
            minute=0,
            args=[app]
        )
        
        # Sync consumption data every hour
        scheduler.add_job(
            sync_consumption_job,
            'cron',
            minute=5,
            args=[app]
        )
        
        # Train models once a day at 2:00 AM
        scheduler.add_job(
            train_models_job,
            'cron',
            hour=2,
            minute=0,
            args=[app]
        )
        
        # Generate predictions every 6 hours
        scheduler.add_job(
            generate_predictions_job,
            'cron',
            hour='*/6',
            minute=30,
            args=[app]
        )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler

def sync_devices_job(app):
    """Job to sync devices from external API"""
    with app.app_context():
        logger.info("Running device sync job")
        DataCollector.sync_all_devices()

def sync_consumption_job(app):
    """Job to sync consumption data from external API"""
    with app.app_context():
        logger.info("Running consumption sync job")
        try:
            # Get device IDs from the API
            response = requests.get(DataCollector.DEVICES_API_URL)
            response.raise_for_status()
            devices_data = response.json()
            device_ids = [device['id'] for device in devices_data]
            
            # Sync consumption data for each device
            DataCollector.sync_all_consumption(device_ids)
        except Exception as e:
            logger.error(f"Error in consumption sync job: {str(e)}")

def train_models_job(app):
    """Job to train prediction models"""
    with app.app_context():
        logger.info("Running model training job")
        ModelTrainer.train_all_models()

def generate_predictions_job(app):
    """Job to generate predictions"""
    with app.app_context():
        logger.info("Running prediction generation job")
        ModelTrainer.generate_predictions(days_ahead=2)
