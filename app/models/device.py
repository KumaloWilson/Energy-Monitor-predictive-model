from app import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    meter_number = db.Column(db.String(50), nullable=True)
    rated_power = db.Column(db.String(50), nullable=False)
    relay_status = db.Column(db.String(10), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with consumption records
    consumption_records = db.relationship('ConsumptionRecord', backref='device', lazy=True)
    
    def __repr__(self):
        return f"<Device {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'Device': self.name,
            'MeterNumber': self.meter_number,
            'Rated_Power': self.rated_power,
            'Relay_Status': self.relay_status,
            'DateAdded': self.date_added.isoformat() + 'Z'
        }
