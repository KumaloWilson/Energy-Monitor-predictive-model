from app import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rated_power = db.Column(db.String(50), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with consumption records
    consumption_records = db.relationship('ConsumptionRecord', backref='device', lazy=True)
    
    def __repr__(self):
        return f"<Device {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'Device': self.name,
            'Rated_Power': self.rated_power,
            'DateAdded': self.date_added.isoformat() + 'Z'
        }
