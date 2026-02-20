from datetime import datetime
from backend.extensions import db

class WasteInventory(db.Model):
    """
    Tracks organic waste generated on the farm (stalks, husks, manure).
    """
    __tablename__ = 'waste_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    
    waste_type = db.Column(db.String(50), nullable=False) # BIO_MASS, MANURE, PLASTIC
    quantity_kg = db.Column(db.Float, default=0.0)
    
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BioEnergyOutput(db.Model):
    """
    Tracks energy generated from processed bio-mass.
    """
    __tablename__ = 'bio_energy_outputs'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    waste_source_id = db.Column(db.Integer, db.ForeignKey('waste_inventory.id'))
    
    energy_kwh = db.Column(db.Float, nullable=False)
    efficiency_score = db.Column(db.Float) # 0-1.0
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CircularCredit(db.Model):
    """
    Monetized credits earned through waste recycling and energy generation.
    """
    __tablename__ = 'circular_credits'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    
    total_earned = db.Column(db.Float, default=0.0)
    available_balance = db.Column(db.Float, default=0.0)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'farm_id': self.farm_id,
            'balance': self.available_balance,
            'total_earned': self.total_earned
        }
