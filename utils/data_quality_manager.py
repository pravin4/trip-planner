"""
Data Quality and Realism Manager
Handles activity variety, cost realism, missing data, and disclaimers.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Metrics for itinerary quality assessment"""
    activity_variety_score: float  # 0-1, higher is better
    cost_realism_score: float      # 0-1, higher is better
    geographic_efficiency: float   # 0-1, higher is better
    data_completeness: float       # 0-1, higher is better
    overall_quality: float         # 0-1, higher is better
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]

class DataQualityManager:
    """Comprehensive data quality and realism management system"""
    
    # Activity type diversity weights (should be balanced across days)
    ACTIVITY_WEIGHTS = {
        "cultural": 0.25,      # Museums, theaters, historical sites
        "outdoor": 0.25,       # Parks, hiking, beaches
        "entertainment": 0.20,  # Shopping, amusement parks, casinos
        "food": 0.15,          # Restaurants, food tours, cafes
        "relaxation": 0.15     # Spas, gardens, scenic views
    }
    
    # Realistic cost ranges by activity type (per person)
    COST_RANGES = {
        "museum": (15, 25),
        "art_gallery": (10, 20),
        "theater": (50, 150),
        "concert": (40, 200),
        "historical_site": (10, 20),
        "church": (0, 5),
        "monument": (0, 10),
        "hiking": (0, 15),
        "beach": (0, 10),
        "park": (0, 5),
        "garden": (5, 15),
        "zoo": (20, 35),
        "aquarium": (25, 40),
        "amusement_park": (80, 150),
        "casino": (0, 50),
        "shopping": (0, 100),
        "spa": (80, 200),
        "restaurant": (20, 80),
        "cafe": (8, 25),
        "food_tour": (60, 120),
        "wine_tasting": (40, 80),
        "default": (10, 30)
    }
    
    # Realistic duration ranges by activity type (in hours)
    DURATION_RANGES = {
        "museum": (1.5, 3.0),
        "art_gallery": (1.0, 2.0),
        "theater": (2.5, 4.0),
        "concert": (2.0, 3.5),
        "historical_site": (1.0, 2.0),
        "church": (0.5, 1.0),
        "monument": (0.5, 1.0),
        "hiking": (2.0, 6.0),
        "beach": (2.0, 6.0),
        "park": (1.0, 3.0),
        "garden": (0.5, 2.0),
        "zoo": (2.0, 4.0),
        "aquarium": (1.5, 3.0),
        "amusement_park": (4.0, 8.0),
        "casino": (2.0, 6.0),
        "shopping": (1.0, 4.0),
        "spa": (1.0, 3.0),
        "restaurant": (1.0, 2.0),
        "cafe": (0.5, 1.5),
        "food_tour": (2.0, 4.0),
        "wine_tasting": (1.5, 3.0),
        "default": (1.0, 2.0)
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def improve_itinerary_quality(self, itinerary: Dict[str, Any], 
                                preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Improve the overall quality and realism of an itinerary.
        
        Args:
            itinerary: The itinerary to improve
            preferences: User preferences
            
        Returns:
            Improved itinerary with quality metrics
        """
        try:
            day_plans = itinerary.get("day_plans", [])
            
            # Step 0: Clean location strings (fix geocoding issues)
            day_plans = self._clean_location_strings(day_plans)
            
            # Step 1: Improve activity variety
            day_plans = self._improve_activity_variety(day_plans, preferences)
            
            # Step 2: Improve cost realism
            day_plans = self._improve_cost_realism(day_plans, preferences)
            
            # Step 3: Fill missing data
            day_plans = self._fill_missing_data(day_plans, preferences)
            
            # Step 4: Validate geographic logic
            day_plans = self._validate_geographic_logic(day_plans)
            
            # Step 5: Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(day_plans, preferences)
            
            # Step 6: Add disclaimers
            disclaimers = self._generate_disclaimers(day_plans, quality_metrics)
            
            # Update itinerary
            itinerary["day_plans"] = day_plans
            itinerary["quality_metrics"] = quality_metrics.__dict__
            itinerary["disclaimers"] = disclaimers
            
            return itinerary
            
        except Exception as e:
            self.logger.error(f"Error improving itinerary quality: {e}")
            return itinerary
    
    def _improve_activity_variety(self, day_plans: List[Dict[str, Any]], 
                                preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Improve activity variety across days."""
        
        # Analyze current activity distribution
        activity_types = []
        for day_plan in day_plans:
            for activity in day_plan.get("activities", []):
                activity_type = activity.get("type", "default")
                activity_types.append(activity_type)
        
        # Calculate current distribution
        type_counts = {}
        for activity_type in activity_types:
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        
        # Identify underrepresented activity types
        total_activities = len(activity_types)
        underrepresented = []
        
        for target_type, target_weight in self.ACTIVITY_WEIGHTS.items():
            current_count = type_counts.get(target_type, 0)
            target_count = int(total_activities * target_weight)
            
            if current_count < target_count:
                underrepresented.append((target_type, target_count - current_count))
        
        # Suggest activity additions for underrepresented types
        for day_plan in day_plans:
            if underrepresented:
                target_type, needed = underrepresented[0]
                
                # Add a suggested activity of the underrepresented type
                suggested_activity = self._generate_suggested_activity(target_type, day_plan)
                if suggested_activity:
                    day_plan["activities"].append(suggested_activity)
                    underrepresented[0] = (target_type, needed - 1)
                    
                    if needed <= 1:
                        underrepresented.pop(0)
        
        return day_plans
    
    def _generate_suggested_activity(self, activity_type: str, 
                                   day_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a suggested activity of the specified type."""
        
        location = day_plan.get("cluster_name", "Unknown")
        
        # Activity suggestions by type
        suggestions = {
            "cultural": [
                {"name": f"Local Museum", "type": "museum", "description": "Explore local history and culture"},
                {"name": f"Art Gallery", "type": "art_gallery", "description": "View local and international art"},
                {"name": f"Historical Site", "type": "historical_site", "description": "Visit a significant historical location"}
            ],
            "outdoor": [
                {"name": f"City Park", "type": "park", "description": "Enjoy outdoor recreation and nature"},
                {"name": f"Scenic Viewpoint", "type": "outdoor", "description": "Take in beautiful views of the area"},
                {"name": f"Walking Trail", "type": "hiking", "description": "Explore the area on foot"}
            ],
            "entertainment": [
                {"name": f"Shopping District", "type": "shopping", "description": "Browse local shops and boutiques"},
                {"name": f"Entertainment Center", "type": "entertainment", "description": "Enjoy local entertainment options"}
            ],
            "food": [
                {"name": f"Local Cafe", "type": "cafe", "description": "Try local coffee and pastries"},
                {"name": f"Food Market", "type": "food", "description": "Explore local food vendors and specialties"}
            ],
            "relaxation": [
                {"name": f"Botanical Garden", "type": "garden", "description": "Relax in beautiful garden surroundings"},
                {"name": f"Scenic Overlook", "type": "relaxation", "description": "Peaceful spot to enjoy the view"}
            ]
        }
        
        if activity_type in suggestions:
            activity = random.choice(suggestions[activity_type])
            activity["location"] = {"name": location}
            return activity
        
        return None
    
    def _improve_cost_realism(self, day_plans: List[Dict[str, Any]], 
                            preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Improve cost realism for activities and restaurants."""
        
        budget_level = preferences.get("budget_level", "moderate")
        cost_multiplier = {
            "budget": 0.7,
            "moderate": 1.0,
            "luxury": 1.5
        }.get(budget_level, 1.0)
        
        for day_plan in day_plans:
            # Improve activity costs
            for activity in day_plan.get("activities", []):
                if isinstance(activity, dict):
                    activity_type = activity.get("type", "default")
                    cost_range = self.COST_RANGES.get(activity_type, self.COST_RANGES["default"])
                    
                    # Set realistic cost based on type and budget level
                    base_cost = random.uniform(cost_range[0], cost_range[1])
                    adjusted_cost = base_cost * cost_multiplier
                    
                    activity["cost"] = round(adjusted_cost, 2)
                    
                    # Also improve duration if missing
                    if "duration_hours" not in activity:
                        duration_range = self.DURATION_RANGES.get(activity_type, self.DURATION_RANGES["default"])
                        activity["duration_hours"] = round(random.uniform(duration_range[0], duration_range[1]), 1)
            
            # Improve restaurant costs
            for restaurant in day_plan.get("restaurants", []):
                if isinstance(restaurant, dict):
                    cuisine_type = restaurant.get("cuisine_type", "Local")
                    price_level = restaurant.get("price_level", 2)
                    
                    # Realistic cost per person based on cuisine and price level
                    base_cost = {
                        1: 15,  # Budget
                        2: 30,  # Moderate
                        3: 50,  # Expensive
                        4: 80   # Luxury
                    }.get(price_level, 30)
                    
                    # Adjust for cuisine type
                    cuisine_multiplier = {
                        "fine_dining": 1.5,
                        "steakhouse": 1.3,
                        "seafood": 1.2,
                        "local": 1.0,
                        "casual": 0.8,
                        "fast_food": 0.5
                    }.get(cuisine_type.lower(), 1.0)
                    
                    adjusted_cost = base_cost * cuisine_multiplier * cost_multiplier
                    restaurant["cost_per_person"] = round(adjusted_cost, 2)
        
        return day_plans
    
    def _fill_missing_data(self, day_plans: List[Dict[str, Any]], 
                          preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fill missing data with realistic defaults."""
        
        for day_plan in day_plans:
            # Fill missing activity data
            for activity in day_plan.get("activities", []):
                if isinstance(activity, dict):
                    # Ensure location data
                    if "location" not in activity:
                        activity["location"] = {"name": day_plan.get("cluster_name", "Unknown")}
                    
                    # Ensure type
                    if "type" not in activity:
                        activity["type"] = "default"
                    
                    # Ensure description
                    if "description" not in activity:
                        activity["description"] = f"Visit {activity.get('name', 'this location')}"
                    
                    # Ensure rating
                    if "rating" not in activity:
                        activity["rating"] = round(random.uniform(3.5, 4.8), 1)
                    
                    # Ensure price level
                    if "price_level" not in activity:
                        activity["price_level"] = random.randint(1, 3)
            
            # Fill missing restaurant data
            for restaurant in day_plan.get("restaurants", []):
                if isinstance(restaurant, dict):
                    # Ensure location data
                    if "location" not in restaurant:
                        restaurant["location"] = {"name": day_plan.get("cluster_name", "Unknown")}
                    
                    # Ensure cuisine type
                    if "cuisine_type" not in restaurant:
                        restaurant["cuisine_type"] = "Local"
                    
                    # Ensure rating
                    if "rating" not in restaurant:
                        restaurant["rating"] = round(random.uniform(3.5, 4.8), 1)
                    
                    # Ensure price level
                    if "price_level" not in restaurant:
                        restaurant["price_level"] = random.randint(1, 3)
            
            # Fill missing accommodation data
            for accommodation in day_plan.get("accommodations", []):
                if isinstance(accommodation, dict):
                    # Ensure location data
                    if "location" not in accommodation:
                        accommodation["location"] = {"name": day_plan.get("cluster_name", "Unknown")}
                    
                    # Ensure rating
                    if "rating" not in accommodation:
                        accommodation["rating"] = round(random.uniform(3.5, 4.8), 1)
                    
                    # Ensure price level
                    if "price_level" not in accommodation:
                        accommodation["price_level"] = random.randint(1, 4)
        
        return day_plans
    
    def _validate_geographic_logic(self, day_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and improve geographic logic."""
        
        for day_plan in day_plans:
            activities = day_plan.get("activities", [])
            cluster_name = day_plan.get("cluster_name", "Unknown")
            
            # Ensure all activities have consistent location data
            for activity in activities:
                if isinstance(activity, dict):
                    if "location" not in activity:
                        activity["location"] = {"name": cluster_name}
                    elif isinstance(activity["location"], dict):
                        if "name" not in activity["location"]:
                            activity["location"]["name"] = cluster_name
            
            # Add geographic validation note
            day_plan["geographic_validation"] = {
                "cluster_name": cluster_name,
                "activities_in_cluster": len(activities),
                "geographic_efficiency": "high" if len(activities) <= 4 else "moderate"
            }
        
        return day_plans
    
    def _calculate_quality_metrics(self, day_plans: List[Dict[str, Any]], 
                                 preferences: Dict[str, Any]) -> QualityMetrics:
        """Calculate comprehensive quality metrics."""
        
        issues = []
        warnings = []
        suggestions = []
        
        # Calculate activity variety score
        activity_types = []
        for day_plan in day_plans:
            for activity in day_plan.get("activities", []):
                if isinstance(activity, dict):
                    activity_types.append(activity.get("type", "default"))
        
        type_counts = {}
        for activity_type in activity_types:
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        
        total_activities = len(activity_types)
        variety_score = 0.0
        
        if total_activities > 0:
            # Calculate how well distributed the activities are
            expected_distribution = {k: v * total_activities for k, v in self.ACTIVITY_WEIGHTS.items()}
            actual_distribution = type_counts
            
            # Calculate similarity to expected distribution
            max_diff = total_activities
            actual_diff = sum(abs(actual_distribution.get(k, 0) - expected_distribution.get(k, 0)) 
                            for k in set(actual_distribution.keys()) | set(expected_distribution.keys()))
            
            variety_score = max(0.0, 1.0 - (actual_diff / max_diff))
        
        # Calculate cost realism score
        cost_score = 1.0  # Assume good for now, could be enhanced with more validation
        
        # Calculate geographic efficiency
        geo_score = 1.0
        for day_plan in day_plans:
            activities = day_plan.get("activities", [])
            if len(activities) > 6:
                geo_score *= 0.8  # Penalize over-packed days
                warnings.append(f"Day {day_plan.get('date', 'Unknown')} has many activities")
        
        # Calculate data completeness
        completeness_score = 1.0
        missing_fields = 0
        total_fields = 0
        
        for day_plan in day_plans:
            for activity in day_plan.get("activities", []):
                if isinstance(activity, dict):
                    required_fields = ["name", "type", "location", "cost", "duration_hours"]
                    for field in required_fields:
                        total_fields += 1
                        if field not in activity or activity[field] is None:
                            missing_fields += 1
        
        if total_fields > 0:
            completeness_score = 1.0 - (missing_fields / total_fields)
        
        # Overall quality score
        overall_quality = (variety_score + cost_score + geo_score + completeness_score) / 4
        
        # Generate issues and warnings
        if variety_score < 0.5:
            issues.append("Low activity variety - consider adding different types of activities")
        
        if geo_score < 0.7:
            warnings.append("Some days may be over-packed")
        
        if completeness_score < 0.8:
            warnings.append("Some activity data is incomplete")
        
        if overall_quality < 0.7:
            suggestions.append("Consider reviewing the itinerary for better balance")
        
        return QualityMetrics(
            activity_variety_score=variety_score,
            cost_realism_score=cost_score,
            geographic_efficiency=geo_score,
            data_completeness=completeness_score,
            overall_quality=overall_quality,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _generate_disclaimers(self, day_plans: List[Dict[str, Any]], 
                            quality_metrics: QualityMetrics) -> List[str]:
        """Generate appropriate disclaimers for the itinerary."""
        
        disclaimers = [
            "⚠️ **Cost Estimates**: All costs are estimates and may vary based on season, availability, and booking time.",
            "⚠️ **Availability**: Attractions and restaurants may have limited availability or require advance booking.",
            "⚠️ **Weather**: Outdoor activities may be affected by weather conditions.",
            "⚠️ **Opening Hours**: Please verify opening hours before visiting attractions.",
            "⚠️ **Transportation**: Travel times may vary due to traffic, weather, or public transit schedules."
        ]
        
        # Add quality-specific disclaimers
        if quality_metrics.overall_quality < 0.7:
            disclaimers.append("⚠️ **Itinerary Quality**: This itinerary may benefit from additional planning and customization.")
        
        if quality_metrics.activity_variety_score < 0.5:
            disclaimers.append("⚠️ **Activity Variety**: Consider adding more diverse activities to enhance your experience.")
        
        if quality_metrics.geographic_efficiency < 0.8:
            disclaimers.append("⚠️ **Geographic Efficiency**: Some days may be quite busy - consider spreading activities across more days.")
        
        return disclaimers 

    def _clean_location_strings(self, day_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean up malformed location strings that cause geocoding issues."""
        
        for day_plan in day_plans:
            # Clean activities
            for activity in day_plan.get("activities", []):
                if "location" in activity:
                    activity["location"] = self._clean_location(activity["location"])
                if "name" in activity:
                    activity["name"] = self._clean_activity_name(activity["name"])
            
            # Clean accommodations
            for accommodation in day_plan.get("accommodations", []):
                if "location" in accommodation:
                    accommodation["location"] = self._clean_location(accommodation["location"])
                if "name" in accommodation:
                    accommodation["name"] = self._clean_accommodation_name(accommodation["name"])
            
            # Clean restaurants
            for restaurant in day_plan.get("restaurants", []):
                if "location" in restaurant:
                    restaurant["location"] = self._clean_location(restaurant["location"])
                if "name" in restaurant:
                    restaurant["name"] = self._clean_restaurant_name(restaurant["name"])
        
        return day_plans
    
    def _clean_location(self, location: str) -> str:
        """Clean a location string to make it geocodable."""
        if not location:
            return location
        
        # Remove duplicate parts like "Big Sur River Gorge, Big Sur River Gorge and nearby attractions"
        if "," in location:
            parts = [part.strip() for part in location.split(",")]
            # Remove duplicates and "and nearby attractions" type suffixes
            cleaned_parts = []
            for part in parts:
                if part not in cleaned_parts and not any(suffix in part.lower() for suffix in [
                    "and nearby attractions", "and surrounding area", "and vicinity"
                ]):
                    cleaned_parts.append(part)
            
            # Take the first meaningful part
            if cleaned_parts:
                return cleaned_parts[0]
        
        return location
    
    def _clean_activity_name(self, name: str) -> str:
        """Clean an activity name."""
        if not name:
            return name
        
        # Remove location suffixes that shouldn't be in the name
        suffixes_to_remove = [
            " and nearby attractions",
            " and surrounding area", 
            " and vicinity",
            ", Big Sur River Gorge and nearby attractions",
            ", Andrew Molera State Park and nearby attractions"
        ]
        
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        return name.strip()
    
    def _clean_accommodation_name(self, name: str) -> str:
        """Clean an accommodation name."""
        return self._clean_activity_name(name)
    
    def _clean_restaurant_name(self, name: str) -> str:
        """Clean a restaurant name."""
        return self._clean_activity_name(name) 