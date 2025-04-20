# Create this new file to centralize API URLs and data collection utilities

import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCollector:
    # Base API URLs
    DEVICES_API_URL = "https://sereneinv.co.zw/minimeter/all-devices-registered/"
    CONSUMPTION_API_BASE_URL = "https://sereneinv.co.zw/minimeter/all-records-per-device"
    TOTAL_CONSUMPTION_API_URL = "https://sereneinv.co.zw/minimeter/total-consumption-summary/"
    
    @staticmethod
    def fetch_devices():
        """Fetch all devices from the API"""
        try:
            response = requests.get(DataCollector.DEVICES_API_URL)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching devices: {str(e)}")
            return []
    
    @staticmethod
    def fetch_device_consumption(device_id):
        """Fetch consumption data for a device"""
        try:
            api_url = f"{DataCollector.CONSUMPTION_API_BASE_URL}/{device_id}"
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching consumption for device {device_id}: {str(e)}")
            return []
    
    @staticmethod
    def fetch_total_consumption(device_ids, start_date, end_date):
        """Fetch total consumption for devices in a date range"""
        try:
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Build the API URL with query parameters
            device_ids_str = ",".join(map(str, device_ids))
            api_url = f"{DataCollector.TOTAL_CONSUMPTION_API_URL}?device_ids={device_ids_str}&start_date={start_date_str}&end_date={end_date_str}"
            
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching total consumption: {str(e)}")
            return []
