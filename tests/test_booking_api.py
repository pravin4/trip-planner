#!/usr/bin/env python3
"""
Test script for Booking.com API integration
"""

import sys
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_integrations.booking_api import BookingAPI

def test_booking_api():
    """Test the Booking.com API functionality"""
    
    print("🏨 Testing Booking.com API Integration...")
    
    try:
        api = BookingAPI()
        print("✅ Booking.com API initialized successfully")
        
        # Test destination search
        print("\n🔍 Testing destination search...")
        search_result = api.search_destinations("man")  # Test with "man" as in your example
        
        if search_result.success:
            print(f"✅ Found {len(search_result.data)} destinations")
            for dest in search_result.data[:3]:
                print(f"  - {dest['name']} (ID: {dest['dest_id']})")
            
            # Test hotel search if we have a destination
            if search_result.data:
                dest_id = search_result.data[0]['dest_id']
                check_in = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                check_out = (date.today() + timedelta(days=33)).strftime("%Y-%m-%d")
                
                print(f"\n🏨 Testing hotel search for {search_result.data[0]['name']}...")
                print(f"  Check-in: {check_in}, Check-out: {check_out}")
                
                hotel_result = api.search_hotels(dest_id, check_in, check_out)
                
                if hotel_result.success:
                    print(f"✅ Found {len(hotel_result.data)} hotels")
                    for hotel in hotel_result.data[:3]:
                        print(f"  - {hotel['name']}")
                        print(f"    Price: ${hotel['price_per_night']}/night")
                        print(f"    Rating: {hotel['rating']:.1f}/5.0")
                        print(f"    Location: {hotel['location']['address']}")
                        if hotel.get('breakfast_included'):
                            print(f"    ✅ Breakfast included")
                        if hotel.get('free_cancellation'):
                            print(f"    ✅ Free cancellation")
                else:
                    print(f"❌ Hotel search failed: {hotel_result.error}")
            else:
                print("❌ No destinations found for hotel search")
        else:
            print(f"❌ Destination search failed: {search_result.error}")
        
        print("\n🎉 Booking.com API test completed!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set BOOKING_API_KEY in your .env file")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_booking_api() 