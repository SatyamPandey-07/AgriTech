from backend.celery_app import celery_app
from backend.models.traceability import SupplyBatch, CustodyLog
from backend.models.gews import OutbreakZone
from backend.services.neutralization_engine import NeutralizationEngine
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='tasks.quarantine_red_zone_scan')
def quarantine_red_zone_scan():
    """
    Periodic job to verify contact tracing for all batches.
    Auto-locks any batch that passed through a high-risk migration vector.
    """
    logger.info("Starting Biosecurity Quarantine Scan...")
    
    # Analyze all active outbreaks
    outbreaks = OutbreakZone.query.filter(OutbreakZone.status != 'contained').all()
    for o in outbreaks:
        NeutralizationEngine.run_outbreak_analysis(o.id)
        
    # Second Pass: Contact Tracing (L3 Requirement)
    # Check custody logs for batches that intersecting quarantined locations
    red_zones = [o.zone_id for o in outbreaks]
    if red_zones:
        # Batches that were recently in a red zone but not yet locked
        at_risk_batches = SupplyBatch.query.join(CustodyLog).filter(
            CustodyLog.location.in_(red_zones),
            SupplyBatch.quarantine_status.is_(None)
        ).all()
        
        for b in at_risk_batches:
            b.quarantine_status = 'TRACE_LOCK'
            b.status = 'QUALITY_CHECK' # Force re-inspection
            
        db.session.commit()
        return {'status': 'processed', 'locked_via_tracing': len(at_risk_batches)}
    
    return {'status': 'no_active_threats'}
