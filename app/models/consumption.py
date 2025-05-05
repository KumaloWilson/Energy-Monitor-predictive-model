from app import db
from datetime import datetime

class ConsumptionRecord(db.Model):
    __tablename__ = 'consumption_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    voltage = db.Column(db.Float, nullable=False)
    current = db.Column(db.Float, nullable=False)
    time_on = db.Column(db.Float, nullable=False)  # in minutes
    active_energy = db.Column(db.Float, nullable=False)  # in kWh
    reading_timestamp = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"<ConsumptionRecord {self.id} for device {self.device_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'Appliance_Info': self.device_id,
            'Voltage': f"{self.voltage:.1f}",
            'Current': f"{self.current:.2f}",
            'TimeOn': f"{self.time_on:.2f}",
            'ActiveEnergy': f"{self.active_energy:.4f}",
            'Reading_Time_Stamp': self.reading_timestamp.isoformat() + 'Z'
        }
