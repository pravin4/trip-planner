import os
from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from api_integrations.google_places import GooglePlacesAPI
from api_integrations.booking_api import BookingAPI
from api_integrations.yelp_api import YelpAPI
from models.travel_models import Activity, ActivityType, Location, APIResponse
import logging
from pydantic import BaseModel
from datetime import date

logger = logging.getLogger(__name__)

class ResearchState(BaseModel):
    destination: str
    preferences: Dict[str, Any]
    research_results: Dict[str, Any] = {}
    attractions: List[Dict[str, Any]] = []
    restaurants: List[Dict[str, Any]] = []
    accommodations: List[Dict[str, Any]] = []
    research_complete: bool = False
    error: Optional[str] = None

class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.google_places = GooglePlacesAPI()
        self.booking_api = BookingAPI()
        self.yelp_api = YelpAPI()
        # Use the Pydantic model as the state schema
        self.state_schema = ResearchState
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the research workflow using LangGraph"""
        workflow = StateGraph(self.state_schema)
        # Add nodes
        workflow.add_node("analyze_destination", self._analyze_destination)
        workflow.add_node("research_attractions", self._research_attractions)
        workflow.add_node("research_restaurants", self._research_restaurants)
        workflow.add_node("research_accommodations", self._research_accommodations)
        workflow.add_node("compile_research", self._compile_research)
        # Add entrypoint
        workflow.add_edge(START, "analyze_destination")
        # Add edges
        workflow.add_edge("analyze_destination", "research_attractions")
        workflow.add_edge("research_attractions", "research_restaurants")
        workflow.add_edge("research_restaurants", "research_accommodations")
        workflow.add_edge("research_accommodations", "compile_research")
        workflow.add_edge("compile_research", END)
        return workflow.compile()
    
    def _analyze_destination(self, state: ResearchState) -> ResearchState:
        """Analyze the destination and extract key information"""
        try:
            destination = state.destination
            
            # Use LLM to analyze destination
            system_prompt = """
            You are a travel research expert. Analyze the given destination and extract key information:
            - Best time to visit
            - Popular attractions
            - Local cuisine
            - Transportation options
            - Cultural highlights
            - Weather considerations
            
            Return a structured analysis in JSON format.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze the destination: {destination}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the response (simplified - in production, use proper JSON parsing)
            analysis = {
                "destination": destination,
                "analysis": response.content,
                "timestamp": "2024-01-01"  # Would be actual timestamp
            }
            
            state.research_results = analysis
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing destination: {e}")
            state.error = str(e)
            return state
    
    def _research_attractions(self, state: ResearchState) -> ResearchState:
        """Research attractions and activities in the destination"""
        try:
            destination = state.destination
            preferences = state.preferences
            activity_types = preferences.get("activity_types", [ActivityType.CULTURAL])
            
            attractions = []
            
            for activity_type in activity_types:
                result = self.google_places.find_attractions(destination, activity_type)
                

                if result.success and result.data:
                    # Convert Activity objects to dictionaries and limit to top 5
                    activity_dicts = []
                    for activity in result.data[:5]:
                        activity_dicts.append({
                            "name": activity.name,
                            "type": activity.type.value if hasattr(activity.type, 'value') else str(activity.type),
                            "duration_hours": activity.duration_hours,
                            "cost": activity.cost,
                            "description": activity.description,
                            "location": {
                                "name": activity.location.name if activity.location else "",
                                "address": activity.location.address if activity.location else "",
                                "latitude": activity.location.latitude if activity.location else 0,
                                "longitude": activity.location.longitude if activity.location else 0
                            } if activity.location else {}
                        })
                    attractions.extend(activity_dicts)
            
            state.attractions = attractions
            return state
            
        except Exception as e:
            logger.error(f"Error researching attractions: {e}")
            state.error = str(e)
            return state
    
    def _research_restaurants(self, state: ResearchState) -> ResearchState:
        """Research restaurants and dining options using Yelp API with Google Places fallback"""
        try:
            destination = state.destination
            preferences = state.preferences
            budget_level = preferences.get("budget_level", "moderate")
            
            restaurants = []
            
            # Try Yelp API first for better restaurant data
            try:
                # Get top-rated restaurants from Yelp
                yelp_result = self.yelp_api.get_top_rated_restaurants(
                    destination, min_rating=4.0, limit=15
                )
                
                if yelp_result.success and yelp_result.data:
                    for restaurant in yelp_result.data:
                        # Convert Yelp price level to numeric
                        price_level = len(restaurant.get('price', '$'))
                        
                        # Estimate cost per person based on price level
                        cost_per_person = {
                            1: 15,  # $
                            2: 30,  # $$
                            3: 60,  # $$$
                            4: 100  # $$$$
                        }.get(price_level, 30)
                        
                        # Filter by budget level
                        if budget_level == "budget" and price_level > 2:
                            continue
                        elif budget_level == "luxury" and price_level < 3:
                            continue
                        
                        restaurant_dict = {
                            "name": restaurant.get('name', ''),
                            "cuisine": restaurant.get('categories', ['Local'])[0] if restaurant.get('categories') else 'Local',
                            "price_level": price_level,
                            "rating": restaurant.get('rating', 4.0),
                            "cost_per_person": cost_per_person,
                            "review_count": restaurant.get('review_count', 0),
                            "location": {
                                "name": restaurant.get('name', ''),
                                "address": restaurant.get('location', {}).get('address', ''),
                                "city": restaurant.get('location', {}).get('city', ''),
                                "state": restaurant.get('location', {}).get('state', ''),
                                "latitude": restaurant.get('location', {}).get('latitude'),
                                "longitude": restaurant.get('location', {}).get('longitude'),
                                "rating": restaurant.get('rating', 4.0),
                                "price_level": price_level
                            }
                        }
                        restaurants.append(restaurant_dict)
                        
                        if len(restaurants) >= 10:  # Limit to 10 restaurants
                            break
                            
            except Exception as e:
                logger.warning(f"Yelp API not available: {e}")
            
            # If Yelp didn't provide enough restaurants, supplement with Google Places
            if len(restaurants) < 5:
                try:
                    result = self.google_places.search_places(
                        query=f"restaurants in {destination}",
                        location=destination,
                        types=['restaurant']
                    )
                    
                    if result.success and result.data:
                        for place in result.data:
                            # Skip if we already have this restaurant
                            if any(r['name'] == place.name for r in restaurants):
                                continue
                                
                            restaurant_dict = {
                                "name": place.name,
                                "cuisine": "Local",
                                "price_level": place.price_level or 2,
                                "rating": place.rating or 4.0,
                                "cost_per_person": (place.price_level or 2) * 15,
                                "review_count": 0,
                                "location": {
                                    "name": place.name,
                                    "address": place.address,
                                    "latitude": place.latitude,
                                    "longitude": place.longitude,
                                    "place_id": place.place_id,
                                    "rating": place.rating,
                                    "price_level": place.price_level
                                }
                            }
                            restaurants.append(restaurant_dict)
                            
                            if len(restaurants) >= 10:
                                break
                except Exception as e:
                    logger.warning(f"Google Places API also failed: {e}")
            
            # Final fallback if no restaurants found
            if not restaurants:
                restaurants = [
                    {
                        "name": f"Local Restaurant in {destination}",
                        "cuisine": "Local",
                        "price_level": 2,
                        "rating": 4.2,
                        "cost_per_person": 30.0,
                        "review_count": 50,
                        "location": {
                            "name": f"Local Restaurant in {destination}",
                            "address": f"Downtown {destination}",
                            "latitude": 0,
                            "longitude": 0
                        }
                    },
                    {
                        "name": f"Fine Dining in {destination}",
                        "cuisine": "International",
                        "price_level": 3,
                        "rating": 4.5,
                        "cost_per_person": 60.0,
                        "review_count": 75,
                        "location": {
                            "name": f"Fine Dining in {destination}",
                            "address": f"Upscale area of {destination}",
                            "latitude": 0,
                            "longitude": 0
                        }
                    }
                ]
            
            state.restaurants = restaurants
            return state
            
        except Exception as e:
            logger.error(f"Error researching restaurants: {e}")
            state.error = str(e)
            return state
    
    def _research_accommodations(self, state: ResearchState) -> ResearchState:
        """Research accommodation options using Booking.com API"""
        try:
            destination = state.destination
            preferences = state.preferences
            budget_level = preferences.get("budget_level", "moderate")
            group_size = preferences.get("group_size", 2)
            
            # First, search for destination ID
            try:
                dest_result = self.booking_api.search_destinations(destination)
            except Exception as e:
                logger.warning(f"Booking.com API not available: {e}")
                dest_result = None
            
            accommodations = []
            if dest_result and dest_result.success and dest_result.data:
                # Use the first destination found
                dest_id = dest_result.data[0]['dest_id']
                
                # Set check-in and check-out dates (30 days from now for 3 nights)
                from datetime import date, timedelta
                check_in = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                check_out = (date.today() + timedelta(days=33)).strftime("%Y-%m-%d")
                
                # Search for hotels
                try:
                    hotel_result = self.booking_api.search_hotels(
                        dest_id, check_in, check_out, 
                        adults=group_size, children=0, rooms=1
                    )
                except Exception as e:
                    logger.warning(f"Booking.com hotel search failed: {e}")
                    hotel_result = None
                
                if hotel_result and hotel_result.success and hotel_result.data:
                    # Filter by budget level
                    filtered_hotels = []
                    for hotel in hotel_result.data:
                        price = hotel.get("price_per_night", 0)
                        
                        # Apply budget filtering
                        if budget_level == "budget" and price <= 100:
                            filtered_hotels.append(hotel)
                        elif budget_level == "moderate" and 50 <= price <= 200:
                            filtered_hotels.append(hotel)
                        elif budget_level == "luxury" and price >= 150:
                            filtered_hotels.append(hotel)
                        else:
                            # Include if no specific budget filter
                            filtered_hotels.append(hotel)
                    
                    accommodations = filtered_hotels[:8]  # Limit to 8 hotels
            
            # If no accommodations found via Booking.com, fall back to Google Places
            if not accommodations:
                logger.info("Booking.com API not available, using Google Places fallback")
                result = self.google_places.search_places(
                    query=f"hotels in {destination}",
                    location=destination,
                    types=['lodging']
                )
                
                if result.success and result.data:
                    for i, place in enumerate(result.data[:8]):
                        base_price = 100
                        if budget_level == "budget":
                            base_price = 60
                        elif budget_level == "luxury":
                            base_price = 200
                        
                        price_multiplier = (place.price_level or 2) / 2
                        price_per_night = base_price * price_multiplier
                        
                        accommodation_dict = {
                            "name": place.name,
                            "type": "hotel",
                            "price_per_night": price_per_night,
                            "rating": place.rating or 4.0,
                            "amenities": ["WiFi", "Parking", "Breakfast"],
                            "location": {
                                "name": place.name,
                                "address": place.address,
                                "latitude": place.latitude,
                                "longitude": place.longitude,
                                "place_id": place.place_id,
                                "rating": place.rating,
                                "price_level": place.price_level
                            }
                        }
                        accommodations.append(accommodation_dict)
            
            # Final fallback if still no accommodations
            if not accommodations:
                accommodations = [
                    {
                        "name": f"Downtown Hotel in {destination}",
                        "type": "hotel",
                        "price_per_night": 120 if budget_level == "budget" else 180,
                        "rating": 4.0,
                        "amenities": ["WiFi", "Parking", "Breakfast"],
                        "location": {
                            "name": f"Downtown Hotel in {destination}",
                            "address": f"Downtown {destination}",
                            "latitude": 0,
                            "longitude": 0
                        }
                    }
                ]
            
            state.accommodations = accommodations
            return state
            
        except Exception as e:
            logger.error(f"Error researching accommodations: {e}")
            state.error = str(e)
            return state
    
    def _compile_research(self, state: ResearchState) -> ResearchState:
        """Compile all research results into a comprehensive report"""
        try:
            # Use LLM to compile research results
            system_prompt = """
            You are a travel research expert. Compile the research results into a comprehensive report.
            Include:
            - Destination overview
            - Top attractions and activities
            - Dining recommendations
            - Accommodation options
            - Key insights and tips
            
            Make the report engaging and informative for travelers.
            """
            
            research_data = {
                "attractions": len(state.attractions),
                "restaurants": len(state.restaurants),
                "accommodations": len(state.accommodations),
                "analysis": state.research_results.get("analysis", "")
            }
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Compile research report for: {research_data}")
            ]
            
            response = self.llm.invoke(messages)
            
            state.research_results["compiled_report"] = response.content
            state.research_complete = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error compiling research: {e}")
            state.error = str(e)
            return state
    
    def research_destination(self, destination: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to research a destination"""
        try:
            initial_state = ResearchState(
                destination=destination,
                preferences=preferences,
                research_results={},
                attractions=[],
                restaurants=[],
                accommodations=[],
                research_complete=False,
                error=""
            )
            
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Check if final_state is already a dict or needs conversion
            if hasattr(final_state, 'model_dump'):
                return final_state.model_dump()
            else:
                return final_state
            
        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            return {
                "error": str(e),
                "research_complete": False
            }
    
    def get_attractions_by_type(self, destination: str, activity_type: ActivityType) -> List[Activity]:
        """Get attractions of a specific type"""
        result = self.google_places.find_attractions(destination, activity_type)
        
        if result.success:
            return result.data
        else:
            logger.error(f"Error getting attractions: {result.error}")
            return []
    
    def get_nearby_places(self, location: str, place_type: str = None) -> List[Location]:
        """Get nearby places of interest"""
        result = self.google_places.get_nearby_places(location, place_type=place_type)
        
        if result.success:
            return result.data
        else:
            logger.error(f"Error getting nearby places: {result.error}")
            return [] 