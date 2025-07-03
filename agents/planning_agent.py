import os
from typing import Dict, List, Any, Optional
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
        """Create day-by-day plans based on geographic clustering"""
        try:
            destination = state.destination
            start_date = datetime.fromisoformat(state.start_date).date()
            end_date = datetime.fromisoformat(state.end_date).date()
            research_data = state.research_data
            preferences = state.preferences
            
            # Calculate trip duration
            duration = (end_date - start_date).days + 1
            
            # Get activities and restaurants from research data
            activities = research_data.get("attractions", [])
            restaurants = research_data.get("restaurants", [])
            
            # Cluster activities by geographic location
            clusters = GeographicUtils.cluster_activities_by_location(activities)
            
            # Assign restaurants to clusters
            clusters = GeographicUtils.cluster_restaurants_by_location(restaurants, clusters)
            
            # Create day plans based on geographic clusters
            day_plans = GeographicUtils.create_geographic_day_plans(
                clusters, duration, max_activities_per_day=4
            )
            
            # Add accommodation recommendations to day plans
            accommodations = research_data.get("accommodations", [])
            day_plans = self._add_accommodation_recommendations(day_plans, accommodations, clusters)
            
            # Ensure each day plan has accommodations field for frontend compatibility
            for day_plan in day_plans:
                if "recommended_accommodation" in day_plan:
                    day_plan["accommodations"] = [day_plan["recommended_accommodation"]]
                else:
                    day_plan["accommodations"] = []
            
            # Add date information to each day plan
            for i, day_plan in enumerate(day_plans):
                current_date = start_date + timedelta(days=i)
                day_plan["date"] = current_date.isoformat()
                day_plan["day_of_week"] = current_date.strftime("%A")
            
            # Plan inter-city transportation if multiple destinations
            destinations = self._extract_destinations_from_preferences(preferences)
            if len(destinations) > 1:
                travel_days = self.transportation_planner.plan_inter_city_travel(
                    destinations, state.start_date, state.end_date, preferences
                )
                # Adjust day plans for travel days
                day_plans = self.transportation_planner.adjust_day_plans_for_travel(day_plans, travel_days)
            
            # Add local transportation planning for each day
            for day_plan in day_plans:
                activities = day_plan.get("activities", [])
                cluster_name = day_plan.get("cluster_name", "Unknown")
                
                # Plan local transportation within the cluster
                local_transport = self.transportation_planner.plan_local_transportation(activities, cluster_name)
                
                # Add transportation information to day plan
                if local_transport:
                    day_plan["local_transportation"] = [
                        {
                            "from": leg.from_location,
                            "to": leg.to_location,
                            "mode": leg.mode,
                            "duration_minutes": leg.duration_minutes,
                            "cost_per_person": leg.cost_per_person,
                            "notes": leg.notes
                        }
                        for leg in local_transport
                    ]
                    
                    # Update total travel time
                    total_local_time = sum(leg.duration_minutes for leg in local_transport)
                    day_plan["travel_time_minutes"] = day_plan.get("travel_time_minutes", 0) + total_local_time
                    
                    # Update transportation cost
                    total_local_cost = sum(leg.cost_per_person for leg in local_transport) * preferences.get("group_size", 2)
                    day_plan["local_transportation_cost"] = total_local_cost
                
                # --- Time Management Integration ---
                # Build travel legs in the format expected by TimeManager
                travel_legs = day_plan.get("local_transportation", [])
                # Generate a time-aware schedule
                schedule = self.time_manager.create_realistic_schedule(activities, travel_legs, preferences)
                # Store schedule and validation in the day plan
                day_plan["time_slots"] = [slot.__dict__ for slot in schedule.time_slots]
                day_plan["schedule_validation"] = self.time_manager.validate_schedule(schedule)
            
            # Validate the geographic logic
            validation = GeographicUtils.validate_itinerary_geography(day_plans)
            
            # Update state
            state_dict = state.model_dump()
            state_dict["day_plans"] = day_plans
            state_dict["geographic_validation"] = validation
            return PlanningState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error creating day plans: {e}")
            state_dict = state.model_dump()
            state_dict["error"] = str(e)
            return PlanningState(**state_dict)
    
    def _plan_transportation_for_cluster(self, activities: List[Dict[str, Any]], 
                                       cluster_name: str) -> List[str]:
        """Plan transportation within a geographic cluster"""
        if not activities:
            return ["Walking around the area"]
        
        if len(activities) == 1:
            return ["Walking to the attraction"]
        
        # Calculate distances and suggest transportation
        transportation_plan = []
        
        for i in range(len(activities) - 1):
            loc1 = activities[i].get("location", {})
            loc2 = activities[i + 1].get("location", {})
            
            if (loc1.get("latitude") and loc1.get("longitude") and 
                loc2.get("latitude") and loc2.get("longitude")):
                
                distance = GeographicUtils.calculate_distance(
                    loc1["latitude"], loc1["longitude"],
                    loc2["latitude"], loc2["longitude"]
                )
                
                if distance <= 1.0:  # Within 1km
                    transport = "Walking"
                elif distance <= 5.0:  # Within 5km
                    transport = "Short taxi ride or public transit"
                else:
                    transport = "Car or longer taxi ride"
                
                transportation_plan.append(
                    f"{transport} from {activities[i].get('name')} to {activities[i + 1].get('name')} "
                    f"({distance:.1f}km)"
                )
        
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
        
        if restaurants:
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
                
                for i, part in enumerate(parts):
                    if part in ["to", "via", "through"] and i > 0 and i < len(parts) - 1:
                        # Add the destination before the connector
                        if i > 1:
                            destinations.append(" ".join(parts[:i]))
                        # Add the destination after the connector
                        destinations.append(" ".join(parts[i+1:]))
                
                # If no destinations found, use the original route
                if not destinations:
                    destinations = [route]
                
                return destinations
        
        # Default to single destination
        return [preferences.get("destination", "Unknown")]
    
    def _plan_transportation(self, destination: str, activities: List[Dict[str, Any]]) -> List[str]:
        """Plan transportation between activities"""
        
        if not activities:
            return ["Walking around the city"]
        
        # Simple transportation planning
        # In production, this would use Google Maps API for actual routes
        transport_options = []
        
        if len(activities) > 1:
            transport_options.append("Public transit between attractions")
        
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
            transport_options.append("Walking for outdoor activities")
        
        if not transport_options:
            transport_options.append("Walking and public transit")
        
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
                else:
                    activity_objects.append(act)
            
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
                else:
                    restaurant_objects.append(rest)
            
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