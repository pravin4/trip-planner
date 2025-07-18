"""
Booking.com API Integration
Provides hotel availability and pricing as a fallback to Amadeus.
Uses RapidAPI Booking.com endpoint.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from models.travel_models import Location, Accommodation, AccommodationType, APIResponse
import logging

logger = logging.getLogger(__name__)

class BookingAPI:
    """Booking.com API client for hotel availability and pricing."""
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://booking-com.p.rapidapi.com/v1"
        
        if not self.api_key:
            logger.warning("RapidAPI key not found. Set RAPIDAPI_KEY in .env for Booking.com integration")
        else:
            logger.info("Booking.com API configured")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make request to Booking.com API via RapidAPI."""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'booking-com.p.rapidapi.com'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Booking.com API request failed: {e}")
            return None
    
    def search_hotels(self, destination: str, check_in: date, check_out: date, 
                     adults: int = 2, children: int = 0) -> APIResponse:
        """
        Search for available hotels with pricing.
        
        Args:
            destination: Destination name (e.g., "San Francisco")
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            
        Returns:
            APIResponse with hotel availability and pricing
        """
        try:
            if not self.api_key:
                return APIResponse(success=False, error="Booking.com API not configured")
            
            # First, get destination ID
            dest_result = self._get_destination_id(destination)
            if not dest_result:
                return APIResponse(success=False, error=f"Could not find destination: {destination}")
            
            # Search for hotels
            params = {
                'dest_id': dest_result['dest_id'],
                'search_type': 'city',
                'arrival_date': check_in.strftime('%Y-%m-%d'),
                'departure_date': check_out.strftime('%Y-%m-%d'),
                'adults': adults,
                'children': children,
                'room_number': '1',
                'units': 'metric',
                'currency': 'USD',
                'locale': 'en-us'
            }
            
            data = self._make_request('/hotels/search', params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch hotel data")
            
            hotels = []
            for hotel in data.get('result', []):
                hotel_info = {
                    'name': hotel.get('hotel_name', 'Unknown'),
                    'hotel_id': hotel.get('hotel_id'),
                    'location': {
                        'latitude': hotel.get('latitude'),
                        'longitude': hotel.get('longitude'),
                        'address': hotel.get('address', ''),
                        'city': hotel.get('city', ''),
                        'country': hotel.get('country', '')
                    },
                    'rating': hotel.get('review_score', 0),
                    'price_range': {
                        'min_price': hotel.get('min_total_price', 0),
                        'max_price': hotel.get('max_total_price', 0),
                        'currency': 'USD',
                        'available': True
                    },
                    'amenities': hotel.get('hotel_include_breakfast', False),
                    'available': True
                }
                hotels.append(hotel_info)
            
            return APIResponse(
                success=True,
                data=hotels,
                metadata={
                    'destination': destination,
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'total_hotels': len(hotels)
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return APIResponse(success=False, error=str(e))
    
    def _get_destination_id(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get destination ID for Booking.com API."""
        try:
            params = {
                'name': destination,
                'locale': 'en-us'
            }
            
            data = self._make_request('/hotels/locations', params)
            if not data:
                return None
            
            # Return the first result
            results = data.get('result', [])
            if results:
                return {
                    'dest_id': results[0].get('dest_id'),
                    'name': results[0].get('name'),
                    'type': results[0].get('dest_type')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting destination ID: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    api = BookingAPI()
    
    print("Testing Booking.com API...")
    
    # Test hotel search
    result = api.search_hotels("San Francisco", date(2025, 7, 4), date(2025, 7, 6), 2)
    if result.success:
        print(f"Found {len(result.data)} hotels")
        for hotel in result.data[:3]:
            print(f"- {hotel['name']}: ${hotel['price_range']['min_price']}")
    else:
        print(f"Error: {result.error}") 