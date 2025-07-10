#!/usr/bin/env python3
"""
Dynamic Route Planner
Uses real APIs to find stops, attractions, and route information dynamically.
"""

import os
import sys
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.dynamic_config import config_manager
from utils.geocoding_service import GeocodingService
from api_integrations.google_places import GooglePlacesAPI

logger = logging.getLogger(__name__)

class DynamicRoutePlanner:
    """Dynamic route planner using real APIs and data."""
    
    def __init__(self):
        """Initialize the dynamic route planner."""
        self.geocoding = GeocodingService()
        self.google_places = GooglePlacesAPI()
        self.config = config_manager
        
    def find_dynamic_stops(self, origin: str, destination: str, 
                          route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Find dynamic stops along a route using real APIs."""
        try:
            stops = []
            
            # Get route information
            route_info = self._get_route_info(origin, destination)
            if not route_info:
                return stops
            
            # Find major cities along the route
            major_cities = self._find_major_cities_along_route(route_coords)
            
            # Find attractions near major cities
            for city in major_cities:
                attractions = self._find_attractions_near_city(city)
                if attractions:
                    stops.append({
                        "location": city["location"],
                        "name": city["name"],
                        "type": "city_attraction",
                        "attractions": attractions,
                        "stop_duration": 2.0,  # 2 hours for city exploration
                        "description": f"Explore {city['name']} and nearby attractions"
                    })
            
            # Find rest stops and services
            rest_stops = self._find_rest_stops_along_route(route_coords)
            stops.extend(rest_stops)
            
            # Find scenic viewpoints
            scenic_stops = self._find_scenic_viewpoints(route_coords)
            stops.extend(scenic_stops)
            
            # Find local restaurants and food stops
            food_stops = self._find_food_stops_along_route(route_coords)
            stops.extend(food_stops)
            
            # Sort stops by distance from origin
            stops = self._sort_stops_by_distance(origin, stops)
            
            # Add timing information
            stops = self._add_timing_to_stops(stops, route_info)
            
            logger.info(f"Found {len(stops)} dynamic stops along route")
            return stops
            
        except Exception as e:
            logger.error(f"Error finding dynamic stops: {e}")
            return []
    
    def _get_route_info(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        """Get route information using Google Maps API."""
        try:
            origin_coords = self.geocoding.get_coordinates(origin)
            dest_coords = self.geocoding.get_coordinates(destination)
            
            if not origin_coords or not dest_coords:
                return None
            
            # Use Google Maps Directions API
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": f"{origin_coords[0]},{origin_coords[1]}",
                "destination": f"{dest_coords[0]},{dest_coords[1]}",
                "key": os.getenv("GOOGLE_MAPS_API_KEY"),
                "alternatives": "true",
                "avoid": "tolls|highways"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "OK" and data["routes"]:
                    route = data["routes"][0]  # Use first route
                    return {
                        "distance": route["legs"][0]["distance"]["value"] / 1000,  # km
                        "duration": route["legs"][0]["duration"]["value"] / 3600,  # hours
                        "steps": route["legs"][0]["steps"],
                        "waypoints": self._extract_waypoints(route["legs"][0]["steps"])
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting route info: {e}")
            return None
    
    def _extract_waypoints(self, steps: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """Extract waypoints from route steps."""
        waypoints = []
        for step in steps:
            start_location = step["start_location"]
            waypoints.append((start_location["lat"], start_location["lng"]))
        
        # Add end location
        if steps:
            end_location = steps[-1]["end_location"]
            waypoints.append((end_location["lat"], end_location["lng"]))
        
        return waypoints
    
    def _find_major_cities_along_route(self, route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Find major cities along the route."""
        cities = []
        
        # Sample points along the route (every 50km)
        sample_distance = 50  # km
        total_distance = self._calculate_route_distance(route_coords)
        
        for i in range(0, len(route_coords) - 1, max(1, len(route_coords) // 10)):
            lat, lng = route_coords[i]
            
            # Find nearby cities using reverse geocoding
            city_info = self._find_nearby_city(lat, lng)
            if city_info and city_info["population"] > 10000:  # Only major cities
                cities.append(city_info)
        
        return cities
    
    def _find_nearby_city(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """Find nearby city using reverse geocoding."""
        try:
            # Use Google Geocoding API for reverse geocoding
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lng}",
                "key": os.getenv("GOOGLE_MAPS_API_KEY"),
                "result_type": "locality"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    return {
                        "name": result["formatted_address"],
                        "location": {"lat": lat, "lng": lng},
                        "population": self._estimate_city_population(result["formatted_address"])
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding nearby city: {e}")
            return None
    
    def _estimate_city_population(self, city_name: str) -> int:
        """Estimate city population (simplified - in production, use real population API)."""
        # This is a simplified estimation - in production, use a real population API
        population_estimates = {
            "san francisco": 873965,
            "oakland": 440646,
            "san jose": 1030119,
            "sacramento": 513624,
            "fresno": 542107,
            "stockton": 320804,
            "bakersfield": 403455,
            "modesto": 218464,
            "fremont": 230504,
            "santa rosa": 178127
        }
        
        city_lower = city_name.lower()
        for key, pop in population_estimates.items():
            if key in city_lower:
                return pop
        
        return 50000  # Default estimate
    
    def _find_attractions_near_city(self, city: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find attractions near a city using Google Places API."""
        try:
            lat = city["location"]["lat"]
            lng = city["location"]["lng"]
            
            # Search for tourist attractions
            attractions = self.google_places.search_nearby(
                lat, lng, 
                radius=self.config.get_api_config().google_places_radius,
                type="tourist_attraction"
            )
            
            # Also search for museums, parks, etc.
            museums = self.google_places.search_nearby(
                lat, lng, 
                radius=self.config.get_api_config().google_places_radius,
                type="museum"
            )
            
            parks = self.google_places.search_nearby(
                lat, lng, 
                radius=self.config.get_api_config().google_places_radius,
                type="park"
            )
            
            # Combine and limit results
            all_attractions = attractions + museums + parks
            return all_attractions[:self.config.get_api_config().google_places_max_results]
            
        except Exception as e:
            logger.error(f"Error finding attractions near {city['name']}: {e}")
            return []
    
    def _find_rest_stops_along_route(self, route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Find rest stops and services along the route."""
        rest_stops = []
        
        # Find stops every 4 hours of driving
        stop_interval = self.config.get_stop_interval("rest")
        
        for i in range(0, len(route_coords), max(1, len(route_coords) // 8)):
            lat, lng = route_coords[i]
            
            # Find gas stations, rest areas, etc.
            services = self._find_services_near_point(lat, lng)
            if services:
                rest_stops.append({
                    "location": {"lat": lat, "lng": lng},
                    "name": f"Rest Stop {len(rest_stops) + 1}",
                    "type": "rest_stop",
                    "services": services,
                    "stop_duration": 0.5,  # 30 minutes
                    "description": "Rest stop with gas, food, and facilities"
                })
        
        return rest_stops
    
    def _find_services_near_point(self, lat: float, lng: float) -> List[Dict[str, Any]]:
        """Find services (gas stations, restaurants) near a point."""
        try:
            services = []
            
            # Find gas stations
            gas_stations = self.google_places.search_nearby(
                lat, lng, radius=5000, type="gas_station"
            )
            services.extend(gas_stations[:3])
            
            # Find restaurants
            restaurants = self.google_places.search_nearby(
                lat, lng, radius=5000, type="restaurant"
            )
            services.extend(restaurants[:3])
            
            return services
            
        except Exception as e:
            logger.error(f"Error finding services: {e}")
            return []
    
    def _find_scenic_viewpoints(self, route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Find scenic viewpoints along the route."""
        scenic_stops = []
        
        # Look for scenic areas every 100km
        for i in range(0, len(route_coords), max(1, len(route_coords) // 5)):
            lat, lng = route_coords[i]
            
            # Search for scenic viewpoints
            viewpoints = self.google_places.search_nearby(
                lat, lng, radius=10000, type="tourist_attraction"
            )
            
            # Filter for scenic locations
            scenic_locations = [v for v in viewpoints if self._is_scenic_location(v)]
            
            if scenic_locations:
                scenic_stops.append({
                    "location": {"lat": lat, "lng": lng},
                    "name": f"Scenic Viewpoint {len(scenic_stops) + 1}",
                    "type": "scenic",
                    "attractions": scenic_locations[:2],
                    "stop_duration": 1.0,  # 1 hour for photos and views
                    "description": "Scenic viewpoint for photos and sightseeing"
                })
        
        return scenic_stops
    
    def _is_scenic_location(self, place: Dict[str, Any]) -> bool:
        """Check if a place is likely to be scenic."""
        scenic_keywords = [
            "view", "overlook", "vista", "point", "summit", "peak", "ridge",
            "beach", "coast", "cliff", "canyon", "valley", "lake", "river",
            "park", "forest", "trail", "scenic", "panorama"
        ]
        
        name = place.get("name", "").lower()
        types = place.get("types", [])
        
        # Check name for scenic keywords
        for keyword in scenic_keywords:
            if keyword in name:
                return True
        
        # Check types
        scenic_types = ["natural_feature", "park", "tourist_attraction"]
        for scenic_type in scenic_types:
            if scenic_type in types:
                return True
        
        return False
    
    def _find_food_stops_along_route(self, route_coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Find local food stops along the route."""
        food_stops = []
        
        # Find food stops every 3 hours
        for i in range(0, len(route_coords), max(1, len(route_coords) // 6)):
            lat, lng = route_coords[i]
            
            # Find local restaurants
            restaurants = self.google_places.search_nearby(
                lat, lng, radius=5000, type="restaurant"
            )
            
            # Filter for highly-rated restaurants
            good_restaurants = [r for r in restaurants if r.get("rating", 0) >= 4.0]
            
            if good_restaurants:
                food_stops.append({
                    "location": {"lat": lat, "lng": lng},
                    "name": f"Food Stop {len(food_stops) + 1}",
                    "type": "food",
                    "restaurants": good_restaurants[:3],
                    "stop_duration": 1.5,  # 1.5 hours for meal
                    "description": "Local dining options"
                })
        
        return food_stops
    
    def _sort_stops_by_distance(self, origin: str, stops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort stops by distance from origin."""
        try:
            origin_coords = self.geocoding.get_coordinates(origin)
            if not origin_coords:
                return stops
            
            for stop in stops:
                stop_lat = stop["location"]["lat"]
                stop_lng = stop["location"]["lng"]
                distance = self._calculate_distance(origin_coords, (stop_lat, stop_lng))
                stop["distance_from_origin"] = distance
            
            return sorted(stops, key=lambda x: x.get("distance_from_origin", 0))
            
        except Exception as e:
            logger.error(f"Error sorting stops: {e}")
            return stops
    
    def _add_timing_to_stops(self, stops: List[Dict[str, Any]], route_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add timing information to stops."""
        try:
            total_duration = route_info.get("duration", 0)
            current_time = 0
            
            for stop in stops:
                stop["estimated_time"] = current_time
                current_time += stop.get("stop_duration", 1.0)
            
            return stops
            
        except Exception as e:
            logger.error(f"Error adding timing to stops: {e}")
            return stops
    
    def _calculate_route_distance(self, route_coords: List[Tuple[float, float]]) -> float:
        """Calculate total route distance."""
        total_distance = 0
        for i in range(len(route_coords) - 1):
            total_distance += self._calculate_distance(route_coords[i], route_coords[i + 1])
        return total_distance
    
    def _calculate_distance(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in km."""
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        # Haversine formula
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c 