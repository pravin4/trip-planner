"""
Accommodation Fallback System
Provides realistic hotel data when external APIs (Amadeus, Booking.com) are not available.
"""

import random
from typing import List, Dict, Any
from datetime import date
import logging

logger = logging.getLogger(__name__)

class AccommodationFallback:
    """Fallback accommodation system with realistic hotel data."""
    
    # Common hotel chains and their characteristics
    HOTEL_CHAINS = {
        "budget": [
            "Motel 6", "Super 8", "Days Inn", "Travelodge", "Red Roof Inn",
            "Econo Lodge", "Howard Johnson", "Comfort Inn", "Quality Inn"
        ],
        "midrange": [
            "Holiday Inn", "Best Western", "Hampton Inn", "Courtyard by Marriott",
            "Fairfield Inn", "Hilton Garden Inn", "Embassy Suites", "DoubleTree"
        ],
        "upscale": [
            "Marriott", "Hilton", "Hyatt", "Sheraton", "Westin", "Renaissance",
            "W Hotels", "Ritz-Carlton", "Four Seasons", "Waldorf Astoria"
        ]
    }
    
    # Price ranges by budget level (per night)
    PRICE_RANGES = {
        "budget": (60, 120),
        "midrange": (120, 250),
        "upscale": (250, 600)
    }
    
    # Common amenities by hotel type
    AMENITIES = {
        "budget": ["Free WiFi", "Parking", "24/7 Front Desk"],
        "midrange": ["Free WiFi", "Parking", "24/7 Front Desk", "Breakfast", "Fitness Center", "Pool"],
        "upscale": ["Free WiFi", "Parking", "24/7 Front Desk", "Breakfast", "Fitness Center", "Pool", "Spa", "Restaurant", "Room Service"]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_fallback_hotels(self, destination: str, check_in: date, check_out: date, 
                           adults: int = 2, budget_level: str = "midrange", 
                           count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate realistic fallback hotel data.
        
        Args:
            destination: Destination name
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            budget_level: Budget level (budget, midrange, upscale)
            count: Number of hotels to generate
            
        Returns:
            List of hotel dictionaries
        """
        try:
            hotels = []
            nights = (check_out - check_in).days
            
            for i in range(count):
                hotel = self._generate_hotel(destination, budget_level, nights, adults, i)
                hotels.append(hotel)
            
            return hotels
            
        except Exception as e:
            self.logger.error(f"Error generating fallback hotels: {e}")
            return []
    
    def _generate_hotel(self, destination: str, budget_level: str, nights: int, 
                       adults: int, index: int) -> Dict[str, Any]:
        """Generate a single hotel entry."""
        
        # Select hotel chain
        chains = self.HOTEL_CHAINS.get(budget_level, self.HOTEL_CHAINS["midrange"])
        chain = random.choice(chains)
        
        # Generate hotel name
        hotel_name = f"{chain} {destination}"
        if index > 0:
            hotel_name += f" - {index + 1}"
        
        # Generate price
        min_price, max_price = self.PRICE_RANGES.get(budget_level, self.PRICE_RANGES["midrange"])
        base_price = random.uniform(min_price, max_price)
        
        # Adjust price based on demand (weekend vs weekday)
        day_of_week = check_in.weekday()
        if day_of_week >= 4:  # Weekend
            base_price *= 1.2
        
        # Calculate total price
        total_price = base_price * nights * adults
        
        # Generate rating
        if budget_level == "budget":
            rating = random.uniform(3.0, 4.0)
        elif budget_level == "midrange":
            rating = random.uniform(3.5, 4.5)
        else:  # upscale
            rating = random.uniform(4.0, 5.0)
        
        # Select amenities
        available_amenities = self.AMENITIES.get(budget_level, self.AMENITIES["midrange"])
        num_amenities = random.randint(3, len(available_amenities))
        selected_amenities = random.sample(available_amenities, num_amenities)
        
        return {
            "name": hotel_name,
            "hotel_id": f"fallback_{destination.lower().replace(' ', '_')}_{index}",
            "chain_code": chain.split()[0].upper(),
            "location": {
                "latitude": None,
                "longitude": None,
                "address": f"{destination}, CA, USA",
                "city": destination,
                "country": "USA"
            },
            "rating": round(rating, 1),
            "amenities": selected_amenities,
            "available": True,
            "price_range": {
                "total": round(total_price, 2),
                "currency": "USD",
                "base": round(base_price, 2),
                "taxes": round(total_price * 0.12, 2),  # 12% tax estimate
                "available": True,
                "per_night": round(base_price, 2)
            },
            "source": "Fallback System",
            "description": f"Comfortable {budget_level} accommodation in {destination}"
        }
    
    def get_accommodation_recommendations(self, destination: str, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get accommodation recommendations based on preferences.
        
        Args:
            destination: Destination name
            preferences: User preferences
            
        Returns:
            List of accommodation recommendations
        """
        try:
            # Determine budget level from preferences
            budget_level = preferences.get("budget_level", "moderate")
            if budget_level in ["low", "budget"]:
                budget_category = "budget"
            elif budget_level in ["high", "luxury"]:
                budget_category = "upscale"
            else:
                budget_category = "midrange"
            
            # Generate recommendations
            hotels = self.get_fallback_hotels(
                destination=destination,
                check_in=date.today(),
                check_out=date.today(),
                adults=preferences.get("group_size", 2),
                budget_level=budget_category,
                count=8
            )
            
            return hotels
            
        except Exception as e:
            self.logger.error(f"Error getting accommodation recommendations: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    fallback = AccommodationFallback()
    
    print("Testing Accommodation Fallback System...")
    
    # Test hotel generation
    hotels = fallback.get_fallback_hotels("San Francisco", date(2025, 7, 4), date(2025, 7, 6), 2, "midrange", 3)
    
    print(f"Generated {len(hotels)} hotels:")
    for hotel in hotels:
        print(f"- {hotel['name']}: ${hotel['price_range']['total']} ({hotel['rating']} stars)")
        print(f"  Amenities: {', '.join(hotel['amenities'][:3])}") 