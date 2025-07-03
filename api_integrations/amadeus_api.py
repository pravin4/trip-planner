"""
Amadeus API Integration
Provides real-time hotel availability and pricing data.
Free tier available with registration.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import date, datetime, timedelta
from models.travel_models import Location, Accommodation, AccommodationType, APIResponse
import logging

logger = logging.getLogger(__name__)

class AmadeusAPI:
    """Amadeus API client for hotel availability and pricing."""
    
    def __init__(self):
        # Determine which environment to use
        self.environment = os.getenv("AMADEUS_ENVIRONMENT", "sandbox").lower()
        
        if self.environment == "production":
            self.client_id = os.getenv("AMADEUS_PRODUCTION_CLIENT_ID")
            self.client_secret = os.getenv("AMADEUS_PRODUCTION_CLIENT_SECRET")
            self.base_url = "https://api.amadeus.com/v1"  # Production API
        else:
            self.client_id = os.getenv("AMADEUS_SANDBOX_CLIENT_ID")
            self.client_secret = os.getenv("AMADEUS_SANDBOX_CLIENT_SECRET")
            self.base_url = "https://test.api.amadeus.com/v1"  # Test API
        
        self.access_token = None
        self.token_expiry = None
        
        # Common city codes as fallbacks
        self.common_city_codes = {
            "san francisco": "SFO",
            "new york": "NYC", 
            "los angeles": "LAX",
            "chicago": "CHI",
            "miami": "MIA",
            "las vegas": "LAS",
            "seattle": "SEA",
            "boston": "BOS",
            "washington dc": "WAS",
            "denver": "DEN",
            "austin": "AUS",
            "nashville": "BNA",
            "portland": "PDX",
            "atlanta": "ATL",
            "phoenix": "PHX",
            "dallas": "DFW",
            "houston": "IAH",
            "orlando": "MCO",
            "san diego": "SAN",
            "philadelphia": "PHL"
        }
        
        if not self.client_id or not self.client_secret:
            logger.warning(f"Amadeus {self.environment} API credentials not found. Set AMADEUS_{self.environment.upper()}_CLIENT_ID and AMADEUS_{self.environment.upper()}_CLIENT_SECRET in .env")
        else:
            logger.info(f"Amadeus {self.environment} environment configured")
    
    def _get_access_token(self) -> bool:
        """Get OAuth access token from Amadeus API."""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return True
        
        if not self.client_id or not self.client_secret:
            return False
        
        try:
            url = f"{self.base_url}/security/oauth2/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 1800)  # Default 30 minutes
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to get Amadeus access token: {e}")
            return False
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make authenticated request to Amadeus API."""
        if not self._get_access_token():
            return None
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Amadeus API request failed: {e}")
            return None
    
    def search_hotels(self, city_code: str, check_in: date, check_out: date, 
                     adults: int = 1, radius: int = 5) -> APIResponse:
        """
        Search for available hotels with real pricing.
        
        Args:
            city_code: IATA city code (e.g., "SFO" for San Francisco)
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            radius: Search radius in km
            
        Returns:
            APIResponse with hotel availability and pricing
        """
        try:
            if not self._get_access_token():
                return APIResponse(success=False, error="Amadeus API not configured")
            
            # First, get hotels in the city
            hotel_params = {
                'cityCode': city_code
            }
            
            hotel_data = self._make_request('/reference-data/locations/hotels/by-city', hotel_params)
            if not hotel_data:
                return APIResponse(success=False, error="Failed to fetch hotel data")
            
            hotels = []
            for hotel in hotel_data.get('data', []):
                hotel_info = {
                    'name': hotel.get('name', 'Unknown'),
                    'hotel_id': hotel.get('hotelId'),
                    'chain_code': hotel.get('chainCode'),
                    'location': {
                        'latitude': hotel.get('geoCode', {}).get('latitude'),
                        'longitude': hotel.get('geoCode', {}).get('longitude'),
                        'address': hotel.get('address', {})
                    },
                    'rating': hotel.get('rating'),
                    'amenities': hotel.get('amenities', []),
                    'available': True,  # Will be updated with pricing data
                    'price_range': None  # Will be populated with real pricing
                }
                hotels.append(hotel_info)
            
            # Get pricing for available hotels
            hotels_with_pricing = self._get_hotel_pricing(hotels, check_in, check_out, adults)
            
            return APIResponse(
                success=True,
                data=hotels_with_pricing,
                metadata={
                    'city_code': city_code,
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'total_hotels': len(hotels_with_pricing)
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return APIResponse(success=False, error=str(e))
    
    def _get_hotel_pricing(self, hotels: List[Dict], check_in: date, 
                          check_out: date, adults: int) -> List[Dict]:
        """Get real pricing for hotels."""
        hotels_with_pricing = []
        
        for hotel in hotels[:10]:  # Limit to 10 hotels to avoid rate limits
            try:
                hotel_id = hotel.get('hotel_id')
                if not hotel_id:
                    continue
                
                params = {
                    'hotelIds': hotel_id,
                    'checkInDate': check_in.strftime('%Y-%m-%d'),
                    'checkOutDate': check_out.strftime('%Y-%m-%d'),
                    'adults': adults,
                    'currency': 'USD'
                }
                
                pricing_data = self._make_request('/shopping/hotel-offers', params)
                if pricing_data and pricing_data.get('data'):
                    offers = pricing_data['data'][0].get('offers', [])
                    if offers:
                        # Get the best offer
                        best_offer = min(offers, key=lambda x: float(x.get('price', {}).get('total', 999999)))
                        hotel['price_range'] = {
                            'total': float(best_offer.get('price', {}).get('total', 0)),
                            'currency': best_offer.get('price', {}).get('currency', 'USD'),
                            'base': float(best_offer.get('price', {}).get('base', 0)),
                            'taxes': float(best_offer.get('price', {}).get('taxes', 0)),
                            'available': True
                        }
                    else:
                        hotel['price_range'] = {'available': False, 'reason': 'No offers available'}
                else:
                    hotel['price_range'] = {'available': False, 'reason': 'Pricing not available'}
                
                hotels_with_pricing.append(hotel)
                
            except Exception as e:
                logger.error(f"Error getting pricing for hotel {hotel.get('name')}: {e}")
                hotel['price_range'] = {'available': False, 'reason': 'Error fetching pricing'}
                hotels_with_pricing.append(hotel)
        
        return hotels_with_pricing
    
    def get_city_code(self, city_name: str) -> Optional[str]:
        """Get IATA city code for a city name."""
        try:
            # First try the common city codes
            city_lower = city_name.lower()
            if city_lower in self.common_city_codes:
                return self.common_city_codes[city_lower]
            
            # Try API lookup
            params = {
                'keyword': city_name,
                'subType': 'CITY'
            }
            
            data = self._make_request('/reference-data/locations', params)
            if data and data.get('data'):
                # Look for the best match
                for location in data['data']:
                    if location.get('subType') == 'CITY':
                        return location.get('iataCode')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting city code for {city_name}: {e}")
            return None
    
    def check_availability(self, hotel_id: str, check_in: date, 
                          check_out: date, adults: int = 1) -> APIResponse:
        """
        Check specific hotel availability and pricing.
        
        Args:
            hotel_id: Amadeus hotel ID
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            
        Returns:
            APIResponse with availability and pricing
        """
        try:
            params = {
                'hotelIds': hotel_id,
                'checkInDate': check_in.strftime('%Y-%m-%d'),
                'checkOutDate': check_out.strftime('%Y-%m-%d'),
                'adults': adults,
                'currency': 'USD'
            }
            
            data = self._make_request('/shopping/hotel-offers', params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch availability")
            
            if not data.get('data'):
                return APIResponse(success=False, error="No availability data found")
            
            hotel_data = data['data'][0]
            offers = hotel_data.get('offers', [])
            
            if not offers:
                return APIResponse(
                    success=False, 
                    error="No rooms available for selected dates"
                )
            
            # Get all available offers
            available_offers = []
            for offer in offers:
                offer_info = {
                    'room_type': offer.get('room', {}).get('type', 'Unknown'),
                    'board_type': offer.get('boardType', 'ROOM_ONLY'),
                    'price': {
                        'total': float(offer.get('price', {}).get('total', 0)),
                        'currency': offer.get('price', {}).get('currency', 'USD'),
                        'base': float(offer.get('price', {}).get('base', 0)),
                        'taxes': float(offer.get('price', {}).get('taxes', 0))
                    },
                    'cancellation_policy': offer.get('policies', {}).get('cancellation', {}),
                    'available': True
                }
                available_offers.append(offer_info)
            
            return APIResponse(
                success=True,
                data={
                    'hotel_name': hotel_data.get('hotel', {}).get('name', 'Unknown'),
                    'hotel_id': hotel_id,
                    'offers': available_offers,
                    'total_offers': len(available_offers)
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return APIResponse(success=False, error=str(e))


# Example usage and testing
if __name__ == "__main__":
    api = AmadeusAPI()
    
    print("Testing Amadeus API...")
    
    # Test city code lookup
    city_code = api.get_city_code("San Francisco")
    if city_code:
        print(f"San Francisco city code: {city_code}")
        
        # Test hotel search
        check_in = date(2024, 7, 4)
        check_out = date(2024, 7, 7)
        
        result = api.search_hotels(city_code, check_in, check_out, adults=2)
        if result.success:
            print(f"Found {len(result.data)} hotels")
            for hotel in result.data[:3]:
                print(f"- {hotel['name']}: ${hotel.get('price_range', {}).get('total', 'N/A')}")
        else:
            print(f"Error: {result.error}")
    else:
        print("Could not get city code for San Francisco") 