from app import db
from datetime import datetime

class EnergyPrediction(db.Model):
    __tablename__ = 'energy_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    predicted_energy = db.Column(db.Float, nullable=False)  # in kWh
    prediction_date = db.Column(db.Date, nullable=False)
    prediction_hour = db.Column(db.Integer, nullable=False)  # 0-23
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with device
    device = db.relationship('Device', backref='predictions')
    
    def __repr__(self):
        return f"<EnergyPrediction for device {self.device_id} on {self.prediction_date} hour {self.prediction_hour}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else None,
            'predicted_energy': self.predicted_energy,
            'prediction_date': self.prediction_date.isoformat(),
            'prediction_hour': self.prediction_hour,
            'created_at': self.created_at.isoformat() + 'Z'
        }

class PeakDemandPrediction(db.Model):
    __tablename__ = 'peak_demand_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    predicted_peak_demand = db.Column(db.Float, nullable=False)  # in kW
    prediction_date = db.Column(db.Date, nullable=False)
    prediction_hour = db.Column(db.Integer, nullable=False)  # 0-23
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PeakDemandPrediction on {self.prediction_date} hour {self.prediction_hour}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'predicted_peak_demand': self.predicted_peak_demand,
            'prediction_date': self.prediction_date.isoformat(),
            'prediction_hour': self.prediction_hour,
            'created_at': self.created_at.isoformat() + 'Z'
        }
