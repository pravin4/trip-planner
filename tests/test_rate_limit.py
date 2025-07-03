#!/usr/bin/env python3
"""
Test rate limits and wait before retrying
"""

import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("⏱️ Testing Rate Limits...")

api_key = os.getenv("BOOKING_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
}

# Test with a simple endpoint and wait between requests
endpoints_to_test = [
    ("hotels/search", {
        "dest_id": "-553173",
        "search_type": "city",
        "arrival_date": "2024-08-01",
        "departure_date": "2024-08-04",
        "adults": "2",
        "children": "0",
        "room_number": "1",
        "currency": "USD",
        "units": "metric",
        "page_number": "0"
    }),
    ("properties/list-by-map", {
        "bbox": "-122.5,37.7,-122.4,37.8",
        "currency": "USD",
        "checkin_date": "2024-08-01",
        "checkout_date": "2024-08-04",
        "adults": "2",
        "children": "0",
        "room_number": "1"
    })
]

for i, (endpoint, params) in enumerate(endpoints_to_test):
    print(f"\n🌐 Test {i+1}: {endpoint}")
    
    url = f"https://booking-com.p.rapidapi.com/v1/{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            if endpoint == "hotels/search":
                results = data.get("result", [])
                print(f"Found {len(results)} hotels")
                if results:
                    hotel = results[0]
                    print(f"First hotel: {hotel.get('hotel_name', 'Unknown')}")
                    print(f"Price: ${hotel.get('min_total_price', 'N/A')}")
            elif endpoint == "properties/list-by-map":
                results = data.get("result", [])
                print(f"Found {len(results)} properties")
                if results:
                    prop = results[0]
                    print(f"First property: {prop.get('hotel_name', 'Unknown')}")
                    print(f"Price: ${prop.get('min_total_price', 'N/A')}")
        elif response.status_code == 429:
            print("⏱️ Rate limited. Waiting 30 seconds...")
            time.sleep(30)
            
            # Retry after waiting
            print("🔄 Retrying...")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"Retry Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS after retry!")
            else:
                print(f"❌ Still failed: {response.text[:200]}...")
        else:
            print(f"❌ Failed: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Wait between tests
    if i < len(endpoints_to_test) - 1:
        print("⏱️ Waiting 10 seconds before next test...")
        time.sleep(10)

print("\n🎉 Rate limit test completed!") 