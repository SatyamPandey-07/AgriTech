from datetime import datetime, timedelta
from backend.models.farm import Farm
from backend.models.weather import WeatherData
from backend.models.soil_health import SoilTest
from backend.extensions import db
import logging

logger = logging.getLogger(__name__)

class VelocityEngine:
    """
    Predicts harvest windows and maturity using Growing Degree Days (GDD)
    and soil moisture telemetry.
    """

    @staticmethod
    def calculate_harvest_velocity(farm_id):
        """
        Updates the harvest_readiness_index based on current environmental data.
        """
        farm = Farm.query.get(farm_id)
        if not farm: return 0.0

        # 1. Fetch telemetry
        latest_weather = WeatherData.query.filter_by(location=farm.location).order_by(WeatherData.timestamp.desc()).first()
        
        # 2. Maturity Calculation (GDD Simulation)
        # Each day adds to the maturity index based on temperature
        base_temp = 10.0 # Standard base for many crops
        current_temp = latest_weather.temperature if latest_weather else 20.0
        
        # Incremental growth per calculation cycle
        growth_step = max(0, current_temp - base_temp) / 1000.0 # Simulated normalization
        
        farm.harvest_readiness_index = min(1.0, farm.harvest_readiness_index + growth_step)
        
        # 3. Predict harvest date if enough data
        if growth_step > 0:
            days_to_maturity = (1.0 - farm.harvest_readiness_index) / (growth_step * 24) # Assuming 24 updates/day
            farm.predicted_harvest_date = datetime.utcnow() + timedelta(days=days_to_maturity)
        
        db.session.commit()
        return farm.harvest_readiness_index

    @staticmethod
    def run_fleet_prediction():
        """Aggregated run for all farms."""
        farms = Farm.query.all()
        for f in farms:
            VelocityEngine.calculate_harvest_velocity(f.id)
