#!/usr/bin/env python3
"""
Journey Planning Demo
Demonstrates the new journey planning functionality.
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv
from main import SmartTravelPlanner

def demo_journey_planning():
    """Demo the journey planning functionality."""
    
    print("🧳 JOURNEY PLANNING DEMO")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize planner
        planner = SmartTravelPlanner()
        print("✅ Planner initialized with JourneyAgent")
        
        # Test 1: Road Trip (San Jose to Big Sur)
        print("\n🚗 TEST 1: Road Trip - San Jose to Big Sur")
        print("-" * 40)
        
        road_trip = planner.create_itinerary(
            destination="San Jose to Big Sur",
            start_date=(date.today() + timedelta(days=10)).isoformat(),
            end_date=(date.today() + timedelta(days=13)).isoformat(),
            budget=1500.0,
            starting_point="San Jose"
        )
        
        if "journey_plan" in road_trip:
            journey = road_trip["journey_plan"]
            print(f"✅ Journey Plan Created:")
            print(f"   - Travel Mode: {journey.get('travel_mode', 'unknown')}")
            print(f"   - Distance: {journey.get('total_distance', 0):.1f} km")
            print(f"   - Duration: {journey.get('total_duration', 0):.1f} hours")
            print(f"   - Journey Cost: ${journey.get('total_cost', 0):.2f}")
            
            if journey.get("stops"):
                print(f"   - Stops: {len(journey['stops'])} planned")
                for i, stop in enumerate(journey["stops"][:2]):
                    print(f"     {i+1}. {stop.get('stop_type', 'unknown')} at {stop.get('location', 'unknown')}")
        
        # Test 2: Flight Planning (San Jose to New York)
        print("\n✈️ TEST 2: Flight Planning - San Jose to New York")
        print("-" * 40)
        
        flight_trip = planner.create_itinerary(
            destination="San Jose to New York",
            start_date=(date.today() + timedelta(days=20)).isoformat(),
            end_date=(date.today() + timedelta(days=25)).isoformat(),
            budget=3000.0,
            starting_point="San Jose"
        )
        
        if "journey_plan" in flight_trip:
            journey = flight_trip["journey_plan"]
            print(f"✅ Flight Journey Plan Created:")
            print(f"   - Travel Mode: {journey.get('travel_mode', 'unknown')}")
            print(f"   - Distance: {journey.get('total_distance', 0):.1f} km")
            print(f"   - Journey Cost: ${journey.get('total_cost', 0):.2f}")
            
            if journey.get("flights"):
                flight = journey["flights"]
                print(f"   - Flight: {flight.get('airline', 'Unknown')} {flight.get('flight_number', 'Unknown')}")
                print(f"   - Cost: ${flight.get('cost', 0):.2f}")
            
            if journey.get("airports"):
                airports = journey["airports"]
                print(f"   - Origin Airport: {airports.get('origin_airport', {}).get('name', 'Unknown')}")
                print(f"   - Destination Airport: {airports.get('destination_airport', {}).get('name', 'Unknown')}")
        
        # Test 3: Cost Integration
        print("\n💰 TEST 3: Cost Integration")
        print("-" * 40)
        
        if "cost_breakdown" in road_trip:
            costs = road_trip["cost_breakdown"]
            print(f"✅ Total Trip Cost: ${costs.get('total', 0):.2f}")
            print(f"   - Transportation: ${costs.get('transportation', 0):.2f}")
            print(f"   - Accommodations: ${costs.get('accommodations', 0):.2f}")
            print(f"   - Activities: ${costs.get('activities', 0):.2f}")
            print(f"   - Meals: ${costs.get('meals', 0):.2f}")
        
        print("\n🎉 Journey Planning Demo Complete!")
        print("\nKey Features Added:")
        print("✅ Road trip planning with stops")
        print("✅ Flight planning with airports")
        print("✅ Cost integration")
        print("✅ Route optimization")
        print("✅ Multi-modal transportation")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_journey_planning() 