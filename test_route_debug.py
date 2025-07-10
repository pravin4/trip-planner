#!/usr/bin/env python3
"""
Debug script to test route planning functionality.
"""

import os
import sys
from datetime import date, timedelta
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_route_detection():
    """Test route detection logic."""
    route_indicators = [" to ", " → ", " -> ", " via ", " through "]
    
    test_cases = [
        "San Jose to Redwood National Park",
        "San Jose to Big Sur",
        "Redwood National Park",
        "San Francisco to Yosemite"
    ]
    
    for test_case in test_cases:
        is_route = any(indicator in test_case.lower() for indicator in route_indicators)
        print(f"'{test_case}' -> Is route: {is_route}")
        
        if is_route:
            # Parse route
            for indicator in route_indicators:
                if indicator in test_case.lower():
                    parts = test_case.split(indicator)
                    if len(parts) == 2:
                        origin = parts[0].strip()
                        destination = parts[1].strip()
                        print(f"  Origin: {origin}")
                        print(f"  Destination: {destination}")
                        break

def test_route_planning_logic():
    """Test the route planning logic without full initialization."""
    try:
        from agents.planning_agent import PlanningAgent
        
        # Test route detection
        pa = PlanningAgent()
        
        test_destination = "San Jose to Redwood National Park"
        is_route = pa._is_route_destination(test_destination)
        print(f"\nRoute detection test:")
        print(f"Destination: '{test_destination}'")
        print(f"Is route: {is_route}")
        
        if is_route:
            route_info = pa._parse_route_destination(test_destination)
            print(f"Route info: {route_info}")
            
            # Test the route day plans creation
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=6)
            duration = 7
            
            print(f"\nTesting route day plans creation...")
            print(f"Start date: {start_date}")
            print(f"End date: {end_date}")
            print(f"Duration: {duration}")
            
            # Mock research data
            research_data = {
                "attractions": [],
                "restaurants": [],
                "accommodations": []
            }
            
            # Mock preferences
            preferences = {
                "budget": 2000,
                "accommodation_types": ["hotel"],
                "activity_types": ["cultural"]
            }
            
            try:
                day_plans = pa._create_route_day_plans(
                    route_info["origin"], 
                    route_info["destination"], 
                    start_date, end_date, 
                    research_data, preferences, duration
                )
                print(f"Successfully created {len(day_plans)} day plans")
                
                for i, day in enumerate(day_plans):
                    print(f"\nDay {i+1}:")
                    print(f"  Type: {day.get('type', 'unknown')}")
                    print(f"  Activities: {len(day.get('activities', []))}")
                    print(f"  Accommodations: {len(day.get('accommodations', []))}")
                    print(f"  Transportation: {len(day.get('transportation', []))}")
                    
            except Exception as e:
                print(f"Error creating route day plans: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Route Detection Test ===")
    test_route_detection()
    
    print("\n=== Route Planning Logic Test ===")
    test_route_planning_logic() 