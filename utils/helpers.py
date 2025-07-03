import re
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def validate_date_format(date_str: str) -> bool:
    """Validate if a date string is in YYYY-MM-DD format."""
    try:
        date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate that start_date is before end_date."""
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        return start < end
    except ValueError:
        return False


def format_location(location: str) -> str:
    """Format location string for better API compatibility."""
    # Remove extra whitespace and normalize
    formatted = re.sub(r'\s+', ' ', location.strip())
    
    # Ensure it ends with a country/state if not already present
    if not re.search(r',\s*[A-Z]{2,3}$', formatted):
        # Add common country codes if missing
        if 'united states' in formatted.lower() or 'usa' in formatted.lower():
            formatted += ', US'
        elif 'canada' in formatted.lower():
            formatted += ', CA'
        elif 'united kingdom' in formatted.lower() or 'uk' in formatted.lower():
            formatted += ', UK'
    
    return formatted


def calculate_trip_duration(start_date: str, end_date: str) -> int:
    """Calculate trip duration in days."""
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        return (end - start).days + 1
    except ValueError:
        return 0


def estimate_daily_budget(total_budget: float, duration: int) -> float:
    """Estimate daily budget from total budget and trip duration."""
    if duration <= 0:
        return 0.0
    return total_budget / duration


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount with proper symbol."""
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "CAD": "C$",
        "AUD": "A$"
    }
    
    symbol = currency_symbols.get(currency, "$")
    return f"{symbol}{amount:,.2f}"


def validate_budget(budget: float) -> bool:
    """Validate that budget is reasonable."""
    return 0 < budget <= 100000  # Between $1 and $100k


def sanitize_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate user preferences."""
    sanitized = {}
    
    # Valid accommodation types
    valid_accommodation_types = ["hotel", "hostel", "camping", "glamping", "resort", "cabin"]
    
    # Valid activity types
    valid_activity_types = ["outdoor", "cultural", "adventure", "relaxation", "food", "shopping", "nightlife"]
    
    # Valid budget levels
    valid_budget_levels = ["budget", "moderate", "luxury"]
    
    # Sanitize accommodation types
    if "accommodation_types" in preferences:
        acc_types = preferences["accommodation_types"]
        if isinstance(acc_types, list):
            sanitized["accommodation_types"] = [
                acc_type for acc_type in acc_types 
                if acc_type.lower() in valid_accommodation_types
            ]
    
    # Sanitize activity types
    if "activity_types" in preferences:
        act_types = preferences["activity_types"]
        if isinstance(act_types, list):
            sanitized["activity_types"] = [
                act_type for act_type in act_types 
                if act_type.lower() in valid_activity_types
            ]
    
    # Sanitize budget level
    if "budget_level" in preferences:
        budget_level = preferences["budget_level"]
        if isinstance(budget_level, str) and budget_level.lower() in valid_budget_levels:
            sanitized["budget_level"] = budget_level.lower()
    
    # Sanitize numeric values
    if "max_daily_budget" in preferences:
        try:
            daily_budget = float(preferences["max_daily_budget"])
            if validate_budget(daily_budget):
                sanitized["max_daily_budget"] = daily_budget
        except (ValueError, TypeError):
            pass
    
    if "group_size" in preferences:
        try:
            group_size = int(preferences["group_size"])
            if 1 <= group_size <= 20:  # Reasonable group size
                sanitized["group_size"] = group_size
        except (ValueError, TypeError):
            pass
    
    # Sanitize boolean values
    if "children" in preferences:
        sanitized["children"] = bool(preferences["children"])
    
    # Sanitize lists
    if "dietary_restrictions" in preferences:
        restrictions = preferences["dietary_restrictions"]
        if isinstance(restrictions, list):
            sanitized["dietary_restrictions"] = [
                str(restriction).strip() for restriction in restrictions
                if restriction and len(str(restriction).strip()) <= 50
            ]
    
    if "accessibility_needs" in preferences:
        needs = preferences["accessibility_needs"]
        if isinstance(needs, list):
            sanitized["accessibility_needs"] = [
                str(need).strip() for need in needs
                if need and len(str(need).strip()) <= 50
            ]
    
    return sanitized


def generate_trip_summary(itinerary: Any) -> Dict[str, Any]:
    """Generate a summary of the trip for display."""
    try:
        return {
            "destination": itinerary.destination,
            "duration": itinerary.duration_days,
            "start_date": itinerary.start_date.strftime("%B %d, %Y"),
            "end_date": itinerary.end_date.strftime("%B %d, %Y"),
            "total_cost": format_currency(itinerary.total_cost),
            "budget_status": "Within Budget" if itinerary.remaining_budget >= 0 else "Over Budget",
            "remaining_budget": format_currency(itinerary.remaining_budget),
            "total_activities": sum(len(day.activities) for day in itinerary.day_plans),
            "total_restaurants": sum(len(day.restaurants) for day in itinerary.day_plans),
            "cost_breakdown": {
                "accommodation": format_currency(itinerary.cost_breakdown.get("accommodation", 0)),
                "activities": format_currency(itinerary.cost_breakdown.get("activities", 0)),
                "dining": format_currency(itinerary.cost_breakdown.get("dining", 0)),
                "transportation": format_currency(itinerary.cost_breakdown.get("transportation", 0)),
                "miscellaneous": format_currency(itinerary.cost_breakdown.get("miscellaneous", 0))
            }
        }
    except Exception as e:
        logger.error(f"Error generating trip summary: {e}")
        return {}


def format_activity_summary(activity: Any) -> Dict[str, Any]:
    """Format activity information for display."""
    try:
        return {
            "name": activity.name,
            "type": activity.type.value.title(),
            "duration": f"{activity.duration_hours}h",
            "cost": format_currency(activity.cost),
            "description": activity.description or "No description available",
            "location": activity.location.name if activity.location else "Location not specified"
        }
    except Exception as e:
        logger.error(f"Error formatting activity summary: {e}")
        return {}


def format_restaurant_summary(restaurant: Any) -> Dict[str, Any]:
    """Format restaurant information for display."""
    try:
        return {
            "name": restaurant.name,
            "cuisine": restaurant.cuisine_type,
            "price_level": "$" * restaurant.price_level,
            "cost_per_person": format_currency(restaurant.cost_per_person),
            "rating": f"{restaurant.rating}/5" if restaurant.rating else "No rating",
            "description": restaurant.description or "No description available"
        }
    except Exception as e:
        logger.error(f"Error formatting restaurant summary: {e}")
        return {}


def get_season_from_date(date_obj: date) -> str:
    """Get season from date."""
    month = date_obj.month
    
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


def is_weekend(date_obj: date) -> bool:
    """Check if date falls on a weekend."""
    return date_obj.weekday() >= 5  # Saturday = 5, Sunday = 6


def calculate_optimal_activity_order(activities: List[Any]) -> List[Any]:
    """Calculate optimal order for activities based on type and duration."""
    if not activities:
        return []
    
    # Sort activities by type and duration
    # Outdoor activities in morning, cultural in afternoon, nightlife in evening
    type_priority = {
        "outdoor": 1,
        "cultural": 2,
        "adventure": 3,
        "relaxation": 4,
        "food": 5,
        "shopping": 6,
        "nightlife": 7
    }
    
    sorted_activities = sorted(
        activities,
        key=lambda x: (type_priority.get(x.type.value, 8), x.duration_hours)
    )
    
    return sorted_activities


def validate_api_response(response: Dict[str, Any]) -> bool:
    """Validate API response structure."""
    required_fields = ["success"]
    
    for field in required_fields:
        if field not in response:
            return False
    
    return response.get("success", False)


def format_error_message(error: Exception) -> str:
    """Format error message for user display."""
    error_str = str(error)
    
    # Common error patterns
    if "API key" in error_str.lower():
        return "API key is missing or invalid. Please check your configuration."
    elif "rate limit" in error_str.lower():
        return "API rate limit exceeded. Please try again later."
    elif "not found" in error_str.lower():
        return "The requested information was not found."
    elif "network" in error_str.lower():
        return "Network error. Please check your internet connection."
    else:
        return f"An error occurred: {error_str}" 