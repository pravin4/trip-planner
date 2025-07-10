#!/usr/bin/env python3
"""
Journey Planning Agent
Handles road trips, flights, and multi-modal transportation planning with dynamic configuration.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from utils.geocoding_service import GeocodingService
from utils.transportation_planner import TransportationPlanner
from utils.dynamic_route_planner import DynamicRoutePlanner
from api_integrations.google_places import GooglePlacesAPI
from config.dynamic_config import config_manager

logger = logging.getLogger(__name__)

@dataclass
class JourneyState:
    """State for journey planning workflow."""
    origin: str = ""
    destination: str = ""
    start_date: str = ""
    end_date: str = ""
    travel_mode: str = "drive"  # drive, fly, multi_modal
    preferences: Dict[str, Any] = None
    journey_plan: Dict[str, Any] = None
    route_stops: List[Dict[str, Any]] = None
    flight_info: Dict[str, Any] = None
    airport_info: Dict[str, Any] = None
    total_distance: float = 0.0
    total_duration: float = 0.0
    total_cost: float = 0.0
    messages: List[Dict[str, Any]] = None

class JourneyAgent:
    """Agent for planning journeys including road trips and flights with dynamic configuration."""
    
    def __init__(self):
        """Initialize the Journey Agent."""
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.geocoding = GeocodingService()
        self.transportation = TransportationPlanner()
        self.google_places = GooglePlacesAPI()
        self.dynamic_route_planner = DynamicRoutePlanner()
        self.config = config_manager
        
        # Create the workflow
        self.workflow = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create the journey planning workflow."""
        workflow = StateGraph(JourneyState)
        
        # Add nodes
        workflow.add_node("analyze_journey", self._analyze_journey)
        workflow.add_node("plan_route", self._plan_route)
        workflow.add_node("find_stops", self._find_stops)
        workflow.add_node("plan_flights", self._plan_flights)
        workflow.add_node("optimize_journey", self._optimize_journey)
        workflow.add_node("calculate_journey_costs", self._calculate_journey_costs)
        workflow.add_node("finalize_journey", self._finalize_journey)
        
        # Add edges
        workflow.add_edge("analyze_journey", "plan_route")
        workflow.add_edge("plan_route", "find_stops")
        workflow.add_edge("find_stops", "plan_flights")
        workflow.add_edge("plan_flights", "optimize_journey")
        workflow.add_edge("optimize_journey", "calculate_journey_costs")
        workflow.add_edge("calculate_journey_costs", "finalize_journey")
        workflow.add_edge("finalize_journey", END)
        
        # Add START edge
        workflow.add_edge(START, "analyze_journey")
        
        return workflow.compile()
    
    def _analyze_journey(self, state: JourneyState) -> JourneyState:
        """Analyze the journey requirements and determine travel mode."""
        try:
            # Clean and validate location strings
            origin_clean = self._clean_location_string(state.origin)
            dest_clean = self._clean_location_string(state.destination)
            
            origin_coords = self.geocoding.get_coordinates(origin_clean)
            dest_coords = self.geocoding.get_coordinates(dest_clean)
            
            if not origin_coords or not dest_coords:
                # Try with fallback locations
                origin_coords = self._get_fallback_coordinates(origin_clean)
                dest_coords = self._get_fallback_coordinates(dest_clean)
                
                if not origin_coords or not dest_coords:
                    raise ValueError(f"Could not get coordinates for {origin_clean} or {dest_clean}")
            
            # Calculate direct distance
            distance = self._calculate_distance(origin_coords, dest_coords)
            
            # Get dynamic distance thresholds from configuration
            distance_config = self.config.get_distance_config()
            
            # Check for user preferences first (this should override everything)
            if state.preferences and "travel_mode" in state.preferences:
                state.travel_mode = state.preferences["travel_mode"]
                logger.info(f"Using user-specified travel mode: {state.travel_mode}")
            else:
                # Determine travel mode based on dynamic distance thresholds
                if distance > distance_config.long_distance_threshold:
                    state.travel_mode = "fly"
                elif distance > distance_config.medium_distance_threshold:
                    state.travel_mode = "multi_modal"
                else:
                    state.travel_mode = "drive"  # Default to drive for reasonable distances
            
            # Store distance for later use
            state.total_distance = distance
            
            state.messages = add_messages(state.messages, [
                ("system", f"Journey analysis complete. Distance: {distance:.1f} km, Mode: {state.travel_mode}")
            ])
            
        except Exception as e:
            logger.error(f"Error analyzing journey: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error analyzing journey: {str(e)}")
            ])
        
        return state
    
    def _plan_route(self, state: JourneyState) -> JourneyState:
        """Plan the route between origin and destination."""
        try:
            origin_clean = self._clean_location_string(state.origin)
            dest_clean = self._clean_location_string(state.destination)
            
            origin_coords = self.geocoding.get_coordinates(origin_clean)
            dest_coords = self.geocoding.get_coordinates(dest_clean)
            
            if state.travel_mode in ["drive", "multi_modal"]:
                # Get driving route with intermediate waypoints
                route = self.transportation.get_driving_route(
                    origin_coords, dest_coords
                )
                
                if route:
                    # Add intermediate waypoints for long journeys
                    if state.total_distance > 200:  # More than 200 km
                        intermediate_waypoints = self._add_intermediate_waypoints(
                            origin_coords, dest_coords, route
                        )
                        route["waypoints"] = intermediate_waypoints
                    
                    state.journey_plan = {
                        "route": route,
                        "distance": route.get("distance", 0),
                        "duration": route.get("duration", 0),
                        "waypoints": route.get("waypoints", [])
                    }
                    state.total_distance = route.get("distance", 0)
                    state.total_duration = route.get("duration", 0)
            
            state.messages = add_messages(state.messages, [
                ("system", f"Route planned. Distance: {state.total_distance:.1f} km, Duration: {state.total_duration:.1f} hours")
            ])
            
        except Exception as e:
            logger.error(f"Error planning route: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error planning route: {str(e)}")
            ])
        
        return state
    
    def _find_stops(self, state: JourneyState) -> JourneyState:
        """Find interesting stops along the route using dynamic route planning."""
        try:
            if state.travel_mode not in ["drive", "multi_modal"]:
                return state
            
            if not state.journey_plan or not state.journey_plan.get("waypoints"):
                return state
            
            # Extract route coordinates for dynamic stop finding
            route_coords = []
            waypoints = state.journey_plan["waypoints"]
            
            for waypoint in waypoints:
                if "location" in waypoint:
                    route_coords.append((waypoint["location"]["lat"], waypoint["location"]["lng"]))
            
            # Use dynamic route planner to find stops
            dynamic_stops = self.dynamic_route_planner.find_dynamic_stops(
                state.origin, state.destination, route_coords
            )
            
            # Add rest stops for long journeys using dynamic intervals
            if state.total_duration > self.config.get_distance_config().rest_stop_interval:
                rest_stops = self._add_rest_stops(waypoints)
                dynamic_stops.extend(rest_stops)
            
            # Remove duplicates and sort by distance
            unique_stops = []
            seen_locations = set()
            for stop in dynamic_stops:
                location_key = f"{stop['location'].get('lat', 0):.3f},{stop['location'].get('lng', 0):.3f}"
                if location_key not in seen_locations:
                    unique_stops.append(stop)
                    seen_locations.add(location_key)
            
            state.route_stops = sorted(unique_stops, key=lambda x: x.get("distance_from_origin", 0))
            
            state.messages = add_messages(state.messages, [
                ("system", f"Found {len(state.route_stops)} dynamic stops along the route")
            ])
            
        except Exception as e:
            logger.error(f"Error finding stops: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error finding stops: {str(e)}")
            ])
        
        return state
    
    def _plan_flights(self, state: JourneyState) -> JourneyState:
        """Plan flights if flying or multi-modal."""
        try:
            if state.travel_mode not in ["fly", "multi_modal"]:
                return state
            
            # Find nearest airports
            origin_airports = self._find_nearest_airports(state.origin)
            dest_airports = self._find_nearest_airports(state.destination)
            
            if origin_airports and dest_airports:
                # For now, use mock flight data
                # In production, integrate with flight APIs (Amadeus, Skyscanner, etc.)
                flight_info = self._get_mock_flight_info(
                    origin_airports[0], dest_airports[0], state.start_date
                )
                
                state.flight_info = flight_info
                state.airport_info = {
                    "origin_airport": origin_airports[0],
                    "destination_airport": dest_airports[0],
                    "origin_airports": origin_airports,
                    "destination_airports": dest_airports
                }
            
            state.messages = add_messages(state.messages, [
                ("system", f"Flight planning complete for {state.travel_mode} journey")
            ])
            
        except Exception as e:
            logger.error(f"Error planning flights: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error planning flights: {str(e)}")
            ])
        
        return state
    
    def _optimize_journey(self, state: JourneyState) -> JourneyState:
        """Optimize the overall journey plan."""
        try:
            # Optimize stop order for road trips
            if state.route_stops and state.travel_mode in ["drive", "multi_modal"]:
                state.route_stops = self._optimize_stop_order(state.route_stops)
            
            # Add timing information
            if state.journey_plan:
                state.journey_plan["timing"] = self._calculate_timing(
                    state.start_date, state.total_duration, state.route_stops
                )
            
            state.messages = add_messages(state.messages, [
                ("system", "Journey optimization complete")
            ])
            
        except Exception as e:
            logger.error(f"Error optimizing journey: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error optimizing journey: {str(e)}")
            ])
        
        return state
    
    def _calculate_journey_costs(self, state: JourneyState) -> JourneyState:
        """Calculate costs for the journey using dynamic pricing."""
        try:
            cost_config = self.config.get_cost_config()
            
            costs = {
                "transportation": 0,
                "accommodations": 0,
                "activities": 0,
                "meals": 0,
                "total": 0
            }
            
            # Transportation costs using dynamic pricing
            if state.travel_mode == "drive":
                # Dynamic gas cost calculation
                gas_cost = self.config.calculate_dynamic_gas_cost(state.total_distance)
                
                # Dynamic toll cost calculation
                toll_cost = self.config.calculate_dynamic_toll_cost(state.total_distance)
                
                # Dynamic parking cost calculation
                parking_cost = self.config.calculate_dynamic_parking_cost(state.total_duration)
                
                costs["transportation"] = gas_cost + toll_cost + parking_cost
                
            elif state.travel_mode == "fly":
                # Flight cost using dynamic pricing
                flight_cost = state.total_distance * cost_config.flight_cost_per_km
                costs["transportation"] = flight_cost
                
            elif state.travel_mode == "multi_modal":
                # Multi-modal cost (combination of different modes)
                drive_distance = state.total_distance * 0.3  # Assume 30% driving
                fly_distance = state.total_distance * 0.7   # Assume 70% flying
                
                drive_cost = self.config.calculate_dynamic_gas_cost(drive_distance)
                fly_cost = fly_distance * cost_config.flight_cost_per_km
                
                costs["transportation"] = drive_cost + fly_cost
            
            # Activity costs (based on number of stops)
            if state.route_stops:
                activity_cost = len(state.route_stops) * 25  # $25 per stop/activity
                costs["activities"] = activity_cost
            
            # Meal costs (based on journey duration)
            meal_cost = max(1, state.total_duration / 4) * 15  # $15 per meal, every 4 hours
            costs["meals"] = meal_cost
            
            # Calculate total
            costs["total"] = sum(costs.values())
            state.total_cost = costs["total"]
            
            state.messages = add_messages(state.messages, [
                ("system", f"Journey costs calculated: ${costs['total']:.2f} total")
            ])
            
        except Exception as e:
            logger.error(f"Error calculating journey costs: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error calculating journey costs: {str(e)}")
            ])
        
        return state
    
    def _finalize_journey(self, state: JourneyState) -> JourneyState:
        """Finalize the journey plan."""
        try:
            # Create final journey summary
            journey_summary = {
                "origin": state.origin,
                "destination": state.destination,
                "travel_mode": state.travel_mode,
                "total_distance": state.total_distance,
                "total_duration": state.total_duration,
                "total_cost": state.total_cost,
                "route": state.journey_plan,
                "stops": state.route_stops,
                "flights": state.flight_info,
                "airports": state.airport_info,
                "start_date": state.start_date,
                "end_date": state.end_date
            }
            
            state.journey_plan = journey_summary
            
            state.messages = add_messages(state.messages, [
                ("system", "Journey plan finalized successfully")
            ])
            
        except Exception as e:
            logger.error(f"Error finalizing journey: {e}")
            state.messages = add_messages(state.messages, [
                ("system", f"Error finalizing journey: {str(e)}")
            ])
        
        return state
    
    def plan_journey(self, origin: str, destination: str, start_date: str, 
                    end_date: str, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Plan a complete journey from origin to destination."""
        try:
            # Initialize state with proper defaults
            state = JourneyState(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                preferences=preferences or {},
                journey_plan={},
                route_stops=[],
                flight_info={},
                airport_info={},
                messages=[]
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            # Handle both dict and object returns from LangGraph
            if isinstance(final_state, dict):
                # Newer LangGraph versions return dict
                journey_plan = final_state.get("journey_plan", {})
                travel_mode = final_state.get("travel_mode", "drive")
                total_distance = final_state.get("total_distance", 0)
                total_duration = final_state.get("total_duration", 0)
                total_cost = final_state.get("total_cost", 0)
                route_stops = final_state.get("route_stops", [])
            else:
                # Older LangGraph versions return state object
                journey_plan = final_state.journey_plan or {}
                travel_mode = final_state.travel_mode
                total_distance = final_state.total_distance
                total_duration = final_state.total_duration
                total_cost = final_state.total_cost
                route_stops = final_state.route_stops or []
            
            # Return comprehensive journey plan
            return {
                "travel_mode": travel_mode,
                "total_distance": total_distance,
                "total_duration": total_duration,
                "total_cost": total_cost,
                "route_stops": route_stops,
                "journey_plan": journey_plan,
                "origin": origin,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "preferences": preferences or {}
            }
            
        except Exception as e:
            logger.error(f"Error planning journey: {e}")
            # Return fallback plan
            return {
                "travel_mode": "drive",
                "total_distance": 0,
                "total_duration": 0,
                "total_cost": 0,
                "route_stops": [],
                "journey_plan": {},
                "origin": origin,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "preferences": preferences or {},
                "error": str(e)
            }
    
    def _calculate_distance(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in km."""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r
    
    def _find_nearby_attractions(self, location: Dict[str, float]) -> List[Dict[str, Any]]:
        """Find nearby attractions using Google Places API."""
        try:
            lat = location.get("lat")
            lng = location.get("lng")
            
            if not lat or not lng:
                return []
            
            # Search for tourist attractions
            places = self.google_places.search_nearby(
                lat, lng, radius=5000, type="tourist_attraction"
            )
            
            return places[:5]  # Return top 5 attractions
            
        except Exception as e:
            logger.error(f"Error finding nearby attractions: {e}")
            return []
    
    def _add_rest_stops(self, waypoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add rest stops for long journeys."""
        rest_stops = []
        
        # Add rest stops every 4 hours
        target_interval = 4  # hours
        current_duration = 0
        
        for waypoint in waypoints:
            current_duration += waypoint.get("duration", 0)
            
            if current_duration >= target_interval:
                rest_stops.append({
                    "location": waypoint["location"],
                    "duration": current_duration,
                    "stop_type": "rest",
                    "description": "Rest stop - gas, food, bathroom"
                })
                current_duration = 0
        
        return rest_stops
    
    def _find_nearest_airports(self, location: str) -> List[Dict[str, Any]]:
        """Find nearest airports to a location."""
        try:
            coords = self.geocoding.get_coordinates(location)
            if not coords:
                return []
            
            # Search for airports using Google Places
            airports = self.google_places.search_nearby(
                coords[0], coords[1], radius=50000, type="airport"
            )
            
            return airports[:3]  # Return top 3 nearest airports
            
        except Exception as e:
            logger.error(f"Error finding airports: {e}")
            return []
    
    def _get_mock_flight_info(self, origin_airport: Dict[str, Any], 
                             dest_airport: Dict[str, Any], date: str) -> Dict[str, Any]:
        """Get mock flight information (replace with real API in production)."""
        return {
            "origin_airport": origin_airport.get("name", "Unknown"),
            "destination_airport": dest_airport.get("name", "Unknown"),
            "departure_time": "09:00",
            "arrival_time": "11:30",
            "airline": "Mock Airlines",
            "flight_number": "MA123",
            "cost": 350,
            "duration": 2.5
        }
    
    def _optimize_stop_order(self, stops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize the order of stops for efficiency."""
        # Simple optimization: sort by duration
        return sorted(stops, key=lambda x: x.get("duration", 0))
    
    def _calculate_timing(self, start_date: str, total_duration: float, 
                         stops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate timing for the journey."""
        start_dt = datetime.fromisoformat(start_date)
        
        timing = {
            "start_time": start_dt.isoformat(),
            "estimated_end_time": (start_dt + timedelta(hours=total_duration)).isoformat(),
            "stop_times": []
        }
        
        current_time = start_dt
        for stop in stops:
            stop_duration = stop.get("duration", 0)
            current_time += timedelta(hours=stop_duration)
            
            timing["stop_times"].append({
                "location": stop["location"],
                "time": current_time.isoformat(),
                "stop_type": stop.get("stop_type", "unknown")
            })
        
        return timing 

    def _get_predefined_stops(self, origin: str, destination: str) -> List[Dict[str, Any]]:
        """Get predefined stops for popular routes."""
        origin_lower = origin.lower()
        dest_lower = destination.lower()
        
        # San Jose to Shelter Cove route
        if "san jose" in origin_lower and "shelter cove" in dest_lower:
            return [
                {
                    "location": {"lat": 37.7749, "lng": -122.4194},
                    "duration": 1.0,
                    "name": "San Francisco",
                    "attractions": [
                        {"name": "Golden Gate Bridge", "type": "landmark"},
                        {"name": "Fisherman's Wharf", "type": "attraction"},
                        {"name": "Alcatraz Island", "type": "historical"}
                    ],
                    "stop_type": "major_city",
                    "description": "Stop in San Francisco for iconic landmarks and attractions"
                },
                {
                    "location": {"lat": 36.6002, "lng": -121.8947},
                    "duration": 3.5,
                    "name": "Monterey",
                    "attractions": [
                        {"name": "Monterey Bay Aquarium", "type": "aquarium"},
                        {"name": "Cannery Row", "type": "historical"},
                        {"name": "17-Mile Drive", "type": "scenic"}
                    ],
                    "stop_type": "coastal_town",
                    "description": "Visit Monterey for the famous aquarium and coastal views"
                },
                {
                    "location": {"lat": 36.2704, "lng": -121.8081},
                    "duration": 5.0,
                    "name": "Big Sur",
                    "attractions": [
                        {"name": "Bixby Bridge", "type": "landmark"},
                        {"name": "McWay Falls", "type": "waterfall"},
                        {"name": "Pfeiffer Beach", "type": "beach"}
                    ],
                    "stop_type": "scenic",
                    "description": "Experience the stunning Big Sur coastline"
                }
            ]
        
        # San Jose to Big Sur route
        elif "san jose" in origin_lower and "big sur" in dest_lower:
            return [
                {
                    "location": {"lat": 36.6002, "lng": -121.8947},
                    "duration": 2.5,
                    "name": "Monterey",
                    "attractions": [
                        {"name": "Monterey Bay Aquarium", "type": "aquarium"},
                        {"name": "Cannery Row", "type": "historical"}
                    ],
                    "stop_type": "coastal_town"
                }
            ]
        
        # Generic California coastal route
        elif any(city in origin_lower for city in ["san jose", "san francisco", "oakland"]) and \
             any(city in dest_lower for city in ["monterey", "carmel", "big sur", "santa barbara"]):
            return [
                {
                    "location": {"lat": 36.6002, "lng": -121.8947},
                    "duration": 2.0,
                    "name": "Monterey",
                    "attractions": [
                        {"name": "Monterey Bay Aquarium", "type": "aquarium"},
                        {"name": "Cannery Row", "type": "historical"}
                    ],
                    "stop_type": "coastal_town"
                }
            ]
        
        return [] 

    def _clean_location_string(self, location: str) -> str:
        """Clean location string for better geocoding."""
        if not location:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = location.strip()
        
        # Handle common abbreviations
        abbreviations = {
            "SF": "San Francisco",
            "NYC": "New York City",
            "LA": "Los Angeles",
            "DC": "Washington DC",
            "Vegas": "Las Vegas",
            "Philly": "Philadelphia"
        }
        
        for abbr, full in abbreviations.items():
            if cleaned.upper() == abbr.upper():
                cleaned = full
                break
        
        return cleaned
    
    def _get_fallback_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """Get fallback coordinates for common locations."""
        fallback_coords = {
            "San Francisco": (37.7749, -122.4194),
            "New York City": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "Chicago": (41.8781, -87.6298),
            "Miami": (25.7617, -80.1918),
            "Seattle": (47.6062, -122.3321),
            "Denver": (39.7392, -104.9903),
            "Austin": (30.2672, -97.7431),
            "Nashville": (36.1627, -86.7816),
            "New Orleans": (29.9511, -90.0715),
            "Portland": (45.5152, -122.6784),
            "San Diego": (32.7157, -117.1611),
            "Las Vegas": (36.1699, -115.1398),
            "Phoenix": (33.4484, -112.0740),
            "Dallas": (32.7767, -96.7970),
            "Houston": (29.7604, -95.3698),
            "Atlanta": (33.7490, -84.3880),
            "Boston": (42.3601, -71.0589),
            "Philadelphia": (39.9526, -75.1652),
            "Washington DC": (38.9072, -77.0369)
        }
        
        return fallback_coords.get(location)
    
    def _add_intermediate_waypoints(self, origin: Tuple[float, float], 
                                   destination: Tuple[float, float], 
                                   route: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add intermediate waypoints for long journeys."""
        waypoints = route.get("waypoints", [])
        
        # For very long journeys, add major cities as waypoints
        if self._calculate_distance(origin, destination) > 500:
            # Find major cities along the route
            major_cities = self._find_major_cities_along_route(origin, destination)
            
            for city in major_cities:
                waypoints.append({
                    "location": {"lat": city["lat"], "lng": city["lng"]},
                    "name": city["name"],
                    "type": "major_city",
                    "duration": 0  # Will be calculated
                })
        
        return waypoints
    
    def _find_major_cities_along_route(self, origin: Tuple[float, float], 
                                      destination: Tuple[float, float]) -> List[Dict[str, Any]]:
        """Find major cities along a route."""
        # This is a simplified version - in production, use a proper geographic database
        major_cities = [
            {"name": "Sacramento", "lat": 38.5816, "lng": -121.4944},
            {"name": "Reno", "lat": 39.5296, "lng": -119.8138},
            {"name": "Salt Lake City", "lat": 40.7608, "lng": -111.8910},
            {"name": "Denver", "lat": 39.7392, "lng": -104.9903},
            {"name": "Kansas City", "lat": 39.0997, "lng": -94.5786},
            {"name": "St. Louis", "lat": 38.6270, "lng": -90.1994},
            {"name": "Nashville", "lat": 36.1627, "lng": -86.7816},
            {"name": "Atlanta", "lat": 33.7490, "lng": -84.3880},
            {"name": "Charlotte", "lat": 35.2271, "lng": -80.8431},
            {"name": "Richmond", "lat": 37.5407, "lng": -77.4360}
        ]
        
        # Filter cities that are roughly along the route
        route_cities = []
        for city in major_cities:
            city_coords = (city["lat"], city["lng"])
            
            # Check if city is within reasonable distance of the route
            if self._is_point_near_route(origin, destination, city_coords, max_distance=100):
                route_cities.append(city)
        
        return route_cities[:3]  # Limit to 3 cities
    
    def _is_point_near_route(self, start: Tuple[float, float], end: Tuple[float, float], 
                            point: Tuple[float, float], max_distance: float = 100) -> bool:
        """Check if a point is near a route line."""
        # Calculate distance from point to line segment
        # This is a simplified calculation
        start_lat, start_lng = start
        end_lat, end_lng = end
        point_lat, point_lng = point
        
        # Calculate distance using haversine formula
        distance = self._calculate_distance(start, point)
        
        return distance <= max_distance 