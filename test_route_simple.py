#!/usr/bin/env python3
"""
Simple test to debug route detection and planning.
"""

import os
import sys
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_destination_parsing():
    """Test destination parsing logic."""
    
    # Test cases
    test_cases = [
        ("Redwood National Park", "San Jose"),
        ("San Jose to Redwood National Park", "San Jose"),
        ("Big Sur", "San Jose"),
        ("San Francisco to Yosemite", "San Jose")
    ]
    
    for destination, starting_point in test_cases:
        print(f"\nTesting: '{destination}' with starting_point: '{starting_point}'")
        
        # Test route detection
        route_indicators = [" to ", " → ", " -> ", " via ", " through "]
        is_route = any(indicator in destination.lower() for indicator in route_indicators)
        print(f"  Is route: {is_route}")
        
        if is_route:
            # Parse route
            for indicator in route_indicators:
                if indicator in destination.lower():
                    parts = destination.split(indicator)
                    if len(parts) == 2:
                        origin = parts[0].strip()
                        final_dest = parts[1].strip()
                        route_desc = destination
                        print(f"  Origin: {origin}")
                        print(f"  Destination: {final_dest}")
                        print(f"  Route description: {route_desc}")
                        break
        else:
            # Check if starting_point is different from destination
            if (starting_point.lower() not in destination.lower() and 
                destination.lower() not in starting_point.lower() and
                starting_point != "San Jose"):
                print(f"  Might be route from {starting_point} to {destination}")
                route_desc = f"{starting_point} to {destination}"
                print(f"  Route description: {route_desc}")
            else:
                print(f"  Single destination: {destination}")

def test_planning_agent_route_detection():
    """Test the planning agent's route detection."""
    try:
        from agents.planning_agent import PlanningAgent
        
        # Create a minimal planning agent without LLM
        class MinimalPlanningAgent:
            def _is_route_destination(self, destination: str) -> bool:
                """Check if destination is a route (e.g., 'A to B')."""
                route_indicators = [" to ", " → ", " -> ", " via ", " through "]
                return any(indicator in destination.lower() for indicator in route_indicators)
            
            def _parse_route_destination(self, destination: str) -> dict:
                """Parse route destination into origin and destination."""
                route_indicators = [" to ", " → ", " -> ", " via ", " through "]
                
                for indicator in route_indicators:
                    if indicator in destination.lower():
                        parts = destination.split(indicator)
                        if len(parts) == 2:
                            return {
                                "origin": parts[0].strip(),
                                "destination": parts[1].strip(),
                                "route_description": destination
                            }
                
                # Fallback: assume it's a single destination
                return {
                    "origin": "San Jose",  # Default starting point
                    "destination": destination,
                    "route_description": destination
                }
        
        pa = MinimalPlanningAgent()
        
        test_destinations = [
            "Redwood National Park",
            "San Jose to Redwood National Park",
            "Big Sur",
            "San Francisco to Yosemite"
        ]
        
        for dest in test_destinations:
            print(f"\nTesting planning agent with: '{dest}'")
            is_route = pa._is_route_destination(dest)
            print(f"  Is route: {is_route}")
            
            if is_route:
                route_info = pa._parse_route_destination(dest)
                print(f"  Route info: {route_info}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Destination Parsing Test ===")
    test_destination_parsing()
    
    print("\n=== Planning Agent Route Detection Test ===")
    test_planning_agent_route_detection() 