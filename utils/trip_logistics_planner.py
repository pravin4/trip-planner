"""
Trip Logistics Planner
Handles departure/arrival planning, overall trip logistics, and routing from starting point.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)

@dataclass
class TripLeg:
    """Represents a trip leg with departure and arrival details"""
    from_location: str
    to_location: str
    departure_time: str
    arrival_time: str
    duration_hours: float
    distance_km: float
    mode: str
    cost_per_person: float
    notes: str = ""

@dataclass
class TripLogistics:
    """Complete trip logistics including departure and arrival"""
    departure_leg: Optional[TripLeg] = None
    return_leg: Optional[TripLeg] = None
    total_travel_time: float = 0.0
    total_travel_cost: float = 0.0
    travel_days: List[str] = None
    starting_point: str = ""
    destination: str = ""

class TripLogisticsPlanner:
    """Handles complete trip logistics from departure to return"""
    
    # Common starting points and their coordinates
    STARTING_POINTS = {
        "san jose": (37.3382, -121.8863),
        "san francisco": (37.7749, -122.4194),
        "los angeles": (34.0522, -118.2437),
        "new york": (40.7128, -74.0060),
        "chicago": (41.8781, -87.6298),
        "miami": (25.7617, -80.1918),
        "seattle": (47.6062, -122.3321),
        "boston": (42.3601, -71.0589),
        "washington dc": (38.9072, -77.0369),
        "denver": (39.7392, -104.9903),
        "austin": (30.2672, -97.7431),
        "portland": (45.5152, -122.6784),
        "san diego": (32.7157, -117.1611),
        "phoenix": (33.4484, -112.0740),
        "dallas": (32.7767, -96.7970),
        "houston": (29.7604, -95.3698),
        "atlanta": (33.7490, -84.3880)
    }
    
    # Additional destination coordinates
    DESTINATION_COORDS = {
        "shelter cove": (40.0304, -124.0731),
        "big sur": (36.2704, -121.8081),
        "solvang": (34.5958, -120.1376),
        "napa": (38.2975, -122.2869),
        "yosemite": (37.8651, -119.5383),
        "lake tahoe": (39.0968, -120.0324),
        "monterey": (36.6002, -121.8947),
        "santa barbara": (34.4208, -119.6982),
        "palm springs": (33.8303, -116.5453),
        "carmel": (36.5552, -121.9233),
        "santa cruz": (36.9741, -122.0308),
        "half moon bay": (37.4636, -122.4286),
        "pacific grove": (36.6177, -121.9166),
        "cambria": (35.5641, -121.0807),
        "san luis obispo": (35.2828, -120.6596),
        "pismo beach": (35.1428, -120.6413),
        "avila beach": (35.1800, -120.7319),
        "morro bay": (35.3658, -120.8499),
        "cayucos": (35.4428, -120.8921),
        "cambria": (35.5641, -121.0807),
        "san simeon": (35.6444, -121.1891),
        "gorda": (35.9094, -121.4655),
        "lucia": (36.0166, -121.5497),
        "partington cove": (36.1197, -121.6419),
        "garrapata state park": (36.4669, -121.9297),
        "point lobos": (36.5166, -121.9422),
        "17-mile drive": (36.5697, -121.9497),
        "pebble beach": (36.5697, -121.9497),
        "carmel-by-the-sea": (36.5552, -121.9233),
        "point sur": (36.3083, -121.8994),
        "bixby bridge": (36.3723, -121.9019),
        "mcfway falls": (36.2704, -121.8081),
        "pfeiffer beach": (36.2405, -121.7777),
        "julia pfeiffer burns state park": (36.1697, -121.6708),
        "andrew molera state park": (36.2858, -121.8472),
        "point sur lighthouse": (36.3083, -121.8994),
        "garrapata beach": (36.4669, -121.9297),
        "rocky point": (36.5697, -121.9497),
        "bird rock": (36.5697, -121.9497),
        "cypress point": (36.5697, -121.9497),
        "china rock": (36.5697, -121.9497),
        "ghost trees": (36.5697, -121.9497),
        "pacific grove": (36.6177, -121.9166),
        "asilomar state beach": (36.6177, -121.9166),
        "lovers point": (36.6177, -121.9166),
        "point piños": (36.6333, -121.9333),
        "monterey bay aquarium": (36.6183, -121.9016),
        "cannery row": (36.6183, -121.9016),
        "fisherman's wharf": (36.6183, -121.9016),
        "old fisherman's wharf": (36.6183, -121.9016),
        "presidio of monterey": (36.6183, -121.9016),
        "monterey state beach": (36.6183, -121.9016),
        "del monte beach": (36.6183, -121.9016),
        "san carlos beach": (36.6183, -121.9016),
        "coast guard pier": (36.6183, -121.9016),
        "breakwater cove": (36.6183, -121.9016),
        "lovers point park": (36.6177, -121.9166),
        "asilomar conference grounds": (36.6177, -121.9166),
        "asilomar beach": (36.6177, -121.9166),
        "asilomar dunes": (36.6177, -121.9166),
        "asilomar tide pools": (36.6177, -121.9166),
        "asilomar coastal trail": (36.6177, -121.9166),
        "asilomar state beach": (36.6177, -121.9166),
        "asilomar conference grounds": (36.6177, -121.9166),
        "asilomar beach": (36.6177, -121.9166),
        "asilomar dunes": (36.6177, -121.9166),
        "asilomar tide pools": (36.6177, -121.9166),
        "asilomar coastal trail": (36.6177, -121.9166)
    }
    
    # Transportation modes and their characteristics
    TRANSPORT_MODES = {
        "car": {
            "speed_kmh": 80,
            "cost_per_km": 0.15,
            "max_distance": 800,  # km
            "prep_time_hours": 0.5
        },
        "plane": {
            "speed_kmh": 800,
            "cost_per_km": 0.50,
            "max_distance": 5000,
            "prep_time_hours": 2.0
        },
        "train": {
            "speed_kmh": 120,
            "cost_per_km": 0.10,
            "max_distance": 1000,
            "prep_time_hours": 1.0
        },
        "bus": {
            "speed_kmh": 70,
            "cost_per_km": 0.05,
            "max_distance": 500,
            "prep_time_hours": 0.5
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def plan_complete_trip(self, starting_point: str, destination: str, 
                          start_date: str, end_date: str, 
                          preferences: Dict[str, Any]) -> TripLogistics:
        """
        Plan complete trip logistics from departure to return.
        
        Args:
            starting_point: Starting location (e.g., "San Jose")
            destination: Destination location (e.g., "Big Sur, Solvang")
            start_date: Trip start date
            end_date: Trip end date
            preferences: User preferences
            
        Returns:
            TripLogistics object with complete trip plan
        """
        try:
            # Extract main destination from multi-destination string
            main_destination = self._extract_main_destination(destination)
            
            # Plan departure leg
            departure_leg = self._plan_departure_leg(
                starting_point, main_destination, start_date, preferences
            )
            
            # Plan return leg
            return_leg = self._plan_return_leg(
                main_destination, starting_point, end_date, preferences
            )
            
            # Calculate totals
            total_travel_time = 0.0
            total_travel_cost = 0.0
            
            if departure_leg:
                total_travel_time += departure_leg.duration_hours
                total_travel_cost += departure_leg.cost_per_person
            
            if return_leg:
                total_travel_time += return_leg.duration_hours
                total_travel_cost += return_leg.cost_per_person
            
            # Multiply by group size
            group_size = preferences.get("group_size", 1)
            total_travel_cost *= group_size
            
            # Determine travel days
            travel_days = []
            if departure_leg:
                travel_days.append(start_date)
            if return_leg:
                travel_days.append(end_date)
            
            return TripLogistics(
                departure_leg=departure_leg,
                return_leg=return_leg,
                total_travel_time=total_travel_time,
                total_travel_cost=total_travel_cost,
                travel_days=travel_days,
                starting_point=starting_point,
                destination=destination
            )
            
        except Exception as e:
            self.logger.error(f"Error planning complete trip: {e}")
            return TripLogistics()
    
    def _extract_main_destination(self, destination: str) -> str:
        """Extract the main destination from a multi-destination string."""
        # Handle cases like "Big Sur, Solvang" or "San Francisco, CA"
        if "," in destination:
            # Take the first part as main destination
            return destination.split(",")[0].strip()
        return destination
    
    def _plan_departure_leg(self, starting_point: str, destination: str, 
                           start_date: str, preferences: Dict[str, Any]) -> Optional[TripLeg]:
        """Plan the departure leg from starting point to destination."""
        
        # Get coordinates
        start_coords = self._get_coordinates(starting_point)
        dest_coords = self._get_coordinates(destination)
        
        if not start_coords or not dest_coords:
            return None
        
        # Calculate distance
        distance = self._calculate_distance(start_coords, dest_coords)
        
        # Select transportation mode
        mode = self._select_transportation_mode(distance, preferences)
        
        # Calculate duration and cost
        duration_hours = self._calculate_duration(distance, mode)
        cost_per_person = self._calculate_cost(distance, mode, preferences)
        
        # Set departure and arrival times
        departure_time = "09:00"  # Default morning departure
        arrival_time = self._calculate_arrival_time(departure_time, duration_hours)
        
        # Generate notes
        notes = self._generate_departure_notes(starting_point, destination, mode, distance)
        
        return TripLeg(
            from_location=starting_point,
            to_location=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_hours=duration_hours,
            distance_km=distance,
            mode=mode,
            cost_per_person=cost_per_person,
            notes=notes
        )
    
    def _plan_return_leg(self, destination: str, starting_point: str, 
                        end_date: str, preferences: Dict[str, Any]) -> Optional[TripLeg]:
        """Plan the return leg from destination to starting point."""
        
        # Get coordinates
        dest_coords = self._get_coordinates(destination)
        start_coords = self._get_coordinates(starting_point)
        
        if not dest_coords or not start_coords:
            return None
        
        # Calculate distance
        distance = self._calculate_distance(dest_coords, start_coords)
        
        # Select transportation mode
        mode = self._select_transportation_mode(distance, preferences)
        
        # Calculate duration and cost
        duration_hours = self._calculate_duration(distance, mode)
        cost_per_person = self._calculate_cost(distance, mode, preferences)
        
        # Set departure and arrival times (afternoon return)
        departure_time = "15:00"  # Default afternoon departure
        arrival_time = self._calculate_arrival_time(departure_time, duration_hours)
        
        # Generate notes
        notes = self._generate_return_notes(destination, starting_point, mode, distance)
        
        return TripLeg(
            from_location=destination,
            to_location=starting_point,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_hours=duration_hours,
            distance_km=distance,
            mode=mode,
            cost_per_person=cost_per_person,
            notes=notes
        )
    
    def _get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a location."""
        location_lower = location.lower()
        
        # Check starting points first
        if location_lower in self.STARTING_POINTS:
            return self.STARTING_POINTS[location_lower]
        
        # Check destination coordinates
        if location_lower in self.DESTINATION_COORDS:
            return self.DESTINATION_COORDS[location_lower]
        
        # Check partial matches in starting points
        for known_location, coords in self.STARTING_POINTS.items():
            if location_lower in known_location or known_location in location_lower:
                return coords
        
        # Check partial matches in destination coordinates
        for known_location, coords in self.DESTINATION_COORDS.items():
            if location_lower in known_location or known_location in location_lower:
                return coords
        
        # For unknown locations, try to use a geocoding service
        try:
            from utils.geocoding_service import GeocodingService
            geocoding = GeocodingService()
            coords = geocoding.get_coordinates(location)
            if coords:
                return coords
        except Exception as e:
            self.logger.warning(f"Could not geocode {location}: {e}")
        
        # Default to San Francisco if unknown
        self.logger.warning(f"Unknown location: {location}, using San Francisco as fallback")
        return (37.7749, -122.4194)
    
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
    
    def _select_transportation_mode(self, distance: float, preferences: Dict[str, Any]) -> str:
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
    
    def _calculate_duration(self, distance: float, mode: str) -> float:
        """Calculate travel duration in hours."""
        if mode not in self.TRANSPORT_MODES:
            return distance / 60  # Default 60 km/h
        
        mode_info = self.TRANSPORT_MODES[mode]
        travel_time = distance / mode_info["speed_kmh"]
        prep_time = mode_info["prep_time_hours"]
        
        return travel_time + prep_time
    
    def _calculate_cost(self, distance: float, mode: str, preferences: Dict[str, Any]) -> float:
        """Calculate travel cost per person."""
        if mode not in self.TRANSPORT_MODES:
            return distance * 0.15  # Default cost
        
        mode_info = self.TRANSPORT_MODES[mode]
        base_cost = distance * mode_info["cost_per_km"]
        
        # Adjust for budget level
        budget_level = preferences.get("budget_level", "moderate")
        if budget_level == "budget":
            base_cost *= 0.8  # 20% discount for budget
        elif budget_level == "luxury":
            base_cost *= 1.5  # 50% premium for luxury
        
        return base_cost
    
    def _calculate_arrival_time(self, departure_time: str, duration_hours: float) -> str:
        """Calculate arrival time based on departure time and duration."""
        try:
            departure = datetime.strptime(departure_time, "%H:%M")
            arrival = departure + timedelta(hours=duration_hours)
            return arrival.strftime("%H:%M")
        except:
            return "18:00"  # Default arrival time
    
    def _generate_departure_notes(self, starting_point: str, destination: str, 
                                mode: str, distance: float) -> str:
        """Generate departure notes."""
        if mode == "car":
            return f"Drive from {starting_point} to {destination} ({distance:.0f}km). Consider traffic and rest stops."
        elif mode == "plane":
            return f"Fly from {starting_point} to nearest airport, then drive to {destination}."
        elif mode == "train":
            return f"Take train from {starting_point} to {destination}."
        elif mode == "bus":
            return f"Take bus from {starting_point} to {destination}."
        else:
            return f"Travel from {starting_point} to {destination}."
    
    def _generate_return_notes(self, destination: str, starting_point: str, 
                             mode: str, distance: float) -> str:
        """Generate return notes."""
        if mode == "car":
            return f"Return drive from {destination} to {starting_point} ({distance:.0f}km)."
        elif mode == "plane":
            return f"Drive to nearest airport, then fly back to {starting_point}."
        elif mode == "train":
            return f"Take train from {destination} back to {starting_point}."
        elif mode == "bus":
            return f"Take bus from {destination} back to {starting_point}."
        else:
            return f"Return travel from {destination} to {starting_point}."
    
    def get_trip_summary(self, logistics: TripLogistics) -> Dict[str, Any]:
        """Generate a summary of the trip logistics."""
        summary = {
            "starting_point": logistics.starting_point,
            "destination": logistics.destination,
            "total_travel_time_hours": logistics.total_travel_time,
            "total_travel_cost": logistics.total_travel_cost,
            "travel_days": logistics.travel_days,
            "departure_info": None,
            "return_info": None
        }
        
        if logistics.departure_leg:
            summary["departure_info"] = {
                "from": logistics.departure_leg.from_location,
                "to": logistics.departure_leg.to_location,
                "departure_time": logistics.departure_leg.departure_time,
                "arrival_time": logistics.departure_leg.arrival_time,
                "duration_hours": logistics.departure_leg.duration_hours,
                "mode": logistics.departure_leg.mode,
                "cost_per_person": logistics.departure_leg.cost_per_person,
                "notes": logistics.departure_leg.notes
            }
        
        if logistics.return_leg:
            summary["return_info"] = {
                "from": logistics.return_leg.from_location,
                "to": logistics.return_leg.to_location,
                "departure_time": logistics.return_leg.departure_time,
                "arrival_time": logistics.return_leg.arrival_time,
                "duration_hours": logistics.return_leg.duration_hours,
                "mode": logistics.return_leg.mode,
                "cost_per_person": logistics.return_leg.cost_per_person,
                "notes": logistics.return_leg.notes
            }
        
        return summary
    
    def optimize_multi_destination_route(self, starting_point: str, destinations: List[str], 
                                       preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize route for multiple destinations to minimize backtracking.
        
        Args:
            starting_point: Starting location
            destinations: List of destinations to visit
            preferences: User preferences
            
        Returns:
            Optimized route with logical flow
        """
        try:
            if not destinations:
                return {"route": [starting_point], "total_distance": 0}
            
            # Get coordinates for all locations
            locations = [starting_point] + destinations
            coordinates = {}
            
            for location in locations:
                coords = self._get_coordinates(location)
                if coords:
                    coordinates[location] = coords
                else:
                    # Use default coordinates if not found
                    coordinates[location] = (0, 0)
            
            # Calculate distances between all locations
            distance_matrix = {}
            for loc1 in locations:
                distance_matrix[loc1] = {}
                for loc2 in locations:
                    if loc1 != loc2:
                        dist = self._calculate_distance(coordinates[loc1], coordinates[loc2])
                        distance_matrix[loc1][loc2] = dist
                    else:
                        distance_matrix[loc1][loc2] = 0
            
            # Simple greedy algorithm to find optimal route
            # Start from starting point, always go to nearest unvisited destination
            unvisited = destinations.copy()
            current = starting_point
            route = [starting_point]
            total_distance = 0
            
            while unvisited:
                # Find nearest unvisited destination
                nearest = None
                min_distance = float('inf')
                
                for dest in unvisited:
                    distance = distance_matrix[current][dest]
                    if distance < min_distance:
                        min_distance = distance
                        nearest = dest
                
                if nearest:
                    route.append(nearest)
                    total_distance += min_distance
                    current = nearest
                    unvisited.remove(nearest)
                else:
                    break
            
            # Add return to starting point
            if route[-1] != starting_point:
                return_distance = distance_matrix[route[-1]][starting_point]
                total_distance += return_distance
                route.append(starting_point)
            
            # Create route segments
            route_segments = []
            for i in range(len(route) - 1):
                from_loc = route[i]
                to_loc = route[i + 1]
                distance = distance_matrix[from_loc][to_loc]
                
                segment = {
                    "from": from_loc,
                    "to": to_loc,
                    "distance_km": distance,
                    "mode": self._select_transportation_mode(distance, preferences),
                    "duration_hours": self._calculate_duration(distance, 
                        self._select_transportation_mode(distance, preferences)),
                    "cost_per_person": self._calculate_cost(distance, 
                        self._select_transportation_mode(distance, preferences), preferences)
                }
                route_segments.append(segment)
            
            return {
                "route": route,
                "route_segments": route_segments,
                "total_distance": total_distance,
                "total_cost": sum(seg["cost_per_person"] for seg in route_segments),
                "total_duration": sum(seg["duration_hours"] for seg in route_segments),
                "optimization_notes": self._generate_route_optimization_notes(route, total_distance)
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing route: {e}")
            return {"route": [starting_point] + destinations, "total_distance": 0}
    
    def _generate_route_optimization_notes(self, route: List[str], total_distance: float) -> str:
        """Generate notes about the optimized route."""
        if len(route) <= 3:
            return "Direct route with minimal backtracking."
        
        # Analyze the route for efficiency
        notes = []
        
        # Check for backtracking
        if len(route) > 3:
            notes.append("Multi-destination route optimized to minimize travel time.")
        
        if total_distance > 500:
            notes.append("Long-distance trip - consider breaking into multiple trips.")
        elif total_distance > 200:
            notes.append("Moderate distance - plan for rest stops and fuel.")
        else:
            notes.append("Short to moderate distance - efficient route planned.")
        
        return " ".join(notes) 