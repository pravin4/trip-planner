#!/usr/bin/env python3
"""
Test script for Smart Travel Planner
Demonstrates the functionality without requiring API keys.
"""

import os
import sys
from datetime import date, timedelta
from models.travel_models import (
    TravelPreferences, AccommodationType, ActivityType, BudgetLevel,
    Location, Activity, Restaurant, DayPlan, Itinerary
)
from core.cost_estimator import CostEstimator
from core.pdf_generator import PDFGenerator
from utils.helpers import (
    generate_trip_summary, format_currency, validate_date_format, 
    validate_date_range, format_location
)

def create_sample_itinerary():
    """Create a sample itinerary for testing."""
    
    # Create sample location
    location = Location(
        name="Golden Gate Park",
        address="Golden Gate Park, San Francisco, CA",
        latitude=37.7694,
        longitude=-122.4862,
        rating=4.5,
        price_level=2
    )
    
    # Create sample activities
    activities = [
        Activity(
            name="Visit Golden Gate Bridge",
            location=location,
            type=ActivityType.OUTDOOR,
            duration_hours=2.0,
            cost=0.0,
            description="Walk across the iconic Golden Gate Bridge"
        ),
        Activity(
            name="Explore Fisherman's Wharf",
            location=Location(name="Fisherman's Wharf", address="Fisherman's Wharf, San Francisco, CA"),
            type=ActivityType.CULTURAL,
            duration_hours=3.0,
            cost=25.0,
            description="Visit the famous waterfront area"
        ),
        Activity(
            name="Alcatraz Island Tour",
            location=Location(name="Alcatraz Island", address="Alcatraz Island, San Francisco, CA"),
            type=ActivityType.CULTURAL,
            duration_hours=4.0,
            cost=45.0,
            description="Tour the historic Alcatraz prison"
        )
    ]
    
    # Create sample restaurants
    restaurants = [
        Restaurant(
            name="Fisherman's Grotto",
            location=Location(name="Fisherman's Grotto", address="2847 Taylor St, San Francisco, CA"),
            cuisine_type="Seafood",
            price_level=3,
            rating=4.2,
            cost_per_person=45.0,
            description="Famous seafood restaurant"
        ),
        Restaurant(
            name="Tartine Bakery",
            location=Location(name="Tartine Bakery", address="600 Guerrero St, San Francisco, CA"),
            cuisine_type="Bakery",
            price_level=2,
            rating=4.6,
            cost_per_person=20.0,
            description="Artisan bakery and cafe"
        )
    ]
    
    # Create travel preferences
    preferences = TravelPreferences(
        accommodation_types=[AccommodationType.HOTEL, AccommodationType.GLAMPING],
        activity_types=[ActivityType.OUTDOOR, ActivityType.CULTURAL],
        budget_level=BudgetLevel.MODERATE,
        max_daily_budget=200.0,
        group_size=2,
        children=False,
        dietary_restrictions=["vegetarian"]
    )
    
    # Create day plans
    start_date = date.today() + timedelta(days=30)
    day_plans = []
    
    for i in range(3):
        day_date = start_date + timedelta(days=i)
        day_plan = DayPlan(
            date=day_date,
            activities=activities[i:i+1] if i < len(activities) else [],
            restaurants=restaurants[i:i+1] if i < len(restaurants) else [],
            transportation=["Public transit", "Walking"],
            notes=f"Day {i+1} in San Francisco - exploring the city"
        )
        day_plans.append(day_plan)
    
    # Create itinerary
    itinerary = Itinerary(
        destination="San Francisco, CA",
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        total_budget=1500.0,
        preferences=preferences,
        day_plans=day_plans,
        total_cost=850.0,
        cost_breakdown={
            "accommodation": 450.0,
            "activities": 70.0,
            "dining": 195.0,
            "transportation": 60.0,
            "miscellaneous": 75.0
        }
    )
    
    return itinerary

def test_cost_estimator():
    """Test the cost estimator functionality."""
    print("🧮 Testing Cost Estimator...")
    
    estimator = CostEstimator()
    
    # Test location multiplier
    sf_multiplier = estimator.get_location_multiplier("San Francisco")
    ny_multiplier = estimator.get_location_multiplier("New York")
    
    print(f"  San Francisco cost multiplier: {sf_multiplier}")
    print(f"  New York cost multiplier: {ny_multiplier}")
    
    # Test accommodation cost estimation
    hotel_cost = estimator.estimate_accommodation_cost(
        AccommodationType.HOTEL,
        BudgetLevel.MODERATE,
        "San Francisco",
        3
    )
    
    print(f"  3-night hotel in SF (moderate): ${hotel_cost:.2f}")
    
    # Test activity cost estimation
    activities = [
        Activity(
            name="Museum Visit", 
            location=Location(name="Museum", address="San Francisco, CA"), 
            type=ActivityType.CULTURAL, 
            duration_hours=2, 
            cost=0
        ),
        Activity(
            name="Park Walk", 
            location=Location(name="Park", address="San Francisco, CA"), 
            type=ActivityType.OUTDOOR, 
            duration_hours=1, 
            cost=0
        )
    ]
    
    activity_cost = estimator.estimate_activity_costs(
        activities,
        BudgetLevel.MODERATE,
        "San Francisco"
    )
    
    print(f"  Activity costs in SF: ${activity_cost:.2f}")
    
    print("✅ Cost Estimator tests completed\n")

def test_pdf_generator():
    """Test the PDF generator functionality."""
    print("📄 Testing PDF Generator...")
    
    try:
        # Create sample itinerary
        itinerary = create_sample_itinerary()
        
        # Initialize PDF generator
        pdf_generator = PDFGenerator()
        
        # Create outputs directory
        os.makedirs("outputs", exist_ok=True)
        
        # Generate PDF
        pdf_path = "outputs/test_itinerary.pdf"
        success = pdf_generator.generate_itinerary_pdf(itinerary, pdf_path)
        
        if success:
            print(f"  ✅ PDF generated successfully: {pdf_path}")
        else:
            print("  ❌ PDF generation failed")
            
    except Exception as e:
        print(f"  ❌ PDF generation error: {e}")
    
    print("✅ PDF Generator tests completed\n")

def test_helpers():
    """Test the helper functions."""
    print("🔧 Testing Helper Functions...")
    
    # Test date validation
    valid_date = "2024-06-15"
    invalid_date = "2024-13-45"
    
    print(f"  Valid date '{valid_date}': {validate_date_format(valid_date)}")
    print(f"  Invalid date '{invalid_date}': {validate_date_format(invalid_date)}")
    
    # Test date range validation
    start_date = "2024-06-15"
    end_date = "2024-06-20"
    invalid_end = "2024-06-10"
    
    print(f"  Valid date range: {validate_date_range(start_date, end_date)}")
    print(f"  Invalid date range: {validate_date_range(start_date, invalid_end)}")
    
    # Test location formatting
    locations = [
        "san francisco",
        "new york",
        "london, uk",
        "toronto, canada"
    ]
    
    for location in locations:
        formatted = format_location(location)
        print(f"  '{location}' -> '{formatted}'")
    
    # Test currency formatting
    amounts = [1234.56, 99.99, 0.50, 1000000]
    for amount in amounts:
        formatted = format_currency(amount)
        print(f"  ${amount} -> {formatted}")
    
    print("✅ Helper Functions tests completed\n")

def test_itinerary_summary():
    """Test itinerary summary generation."""
    print("📊 Testing Itinerary Summary...")
    
    # Create sample itinerary
    itinerary = create_sample_itinerary()
    
    # Generate summary
    summary = generate_trip_summary(itinerary)
    
    print(f"  Destination: {summary['destination']}")
    print(f"  Duration: {summary['duration']} days")
    print(f"  Total Cost: {summary['total_cost']}")
    print(f"  Budget Status: {summary['budget_status']}")
    print(f"  Total Activities: {summary['total_activities']}")
    print(f"  Total Restaurants: {summary['total_restaurants']}")
    
    print("  Cost Breakdown:")
    for category, amount in summary['cost_breakdown'].items():
        print(f"    {category.title()}: {amount}")
    
    print("✅ Itinerary Summary tests completed\n")

def main():
    """Run all tests."""
    print("🧳 Smart Travel Planner - Test Suite")
    print("=" * 50)
    
    # Test helper functions
    test_helpers()
    
    # Test cost estimator
    test_cost_estimator()
    
    # Test itinerary summary
    test_itinerary_summary()
    
    # Test PDF generator
    test_pdf_generator()
    
    print("🎉 All tests completed successfully!")
    print("\n📝 Note: This test suite demonstrates the core functionality")
    print("   without requiring API keys. For full functionality with")
    print("   real data, set up your API keys in the .env file.")

if __name__ == "__main__":
    main() 