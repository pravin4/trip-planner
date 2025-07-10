#!/usr/bin/env python3
"""
Test Route Detection
Tests the improved route detection functionality.
"""

from main import SmartTravelPlanner

def test_route_detection():
    """Test route detection with various inputs."""
    
    print("🧳 TESTING ROUTE DETECTION")
    print("=" * 50)
    
    planner = SmartTravelPlanner()
    
    # Test cases
    test_cases = [
        {
            "destination": "San Jose to Big Sur",
            "starting_point": "San Jose",
            "expected_type": "route"
        },
        {
            "destination": "San Jose, CA to Shelter Cove",
            "starting_point": "San Jose",
            "expected_type": "route"
        },
        {
            "destination": "Shelter Cove",
            "starting_point": "San Jose, CA",
            "expected_type": "route"
        },
        {
            "destination": "Big Sur",
            "starting_point": "San Jose",
            "expected_type": "route"
        },
        {
            "destination": "San Francisco, CA",
            "starting_point": "San Jose",
            "expected_type": "route"
        },
        {
            "destination": "New York",
            "starting_point": "San Jose",
            "expected_type": "route"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['destination']} (from {test_case['starting_point']})")
        
        try:
            result = planner._parse_and_validate_destination(
                test_case['destination'], 
                test_case['starting_point']
            )
            
            print(f"   Result Type: {result['type']}")
            print(f"   Expected: {test_case['expected_type']}")
            
            if result['type'] == 'route':
                print(f"   Start: {result['start']}")
                print(f"   End: {result['end']}")
                print(f"   Route: {result['route_description']}")
            
            if result['type'] == test_case['expected_type']:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n🎉 Route Detection Test Complete!")

if __name__ == "__main__":
    test_route_detection() 