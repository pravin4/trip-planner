"""
Geocoding Service
Provides real geocoding functionality using Google Maps API and fallback services.
"""

import os
import requests
import logging
from typing import Optional, Tuple, Dict, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GeocodingService:
    """Real geocoding service using multiple APIs for reliability."""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.nominatim_base_url = "https://nominatim.openstreetmap.org"
        
    def get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location using real geocoding APIs.
        
        Args:
            location: Location string (e.g., "San Jose, CA", "Big Sur, California")
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            # Try Google Maps API first (most accurate)
            if self.google_api_key:
                coords = self._google_geocode(location)
                if coords:
                    logger.info(f"Found coordinates for '{location}' via Google: {coords}")
                    return coords
            
            # Fallback to Nominatim (OpenStreetMap)
            coords = self._nominatim_geocode(location)
            if coords:
                logger.info(f"Found coordinates for '{location}' via Nominatim: {coords}")
                return coords
            
            logger.warning(f"Could not find coordinates for '{location}'")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding '{location}': {e}")
            return None
    
    def _google_geocode(self, location: str) -> Optional[Tuple[float, float]]:
        """Geocode using Google Maps API."""
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': location,
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                lat = result['geometry']['location']['lat']
                lng = result['geometry']['location']['lng']
                return (lat, lng)
            
            return None
            
        except Exception as e:
            logger.error(f"Google geocoding error: {e}")
            return None
    
    def _nominatim_geocode(self, location: str) -> Optional[Tuple[float, float]]:
        """Geocode using Nominatim (OpenStreetMap) as fallback."""
        try:
            url = f"{self.nominatim_base_url}/search"
            params = {
                'q': location,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'SmartTravelPlanner/1.0 (https://github.com/your-repo)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                return (lat, lon)
            
            return None
            
        except Exception as e:
            logger.error(f"Nominatim geocoding error: {e}")
            return None
    
    def get_location_info(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed location information including coordinates and address components.
        
        Args:
            location: Location string
            
        Returns:
            Dictionary with location details or None
        """
        try:
            if not self.google_api_key:
                return None
            
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': location,
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                # Extract address components
                address_components = {}
                for component in result['address_components']:
                    types = component['types']
                    if 'locality' in types:
                        address_components['city'] = component['long_name']
                    elif 'administrative_area_level_1' in types:
                        address_components['state'] = component['long_name']
                    elif 'country' in types:
                        address_components['country'] = component['long_name']
                    elif 'postal_code' in types:
                        address_components['postal_code'] = component['long_name']
                
                return {
                    'formatted_address': result['formatted_address'],
                    'coordinates': (
                        result['geometry']['location']['lat'],
                        result['geometry']['location']['lng']
                    ),
                    'address_components': address_components,
                    'place_id': result['place_id']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting location info for '{location}': {e}")
            return None
    
    def calculate_distance(self, from_location: str, to_location: str) -> Optional[float]:
        """
        Calculate real distance between two locations using Google Maps API.
        
        Args:
            from_location: Starting location
            to_location: Destination location
            
        Returns:
            Distance in kilometers or None
        """
        try:
            if not self.google_api_key:
                return None
            
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': from_location,
                'destinations': to_location,
                'units': 'metric',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if (data['status'] == 'OK' and 
                data['rows'] and 
                data['rows'][0]['elements'] and
                data['rows'][0]['elements'][0]['status'] == 'OK'):
                
                distance_text = data['rows'][0]['elements'][0]['distance']['text']
                # Extract numeric value from "123.4 km"
                distance_km = float(distance_text.split()[0])
                return distance_km
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return None
    
    def get_travel_time(self, from_location: str, to_location: str, 
                       mode: str = 'driving') -> Optional[Dict[str, Any]]:
        """
        Get real travel time between two locations.
        
        Args:
            from_location: Starting location
            to_location: Destination location
            mode: Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Dictionary with travel time info or None
        """
        try:
            if not self.google_api_key:
                return None
            
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': from_location,
                'destinations': to_location,
                'mode': mode,
                'units': 'metric',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if (data['status'] == 'OK' and 
                data['rows'] and 
                data['rows'][0]['elements'] and
                data['rows'][0]['elements'][0]['status'] == 'OK'):
                
                element = data['rows'][0]['elements'][0]
                
                return {
                    'distance_km': float(element['distance']['text'].split()[0]),
                    'duration_minutes': element['duration']['value'] // 60,
                    'duration_text': element['duration']['text'],
                    'mode': mode
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting travel time: {e}")
            return None 