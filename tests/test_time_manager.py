#!/usr/bin/env python3
"""
Test script for time management module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.time_manager import TimeManager
from datetime import time

def test_time_manager():
    print("Testing Time Management Module")
    print("=" * 50)
    
    tm = TimeManager()
    
    # Example activities for a day
    activities = [
        {"name": "Golden Gate Park", "type": "park", "location": {"name": "Golden Gate Park"}},
        {"name": "de Young Museum", "type": "museum", "location": {"name": "de Young Museum"}},
        {"name": "Lunch at Tartine", "type": "restaurant", "location": {"name": "Tartine"}},
        {"name": "Alcatraz Tour", "type": "tour", "location": {"name": "Alcatraz Island"}},
        {"name": "Dinner at Fisherman's Wharf", "type": "restaurant", "location": {"name": "Fisherman's Wharf"}},
    ]
    
    # Example travel legs (between activities)
    travel_legs = [
        {"from": "Golden Gate Park", "to": "de Young Museum", "duration_minutes": 15, "notes": "Short walk"},
        {"from": "de Young Museum", "to": "Tartine", "duration_minutes": 20, "notes": "Taxi ride"},
        {"from": "Tartine", "to": "Alcatraz Island", "duration_minutes": 30, "notes": "Ferry"},
        {"from": "Alcatraz Island", "to": "Fisherman's Wharf", "duration_minutes": 25, "notes": "Boat and walk"},
    ]
    
    preferences = {"dietary_restrictions": [], "budget_level": "moderate"}
    
    schedule = tm.create_realistic_schedule(activities, travel_legs, preferences)
    
    print(f"Total activity time: {schedule.total_activity_time} min")
    print(f"Total travel time: {schedule.total_travel_time} min")
    print(f"Total rest time: {schedule.total_rest_time} min")
    print(f"Efficiency score: {schedule.efficiency_score:.2f}")
    print(f"Meal times: {schedule.meal_times}")
    print("\nDay Schedule:")
    for slot in schedule.time_slots:
        print(f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}: {slot.activity_name} ({slot.activity_type}) @ {slot.location} [{slot.duration_minutes} min]")
        if slot.notes:
            print(f"   Notes: {slot.notes}")
    
    # Validate schedule
    validation = tm.validate_schedule(schedule)
    print("\nValidation:")
    print(f"Valid: {validation['valid']}")
    print(f"Issues: {validation['issues']}")
    print(f"Warnings: {validation['warnings']}")
    print(f"Efficiency Score: {validation['efficiency_score']:.2f}")
    
    print("\nTime management test completed!")

if __name__ == "__main__":
    test_time_manager() 