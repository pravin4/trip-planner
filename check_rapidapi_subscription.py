#!/usr/bin/env python3
"""
Check RapidAPI subscription status and available endpoints
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 RapidAPI Subscription Diagnostic...")

api_key = os.getenv("BOOKING_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

print(f"✅ API Key: {api_key[:10]}...{api_key[-10:]}")

# Test different possible Booking.com API hosts
possible_hosts = [
    "booking-com.p.rapidapi.com",
    "booking-com-v1.p.rapidapi.com", 
    "booking-com-api.p.rapidapi.com"
]

print("\n🌐 Testing different API hosts...")

for host in possible_hosts:
    print(f"\n📡 Testing host: {host}")
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host
    }
    
    # Try a simple endpoint
    url = f"https://{host}/v1/hotels/locations"
    params = {"query": "test", "locale": "en-us"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS! This host works: {host}")
            break
        elif response.status_code == 403:
            print(f"  ❌ 403 Forbidden - Not subscribed to this API")
        else:
            print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}...")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n📋 Troubleshooting Steps:")
print("1. Go to https://rapidapi.com/apidojo/api/booking/")
print("2. Make sure you're subscribed to the 'Booking.com' API")
print("3. Check if your subscription is active")
print("4. Verify the API key matches your subscription")
print("5. Try the free plan if you haven't already")

print("\n🔗 Direct Links:")
print("- Booking.com API: https://rapidapi.com/apidojo/api/booking/")
print("- Your RapidAPI Dashboard: https://rapidapi.com/dashboard")

print("\n🎉 Diagnostic completed!") 