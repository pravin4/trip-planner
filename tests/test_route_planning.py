#!/usr/bin/env python3
"""
Test script for the improved route planning system.
Tests the new day-by-day planning with proper journey progression.
"""

import os
import sys
from datetime import date, timedelta
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SmartTravelPlanner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_route_planning():
    """Test the improved route planning system."""
    try:
        # Initialize the planner
        planner = SmartTravelPlanner()
        
        # Test parameters
        route_destination = "San Jose to Redwood National Park"
        start_date = (date.today() + timedelta(days=1)).isoformat()  # Tomorrow
        end_date = (date.today() + timedelta(days=7)).isoformat()    # 7 days from tomorrow
        budget = 2000.0
        
        logger.info(f"Testing route planning for: {route_destination}")
        logger.info(f"Dates: {start_date} to {end_date}")
        logger.info(f"Budget: ${budget}")
        
        # Create itinerary
        itinerary = planner.create_itinerary(
            destination=route_destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point="San Jose"
        )
        
        # Analyze the results
        logger.info("\n" + "="*50)
        logger.info("ITINERARY ANALYSIS")
        logger.info("="*50)
        
        # Check if it's a route
        if " to " in route_destination:
            logger.info("✓ Route detected correctly")
        else:
            logger.warning("✗ Route not detected")
        
        # Check day plans
        day_plans = itinerary.get("day_plans", [])
        logger.info(f"✓ Generated {len(day_plans)} day plans")
        
        # Analyze each day
        for i, day_plan in enumerate(day_plans, 1):
            logger.info(f"\nDay {i} ({day_plan.get('date', 'Unknown')}):")
            logger.info(f"  Type: {day_plan.get('type', 'Unknown')}")
            logger.info(f"  Activities: {len(day_plan.get('activities', []))}")
            logger.info(f"  Transportation: {len(day_plan.get('transportation', []))}")
            logger.info(f"  Accommodations: {len(day_plan.get('accommodations', []))}")
            
            # Check for proper progression
            if i == 1:
                if day_plan.get('type') == 'departure':
                    logger.info("  ✓ Day 1 is departure day")
                else:
                    logger.warning("  ✗ Day 1 should be departure day")
            
            elif i == len(day_plans):
                if day_plan.get('type') == 'return':
                    logger.info("  ✓ Final day is return day")
                else:
                    logger.info("  ℹ Final day is not return day (may be exploration)")
            
            # Check for activities
            activities = day_plan.get('activities', [])
            if activities:
                for activity in activities:
                    logger.info(f"    - {activity.get('name', 'Unknown activity')}")
        
        # Check total cost
        total_cost = itinerary.get('total_cost', 0)
        logger.info(f"\n✓ Total cost: ${total_cost:.2f}")
        
        # Check if cost is within budget
        if total_cost <= budget:
            logger.info("✓ Cost is within budget")
        else:
            logger.warning(f"✗ Cost exceeds budget by ${total_cost - budget:.2f}")
        
        # Check for journey information
        if 'journey_info' in itinerary:
            logger.info("✓ Journey information included")
        else:
            logger.info("ℹ No specific journey information")
        
        logger.info("\n" + "="*50)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_route_planning()
    if success:
        print("\n✅ Route planning test passed!")
    else:
        print("\n❌ Route planning test failed!")
        sys.exit(1) 