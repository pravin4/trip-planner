#!/usr/bin/env python3
"""
Interactive Travel Planner
A step-by-step interactive interface for creating travel itineraries.
"""

import os
import sys
from datetime import date, datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SmartTravelPlanner

# Load environment variables
load_dotenv()

class InteractiveTravelPlanner:
    def __init__(self):
        self.planner = SmartTravelPlanner()
        
    def get_destination(self) -> str:
        """Get destination from user."""
        print("\n🌍 DESTINATION")
        print("=" * 40)
        destination = input("Where would you like to travel? (e.g., 'Big Sur, CA', 'Solvang, CA'): ").strip()
        
        if not destination:
            print("❌ Destination is required!")
            return self.get_destination()
            
        return destination
    
    def get_dates(self) -> tuple:
        """Get travel dates from user."""
        print("\n📅 TRAVEL DATES")
        print("=" * 40)
        
        # Get start date
        while True:
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-07-04)")
        
        # Get end date
        while True:
            end_date = input("End date (YYYY-MM-DD): ").strip()
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                if end_datetime <= start_datetime:
                    print("❌ End date must be after start date!")
                    continue
                break
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-07-07)")
        
        return start_date, end_date
    
    def get_budget(self) -> float:
        """Get budget from user."""
        print("\n💰 BUDGET")
        print("=" * 40)
        
        while True:
            try:
                budget = float(input("What's your total budget? $").strip())
                if budget <= 0:
                    print("❌ Budget must be greater than 0!")
                    continue
                return budget
            except ValueError:
                print("❌ Please enter a valid number!")
    
    def get_group_size(self) -> int:
        """Get group size from user."""
        print("\n👥 GROUP SIZE")
        print("=" * 40)
        
        while True:
            try:
                group_size = int(input("How many people are traveling? ").strip())
                if group_size <= 0:
                    print("❌ Group size must be at least 1!")
                    continue
                return group_size
            except ValueError:
                print("❌ Please enter a valid number!")
    
    def get_activity_types(self) -> List[str]:
        """Get activity preferences from user."""
        print("\n🎯 ACTIVITY TYPES")
        print("=" * 40)
        print("Available activity types:")
        activities = [
            "cultural", "outdoor", "adventure", "relaxation", 
            "shopping", "nightlife", "food"
        ]
        
        for i, activity in enumerate(activities, 1):
            print(f"  {i}. {activity.title()}")
        
        print("\nEnter the numbers of activities you're interested in (comma-separated):")
        print("Example: 1,3,5 for Cultural, Adventure, Shopping")
        
        while True:
            try:
                choices = input("Your choices: ").strip()
                if not choices:
                    return ["cultural", "outdoor"]  # Default
                
                selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
                selected_activities = [activities[i] for i in selected_indices if 0 <= i < len(activities)]
                
                if not selected_activities:
                    print("❌ Please select at least one activity type!")
                    continue
                    
                return selected_activities
            except (ValueError, IndexError):
                print("❌ Invalid selection! Please enter numbers separated by commas.")
    
    def get_accommodation_types(self) -> List[str]:
        """Get accommodation preferences from user."""
        print("\n🏨 ACCOMMODATION TYPES")
        print("=" * 40)
        print("Available accommodation types:")
        accommodations = [
            "hotel", "hostel", "camping", "glamping", "cabin", "resort"
        ]
        
        for i, acc in enumerate(accommodations, 1):
            print(f"  {i}. {acc.title()}")
        
        print("\nEnter the numbers of accommodation types you prefer (comma-separated):")
        
        while True:
            try:
                choices = input("Your choices: ").strip()
                if not choices:
                    return ["hotel"]  # Default
                
                selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
                selected_accommodations = [accommodations[i] for i in selected_indices if 0 <= i < len(accommodations)]
                
                if not selected_accommodations:
                    print("❌ Please select at least one accommodation type!")
                    continue
                    
                return selected_accommodations
            except (ValueError, IndexError):
                print("❌ Invalid selection! Please enter numbers separated by commas.")
    
    def get_budget_level(self) -> str:
        """Get budget level from user."""
        print("\n💸 BUDGET LEVEL")
        print("=" * 40)
        print("1. Budget (economical options)")
        print("2. Moderate (balanced options)")
        print("3. Luxury (premium options)")
        
        while True:
            choice = input("Your choice (1-3): ").strip()
            if choice == "1":
                return "budget"
            elif choice == "2":
                return "moderate"
            elif choice == "3":
                return "luxury"
            else:
                print("❌ Please enter 1, 2, or 3!")
    
    def get_children(self) -> bool:
        """Ask if children are included."""
        print("\n👶 CHILDREN")
        print("=" * 40)
        
        while True:
            response = input("Are children included in your trip? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("❌ Please enter 'y' or 'n'!")
    
    def get_dietary_restrictions(self) -> List[str]:
        """Get dietary restrictions from user."""
        print("\n🥗 DIETARY RESTRICTIONS")
        print("=" * 40)
        print("Enter any dietary restrictions (comma-separated) or press Enter for none:")
        print("Examples: vegetarian, vegan, gluten-free, dairy-free, halal, kosher")
        
        restrictions = input("Restrictions: ").strip()
        if not restrictions:
            return []
        
        return [r.strip().lower() for r in restrictions.split(",")]
    
    def get_pdf_output(self) -> str:
        """Ask if user wants PDF output."""
        print("\n📄 PDF OUTPUT")
        print("=" * 40)
        
        while True:
            response = input("Would you like to generate a PDF itinerary? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                filename = input("Enter filename (e.g., 'my_trip.pdf'): ").strip()
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                return f"outputs/{filename}"
            elif response in ['n', 'no']:
                return None
            else:
                print("❌ Please enter 'y' or 'n'!")
    
    def run(self):
        """Run the interactive travel planner."""
        print("🧳 INTERACTIVE TRAVEL PLANNER")
        print("=" * 50)
        print("Let's plan your perfect trip! Answer the questions below.")
        
        try:
            # Collect all user inputs
            destination = self.get_destination()
            start_date, end_date = self.get_dates()
            budget = self.get_budget()
            group_size = self.get_group_size()
            activity_types = self.get_activity_types()
            accommodation_types = self.get_accommodation_types()
            budget_level = self.get_budget_level()
            children = self.get_children()
            dietary_restrictions = self.get_dietary_restrictions()
            pdf_output = self.get_pdf_output()
            
            # Create preferences dictionary
            preferences = {
                "accommodation_types": accommodation_types,
                "activity_types": activity_types,
                "budget_level": budget_level,
                "group_size": group_size,
                "children": children,
                "dietary_restrictions": dietary_restrictions
            }
            
            # Show summary
            print("\n📋 TRIP SUMMARY")
            print("=" * 50)
            print(f"Destination: {destination}")
            print(f"Dates: {start_date} to {end_date}")
            print(f"Budget: ${budget:,.2f}")
            print(f"Group Size: {group_size}")
            print(f"Activities: {', '.join(activity_types)}")
            print(f"Accommodations: {', '.join(accommodation_types)}")
            print(f"Budget Level: {budget_level.title()}")
            print(f"Children: {'Yes' if children else 'No'}")
            if dietary_restrictions:
                print(f"Dietary Restrictions: {', '.join(dietary_restrictions)}")
            
            # Confirm
            confirm = input("\nProceed with planning? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Trip planning cancelled.")
                return
            
            # Create itinerary
            print("\n🔄 Creating your itinerary...")
            itinerary = self.planner.create_itinerary(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                preferences=preferences
            )
            
            # Display results
            print("\n✅ ITINERARY CREATED!")
            print("=" * 50)
            print(f"Destination: {itinerary['destination']}")
            print(f"Duration: {itinerary.get('duration_days', 'N/A')} days")
            print(f"Total Cost: ${itinerary['total_cost']:.2f}")
            print(f"Budget Status: {'✅ Within Budget' if itinerary.get('remaining_budget', 0) >= 0 else '⚠️ Over Budget'}")
            
            # Generate PDF if requested
            if pdf_output:
                os.makedirs("outputs", exist_ok=True)
                print(f"\n📄 Generating PDF...")
                if self.planner.generate_pdf(itinerary, pdf_output):
                    print(f"✅ PDF saved: {pdf_output}")
                else:
                    print("❌ Failed to generate PDF")
            
            # Get travel guide
            print(f"\n🌐 Getting travel guide for {destination}...")
            guide = self.planner.get_wikivoyage_guide(destination)
            if guide["success"]:
                print(f"📖 Travel Guide: {guide['guide']['extract'][:200]}...")
            
            print("\n🎉 Your trip is planned! Enjoy your travels!")
            
        except KeyboardInterrupt:
            print("\n\n❌ Trip planning cancelled by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    planner = InteractiveTravelPlanner()
    planner.run() 