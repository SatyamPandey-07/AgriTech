from backend.celery_app import celery_app
from backend.models.circular import WasteInventory, CircularCredit
from backend.services.transformer_logic import TransformerLogic
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='tasks.circular_economy_sync')
def circular_economy_sync():
    """
    Daily task to scan unprocessed waste and trigger energy conversion.
    """
    logger.info("Starting Circular Economy Sync...")
    unprocessed_waste = WasteInventory.query.filter_by(is_processed=False).all()
    
    processed_count = 0
    total_energy = 0.0
    
    for waste in unprocessed_waste:
        try:
            energy = TransformerLogic.process_waste_to_energy(waste.id)
            total_energy += energy
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process waste {waste.id}: {str(e)}")
            
    return {
        'status': 'completed', 
        'items_processed': processed_count,
        'total_energy_kwh': total_energy
    }
