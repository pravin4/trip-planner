#!/usr/bin/env python3
"""
Specific test to debug route detection with web form values.
"""

def test_route_detection_with_web_values():
    """Test route detection with the exact values from the web form."""
    
    # These are the exact values from the web form
    starting_point = "San Jose, CA"  # From the form
    destination = "Redwood National Park"  # From the form
    
    print(f"Testing with web form values:")
    print(f"  Starting point: '{starting_point}'")
    print(f"  Destination: '{destination}'")
    
    # Test the exact logic from main.py
    starting_point_lower = starting_point.lower()
    destination_lower = destination.lower()
    
    print(f"\nLogic test:")
    print(f"  starting_point.lower() = '{starting_point_lower}'")
    print(f"  destination.lower() = '{destination_lower}'")
    print(f"  starting_point.lower() not in destination.lower() = {starting_point_lower not in destination_lower}")
    print(f"  destination.lower() not in starting_point.lower() = {destination_lower not in starting_point_lower}")
    print(f"  starting_point.lower() != destination.lower() = {starting_point_lower != destination_lower}")
    
    # Test the first condition
    condition1 = (starting_point_lower not in destination_lower and 
                  destination_lower not in starting_point_lower and
                  starting_point_lower != destination_lower)
    print(f"\nCondition 1: {condition1}")
    
    # Test the second condition
    starting_point_words = starting_point_lower.split()
    destination_words = destination_lower.split()
    print(f"  starting_point words: {starting_point_words}")
    print(f"  destination words: {destination_words}")
    
    starting_point_in_dest = any(city in destination_lower for city in starting_point_words)
    dest_in_starting_point = any(city in starting_point_lower for city in destination_words)
    
    print(f"  Any starting_point word in destination: {starting_point_in_dest}")
    print(f"  Any destination word in starting_point: {dest_in_starting_point}")
    
    condition2 = (starting_point_lower != destination_lower and
                  not starting_point_in_dest and
                  not dest_in_starting_point)
    print(f"Condition 2: {condition2}")
    
    # Final result
    is_route = condition1 or condition2
    print(f"\nFinal result - Is route: {is_route}")
    
    if is_route:
        route_description = f"{starting_point} to {destination}"
        print(f"Route description: {route_description}")

if __name__ == "__main__":
    test_route_detection_with_web_values() 