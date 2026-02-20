from datetime import datetime, timedelta
from backend.models.gews import OutbreakZone, MigrationVector, BiosecurityContainment
from backend.models.irrigation import IrrigationZone
from backend.models.traceability import SupplyBatch
from backend.extensions import db
from backend.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class NeutralizationEngine:
    """
    Predicts migration vectors and triggers autonomous bio-security defenses.
    """

    @staticmethod
    def run_outbreak_analysis(zone_id):
        """
        Analyzes an outbreak and triggers defensive multi-module lockdowns.
        """
        zone = OutbreakZone.query.get(zone_id)
        if not zone or zone.status == 'contained': return

        # 1. Predictive Migration Modelling (L3-1562)
        # Correlation with "Wind Patterns" and "Infection Speed"
        vector = MigrationVector(
            outbreak_zone_id=zone.id,
            vector_direction_deg=zone.wind_vector_deg or 180.0,
            estimated_speed_kmh=zone.propagation_velocity or 0.5,
            probability_score=0.92
        )
        db.session.add(vector)

        # 2. Trigger Autonomous Containtment
        NeutralizationEngine._trigger_lockdowns(zone)
        
        db.session.commit()
        return True

    @staticmethod
    def _trigger_lockdowns(zone):
        """
        Executes hardware and logistics shutdowns.
        """
        # A. Irrigation Fertigation Neutralization
        # In a real app, query farms inside the center + radius + vector projection
        # For L3 demonstration, we tag relevant irrigation zones
        affected_zones = IrrigationZone.query.filter(IrrigationZone.name.contains(zone.disease_name)).all()
        for az in affected_zones:
            az.pest_control_mode = True
            az.fertigation_enabled = True
            az.chemical_concentration = 200.0 # Emergency Neutralizer Concentration (ppm)
            az.biosecurity_lockdown = True

        # B. Logistics Shutdown (L3 Requirement: Autonomous Shutdown)
        # Red-Zones stop all batch movements (No Transport Manifests allowed)
        affected_batches = SupplyBatch.query.filter_by(farm_location=zone.zone_id).all()
        for batch in affected_batches:
            # Contact Tracing (Metadata update)
            batch.quarantine_status = 'RED_ZONE_LOCKED'
            batch.status = 'REJECTED' # Immediate halt
            
        # Create containment audit record
        containment = BiosecurityContainment(
            outbreak_zone_id=zone.id,
            blockade_type='BATCH_LOCK_FERTIGATION_ON',
            quarantine_level='CRITICAL'
        )
        db.session.add(containment)

        # Audit Trail
        AuditService.log_event(
            user_id=1, # System process
            action="BIO_SECURITY_CONTAINMENT_TRIGGERED",
            resource_type="OUTBREAK_ZONE",
            resource_id=zone.id,
            details=f"Autonomous shutdown of {len(affected_batches)} batches and {len(affected_zones)} irrigation nodes.",
            risk_level="CRITICAL"
        )
