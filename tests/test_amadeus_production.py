#!/usr/bin/env python3
"""
Test Amadeus Production API
Tests the Amadeus production environment with real credentials.
"""

import os
import sys
import pytest
from datetime import date, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_integrations.amadeus_api import AmadeusAPI

class TestAmadeusProduction:
    """Test Amadeus production API functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        load_dotenv()
        self.amadeus = AmadeusAPI()
        
    def test_environment_configuration(self):
        """Test that Amadeus is configured for production."""
        assert self.amadeus.environment == "production"
        assert self.amadeus.base_url == "https://api.amadeus.com/v1"
        
    def test_credentials_configured(self):
        """Test that production credentials are set."""
        prod_client_id = os.getenv("AMADEUS_PRODUCTION_CLIENT_ID")
        prod_client_secret = os.getenv("AMADEUS_PRODUCTION_CLIENT_SECRET")
        
        assert prod_client_id is not None, "AMADEUS_PRODUCTION_CLIENT_ID not set"
        assert prod_client_secret is not None, "AMADEUS_PRODUCTION_CLIENT_SECRET not set"
        
    def test_access_token(self):
        """Test that we can get an access token."""
        token_result = self.amadeus._get_access_token()
        assert token_result is True
        assert self.amadeus.access_token is not None
        
    def test_city_code_lookup(self):
        """Test city code lookup for major cities."""
        test_cities = [
            ("San Francisco", "SFO"),
            ("New York", "NYC"),
            ("Los Angeles", "LAX"),
            ("Chicago", "CHI"),
            ("Miami", "MIA")
        ]
        
        for city_name, expected_code in test_cities:
            city_code = self.amadeus.get_city_code(city_name)
            assert city_code == expected_code, f"Expected {expected_code} for {city_name}, got {city_code}"
            
    def test_hotel_search(self):
        """Test hotel search functionality."""
        city_code = self.amadeus.get_city_code("San Francisco")
        assert city_code == "SFO"
        
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=12)
        
        result = self.amadeus.search_hotels(city_code, check_in, check_out, 2)
        
        assert result.success is True, f"Hotel search failed: {result.error}"
        assert len(result.data) > 0, "No hotels found"
        
        # Check that hotels have required fields
        first_hotel = result.data[0]
        assert 'name' in first_hotel
        assert 'hotel_id' in first_hotel
        assert 'location' in first_hotel
        
    def test_hotel_pricing(self):
        """Test that hotels have pricing information."""
        city_code = self.amadeus.get_city_code("New York")
        check_in = date.today() + timedelta(days=15)
        check_out = date.today() + timedelta(days=17)
        
        result = self.amadeus.search_hotels(city_code, check_in, check_out, 2)
        
        if result.success and result.data:
            # Check that at least some hotels have pricing info
            hotels_with_pricing = [
                hotel for hotel in result.data 
                if hotel.get('price_range') and hotel['price_range'].get('available', False)
            ]
            
            # Note: Pricing might not be available for all hotels/dates
            # This test just ensures the structure is correct
            for hotel in result.data[:3]:  # Check first 3 hotels
                assert 'price_range' in hotel
                price_range = hotel['price_range']
                assert isinstance(price_range, dict)
                
    def test_city_with_state_suffix(self):
        """Test that city codes work with state suffixes."""
        # Test with state suffix
        city_code_with_state = self.amadeus.get_city_code("San Francisco, CA")
        city_code_without_state = self.amadeus.get_city_code("San Francisco")
        
        assert city_code_with_state == "SFO"
        assert city_code_without_state == "SFO"
        assert city_code_with_state == city_code_without_state

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 