from backend.models.circular import WasteInventory, BioEnergyOutput, CircularCredit
from backend.models.sustainability import SustainabilityScore
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)

class TransformerLogic:
    """
    Calculates efficiency of waste-to-energy transformation and 
    awards circular credits.
    """

    @staticmethod
    def process_waste_to_energy(waste_id):
        """
        Converts organic biomass to energy kwh and awards credits.
        """
        waste = WasteInventory.query.get(waste_id)
        if not waste or waste.is_processed: return 0.0

        # Transformation Logic (Calculated Efficiency)
        # 1kg BIO_MASS approx 0.5 kWh
        # 1kg MANURE approx 0.8 kWh (Biogas potential)
        rates = {'BIO_MASS': 0.5, 'MANURE': 0.8}
        yield_rate = rates.get(waste.waste_type, 0.1)
        
        energy_generated = waste.quantity_kg * yield_rate
        efficiency = 0.85 # Constant for simulated reactor performance

        output = BioEnergyOutput(
            farm_id=waste.farm_id,
            waste_source_id=waste.id,
            energy_kwh=energy_generated,
            efficiency_score=efficiency
        )
        db.session.add(output)
        
        waste.is_processed = True
        
        # Award Circular Credits: 1 kWh = 2 Credits
        credits_to_award = energy_generated * 2.0
        TransformerLogic.update_circular_ledger(waste.farm_id, credits_to_award)
        
        db.session.commit()
        return energy_generated

    @staticmethod
    def update_circular_ledger(farm_id, amount):
        """
        Aggregates credits and handles Recursive Nutrient Recovery bonuses.
        """
        ledger = CircularCredit.query.filter_by(farm_id=farm_id).first()
        if not ledger:
            ledger = CircularCredit(farm_id=farm_id)
            db.session.add(ledger)
        
        ledger.total_earned += amount
        ledger.available_balance += amount
        
        # Recursive Nutrient Recovery (L3-1561)
        # Reusing transformation byproducts (slurry) locally increases sustainability.
        score = SustainabilityScore.query.filter_by(farm_id=farm_id).first()
        if score:
            # Bonus: 0.1 increase in overall sustainability for circular activity
            score.biodiversity_index = min(100.0, (score.biodiversity_index or 50.0) + 0.5)
            # This implicitly reduces Scope 3 if tracked
            
    @staticmethod
    def use_credits(farm_id, amount):
        """Deduct credits for purchases or barter."""
        ledger = CircularCredit.query.filter_by(farm_id=farm_id).first()
        if ledger and ledger.available_balance >= amount:
            ledger.available_balance -= amount
            db.session.commit()
            return True
        return False
