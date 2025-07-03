#!/usr/bin/env python3
"""
Test script for real hotel availability checking using Amadeus API.
This demonstrates how to check actual availability and pricing for specific dates.
"""

import os
import sys
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_integrations.amadeus_api import AmadeusAPI
from main import SmartTravelPlanner

def test_amadeus_api():
    """Test Amadeus API directly."""
    print("🔍 Testing Amadeus API for Real Hotel Availability")
    print("=" * 60)
    
    api = AmadeusAPI()
    
    # Check if API is configured
    if not api.client_id or not api.client_secret:
        print("❌ Amadeus API not configured!")
        print("Please set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in your .env file")
        print("Get free API keys at: https://developers.amadeus.com/")
        return
    
    # Test availability for different cities
    test_cities = ["New York", "London", "Paris", "Tokyo"]
    
    for city in test_cities:
        print(f"\n🏨 Testing {city}...")
        city_code = api.get_city_code(city)
        if city_code:
            print(f"✅ Found city code: {city_code}")
            
            # Test hotel search
            check_in = date(2024, 9, 15)
            check_out = date(2024, 9, 18)
            
            result = api.search_hotels(city_code, check_in, check_out, adults=2)
            if result.success:
                available_hotels = [
                    hotel for hotel in result.data 
                    if hotel.get('price_range', {}).get('available', False)
                ]
                print(f"💰 {len(available_hotels)} hotels have real pricing available")
                
                if available_hotels:
                    print("🏆 Hotels with pricing:")
                    for hotel in available_hotels[:3]:
                        price_data = hotel.get('price_range', {})
                        print(f"  - {hotel['name']}: ${price_data.get('total', 'N/A')}")
                    break  # Found a city with pricing, stop testing
            else:
                print(f"❌ Error: {result.error}")
        else:
            print(f"❌ Could not find city code for {city}")
    
    if not any(available_hotels for available_hotels in [api.search_hotels(api.get_city_code(city), date(2024, 9, 15), date(2024, 9, 18), 2).data if api.get_city_code(city) else [] for city in test_cities]):
        print("\n📝 Note: No cities had pricing data in sandbox environment.")
        print("This is normal - sandbox has limited data. Try production environment for real pricing.")

def test_integrated_availability():
    """Test availability checking through the main planner."""
    print("\n\n🔍 Testing Integrated Availability Checking")
    print("=" * 60)
    
    planner = SmartTravelPlanner()
    
    # Test availability for a future date (not peak season)
    destination = "San Francisco"
    check_in = date(2024, 9, 15)  # Mid-September (less peak)
    check_out = date(2024, 9, 18)
    
    print(f"🏨 Checking real availability for {destination}")
    print(f"📅 Dates: {check_in} to {check_out}")
    print(f"👥 Guests: 2 adults")
    
    availability = planner.check_hotel_availability(destination, check_in, check_out, adults=2)
    
    if availability["success"]:
        print(f"\n✅ Found {availability['total_available']} available hotels!")
        
        # Show cost breakdown
        if availability["data"]:
            costs = [hotel.get('price_range', {}).get('total', 0) for hotel in availability["data"]]
            min_cost = min(costs)
            max_cost = max(costs)
            avg_cost = sum(costs) / len(costs)
            
            print(f"\n💰 Cost Breakdown:")
            print(f"   💵 Cheapest: ${min_cost:.2f}")
            print(f"   💵 Most Expensive: ${max_cost:.2f}")
            print(f"   💵 Average: ${avg_cost:.2f}")
            
            # Show top recommendations
            print(f"\n🏆 Top 3 Recommendations:")
            for i, hotel in enumerate(availability["data"][:3], 1):
                price_data = hotel.get('price_range', {})
                print(f"\n{i}. {hotel['name']}")
                print(f"   💵 ${price_data.get('total', 'N/A')} total")
                print(f"   ⭐ Rating: {hotel.get('rating', 'N/A')}")
                
    else:
        print(f"❌ Error: {availability['error']}")

def main():
    """Main test function."""
    print("🏨 Real Hotel Availability Testing")
    print("=" * 60)
    print("This script tests real-time hotel availability and pricing")
    print("using the Amadeus API integration.")
    print()
    
    # Test direct API
    test_amadeus_api()
    
    # Test integrated functionality
    test_integrated_availability()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("\n📝 Notes:")
    print("- Real availability data requires Amadeus API credentials")
    print("- Pricing is real-time and subject to change")
    print("- Availability may vary based on demand and season")
    print("- Book early for peak travel dates!")

if __name__ == "__main__":
    main() 