from flask import Blueprint, jsonify, request
from backend.models.gews import OutbreakZone, MigrationVector, BiosecurityContainment
from backend.auth_utils import token_required
from backend.extensions import db

biosecurity_bp = Blueprint('biosecurity', __name__)

@biosecurity_bp.route('/threat-monitor', methods=['GET'])
@token_required
def get_threat_monitor(current_user):
    """
    Returns real-time geospatial threat intelligence map.
    """
    active_zones = OutbreakZone.query.filter(OutbreakZone.status != 'contained').all()
    
    # Include predicted vectors for the next 24 hours
    vectors = MigrationVector.query.order_by(MigrationVector.timestamp.desc()).limit(10).all()
    
    return jsonify({
        'status': 'success',
        'outbreaks': [z.to_geojson_feature() for z in active_zones],
        'migration_vectors': [{
            'zone_id': v.outbreak_zone_id,
            'direction': v.vector_direction_deg,
            'speed_kmh': v.estimated_speed_kmh,
            'confidence': v.probability_score
        } for v in vectors]
    })

@biosecurity_bp.route('/containment-status', methods=['GET'])
@token_required
def get_containment_status(current_user):
    """
    View currently locked irrigation nodes and quarantined batches.
    """
    active_containments = BiosecurityContainment.query.filter_by(is_active=True).all()
    
    return jsonify({
        'status': 'success',
        'containments': [c.to_dict() for c in active_containments]
    })

@biosecurity_bp.route('/emergency-override', methods=['POST'])
@token_required
def emergency_override(current_user):
    """Allows admin to lift autonomous lockdowns."""
    # Logic to deactivate BiosecurityContainment and unlock batches
    pass
