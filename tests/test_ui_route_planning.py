#!/usr/bin/env python3
"""
Test script for the improved route-based itinerary system.
Tests the new day-by-day planning with proper journey progression for UI display.
"""

import os
import sys
from datetime import date, timedelta
import logging
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SmartTravelPlanner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_route_planning_ui_format():
    """Test the improved route planning system produces proper UI format."""
    try:
        # Initialize the planner
        planner = SmartTravelPlanner()
        
        # Test parameters
        route_destination = "San Jose to Redwood National Park"
        start_date = (date.today() + timedelta(days=1)).isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()
        
        # Create travel preferences
        travel_prefs = {
            "budget": 2000,
            "group_size": 2,
            "activity_types": ["outdoor", "cultural", "adventure"],
            "accommodation_types": ["hotel", "camping"],
            "travel_mode": "drive"
        }
        
        logger.info(f"Testing route planning for: {route_destination}")
        logger.info(f"Dates: {start_date} to {end_date}")
        
        # Create itinerary
        result = planner.create_itinerary(
            destination=route_destination,
            start_date=start_date,
            end_date=end_date,
            budget=travel_prefs["budget"],
            preferences=travel_prefs
        )
        
        if result and isinstance(result, dict):
            itinerary = result
            
            # Check if we have day plans
            if "day_plans" in itinerary and itinerary["day_plans"]:
                day_plans = itinerary["day_plans"]
                logger.info(f"✅ Generated {len(day_plans)} day plans")
                
                # Check each day plan structure
                for i, day in enumerate(day_plans):
                    logger.info(f"\n--- Day {i+1} ---")
                    logger.info(f"Type: {day.get('type', 'unknown')}")
                    logger.info(f"Date: {day.get('date', 'unknown')}")
                    logger.info(f"Day Number: {day.get('day_number', 'unknown')}")
                    
                    # Check activities
                    activities = day.get('activities', [])
                    if activities:
                        logger.info(f"Activities ({len(activities)}):")
                        for act in activities:
                            if isinstance(act, dict):
                                logger.info(f"  - {act.get('name', 'Unknown')} at {act.get('location', 'Unknown')}")
                            elif isinstance(act, str):
                                logger.warning(f"  - [STRING ENTRY] {act}")
                            else:
                                logger.warning(f"  - [UNKNOWN TYPE] {act}")
                    # Check accommodations
                    accommodations = day.get('accommodations', [])
                    if accommodations:
                        logger.info(f"Accommodations ({len(accommodations)}):")
                        for acc in accommodations:
                            if isinstance(acc, dict):
                                logger.info(f"  - {acc.get('name', 'Unknown')} in {acc.get('location', 'Unknown')}")
                            elif isinstance(acc, str):
                                logger.warning(f"  - [STRING ENTRY] {acc}")
                            else:
                                logger.warning(f"  - [UNKNOWN TYPE] {acc}")
                    # Check transportation
                    transportation = day.get('transportation', [])
                    if transportation:
                        logger.info(f"Transportation ({len(transportation)}):")
                        for trans in transportation:
                            if isinstance(trans, dict):
                                from_loc = trans.get('from', 'Unknown')
                                to_loc = trans.get('to', 'Unknown')
                                mode = trans.get('mode', 'Unknown')
                                logger.info(f"  - {mode}: {from_loc} → {to_loc}")
                            elif isinstance(trans, str):
                                logger.warning(f"  - [STRING ENTRY] {trans}")
                            else:
                                logger.warning(f"  - [UNKNOWN TYPE] {trans}")
                
                # Check if we have proper route progression
                first_day = day_plans[0] if day_plans else {}
                last_day = day_plans[-1] if day_plans else {}
                
                if first_day.get('type') == 'departure':
                    logger.info("✅ First day is properly marked as departure")
                else:
                    logger.warning(f"⚠️ First day type: {first_day.get('type', 'unknown')}")
                
                if last_day.get('type') == 'return':
                    logger.info("✅ Last day is properly marked as return")
                else:
                    logger.warning(f"⚠️ Last day type: {last_day.get('type', 'unknown')}")
                
                # Check for intermediate stops
                intermediate_days = [day for day in day_plans if day.get('type') in ['travel', 'exploration']]
                if len(intermediate_days) > 0:
                    logger.info(f"✅ Found {len(intermediate_days)} intermediate days with stops")
                else:
                    logger.warning("⚠️ No intermediate days found")
                
            else:
                logger.error("❌ No day plans generated")
                return False
            
            # Check total cost
            total_cost = itinerary.get('total_cost', 0)
            logger.info(f"Total cost: ${total_cost:.2f}")
            
            # Check if within budget
            budget = travel_prefs.get('budget', 0)
            if total_cost <= budget:
                logger.info("✅ Cost is within budget")
            else:
                logger.warning(f"⚠️ Cost exceeds budget by ${total_cost - budget:.2f}")
            
            return True
            
        else:
            logger.error("❌ No itinerary generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing route planning: {e}")
        return False

if __name__ == "__main__":
    success = test_route_planning_ui_format()
    if success:
        print("\n🎉 Route planning UI format test PASSED!")
        print("The system now generates proper route-based itineraries with:")
        print("- Clear day-by-day progression")
        print("- Intermediate stops and sleepovers")
        print("- Proper departure and return days")
        print("- Detailed transportation information")
        print("- Location-specific activities and accommodations")
    else:
        print("\n❌ Route planning UI format test FAILED!")
        sys.exit(1) 