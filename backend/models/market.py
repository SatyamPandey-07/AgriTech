from datetime import datetime
from backend.extensions import db

class ForwardContract(db.Model):
    """
    Agreements to sell future harvest at a locked-in price.
    """
    __tablename__ = 'forward_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id')) # Optional until matched
    
    crop_type = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    locked_price_per_kg = db.Column(db.Float, nullable=False)
    
    delivery_deadline = db.Column(db.DateTime, nullable=False)
    contract_status = db.Column(db.String(50), default='PENDING') # PENDING, MATCHED, SETTLED, EXPIRED
    
    # Financial Hedge Info
    hedge_ratio = db.Column(db.Float, default=0.5) # Ratio of total yield protected
    volatility_score_at_creation = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'crop_type': self.crop_type,
            'quantity': self.quantity_kg,
            'price': self.locked_price_per_kg,
            'deadline': self.delivery_deadline.isoformat(),
            'status': self.contract_status,
            'hedge_ratio': self.hedge_ratio
        }

class PriceHedgingLog(db.Model):
    """
    Audit trail for autonomous hedging decisions.
    """
    __tablename__ = 'price_hedging_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    
    action_taken = db.Column(db.String(100)) # e.g., "Auto-Locked 500kg Wheat Future"
    reasoning = db.Column(db.Text) # AI reasoning string
    
    market_price_snapshot = db.Column(db.Float)
    hedge_ratio_applied = db.Column(db.Float)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
