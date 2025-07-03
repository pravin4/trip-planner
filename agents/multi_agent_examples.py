"""
Multi-Agent System Examples using AutoGen and CrewAI for Travel Planning.

This module demonstrates two different approaches to multi-agent travel planning:
1. AutoGen: Conversational agents that discuss and refine plans together
2. CrewAI: Task-oriented agents with specific roles and sequential execution
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

# AutoGen imports
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("AutoGen not available. Install with: pip install autogen")

# CrewAI imports
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("CrewAI not available. Install with: pip install crewai")

from models.travel_models import TravelPreferences, Itinerary, DayPlan, Activity
from api_integrations.google_places_api import GooglePlacesAPI
from api_integrations.yelp_api import YelpAPI
from api_integrations.expedia_api import ExpediaAPI

logger = logging.getLogger(__name__)

class AutoGenTravelPlanner:
    """
    Travel planner using AutoGen's conversational multi-agent approach.
    
    AutoGen is great for:
    - Brainstorming travel ideas
    - Collaborative planning with human input
    - Iterative refinement of plans
    - Multi-perspective discussions
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize AutoGen travel planner with agents."""
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen is not installed")
        
        # Configure LLM
        config_list = [
            {
                "model": "gpt-4",
                "api_key": openai_api_key,
            }
        ]
        
        # Create specialized agents
        self.researcher = AssistantAgent(
            name="Travel_Researcher",
            system_message="""You are a travel research expert. Your role is to:
            - Research destinations, attractions, and activities
            - Provide detailed information about locations
            - Suggest hidden gems and local experiences
            - Consider weather, seasons, and local events
            Always provide specific, actionable recommendations.""",
            llm_config={"config_list": config_list}
        )
        
        self.planner = AssistantAgent(
            name="Itinerary_Planner",
            system_message="""You are an expert travel planner. Your role is to:
            - Create detailed day-by-day itineraries
            - Optimize schedules for efficiency and enjoyment
            - Balance activities with rest time
            - Consider travel times between locations
            - Ensure realistic timing for each activity
            Always create practical, enjoyable schedules.""",
            llm_config={"config_list": config_list}
        )
        
        self.budget_expert = AssistantAgent(
            name="Budget_Expert",
            system_message="""You are a travel budget specialist. Your role is to:
            - Estimate costs for accommodations, activities, and dining
            - Suggest budget-friendly alternatives
            - Optimize spending across different categories
            - Provide cost-saving tips and strategies
            - Ensure plans stay within budget constraints
            Always provide realistic cost estimates and savings opportunities.""",
            llm_config={"config_list": config_list}
        )
        
        self.critic = AssistantAgent(
            name="Travel_Critic",
            system_message="""You are a travel critic and validator. Your role is to:
            - Review and critique travel plans
            - Identify potential issues or improvements
            - Ensure plans are realistic and enjoyable
            - Suggest alternatives for better experiences
            - Validate that plans meet traveler preferences
            Always provide constructive feedback and suggestions.""",
            llm_config={"config_list": config_list}
        )
        
        # Create group chat
        self.group_chat = GroupChat(
            agents=[self.researcher, self.planner, self.budget_expert, self.critic],
            messages=[],
            max_round=50
        )
        
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={"config_list": config_list}
        )
        
        # User proxy for human interaction
        self.user_proxy = UserProxyAgent(
            name="Traveler",
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"work_dir": "travel_planning"},
            llm_config={"config_list": config_list}
        )
    
    def plan_trip(self, preferences: TravelPreferences) -> Dict[str, Any]:
        """
        Plan a trip using AutoGen's conversational approach.
        
        Args:
            preferences: Travel preferences and constraints
            
        Returns:
            Dictionary containing the planning conversation and final plan
        """
        # Create initial planning prompt
        prompt = f"""
        Let's plan an amazing trip! Here are the details:
        
        Destination: {preferences.destination}
        Dates: {preferences.start_date} to {preferences.end_date}
        Budget: ${preferences.budget}
        Travelers: {preferences.num_travelers}
        Interests: {', '.join(preferences.interests)}
        Accommodation Type: {preferences.accommodation_type}
        
        Please work together to create a comprehensive travel plan:
        
        1. Travel_Researcher: Research the destination and suggest activities
        2. Itinerary_Planner: Create a detailed day-by-day schedule
        3. Budget_Expert: Estimate costs and suggest budget optimizations
        4. Travel_Critic: Review the plan and suggest improvements
        
        Each agent should contribute their expertise and collaborate to create the best possible plan.
        Consider the traveler's preferences, budget constraints, and practical logistics.
        
        Start by having the Travel_Researcher begin with destination research.
        """
        
        # Initiate the group conversation
        self.user_proxy.initiate_chat(
            self.manager,
            message=prompt
        )
        
        # Return the conversation history and any generated plans
        return {
            "conversation": self.group_chat.messages,
            "preferences": preferences.dict()
        }


class CrewAITravelPlanner:
    """
    Travel planner using CrewAI's task-oriented multi-agent approach.
    
    CrewAI is great for:
    - Structured, sequential planning workflows
    - Clear role separation and task delegation
    - Automated execution without human intervention
    - Complex multi-step processes
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize CrewAI travel planner with agents and tools."""
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI is not installed")
        
        # Initialize API clients
        self.google_places = GooglePlacesAPI()
        self.yelp = YelpAPI()
        self.expedia = ExpediaAPI()
        
        # Create specialized agents with tools
        self.research_agent = Agent(
            role="Travel Research Specialist",
            goal="Research destinations, attractions, and activities to provide comprehensive travel information",
            backstory="""You are an expert travel researcher with years of experience 
            discovering amazing destinations and experiences. You have deep knowledge 
            of local cultures, hidden gems, and practical travel information.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                DestinationResearchTool(self.google_places),
                ActivitySearchTool(self.google_places),
                RestaurantSearchTool(self.yelp)
            ]
        )
        
        self.planning_agent = Agent(
            role="Itinerary Planning Expert",
            goal="Create detailed, optimized day-by-day travel itineraries",
            backstory="""You are a master travel planner who excels at creating 
            perfect itineraries. You understand how to balance activities, rest time, 
            and logistics to create enjoyable travel experiences.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                AccommodationSearchTool(self.expedia),
                FlightSearchTool(self.expedia),
                CostEstimationTool()
            ]
        )
        
        self.budget_agent = Agent(
            role="Budget Optimization Specialist",
            goal="Optimize travel plans to maximize value within budget constraints",
            backstory="""You are a financial expert specializing in travel budgets. 
            You know how to stretch travel dollars and find the best value for money 
            while maintaining quality experiences.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                BudgetAnalysisTool(),
                CostOptimizationTool()
            ]
        )
        
        self.validation_agent = Agent(
            role="Travel Plan Validator",
            goal="Review and validate travel plans for feasibility and quality",
            backstory="""You are a seasoned traveler and critic who can spot issues 
            in travel plans and suggest improvements. You ensure plans are realistic, 
            enjoyable, and meet traveler expectations.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                PlanValidationTool(),
                AlternativeSuggestionTool()
            ]
        )
    
    def plan_trip(self, preferences: TravelPreferences) -> Dict[str, Any]:
        """
        Plan a trip using CrewAI's task-oriented approach.
        
        Args:
            preferences: Travel preferences and constraints
            
        Returns:
            Dictionary containing the planning results and final itinerary
        """
        # Create tasks for each agent
        research_task = Task(
            description=f"""
            Research the destination {preferences.destination} and provide comprehensive information:
            
            1. Top attractions and must-see places
            2. Local activities and experiences
            3. Restaurant recommendations
            4. Weather and best times to visit
            5. Cultural highlights and events
            6. Practical travel information (transportation, safety, etc.)
            
            Consider the traveler's interests: {', '.join(preferences.interests)}
            Focus on experiences that match their preferences.
            """,
            agent=self.research_agent,
            expected_output="Detailed destination research report with attractions, activities, and recommendations"
        )
        
        planning_task = Task(
            description=f"""
            Create a detailed day-by-day itinerary for the trip:
            
            Destination: {preferences.destination}
            Dates: {preferences.start_date} to {preferences.end_date}
            Travelers: {preferences.num_travelers}
            Accommodation Type: {preferences.accommodation_type}
            
            Use the research from the previous task to create:
            1. Daily schedules with specific activities
            2. Accommodation recommendations
            3. Transportation plans
            4. Meal planning and restaurant bookings
            5. Realistic timing and logistics
            
            Ensure the plan is practical and enjoyable.
            """,
            agent=self.planning_agent,
            expected_output="Complete day-by-day itinerary with accommodations, activities, and logistics",
            context=[research_task]
        )
        
        budget_task = Task(
            description=f"""
            Analyze and optimize the travel plan for budget:
            
            Total Budget: ${preferences.budget}
            
            Review the itinerary and:
            1. Estimate total costs for all components
            2. Identify cost-saving opportunities
            3. Suggest budget-friendly alternatives
            4. Optimize spending across categories
            5. Ensure the plan stays within budget
            
            Provide specific cost estimates and savings recommendations.
            """,
            agent=self.budget_agent,
            expected_output="Budget analysis with cost estimates and optimization recommendations",
            context=[planning_task]
        )
        
        validation_task = Task(
            description=f"""
            Review and validate the complete travel plan:
            
            Evaluate the itinerary for:
            1. Feasibility and realism
            2. Enjoyment and experience quality
            3. Logistical soundness
            4. Budget compliance
            5. Alignment with traveler preferences
            
            Identify any issues and suggest improvements.
            Provide final recommendations and alternatives if needed.
            """,
            agent=self.validation_agent,
            expected_output="Validation report with feedback and final recommendations",
            context=[budget_task]
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[self.research_agent, self.planning_agent, self.budget_agent, self.validation_agent],
            tasks=[research_task, planning_task, budget_task, validation_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Execute the planning process
        result = crew.kickoff()
        
        return {
            "planning_result": result,
            "preferences": preferences.dict(),
            "tasks_completed": [task.description for task in [research_task, planning_task, budget_task, validation_task]]
        }


# Tool classes for CrewAI agents
class DestinationResearchTool(BaseTool):
    """Tool for researching destinations using Google Places API."""
    
    def __init__(self, google_places_api: GooglePlacesAPI):
        super().__init__()
        self.google_places = google_places_api
    
    def run(self, destination: str) -> str:
        """Research a destination and return comprehensive information."""
        try:
            # Search for places of interest
            places = self.google_places.search_places(destination, "tourist_attraction")
            restaurants = self.google_places.search_places(destination, "restaurant")
            
            result = f"Destination Research for {destination}:\n\n"
            result += "Top Attractions:\n"
            for place in places[:5]:
                result += f"- {place['name']}: {place.get('rating', 'N/A')} stars\n"
            
            result += "\nRestaurant Recommendations:\n"
            for restaurant in restaurants[:5]:
                result += f"- {restaurant['name']}: {restaurant.get('rating', 'N/A')} stars\n"
            
            return result
        except Exception as e:
            return f"Error researching destination: {str(e)}"


class ActivitySearchTool(BaseTool):
    """Tool for searching activities using Google Places API."""
    
    def __init__(self, google_places_api: GooglePlacesAPI):
        super().__init__()
        self.google_places = google_places_api
    
    def run(self, location: str, activity_type: str = "tourist_attraction") -> str:
        """Search for activities in a location."""
        try:
            activities = self.google_places.search_places(location, activity_type)
            
            result = f"Activities in {location}:\n\n"
            for activity in activities[:10]:
                result += f"- {activity['name']}: {activity.get('rating', 'N/A')} stars\n"
                if 'vicinity' in activity:
                    result += f"  Location: {activity['vicinity']}\n"
            
            return result
        except Exception as e:
            return f"Error searching activities: {str(e)}"


class RestaurantSearchTool(BaseTool):
    """Tool for searching restaurants using Yelp API."""
    
    def __init__(self, yelp_api: YelpAPI):
        super().__init__()
        self.yelp = yelp_api
    
    def run(self, location: str, cuisine: str = None) -> str:
        """Search for restaurants in a location."""
        try:
            restaurants = self.yelp.search_restaurants(location, cuisine=cuisine)
            
            result = f"Restaurants in {location}:\n\n"
            for restaurant in restaurants[:10]:
                result += f"- {restaurant.name}: {restaurant.rating} stars\n"
                result += f"  Price: {restaurant.price_range}\n"
                result += f"  Categories: {', '.join(restaurant.categories)}\n"
            
            return result
        except Exception as e:
            return f"Error searching restaurants: {str(e)}"


class AccommodationSearchTool(BaseTool):
    """Tool for searching accommodations using Expedia API."""
    
    def __init__(self, expedia_api: ExpediaAPI):
        super().__init__()
        self.expedia = expedia_api
    
    def run(self, location: str, check_in: str, check_out: str, guests: int = 2) -> str:
        """Search for accommodations in a location."""
        try:
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            
            hotels = self.expedia.search_hotels(location, check_in_date, check_out_date, guests)
            
            result = f"Accommodations in {location}:\n\n"
            for hotel in hotels[:5]:
                result += f"- {hotel.name}: ${hotel.price_per_night}/night\n"
                result += f"  Rating: {hotel.rating} stars\n"
                result += f"  Amenities: {', '.join(hotel.amenities[:3])}\n"
            
            return result
        except Exception as e:
            return f"Error searching accommodations: {str(e)}"


class FlightSearchTool(BaseTool):
    """Tool for searching flights using Expedia API."""
    
    def __init__(self, expedia_api: ExpediaAPI):
        super().__init__()
        self.expedia = expedia_api
    
    def run(self, origin: str, destination: str, departure_date: str, passengers: int = 1) -> str:
        """Search for flights between locations."""
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
            
            flights = self.expedia.search_flights(origin, destination, dep_date, passengers=passengers)
            
            result = f"Flights from {origin} to {destination}:\n\n"
            for flight in flights[:5]:
                result += f"- {flight.airline} {flight.flight_number}\n"
                result += f"  Departure: {flight.departure_time.strftime('%H:%M')}\n"
                result += f"  Arrival: {flight.arrival_time.strftime('%H:%M')}\n"
                result += f"  Price: ${flight.price}\n"
            
            return result
        except Exception as e:
            return f"Error searching flights: {str(e)}"


class CostEstimationTool(BaseTool):
    """Tool for estimating travel costs."""
    
    def run(self, itinerary_description: str, budget: float) -> str:
        """Estimate costs for a travel itinerary."""
        # This is a simplified estimation - in practice, you'd use more sophisticated logic
        estimated_costs = {
            "accommodation": budget * 0.4,
            "activities": budget * 0.3,
            "dining": budget * 0.2,
            "transportation": budget * 0.1
        }
        
        result = "Cost Estimation:\n\n"
        for category, cost in estimated_costs.items():
            result += f"{category.title()}: ${cost:.2f}\n"
        
        result += f"\nTotal Estimated: ${sum(estimated_costs.values()):.2f}\n"
        result += f"Budget: ${budget:.2f}\n"
        result += f"Remaining: ${budget - sum(estimated_costs.values()):.2f}\n"
        
        return result


class BudgetAnalysisTool(BaseTool):
    """Tool for analyzing and optimizing travel budgets."""
    
    def run(self, cost_breakdown: str, preferences: str) -> str:
        """Analyze budget and suggest optimizations."""
        result = "Budget Analysis:\n\n"
        result += "Based on the cost breakdown and preferences:\n"
        result += "1. Consider staying in budget accommodations to save 20-30%\n"
        result += "2. Look for free activities and attractions\n"
        result += "3. Use public transportation instead of taxis\n"
        result += "4. Eat at local restaurants instead of tourist spots\n"
        result += "5. Book activities in advance for better rates\n\n"
        result += "These changes could save 25-40% of your total budget."
        
        return result


class CostOptimizationTool(BaseTool):
    """Tool for suggesting cost-saving alternatives."""
    
    def run(self, current_plan: str, budget_constraint: float) -> str:
        """Suggest cost-saving alternatives for the travel plan."""
        result = "Cost Optimization Suggestions:\n\n"
        result += "1. Accommodation: Consider hostels, vacation rentals, or budget hotels\n"
        result += "2. Transportation: Use public transit, walking, or bike rentals\n"
        result += "3. Activities: Look for free walking tours, museum free days\n"
        result += "4. Dining: Eat breakfast at accommodation, pack lunches\n"
        result += "5. Shopping: Buy souvenirs at local markets instead of tourist shops\n"
        result += "6. Timing: Travel during shoulder season for better rates\n"
        
        return result


class PlanValidationTool(BaseTool):
    """Tool for validating travel plans."""
    
    def run(self, itinerary: str, preferences: str) -> str:
        """Validate a travel plan for feasibility and quality."""
        result = "Plan Validation:\n\n"
        result += "✅ Plan appears realistic and well-structured\n"
        result += "✅ Activities align with traveler interests\n"
        result += "✅ Adequate time allocated for each activity\n"
        result += "✅ Rest time included between activities\n"
        result += "✅ Transportation logistics considered\n"
        result += "✅ Budget constraints respected\n\n"
        result += "Overall Assessment: This is a solid travel plan that should provide an enjoyable experience."
        
        return result


class AlternativeSuggestionTool(BaseTool):
    """Tool for suggesting alternative options."""
    
    def run(self, current_plan: str, preferences: str) -> str:
        """Suggest alternative options for the travel plan."""
        result = "Alternative Suggestions:\n\n"
        result += "1. Consider adding a local cooking class for cultural immersion\n"
        result += "2. Include a day trip to nearby attractions\n"
        result += "3. Add a sunset viewing spot for memorable photos\n"
        result += "4. Consider a guided tour for historical context\n"
        result += "5. Include a local market visit for authentic experience\n"
        result += "6. Add a relaxation day with spa or wellness activities\n"
        
        return result


def compare_approaches():
    """Compare AutoGen vs CrewAI approaches for travel planning."""
    
    comparison = """
    AutoGen vs CrewAI for Travel Planning:
    
    AUTOGEN APPROACH:
    ✅ Pros:
    - Interactive and conversational
    - Human-in-the-loop capabilities
    - Great for brainstorming and refinement
    - Flexible discussion format
    - Good for complex decision-making
    
    ❌ Cons:
    - Less structured workflow
    - Can be verbose and time-consuming
    - Harder to automate completely
    - May not always reach consensus
    
    CREWAI APPROACH:
    ✅ Pros:
    - Structured, sequential workflow
    - Clear role separation
    - Automated execution
    - Predictable output format
    - Good for complex multi-step processes
    
    ❌ Cons:
    - Less interactive
    - Limited human intervention
    - More rigid workflow
    - May miss creative solutions
    
    RECOMMENDATION:
    - Use AutoGen for initial planning and brainstorming
    - Use CrewAI for detailed execution and optimization
    - Combine both for comprehensive travel planning
    """
    
    return comparison


if __name__ == "__main__":
    # Example usage
    print("Multi-Agent Travel Planning Examples")
    print("=" * 50)
    
    # Show comparison
    print(compare_approaches())
    
    # Example preferences
    preferences = TravelPreferences(
        destination="San Francisco",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=37),
        budget=3000.0,
        num_travelers=2,
        interests=["food", "culture", "outdoors"],
        accommodation_type="hotel"
    )
    
    print(f"\nExample planning for: {preferences.destination}")
    print(f"Budget: ${preferences.budget}")
    print(f"Interests: {', '.join(preferences.interests)}") 