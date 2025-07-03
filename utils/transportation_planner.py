"""
Transportation Planning Module
Handles inter-city travel, realistic travel times, and transportation mode selection.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from utils.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)

@dataclass
class TransportationLeg:
    """Represents a transportation leg between two locations"""
    from_location: str
    to_location: str
    distance_km: float
    duration_minutes: int
    mode: str
    cost_per_person: float
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    notes: str = ""

@dataclass
class TravelDay:
    """Represents a travel day with transportation legs"""
    date: str
    legs: List[TransportationLeg]
    total_travel_time: int
    total_cost: float
    is_travel_only: bool = False

class TransportationPlanner:
    """Comprehensive transportation planning system using real geocoding and APIs"""
    
    # Average speeds in km/h for different modes (realistic estimates)
    SPEEDS = {
        "walking": 5,
        "bicycle": 15,
        "car": 60,  # Highway speed
        "car_urban": 30,  # Urban driving
        "bus": 40,
        "train": 120,
        "plane": 800,
        "ferry": 30
    }
    
    # Cost per km for different modes (market-based estimates)
    COSTS_PER_KM = {
        "walking": 0,
        "bicycle": 0,
        "car": 0.15,  # Gas + maintenance
        "car_urban": 0.20,
        "bus": 0.05,
        "train": 0.10,
        "plane": 0.50,  # Base fare per km
        "ferry": 0.30
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.geocoding_service = GeocodingService()
    
    def plan_inter_city_travel(self, destinations: List[str], start_date: str, 
                              end_date: str, preferences: Dict[str, Any]) -> List[TravelDay]:
        """
        Plan transportation between multiple cities using real geocoding.
        
        Args:
            destinations: List of destination cities
            start_date: Trip start date
            end_date: Trip end date
            preferences: User preferences including budget_level, group_size
            
        Returns:
            List of TravelDay objects with transportation plans
        """
        if len(destinations) <= 1:
            return []
        
        travel_days = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate days needed for travel
        total_days = (end_date_obj - current_date).days + 1
        travel_days_needed = len(destinations) - 1
        
        # Distribute travel days across the trip
        travel_day_indices = self._distribute_travel_days(total_days, travel_days_needed)
        
        for i, (from_city, to_city) in enumerate(zip(destinations[:-1], destinations[1:])):
            if i < len(travel_day_indices):
                travel_day_index = travel_day_indices[i]
                travel_date = current_date + timedelta(days=travel_day_index)
                
                # Plan transportation between these cities using real geocoding
                legs = self._plan_city_to_city_travel(
                    from_city, to_city, preferences
                )
                
                if legs:
                    total_travel_time = sum(leg.duration_minutes for leg in legs)
                    total_cost = sum(leg.cost_per_person for leg in legs) * preferences.get("group_size", 2)
                    
                    travel_day = TravelDay(
                        date=travel_date.strftime("%Y-%m-%d"),
                        legs=legs,
                        total_travel_time=total_travel_time,
                        total_cost=total_cost,
                        is_travel_only=total_travel_time > 240  # More than 4 hours = travel only day
                    )
                    travel_days.append(travel_day)
        
        return travel_days
    
    def _distribute_travel_days(self, total_days: int, travel_days_needed: int) -> List[int]:
        """Distribute travel days across the trip duration."""
        if travel_days_needed == 0:
            return []
        
        # Simple distribution: spread travel days evenly
        if travel_days_needed == 1:
            return [total_days // 2]  # Middle of trip
        
        # For multiple travel days, distribute them
        step = total_days // (travel_days_needed + 1)
        return [step * (i + 1) for i in range(travel_days_needed)]
    
    def _plan_city_to_city_travel(self, from_city: str, to_city: str, 
                                 preferences: Dict[str, Any]) -> List[TransportationLeg]:
        """Plan transportation between two cities using real geocoding."""
        
        # Get real coordinates using geocoding service
        from_coords = self.geocoding_service.get_coordinates(from_city)
        to_coords = self.geocoding_service.get_coordinates(to_city)
        
        if not from_coords or not to_coords:
            self.logger.warning(f"Could not get coordinates for {from_city} or {to_city}")
            return []
        
        # Calculate distance using real coordinates
        distance = self._calculate_distance(from_coords, to_coords)
        
        # Get real travel time and distance from Google Maps API if available
        travel_info = self.geocoding_service.get_travel_time(from_city, to_city, 'driving')
        
        if travel_info:
            # Use real travel data
            distance = travel_info['distance_km']
            duration_minutes = travel_info['duration_minutes']
        else:
            # Fallback to calculated distance and estimated duration
            duration_minutes = int(self._calculate_travel_duration(distance, "car") * 60)
        
        # Determine transportation mode based on distance and preferences
        mode = self._select_transportation_mode(distance, preferences)
        
        # Calculate cost
        cost_per_person = self._calculate_travel_cost(distance, mode, preferences)
        
        # Create transportation leg
        leg = TransportationLeg(
            from_location=from_city.title(),
            to_location=to_city.title(),
            distance_km=distance,
            duration_minutes=duration_minutes,
            mode=mode,
            cost_per_person=cost_per_person,
            notes=self._generate_travel_notes(distance, mode, from_city, to_city)
        )
        
        return [leg]
    
    def _calculate_distance(self, from_coords: Tuple[float, float], 
                          to_coords: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        lat1, lon1 = from_coords
        lat2, lon2 = to_coords
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    def _select_transportation_mode(self, distance: float, 
                                  preferences: Dict[str, Any]) -> str:
        """Select the best transportation mode based on distance and preferences."""
        budget_level = preferences.get("budget_level", "moderate")
        
        # For short distances (< 100 km), prefer car
        if distance < 100:
            return "car"
        
        # For medium distances (100-500 km), consider budget
        elif distance < 500:
            if budget_level == "budget":
                return "bus"
            elif budget_level == "luxury":
                return "plane"
            else:
                return "car"  # Default to car for moderate budget
        
        # For long distances (> 500 km), prefer plane
        else:
            return "plane"
    
    def _calculate_travel_duration(self, distance: float, mode: str) -> float:
        """Calculate travel duration in hours."""
        speed = self.SPEEDS.get(mode, 60)  # Default 60 km/h
        return distance / speed
    
    def _calculate_travel_cost(self, distance: float, mode: str, 
                             preferences: Dict[str, Any]) -> float:
        """Calculate travel cost per person."""
        base_cost = distance * self.COSTS_PER_KM.get(mode, 0.15)
        
        # Adjust for budget level
        budget_level = preferences.get("budget_level", "moderate")
        if budget_level == "budget":
            base_cost *= 0.8  # 20% discount for budget
        elif budget_level == "luxury":
            base_cost *= 1.5  # 50% premium for luxury
        
        return base_cost
    
    def _generate_travel_notes(self, distance: float, mode: str, 
                             from_city: str, to_city: str) -> str:
        """Generate travel notes based on mode and distance."""
        if mode == "car":
            return f"Drive from {from_city} to {to_city} ({distance:.0f}km). Consider traffic and rest stops."
        elif mode == "plane":
            return f"Fly from {from_city} to nearest airport, then drive to {to_city}."
        elif mode == "train":
            return f"Take train from {from_city} to {to_city}."
        elif mode == "bus":
            return f"Take bus from {from_city} to {to_city}."
        else:
            return f"Travel from {from_city} to {to_city}."
    
    def plan_local_transportation(self, activities: List[Dict[str, Any]], 
                                cluster_name: str) -> List[TransportationLeg]:
        """Plan local transportation between activities in a cluster."""
        legs = []
        
        if len(activities) < 2:
            return legs
        
        # Sort activities by time if available
        sorted_activities = sorted(activities, key=lambda x: x.get('time_slot', ''))
        
        for i in range(len(sorted_activities) - 1):
            current_activity = sorted_activities[i]
            next_activity = sorted_activities[i + 1]
            
            # Get coordinates for both activities
            current_coords = self.geocoding_service.get_coordinates(
                f"{current_activity.get('name', '')}, {cluster_name}"
            )
            next_coords = self.geocoding_service.get_coordinates(
                f"{next_activity.get('name', '')}, {cluster_name}"
            )
            
            if current_coords and next_coords:
                distance = self._calculate_distance(current_coords, next_coords)
                
                # For local travel, use walking or short taxi rides
                if distance < 2:  # Less than 2km
                    mode = "walking"
                    duration_minutes = int(distance * 12)  # 12 min per km walking
                    cost_per_person = 0
                else:
                    mode = "car_urban"
                    duration_minutes = int(distance * 2)  # 2 min per km in urban traffic
                    cost_per_person = distance * self.COSTS_PER_KM["car_urban"]
                
                leg = TransportationLeg(
                    from_location=current_activity.get('name', ''),
                    to_location=next_activity.get('name', ''),
                    distance_km=distance,
                    duration_minutes=duration_minutes,
                    mode=mode,
                    cost_per_person=cost_per_person,
                    notes=f"{mode.title()} from {current_activity.get('name', '')} to {next_activity.get('name', '')}"
                )
                legs.append(leg)
        
        return legs
    
    def adjust_day_plans_for_travel(self, day_plans: List[Dict[str, Any]], 
                                  travel_days: List[TravelDay]) -> List[Dict[str, Any]]:
        """Adjust day plans to account for travel days."""
        # This method can be expanded to handle travel day adjustments
        # For now, return the original day plans
        return day_plans 