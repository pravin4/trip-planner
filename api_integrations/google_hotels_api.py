"""
Google Hotels API Integration
Uses Google Places API to search for hotels and get availability information.
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

class GoogleHotelsAPI:
    """Google Hotels API client using Google Places API."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
        if not self.api_key:
            logger.warning("Google Maps API key not found. Set GOOGLE_MAPS_API_KEY in .env for Google Hotels integration")
        else:
            logger.info("Google Hotels API configured")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make request to Google Places API."""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            params = params or {}
            params['key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Hotels API request failed: {e}")
            return None
    
    def search_hotels(self, destination: str, check_in: date, check_out: date, 
                     adults: int = 2, children: int = 0) -> APIResponse:
        """
        Search for hotels using Google Places API.
        
        Args:
            destination: Destination name (e.g., "San Francisco")
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            
        Returns:
            APIResponse with hotel data
        """
        try:
            if not self.api_key:
                return APIResponse(success=False, error="Google Hotels API not configured")
            
            # First, get coordinates for the destination
            coords = self._get_destination_coordinates(destination)
            if not coords:
                return APIResponse(success=False, error=f"Could not find coordinates for {destination}")
            
            # Search for hotels near the destination
            params = {
                'location': f"{coords['lat']},{coords['lng']}",
                'radius': '5000',  # 5km radius
                'type': 'lodging',
                'keyword': 'hotel',
                'rankby': 'rating'
            }
            
            data = self._make_request('/nearbysearch/json', params)
            if not data or data.get('status') != 'OK':
                return APIResponse(success=False, error=f"Google API error: {data.get('status', 'Unknown')}")
            
            hotels = []
            for place in data.get('results', []):
                # Get detailed information for each hotel
                details = self._get_place_details(place.get('place_id'))
                
                hotel_data = {
                    'name': place.get('name', 'Unknown'),
                    'hotel_id': place.get('place_id'),
                    'location': {
                        'latitude': place.get('geometry', {}).get('location', {}).get('lat'),
                        'longitude': place.get('geometry', {}).get('location', {}).get('lng'),
                        'address': place.get('vicinity', ''),
                        'formatted_address': details.get('formatted_address', '')
                    },
                    'rating': place.get('rating', 0),
                    'price_level': place.get('price_level', 2),
                    'price_range': {
                        'min_price': self._estimate_price_from_level(place.get('price_level', 2)),
                        'currency': 'USD',
                        'available': True,
                        'note': 'Estimated price based on Google price level'
                    },
                    'amenities': details.get('amenities', []),
                    'available': True,
                    'photos': place.get('photos', [])
                }
                hotels.append(hotel_data)
            
            return APIResponse(
                success=True,
                data=hotels,
                metadata={
                    'destination': destination,
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'total_hotels': len(hotels),
                    'source': 'Google Places API'
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return APIResponse(success=False, error=str(e))
    
    def _get_destination_coordinates(self, destination: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a destination using Google Geocoding API."""
        try:
            params = {
                'address': destination,
                'components': 'country:US'
            }
            
            data = self._make_request('/geocode/json', params)
            if not data or data.get('status') != 'OK':
                return None
            
            results = data.get('results', [])
            if results:
                location = results[0].get('geometry', {}).get('location', {})
                return {
                    'lat': location.get('lat'),
                    'lng': location.get('lng')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates: {e}")
            return None
    
    def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information for a place."""
        try:
            params = {
                'place_id': place_id,
                'fields': 'formatted_address,formatted_phone_number,website,opening_hours,price_level'
            }
            
            data = self._make_request('/details/json', params)
            if data and data.get('status') == 'OK':
                result = data.get('result', {})
                return {
                    'formatted_address': result.get('formatted_address', ''),
                    'phone': result.get('formatted_phone_number', ''),
                    'website': result.get('website', ''),
                    'opening_hours': result.get('opening_hours', {}),
                    'amenities': []  # Google doesn't provide detailed amenities
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return {}
    
    def _estimate_price_from_level(self, price_level: int) -> float:
        """Estimate price based on Google's price level (0-4)."""
        price_estimates = {
            0: 50,   # Free
            1: 75,   # Inexpensive
            2: 150,  # Moderate
            3: 250,  # Expensive
            4: 400   # Very Expensive
        }
        return price_estimates.get(price_level, 150)


# Example usage and testing
if __name__ == "__main__":
    api = GoogleHotelsAPI()
    
    print("Testing Google Hotels API...")
    
    # Test hotel search
    result = api.search_hotels("San Francisco", date(2025, 7, 4), date(2025, 7, 6), 2)
    if result.success:
        print(f"Found {len(result.data)} hotels")
        for hotel in result.data[:3]:
            print(f"- {hotel['name']}: ${hotel['price_range']['min_price']} (Level {hotel.get('price_level', 'Unknown')})")
    else:
        print(f"Error: {result.error}") 