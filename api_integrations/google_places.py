import os
import googlemaps
from typing import List, Optional, Dict, Any
from models.travel_models import Location, Activity, ActivityType, APIResponse
import logging

logger = logging.getLogger(__name__)


class GooglePlacesAPI:
    def __init__(self):
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable is required")
        
        self.client = googlemaps.Client(key=api_key)
    
    def search_places(self, query: str, location: Optional[str] = None, 
                     radius: int = 5000, types: Optional[List[str]] = None) -> APIResponse:
        """Search for places using Google Places API"""
        try:
            params = {
                'query': query,
                'radius': radius
            }
            
            if location:
                # Geocode the location first
                geocode_result = self.client.geocode(location)
                if geocode_result:
                    lat = geocode_result[0]['geometry']['location']['lat']
                    lng = geocode_result[0]['geometry']['location']['lng']
                    params['location'] = f"{lat},{lng}"
            
            if types:
                params['type'] = '|'.join(types)
            
            places_result = self.client.places(**params)
            
            places = []
            for place in places_result.get('results', []):
                location_obj = Location(
                    name=place.get('name', ''),
                    address=place.get('formatted_address', ''),
                    latitude=place['geometry']['location']['lat'],
                    longitude=place['geometry']['location']['lng'],
                    place_id=place.get('place_id'),
                    rating=place.get('rating'),
                    price_level=place.get('price_level')
                )
                places.append(location_obj)
            
            return APIResponse(
                success=True,
                data=places,
                metadata={'total_results': len(places)}
            )
            
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_place_details(self, place_id: str) -> APIResponse:
        """Get detailed information about a specific place"""
        try:
            details = self.client.place(place_id, fields=[
                'name', 'formatted_address', 'geometry', 'rating', 
                'price_level', 'opening_hours', 'website', 'formatted_phone_number',
                'reviews', 'photos', 'types'
            ])
            
            place_data = details.get('result', {})
            
            location = Location(
                name=place_data.get('name', ''),
                address=place_data.get('formatted_address', ''),
                latitude=place_data['geometry']['location']['lat'],
                longitude=place_data['geometry']['location']['lng'],
                place_id=place_id,
                rating=place_data.get('rating'),
                price_level=place_data.get('price_level')
            )
            
            return APIResponse(
                success=True,
                data={
                    'location': location,
                    'opening_hours': place_data.get('opening_hours'),
                    'website': place_data.get('website'),
                    'phone': place_data.get('formatted_phone_number'),
                    'types': place_data.get('types', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return APIResponse(success=False, error=str(e))
    
    def find_attractions(self, location: str, activity_type: ActivityType) -> APIResponse:
        """Find attractions based on activity type"""
        type_mapping = {
            ActivityType.CULTURAL: ['museum', 'art_gallery', 'library', 'church'],
            ActivityType.OUTDOOR: ['park', 'natural_feature', 'campground'],
            ActivityType.ADVENTURE: ['amusement_park', 'aquarium', 'zoo'],
            ActivityType.RELAXATION: ['spa', 'beauty_salon', 'health'],
            ActivityType.FOOD: ['restaurant', 'cafe', 'bar'],
            ActivityType.SHOPPING: ['shopping_mall', 'store', 'market'],
            ActivityType.NIGHTLIFE: ['bar', 'night_club', 'casino']
        }
        
        types = type_mapping.get(activity_type, ['tourist_attraction'])
        
        activities = []
        for place_type in types:
            result = self.search_places(
                query=f"{activity_type.value} in {location}",
                location=location,
                types=[place_type]
            )
            
            if result.success:
                for place in result.data:
                    # Estimate cost based on activity type and price level
                    base_costs = {
                        ActivityType.CULTURAL: 15,
                        ActivityType.OUTDOOR: 5,
                        ActivityType.ADVENTURE: 25,
                        ActivityType.RELAXATION: 50,
                        ActivityType.FOOD: 20,
                        ActivityType.SHOPPING: 0,
                        ActivityType.NIGHTLIFE: 30
                    }
                    
                    base_cost = base_costs.get(activity_type, 20)
                    price_multiplier = (place.price_level or 2) / 2
                    estimated_cost = base_cost * price_multiplier
                    
                    activity = Activity(
                        name=place.name,
                        location=place,
                        type=activity_type,
                        duration_hours=2.0,  # Default duration
                        cost=estimated_cost,
                        description=f"{activity_type.value.title()} activity at {place.name}"
                    )
                    activities.append(activity)
        
        return APIResponse(
            success=True,
            data=activities,
            metadata={'activity_type': activity_type, 'total_activities': len(activities)}
        )
    
    def get_nearby_places(self, location: str, radius: int = 1000, 
                         place_type: Optional[str] = None) -> APIResponse:
        """Get nearby places of a specific type"""
        try:
            # Geocode the location
            geocode_result = self.client.geocode(location)
            if not geocode_result:
                return APIResponse(success=False, error="Location not found")
            
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']
            
            params = {
                'location': f"{lat},{lng}",
                'radius': radius
            }
            
            if place_type:
                params['type'] = place_type
            
            nearby_result = self.client.places_nearby(**params)
            
            places = []
            for place in nearby_result.get('results', []):
                location_obj = Location(
                    name=place.get('name', ''),
                    address=place.get('vicinity', ''),
                    latitude=place['geometry']['location']['lat'],
                    longitude=place['geometry']['location']['lng'],
                    place_id=place.get('place_id'),
                    rating=place.get('rating'),
                    price_level=place.get('price_level')
                )
                places.append(location_obj)
            
            return APIResponse(
                success=True,
                data=places,
                metadata={'total_results': len(places)}
            )
            
        except Exception as e:
            logger.error(f"Error getting nearby places: {e}")
            return APIResponse(success=False, error=str(e)) 