#!/usr/bin/env python3
"""Debug script to test stops for San Jose to Redwood National Park route."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.journey_agent import JourneyAgent

def test_stops_debug():
    """Test stops generation for the route."""
    print("🧪 Testing Stops Generation for San Jose to Redwood National Park")
    print("=" * 70)
    
    try:
        # Initialize JourneyAgent
        agent = JourneyAgent()
        
        # Test predefined stops
        print("\n1️⃣ Testing Predefined Stops...")
        predefined_stops = agent._get_predefined_stops("San Jose, CA", "Redwood National Park")
        print(f"   Found {len(predefined_stops)} predefined stops")
        for stop in predefined_stops:
            print(f"   - {stop.get('name', 'Unknown')}: {stop.get('description', 'No description')}")
        
        # Test journey planning
        print("\n2️⃣ Testing Journey Planning...")
        journey_result = agent.plan_journey(
            origin="San Jose, CA",
            destination="Redwood National Park",
            start_date="2025-07-10",
            end_date="2025-07-16",
            preferences={"travel_mode": "drive"}
        )
        
        print(f"   Travel mode: {journey_result.get('travel_mode')}")
        print(f"   Distance: {journey_result.get('total_distance', 0):.1f} km")
        print(f"   Duration: {journey_result.get('total_duration', 0):.1f} hours")
        
        # Check journey plan
        journey_plan = journey_result.get('journey_plan', {})
        print(f"   Journey plan keys: {list(journey_plan.keys())}")
        
        # Check waypoints
        waypoints = journey_plan.get('waypoints', [])
        print(f"   Waypoints: {len(waypoints)} found")
        for i, waypoint in enumerate(waypoints):
            print(f"     {i+1}. {waypoint.get('name', 'Unknown')} at {waypoint.get('location', {})}")
        
        # Check route stops
        route_stops = journey_result.get('route_stops', [])
        print(f"   Route stops: {len(route_stops)} found")
        for i, stop in enumerate(route_stops):
            print(f"     {i+1}. {stop.get('name', 'Unknown')} - {stop.get('stop_type', 'unknown')}")
            attractions = stop.get('attractions', [])
            if attractions:
                print(f"        Attractions: {[a.get('name', 'Unknown') for a in attractions]}")
        
        # Test nearby attractions
        print("\n3️⃣ Testing Nearby Attractions...")
        test_location = {"lat": 40.0304, "lng": -124.0731}  # Near Redwood NP
        nearby = agent._find_nearby_attractions(test_location)
        print(f"   Found {len(nearby)} nearby attractions")
        for attraction in nearby[:3]:
            print(f"   - {attraction.get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stops_debug()
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}: Stops debug test")
    sys.exit(0 if success else 1) 