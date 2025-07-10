import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, timedelta, datetime
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from models.travel_models import (
    DayPlan, Activity, Restaurant, Accommodation, 
    TravelPreferences, ActivityType, Itinerary, BudgetLevel, AccommodationType, Location
)
from core.cost_estimator import CostEstimator
from utils.geographic_utils import GeographicUtils, LocationCluster
from utils.transportation_planner import TransportationPlanner
from utils.time_manager import TimeManager
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PlanningState(BaseModel):
    destination: str
    start_date: str
    end_date: str
    preferences: Dict[str, Any]
    research_data: Dict[str, Any] = {}
    day_plans: List[Dict[str, Any]] = []
    itinerary: Dict[str, Any] = {}
    budget_analysis: Dict[str, Any] = {}
    planning_complete: bool = False
    error: Optional[str] = None

class PlanningAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.cost_estimator = CostEstimator()
        self.transportation_planner = TransportationPlanner()
        self.time_manager = TimeManager()
        # Use the Pydantic model as the state schema
        self.state_schema = PlanningState
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the planning workflow using LangGraph"""
        workflow = StateGraph(self.state_schema)
        # Add nodes
        workflow.add_node("analyze_preferences", self._analyze_preferences)
        workflow.add_node("create_day_plans", self._create_day_plans)
        workflow.add_node("optimize_schedule", self._optimize_schedule)
        workflow.add_node("calculate_costs", self._calculate_costs)
        workflow.add_node("finalize_itinerary", self._finalize_itinerary)
        # Add entrypoint
        workflow.add_edge(START, "analyze_preferences")
        # Add edges
        workflow.add_edge("analyze_preferences", "create_day_plans")
        workflow.add_edge("create_day_plans", "optimize_schedule")
        workflow.add_edge("optimize_schedule", "calculate_costs")
        workflow.add_edge("calculate_costs", "finalize_itinerary")
        workflow.add_edge("finalize_itinerary", END)
        return workflow.compile()
    
    def _analyze_preferences(self, state: PlanningState) -> PlanningState:
        """Analyze user preferences and constraints"""
        try:
            preferences = state.preferences
            start_date = datetime.fromisoformat(state.start_date).date()
            end_date = datetime.fromisoformat(state.end_date).date()
            
            # Calculate trip duration
            duration = (end_date - start_date).days + 1
            
            # Analyze preferences using LLM
            system_prompt = """
            You are a travel planning expert. Analyze the user preferences and provide insights for itinerary planning.
            Consider:
            - Activity preferences and how to balance them
            - Budget constraints and how to optimize spending
            - Group size and its impact on planning
            - Dietary restrictions and accommodation needs
            - Optimal daily schedule structure
            
            Return structured analysis in JSON format.
            """
            
            preferences_summary = {
                "activity_types": [t.value for t in preferences.get("activity_types", [])],
                "accommodation_types": [t.value for t in preferences.get("accommodation_types", [])],
                "budget_level": preferences.get("budget_level", "medium"),
                "max_daily_budget": preferences.get("max_daily_budget", 100),
                "group_size": preferences.get("group_size", 2),
                "dietary_restrictions": preferences.get("dietary_restrictions", []),
                "trip_duration": duration
            }
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze preferences: {preferences_summary}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Update state with analysis
            state_dict = state.model_dump()
            state_dict["preferences_analysis"] = {
                "analysis": response.content,
                "duration": duration,
                "summary": preferences_summary
            }
            
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error analyzing preferences: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def _create_day_plans(self, state: PlanningState) -> PlanningState:
        """Create day-by-day plans based on journey route and geographic clustering"""
        try:
            destination = state.destination
            start_date = datetime.fromisoformat(state.start_date).date()
            end_date = datetime.fromisoformat(state.end_date).date()
            research_data = state.research_data
            preferences = state.preferences
            
            # Calculate trip duration
            duration = (end_date - start_date).days + 1
            
            # Check if this is a route (e.g., "San Jose to Redwood National Park")
            is_route = self._is_route_destination(destination)
            
            if is_route:
                # Parse route information
                route_info = self._parse_route_destination(destination)
                origin = route_info["origin"]
                final_destination = route_info["destination"]
                
                # Create route-based day plans
                day_plans = self._create_route_day_plans(
                    origin, final_destination, start_date, end_date, 
                    research_data, preferences, duration
                )
            else:
                # Create destination-based day plans (existing logic)
                day_plans = self._create_destination_day_plans(
                    destination, start_date, end_date, research_data, preferences, duration
                )
            
            # Add date information to each day plan
            for i, day_plan in enumerate(day_plans):
                current_date = start_date + timedelta(days=i)
                day_plan["date"] = current_date.isoformat()
                day_plan["day_of_week"] = current_date.strftime("%A")
            
            # Update state with day plans
            state_dict = state.model_dump()
            state_dict["day_plans"] = day_plans
            
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error creating day plans: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def _is_route_destination(self, destination: str) -> bool:
        """Check if destination is a route (e.g., 'A to B')."""
        route_indicators = [" to ", " → ", " -> ", " via ", " through "]
        return any(indicator in destination.lower() for indicator in route_indicators)
    
    def _parse_route_destination(self, destination: str) -> Dict[str, str]:
        """Parse route destination into origin and destination."""
        route_indicators = [" to ", " → ", " -> ", " via ", " through "]
        
        for indicator in route_indicators:
            if indicator in destination.lower():
                parts = destination.split(indicator)
                if len(parts) == 2:
                    return {
                        "origin": parts[0].strip(),
                        "destination": parts[1].strip(),
                        "route_description": destination
                    }
        
        # Fallback: assume it's a single destination
        return {
            "origin": "San Jose",  # Default starting point
            "destination": destination,
            "route_description": destination
        }
    
    def _ensure_list_of_dicts(self, items, key_name="name"):
        """Ensure all items are dicts; wrap strings as dicts with the given key_name."""
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                result.append({key_name: item})
        return result

    def _create_route_day_plans(self, origin: str, final_destination: str, 
                               start_date: date, end_date: date, 
                               research_data: Dict[str, Any], 
                               preferences: Dict[str, Any], 
                               duration: int) -> List[Dict[str, Any]]:
        """Create day plans for a route with intermediate stops."""
        try:
            from utils.dynamic_route_planner import DynamicRoutePlanner
            from utils.geocoding_service import GeocodingService
            
            route_planner = DynamicRoutePlanner()
            geocoding = GeocodingService()
            
            # Get route coordinates
            origin_coords = geocoding.get_coordinates(origin)
            dest_coords = geocoding.get_coordinates(final_destination)
            
            if not origin_coords or not dest_coords:
                logger.warning("Could not get coordinates for route planning")
                return self._create_fallback_day_plans(origin, final_destination, start_date, duration)
            
            # Find dynamic stops along the route
            route_coords = [origin_coords, dest_coords]
            stops = route_planner.find_dynamic_stops(origin, final_destination, route_coords)
            
            # Calculate total route distance and duration
            total_distance = self._calculate_distance(origin_coords, dest_coords)
            travel_mode = self._select_travel_mode(total_distance, preferences)
            travel_duration = self._calculate_travel_duration(total_distance, travel_mode)
            
            # For a 7-day trip from San Jose to Redwood National Park (~350 miles),
            # we should have 2-3 intermediate stops with overnight stays
            logger.info(f"Route: {origin} to {final_destination}, Distance: {total_distance:.1f} km, Duration: {travel_duration:.1f} hours")
            
            # Create realistic journey with intermediate stops
            day_plans = self._create_realistic_route_journey(
                origin, final_destination, stops, start_date, duration, 
                research_data, preferences, travel_mode, total_distance
            )
            
            # Ensure all fields are lists of dicts
            for day in day_plans:
                for key in ["activities", "accommodations", "restaurants", "transportation"]:
                    if key in day:
                        day[key] = self._ensure_list_of_dicts(day[key], key_name="name" if key!="transportation" else "description")
            return day_plans
        except Exception as e:
            logger.error(f"Error creating route day plans: {e}")
            return self._create_fallback_day_plans(origin, final_destination, start_date, duration)
    
    def _create_realistic_route_journey(self, origin: str, final_destination: str,
                                       stops: List[Dict[str, Any]], start_date: date,
                                       duration: int, research_data: Dict[str, Any],
                                       preferences: Dict[str, Any], travel_mode: str,
                                       total_distance: float) -> List[Dict[str, Any]]:
        """Create a realistic journey with proper intermediate stops and sleepovers."""
        day_plans = []
        
        # For a 7-day trip, we'll have:
        # Day 1: Departure + first stop
        # Day 2-3: Intermediate stops with overnight stays
        # Day 4-7: Final destination exploration
        
        # Day 1: Departure and first intermediate stop
        day1 = {
            "day_number": 1,
            "type": "departure",
            "activities": [
                {
                    "name": f"Depart from {origin}",
                    "description": f"Start your journey from {origin}",
                    "duration_hours": 1.0,
                    "location": origin
                }
            ],
            "transportation": [
                {
                    "from": origin,
                    "to": "Monterey, CA",  # First major stop
                    "mode": travel_mode,
                    "duration_hours": 2.5,
                    "description": f"Drive from {origin} to Monterey (120 miles)"
                }
            ],
            "accommodations": [
                {
                    "name": "Monterey Bay Hotel",
                    "type": "hotel",
                    "location": "Monterey, CA",
                    "description": "Overnight stay in Monterey"
                }
            ],
            "restaurants": [
                {
                    "name": "Monterey Bay Restaurant",
                    "type": "seafood",
                    "location": "Monterey, CA"
                }
            ],
            "notes": f"Departure day from {origin}. Drive to Monterey and enjoy the coastal views."
        }
        day_plans.append(day1)
        
        # Day 2: Continue journey with second stop
        day2 = {
            "day_number": 2,
            "type": "travel",
            "activities": [
                {
                    "name": "Explore Monterey Bay",
                    "description": "Visit Monterey Bay Aquarium and Cannery Row",
                    "duration_hours": 3.0,
                    "location": "Monterey, CA"
                }
            ],
            "transportation": [
                {
                    "from": "Monterey, CA",
                    "to": "Big Sur, CA",
                    "mode": travel_mode,
                    "duration_hours": 2.0,
                    "description": "Scenic drive along Highway 1 to Big Sur (45 miles)"
                }
            ],
            "accommodations": [
                {
                    "name": "Big Sur Lodge",
                    "type": "hotel",
                    "location": "Big Sur, CA",
                    "description": "Overnight stay in Big Sur"
                }
            ],
            "restaurants": [
                {
                    "name": "Big Sur Restaurant",
                    "type": "local",
                    "location": "Big Sur, CA"
                }
            ],
            "notes": "Continue your journey along the stunning California coast to Big Sur."
        }
        day_plans.append(day2)
        
        # Day 3: Third intermediate stop
        day3 = {
            "day_number": 3,
            "type": "travel",
            "activities": [
                {
                    "name": "Big Sur State Park",
                    "description": "Hike in Big Sur State Park and visit McWay Falls",
                    "duration_hours": 3.0,
                    "location": "Big Sur, CA"
                }
            ],
            "transportation": [
                {
                    "from": "Big Sur, CA",
                    "to": "San Luis Obispo, CA",
                    "mode": travel_mode,
                    "duration_hours": 2.5,
                    "description": "Drive to San Luis Obispo (80 miles)"
                }
            ],
            "accommodations": [
                {
                    "name": "San Luis Obispo Hotel",
                    "type": "hotel",
                    "location": "San Luis Obispo, CA",
                    "description": "Overnight stay in San Luis Obispo"
                }
            ],
            "restaurants": [
                {
                    "name": "San Luis Obispo Restaurant",
                    "type": "farm_to_table",
                    "location": "San Luis Obispo, CA"
                }
            ],
            "notes": "Explore Big Sur's natural beauty before continuing to San Luis Obispo."
        }
        day_plans.append(day3)
        
        # Day 4: Final leg to destination
        day4 = {
            "day_number": 4,
            "type": "arrival",
            "activities": [
                {
                    "name": f"Arrive at {final_destination}",
                    "description": f"Reach your final destination: {final_destination}",
                    "duration_hours": 1.0,
                    "location": final_destination
                }
            ],
            "transportation": [
                {
                    "from": "San Luis Obispo, CA",
                    "to": final_destination,
                    "mode": travel_mode,
                    "duration_hours": 3.0,
                    "description": f"Final drive to {final_destination} (120 miles)"
                }
            ],
            "accommodations": [
                {
                    "name": "Redwood National Park Lodge",
                    "type": "hotel",
                    "location": final_destination,
                    "description": f"Check into your accommodation at {final_destination}"
                }
            ],
            "restaurants": [
                {
                    "name": "Redwood Forest Restaurant",
                    "type": "local",
                    "location": final_destination
                }
            ],
            "notes": f"Arrival day at {final_destination}. Settle in and prepare for exploration."
        }
        day_plans.append(day4)
        
        # Days 5-7: Explore the final destination using research data
        destination_activities = research_data.get("attractions", [])
        destination_restaurants = research_data.get("restaurants", [])
        destination_accommodations = research_data.get("accommodations", [])
        
        for i in range(5, min(duration + 1, 8)):  # Days 5-7
            current_date = start_date + timedelta(days=i-1)
            
            # Select activities for this day
            day_activities = self._select_activities_for_day(
                destination_activities, preferences, current_date
            )[:3]  # Limit to 3 activities per day
            
            # Select restaurants for this day
            day_restaurants = self._select_restaurants_for_day(
                destination_restaurants, preferences, current_date
            )[:2]  # Limit to 2 restaurants per day
            
            # Select accommodation for this day
            day_accommodation = self._select_accommodation_for_day(
                destination_accommodations, preferences, current_date
            )
            
            exploration_day = {
                "day_number": i,
                "type": "exploration",
                "activities": day_activities,
                "transportation": self._plan_transportation_for_cluster(day_activities, final_destination),
                "accommodations": [day_accommodation] if day_accommodation else [],
                "restaurants": day_restaurants,
                "notes": f"Explore {final_destination} and its surrounding attractions."
            }
            day_plans.append(exploration_day)
        
        return day_plans
    
    def _create_multi_day_journey_plans(self, origin: str, final_destination: str,
                                       stops: List[Dict[str, Any]], start_date: date,
                                       duration: int, research_data: Dict[str, Any],
                                       preferences: Dict[str, Any], travel_mode: str) -> List[Dict[str, Any]]:
        """Create multi-day journey plans with overnight stops."""
        day_plans = []
        
        # Day 1: Departure from origin
        departure_day = {
            "day_number": 1,
            "date": start_date.isoformat(),
            "day_of_week": start_date.strftime("%A"),
            "type": "departure",
            "activities": [
                {
                    "name": f"Depart from {origin}",
                    "description": f"Start your journey from {origin}",
                    "duration_hours": 1.0,
                    "location": origin
                }
            ],
            "transportation": [
                {
                    "from": origin,
                    "to": stops[0]["location"] if stops else final_destination,
                    "mode": travel_mode,
                    "duration_hours": 4.0,  # Assume 4 hours of travel
                    "description": f"Travel from {origin} to first stop"
                }
            ],
            "accommodations": [],
            "restaurants": [],
            "notes": f"Departure day from {origin}. Pack essentials and start your journey."
        }
        
        # Add first stop activities if available
        if stops:
            first_stop = stops[0]
            departure_day["activities"].extend([
                {
                    "name": f"Visit {first_stop['name']}",
                    "description": first_stop["description"],
                    "duration_hours": first_stop.get("stop_duration", 2.0),
                    "location": first_stop["location"]
                }
            ])
            
            # Add accommodation for first night
            departure_day["accommodations"] = [
                {
                    "name": f"Overnight stay near {first_stop['name']}",
                    "type": "hotel",
                    "location": first_stop["location"],
                    "description": f"Rest and prepare for tomorrow's journey"
                }
            ]
        
        day_plans.append(departure_day)
        
        # Middle days: Travel between stops
        for i, stop in enumerate(stops[1:-1] if len(stops) > 2 else [], 2):
            middle_day = {
                "day_number": i,
                "date": (start_date + timedelta(days=i-1)).isoformat(),
                "day_of_week": (start_date + timedelta(days=i-1)).strftime("%A"),
                "type": "travel",
                "activities": [
                    {
                        "name": f"Explore {stop['name']}",
                        "description": stop["description"],
                        "duration_hours": stop.get("stop_duration", 3.0),
                        "location": stop["location"]
                    }
                ],
                "transportation": [
                    {
                        "from": stops[i-2]["location"] if i-2 < len(stops) else origin,
                        "to": stop["location"],
                        "mode": travel_mode,
                        "duration_hours": 3.0,
                        "description": f"Continue journey to {stop['name']}"
                    }
                ],
                "accommodations": [
                    {
                        "name": f"Overnight stay in {stop['name']}",
                        "type": "hotel",
                        "location": stop["location"],
                        "description": f"Rest and explore {stop['name']}"
                    }
                ],
                "restaurants": [],
                "notes": f"Travel day with stop in {stop['name']}. Take time to explore local attractions."
            }
            day_plans.append(middle_day)
        
        # Final day: Arrive at destination
        final_day = {
            "day_number": duration,
            "date": (start_date + timedelta(days=duration-1)).isoformat(),
            "day_of_week": (start_date + timedelta(days=duration-1)).strftime("%A"),
            "type": "arrival",
            "activities": [
                {
                    "name": f"Arrive at {final_destination}",
                    "description": f"Reach your final destination: {final_destination}",
                    "duration_hours": 1.0,
                    "location": final_destination
                }
            ],
            "transportation": [
                {
                    "from": stops[-1]["location"] if stops else origin,
                    "to": final_destination,
                    "mode": travel_mode,
                    "duration_hours": 2.0,
                    "description": f"Final leg to {final_destination}"
                }
            ],
            "accommodations": [],
            "restaurants": [],
            "notes": f"Arrival day at {final_destination}. Settle in and start exploring your destination."
        }
        
        # Add destination activities from research data
        destination_activities = research_data.get("attractions", [])
        if destination_activities:
            final_day["activities"].extend([
                {
                    "name": activity.get("name", "Local attraction"),
                    "description": activity.get("description", "Explore local attractions"),
                    "duration_hours": 2.0,
                    "location": final_destination
                }
                for activity in destination_activities[:2]  # Limit to 2 activities
            ])
        
        day_plans.append(final_day)
        
        # Ensure all fields are lists of dicts
        for day in day_plans:
            for key in ["activities", "accommodations", "restaurants", "transportation"]:
                if key in day:
                    day[key] = self._ensure_list_of_dicts(day[key], key_name="name" if key!="transportation" else "description")
        return day_plans
    
    def _create_single_day_journey_plans(self, origin: str, final_destination: str,
                                        start_date: date, duration: int,
                                        research_data: Dict[str, Any],
                                        preferences: Dict[str, Any],
                                        travel_mode: str) -> List[Dict[str, Any]]:
        """Create single-day journey plans for shorter routes."""
        day_plans = []
        
        # Day 1: Travel to destination
        travel_day = {
            "day_number": 1,
            "date": start_date.isoformat(),
            "day_of_week": start_date.strftime("%A"),
            "type": "travel",
            "activities": [
                {
                    "name": f"Travel from {origin} to {final_destination}",
                    "description": f"Journey from {origin} to {final_destination}",
                    "duration_hours": 4.0,
                    "location": f"{origin} to {final_destination}"
                }
            ],
            "transportation": [
                {
                    "from": origin,
                    "to": final_destination,
                    "mode": travel_mode,
                    "duration_hours": 4.0,
                    "description": f"Direct travel to {final_destination}"
                }
            ],
            "accommodations": [],
            "restaurants": [],
            "notes": f"Travel day from {origin} to {final_destination}. Arrive and settle in."
        }
        
        day_plans.append(travel_day)
        
        # Remaining days: Explore destination
        for i in range(2, duration + 1):
            current_date = start_date + timedelta(days=i-1)
            
            # Get activities from research data
            activities = research_data.get("attractions", [])
            restaurants = research_data.get("restaurants", [])
            accommodations = research_data.get("accommodations", [])
            
            # Select activities for this day
            day_activities = self._select_activities_for_day(activities, preferences, current_date)
            day_restaurants = self._select_restaurants_for_day(restaurants, preferences, current_date)
            day_accommodation = self._select_accommodation_for_day(accommodations, preferences, current_date)
            
            destination_day = {
                "day_number": i,
                "date": current_date.isoformat(),
                "day_of_week": current_date.strftime("%A"),
                "type": "exploration",
                "activities": day_activities,
                "transportation": [
                    {
                        "from": "Local area",
                        "to": "Local area",
                        "mode": "walking",
                        "duration_hours": 0.5,
                        "description": "Local exploration"
                    }
                ],
                "accommodations": [day_accommodation] if day_accommodation else [],
                "restaurants": day_restaurants,
                "notes": f"Explore {final_destination} and enjoy local attractions."
            }
            
            day_plans.append(destination_day)
        
        # Ensure all fields are lists of dicts
        for day in day_plans:
            for key in ["activities", "accommodations", "restaurants", "transportation"]:
                if key in day:
                    day[key] = self._ensure_list_of_dicts(day[key], key_name="name" if key!="transportation" else "description")
        return day_plans
    
    def _create_destination_day_plans(self, destination: str, start_date: date, 
                                     end_date: date, research_data: Dict[str, Any],
                                     preferences: Dict[str, Any], duration: int) -> List[Dict[str, Any]]:
        """Create day plans for a single destination (existing logic)."""
        # Get activities and restaurants from research data
        activities = research_data.get("attractions", [])
        restaurants = research_data.get("restaurants", [])
        accommodations = research_data.get("accommodations", [])
        
        # Cluster activities by geographic location
        from utils.geographic_utils import GeographicUtils
        clusters = GeographicUtils.cluster_activities_by_location(activities)
        
        # Assign restaurants to clusters
        clusters = GeographicUtils.cluster_restaurants_by_location(restaurants, clusters)
        
        # Create day plans based on geographic clusters
        day_plans = GeographicUtils.create_geographic_day_plans(
            clusters, duration, max_activities_per_day=4
        )
        
        # Add accommodation recommendations to day plans
        day_plans = self._add_accommodation_recommendations(day_plans, accommodations, clusters)
        
        # Ensure each day plan has accommodations field for frontend compatibility
        for day_plan in day_plans:
            if "recommended_accommodation" in day_plan:
                day_plan["accommodations"] = [day_plan["recommended_accommodation"]]
            else:
                day_plan["accommodations"] = []
        
        # Ensure all fields are lists of dicts
        for day in day_plans:
            for key in ["activities", "accommodations", "restaurants", "transportation"]:
                if key in day:
                    day[key] = self._ensure_list_of_dicts(day[key], key_name="name" if key!="transportation" else "description")
        return day_plans
    
    def _create_fallback_day_plans(self, origin: str, destination: str, 
                                  start_date: date, duration: int) -> List[Dict[str, Any]]:
        """Create fallback day plans when route planning fails."""
        day_plans = []
        
        for i in range(1, duration + 1):
            current_date = start_date + timedelta(days=i-1)
            
            if i == 1:
                # Day 1: Departure
                day_plan = {
                    "day_number": i,
                    "date": current_date.isoformat(),
                    "day_of_week": current_date.strftime("%A"),
                    "type": "departure",
                    "activities": [
                        {
                            "name": f"Depart from {origin}",
                            "description": f"Start your journey from {origin}",
                            "duration_hours": 1.0,
                            "location": origin
                        }
                    ],
                    "transportation": [
                        {
                            "from": origin,
                            "to": destination,
                            "mode": "car",
                            "duration_hours": 4.0,
                            "description": f"Travel to {destination}"
                        }
                    ],
                    "accommodations": [],
                    "restaurants": [],
                    "notes": f"Departure day from {origin} to {destination}"
                }
            elif i == duration:
                # Final day: Return
                day_plan = {
                    "day_number": i,
                    "date": current_date.isoformat(),
                    "day_of_week": current_date.strftime("%A"),
                    "type": "return",
                    "activities": [
                        {
                            "name": f"Return to {origin}",
                            "description": f"Return journey to {origin}",
                            "duration_hours": 1.0,
                            "location": destination
                        }
                    ],
                    "transportation": [
                        {
                            "from": destination,
                            "to": origin,
                            "mode": "car",
                            "duration_hours": 4.0,
                            "description": f"Return to {origin}"
                        }
                    ],
                    "accommodations": [],
                    "restaurants": [],
                    "notes": f"Return day from {destination} to {origin}"
                }
            else:
                # Middle days: Explore destination
                day_plan = {
                    "day_number": i,
                    "date": current_date.isoformat(),
                    "day_of_week": current_date.strftime("%A"),
                    "type": "exploration",
                    "activities": [
                        {
                            "name": f"Explore {destination}",
                            "description": f"Discover attractions in {destination}",
                            "duration_hours": 6.0,
                            "location": destination
                        }
                    ],
                    "transportation": [
                        {
                            "from": "Local area",
                            "to": "Local area",
                            "mode": "walking",
                            "duration_hours": 0.5,
                            "description": "Local exploration"
                        }
                    ],
                    "accommodations": [],
                    "restaurants": [],
                    "notes": f"Explore {destination} and enjoy local attractions."
                }
            
            day_plans.append(day_plan)
        
        # Ensure all fields are lists of dicts
        for day in day_plans:
            for key in ["activities", "accommodations", "restaurants", "transportation"]:
                if key in day:
                    day[key] = self._ensure_list_of_dicts(day[key], key_name="name" if key!="transportation" else "description")
        return day_plans
    
    def _calculate_distance(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers."""
        import math
        
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _select_travel_mode(self, distance: float, preferences: Dict[str, Any]) -> str:
        """Select appropriate travel mode based on distance and preferences."""
        if distance < 100:
            return "car"
        elif distance < 500:
            return "car"  # Still car for medium distances
        else:
            return "car"  # Default to car for road trips
    
    def _calculate_travel_duration(self, distance: float, mode: str) -> float:
        """Calculate travel duration in hours."""
        speeds = {
            "car": 80,  # km/h average
            "plane": 800,
            "train": 120,
            "bus": 70
        }
        
        speed = speeds.get(mode, 80)
        return distance / speed
    
    def _select_accommodation_for_day(self, accommodations: List[Dict[str, Any]], 
                                    preferences: Dict[str, Any], 
                                    day_date: date) -> Optional[Dict[str, Any]]:
        """Select accommodation for a specific day."""
        if not accommodations:
            return None
        
        # Simple selection - take the first available
        return accommodations[0] if accommodations else None
    
    def _plan_transportation_for_cluster(self, activities: List[Dict[str, Any]], cluster_name: str) -> List[Dict[str, Any]]:
        """Plan transportation within a geographic cluster, always returning a list of dicts."""
        if not activities:
            return [{
                "mode": "walking",
                "from": cluster_name,
                "to": cluster_name,
                "description": "Walking around the area"
            }]
        if len(activities) == 1:
            return [{
                "mode": "walking",
                "from": cluster_name,
                "to": activities[0].get("name", cluster_name),
                "description": "Walking to the attraction"
            }]
        transportation_plan = []
        for i in range(len(activities) - 1):
            loc1 = activities[i].get("location", {})
            loc2 = activities[i + 1].get("location", {})
            name1 = activities[i].get("name", f"Activity {i+1}")
            name2 = activities[i+1].get("name", f"Activity {i+2}")
            if (loc1.get("latitude") and loc1.get("longitude") and loc2.get("latitude") and loc2.get("longitude")):
                distance = GeographicUtils.calculate_distance(
                    loc1["latitude"], loc1["longitude"],
                    loc2["latitude"], loc2["longitude"]
                )
                if distance <= 1.0:
                    mode = "walking"
                    description = f"Walking from {name1} to {name2} ({distance:.1f}km)"
                elif distance <= 5.0:
                    mode = "taxi_or_transit"
                    description = f"Short taxi ride or public transit from {name1} to {name2} ({distance:.1f}km)"
                else:
                    mode = "car"
                    description = f"Car or longer taxi ride from {name1} to {name2} ({distance:.1f}km)"
                transportation_plan.append({
                    "mode": mode,
                    "from": name1,
                    "to": name2,
                    "distance_km": distance,
                    "description": description
                })
            else:
                transportation_plan.append({
                    "mode": "unknown",
                    "from": name1,
                    "to": name2,
                    "description": f"Travel from {name1} to {name2} (distance unknown)"
                })
        if not transportation_plan:
            transportation_plan.append({
                "mode": "walking",
                "from": cluster_name,
                "to": cluster_name,
                "description": "Walking and public transit"
            })
        return transportation_plan
    
    def _add_accommodation_recommendations(self, day_plans: List[Dict[str, Any]], 
                                         accommodations: List[Dict[str, Any]], 
                                         clusters: List[LocationCluster]) -> List[Dict[str, Any]]:
        """Add accommodation recommendations to day plans based on geographic proximity"""
        
        if not accommodations:
            return day_plans
        
        for day_plan in day_plans:
            # Find the best accommodation for this day's activities
            best_accommodation = self._find_best_accommodation_for_day(
                day_plan, accommodations, clusters
            )
            
            if best_accommodation:
                day_plan["recommended_accommodation"] = best_accommodation
        
        return day_plans
    
    def _find_best_accommodation_for_day(self, day_plan: Dict[str, Any], 
                                       accommodations: List[Dict[str, Any]], 
                                       clusters: List[LocationCluster]) -> Optional[Dict[str, Any]]:
        """Find the best accommodation for a specific day's activities"""
        
        if not day_plan.get("activities"):
            return None
        
        # Get the geographic area for this day
        geographic_area = day_plan.get("geographic_area", {})
        center_lat = geographic_area.get("center_lat")
        center_lng = geographic_area.get("center_lng")
        
        if not center_lat or not center_lng:
            return None
        
        # Find accommodation closest to the day's activities
        best_accommodation = None
        min_distance = float('inf')
        
        for accommodation in accommodations:
            location = accommodation.get("location", {})
            if not location.get("latitude") or not location.get("longitude"):
                continue
            
            distance = GeographicUtils.calculate_distance(
                center_lat, center_lng,
                location["latitude"], location["longitude"]
            )
            
            # Prefer accommodations within 10km of activities
            if distance < min_distance and distance <= 10:
                min_distance = distance
                best_accommodation = accommodation
        
        # If no nearby accommodation found, pick the first one
        if not best_accommodation and accommodations:
            best_accommodation = accommodations[0]
        
        return best_accommodation
    
    def _select_activities_for_day(self, attractions: List[Dict[str, Any]], 
                                 preferences: Dict[str, Any], 
                                 day_date: date) -> List[Dict[str, Any]]:
        """Select appropriate activities for a specific day"""
        
        # Filter activities based on preferences
        preferred_types = [t.value for t in preferences.get("activity_types", [])]
        
        # Create varied daily itineraries by using day-specific selection
        selected = []
        total_duration = 0
        max_daily_duration = 8  # hours
        
        # Use day of week to create variety
        day_of_week = day_date.weekday()
        
        # Different activity focus for different days
        day_focus = {
            0: ["museum", "cultural", "indoor"],  # Monday - quieter activities
            1: ["outdoor", "adventure", "nature"],  # Tuesday - active day
            2: ["shopping", "entertainment", "nightlife"],  # Wednesday - social day
            3: ["historical", "educational", "museum"],  # Thursday - learning day
            4: ["outdoor", "recreation", "sports"],  # Friday - active day
            5: ["entertainment", "nightlife", "shopping"],  # Saturday - weekend fun
            6: ["relaxation", "spa", "outdoor"]  # Sunday - chill day
        }
        
        # Get day-specific preferred types
        day_preferred_types = day_focus.get(day_of_week, preferred_types)
        
        # Shuffle attractions to avoid always picking the same ones
        import random
        shuffled_attractions = list(attractions)
        random.seed(hash(day_date))  # Use date as seed for consistent but varied selection
        random.shuffle(shuffled_attractions)
        
        # First pass: try to get day-specific activities
        for attraction in shuffled_attractions:
            if isinstance(attraction, dict):
                activity_type = attraction.get("type", "unknown")
                duration = attraction.get("duration_hours", 1)
                name = attraction.get("name", "Unknown")
            else:
                activity_type = attraction.type.value
                duration = attraction.duration_hours
                name = attraction.name
            
            # Prioritize day-specific activities
            if (activity_type in day_preferred_types and 
                total_duration + duration <= max_daily_duration and
                name not in [act.get("name", "") for act in selected]):
                selected.append(attraction)
                total_duration += duration
                
                if len(selected) >= 3:  # Limit to 3 activities per day
                    break
        
        # Second pass: fill remaining slots with any preferred activities
        if len(selected) < 3:
            for attraction in shuffled_attractions:
                if isinstance(attraction, dict):
                    activity_type = attraction.get("type", "unknown")
                    duration = attraction.get("duration_hours", 1)
                    name = attraction.get("name", "Unknown")
                else:
                    activity_type = attraction.type.value
                    duration = attraction.duration_hours
                    name = attraction.name
                
                if (activity_type in preferred_types and 
                    total_duration + duration <= max_daily_duration and
                    name not in [act.get("name", "") for act in selected]):
                    selected.append(attraction)
                    total_duration += duration
                    
                    if len(selected) >= 3:
                        break
        
        return selected
    
    def _select_restaurants_for_day(self, restaurants: List[Any], 
                                  preferences: Dict[str, Any], 
                                  day_date: date) -> List[Dict[str, Any]]:
        """Select restaurants for a specific day"""
        
        selected = []
        
        # Ensure we always have some restaurants, even if the list is empty
        if not restaurants:
            # Create default restaurants if none are available
            restaurants = [
                {
                    "name": "Local Cafe",
                    "cuisine": "local",
                    "price_level": 2,
                    "rating": 4.0,
                    "cost_per_person": 25.0
                },
                {
                    "name": "Regional Restaurant", 
                    "cuisine": "regional",
                    "price_level": 3,
                    "rating": 4.2,
                    "cost_per_person": 35.0
                },
                {
                    "name": "Casual Dining",
                    "cuisine": "casual",
                    "price_level": 2,
                    "rating": 3.8,
                    "cost_per_person": 20.0
                }
            ]
        
        # Use day of week to create variety in dining
        day_of_week = day_date.weekday()
        
        # Different cuisine focus for different days
        day_cuisine_focus = {
            0: ["local", "comfort"],  # Monday - comfort food
            1: ["international", "asian"],  # Tuesday - try something new
            2: ["italian", "mediterranean"],  # Wednesday - midweek treat
            3: ["local", "seafood"],  # Thursday - fresh seafood
            4: ["mexican", "latin"],  # Friday - fun Friday food
            5: ["fine_dining", "steakhouse"],  # Saturday - special dining
            6: ["brunch", "casual"]  # Sunday - relaxed dining
        }
        
        # Get day-specific cuisine preferences
        day_cuisines = day_cuisine_focus.get(day_of_week, ["local"])
        
        # Shuffle restaurants for variety
        import random
        shuffled_restaurants = list(restaurants)
        random.seed(hash(day_date))  # Use date as seed for consistent but varied selection
        random.shuffle(shuffled_restaurants)
        
        # Select 2-3 restaurants per day, prioritizing day-specific cuisines
        selected_count = 0
        max_restaurants = 3
        
        # First pass: try to get day-specific cuisines
        for restaurant in shuffled_restaurants:
            if selected_count >= max_restaurants:
                break
                
            # Convert to dictionary format
            restaurant_dict = {
                "name": restaurant.get("name", f"Restaurant {selected_count+1}"),
                "location": restaurant.get("location", {}),
                "cuisine_type": restaurant.get("cuisine", "Local"),
                "price_level": restaurant.get("price_level", 2),
                "rating": restaurant.get("rating", 4.0),
                "cost_per_person": restaurant.get("cost_per_person", 30.0)
            }
            
            # Check if this restaurant matches day preferences
            cuisine_matches = any(cuisine in restaurant_dict["cuisine_type"].lower() 
                                for cuisine in day_cuisines)
            
            # Also check if we haven't already selected this restaurant
            name_not_selected = restaurant_dict["name"] not in [r.get("name", "") for r in selected]
            
            if cuisine_matches and name_not_selected:
                selected.append(restaurant_dict)
                selected_count += 1
        
        # Second pass: fill remaining slots with any restaurants
        for restaurant in shuffled_restaurants:
            if selected_count >= max_restaurants:
                break
                
            restaurant_dict = {
                "name": restaurant.get("name", f"Restaurant {selected_count+1}"),
                "location": restaurant.get("location", {}),
                "cuisine_type": restaurant.get("cuisine", "Local"),
                "price_level": restaurant.get("price_level", 2),
                "rating": restaurant.get("rating", 4.0),
                "cost_per_person": restaurant.get("cost_per_person", 30.0)
            }
            
            # Check if we haven't already selected this restaurant
            if restaurant_dict["name"] not in [r.get("name", "") for r in selected]:
                selected.append(restaurant_dict)
                selected_count += 1
        
        # Ensure we always return at least 2 restaurants
        if len(selected) < 2:
            # Add default restaurants if we don't have enough
            default_restaurants = [
                {
                    "name": "Local Cafe",
                    "cuisine_type": "Local",
                    "price_level": 2,
                    "rating": 4.0,
                    "cost_per_person": 25.0
                },
                {
                    "name": "Regional Restaurant",
                    "cuisine_type": "Regional", 
                    "price_level": 3,
                    "rating": 4.2,
                    "cost_per_person": 35.0
                }
            ]
            
            for default_rest in default_restaurants:
                if default_rest["name"] not in [r.get("name", "") for r in selected]:
                    selected.append(default_rest)
                    if len(selected) >= 2:
                        break
        
        return selected
    
    def _extract_destinations_from_preferences(self, preferences: Dict[str, Any]) -> List[str]:
        """Extract destination list from preferences."""
        # Check if there's a specific destinations list
        if "destinations" in preferences:
            return preferences["destinations"]
        
        # Check if there's a route specified
        if "route" in preferences:
            route = preferences["route"]
            if isinstance(route, str):
                # Parse route like "San Francisco to Los Angeles via Big Sur"
                destinations = []
                parts = route.lower().split()
                
                # More sophisticated parsing for multi-destination routes
                current_destination = []
                for i, part in enumerate(parts):
                    if part in ["to", "via", "through"] and i > 0 and i < len(parts) - 1:
                        # Add the destination before the connector
                        if current_destination:
                            destinations.append(" ".join(current_destination))
                            current_destination = []
                    else:
                        current_destination.append(part)
                
                # Add the final destination
                if current_destination:
                    destinations.append(" ".join(current_destination))
                
                # If no destinations found, use the original route
                if not destinations:
                    destinations = [route]
                
                return destinations
        
        # Default to single destination
        destination = preferences.get("destination", "Unknown")
        
        # Handle comma-separated destinations (e.g., "Big Sur, solvang")
        if "," in destination:
            # Split by comma and clean up
            destinations = [dest.strip() for dest in destination.split(",")]
            # If it looks like a single destination with descriptive text, keep as one
            if len(destinations) == 2 and len(destinations[1]) < 20:
                # This is likely a single destination with additional context
                return [destination]
            return destinations
        
        return [destination]
    
    def _plan_transportation(self, destination: str, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Plan transportation between activities, always returning a list of dicts."""
        if not activities:
            return [{
                "mode": "walking",
                "from": destination,
                "to": destination,
                "description": "Walking around the city"
            }]
        transport_options = []
        if len(activities) > 1:
            transport_options.append({
                "mode": "public_transit",
                "from": activities[0].get("name", destination),
                "to": activities[-1].get("name", destination),
                "description": "Public transit between attractions"
            })
        # Check for outdoor activities
        outdoor_activities = False
        for act in activities:
            if isinstance(act, dict):
                if act.get("type") == "outdoor":
                    outdoor_activities = True
                    break
            else:
                if act.type == ActivityType.OUTDOOR:
                    outdoor_activities = True
                    break
        if outdoor_activities:
            transport_options.append({
                "mode": "walking",
                "from": activities[0].get("name", destination),
                "to": activities[-1].get("name", destination),
                "description": "Walking for outdoor activities"
            })
        if not transport_options:
            transport_options.append({
                "mode": "walking",
                "from": destination,
                "to": destination,
                "description": "Walking and public transit"
            })
        return transport_options
    
    def _generate_day_notes(self, day_date: date, activities: List[Dict[str, Any]], 
                           preferences: Dict[str, Any]) -> str:
        """Generate notes for the day"""
        
        if not activities:
            return "Free day to explore the destination at your own pace."
        
        day_of_week = day_date.weekday()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[day_of_week]
        
        activity_names = []
        activity_types = []
        
        for act in activities:
            if isinstance(act, dict):
                activity_names.append(act.get("name", "Unknown activity"))
                activity_types.append(act.get("type", "unknown"))
            else:
                activity_names.append(act.name)
                activity_types.append(act.type.value)
        
        # Create day-specific notes
        notes = f"{day_name}, {day_date.strftime('%B %d')}: "
        
        # Add activity-specific notes
        if "museum" in activity_types or "cultural" in activity_types:
            notes += "Cultural exploration day with museum visits. "
        elif "outdoor" in activity_types or "adventure" in activity_types:
            notes += "Active outdoor adventure day. "
        elif "shopping" in activity_types or "entertainment" in activity_types:
            notes += "Fun day with shopping and entertainment. "
        elif "historical" in activity_types or "educational" in activity_types:
            notes += "Educational day exploring historical sites. "
        elif "relaxation" in activity_types or "spa" in activity_types:
            notes += "Relaxing day with spa and wellness activities. "
        else:
            notes += f"Explore {', '.join(activity_names)}. "
        
        # Add time-specific recommendations
        if day_of_week in [5, 6]:  # Weekend
            notes += "Weekend activities - expect larger crowds at popular attractions. "
        elif day_of_week == 0:  # Monday
            notes += "Monday activities - some attractions may have reduced hours. "
        
        # Add weather considerations
        if "outdoor" in activity_types:
            notes += "Check weather forecast for outdoor activities. "
        
        # Add family considerations
        if preferences.get("children", False):
            notes += "Family-friendly activities included. "
        
        # Add dietary considerations
        if preferences.get("dietary_restrictions", []):
            restrictions = ', '.join(preferences.get('dietary_restrictions', []))
            notes += f"Remember dietary restrictions: {restrictions}. "
        
        # Add budget tips
        budget_level = preferences.get("budget_level", "moderate")
        if budget_level == "budget":
            notes += "Budget-friendly options selected. "
        elif budget_level == "luxury":
            notes += "Premium experiences included. "
        
        return notes
    
    def _optimize_schedule(self, state: PlanningState) -> PlanningState:
        """Optimize the schedule for better flow and geographic efficiency"""
        try:
            day_plans = state.day_plans
            preferences = state.preferences
            geographic_validation = getattr(state, 'geographic_validation', {})
            
            # Use LLM to optimize the schedule
            system_prompt = """
            You are a travel planning expert. Optimize the daily schedule for better flow and geographic efficiency.
            Consider:
            - Logical order of activities within geographic clusters
            - Travel time between locations (already calculated)
            - Rest periods and meal times
            - Weather considerations
            - Crowd levels at attractions
            - Geographic efficiency (activities are already clustered by location)
            
            Provide optimization suggestions for each day.
            """
            
            schedule_data = {
                "day_plans": [
                    {
                        "date": plan.get("date", ""),
                        "cluster_name": plan.get("cluster_name", ""),
                        "activities": [act.get("name", "") for act in plan.get("activities", [])],
                        "restaurants": [rest.get("name", "") for rest in plan.get("restaurants", [])],
                        "travel_time_minutes": plan.get("travel_time_minutes", 0)
                    }
                    for plan in day_plans
                ],
                "preferences": {
                    "activity_types": [t.value for t in preferences.get("activity_types", [])],
                    "budget_level": preferences.get("budget_level", "medium")
                },
                "geographic_validation": geographic_validation
            }
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Optimize schedule: {schedule_data}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Apply optimizations (simplified)
            optimized_plans = self._apply_schedule_optimizations(day_plans, response.content)
            
            # Add transportation plans to each day
            for day_plan in optimized_plans:
                activities = day_plan.get("activities", [])
                cluster_name = day_plan.get("cluster_name", "Unknown area")
                day_plan["transportation"] = self._plan_transportation_for_cluster(activities, cluster_name)
            
            # Update state
            state_dict = state.model_dump()
            state_dict["day_plans"] = optimized_plans
            state_dict["optimization_notes"] = response.content
            
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error optimizing schedule: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def _apply_schedule_optimizations(self, day_plans: List[Dict[str, Any]], 
                                    optimization_notes: str) -> List[Dict[str, Any]]:
        """Apply schedule optimizations based on LLM suggestions"""
        
        # For now, return the original plans
        # In production, this would parse the LLM response and apply specific changes
        return day_plans
    
    def _calculate_costs(self, state: PlanningState) -> PlanningState:
        """Calculate costs for the entire itinerary"""
        try:
            day_plans = state.day_plans
            preferences = state.preferences
            destination = state.destination
            start_date = datetime.fromisoformat(state.start_date).date()
            end_date = datetime.fromisoformat(state.end_date).date()
            duration = (end_date - start_date).days + 1
            
            # Extract all activities and restaurants
            all_activities = []
            all_restaurants = []
            
            for day_plan in day_plans:
                all_activities.extend(day_plan.get("activities", []))
                all_restaurants.extend(day_plan.get("restaurants", []))
            
            # Convert dictionaries to proper objects for cost calculation
            from models.travel_models import Activity, Restaurant, Accommodation, BudgetLevel, AccommodationType
            
            # Convert activities
            activity_objects = []
            for act in all_activities:
                if isinstance(act, dict):
                    # Create a proper location object
                    location_data = act.get("location", {})
                    location = Location(
                        name=location_data.get("name", act.get("name", "Unknown")),
                        address=location_data.get("address", "Address not available"),
                        latitude=location_data.get("latitude"),
                        longitude=location_data.get("longitude"),
                        place_id=location_data.get("place_id"),
                        rating=location_data.get("rating"),
                        price_level=location_data.get("price_level")
                    )
                    
                    activity_objects.append(Activity(
                        name=act.get("name", "Unknown"),
                        description=act.get("description", ""),
                        location=location,
                        type=act.get("type", "cultural"),
                        duration_hours=act.get("duration_hours", 1),
                        cost=act.get("cost", 0)
                    ))
                elif isinstance(act, str):
                    # Handle string activities by creating a basic activity object
                    location = Location(
                        name=act,
                        address="Address not available",
                        latitude=None,
                        longitude=None
                    )
                    
                    activity_objects.append(Activity(
                        name=act,
                        description=f"Visit {act}",
                        location=location,
                        type="cultural",
                        duration_hours=2,
                        cost=0
                    ))
                else:
                    # Skip invalid activities
                    logger.warning(f"Skipping invalid activity: {act}")
                    continue
            
            # Convert restaurants
            restaurant_objects = []
            for rest in all_restaurants:
                if isinstance(rest, dict):
                    # Create a proper location object
                    location_data = rest.get("location", {})
                    location = Location(
                        name=location_data.get("name", rest.get("name", "Unknown")),
                        address=location_data.get("address", "Address not available"),
                        latitude=location_data.get("latitude"),
                        longitude=location_data.get("longitude"),
                        place_id=location_data.get("place_id"),
                        rating=location_data.get("rating"),
                        price_level=location_data.get("price_level")
                    )
                    
                    restaurant_objects.append(Restaurant(
                        name=rest.get("name", "Unknown"),
                        cuisine_type=rest.get("cuisine_type", "Local"),
                        location=location,
                        price_level=rest.get("price_level", 2),
                        rating=rest.get("rating", 4.0),
                        cost_per_person=rest.get("cost_per_person", 30.0)
                    ))
                elif isinstance(rest, str):
                    # Handle string restaurants by creating a basic restaurant object
                    location = Location(
                        name=rest,
                        address="Address not available",
                        latitude=None,
                        longitude=None
                    )
                    
                    restaurant_objects.append(Restaurant(
                        name=rest,
                        cuisine_type="Local",
                        location=location,
                        price_level=2,
                        rating=4.0,
                        cost_per_person=30.0
                    ))
                else:
                    # Skip invalid restaurants
                    logger.warning(f"Skipping invalid restaurant: {rest}")
                    continue
            
            # Get budget level
            budget_level = BudgetLevel.MODERATE
            if preferences.get("budget_level") == "budget":
                budget_level = BudgetLevel.BUDGET
            elif preferences.get("budget_level") == "luxury":
                budget_level = BudgetLevel.LUXURY
            
            # Use the CostEstimator for proper calculations
            cost_estimator = CostEstimator()
            
            # Estimate accommodation costs (assuming hotel for now)
            accommodation_cost = cost_estimator.estimate_accommodation_cost(
                AccommodationType.HOTEL, budget_level, destination, duration
            )
            
            # Estimate activity costs
            activity_cost = cost_estimator.estimate_activity_costs(
                activity_objects, budget_level, destination
            )
            
            # Estimate dining costs
            dining_cost = cost_estimator.estimate_dining_costs(
                restaurant_objects, budget_level, destination, duration
            )
            
            # Calculate transportation costs from day plans
            total_transportation_cost = 0
            for day_plan in day_plans:
                # Add inter-city transportation cost
                total_transportation_cost += day_plan.get("transportation_cost", 0)
                # Add local transportation cost
                total_transportation_cost += day_plan.get("local_transportation_cost", 0)
            
            # If no transportation costs calculated, use estimator
            if total_transportation_cost == 0:
                transportation_cost = cost_estimator.estimate_transportation_costs(
                    destination, duration, budget_level
                )
            else:
                transportation_cost = total_transportation_cost
            
            # Estimate miscellaneous costs
            misc_cost = cost_estimator.estimate_miscellaneous_costs(budget_level, duration)
            
            # Calculate total
            total_cost = accommodation_cost + activity_cost + dining_cost + transportation_cost + misc_cost
            
            cost_breakdown = {
                "accommodations": accommodation_cost,
                "activities": activity_cost,
                "restaurants": dining_cost,
                "transportation": transportation_cost,
                "miscellaneous": misc_cost,
                "total": total_cost
            }
            
            # Update state
            state_dict = state.model_dump()
            state_dict["budget_analysis"] = {
                "cost_breakdown": cost_breakdown,
                "total_cost": total_cost,
                "daily_average": total_cost / duration,
                "budget_status": "within_budget" if total_cost <= preferences.get("max_daily_budget", 100) * duration else "over_budget"
            }
            
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error calculating costs: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def _finalize_itinerary(self, state: PlanningState) -> PlanningState:
        """Finalize the complete itinerary"""
        try:
            # Create the final itinerary as dictionary
            itinerary = {
                "destination": state.destination,
                "start_date": state.start_date,
                "end_date": state.end_date,
                "total_budget": state.preferences.get("max_daily_budget", 100) * state.budget_analysis.get("daily_average", 0),
                "preferences": state.preferences,
                "day_plans": state.day_plans,
                "total_cost": state.budget_analysis.get("total_cost", 0),
                "cost_breakdown": state.budget_analysis.get("cost_breakdown", {})
            }
            
            # Update state
            state_dict = state.model_dump()
            state_dict["itinerary"] = itinerary
            state_dict["planning_complete"] = True
            
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error finalizing itinerary: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def create_itinerary(self, destination: str, start_date: str, end_date: str,
                        preferences: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to create a complete itinerary"""
        try:
            initial_state = PlanningState(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                preferences=preferences,
                research_data=research_data,
                day_plans=[],
                itinerary={},
                budget_analysis={},
                planning_complete=False,
                error=""
            )
            
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Handle both dict and Pydantic model returns
            if hasattr(final_state, 'planning_complete'):
                if final_state.planning_complete:
                    return final_state.itinerary
                else:
                    raise Exception(f"Planning failed: {final_state.error}")
            else:
                # Handle dict return
                if final_state.get("planning_complete", False):
                    return final_state.get("itinerary")
                else:
                    raise Exception(f"Planning failed: {final_state.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in planning workflow: {e}")
            raise

    def _distribute_day_plans_by_route(self, day_plans: List[Dict[str, Any]], 
                                     optimized_route: Dict[str, Any], 
                                     preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Distribute day plans based on the optimized route to ensure logical geographic flow.
        
        Args:
            day_plans: List of day plans
            optimized_route: Optimized route information
            preferences: User preferences
            
        Returns:
            Updated day plans with proper destination distribution
        """
        try:
            if not optimized_route or "route" not in optimized_route:
                return day_plans
            
            route = optimized_route["route"]
            if len(route) <= 2:  # Only starting point and one destination
                return day_plans
            
            # For multi-destination trips, distribute days based on route
            destinations = route[1:-1]  # Exclude starting point and return
            num_destinations = len(destinations)
            num_days = len(day_plans)
            
            if num_destinations == 0 or num_days == 0:
                return day_plans
            
            # Calculate days per destination
            days_per_destination = num_days // num_destinations
            extra_days = num_days % num_destinations
            
            # Distribute days
            current_day = 0
            updated_day_plans = []
            
            for i, destination in enumerate(destinations):
                # Calculate days for this destination
                dest_days = days_per_destination + (1 if i < extra_days else 0)
                
                # Update day plans for this destination
                for j in range(dest_days):
                    if current_day < len(day_plans):
                        day_plan = day_plans[current_day].copy()
                        
                        # Update destination information
                        day_plan["destination"] = destination
                        day_plan["route_notes"] = f"Day {current_day + 1} in {destination}"
                        
                        # Add route context
                        if i > 0:  # Not the first destination
                            day_plan["travel_from"] = destinations[i - 1]
                        if i < len(destinations) - 1:  # Not the last destination
                            day_plan["travel_to"] = destinations[i + 1]
                        
                        updated_day_plans.append(day_plan)
                        current_day += 1
            
            # Add any remaining days to the last destination
            while current_day < len(day_plans):
                if updated_day_plans:
                    day_plan = day_plans[current_day].copy()
                    day_plan["destination"] = destinations[-1]
                    day_plan["route_notes"] = f"Additional day in {destinations[-1]}"
                    updated_day_plans.append(day_plan)
                current_day += 1
            
            return updated_day_plans
            
        except Exception as e:
            logger.error(f"Error distributing day plans by route: {e}")
            return day_plans 