#!/usr/bin/env python3
"""
Test the correct Booking.com API endpoints
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing Correct Booking.com API...")

api_key = os.getenv("BOOKING_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
}

# Test 1: Search Destination
print("\n🌐 Test 1: Search Destination")
url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
params = {
    "query": "San Francisco"
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=20)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Destination search successful!")
        print(f"Response: {data}")
        
        # Extract destination ID for hotel search
        if data.get("data"):
            dest_id = data["data"][0].get("dest_id") if data["data"] else None
            print(f"Destination ID: {dest_id}")
            
            if dest_id:
                # Test 2: Search Hotels
                print(f"\n🌐 Test 2: Search Hotels for dest_id: {dest_id}")
                url2 = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
                params2 = {
                    "dest_id": dest_id,
                    "search_type": "CITY",
                    "arrival_date": "2024-08-01",
                    "departure_date": "2024-08-04",
                    "adults": "2",
                    "children": "0",
                    "room_number": "1",
                    "currency": "USD",
                    "units": "metric",
                    "page_number": "0"
                }
                
                response2 = requests.get(url2, headers=headers, params=params2, timeout=20)
                print(f"Hotel Search Status: {response2.status_code}")
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print("✅ Hotel search successful!")
                    print(f"Found {len(data2.get('data', []))} hotels")
                    
                    # Show first hotel
                    if data2.get("data"):
                        hotel = data2["data"][0]
                        print(f"First hotel: {hotel.get('hotel_name', 'Unknown')}")
                        print(f"Price: ${hotel.get('min_total_price', 'N/A')}")
                else:
                    print(f"❌ Hotel search failed: {response2.text[:200]}...")
        else:
            print("❌ No destination data found")
    else:
        print(f"❌ Destination search failed: {response.text[:200]}...")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎉 Test completed!") 