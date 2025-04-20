from app.models.device import Device
from app import db
from datetime import datetime
import requests
import json
import logging

logger = logging.getLogger(__name__)

class DeviceController:
    @staticmethod
    def get_all_devices():
        """Get all registered devices"""
        devices = Device.query.all()
        return [device.to_dict() for device in devices]
    
    @staticmethod
    def get_device_by_id(device_id):
        """Get a device by ID"""
        device = Device.query.get(device_id)
        if device:
            return device.to_dict()
        return None
    
    @staticmethod
    def create_device(name, rated_power):
        """Create a new device"""
        device = Device(
            name=name,
            rated_power=rated_power,
            date_added=datetime.utcnow()
        )
        db.session.add(device)
        db.session.commit()
        return device.to_dict()
    
    @staticmethod
    def update_device(device_id, name=None, rated_power=None):
        """Update a device"""
        device = Device.query.get(device_id)
        if not device:
            return None
        
        if name:
            device.name = name
        if rated_power:
            device.rated_power = rated_power
        
        db.session.commit()
        return device.to_dict()
    
    @staticmethod
    def delete_device(device_id):
        """Delete a device"""
        device = Device.query.get(device_id)
        if not device:
            return False
        
        db.session.delete(device)
        db.session.commit()
        return True
    
    @staticmethod
    def sync_devices_from_api(api_url):
        """Sync devices from external API"""
        try:
            logger.info(f"Fetching devices from {api_url}")
            response = requests.get(api_url)
            response.raise_for_status()
            devices_data = response.json()
            
            for device_data in devices_data:
                existing_device = Device.query.get(device_data.get('id'))
                
                if existing_device:
                    # Update existing device
                    existing_device.name = device_data.get('Device')
                    existing_device.rated_power = device_data.get('Rated_Power')
                    # Parse date if needed
                    if 'DateAdded' in device_data:
                        existing_device.date_added = datetime.fromisoformat(device_data.get('DateAdded').replace('Z', '+00:00'))
                else:
                    # Create new device
                    new_device = Device(
                        id=device_data.get('id'),
                        name=device_data.get('Device'),
                        rated_power=device_data.get('Rated_Power')
                    )
                    # Parse date if needed
                    if 'DateAdded' in device_data:
                        new_device.date_added = datetime.fromisoformat(device_data.get('DateAdded').replace('Z', '+00:00'))
                    
                    db.session.add(new_device)
            
            db.session.commit()
            logger.info(f"Successfully synced {len(devices_data)} devices")
            return True
        except Exception as e:
            logger.error(f"Error syncing devices: {str(e)}")
            return False
