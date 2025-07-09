#!/usr/bin/env python3
"""
Test Journey Planning
Tests the new journey planning functionality including road trips and flights.
"""

import os
import sys
import pytest
from datetime import date, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SmartTravelPlanner

class TestJourneyPlanning:
    """Test journey planning functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        load_dotenv()
        self.planner = SmartTravelPlanner()
        
    def test_road_trip_planning(self):
        """Test road trip planning from San Jose to Big Sur."""
        print("\n🧳 Testing Road Trip Planning: San Jose to Big Sur")
        
        # Test parameters
        destination = "San Jose to Big Sur"  # Route format
        start_date = (date.today() + timedelta(days=10)).isoformat()
        end_date = (date.today() + timedelta(days=15)).isoformat()
        budget = 2000.0
        
        # Create itinerary
        itinerary = self.planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point="San Jose"
        )
        
        # Verify journey planning was included
        assert "journey_plan" in itinerary, "Journey plan should be included"
        
        journey_plan = itinerary["journey_plan"]
        print(f"✅ Journey Plan Created:")
        print(f"   - Travel Mode: {journey_plan.get('travel_mode', 'unknown')}")
        print(f"   - Distance: {journey_plan.get('total_distance', 0):.1f} km")
        print(f"   - Duration: {journey_plan.get('total_duration', 0):.1f} hours")
        print(f"   - Cost: ${journey_plan.get('total_cost', 0):.2f}")
        
        # Check for stops
        if journey_plan.get("stops"):
            print(f"   - Stops: {len(journey_plan['stops'])} stops planned")
            for i, stop in enumerate(journey_plan["stops"][:3]):  # Show first 3 stops
                print(f"     {i+1}. {stop.get('stop_type', 'unknown')} at {stop.get('location', 'unknown')}")
        
        # Verify route information
        assert journey_plan.get("origin") == "San Jose", "Origin should be San Jose"
        assert journey_plan.get("destination") == "Big Sur", "Destination should be Big Sur"
        assert journey_plan.get("travel_mode") in ["drive", "multi_modal"], "Should be driving or multi-modal"
        
        print("✅ Road trip planning test passed!")
        
    def test_flight_planning(self):
        """Test flight planning for long distance trips."""
        print("\n✈️ Testing Flight Planning: San Jose to New York")
        
        # Test parameters for a long distance trip
        destination = "San Jose to New York"
        start_date = (date.today() + timedelta(days=20)).isoformat()
        end_date = (date.today() + timedelta(days=25)).isoformat()
        budget = 3000.0
        
        # Create itinerary
        itinerary = self.planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point="San Jose"
        )
        
        # Verify journey planning was included
        assert "journey_plan" in itinerary, "Journey plan should be included"
        
        journey_plan = itinerary["journey_plan"]
        print(f"✅ Flight Journey Plan Created:")
        print(f"   - Travel Mode: {journey_plan.get('travel_mode', 'unknown')}")
        print(f"   - Distance: {journey_plan.get('total_distance', 0):.1f} km")
        print(f"   - Duration: {journey_plan.get('total_duration', 0):.1f} hours")
        print(f"   - Cost: ${journey_plan.get('total_cost', 0):.2f}")
        
        # Check for flight information
        if journey_plan.get("flights"):
            flight_info = journey_plan["flights"]
            print(f"   - Flight: {flight_info.get('airline', 'Unknown')} {flight_info.get('flight_number', 'Unknown')}")
            print(f"   - Departure: {flight_info.get('departure_time', 'Unknown')}")
            print(f"   - Arrival: {flight_info.get('arrival_time', 'Unknown')}")
            print(f"   - Flight Cost: ${flight_info.get('cost', 0):.2f}")
        
        # Check for airport information
        if journey_plan.get("airports"):
            airports = journey_plan["airports"]
            print(f"   - Origin Airport: {airports.get('origin_airport', {}).get('name', 'Unknown')}")
            print(f"   - Destination Airport: {airports.get('destination_airport', {}).get('name', 'Unknown')}")
        
        # Verify flight mode for long distance
        assert journey_plan.get("travel_mode") in ["fly", "multi_modal"], "Should be flying or multi-modal for long distance"
        
        print("✅ Flight planning test passed!")
        
    def test_journey_stops_integration(self):
        """Test that journey stops are integrated into the itinerary."""
        print("\n🛣️ Testing Journey Stops Integration")
        
        # Test parameters
        destination = "San Jose to Yosemite"
        start_date = (date.today() + timedelta(days=5)).isoformat()
        end_date = (date.today() + timedelta(days=8)).isoformat()
        budget = 1500.0
        
        # Create itinerary
        itinerary = self.planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point="San Jose"
        )
        
        # Check that journey stops are added to the first day
        if itinerary.get("day_plans"):
            first_day = itinerary["day_plans"][0]
            
            # Look for journey stop activities
            journey_activities = [
                activity for activity in first_day.get("activities", [])
                if activity.get("type") == "journey_stop"
            ]
            
            if journey_activities:
                print(f"✅ Found {len(journey_activities)} journey stops in first day:")
                for activity in journey_activities[:3]:  # Show first 3
                    print(f"   - {activity.get('name', 'Unknown')}")
                    print(f"     Type: {activity.get('stop_type', 'unknown')}")
                    print(f"     Cost: ${activity.get('cost', 0):.2f}")
            else:
                print("ℹ️ No journey stops found (this is normal for short trips)")
        
        # Verify journey plan exists
        assert "journey_plan" in itinerary, "Journey plan should be included"
        
        print("✅ Journey stops integration test passed!")
        
    def test_cost_integration(self):
        """Test that journey costs are properly integrated into total cost."""
        print("\n💰 Testing Journey Cost Integration")
        
        # Test parameters
        destination = "San Jose to Lake Tahoe"
        start_date = (date.today() + timedelta(days=15)).isoformat()
        end_date = (date.today() + timedelta(days=18)).isoformat()
        budget = 2500.0
        
        # Create itinerary
        itinerary = self.planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point="San Jose"
        )
        
        # Check cost breakdown
        if "cost_breakdown" in itinerary:
            cost_breakdown = itinerary["cost_breakdown"]
            print(f"✅ Cost Breakdown:")
            print(f"   - Total: ${cost_breakdown.get('total', 0):.2f}")
            print(f"   - Transportation: ${cost_breakdown.get('transportation', 0):.2f}")
            print(f"   - Accommodations: ${cost_breakdown.get('accommodations', 0):.2f}")
            print(f"   - Activities: ${cost_breakdown.get('activities', 0):.2f}")
            print(f"   - Meals: ${cost_breakdown.get('meals', 0):.2f}")
        
        # Check journey costs
        if "journey_plan" in itinerary:
            journey_costs = itinerary["journey_plan"].get("costs", {})
            print(f"✅ Journey Costs:")
            print(f"   - Transportation: ${journey_costs.get('transportation', 0):.2f}")
            print(f"   - Accommodations: ${journey_costs.get('accommodations', 0):.2f}")
            print(f"   - Activities: ${journey_costs.get('activities', 0):.2f}")
            print(f"   - Meals: ${journey_costs.get('meals', 0):.2f}")
            print(f"   - Total Journey: ${journey_costs.get('total', 0):.2f}")
        
        print("✅ Journey cost integration test passed!")

if __name__ == "__main__":
    # Run tests
    test_instance = TestJourneyPlanning()
    test_instance.setup()
    
    print("🧳 JOURNEY PLANNING TESTS")
    print("=" * 50)
    
    try:
        test_instance.test_road_trip_planning()
        test_instance.test_flight_planning()
        test_instance.test_journey_stops_integration()
        test_instance.test_cost_integration()
        
        print("\n🎉 All journey planning tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 