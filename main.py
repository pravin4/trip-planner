#!/usr/bin/env python3
"""
Smart Travel Planner - Main Application
An intelligent, agentic travel planning system using LangGraph and multi-agent coordination.
"""

import os
import logging
import argparse
from datetime import date
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

from agents.research_agent import ResearchAgent
from agents.planning_agent import PlanningAgent
from agents.journey_agent import JourneyAgent
from models.travel_models import (
    TravelPreferences, TravelRequest, Itinerary,
    AccommodationType, ActivityType, BudgetLevel
)
from core.pdf_generator import PDFGenerator
from core.cost_estimator import CostEstimator
from api_integrations.wikivoyage_api import WikivoyageAPI
from api_integrations.google_places import GooglePlacesAPI
from api_integrations.yelp_api import YelpAPI
from api_integrations.amadeus_api import AmadeusAPI
from api_integrations.booking_api import BookingAPI
from api_integrations.hotels_com_api import HotelsComAPI
from api_integrations.google_hotels_api import GoogleHotelsAPI
from utils.data_quality_manager import DataQualityManager
from utils.geocoding_service import GeocodingService
from utils.trip_logistics_planner import TripLogisticsPlanner

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartTravelPlanner:
    """
    Main travel planner class that coordinates research, planning, and optimization agents.
    """
    
    def __init__(self):
        """Initialize the travel planner with all necessary components."""
        try:
            # Initialize agents
            self.research_agent = ResearchAgent()
            self.planning_agent = PlanningAgent()
            self.journey_agent = JourneyAgent()
            
            # Initialize utilities
            self.pdf_generator = PDFGenerator()
            self.cost_estimator = CostEstimator()
            
            # Initialize API integrations
            self.google_places = GooglePlacesAPI()
            self.yelp = YelpAPI()
            self.wikivoyage = WikivoyageAPI()
            self.amadeus = AmadeusAPI()
            self.booking = BookingAPI()
            self.hotels_com = HotelsComAPI()
            self.google_hotels = GoogleHotelsAPI()
            
            # Initialize Data Quality Manager
            self.data_quality_manager = DataQualityManager()
            
            # Initialize Geocoding Service
            self.geocoding_service = GeocodingService()
            
            # Initialize Trip Logistics Planner
            self.trip_logistics_planner = TripLogisticsPlanner()
            
            logger.info("Smart Travel Planner initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Smart Travel Planner: {e}")
            raise
    
    def _parse_and_validate_destination(self, destination: str, starting_point: str = "San Jose") -> Dict[str, Any]:
        """
        Parse and validate destination input to prevent geographic confusion.
        
        Args:
            destination: Raw destination input from user
            starting_point: Starting location (default: "San Jose")
            
        Returns:
            Dict with parsed destination info
        """
        # Handle common multi-destination patterns
        if " to " in destination.lower():
            # Route format: "San Jose to Big Sur"
            parts = destination.split(" to ")
            if len(parts) == 2:
                return {
                    "type": "route",
                    "start": parts[0].strip(),
                    "end": parts[1].strip(),
                    "primary_destination": parts[1].strip(),  # Focus on end destination
                    "route_description": destination
                }
        
        # Check if destination contains route indicators
        route_indicators = [" to ", " → ", " -> ", " via ", " through "]
        for indicator in route_indicators:
            if indicator in destination.lower():
                parts = destination.split(indicator)
                if len(parts) == 2:
                    return {
                        "type": "route",
                        "start": parts[0].strip(),
                        "end": parts[1].strip(),
                        "primary_destination": parts[1].strip(),
                        "route_description": destination
                    }
        
        # Check if this looks like a route from starting_point to destination
        # If starting_point is different from destination and destination doesn't contain starting_point
        if (starting_point.lower() not in destination.lower() and 
            destination.lower() not in starting_point.lower() and
            starting_point != "San Jose"):  # Only if starting_point was explicitly set
            # This might be a route from starting_point to destination
            return {
                "type": "route",
                "start": starting_point,
                "end": destination,
                "primary_destination": destination,
                "route_description": f"{starting_point} to {destination}"
            }
        
        # More aggressive route detection: if starting_point and destination are different cities
        # and starting_point is not the default "San Jose", treat as route
        if (starting_point != "San Jose" and 
            starting_point.lower() != destination.lower() and
            not any(city in destination.lower() for city in starting_point.lower().split())):
            return {
                "type": "route",
                "start": starting_point,
                "end": destination,
                "primary_destination": destination,
                "route_description": f"{starting_point} to {destination}"
            }
        
        # Handle comma-separated destinations
        if "," in destination:
            parts = [part.strip() for part in destination.split(",")]
            if len(parts) == 2:
                # Check if second part is descriptive or a separate destination
                second_part = parts[1].lower()
                if len(second_part) < 30 and not any(word in second_part for word in ["via", "through", "to"]):
                    # Likely a single destination with context
                    return {
                        "type": "single",
                        "primary_destination": destination,
                        "parsed_destinations": [destination]
                    }
                else:
                    # Multiple destinations
                    return {
                        "type": "multi",
                        "primary_destination": parts[0],
                        "parsed_destinations": parts
                    }
        
        # Single destination
        return {
            "type": "single",
            "primary_destination": destination,
            "parsed_destinations": [destination]
        }
    
    def create_itinerary(self, 
                        destination: str,
                        start_date: str,
                        end_date: str,
                        budget: float,
                        preferences: Optional[Dict[str, Any]] = None,
                        starting_point: str = "San Jose") -> Itinerary:
        """
        Create a complete travel itinerary with departure/arrival logistics.
        
        Args:
            destination: Travel destination (e.g., "San Francisco, CA")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            budget: Total budget for the trip
            preferences: Optional preferences dictionary
            starting_point: Starting location (default: "San Jose")
            
        Returns:
            Complete itinerary object with departure/arrival logistics
        """
        try:
            logger.info(f"Creating itinerary from {starting_point} to {destination} from {start_date} to {end_date}")
            
            # Parse dates
            start_dt = date.fromisoformat(start_date)
            end_dt = date.fromisoformat(end_date)
            
            # Create travel preferences
            travel_prefs = self._create_travel_preferences(preferences or {})
            
            # Parse destination to check if it's a route
            destination_info = self._parse_and_validate_destination(destination, starting_point)
            
            # Step 1: Plan the journey (road trip, flights, etc.)
            logger.info("Step 1: Planning journey...")
            journey_plan = None
            
            if destination_info["type"] == "route":
                # This is a route (e.g., "San Jose to Big Sur")
                journey_plan = self.journey_agent.plan_journey(
                    origin=destination_info["start"],
                    destination=destination_info["end"],
                    start_date=start_date,
                    end_date=end_date,
                    preferences=travel_prefs.model_dump() if hasattr(travel_prefs, "model_dump") else dict(travel_prefs)
                )
                logger.info(f"Journey planned: {journey_plan.get('travel_mode', 'unknown')} mode, {journey_plan.get('total_distance', 0):.1f} km")
                
                # For routes, pass the full route description to planning agent
                planning_destination = destination  # Use the full route description
            else:
                # For single destinations, use the primary destination
                planning_destination = destination_info["primary_destination"]
            
            # Plan trip logistics with route optimization
            trip_logistics_planner = TripLogisticsPlanner()
            
            # Use the parsed destination info instead of extracting from preferences
            if destination_info["type"] == "route":
                # For routes, use the end destination
                main_destination = destination_info["end"]
            else:
                # For single destinations, use the primary destination
                main_destination = destination_info["primary_destination"]
            
            # Plan logistics using the correct destination
            trip_logistics = trip_logistics_planner.plan_complete_trip(
                starting_point, main_destination, start_date, end_date, travel_prefs.model_dump() if hasattr(travel_prefs, "model_dump") else dict(travel_prefs)
            )
            
            # Step 2: Research the destination
            logger.info("Step 2: Researching destination...")
            research_results = self.research_agent.research_destination(destination, travel_prefs.model_dump())
            
            if not research_results.get("research_complete", False):
                raise Exception(f"Research failed: {research_results.get('error', 'Unknown error')}")
            
            # Step 3: Create the itinerary
            logger.info("Step 3: Creating itinerary...")
            itinerary = self.planning_agent.create_itinerary(
                destination=planning_destination,
                start_date=start_dt.isoformat() if hasattr(start_dt, "isoformat") else str(start_dt),
                end_date=end_dt.isoformat() if hasattr(end_dt, "isoformat") else str(end_dt),
                preferences=travel_prefs.model_dump() if hasattr(travel_prefs, "model_dump") else dict(travel_prefs),
                research_data=research_results
            )
            
            # Step 4: Add departure/arrival logistics to itinerary
            itinerary = self._add_trip_logistics_to_itinerary(itinerary, trip_logistics, starting_point, journey_plan)
            
            # Step 5: Apply data quality improvements
            itinerary = self.data_quality_manager.improve_itinerary_quality(itinerary, travel_prefs.model_dump() if hasattr(travel_prefs, "model_dump") else dict(travel_prefs))
            
            logger.info(f"Itinerary created successfully! Total cost: ${itinerary['total_cost']:.2f}")
            return itinerary
            
        except Exception as e:
            logger.error(f"Error creating itinerary: {e}")
            raise
    
    def _create_travel_preferences(self, preferences_dict: Dict[str, Any]) -> TravelPreferences:
        """Create TravelPreferences object from dictionary."""
        
        # Default preferences
        default_prefs = {
            "accommodation_types": [AccommodationType.HOTEL],
            "activity_types": [ActivityType.CULTURAL],
            "budget_level": BudgetLevel.MODERATE,
            "max_daily_budget": 200.0,
            "dietary_restrictions": [],
            "accessibility_needs": [],
            "group_size": 1,
            "children": False
        }
        
        # Update with user preferences
        if preferences_dict:
            default_prefs.update(preferences_dict)
        
        # Convert string values to enums if needed
        if isinstance(default_prefs["accommodation_types"][0], str):
            default_prefs["accommodation_types"] = [
                AccommodationType(acc_type) for acc_type in default_prefs["accommodation_types"]
            ]
        
        if isinstance(default_prefs["activity_types"][0], str):
            default_prefs["activity_types"] = [
                ActivityType(act_type) for act_type in default_prefs["activity_types"]
            ]
        
        if isinstance(default_prefs["budget_level"], str):
            default_prefs["budget_level"] = BudgetLevel(default_prefs["budget_level"])
        
        return TravelPreferences(**default_prefs)
    
    def generate_pdf(self, itinerary: Itinerary, output_path: str) -> bool:
        """Generate a PDF itinerary."""
        try:
            logger.info(f"Generating PDF itinerary: {output_path}")
            success = self.pdf_generator.generate_itinerary_pdf(itinerary, output_path)
            
            if success:
                logger.info(f"PDF generated successfully: {output_path}")
            else:
                logger.error("Failed to generate PDF")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def optimize_for_budget(self, itinerary: Itinerary, target_budget: float) -> Dict[str, Any]:
        """Optimize the itinerary to fit within a target budget."""
        try:
            logger.info(f"Optimizing itinerary for budget: ${target_budget}")
            
            # Get current cost breakdown
            current_breakdown = itinerary.cost_breakdown
            
            # Optimize costs
            optimized_costs = self.cost_estimator.optimize_for_budget(
                target_budget, 
                current_breakdown, 
                itinerary.preferences
            )
            
            # Get budget suggestions
            suggestions = self.cost_estimator.suggest_budget_adjustments(
                current_breakdown, 
                target_budget
            )
            
            return {
                "original_costs": current_breakdown.dict(),
                "optimized_costs": optimized_costs,
                "suggestions": suggestions,
                "original_total": current_breakdown.total,
                "optimized_total": sum(optimized_costs.values())
            }
            
        except Exception as e:
            logger.error(f"Error optimizing for budget: {e}")
            raise
    
    def get_destination_insights(self, destination: str) -> Dict[str, Any]:
        """Get insights about a destination without creating a full itinerary."""
        try:
            logger.info(f"Getting insights for {destination}")
            
            # Create basic preferences for research
            basic_prefs = TravelPreferences()
            
            # Research the destination
            research_results = self.research_agent.research_destination(destination, basic_prefs.model_dump())
            
            if research_results.get("research_complete", False):
                return {
                    "destination": destination,
                    "research_summary": research_results.get("research_results", {}),
                    "attractions_count": len(research_results.get("attractions", [])),
                    "restaurants_count": len(research_results.get("restaurants", [])),
                    "accommodations_count": len(research_results.get("accommodations", [])),
                    "success": True
                }
            else:
                return {
                    "destination": destination,
                    "error": research_results.get("error", "Unknown error"),
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error getting destination insights: {e}")
            return {
                "destination": destination,
                "error": str(e),
                "success": False
            }
    
    def get_wikivoyage_guide(self, destination: str) -> dict:
        """
        Fetch Wikivoyage travel guide and attractions for a destination.
        Returns a dictionary with guide extract, url, and top attractions.
        """
        try:
            guide = self.wikivoyage.get_destination_guide(destination)
            attractions = self.wikivoyage.get_attractions(destination)
            return {
                "success": guide.success and attractions.success,
                "destination": destination,
                "guide": guide.data if guide.success else {},
                "attractions": attractions.data if attractions.success else [],
                "message": "Wikivoyage guide and attractions fetched successfully" if guide.success else guide.error
            }
        except Exception as e:
            logger.error(f"Error fetching Wikivoyage guide: {e}")
            return {
                "success": False,
                "destination": destination,
                "error": str(e)
            }
    
    def check_hotel_availability(self, destination: str, check_in: date, 
                                check_out: date, adults: int = 2) -> Dict[str, Any]:
        """
        Check real hotel availability and pricing for specific dates.
        Tries multiple APIs in sequence: Amadeus → Booking.com → Hotels.com
        
        Args:
            destination: Destination city name
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            
        Returns:
            Dictionary with availability data
        """
        try:
            # Try Amadeus API first (best for real pricing)
            amadeus_result = self._check_amadeus_availability(destination, check_in, check_out, adults)
            if amadeus_result["success"] and amadeus_result["total_available"] > 0:
                amadeus_result["source"] = "Amadeus API"
                return amadeus_result
            
            # Try Booking.com API second
            logger.info("Amadeus returned no data, trying Booking.com API...")
            booking_result = self._check_booking_availability(destination, check_in, check_out, adults)
            if booking_result["success"] and booking_result["total_available"] > 0:
                booking_result["source"] = "Booking.com API"
                return booking_result
            
            # Try Hotels.com API third
            logger.info("Booking.com returned no data, trying Hotels.com API...")
            hotels_result = self._check_hotels_com_availability(destination, check_in, check_out, adults)
            if hotels_result["success"] and hotels_result["total_available"] > 0:
                hotels_result["source"] = "Hotels.com API"
                return hotels_result
            
            # Try Google Hotels API fourth
            logger.info("Hotels.com returned no data, trying Google Hotels API...")
            google_result = self._check_google_hotels_availability(destination, check_in, check_out, adults)
            if google_result["success"] and google_result["total_available"] > 0:
                google_result["source"] = "Google Hotels API"
                return google_result
            
            # If all APIs fail, return empty results with detailed error info
            return {
                "success": False,
                "error": "No hotel availability data available from any API",
                "data": [],
                "source": "None",
                "api_status": {
                    "amadeus": amadeus_result.get("error", "Not configured"),
                    "booking": booking_result.get("error", "Not configured"), 
                    "hotels_com": hotels_result.get("error", "Not configured"),
                    "google_hotels": google_result.get("error", "Not configured")
                },
                "recommendation": "Add API keys to .env file for real hotel data"
            }
                
        except Exception as e:
            logger.error(f"Error checking hotel availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "source": "Error"
            }
    
    def _check_amadeus_availability(self, destination: str, check_in: date, 
                                   check_out: date, adults: int) -> Dict[str, Any]:
        """Check hotel availability using Amadeus API."""
        try:
            # Get city code for Amadeus API
            city_code = self.amadeus.get_city_code(destination)
            if not city_code:
                return {
                    "success": False,
                    "error": f"Could not find city code for {destination}",
                    "data": [],
                    "total_available": 0
                }
            
            # Search for available hotels with real pricing
            result = self.amadeus.search_hotels(city_code, check_in, check_out, adults)
            
            if result.success:
                # Filter for actually available hotels
                available_hotels = [
                    hotel for hotel in result.data 
                    if hotel.get('price_range', {}).get('available', False)
                ]
                
                return {
                    "success": True,
                    "data": available_hotels,
                    "total_available": len(available_hotels),
                    "city_code": city_code,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "data": [],
                    "total_available": 0
                }
                
        except Exception as e:
            logger.error(f"Error checking Amadeus availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "total_available": 0
            }
    
    def _check_booking_availability(self, destination: str, check_in: date, 
                                   check_out: date, adults: int) -> Dict[str, Any]:
        """Check hotel availability using Booking.com API."""
        try:
            # Search for available hotels
            result = self.booking.search_hotels(destination, check_in, check_out, adults)
            
            if result.success:
                # Filter for available hotels with pricing
                available_hotels = [
                    hotel for hotel in result.data 
                    if hotel.get('available', False) and hotel.get('price_range', {}).get('min_price', 0) > 0
                ]
                
                return {
                    "success": True,
                    "data": available_hotels,
                    "total_available": len(available_hotels),
                    "destination": destination,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "data": [],
                    "total_available": 0
                }
                
        except Exception as e:
            logger.error(f"Error checking Booking.com availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "total_available": 0
            }
    
    def _check_hotels_com_availability(self, destination: str, check_in: date, 
                                      check_out: date, adults: int) -> Dict[str, Any]:
        """Check hotel availability using Hotels.com API."""
        try:
            # Search for available hotels
            result = self.hotels_com.search_hotels(destination, check_in, check_out, adults)
            
            if result.success:
                # Filter for available hotels with pricing
                available_hotels = [
                    hotel for hotel in result.data 
                    if hotel.get('available', False) and hotel.get('price_range', {}).get('min_price', 0) > 0
                ]
                
                return {
                    "success": True,
                    "data": available_hotels,
                    "total_available": len(available_hotels),
                    "destination": destination,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "data": [],
                    "total_available": 0
                }
                
        except Exception as e:
            logger.error(f"Error checking Hotels.com availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "total_available": 0
            }
    
    def _check_google_hotels_availability(self, destination: str, check_in: date, 
                                          check_out: date, adults: int) -> Dict[str, Any]:
        """Check hotel availability using Google Hotels API."""
        try:
            # Search for available hotels
            result = self.google_hotels.search_hotels(destination, check_in, check_out, adults)
            
            if result.success:
                # Filter for available hotels with pricing
                available_hotels = [
                    hotel for hotel in result.data 
                    if hotel.get('available', False) and hotel.get('price_range', {}).get('min_price', 0) > 0
                ]
                
                return {
                    "success": True,
                    "data": available_hotels,
                    "total_available": len(available_hotels),
                    "destination": destination,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "data": [],
                    "total_available": 0
                }
                
        except Exception as e:
            logger.error(f"Error checking Google Hotels availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "total_available": 0
            }
    
    def get_yelp_restaurants(self, destination: str, cuisine: str = None, 
                           min_rating: float = 4.0, limit: int = 10) -> Dict[str, Any]:
        """
        Get restaurant recommendations from Yelp.
        
        Args:
            destination: Destination to search
            cuisine: Specific cuisine type (optional)
            min_rating: Minimum rating filter
            limit: Maximum number of results
            
        Returns:
            Dictionary with restaurant data
        """
        try:
            if cuisine:
                result = self.yelp.search_by_cuisine(destination, cuisine, limit)
            else:
                result = self.yelp.get_top_rated_restaurants(destination, min_rating, limit)
            
            if result.success:
                return {
                    "success": True,
                    "restaurants": result.data,
                    "metadata": result.metadata
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "restaurants": []
                }
                
        except Exception as e:
            logger.error(f"Error getting Yelp restaurants: {e}")
            return {
                "success": False,
                "error": str(e),
                "restaurants": []
            }
    
    def _extract_destinations_from_preferences(self, preferences: Dict[str, Any]) -> List[str]:
        """Extract destinations from travel preferences."""
        destinations = []
        if isinstance(preferences.get("parsed_destinations"), list):
            destinations.extend(preferences["parsed_destinations"])
        elif isinstance(preferences.get("primary_destination"), str):
            destinations.append(preferences["primary_destination"])
        return destinations
    
    def _add_trip_logistics_to_itinerary(self, itinerary: Dict[str, Any], 
                                       trip_logistics: Any, 
                                       starting_point: str,
                                       journey_plan: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add departure/arrival logistics and journey planning to the itinerary."""
        try:
            # Convert TripLogistics object to dict if needed
            if hasattr(trip_logistics, 'departure_leg'):
                # It's a TripLogistics object
                logistics_dict = {
                    "departure_info": {
                        "from": trip_logistics.departure_leg.from_location if trip_logistics.departure_leg else starting_point,
                        "to": trip_logistics.departure_leg.to_location if trip_logistics.departure_leg else destination,
                        "departure_time": trip_logistics.departure_leg.departure_time if trip_logistics.departure_leg else "09:00",
                        "arrival_time": trip_logistics.departure_leg.arrival_time if trip_logistics.departure_leg else "Unknown",
                        "duration": trip_logistics.departure_leg.duration_hours if trip_logistics.departure_leg else 0,
                        "mode": trip_logistics.departure_leg.mode if trip_logistics.departure_leg else "car",
                        "cost": trip_logistics.departure_leg.cost_per_person if trip_logistics.departure_leg else 0,
                        "notes": trip_logistics.departure_leg.notes if trip_logistics.departure_leg else ""
                    },
                    "return_info": {
                        "from": trip_logistics.return_leg.from_location if trip_logistics.return_leg else destination,
                        "to": trip_logistics.return_leg.to_location if trip_logistics.return_leg else starting_point,
                        "departure_time": trip_logistics.return_leg.departure_time if trip_logistics.return_leg else "16:00",
                        "arrival_time": trip_logistics.return_leg.arrival_time if trip_logistics.return_leg else "Unknown",
                        "duration": trip_logistics.return_leg.duration_hours if trip_logistics.return_leg else 0,
                        "mode": trip_logistics.return_leg.mode if trip_logistics.return_leg else "car",
                        "cost": trip_logistics.return_leg.cost_per_person if trip_logistics.return_leg else 0,
                        "notes": trip_logistics.return_leg.notes if trip_logistics.return_leg else ""
                    },
                    "total_travel_time": trip_logistics.total_travel_time,
                    "total_travel_cost": trip_logistics.total_travel_cost,
                    "travel_days": trip_logistics.travel_days or [],
                    "starting_point": trip_logistics.starting_point,
                    "destination": trip_logistics.destination
                }
            else:
                # It's already a dict
                logistics_dict = trip_logistics
            
            # Add trip logistics to itinerary
            itinerary["trip_logistics"] = logistics_dict
            itinerary["starting_point"] = starting_point
            
            # Add journey plan if available (this takes precedence for route planning)
            if journey_plan:
                itinerary["journey_plan"] = journey_plan
                
                # Add journey stops to the itinerary
                if journey_plan.get("stops"):
                    self._add_journey_stops_to_itinerary(itinerary, journey_plan["stops"])
                
                # For route planning, use journey plan costs instead of trip logistics
                if journey_plan.get("total_cost"):
                    # Remove any existing transportation costs to avoid double counting
                    if "cost_breakdown" in itinerary:
                        # Subtract existing transportation costs
                        existing_transport = itinerary["cost_breakdown"].get("transportation", 0)
                        itinerary["total_cost"] -= existing_transport
                        itinerary["cost_breakdown"]["transportation"] = 0
                    
                    # Add journey costs
                    itinerary["total_cost"] += journey_plan["total_cost"]
                    
                    # Update cost breakdown with journey costs
                    if "cost_breakdown" in itinerary:
                        journey_costs = journey_plan.get("costs", {})
                        for cost_type, amount in journey_costs.items():
                            if cost_type in itinerary["cost_breakdown"]:
                                itinerary["cost_breakdown"][cost_type] += amount
                            else:
                                itinerary["cost_breakdown"][cost_type] = amount
                        
                        # Ensure total is correct
                        itinerary["cost_breakdown"]["total"] = sum(
                            v for k, v in itinerary["cost_breakdown"].items() if k != "total"
                        )
                
                # Update trip logistics with journey plan info
                if journey_plan.get("travel_mode"):
                    logistics_dict["journey_mode"] = journey_plan["travel_mode"]
                    logistics_dict["journey_distance"] = journey_plan.get("total_distance", 0)
                    logistics_dict["journey_duration"] = journey_plan.get("total_duration", 0)
                    
                    # Update departure and return info with journey plan data
                    if logistics_dict.get("departure_info"):
                        logistics_dict["departure_info"]["mode"] = journey_plan["travel_mode"]
                        logistics_dict["departure_info"]["notes"] = self._generate_departure_notes(
                            starting_point, 
                            logistics_dict["departure_info"]["to"], 
                            journey_plan["travel_mode"], 
                            journey_plan.get("total_distance", 0)
                        )
                    
                    if logistics_dict.get("return_info"):
                        logistics_dict["return_info"]["mode"] = journey_plan["travel_mode"]
                        logistics_dict["return_info"]["notes"] = self._generate_return_notes(
                            logistics_dict["return_info"]["from"], 
                            starting_point, 
                            journey_plan["travel_mode"], 
                            journey_plan.get("total_distance", 0)
                        )
            
            # Only add trip logistics costs if no journey plan exists (for non-route trips)
            elif logistics_dict.get("total_travel_cost"):
                itinerary["total_cost"] += logistics_dict["total_travel_cost"]
                
                # Update cost breakdown
                if "cost_breakdown" in itinerary:
                    itinerary["cost_breakdown"]["transportation"] += logistics_dict["total_travel_cost"]
                    itinerary["cost_breakdown"]["total"] = sum(itinerary["cost_breakdown"].values())
            
            # Integrate departure logistics into the first day instead of creating a separate day
            if logistics_dict.get("departure_info") and itinerary.get("day_plans"):
                first_day = itinerary["day_plans"][0]
                departure_transport = f"Departure: {logistics_dict['departure_info']['notes']}"
                
                # Add departure transportation to existing transportation or create new list
                if "transportation" in first_day:
                    first_day["transportation"].insert(0, departure_transport)
                else:
                    first_day["transportation"] = [departure_transport]
                
                # Add departure note to the first day
                departure_note = f"Departure day from {starting_point} to {logistics_dict['departure_info']['to']}"
                if "notes" in first_day:
                    first_day["notes"] = departure_note + ". " + first_day["notes"]
                else:
                    first_day["notes"] = departure_note
            
            # Integrate return logistics into the last day instead of creating a separate day
            if logistics_dict.get("return_info") and itinerary.get("day_plans"):
                last_day = itinerary["day_plans"][-1]
                return_transport = f"Return: {logistics_dict['return_info']['notes']}"
                
                # Add return transportation to existing transportation or create new list
                if "transportation" in last_day:
                    last_day["transportation"].append(return_transport)
                else:
                    last_day["transportation"] = [return_transport]
                
                # Add return note to the last day
                return_note = f"Return day from {logistics_dict['return_info']['from']} to {starting_point}"
                if "notes" in last_day:
                    last_day["notes"] = last_day["notes"] + ". " + return_note
                else:
                    last_day["notes"] = return_note
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error adding trip logistics to itinerary: {e}")
            return itinerary
    
    def _add_journey_stops_to_itinerary(self, itinerary: Dict[str, Any], stops: List[Dict[str, Any]]) -> None:
        """Add journey stops as activities to the appropriate days."""
        try:
            if not stops or not itinerary.get("day_plans"):
                return
            
            # Add stops to the first day as journey activities
            first_day = itinerary["day_plans"][0]
            
            # Create journey activities from stops
            journey_activities = []
            for stop in stops:
                if stop.get("attractions"):
                    for attraction in stop["attractions"]:
                        journey_activities.append({
                            "name": f"Journey Stop: {attraction.get('name', 'Unknown')}",
                            "location": stop["location"],
                            "duration": "1-2 hours",
                            "cost": 20,  # Estimated cost for attraction
                            "type": "journey_stop",
                            "description": f"Stop along the journey: {attraction.get('name', 'Unknown')}",
                            "stop_type": stop.get("stop_type", "attraction")
                        })
                elif stop.get("stop_type") == "rest":
                    journey_activities.append({
                        "name": "Rest Stop",
                        "location": stop["location"],
                        "duration": "30 minutes",
                        "cost": 0,
                        "type": "journey_stop",
                        "description": "Rest stop for gas, food, and bathroom",
                        "stop_type": "rest"
                    })
            
            # Add journey activities to the first day
            if journey_activities:
                if "activities" in first_day:
                    first_day["activities"].extend(journey_activities)
                else:
                    first_day["activities"] = journey_activities
                
                # Add journey note
                journey_note = f"Journey includes {len(stops)} stops along the route"
                if "notes" in first_day:
                    first_day["notes"] = journey_note + ". " + first_day["notes"]
                else:
                    first_day["notes"] = journey_note
                    
        except Exception as e:
            logger.error(f"Error adding journey stops to itinerary: {e}")
    
    def _get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a location using real geocoding service."""
        return self.geocoding_service.get_coordinates(location)
    
    def _calculate_distance(self, from_coords: Tuple[float, float], 
                          to_coords: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        import math
        
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
        
        # For medium distances (100-800 km), consider budget and preferences
        elif distance < 800:
            # Check if user specified travel mode in preferences
            if "travel_mode" in preferences:
                return preferences["travel_mode"]
            
            # For moderate distances, prefer car unless budget constraints
            if budget_level == "budget":
                return "bus"  # Budget option
            elif budget_level == "luxury":
                return "plane"  # Luxury option
            else:
                return "car"  # Default to car for moderate budget
        
        # For long distances (> 800 km), prefer plane
        else:
            return "plane"
    
    def _calculate_duration(self, distance: float, mode: str) -> float:
        """Calculate travel duration in hours."""
        speeds = {
            "car": 80,
            "plane": 800,
            "train": 120,
            "bus": 70
        }
        
        speed = speeds.get(mode, 60)  # Default 60 km/h
        return distance / speed
    
    def _calculate_cost(self, distance: float, mode: str, preferences: Dict[str, Any]) -> float:
        """Calculate travel cost per person."""
        costs_per_km = {
            "car": 0.15,
            "plane": 0.50,
            "train": 0.10,
            "bus": 0.05
        }
        
        base_cost = distance * costs_per_km.get(mode, 0.15)
        
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
            from datetime import datetime, timedelta
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




def main():
    """Main function to demonstrate the travel planner."""
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Smart Travel Planner - Create custom itineraries')
    parser.add_argument('--destination', '-d', type=str, default="San Francisco, CA",
                       help='Travel destination (e.g., "San Francisco, CA", "Solvang, CA")')
    parser.add_argument('--start-date', '-s', type=str, default="2024-06-15",
                       help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', '-e', type=str, default="2024-06-20", 
                       help='End date in YYYY-MM-DD format')
    parser.add_argument('--budget', '-b', type=float, default=2000.0,
                       help='Total budget for the trip')
    parser.add_argument('--group-size', '-g', type=int, default=2,
                       help='Number of travelers')
    parser.add_argument('--activity-types', '-a', nargs='+', 
                       default=['cultural', 'outdoor'],
                       help='Activity types (e.g., cultural outdoor adventure)')
    parser.add_argument('--accommodation-types', '-acc', nargs='+',
                       default=['hotel'],
                       help='Accommodation types (e.g., hotel hostel camping)')
    parser.add_argument('--budget-level', '-bl', type=str, default='moderate',
                       choices=['budget', 'moderate', 'luxury'],
                       help='Budget level')
    parser.add_argument('--children', action='store_true',
                       help='Include children in planning')
    parser.add_argument('--dietary-restrictions', '-dr', nargs='+', default=[],
                       help='Dietary restrictions (e.g., vegetarian gluten-free)')
    parser.add_argument('--output-pdf', '-o', type=str, default=None,
                       help='Output PDF path (optional)')
    parser.add_argument('--demo', action='store_true',
                       help='Run demo mode with default values')
    
    args = parser.parse_args()
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return
    
    try:
        # Initialize the travel planner
        planner = SmartTravelPlanner()
        
        if args.demo:
            # Run demo mode
            print("🧳 Smart Travel Planner Demo")
            print("=" * 50)
            
            # Create an example itinerary
            itinerary = planner.create_itinerary(
                destination="San Francisco, CA",
                start_date="2024-06-15",
                end_date="2024-06-20",
                budget=2000,
                preferences={
                    "accommodation_types": ["hotel", "glamping"],
                    "activity_types": ["outdoor", "cultural"],
                    "budget_level": "moderate",
                    "group_size": 2
                }
            )
            
            print(f"✅ Itinerary created for {itinerary['destination']}")
            print(f"📅 Duration: {itinerary.get('duration_days', 'N/A')} days")
            print(f"💰 Total Cost: ${itinerary['total_cost']:.2f}")
            print(f"📊 Budget Status: {'✅ Within Budget' if itinerary.get('remaining_budget', 0) >= 0 else '⚠️ Over Budget'}")
            
            # Show quality metrics and disclaimers
            if 'quality_metrics' in itinerary:
                qm = itinerary['quality_metrics']
                print("\n🧠 Quality Metrics:")
                print(f"- Activity Variety Score: {qm.get('activity_variety_score', 0):.2f}")
                print(f"- Cost Realism Score: {qm.get('cost_realism_score', 0):.2f}")
                print(f"- Geographic Efficiency: {qm.get('geographic_efficiency', 0):.2f}")
                print(f"- Data Completeness: {qm.get('data_completeness', 0):.2f}")
                print(f"- Overall Quality: {qm.get('overall_quality', 0):.2f}")
                if qm.get('issues'):
                    print(f"  Issues: {qm['issues']}")
                if qm.get('warnings'):
                    print(f"  Warnings: {qm['warnings']}")
                if qm.get('suggestions'):
                    print(f"  Suggestions: {qm['suggestions']}")
            if 'disclaimers' in itinerary:
                print("\n⚠️ Disclaimers:")
                for disclaimer in itinerary['disclaimers']:
                    print(f"- {disclaimer}")
            
            # Generate PDF
            pdf_path = "outputs/san_francisco_itinerary.pdf"
            os.makedirs("outputs", exist_ok=True)
            
            if planner.generate_pdf(itinerary, pdf_path):
                print(f"📄 PDF generated: {pdf_path}")
            
            # Get destination insights
            insights = planner.get_destination_insights("New York, NY")
            if insights["success"]:
                print(f"🔍 Found {insights['attractions_count']} attractions in New York")
            
            # Get Wikivoyage guide
            guide = planner.get_wikivoyage_guide("New York, NY")
            if guide["success"]:
                print(f"🌐 Wikivoyage Guide: {guide['guide']['extract']}")
            
            print("\n🎉 Demo completed successfully!")
            
        else:
            # Run custom itinerary
            print(f"🧳 Planning trip to {args.destination}")
            print(f"📅 {args.start_date} to {args.end_date}")
            print(f"👥 Group size: {args.group_size}")
            print(f"💰 Budget: ${args.budget}")
            print("=" * 50)
            
            # Create preferences from arguments
            preferences = {
                "accommodation_types": args.accommodation_types,
                "activity_types": args.activity_types,
                "budget_level": args.budget_level,
                "group_size": args.group_size,
                "children": args.children,
                "dietary_restrictions": args.dietary_restrictions
            }
            
            # Create itinerary
            itinerary = planner.create_itinerary(
                destination=args.destination,
                start_date=args.start_date,
                end_date=args.end_date,
                budget=args.budget,
                preferences=preferences
            )
            
            print(f"✅ Itinerary created for {itinerary['destination']}")
            print(f"📅 Duration: {itinerary.get('duration_days', 'N/A')} days")
            print(f"💰 Total Cost: ${itinerary['total_cost']:.2f}")
            print(f"📊 Budget Status: {'✅ Within Budget' if itinerary.get('remaining_budget', 0) >= 0 else '⚠️ Over Budget'}")
            
            # Show quality metrics and disclaimers
            if 'quality_metrics' in itinerary:
                qm = itinerary['quality_metrics']
                print("\n🧠 Quality Metrics:")
                print(f"- Activity Variety Score: {qm.get('activity_variety_score', 0):.2f}")
                print(f"- Cost Realism Score: {qm.get('cost_realism_score', 0):.2f}")
                print(f"- Geographic Efficiency: {qm.get('geographic_efficiency', 0):.2f}")
                print(f"- Data Completeness: {qm.get('data_completeness', 0):.2f}")
                print(f"- Overall Quality: {qm.get('overall_quality', 0):.2f}")
                if qm.get('issues'):
                    print(f"  Issues: {qm['issues']}")
                if qm.get('warnings'):
                    print(f"  Warnings: {qm['warnings']}")
                if qm.get('suggestions'):
                    print(f"  Suggestions: {qm['suggestions']}")
            if 'disclaimers' in itinerary:
                print("\n⚠️ Disclaimers:")
                for disclaimer in itinerary['disclaimers']:
                    print(f"- {disclaimer}")
            
            # Generate PDF if requested
            if args.output_pdf:
                os.makedirs(os.path.dirname(args.output_pdf), exist_ok=True)
                if planner.generate_pdf(itinerary, args.output_pdf):
                    print(f"📄 PDF generated: {args.output_pdf}")
            
            # Get Wikivoyage guide for the destination
            guide = planner.get_wikivoyage_guide(args.destination)
            if guide["success"]:
                print(f"\n🌐 Travel Guide: {guide['guide']['extract'][:300]}...")
            
            print("\n🎉 Trip planning completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    main() 