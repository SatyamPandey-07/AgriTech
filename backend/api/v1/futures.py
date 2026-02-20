from flask import Blueprint, jsonify, request
from backend.models.market import ForwardContract, PriceHedgingLog
from backend.models.farm import Farm
from backend.auth_utils import token_required
from backend.extensions import db

futures_bp = Blueprint('futures', __name__)

@futures_bp.route('/dashboard/<int:farm_id>', methods=['GET'])
@token_required
def get_futures_dashboard(current_user, farm_id):
    """
    Returns harvest velocity analytics and hedging history for a farm.
    """
    farm = Farm.query.get(farm_id)
    if not farm:
        return jsonify({'error': 'Farm not found'}), 404
        
    contracts = ForwardContract.query.filter_by(farm_id=farm_id).all()
    logs = PriceHedgingLog.query.filter_by(farm_id=farm_id).order_by(PriceHedgingLog.timestamp.desc()).limit(10).all()
    
    return jsonify({
        'status': 'success',
        'metrics': {
            'harvest_readiness': farm.harvest_readiness_index,
            'predicted_yield': farm.predicted_yield_kg,
            'predicted_date': farm.predicted_harvest_date.isoformat() if farm.predicted_harvest_date else None
        },
        'active_contracts': [c.to_dict() for c in contracts],
        'hedging_logs': [{
            'id': l.id,
            'action': l.action_taken,
            'reasoning': l.reasoning,
            'price': l.market_price_snapshot,
            'timestamp': l.timestamp.isoformat()
        } for l in logs]
    })

@futures_bp.route('/contracts/<int:contract_id>/match', methods=['POST'])
@token_required
def match_contract(current_user, contract_id):
    """Allows a buyer to match a forward contract."""
    contract = ForwardContract.query.get(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
        
    if contract.contract_status != 'PENDING':
        return jsonify({'error': 'Contract already matched or expired'}), 400
        
    contract.buyer_id = current_user.id
    contract.contract_status = 'MATCHED'
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Contract {contract_id} matched by buyer {current_user.id}'
    })
