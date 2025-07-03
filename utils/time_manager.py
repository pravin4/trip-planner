"""
Time Management Module
Handles realistic scheduling, activity durations, meal times, and opening hours.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class TimeSlot:
    """Represents a time slot for an activity"""
    start_time: time
    end_time: time
    duration_minutes: int
    activity_name: str
    activity_type: str
    location: str
    notes: str = ""

@dataclass
class DaySchedule:
    """Represents a complete day schedule"""
    date: str
    time_slots: List[TimeSlot]
    total_activity_time: int
    total_travel_time: int
    total_rest_time: int
    meal_times: Dict[str, time]
    efficiency_score: float

class TimeManager:
    """Comprehensive time management system"""
    
    # Standard activity durations (in minutes)
    ACTIVITY_DURATIONS = {
        # Cultural activities
        "museum": 120,  # 2 hours
        "art_gallery": 90,  # 1.5 hours
        "theater": 180,  # 3 hours (including show)
        "concert": 150,  # 2.5 hours
        "historical_site": 90,  # 1.5 hours
        "church": 60,  # 1 hour
        "monument": 45,  # 45 minutes
        
        # Outdoor activities
        "hiking": 180,  # 3 hours
        "beach": 240,  # 4 hours
        "park": 90,  # 1.5 hours
        "garden": 60,  # 1 hour
        "zoo": 180,  # 3 hours
        "aquarium": 120,  # 2 hours
        "botanical_garden": 90,  # 1.5 hours
        
        # Entertainment
        "amusement_park": 360,  # 6 hours
        "water_park": 300,  # 5 hours
        "casino": 180,  # 3 hours
        "shopping": 120,  # 2 hours
        "spa": 120,  # 2 hours
        
        # Food & Dining
        "restaurant": 90,  # 1.5 hours
        "cafe": 60,  # 1 hour
        "food_tour": 180,  # 3 hours
        "wine_tasting": 120,  # 2 hours
        
        # Transportation
        "travel": 0,  # Will be calculated separately
        "check_in": 30,  # 30 minutes
        "check_out": 30,  # 30 minutes
        
        # Default
        "default": 90  # 1.5 hours
    }
    
    # Meal time windows (in hours)
    MEAL_TIMES = {
        "breakfast": (7, 9),  # 7-9 AM
        "lunch": (12, 14),    # 12-2 PM
        "dinner": (18, 21),   # 6-9 PM
        "snack": (15, 16)     # 3-4 PM
    }
    
    # Opening hours for different activity types
    OPENING_HOURS = {
        "museum": (9, 17),      # 9 AM - 5 PM
        "art_gallery": (10, 18), # 10 AM - 6 PM
        "theater": (19, 23),     # 7 PM - 11 PM
        "restaurant": (6, 23),   # 6 AM - 11 PM
        "cafe": (6, 22),         # 6 AM - 10 PM
        "shopping": (9, 21),     # 9 AM - 9 PM
        "park": (6, 22),         # 6 AM - 10 PM
        "beach": (6, 20),        # 6 AM - 8 PM
        "hiking": (6, 18),       # 6 AM - 6 PM
        "default": (9, 18)       # 9 AM - 6 PM
    }
    
    # Buffer times (in minutes)
    BUFFER_TIMES = {
        "between_activities": 15,  # 15 minutes between activities
        "meal_prep": 30,          # 30 minutes before meal
        "travel_buffer": 10,      # 10 minutes travel buffer
        "check_in_buffer": 45,    # 45 minutes for check-in
        "morning_start": 30,      # 30 minutes to get ready
        "evening_end": 60         # 1 hour to wind down
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_realistic_schedule(self, activities: List[Dict[str, Any]], 
                                travel_legs: List[Dict[str, Any]], 
                                preferences: Dict[str, Any]) -> DaySchedule:
        """
        Create a realistic daily schedule with proper time management.
        
        Args:
            activities: List of activities for the day
            travel_legs: Transportation legs between activities
            preferences: User preferences
            
        Returns:
            DaySchedule with optimized time slots
        """
        
        # Start with a clean slate
        time_slots = []
        current_time = time(9, 0)  # Start at 9 AM
        
        # Add morning buffer
        current_time = self._add_minutes(current_time, self.BUFFER_TIMES["morning_start"])
        
        # Process activities and travel
        for i, activity in enumerate(activities):
            # Add travel time if not first activity
            if i > 0 and travel_legs:
                travel_leg = travel_legs[i - 1] if i - 1 < len(travel_legs) else None
                if travel_leg:
                    travel_duration = travel_leg.get("duration_minutes", 0)
                    if travel_duration > 0:
                        travel_slot = TimeSlot(
                            start_time=current_time,
                            end_time=self._add_minutes(current_time, travel_duration),
                            duration_minutes=travel_duration,
                            activity_name=f"Travel to {activity.get('name', 'Unknown')}",
                            activity_type="travel",
                            location=f"From {travel_leg.get('from', 'Unknown')}",
                            notes=travel_leg.get('notes', '')
                        )
                        time_slots.append(travel_slot)
                        current_time = travel_slot.end_time
                        
                        # Add travel buffer
                        current_time = self._add_minutes(current_time, self.BUFFER_TIMES["travel_buffer"])
            
            # Check if we need to add meal time
            current_time = self._check_and_add_meal_time(current_time, time_slots, preferences)
            
            # Calculate activity duration
            activity_duration = self._calculate_activity_duration(activity)
            
            # Check opening hours
            if not self._is_within_opening_hours(current_time, activity):
                # Adjust time to next available slot
                current_time = self._get_next_available_time(current_time, activity)
            
            # Create activity time slot
            activity_slot = TimeSlot(
                start_time=current_time,
                end_time=self._add_minutes(current_time, activity_duration),
                duration_minutes=activity_duration,
                activity_name=activity.get("name", "Unknown"),
                activity_type=activity.get("type", "default"),
                location=activity.get("location", {}).get("name", "Unknown"),
                notes=activity.get("description", "")
            )
            
            time_slots.append(activity_slot)
            current_time = activity_slot.end_time
            
            # Add buffer between activities (except for last activity)
            if i < len(activities) - 1:
                current_time = self._add_minutes(current_time, self.BUFFER_TIMES["between_activities"])
        
        # Calculate totals
        total_activity_time = sum(slot.duration_minutes for slot in time_slots if slot.activity_type != "travel")
        total_travel_time = sum(slot.duration_minutes for slot in time_slots if slot.activity_type == "travel")
        total_rest_time = sum(slot.duration_minutes for slot in time_slots if slot.activity_type == "meal")
        
        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(time_slots, preferences)
        
        # Extract meal times
        meal_times = self._extract_meal_times(time_slots)
        
        return DaySchedule(
            date="",  # Will be set by caller
            time_slots=time_slots,
            total_activity_time=total_activity_time,
            total_travel_time=total_travel_time,
            total_rest_time=total_rest_time,
            meal_times=meal_times,
            efficiency_score=efficiency_score
        )
    
    def _calculate_activity_duration(self, activity: Dict[str, Any]) -> int:
        """Calculate realistic duration for an activity."""
        
        # Check if activity has explicit duration
        if "duration_hours" in activity:
            return int(activity["duration_hours"] * 60)
        
        # Determine activity type
        activity_type = activity.get("type", "default")
        activity_name = activity.get("name", "").lower()
        
        # Map activity name to type if not specified
        if not activity_type or activity_type == "default":
            activity_type = self._infer_activity_type(activity_name)
        
        # Get duration from mapping
        duration = self.ACTIVITY_DURATIONS.get(activity_type, self.ACTIVITY_DURATIONS["default"])
        
        # Adjust based on activity characteristics
        if "tour" in activity_name:
            duration += 30  # Tours often take longer
        elif "museum" in activity_name and "art" in activity_name:
            duration = max(duration, 120)  # Art museums need more time
        elif "park" in activity_name and "national" in activity_name:
            duration = max(duration, 180)  # National parks need more time
        
        return duration
    
    def _infer_activity_type(self, activity_name: str) -> str:
        """Infer activity type from name."""
        activity_name_lower = activity_name.lower()
        
        # Cultural activities
        if any(word in activity_name_lower for word in ["museum", "gallery", "exhibit"]):
            return "museum"
        elif any(word in activity_name_lower for word in ["theater", "theatre", "show", "concert"]):
            return "theater"
        elif any(word in activity_name_lower for word in ["church", "cathedral", "temple"]):
            return "church"
        elif any(word in activity_name_lower for word in ["monument", "statue", "memorial"]):
            return "monument"
        
        # Outdoor activities
        elif any(word in activity_name_lower for word in ["hike", "trail", "mountain"]):
            return "hiking"
        elif any(word in activity_name_lower for word in ["beach", "coast", "shore"]):
            return "beach"
        elif any(word in activity_name_lower for word in ["park", "garden", "botanical"]):
            return "park"
        elif any(word in activity_name_lower for word in ["zoo", "aquarium", "wildlife"]):
            return "zoo"
        
        # Entertainment
        elif any(word in activity_name_lower for word in ["amusement", "theme park", "roller coaster"]):
            return "amusement_park"
        elif any(word in activity_name_lower for word in ["casino", "gambling"]):
            return "casino"
        elif any(word in activity_name_lower for word in ["shopping", "mall", "market"]):
            return "shopping"
        
        # Food & Dining
        elif any(word in activity_name_lower for word in ["restaurant", "dining", "eatery"]):
            return "restaurant"
        elif any(word in activity_name_lower for word in ["cafe", "coffee", "bakery"]):
            return "cafe"
        elif any(word in activity_name_lower for word in ["tour", "tasting", "wine"]):
            return "food_tour"
        
        return "default"
    
    def _check_and_add_meal_time(self, current_time: time, time_slots: List[TimeSlot], 
                                preferences: Dict[str, Any]) -> time:
        """Check if it's time for a meal and add it to the schedule."""
        
        hour = current_time.hour
        
        # Check for lunch time
        if self.MEAL_TIMES["lunch"][0] <= hour <= self.MEAL_TIMES["lunch"][1]:
            if not any(slot.activity_type == "meal" and "lunch" in slot.activity_name.lower() 
                      for slot in time_slots):
                # Add lunch time
                lunch_slot = TimeSlot(
                    start_time=current_time,
                    end_time=self._add_minutes(current_time, 90),  # 1.5 hours for lunch
                    duration_minutes=90,
                    activity_name="Lunch",
                    activity_type="meal",
                    location="Local restaurant",
                    notes="Time for lunch - consider local cuisine"
                )
                time_slots.append(lunch_slot)
                current_time = lunch_slot.end_time
        
        # Check for dinner time
        elif self.MEAL_TIMES["dinner"][0] <= hour <= self.MEAL_TIMES["dinner"][1]:
            if not any(slot.activity_type == "meal" and "dinner" in slot.activity_name.lower() 
                      for slot in time_slots):
                # Add dinner time
                dinner_slot = TimeSlot(
                    start_time=current_time,
                    end_time=self._add_minutes(current_time, 120),  # 2 hours for dinner
                    duration_minutes=120,
                    activity_name="Dinner",
                    activity_type="meal",
                    location="Local restaurant",
                    notes="Time for dinner - consider local cuisine"
                )
                time_slots.append(dinner_slot)
                current_time = dinner_slot.end_time
        
        return current_time
    
    def _is_within_opening_hours(self, current_time: time, activity: Dict[str, Any]) -> bool:
        """Check if current time is within opening hours for the activity."""
        
        activity_type = activity.get("type", "default")
        opening_hours = self.OPENING_HOURS.get(activity_type, self.OPENING_HOURS["default"])
        
        hour = current_time.hour
        return opening_hours[0] <= hour <= opening_hours[1]
    
    def _get_next_available_time(self, current_time: time, activity: Dict[str, Any]) -> time:
        """Get the next available time when the activity opens."""
        
        activity_type = activity.get("type", "default")
        opening_hours = self.OPENING_HOURS.get(activity_type, self.OPENING_HOURS["default"])
        
        # If current time is before opening, wait until opening
        if current_time.hour < opening_hours[0]:
            return time(opening_hours[0], 0)
        
        # If current time is after closing, move to next day (will be handled by caller)
        return current_time
    
    def _add_minutes(self, current_time: time, minutes: int) -> time:
        """Add minutes to a time object, capping at 23:59."""
        total_minutes = current_time.hour * 60 + current_time.minute + minutes
        if total_minutes >= 24 * 60:
            return time(23, 59)
        hours = total_minutes // 60
        mins = total_minutes % 60
        return time(hours, mins)
    
    def _calculate_efficiency_score(self, time_slots: List[TimeSlot], 
                                  preferences: Dict[str, Any]) -> float:
        """Calculate schedule efficiency score (0-1)."""
        
        if not time_slots:
            return 0.0
        
        total_time = sum(slot.duration_minutes for slot in time_slots)
        activity_time = sum(slot.duration_minutes for slot in time_slots 
                           if slot.activity_type not in ["travel", "meal"])
        
        # Base efficiency: activity time vs total time
        base_efficiency = activity_time / total_time if total_time > 0 else 0
        
        # Penalize for too much travel time
        travel_time = sum(slot.duration_minutes for slot in time_slots 
                         if slot.activity_type == "travel")
        travel_penalty = min(travel_time / total_time, 0.3) if total_time > 0 else 0
        
        # Bonus for good meal timing
        meal_bonus = 0.1 if any(slot.activity_type == "meal" for slot in time_slots) else 0
        
        # Penalty for over-scheduling (more than 10 hours of activities)
        overschedule_penalty = 0.2 if activity_time > 600 else 0
        
        efficiency = base_efficiency - travel_penalty + meal_bonus - overschedule_penalty
        return max(0.0, min(1.0, efficiency))
    
    def _extract_meal_times(self, time_slots: List[TimeSlot]) -> Dict[str, time]:
        """Extract meal times from time slots."""
        meal_times = {}
        
        for slot in time_slots:
            if slot.activity_type == "meal":
                if "lunch" in slot.activity_name.lower():
                    meal_times["lunch"] = slot.start_time
                elif "dinner" in slot.activity_name.lower():
                    meal_times["dinner"] = slot.start_time
                elif "breakfast" in slot.activity_name.lower():
                    meal_times["breakfast"] = slot.start_time
        
        return meal_times
    
    def optimize_schedule(self, day_schedule: DaySchedule, 
                         preferences: Dict[str, Any]) -> DaySchedule:
        """Optimize the schedule for better flow and efficiency."""
        
        # For now, return the original schedule
        # In production, this would implement more sophisticated optimization
        return day_schedule
    
    def validate_schedule(self, day_schedule: DaySchedule) -> Dict[str, Any]:
        """Validate the schedule for issues."""
        
        issues = []
        warnings = []
        
        # Check for over-scheduling
        total_time = (day_schedule.total_activity_time + 
                     day_schedule.total_travel_time + 
                     day_schedule.total_rest_time)
        
        if total_time > 600:  # More than 10 hours
            issues.append("Schedule is over-packed (>10 hours)")
        elif total_time > 480:  # More than 8 hours
            warnings.append("Schedule is quite busy (>8 hours)")
        
        # Check for missing meals
        if not day_schedule.meal_times:
            warnings.append("No meal times scheduled")
        
        # Check for efficiency
        if day_schedule.efficiency_score < 0.5:
            issues.append("Low schedule efficiency")
        elif day_schedule.efficiency_score < 0.7:
            warnings.append("Schedule efficiency could be improved")
        
        # Check for travel time
        if day_schedule.total_travel_time > day_schedule.total_activity_time * 0.5:
            warnings.append("High travel time relative to activity time")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "efficiency_score": day_schedule.efficiency_score
        } 