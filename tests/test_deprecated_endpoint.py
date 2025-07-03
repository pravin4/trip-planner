#!/usr/bin/env python3
"""
Test the deprecated Booking.com endpoint that the user mentioned works
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🏨 Testing Deprecated Booking.com Endpoint...")

api_key = os.getenv("BOOKING_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
}

# Test the deprecated endpoint that the user mentioned works
url = "https://booking-com.p.rapidapi.com/v1/properties/list-by-map"
params = {
    "bbox": "-122.5,37.7,-122.4,37.8",  # San Francisco area
    "currency": "USD",
    "checkin_date": "2024-08-01",
    "checkout_date": "2024-08-04",
    "adults": "2",
    "children": "0",
    "room_number": "1"
}

try:
    print(f"🌐 Testing endpoint: {url}")
    print(f"📋 Parameters: {params}")
    
    response = requests.get(url, headers=headers, params=params, timeout=15)
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Deprecated endpoint works!")
        print(f"📈 Found {len(data.get('result', []))} properties")
        
        # Show first few results
        results = data.get('result', [])
        for i, prop in enumerate(results[:3]):
            print(f"  {i+1}. {prop.get('hotel_name', 'Unknown')}")
            print(f"     Price: ${prop.get('min_total_price', 'N/A')}")
            print(f"     Rating: {prop.get('review_score', 'N/A')}")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n🎉 Test completed!") 