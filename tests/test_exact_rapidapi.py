#!/usr/bin/env python3
"""
Test Booking.com API using exact RapidAPI documentation format
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing Exact RapidAPI Format...")

api_key = os.getenv("BOOKING_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

print(f"✅ API Key: {api_key[:10]}...{api_key[-10:]}")

# Test 1: Hotels Locations (exact format from RapidAPI docs)
print("\n🌐 Test 1: Hotels Locations")
url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
}
params = {
    "query": "San Francisco",
    "locale": "en-us"
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Hotels Search (exact format from RapidAPI docs)
print("\n🌐 Test 2: Hotels Search")
url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
params = {
    "dest_id": "-553173",  # San Francisco dest_id
    "search_type": "city",
    "arrival_date": "2024-08-01",
    "departure_date": "2024-08-04",
    "adults": "2",
    "children": "0",
    "room_number": "1",
    "currency": "USD",
    "units": "metric",
    "page_number": "0",
    "checkin_date": "2024-08-01",
    "checkout_date": "2024-08-04"
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Properties List by Map (deprecated but might work)
print("\n🌐 Test 3: Properties List by Map")
url = "https://booking-com.p.rapidapi.com/v1/properties/list-by-map"
params = {
    "bbox": "-122.5,37.7,-122.4,37.8",
    "currency": "USD",
    "checkin_date": "2024-08-01",
    "checkout_date": "2024-08-04",
    "adults": "2",
    "children": "0",
    "room_number": "1"
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n🎉 All tests completed!") 