#!/usr/bin/env python3
"""
Test script for geographic logic and clustering
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geographic_utils import GeographicUtils, LocationCluster

def test_geographic_clustering():
    """Test the geographic clustering functionality"""
    
    print("🧪 Testing Geographic Clustering Logic...")
    
    # Sample activities with location data
    activities = [
        {
            "name": "Golden Gate Bridge",
            "type": "outdoor",
            "duration_hours": 2,
            "cost": 0,
            "location": {
                "latitude": 37.8199,
                "longitude": -122.4783,
                "name": "Golden Gate Bridge",
                "address": "Golden Gate Bridge, San Francisco, CA"
            }
        },
        {
            "name": "Fisherman's Wharf",
            "type": "cultural",
            "duration_hours": 3,
            "cost": 20,
            "location": {
                "latitude": 37.8080,
                "longitude": -122.4177,
                "name": "Fisherman's Wharf",
                "address": "Fisherman's Wharf, San Francisco, CA"
            }
        },
        {
            "name": "Alcatraz Island",
            "type": "cultural",
            "duration_hours": 4,
            "cost": 45,
            "location": {
                "latitude": 37.8270,
                "longitude": -122.4230,
                "name": "Alcatraz Island",
                "address": "Alcatraz Island, San Francisco, CA"
            }
        },
        {
            "name": "Golden Gate Park",
            "type": "outdoor",
            "duration_hours": 3,
            "cost": 0,
            "location": {
                "latitude": 37.7694,
                "longitude": -122.4862,
                "name": "Golden Gate Park",
                "address": "Golden Gate Park, San Francisco, CA"
            }
        },
        {
            "name": "Chinatown",
            "type": "cultural",
            "duration_hours": 2,
            "cost": 10,
            "location": {
                "latitude": 37.7941,
                "longitude": -122.4079,
                "name": "Chinatown",
                "address": "Chinatown, San Francisco, CA"
            }
        }
    ]
    
    # Sample restaurants
    restaurants = [
        {
            "name": "Fisherman's Wharf Restaurant",
            "cuisine": "Seafood",
            "price_level": 3,
            "rating": 4.2,
            "cost_per_person": 45.0,
            "location": {
                "latitude": 37.8080,
                "longitude": -122.4177,
                "name": "Fisherman's Wharf Restaurant",
                "address": "Fisherman's Wharf, San Francisco, CA"
            }
        },
        {
            "name": "Chinatown Dim Sum",
            "cuisine": "Chinese",
            "price_level": 2,
            "rating": 4.0,
            "cost_per_person": 25.0,
            "location": {
                "latitude": 37.7941,
                "longitude": -122.4079,
                "name": "Chinatown Dim Sum",
                "address": "Chinatown, San Francisco, CA"
            }
        }
    ]
    
    print(f"📍 Testing with {len(activities)} activities and {len(restaurants)} restaurants")
    
    # Test distance calculation
    print("\n📏 Testing distance calculation...")
    distance = GeographicUtils.calculate_distance(
        37.8199, -122.4783,  # Golden Gate Bridge
        37.8080, -122.4177   # Fisherman's Wharf
    )
    print(f"Distance between Golden Gate Bridge and Fisherman's Wharf: {distance:.2f} km")
    
    # Test activity clustering
    print("\n🗺️ Testing activity clustering...")
    clusters = GeographicUtils.cluster_activities_by_location(activities)
    print(f"Created {len(clusters)} geographic clusters:")
    
    for i, cluster in enumerate(clusters):
        print(f"  Cluster {i+1}: {cluster.name}")
        print(f"    Center: ({cluster.center_lat:.4f}, {cluster.center_lng:.4f})")
        print(f"    Activities: {len(cluster.activities)}")
        for activity in cluster.activities:
            print(f"      - {activity['name']}")
    
    # Test restaurant assignment to clusters
    print("\n🍽️ Testing restaurant assignment to clusters...")
    clusters_with_restaurants = GeographicUtils.cluster_restaurants_by_location(restaurants, clusters)
    
    for i, cluster in enumerate(clusters_with_restaurants):
        print(f"  Cluster {i+1}: {len(cluster.restaurants)} restaurants")
        for restaurant in cluster.restaurants:
            print(f"      - {restaurant['name']} ({restaurant['cuisine']})")
    
    # Test day plan creation
    print("\n📅 Testing day plan creation...")
    day_plans = GeographicUtils.create_geographic_day_plans(clusters_with_restaurants, 3)
    
    for i, day_plan in enumerate(day_plans):
        print(f"  Day {day_plan['day_number']}: {day_plan['cluster_name']}")
        print(f"    Activities: {len(day_plan['activities'])}")
        print(f"    Restaurants: {len(day_plan['restaurants'])}")
        print(f"    Total duration: {day_plan['total_duration_hours']:.1f} hours")
        print(f"    Travel time: {day_plan['travel_time_minutes']} minutes")
    
    # Test validation
    print("\n✅ Testing itinerary validation...")
    validation = GeographicUtils.validate_itinerary_geography(day_plans)
    print(f"  Is valid: {validation['is_valid']}")
    print(f"  Issues found: {len(validation['issues'])}")
    print(f"  Suggestions: {len(validation['suggestions'])}")
    
    if validation['issues']:
        print("  Issues:")
        for issue in validation['issues']:
            print(f"    - {issue}")
    
    if validation['suggestions']:
        print("  Suggestions:")
        for suggestion in validation['suggestions']:
            print(f"    - {suggestion}")
    
    print("\n🎉 Geographic logic test completed!")

if __name__ == "__main__":
    test_geographic_clustering() 