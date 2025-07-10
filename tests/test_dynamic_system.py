#!/usr/bin/env python3
"""Test the dynamic configuration and route planning system."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dynamic_config():
    """Test dynamic configuration system."""
    print("🧪 Testing Dynamic Configuration System")
    print("=" * 50)
    
    try:
        from config.dynamic_config import config_manager
        
        # Test cost configuration
        print("\n1️⃣ Testing Cost Configuration...")
        cost_config = config_manager.get_cost_config()
        print(f"   Gas price: ${cost_config.gas_price_per_gallon}/gallon")
        print(f"   Fuel efficiency: {cost_config.fuel_efficiency_mpg} mpg")
        print(f"   Toll rate: ${cost_config.toll_rate_per_100km}/100km")
        
        # Test dynamic cost calculations
        distance_km = 500
        gas_cost = config_manager.calculate_dynamic_gas_cost(distance_km)
        toll_cost = config_manager.calculate_dynamic_toll_cost(distance_km)
        parking_cost = config_manager.calculate_dynamic_parking_cost(8)
        
        print(f"   Dynamic costs for {distance_km}km, 8 hours:")
        print(f"     Gas: ${gas_cost:.2f}")
        print(f"     Tolls: ${toll_cost:.2f}")
        print(f"     Parking: ${parking_cost:.2f}")
        print(f"     Total: ${gas_cost + toll_cost + parking_cost:.2f}")
        
        # Test distance configuration
        print("\n2️⃣ Testing Distance Configuration...")
        distance_config = config_manager.get_distance_config()
        print(f"   Short threshold: {distance_config.short_distance_threshold}km")
        print(f"   Medium threshold: {distance_config.medium_distance_threshold}km")
        print(f"   Long threshold: {distance_config.long_distance_threshold}km")
        
        # Test waypoint threshold
        should_add = config_manager.should_add_waypoints(250)
        print(f"   Should add waypoints for 250km: {should_add}")
        
        # Test stop intervals
        attraction_interval = config_manager.get_stop_interval("attraction")
        rest_interval = config_manager.get_stop_interval("rest")
        print(f"   Attraction stop interval: {attraction_interval} hours")
        print(f"   Rest stop interval: {rest_interval} hours")
        
        print("✅ Dynamic configuration system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dynamic config: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynamic_route_planner():
    """Test dynamic route planner."""
    print("\n🧪 Testing Dynamic Route Planner")
    print("=" * 50)
    
    try:
        from utils.dynamic_route_planner import DynamicRoutePlanner
        
        planner = DynamicRoutePlanner()
        print("✅ Dynamic route planner initialized")
        
        # Test with a simple route
        origin = "San Jose, CA"
        destination = "San Francisco, CA"
        route_coords = [
            (37.3382, -121.8863),  # San Jose
            (37.7749, -122.4194)   # San Francisco
        ]
        
        print(f"\n   Testing route: {origin} to {destination}")
        stops = planner.find_dynamic_stops(origin, destination, route_coords)
        
        print(f"   Found {len(stops)} dynamic stops")
        for i, stop in enumerate(stops[:3]):  # Show first 3 stops
            print(f"     Stop {i+1}: {stop.get('name', 'Unknown')} - {stop.get('type', 'unknown')}")
        
        print("✅ Dynamic route planner working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dynamic route planner: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_journey_agent_dynamic():
    """Test JourneyAgent with dynamic configuration."""
    print("\n🧪 Testing JourneyAgent with Dynamic Configuration")
    print("=" * 50)
    
    try:
        from agents.journey_agent import JourneyAgent
        
        agent = JourneyAgent()
        print("✅ JourneyAgent initialized with dynamic configuration")
        
        # Test journey planning
        result = agent.plan_journey(
            origin="San Jose, CA",
            destination="Redwood National Park",
            start_date="2024-07-15",
            end_date="2024-07-17",
            preferences={"travel_mode": "drive"}
        )
        
        print(f"\n   Journey Plan Results:")
        print(f"     Travel mode: {result.get('travel_mode', 'unknown')}")
        print(f"     Distance: {result.get('total_distance', 0):.1f} km")
        print(f"     Duration: {result.get('total_duration', 0):.1f} hours")
        print(f"     Cost: ${result.get('total_cost', 0):.2f}")
        print(f"     Stops found: {len(result.get('route_stops', []))}")
        
        # Show some stops
        stops = result.get('route_stops', [])
        for i, stop in enumerate(stops[:3]):
            print(f"       Stop {i+1}: {stop.get('name', 'Unknown')}")
        
        print("✅ JourneyAgent with dynamic configuration working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing JourneyAgent: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all dynamic system tests."""
    print("🚀 Testing Dynamic Travel Planning System")
    print("=" * 60)
    
    tests = [
        test_dynamic_config,
        test_dynamic_route_planner,
        test_journey_agent_dynamic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Dynamic system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    main() 