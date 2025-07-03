#!/usr/bin/env python3
"""
Simple test to verify API key loading
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔑 Testing API Key Loading...")

# Check if the key is loaded
api_key = os.getenv("BOOKING_API_KEY")
if api_key:
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else '***'}")
    print(f"   Length: {len(api_key)} characters")
else:
    print("❌ No API key found in .env file")

# Test a simple request to see the exact error
import requests

if api_key:
    print("\n🌐 Testing direct API call...")
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }
    
    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
    params = {
        "query": "San Francisco",
        "locale": "en-us"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ API call successful!")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
else:
    print("❌ Cannot test API without key") 