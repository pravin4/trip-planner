#!/usr/bin/env python3
"""
Test Shelter Cove Route
Tests the exact scenario from the UI.
"""

from datetime import date, timedelta
from main import SmartTravelPlanner

def test_shelter_cove_route():
    """Test the exact scenario from the UI."""
    
    print("🧳 TESTING SHELTER COVE ROUTE")
    print("=" * 50)
    
    planner = SmartTravelPlanner()
    
    # Simulate the exact UI input
    destination = "Shelter Cove"
    starting_point = "San Jose, CA"
    start_date = (date.today() + timedelta(days=1)).isoformat()
    end_date = (date.today() + timedelta(days=5)).isoformat()
    budget = 2000.0
    
    print(f"Destination: {destination}")
    print(f"Starting Point: {starting_point}")
    print(f"Dates: {start_date} to {end_date}")
    print(f"Budget: ${budget}")
    
    # Test route detection
    print("\n🔍 Testing Route Detection:")
    destination_info = planner._parse_and_validate_destination(destination, starting_point)
    print(f"Type: {destination_info['type']}")
    
    if destination_info['type'] == 'route':
        print(f"Start: {destination_info['start']}")
        print(f"End: {destination_info['end']}")
        print(f"Route: {destination_info['route_description']}")
        print("✅ Route detected correctly!")
    else:
        print("❌ Route not detected!")
        return
    
    # Test full itinerary creation
    print("\n🚗 Creating Full Itinerary:")
    try:
        itinerary = planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            starting_point=starting_point
        )
        
        print("✅ Itinerary created successfully!")
        
        # Check for journey plan
        if "journey_plan" in itinerary:
            journey = itinerary["journey_plan"]
            print(f"\n🎯 Journey Plan:")
            print(f"   Travel Mode: {journey.get('travel_mode', 'unknown')}")
            print(f"   Distance: {journey.get('total_distance', 0):.1f} km")
            print(f"   Duration: {journey.get('total_duration', 0):.1f} hours")
            print(f"   Journey Cost: ${journey.get('total_cost', 0):.2f}")
            
            if journey.get("stops"):
                print(f"   Stops: {len(journey['stops'])} planned")
                for i, stop in enumerate(journey["stops"][:3]):
                    print(f"     {i+1}. {stop.get('stop_type', 'unknown')} at {stop.get('location', 'unknown')}")
        else:
            print("❌ No journey plan found in itinerary")
        
        # Check total cost
        print(f"\n💰 Total Cost: ${itinerary.get('total_cost', 0):.2f}")
        
        # Check day plans
        if "day_plans" in itinerary:
            print(f"\n📅 Day Plans: {len(itinerary['day_plans'])} days")
            for i, day in enumerate(itinerary["day_plans"][:2]):  # Show first 2 days
                print(f"   Day {i+1}: {len(day.get('activities', []))} activities")
        
    except Exception as e:
        print(f"❌ Error creating itinerary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shelter_cove_route() 