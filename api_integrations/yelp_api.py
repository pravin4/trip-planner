"""
Yelp API Integration
Provides access to restaurant recommendations, reviews, and business information.
"""

import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import List, Dict, Optional, Any
from models.travel_models import Location, Activity, ActivityType, APIResponse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class YelpAPI:
    """Yelp API client for restaurant and business data."""
    
    def __init__(self):
        self.api_key = os.getenv('YELP_API_KEY')
        self.base_url = "https://api.yelp.com/v3"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'User-Agent': 'SmartTravelPlanner/1.0'
            })
            logger.info("Yelp API configured with API key")
        else:
            logger.warning("Yelp API key not found. Yelp integration will be limited.")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make a request to Yelp API."""
        if not self.api_key:
            logger.warning("Yelp API key not available")
            return None
            
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Yelp API request failed: {e}")
            return None
    
    def search_restaurants(self, location: str, term: str = "restaurants", 
                          limit: int = 20, price: str = None, 
                          open_now: bool = True) -> APIResponse:
        """
        Search for restaurants in a location.
        
        Args:
            location: Location to search (city, address, etc.)
            term: Search term (default: "restaurants")
            limit: Maximum number of results
            price: Price range (1-4, where 1=$, 4=$$$$)
            open_now: Whether to only show currently open businesses
            
        Returns:
            APIResponse with restaurant data
        """
        try:
            params = {
                'location': location,
                'term': term,
                'limit': limit,
                'open_now': open_now
            }
            
            if price:
                params['price'] = price
            
            data = self._make_request('/businesses/search', params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch data")
            
            businesses = data.get('businesses', [])
            
            restaurants = []
            for business in businesses:
                restaurant = {
                    'name': business.get('name', ''),
                    'rating': business.get('rating', 0),
                    'price': business.get('price', ''),
                    'categories': [cat.get('title', '') for cat in business.get('categories', [])],
                    'location': {
                        'address': business.get('location', {}).get('address1', ''),
                        'city': business.get('location', {}).get('city', ''),
                        'state': business.get('location', {}).get('state', ''),
                        'zip_code': business.get('location', {}).get('zip_code', ''),
                        'latitude': business.get('coordinates', {}).get('latitude'),
                        'longitude': business.get('coordinates', {}).get('longitude')
                    },
                    'phone': business.get('phone', ''),
                    'url': business.get('url', ''),
                    'review_count': business.get('review_count', 0),
                    'distance': business.get('distance', 0),
                    'is_closed': business.get('is_closed', True)
                }
                restaurants.append(restaurant)
            
            return APIResponse(
                success=True,
                data=restaurants,
                metadata={
                    'location': location,
                    'total_results': len(restaurants),
                    'term': term
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_restaurant_details(self, business_id: str) -> APIResponse:
        """
        Get detailed information about a specific restaurant.
        
        Args:
            business_id: Yelp business ID
            
        Returns:
            APIResponse with detailed restaurant data
        """
        try:
            data = self._make_request(f'/businesses/{business_id}')
            if not data:
                return APIResponse(success=False, error="Failed to fetch restaurant details")
            
            restaurant = {
                'name': data.get('name', ''),
                'rating': data.get('rating', 0),
                'price': data.get('price', ''),
                'categories': [cat.get('title', '') for cat in data.get('categories', [])],
                'location': {
                    'address': data.get('location', {}).get('address1', ''),
                    'city': data.get('location', {}).get('city', ''),
                    'state': data.get('location', {}).get('state', ''),
                    'zip_code': data.get('location', {}).get('zip_code', ''),
                    'latitude': data.get('coordinates', {}).get('latitude'),
                    'longitude': data.get('coordinates', {}).get('longitude')
                },
                'phone': data.get('phone', ''),
                'url': data.get('url', ''),
                'review_count': data.get('review_count', 0),
                'hours': data.get('hours', []),
                'is_closed': data.get('is_closed', True),
                'photos': data.get('photos', []),
                'price_range': data.get('price', ''),
                'attributes': data.get('attributes', {})
            }
            
            return APIResponse(
                success=True,
                data=restaurant,
                metadata={'business_id': business_id}
            )
            
        except Exception as e:
            logger.error(f"Error getting restaurant details: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_restaurant_reviews(self, business_id: str, limit: int = 10) -> APIResponse:
        """
        Get reviews for a specific restaurant.
        
        Args:
            business_id: Yelp business ID
            limit: Maximum number of reviews
            
        Returns:
            APIResponse with review data
        """
        try:
            params = {'limit': limit}
            data = self._make_request(f'/businesses/{business_id}/reviews', params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch reviews")
            
            reviews = data.get('reviews', [])
            
            formatted_reviews = []
            for review in reviews:
                formatted_review = {
                    'id': review.get('id', ''),
                    'rating': review.get('rating', 0),
                    'text': review.get('text', ''),
                    'time_created': review.get('time_created', ''),
                    'user': {
                        'name': review.get('user', {}).get('name', ''),
                        'image_url': review.get('user', {}).get('image_url', '')
                    }
                }
                formatted_reviews.append(formatted_review)
            
            return APIResponse(
                success=True,
                data=formatted_reviews,
                metadata={
                    'business_id': business_id,
                    'total_reviews': len(formatted_reviews)
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting restaurant reviews: {e}")
            return APIResponse(success=False, error=str(e))
    
    def search_by_cuisine(self, location: str, cuisine: str, 
                         limit: int = 15) -> APIResponse:
        """
        Search for restaurants by specific cuisine type.
        
        Args:
            location: Location to search
            cuisine: Cuisine type (e.g., "Italian", "Mexican", "Chinese")
            limit: Maximum number of results
            
        Returns:
            APIResponse with restaurant data
        """
        return self.search_restaurants(location, f"{cuisine} restaurants", limit)
    
    def get_top_rated_restaurants(self, location: str, 
                                 min_rating: float = 4.0,
                                 limit: int = 20) -> APIResponse:
        """
        Get top-rated restaurants in a location.
        
        Args:
            location: Location to search
            min_rating: Minimum rating (1.0-5.0)
            limit: Maximum number of results
            
        Returns:
            APIResponse with top-rated restaurants
        """
        try:
            # First get restaurants
            result = self.search_restaurants(location, "restaurants", limit * 2)
            if not result.success:
                return result
            
            # Filter by rating
            top_rated = [
                restaurant for restaurant in result.data
                if restaurant.get('rating', 0) >= min_rating
            ]
            
            # Sort by rating (highest first)
            top_rated.sort(key=lambda x: x.get('rating', 0), reverse=True)
            
            return APIResponse(
                success=True,
                data=top_rated[:limit],
                metadata={
                    'location': location,
                    'min_rating': min_rating,
                    'total_results': len(top_rated[:limit])
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting top-rated restaurants: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_restaurants_by_price(self, location: str, price_level: str,
                                limit: int = 20) -> APIResponse:
        """
        Get restaurants by price level.
        
        Args:
            location: Location to search
            price_level: Price level (1-4, where 1=$, 4=$$$$)
            limit: Maximum number of results
            
        Returns:
            APIResponse with restaurants in specified price range
        """
        return self.search_restaurants(location, "restaurants", limit, price_level)


# Example usage and testing
if __name__ == "__main__":
    api = YelpAPI()
    
    print("Testing Yelp API...")
    
    # Test restaurant search
    search_result = api.search_restaurants("San Francisco, CA", "Italian restaurants", limit=5)
    if search_result.success:
        print(f"Found {len(search_result.data)} restaurants")
        for restaurant in search_result.data[:3]:
            print(f"- {restaurant['name']} ({restaurant['rating']} stars, {restaurant['price']})")
    
    # Test top-rated restaurants
    top_result = api.get_top_rated_restaurants("San Francisco, CA", min_rating=4.5, limit=5)
    if top_result.success:
        print(f"\nFound {len(top_result.data)} top-rated restaurants")
        for restaurant in top_result.data[:3]:
            print(f"- {restaurant['name']} ({restaurant['rating']} stars)") 