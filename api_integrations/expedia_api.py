"""
Expedia API Integration
Note: Expedia's API requires partnership/affiliation. This module provides a placeholder
for when you have official Expedia API access.

To use real Expedia data, you need:
1. Expedia Partner Central account
2. API credentials (Client ID, Client Secret)
3. Partnership agreement with Expedia

For now, this module provides a structure for real API integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import List, Dict, Optional, Any
from models.travel_models import Location, Activity, ActivityType, APIResponse
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class ExpediaAPI:
    """Expedia API client for hotel and flight data (requires partnership)."""
    
    def __init__(self):
        self.client_id = os.getenv('EXPEDIA_CLIENT_ID')
        self.client_secret = os.getenv('EXPEDIA_CLIENT_SECRET')
        self.base_url = "https://api.ean.com/v3"  # Expedia API base URL
        self.session = requests.Session()
        
        if self.client_id and self.client_secret:
            logger.info("Expedia API configured with credentials")
        else:
            logger.warning("Expedia API credentials not found. Set EXPEDIA_CLIENT_ID and EXPEDIA_CLIENT_SECRET")
    
    def _get_auth_token(self) -> Optional[str]:
        """Get OAuth token for Expedia API."""
        if not self.client_id or not self.client_secret:
            return None
            
        try:
            auth_url = "https://api.ean.com/v3/auth/oauth2/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = self.session.post(auth_url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            logger.error(f"Failed to get Expedia auth token: {e}")
            return None
    
    def search_hotels(self, location: str, check_in: date, check_out: date, 
                     guests: int = 2, rooms: int = 1, max_price: Optional[float] = None) -> APIResponse:
        """
        Search for hotels using Expedia API.
        
        Args:
            location: Destination location
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            max_price: Maximum price per night
            
        Returns:
            APIResponse with hotel data
        """
        if not self.client_id or not self.client_secret:
            return APIResponse(
                success=False, 
                error="Expedia API credentials not configured. This requires partnership with Expedia."
            )
        
        try:
            token = self._get_auth_token()
            if not token:
                return APIResponse(success=False, error="Failed to authenticate with Expedia API")
            
            # Set up headers with auth token
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Build search parameters
            params = {
                'location': location,
                'checkIn': check_in.isoformat(),
                'checkOut': check_out.isoformat(),
                'adults': guests,
                'rooms': rooms
            }
            
            if max_price:
                params['maxPrice'] = max_price
            
            # Make API request
            url = f"{self.base_url}/hotels/search"
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse hotel results
            hotels = []
            for hotel_data in data.get('hotels', []):
                hotel = {
                    'name': hotel_data.get('name', ''),
                    'address': hotel_data.get('address', {}),
                    'rating': hotel_data.get('rating', 0),
                    'price_per_night': hotel_data.get('price', {}).get('total', 0),
                    'amenities': hotel_data.get('amenities', []),
                    'images': hotel_data.get('images', []),
                    'description': hotel_data.get('description', ''),
                    'hotel_id': hotel_data.get('id', '')
                }
                hotels.append(hotel)
            
            return APIResponse(
                success=True,
                data=hotels,
                metadata={
                    'location': location,
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'total_hotels': len(hotels)
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching Expedia hotels: {e}")
            return APIResponse(success=False, error=str(e))
    
    def search_flights(self, origin: str, destination: str, departure_date: date, 
                      return_date: Optional[date] = None, passengers: int = 1) -> APIResponse:
        """
        Search for flights using Expedia API.
        
        Args:
            origin: Departure airport/city
            destination: Arrival airport/city
            departure_date: Departure date
            return_date: Return date (optional for one-way)
            passengers: Number of passengers
            
        Returns:
            APIResponse with flight data
        """
        if not self.client_id or not self.client_secret:
            return APIResponse(
                success=False, 
                error="Expedia API credentials not configured. This requires partnership with Expedia."
            )
        
        try:
            token = self._get_auth_token()
            if not token:
                return APIResponse(success=False, error="Failed to authenticate with Expedia API")
            
            # Set up headers with auth token
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Build search parameters
            params = {
                'origin': origin,
                'destination': destination,
                'departureDate': departure_date.isoformat(),
                'adults': passengers
            }
            
            if return_date:
                params['returnDate'] = return_date.isoformat()
            
            # Make API request
            url = f"{self.base_url}/flights/search"
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse flight results
            flights = []
            for flight_data in data.get('flights', []):
                flight = {
                    'airline': flight_data.get('airline', ''),
                    'flight_number': flight_data.get('flightNumber', ''),
                    'departure_time': flight_data.get('departureTime', ''),
                    'arrival_time': flight_data.get('arrivalTime', ''),
                    'duration': flight_data.get('duration', ''),
                    'price': flight_data.get('price', {}).get('total', 0),
                    'stops': flight_data.get('stops', 0),
                    'origin_airport': flight_data.get('originAirport', ''),
                    'destination_airport': flight_data.get('destinationAirport', '')
                }
                flights.append(flight)
            
            return APIResponse(
                success=True,
                data=flights,
                metadata={
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date.isoformat(),
                    'total_flights': len(flights)
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching Expedia flights: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_hotel_details(self, hotel_id: str) -> APIResponse:
        """Get detailed information about a specific hotel."""
        if not self.client_id or not self.client_secret:
            return APIResponse(
                success=False, 
                error="Expedia API credentials not configured"
            )
        
        try:
            token = self._get_auth_token()
            if not token:
                return APIResponse(success=False, error="Failed to authenticate with Expedia API")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/hotels/{hotel_id}"
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            hotel_data = response.json()
            
            return APIResponse(
                success=True,
                data=hotel_data,
                metadata={'hotel_id': hotel_id}
            )
            
        except Exception as e:
            logger.error(f"Error getting hotel details: {e}")
            return APIResponse(success=False, error=str(e))


# Example usage and testing
if __name__ == "__main__":
    api = ExpediaAPI()
    
    print("Testing Expedia API...")
    print("Note: This requires valid Expedia API credentials")
    
    # Test hotel search (will fail without credentials)
    hotel_result = api.search_hotels(
        "San Francisco, CA",
        date(2024, 6, 15),
        date(2024, 6, 20),
        guests=2
    )
    
    if hotel_result.success:
        print(f"Found {len(hotel_result.data)} hotels")
    else:
        print(f"Hotel search failed: {hotel_result.error}")
    
    # Test flight search (will fail without credentials)
    flight_result = api.search_flights(
        "SFO",
        "LAX", 
        date(2024, 6, 15),
        date(2024, 6, 20),
        passengers=2
    )
    
    if flight_result.success:
        print(f"Found {len(flight_result.data)} flights")
    else:
        print(f"Flight search failed: {flight_result.error}") 