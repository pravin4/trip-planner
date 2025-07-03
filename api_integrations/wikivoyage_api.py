"""
Wikivoyage API Integration
Provides access to travel guides, itineraries, and cultural insights from Wikivoyage.
Free to use, no API key required.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import List, Dict, Optional, Any
from models.travel_models import Location, Activity, ActivityType, APIResponse
import logging
from pydantic import BaseModel
from langgraph.graph import StateGraph, END, START
from langchain.chat_models import ChatOpenAI

logger = logging.getLogger(__name__)

class ResearchState(BaseModel):
    destination: str
    preferences: Dict[str, Any]
    research_results: Dict[str, Any]
    attractions: List[Dict[str, Any]]
    restaurants: List[Dict[str, Any]]
    accommodations: List[Dict[str, Any]]
    research_complete: bool = False
    error: Optional[str] = None

class WikivoyageAPI:
    """Wikivoyage API client for travel guides and cultural data."""
    
    def __init__(self):
        self.base_url = "https://en.wikivoyage.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartTravelPlanner/1.0 (https://github.com/your-repo)'
        })
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to Wikivoyage API."""
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Wikivoyage API request failed: {e}")
            return None
    
    def search_destinations(self, query: str, limit: int = 10) -> APIResponse:
        """
        Search for destinations in Wikivoyage.
        
        Args:
            query: Search query (e.g., "San Francisco")
            limit: Maximum number of results
            
        Returns:
            APIResponse with search results
        """
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': limit,
                'srnamespace': 0  # Main namespace (articles)
            }
            
            data = self._make_request(params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch data")
            
            search_results = data.get('query', {}).get('search', [])
            
            destinations = []
            for result in search_results:
                destinations.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'pageid': result.get('pageid'),
                    'url': f"https://en.wikivoyage.org/wiki/{result.get('title', '').replace(' ', '_')}"
                })
            
            return APIResponse(
                success=True,
                data=destinations,
                metadata={'query': query, 'total_results': len(destinations)}
            )
            
        except Exception as e:
            logger.error(f"Error searching destinations: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_destination_guide(self, destination: str) -> APIResponse:
        """
        Get a complete travel guide for a destination.
        
        Args:
            destination: Destination name (e.g., "San Francisco")
            
        Returns:
            APIResponse with travel guide data
        """
        try:
            # First, search for the destination
            search_result = self.search_destinations(destination, limit=1)
            if not search_result.success or not search_result.data:
                return APIResponse(success=False, error=f"Destination '{destination}' not found")
            
            page_title = search_result.data[0]['title']
            
            # Get the full article content
            params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts|info|coordinates',
                'titles': page_title,
                'exintro': True,
                'explaintext': True,
                'inprop': 'url'
            }
            
            data = self._make_request(params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch guide data")
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return APIResponse(success=False, error="No page data found")
            
            page_data = list(pages.values())[0]
            
            guide = {
                'title': page_data.get('title', ''),
                'extract': page_data.get('extract', ''),
                'url': page_data.get('fullurl', ''),
                'pageid': page_data.get('pageid'),
                'coordinates': page_data.get('coordinates', [])
            }
            
            return APIResponse(
                success=True,
                data=guide,
                metadata={'destination': destination}
            )
            
        except Exception as e:
            logger.error(f"Error getting destination guide: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_attractions(self, destination: str) -> APIResponse:
        """
        Extract attractions from a destination guide.
        
        Args:
            destination: Destination name
            
        Returns:
            APIResponse with attractions list
        """
        try:
            guide_result = self.get_destination_guide(destination)
            if not guide_result.success:
                return guide_result
            
            guide_text = guide_result.data.get('extract', '')
            
            # Parse attractions from the guide text
            attractions = self._parse_attractions_from_text(guide_text, destination)
            
            return APIResponse(
                success=True,
                data=attractions,
                metadata={'destination': destination, 'total_attractions': len(attractions)}
            )
            
        except Exception as e:
            logger.error(f"Error getting attractions: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_cultural_insights(self, destination: str) -> APIResponse:
        """
        Extract cultural insights from a destination guide.
        
        Args:
            destination: Destination name
            
        Returns:
            APIResponse with cultural insights
        """
        try:
            guide_result = self.get_destination_guide(destination)
            if not guide_result.success:
                return guide_result
            
            guide_text = guide_result.data.get('extract', '')
            
            # Extract cultural information
            cultural_info = self._extract_cultural_info(guide_text)
            
            return APIResponse(
                success=True,
                data=cultural_info,
                metadata={'destination': destination}
            )
            
        except Exception as e:
            logger.error(f"Error getting cultural insights: {e}")
            return APIResponse(success=False, error=str(e))
    
    def get_itineraries(self, destination: str) -> APIResponse:
        """
        Get suggested itineraries for a destination.
        
        Args:
            destination: Destination name
            
        Returns:
            APIResponse with itineraries
        """
        try:
            # Search for itinerary pages
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f"{destination} itinerary",
                'srlimit': 5,
                'srnamespace': 0
            }
            
            data = self._make_request(params)
            if not data:
                return APIResponse(success=False, error="Failed to fetch itineraries")
            
            search_results = data.get('query', {}).get('search', [])
            
            itineraries = []
            for result in search_results:
                if 'itinerary' in result.get('title', '').lower():
                    itineraries.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': f"https://en.wikivoyage.org/wiki/{result.get('title', '').replace(' ', '_')}"
                    })
            
            return APIResponse(
                success=True,
                data=itineraries,
                metadata={'destination': destination, 'total_itineraries': len(itineraries)}
            )
            
        except Exception as e:
            logger.error(f"Error getting itineraries: {e}")
            return APIResponse(success=False, error=str(e))
    
    def _parse_attractions_from_text(self, text: str, destination: str) -> List[Dict]:
        """Parse attractions from guide text."""
        attractions = []
        
        # Simple parsing - look for common attraction indicators
        lines = text.split('.')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in [
                'museum', 'park', 'temple', 'church', 'castle', 'palace',
                'monument', 'statue', 'bridge', 'tower', 'beach', 'mountain',
                'garden', 'zoo', 'aquarium', 'theater', 'theatre', 'gallery'
            ]):
                attractions.append({
                    'name': line[:100] + '...' if len(line) > 100 else line,
                    'type': 'attraction',
                    'description': line
                })
        
        return attractions[:10]  # Limit to 10 attractions
    
    def _extract_cultural_info(self, text: str) -> Dict[str, Any]:
        """Extract cultural information from guide text."""
        cultural_info = {
            'language': [],
            'currency': [],
            'customs': [],
            'cuisine': [],
            'history': []
        }
        
        # Simple keyword-based extraction
        text_lower = text.lower()
        
        if 'language' in text_lower:
            cultural_info['language'].append('Language information available')
        
        if 'currency' in text_lower or '$' in text or '€' in text or '£' in text:
            cultural_info['currency'].append('Currency information available')
        
        if 'custom' in text_lower or 'tradition' in text_lower:
            cultural_info['customs'].append('Cultural customs mentioned')
        
        if 'food' in text_lower or 'cuisine' in text_lower or 'restaurant' in text_lower:
            cultural_info['cuisine'].append('Local cuisine information available')
        
        if 'history' in text_lower or 'historic' in text_lower:
            cultural_info['history'].append('Historical information available')
        
        return cultural_info


# Example usage and testing
if __name__ == "__main__":
    api = WikivoyageAPI()
    
    print("Testing Wikivoyage API...")
    
    # Test destination search
    search_result = api.search_destinations("San Francisco")
    if search_result.success:
        print(f"Found {len(search_result.data)} destinations")
        for dest in search_result.data[:3]:
            print(f"- {dest['title']}")
    
    # Test getting a guide
    guide_result = api.get_destination_guide("San Francisco")
    if guide_result.success:
        print(f"\nGuide for San Francisco:")
        print(f"Title: {guide_result.data['title']}")
        print(f"Extract: {guide_result.data['extract'][:200]}...")
    
    # Test getting attractions
    attractions_result = api.get_attractions("San Francisco")
    if attractions_result.success:
        print(f"\nFound {len(attractions_result.data)} attractions")
        for attraction in attractions_result.data[:3]:
            print(f"- {attraction['name']}")

 