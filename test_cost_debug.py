#!/usr/bin/env python3
"""
Debug script to test cost calculations.
"""

import os
import sys
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cost_calculation():
    """Test the cost calculation with the route planning scenario."""
    try:
        from core.cost_estimator import CostEstimator
        from models.travel_models import BudgetLevel, AccommodationType
        
        cost_estimator = CostEstimator()
        
        # Test parameters for San Jose to Redwood National Park (7 days)
        destination = "Redwood National Park"
        duration = 7
        budget_level = BudgetLevel.MODERATE
        
        print(f"Testing cost calculation for {destination} ({duration} days)")
        print(f"Budget level: {budget_level.value}")
        
        # Test accommodation cost
        accommodation_cost = cost_estimator.estimate_accommodation_cost(
            AccommodationType.HOTEL, budget_level, destination, duration
        )
        print(f"Accommodation cost: ${accommodation_cost:.2f}")
        
        # Test dining cost
        dining_cost = cost_estimator.estimate_dining_costs(
            [], budget_level, destination, duration
        )
        print(f"Dining cost: ${dining_cost:.2f}")
        
        # Test transportation cost
        transportation_cost = cost_estimator.estimate_transportation_costs(
            destination, duration, budget_level
        )
        print(f"Transportation cost: ${transportation_cost:.2f}")
        
        # Test miscellaneous cost
        misc_cost = cost_estimator.estimate_miscellaneous_costs(budget_level, duration)
        print(f"Miscellaneous cost: ${misc_cost:.2f}")
        
        # Test activity cost (with some sample activities)
        from models.travel_models import Activity, Location
        sample_activities = [
            Activity(
                name="Redwood National Park Visit",
                description="Explore the redwood forests",
                location=Location(name="Redwood National Park", address="Redwood National Park, CA"),
                type="outdoor",
                duration_hours=4,
                cost=0
            ),
            Activity(
                name="Monterey Bay Aquarium",
                description="Visit the famous aquarium",
                location=Location(name="Monterey Bay Aquarium", address="Monterey, CA"),
                type="cultural",
                duration_hours=3,
                cost=0
            )
        ]
        
        activity_cost = cost_estimator.estimate_activity_costs(
            sample_activities, budget_level, destination
        )
        print(f"Activity cost: ${activity_cost:.2f}")
        
        # Calculate total
        total_cost = accommodation_cost + dining_cost + transportation_cost + misc_cost + activity_cost
        print(f"\nTotal estimated cost: ${total_cost:.2f}")
        print(f"Daily average: ${total_cost/duration:.2f}")
        
        # Test budget comparison
        test_budgets = [500, 1000, 1500, 2000]
        for budget in test_budgets:
            status = "within_budget" if total_cost <= budget else "over_budget"
            print(f"Budget ${budget}: {status}")
            
    except Exception as e:
        print(f"Error in cost calculation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cost_calculation() 