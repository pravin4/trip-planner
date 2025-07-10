#!/usr/bin/env python3
"""
Dynamic Configuration System
Replaces hardcoded values with configurable, dynamic settings.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CostConfig:
    """Dynamic cost configuration."""
    # Gas prices (per gallon) - can be updated from API
    gas_price_per_gallon: float = 3.50
    fuel_efficiency_mpg: float = 25.0
    
    # Toll rates (per 100 km)
    toll_rate_per_100km: float = 5.0
    
    # Parking rates (per hour)
    parking_rate_per_hour: float = 10.0
    
    # Flight cost per km
    flight_cost_per_km: float = 0.15
    
    # Train cost per km
    train_cost_per_km: float = 0.08
    
    # Bus cost per km
    bus_cost_per_km: float = 0.05

@dataclass
class DistanceConfig:
    """Dynamic distance thresholds."""
    # Distance thresholds for travel mode selection (km)
    short_distance_threshold: float = 100.0
    medium_distance_threshold: float = 800.0
    long_distance_threshold: float = 1200.0
    
    # Stop intervals (hours)
    attraction_stop_interval: float = 2.5
    rest_stop_interval: float = 4.0
    
    # Waypoint generation threshold (km)
    waypoint_threshold: float = 200.0

@dataclass
class APIConfig:
    """API configuration and rate limits."""
    # Google Places API
    google_places_radius: int = 5000  # meters
    google_places_max_results: int = 5
    
    # Geocoding fallback
    geocoding_timeout: int = 10  # seconds
    geocoding_retries: int = 3
    
    # Cost API endpoints (for real-time pricing)
    gas_price_api_url: str = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    toll_api_url: str = "https://api.tollguru.com/v1/calc/route/"
    
    # Weather API for route planning
    weather_api_url: str = "https://api.openweathermap.org/data/2.5/weather"

@dataclass
class DynamicConfig:
    """Main dynamic configuration."""
    costs: CostConfig = None
    distances: DistanceConfig = None
    api: APIConfig = None
    
    def __post_init__(self):
        if self.costs is None:
            self.costs = CostConfig()
        if self.distances is None:
            self.distances = DistanceConfig()
        if self.api is None:
            self.api = APIConfig()

class DynamicConfigManager:
    """Manages dynamic configuration and real-time updates."""
    
    def __init__(self, config_file: str = "config/dynamic_settings.json"):
        self.config_file = config_file
        self.config = DynamicConfig()
        self.load_config()
        
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                    # Reconstruct dataclass objects from JSON data
                    costs_data = data.get("costs", {})
                    distances_data = data.get("distances", {})
                    api_data = data.get("api", {})
                    
                    self.config = DynamicConfig(
                        costs=CostConfig(**costs_data),
                        distances=DistanceConfig(**distances_data),
                        api=APIConfig(**api_data)
                    )
                    
                logger.info(f"Loaded dynamic config from {self.config_file}")
            else:
                self.save_config()  # Create default config
                logger.info(f"Created default dynamic config at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Fallback to default config
            self.config = DynamicConfig()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            logger.info(f"Saved dynamic config to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def update_gas_price(self, new_price: float):
        """Update gas price from real-time API."""
        self.config.costs.gas_price_per_gallon = new_price
        self.save_config()
        logger.info(f"Updated gas price to ${new_price}/gallon")
    
    def update_distance_thresholds(self, short: float = None, medium: float = None, long: float = None):
        """Update distance thresholds."""
        if short is not None:
            self.config.distances.short_distance_threshold = short
        if medium is not None:
            self.config.distances.medium_distance_threshold = medium
        if long is not None:
            self.config.distances.long_distance_threshold = long
        self.save_config()
        logger.info("Updated distance thresholds")
    
    def get_cost_config(self) -> CostConfig:
        """Get current cost configuration."""
        return self.config.costs
    
    def get_distance_config(self) -> DistanceConfig:
        """Get current distance configuration."""
        return self.config.distances
    
    def get_api_config(self) -> APIConfig:
        """Get current API configuration."""
        return self.config.api
    
    def calculate_dynamic_gas_cost(self, distance_km: float) -> float:
        """Calculate gas cost using current prices."""
        distance_miles = distance_km * 0.621371
        gallons_needed = distance_miles / self.config.costs.fuel_efficiency_mpg
        return gallons_needed * self.config.costs.gas_price_per_gallon
    
    def calculate_dynamic_toll_cost(self, distance_km: float) -> float:
        """Calculate toll cost using current rates."""
        return (distance_km / 100) * self.config.costs.toll_rate_per_100km
    
    def calculate_dynamic_parking_cost(self, duration_hours: float) -> float:
        """Calculate parking cost using current rates."""
        return duration_hours * self.config.costs.parking_rate_per_hour
    
    def should_add_waypoints(self, distance_km: float) -> bool:
        """Determine if waypoints should be added based on distance."""
        return distance_km > self.config.distances.waypoint_threshold
    
    def get_stop_interval(self, stop_type: str = "attraction") -> float:
        """Get stop interval based on type."""
        if stop_type == "rest":
            return self.config.distances.rest_stop_interval
        return self.config.distances.attraction_stop_interval

# Global config manager instance
config_manager = DynamicConfigManager() 