#!/usr/bin/env python3
"""
Test script for transportation planning system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.transportation_planner import TransportationPlanner
from datetime import datetime, timedelta

def test_transportation_planner():
    """Test the transportation planning system"""
    
    print("Testing Transportation Planning System")
    print("=" * 50)
    
    planner = TransportationPlanner()
    
    # Test 1: Single city (no inter-city travel)
    print("\n1. Testing single city trip:")
    destinations = ["San Francisco"]
    start_date = "2024-07-04"
    end_date = "2024-07-07"
    preferences = {"budget_level": "moderate", "group_size": 2}
    
    travel_days = planner.plan_inter_city_travel(destinations, start_date, end_date, preferences)
    print(f"   Travel days: {len(travel_days)} (expected: 0)")
    
    # Test 2: Multi-city trip
    print("\n2. Testing multi-city trip:")
    destinations = ["San Francisco", "Los Angeles", "Las Vegas"]
    travel_days = planner.plan_inter_city_travel(destinations, start_date, end_date, preferences)
    
    print(f"   Travel days: {len(travel_days)} (expected: 2)")
    for i, travel_day in enumerate(travel_days, 1):
        print(f"   Travel Day {i}: {travel_day.date}")
        print(f"     Total time: {travel_day.total_travel_time} minutes")
        print(f"     Total cost: ${travel_day.total_cost:.2f}")
        print(f"     Travel only: {travel_day.is_travel_only}")
        for leg in travel_day.legs:
            print(f"     {leg.from_location} → {leg.to_location} by {leg.mode}")
            print(f"       Distance: {leg.distance_km:.1f}km, Duration: {leg.duration_minutes}min")
            print(f"       Cost: ${leg.cost_per_person:.2f} per person")
    
    # Test 3: Distance calculations
    print("\n3. Testing distance calculations:")
    from_coords = (37.7749, -122.4194)  # San Francisco
    to_coords = (34.0522, -118.2437)    # Los Angeles
    
    distance = planner._calculate_distance(from_coords, to_coords)
    print(f"   SF to LA: {distance:.1f}km")
    
    # Test 4: Transportation mode selection
    print("\n4. Testing transportation mode selection:")
    distances = [2, 15, 80, 300, 800]
    for distance in distances:
        mode = planner._select_transportation_mode(distance, preferences)
        print(f"   {distance}km → {mode}")
    
    # Test 5: Local transportation planning
    print("\n5. Testing local transportation:")
    activities = [
        {
            "name": "Golden Gate Bridge",
            "location": {"latitude": 37.8199, "longitude": -122.4783}
        },
        {
            "name": "Fisherman's Wharf",
            "location": {"latitude": 37.8080, "longitude": -122.4177}
        },
        {
            "name": "Alcatraz",
            "location": {"latitude": 37.8270, "longitude": -122.4230}
        }
    ]
    
    local_transport = planner.plan_local_transportation(activities, "San Francisco")
    print(f"   Local transport legs: {len(local_transport)}")
    for leg in local_transport:
        print(f"     {leg.from_location} → {leg.to_location}")
        print(f"       Mode: {leg.mode}, Duration: {leg.duration_minutes}min")
    
    print("\nTransportation planning test completed!")

if __name__ == "__main__":
    test_transportation_planner() 