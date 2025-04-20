import requests
from app.controllers.device_controller import DeviceController
from app.controllers.consumption_controller import ConsumptionController
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCollector:
    # Base API URLs
    DEVICES_API_URL = "https://sereneinv.co.zw/minimeter/all-devices-registered/"
    CONSUMPTION_API_BASE_URL = "https://sereneinv.co.zw/minimeter/all-records-per-device"
    TOTAL_CONSUMPTION_API_URL = "https://sereneinv.co.zw/minimeter/total-consumption-summary/"
    
    @staticmethod
    def sync_all_devices():
        """Sync all devices from the external API"""
        try:
            logger.info(f"Syncing devices from {DataCollector.DEVICES_API_URL}")
            return DeviceController.sync_devices_from_api(DataCollector.DEVICES_API_URL)
        except Exception as e:
            logger.error(f"Error syncing devices: {str(e)}")
            return False
    
    @staticmethod
    def sync_device_consumption(device_id):
        """Sync consumption data for a specific device"""
        try:
            api_url = f"{DataCollector.CONSUMPTION_API_BASE_URL}/{device_id}"
            logger.info(f"Syncing consumption data for device {device_id} from {api_url}")
            return ConsumptionController.sync_consumption_from_api(api_url, device_id)
        except Exception as e:
            logger.error(f"Error syncing consumption data: {str(e)}")
            return False
    
    @staticmethod
    def sync_all_consumption(device_ids):
        """Sync consumption data for all specified devices"""
        success = True
        for device_id in device_ids:
            if not DataCollector.sync_device_consumption(device_id):
                success = False
        return success
    
    @staticmethod
    def get_total_consumption(device_ids, days=30):
        """Get total consumption for specified devices for the last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Build the API URL with query parameters
            device_ids_str = ",".join(map(str, device_ids))
            api_url = f"{DataCollector.TOTAL_CONSUMPTION_API_URL}?device_ids={device_ids_str}&start_date={start_date_str}&end_date={end_date_str}"
            
            logger.info(f"Getting total consumption from {api_url}")
            
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting total consumption: {str(e)}")
            return []
