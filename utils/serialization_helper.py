"""
Serialization Helper
Converts complex data structures to JSON-serializable format for web UI.
"""

import json
from typing import Dict, Any, List
from datetime import datetime, date, time
from dataclasses import asdict, is_dataclass

def serialize_for_web(data: Any) -> Any:
    """
    Convert complex data structures to JSON-serializable format.
    
    Args:
        data: Any data structure to serialize
        
    Returns:
        JSON-serializable version of the data
    """
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, time):
        return data.strftime('%H:%M')
    elif isinstance(data, dict):
        return {key: serialize_for_web(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_for_web(item) for item in data]
    elif is_dataclass(data):
        return serialize_for_web(asdict(data))
    else:
        # Try to convert to string for unknown types
        try:
            return str(data)
        except:
            return None

def serialize_itinerary(itinerary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specifically serialize an itinerary for web display.
    
    Args:
        itinerary: The itinerary dictionary
        
    Returns:
        Serialized itinerary ready for JSON response
    """
    if not isinstance(itinerary, dict):
        return {"error": "Invalid itinerary format"}
    
    # Create a clean copy for serialization
    serialized = {}
    
    for key, value in itinerary.items():
        if key == "day_plans":
            # Special handling for day plans
            serialized[key] = serialize_day_plans(value)
        elif key == "quality_metrics":
            # Ensure quality metrics are serializable
            serialized[key] = serialize_for_web(value)
        elif key == "disclaimers":
            # Disclaimers should already be strings
            serialized[key] = value if isinstance(value, list) else []
        else:
            serialized[key] = serialize_for_web(value)
    
    return serialized

def serialize_day_plans(day_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize day plans with special handling for time slots.
    
    Args:
        day_plans: List of day plan dictionaries
        
    Returns:
        Serialized day plans
    """
    if not isinstance(day_plans, list):
        return []
    
    serialized_plans = []
    
    for day_plan in day_plans:
        if not isinstance(day_plan, dict):
            continue
            
        serialized_plan = {}
        
        for key, value in day_plan.items():
            if key == "time_slots":
                # Convert time slots to serializable format
                serialized_plan[key] = serialize_time_slots(value)
            elif key == "schedule_validation":
                # Ensure schedule validation is serializable
                serialized_plan[key] = serialize_for_web(value)
            elif key == "activities":
                # Ensure activities are serializable
                serialized_plan[key] = serialize_activities(value)
            elif key == "restaurants":
                # Ensure restaurants are serializable
                serialized_plan[key] = serialize_restaurants(value)
            elif key == "accommodations":
                # Ensure accommodations are serializable
                serialized_plan[key] = serialize_accommodations(value)
            else:
                serialized_plan[key] = serialize_for_web(value)
        
        serialized_plans.append(serialized_plan)
    
    return serialized_plans

def serialize_time_slots(time_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize time slots for web display.
    
    Args:
        time_slots: List of time slot dictionaries
        
    Returns:
        Serialized time slots
    """
    if not isinstance(time_slots, list):
        return []
    
    serialized_slots = []
    
    for slot in time_slots:
        if not isinstance(slot, dict):
            continue
            
        serialized_slot = {}
        
        for key, value in slot.items():
            if key in ["start_time", "end_time"]:
                # Convert time objects to strings
                if isinstance(value, time):
                    serialized_slot[key] = value.strftime('%H:%M')
                else:
                    serialized_slot[key] = serialize_for_web(value)
            else:
                serialized_slot[key] = serialize_for_web(value)
        
        serialized_slots.append(serialized_slot)
    
    return serialized_slots

def serialize_activities(activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize activities for web display.
    
    Args:
        activities: List of activity dictionaries
        
    Returns:
        Serialized activities
    """
    if not isinstance(activities, list):
        return []
    
    serialized_activities = []
    
    for activity in activities:
        if not isinstance(activity, dict):
            continue
            
        serialized_activity = {}
        
        for key, value in activity.items():
            if key == "location":
                # Ensure location is properly serialized
                if isinstance(value, dict):
                    serialized_activity[key] = serialize_for_web(value)
                else:
                    serialized_activity[key] = {"name": str(value)}
            else:
                serialized_activity[key] = serialize_for_web(value)
        
        serialized_activities.append(serialized_activity)
    
    return serialized_activities

def serialize_restaurants(restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize restaurants for web display.
    
    Args:
        restaurants: List of restaurant dictionaries
        
    Returns:
        Serialized restaurants
    """
    if not isinstance(restaurants, list):
        return []
    
    serialized_restaurants = []
    
    for restaurant in restaurants:
        if not isinstance(restaurant, dict):
            continue
            
        serialized_restaurant = {}
        
        for key, value in restaurant.items():
            if key == "location":
                # Ensure location is properly serialized
                if isinstance(value, dict):
                    serialized_restaurant[key] = serialize_for_web(value)
                else:
                    serialized_restaurant[key] = {"name": str(value)}
            else:
                serialized_restaurant[key] = serialize_for_web(value)
        
        serialized_restaurants.append(serialized_restaurant)
    
    return serialized_restaurants

def serialize_accommodations(accommodations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize accommodations for web display.
    
    Args:
        accommodations: List of accommodation dictionaries
        
    Returns:
        Serialized accommodations
    """
    if not isinstance(accommodations, list):
        return []
    
    serialized_accommodations = []
    
    for accommodation in accommodations:
        if not isinstance(accommodation, dict):
            continue
            
        serialized_accommodation = {}
        
        for key, value in accommodation.items():
            if key == "location":
                # Ensure location is properly serialized
                if isinstance(value, dict):
                    serialized_accommodation[key] = serialize_for_web(value)
                else:
                    serialized_accommodation[key] = {"name": str(value)}
            else:
                serialized_accommodation[key] = serialize_for_web(value)
        
        serialized_accommodations.append(serialized_accommodation)
    
    return serialized_accommodations 