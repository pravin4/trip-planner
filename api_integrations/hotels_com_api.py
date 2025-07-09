"""
Hotels.com API Integration
Alternative hotel availability and pricing API.
Uses RapidAPI Hotels.com endpoint.
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

class HotelsComAPI:
    """Hotels.com API client for hotel availability and pricing."""
    
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://hotels-com-provider.p.rapidapi.com/v1"
        
        if not self.api_key:
            logger.warning("RapidAPI key not found. Set RAPIDAPI_KEY in .env for Hotels.com integration")
        else:
            logger.info("Hotels.com API configured")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make request to Hotels.com API via RapidAPI."""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'hotels-com-provider.p.rapidapi.com'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Hotels.com API request failed: {e}")
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
                return APIResponse(success=False, error="Hotels.com API not configured")
            
            # First, get destination ID
            dest_result = self._get_destination_id(destination)
            if not dest_result:
                return APIResponse(success=False, error=f"Could not find destination: {destination}")
            
            # Search for hotels
            params = {
                'query': destination,
                'checkin_date': check_in.strftime('%Y-%m-%d'),
                'checkout_date': check_out.strftime('%Y-%m-%d'),
                'adults_number': adults,
                'children_number': children,
                'room_number': '1',
                'currency': 'USD',
                'locale': 'en_US'
            }
            
            data = self._make_request('/hotels/search', params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch hotel data")
            
            hotels = []
            for hotel in data.get('searchResults', {}).get('results', []):
                hotel_info = hotel.get('property', {})
                price_info = hotel.get('ratePlan', {}).get('price', {})
                
                hotel_data = {
                    'name': hotel_info.get('name', 'Unknown'),
                    'hotel_id': hotel_info.get('id'),
                    'location': {
                        'latitude': hotel_info.get('mapMarker', {}).get('lat'),
                        'longitude': hotel_info.get('mapMarker', {}).get('lng'),
                        'address': hotel_info.get('address', {}).get('streetAddress', ''),
                        'city': hotel_info.get('address', {}).get('locality', ''),
                        'country': hotel_info.get('address', {}).get('countryName', '')
                    },
                    'rating': hotel_info.get('starRating', 0),
                    'price_range': {
                        'min_price': price_info.get('current', {}).get('plain', 0),
                        'currency': price_info.get('current', {}).get('currencyInfo', {}).get('code', 'USD'),
                        'available': True
                    },
                    'amenities': hotel_info.get('amenities', []),
                    'available': True
                }
                hotels.append(hotel_data)
            
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
        """Get destination ID for Hotels.com API."""
        try:
            params = {
                'query': destination,
                'locale': 'en_US'
            }
            
            data = self._make_request('/destinations/search', params)
            if not data:
                return None
            
            # Return the first result
            results = data.get('suggestions', [])
            if results:
                return {
                    'dest_id': results[0].get('destinationId'),
                    'name': results[0].get('names', {}).get('displayName', {}).get('text'),
                    'type': 'destination'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting destination ID: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    api = HotelsComAPI()
    
    print("Testing Hotels.com API...")
    
    # Test hotel search
    result = api.search_hotels("San Francisco", date(2025, 7, 4), date(2025, 7, 6), 2)
    if result.success:
        print(f"Found {len(result.data)} hotels")
        for hotel in result.data[:3]:
            print(f"- {hotel['name']}: ${hotel['price_range']['min_price']}")
    else:
        print(f"Error: {result.error}") 