#!/usr/bin/env python3
"""
Journey Planning Agent
Handles road trips, flights, and multi-modal transportation planning.
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
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from utils.geocoding_service import GeocodingService
from utils.transportation_planner import TransportationPlanner
from api_integrations.google_places import GooglePlacesAPI

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
    """Agent for planning journeys including road trips and flights."""
    
    def __init__(self):
        """Initialize the Journey Agent."""
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.geocoding = GeocodingService()
        self.transportation = TransportationPlanner()
        self.google_places = GooglePlacesAPI()
        
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
        from langgraph.graph import START
        workflow.add_edge(START, "analyze_journey")
        
        return workflow.compile()
    
    def _analyze_journey(self, state: JourneyState) -> JourneyState:
        """Analyze the journey requirements and determine travel mode."""
        try:
            origin_coords = self.geocoding.get_coordinates(state.origin)
            dest_coords = self.geocoding.get_coordinates(state.destination)
            
            if not origin_coords or not dest_coords:
                raise ValueError(f"Could not get coordinates for {state.origin} or {state.destination}")
            
            # Calculate direct distance
            distance = self._calculate_distance(origin_coords, dest_coords)
            
            # Determine travel mode based on distance and preferences
            if distance > 800:  # More than 800 km
                state.travel_mode = "fly"
            elif distance > 400:  # 400-800 km
                state.travel_mode = "multi_modal"
            else:
                state.travel_mode = "drive"
            
            # Override if specified in preferences
            if state.preferences and "travel_mode" in state.preferences:
                state.travel_mode = state.preferences["travel_mode"]
            
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
            origin_coords = self.geocoding.get_coordinates(state.origin)
            dest_coords = self.geocoding.get_coordinates(state.destination)
            
            if state.travel_mode in ["drive", "multi_modal"]:
                # Get driving route
                route = self.transportation.get_driving_route(
                    origin_coords, dest_coords
                )
                
                if route:
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
        """Find interesting stops along the route."""
        try:
            if state.travel_mode not in ["drive", "multi_modal"]:
                return state
            
            if not state.journey_plan or not state.journey_plan.get("waypoints"):
                return state
            
            stops = []
            waypoints = state.journey_plan["waypoints"]
            
            # Find stops every 2-3 hours of driving
            target_stop_interval = 2.5  # hours
            current_duration = 0
            
            for i, waypoint in enumerate(waypoints):
                current_duration += waypoint.get("duration", 0)
                
                if current_duration >= target_stop_interval:
                    # Find interesting places near this waypoint
                    nearby_places = self._find_nearby_attractions(waypoint["location"])
                    
                    if nearby_places:
                        stops.append({
                            "location": waypoint["location"],
                            "duration": current_duration,
                            "attractions": nearby_places[:3],  # Top 3 attractions
                            "stop_type": "attraction"
                        })
                    
                    current_duration = 0  # Reset timer
            
            # Add rest stops for long journeys
            if state.total_duration > 6:
                rest_stops = self._add_rest_stops(waypoints)
                stops.extend(rest_stops)
            
            state.route_stops = stops
            
            state.messages = add_messages(state.messages, [
                ("system", f"Found {len(stops)} stops along the route")
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
        """Calculate costs for the journey."""
        try:
            costs = {
                "transportation": 0,
                "accommodations": 0,
                "activities": 0,
                "meals": 0,
                "total": 0
            }
            
            # Transportation costs
            if state.travel_mode == "drive":
                # Gas cost (assuming 25 mpg, $3.50/gallon)
                gas_cost = (state.total_distance * 1.609) / 25 * 3.50  # Convert km to miles
                costs["transportation"] = gas_cost
                
            elif state.travel_mode == "fly":
                # Flight cost (mock data)
                costs["transportation"] = state.flight_info.get("cost", 400) if state.flight_info else 400
                
            elif state.travel_mode == "multi_modal":
                # Combination of driving and flying
                drive_distance = state.journey_plan.get("distance", 0) if state.journey_plan else 0
                gas_cost = (drive_distance * 1.609) / 25 * 3.50
                flight_cost = state.flight_info.get("cost", 300) if state.flight_info else 300
                costs["transportation"] = gas_cost + flight_cost
            
            # Accommodation costs for overnight stops
            if state.route_stops:
                overnight_stops = [s for s in state.route_stops if s.get("overnight", False)]
                costs["accommodations"] = len(overnight_stops) * 150  # $150 per night
            
            # Activity costs for stops
            if state.route_stops:
                activity_cost = sum(len(s.get("attractions", [])) * 20 for s in state.route_stops)
                costs["activities"] = activity_cost
            
            # Meal costs
            journey_days = max(1, int(state.total_duration / 8))  # Assume 8 hours per day
            costs["meals"] = journey_days * 50  # $50 per day for meals
            
            costs["total"] = sum(costs.values())
            state.total_cost = costs["total"]
            
            state.journey_plan["costs"] = costs
            
            state.messages = add_messages(state.messages, [
                ("system", f"Journey costs calculated: ${costs['total']:.2f}")
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
            # Initialize state
            state = JourneyState(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                preferences=preferences or {},
                messages=[]
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(state)
            
            # Return the journey plan
            if hasattr(final_state, "journey_plan") and final_state.journey_plan:
                return final_state.journey_plan
            elif hasattr(final_state, "model_dump"):
                return final_state.model_dump()
            else:
                # Convert dataclass to dict
                return {
                    "origin": final_state.origin,
                    "destination": final_state.destination,
                    "travel_mode": final_state.travel_mode,
                    "total_distance": final_state.total_distance,
                    "total_duration": final_state.total_duration,
                    "total_cost": final_state.total_cost,
                    "journey_plan": final_state.journey_plan,
                    "route_stops": final_state.route_stops,
                    "flight_info": final_state.flight_info,
                    "airport_info": final_state.airport_info
                }
                
        except Exception as e:
            logger.error(f"Error planning journey: {e}")
            return {"error": str(e)}
    
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