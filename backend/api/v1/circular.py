from flask import Blueprint, jsonify, request
from backend.models.circular import WasteInventory, CircularCredit, BioEnergyOutput
from backend.auth_utils import token_required
from backend.extensions import db

circular_bp = Blueprint('circular', __name__)

@circular_bp.route('/dashboard/<int:farm_id>', methods=['GET'])
@token_required
def get_circular_dashboard(current_user, farm_id):
    """
    Returns waste stats, energy output, and credit balance for a farm.
    """
    credit = CircularCredit.query.filter_by(farm_id=farm_id).first()
    outputs = BioEnergyOutput.query.filter_by(farm_id=farm_id).order_by(BioEnergyOutput.timestamp.desc()).limit(15).all()
    inventory = WasteInventory.query.filter_by(farm_id=farm_id, is_processed=False).all()
    
    return jsonify({
        'status': 'success',
        'credit_balance': credit.to_dict() if credit else {'balance': 0, 'total_earned': 0},
        'pending_waste_kg': sum(w.quantity_kg for w in inventory),
        'recent_energy_output_kwh': [{
            'id': o.id,
            'kwh': o.energy_kwh,
            'timestamp': o.timestamp.isoformat()
        } for o in outputs]
    })

@circular_bp.route('/report-waste', methods=['POST'])
@token_required
def report_waste(current_user):
    """Manually log a new batch of farm waste."""
    data = request.json
    try:
        waste = WasteInventory(
            farm_id=data['farm_id'],
            waste_type=data.get('type', 'BIO_MASS'),
            quantity_kg=data['quantity']
        )
        db.session.add(waste)
        db.session.commit()
        return jsonify({'status': 'success', 'waste_id': waste.id}), 201
    except KeyError:
        return jsonify({'error': 'Missing farm_id or quantity'}), 400

@circular_bp.route('/spend-credits', methods=['POST'])
@token_required
def spend_credits(current_user):
    """Hook to spend circular credits on platform resources."""
    from backend.services.transformer_logic import TransformerLogic
    data = request.json
    success = TransformerLogic.use_credits(data['farm_id'], data['amount'])
    
    if success:
        return jsonify({'status': 'success', 'message': f'Spent {data["amount"]} circular credits'})
    return jsonify({'error': 'Insufficient balance or farm not found'}), 400
