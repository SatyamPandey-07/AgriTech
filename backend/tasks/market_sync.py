from backend.celery_app import celery_app
from backend.models.market import ForwardContract, PriceHedgingLog
from backend.models.farm import Farm
from backend.extensions import db
import random
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='tasks.futures_hedging_sync')
def futures_hedging_sync():
    """
    Background job to scan commodity prices and auto-negotiate 
    forward contracts for harvest-ready farms.
    """
    logger.info("Starting Autonomous Futures Hedging Sync...")
    
    # Only target farms that have high maturity but haven't locked in everything
    farms = Farm.query.filter(Farm.harvest_readiness_index > 0.6).all()
    count = 0
    
    for farm in farms:
        # Dynamic Hedge Ratio (L3 Requirement)
        # Higher weather volatility = Lower hedge ratio (less risk exposure in fixed price)
        # In a real model, this would query a real Weather API history
        weather_volatility = random.uniform(0.2, 0.8) 
        hedge_ratio = 1.0 - weather_volatility 
        
        if hedge_ratio < 0.2: continue # Don't hedge if too volatile
        
        # Simulated Market Price (In real app, fetch from global commodity API)
        market_price_base = 25.0
        current_market_price = market_price_base + random.uniform(-5.0, 5.0)
        
        # Create Forward Contract
        quantity = (farm.predicted_yield_kg or 1000.0) * hedge_ratio
        
        contract = ForwardContract(
            farm_id=farm.id,
            crop_type="Grains",
            quantity_kg=quantity,
            locked_price_per_kg=current_market_price,
            delivery_deadline=farm.predicted_harvest_date,
            hedge_ratio=hedge_ratio,
            volatility_score_at_creation=weather_volatility
        )
        db.session.add(contract)
        
        # Log the AI reasoning
        log = PriceHedgingLog(
            farm_id=farm.id,
            action_taken=f"Locked {quantity:.1f}kg @ {current_market_price:.2f}",
            reasoning=f"Weather Volatility: {weather_volatility:.2f}. Optimized Hedge Ratio to {hedge_ratio:.2f} to balance risk.",
            market_price_snapshot=current_market_price,
            hedge_ratio_applied=hedge_ratio
        )
        db.session.add(log)
        count += 1
        
    db.session.commit()
    return {'status': 'completed', 'contracts_generated': count}
