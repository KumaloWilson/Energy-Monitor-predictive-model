from app.models.consumption import ConsumptionRecord
from app.models.device import Device
from app import db
from datetime import datetime, timedelta
import requests
import json

class ConsumptionController:
    @staticmethod
    def get_device_consumption(device_id, start_date=None, end_date=None):
        """Get consumption records for a specific device with optional date filtering"""
        query = ConsumptionRecord.query.filter_by(device_id=device_id)
        
        if start_date:
            query = query.filter(ConsumptionRecord.reading_timestamp >= start_date)
        if end_date:
            query = query.filter(ConsumptionRecord.reading_timestamp <= end_date)
        
        records = query.order_by(ConsumptionRecord.reading_timestamp).all()
        return [record.to_dict() for record in records]
    
    @staticmethod
    def get_total_consumption(device_ids=None, start_date=None, end_date=None):
        """Get total consumption for specified devices within a date range"""
        query = db.session.query(
            ConsumptionRecord.device_id,
            db.func.sum(ConsumptionRecord.active_energy).label('total_energy')
        )
        
        if device_ids:
            query = query.filter(ConsumptionRecord.device_id.in_(device_ids))
        if start_date:
            query = query.filter(ConsumptionRecord.reading_timestamp >= start_date)
        if end_date:
            query = query.filter(ConsumptionRecord.reading_timestamp <= end_date)
        
        results = query.group_by(ConsumptionRecord.device_id).all()
        
        return [
            {
                'Appliance_Info_id': device_id,
                'total_energy': float(total_energy)
            }
            for device_id, total_energy in results
        ]
    
    @staticmethod
    def add_consumption_record(device_id, voltage, current, time_on, active_energy, reading_timestamp):
        """Add a new consumption record"""
        record = ConsumptionRecord(
            device_id=device_id,
            voltage=voltage,
            current=current,
            time_on=time_on,
            active_energy=active_energy,
            reading_timestamp=reading_timestamp
        )
        db.session.add(record)
        db.session.commit()
        return record.to_dict()
    
    @staticmethod
    def sync_consumption_from_api(api_url, device_id):
        """Sync consumption records for a device from external API"""
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            records_data = response.json()
            
            for record_data in records_data:
                # Check if record already exists
                existing_record = ConsumptionRecord.query.get(record_data.get('id'))
                
                if not existing_record:
                    # Create new record
                    new_record = ConsumptionRecord(
                        id=record_data.get('id'),
                        device_id=device_id,
                        voltage=float(record_data.get('Voltage')),
                        current=float(record_data.get('Current')),
                        time_on=float(record_data.get('TimeOn')),
                        active_energy=float(record_data.get('ActiveEnergy')),
                        reading_timestamp=datetime.fromisoformat(record_data.get('Reading_Time_Stamp').replace('Z', '+00:00'))
                    )
                    db.session.add(new_record)
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error syncing consumption data: {str(e)}")
            return False
