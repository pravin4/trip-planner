import os
from typing import Dict, List, Optional, Tuple, Any
from models.travel_models import (
    Accommodation, Activity, Restaurant, TravelPreferences, 
    BudgetLevel, AccommodationType, CostBreakdown
)
import logging

logger = logging.getLogger(__name__)


class CostEstimator:
    def __init__(self):
        self.currency = os.getenv("CURRENCY", "USD")
        
        # Base cost estimates by location type and budget level
        self.accommodation_costs = {
            BudgetLevel.BUDGET: {
                AccommodationType.HOTEL: 80,
                AccommodationType.HOSTEL: 30,
                AccommodationType.CAMPING: 20,
                AccommodationType.GLAMPING: 60,
                AccommodationType.CABIN: 70,
                AccommodationType.RESORT: 120
            },
            BudgetLevel.MODERATE: {
                AccommodationType.HOTEL: 150,
                AccommodationType.HOSTEL: 50,
                AccommodationType.CAMPING: 35,
                AccommodationType.GLAMPING: 100,
                AccommodationType.CABIN: 120,
                AccommodationType.RESORT: 250
            },
            BudgetLevel.LUXURY: {
                AccommodationType.HOTEL: 300,
                AccommodationType.HOSTEL: 80,
                AccommodationType.CAMPING: 60,
                AccommodationType.GLAMPING: 200,
                AccommodationType.CABIN: 250,
                AccommodationType.RESORT: 500
            }
        }
        
        # Activity cost estimates
        self.activity_costs = {
            "museum": {"budget": 10, "moderate": 20, "luxury": 40},
            "park": {"budget": 0, "moderate": 5, "luxury": 15},
            "tour": {"budget": 25, "moderate": 50, "luxury": 100},
            "adventure": {"budget": 40, "moderate": 80, "luxury": 150},
            "spa": {"budget": 50, "moderate": 100, "luxury": 200},
            "shopping": {"budget": 20, "moderate": 50, "luxury": 100},
            "nightlife": {"budget": 30, "moderate": 60, "luxury": 120},
            "entertainment": {"budget": 25, "moderate": 50, "luxury": 100},
            "cultural": {"budget": 15, "moderate": 30, "luxury": 60},
            "outdoor": {"budget": 10, "moderate": 20, "luxury": 40},
            "relaxation": {"budget": 20, "moderate": 40, "luxury": 80},
            "food": {"budget": 15, "moderate": 30, "luxury": 60}
        }
        
        # Dining cost estimates per person per meal
        self.dining_costs = {
            BudgetLevel.BUDGET: {"breakfast": 8, "lunch": 12, "dinner": 18},
            BudgetLevel.MODERATE: {"breakfast": 15, "lunch": 25, "dinner": 40},
            BudgetLevel.LUXURY: {"breakfast": 30, "lunch": 50, "dinner": 80}
        }
        
        # Transportation cost estimates
        self.transportation_costs = {
            "public_transit": {"budget": 5, "moderate": 8, "luxury": 15},
            "taxi": {"budget": 20, "moderate": 35, "luxury": 60},
            "rental_car": {"budget": 40, "moderate": 60, "luxury": 100},
            "walking": {"budget": 0, "moderate": 0, "luxury": 0}
        }
        
        # Location cost multipliers (higher for expensive cities)
        self.location_multipliers = {
            "new york": 1.8,
            "san francisco": 1.6,
            "los angeles": 1.5,
            "chicago": 1.3,
            "miami": 1.4,
            "las vegas": 1.2,
            "seattle": 1.4,
            "boston": 1.5,
            "washington dc": 1.4,
            "denver": 1.2,
            "austin": 1.1,
            "nashville": 1.0,
            "portland": 1.2,
            "atlanta": 1.1,
            "phoenix": 0.9,
            "dallas": 1.0,
            "houston": 0.9,
            "orlando": 1.0,
            "san diego": 1.3,
            "philadelphia": 1.2
        }
    
    def get_location_multiplier(self, location: str) -> float:
        """Get cost multiplier for a specific location"""
        location_lower = location.lower()
        for city, multiplier in self.location_multipliers.items():
            if city in location_lower:
                return multiplier
        return 1.0  # Default multiplier
    
    def estimate_accommodation_cost(self, accommodation_type: AccommodationType, 
                                  budget_level: BudgetLevel, location: str, 
                                  nights: int) -> float:
        """Estimate accommodation cost for the trip"""
        base_cost = self.accommodation_costs[budget_level][accommodation_type]
        location_multiplier = self.get_location_multiplier(location)
        
        # Apply seasonal adjustments (simplified)
        seasonal_multiplier = 1.0  # Could be enhanced with actual seasonal data
        
        total_cost = base_cost * location_multiplier * seasonal_multiplier * nights
        
        # Apply group size discount for longer stays
        if nights >= 7:
            total_cost *= 0.9  # 10% discount for week+ stays
        
        return round(total_cost, 2)
    
    def estimate_activity_costs(self, activities: List[Activity], 
                              budget_level: BudgetLevel, location: str) -> float:
        """Estimate total activity costs"""
        location_multiplier = self.get_location_multiplier(location)
        total_cost = 0.0
        
        for activity in activities:
            # Use activity cost if available, otherwise estimate
            if activity.cost > 0:
                total_cost += activity.cost
            else:
                # Estimate based on activity type
                activity_type = activity.type.value
                base_cost = self.activity_costs.get(activity_type, {}).get(
                    budget_level.value, 25
                )
                total_cost += base_cost * location_multiplier
        
        return round(total_cost, 2)
    
    def estimate_dining_costs(self, restaurants: List[Restaurant], 
                            budget_level: BudgetLevel, location: str, 
                            days: int) -> float:
        """Estimate dining costs for the trip"""
        location_multiplier = self.get_location_multiplier(location)
        daily_dining = self.dining_costs[budget_level]
        
        # Calculate daily dining cost
        daily_cost = sum(daily_dining.values())  # breakfast + lunch + dinner
        
        # If specific restaurants are provided, use their costs
        if restaurants:
            restaurant_cost = sum(restaurant.cost_per_person for restaurant in restaurants)
            # Assume 2 meals per day from restaurants, 1 meal from estimates
            total_cost = (restaurant_cost * 2/3) + (daily_cost * days * 1/3)
        else:
            total_cost = daily_cost * days
        
        return round(total_cost * location_multiplier, 2)
    
    def estimate_transportation_costs(self, location: str, days: int, 
                                    budget_level: BudgetLevel,
                                    transportation_type: str = "public_transit") -> float:
        """Estimate transportation costs"""
        location_multiplier = self.get_location_multiplier(location)
        base_cost = self.transportation_costs[transportation_type][budget_level.value]
        
        # Daily transportation cost
        daily_cost = base_cost * location_multiplier
        
        # Apply weekly discount for longer stays
        if days >= 7:
            weekly_cost = daily_cost * 7 * 0.8  # 20% discount for weekly passes
            remaining_days = days - 7
            total_cost = weekly_cost + (daily_cost * remaining_days)
        else:
            total_cost = daily_cost * days
        
        return round(total_cost, 2)
    
    def estimate_miscellaneous_costs(self, budget_level: BudgetLevel, days: int) -> float:
        """Estimate miscellaneous costs (souvenirs, tips, etc.)"""
        daily_misc = {
            BudgetLevel.BUDGET: 10,
            BudgetLevel.MODERATE: 20,
            BudgetLevel.LUXURY: 40
        }
        
        return round(daily_misc[budget_level] * days, 2)
    
    def calculate_total_cost_breakdown(self, 
                                     accommodations: List[Accommodation],
                                     activities: List[Activity],
                                     restaurants: List[Restaurant],
                                     preferences: TravelPreferences,
                                     location: str,
                                     days: int) -> CostBreakdown:
        """Calculate complete cost breakdown for the trip"""
        
        # Accommodation costs
        if accommodations:
            accommodation_cost = sum(acc.price_per_night for acc in accommodations)
        else:
            # Estimate accommodation cost
            acc_type = preferences.accommodation_types[0] if preferences.accommodation_types else AccommodationType.HOTEL
            accommodation_cost = self.estimate_accommodation_cost(
                acc_type, preferences.budget_level, location, days
            )
        
        # Activity costs
        if activities:
            activity_cost = sum(act.cost for act in activities)
        else:
            activity_cost = self.estimate_activity_costs(
                activities, preferences.budget_level, location
            )
        
        # Dining costs
        dining_cost = self.estimate_dining_costs(
            restaurants, preferences.budget_level, location, days
        )
        
        # Transportation costs
        transportation_cost = self.estimate_transportation_costs(
            location, days, preferences.budget_level
        )
        
        # Miscellaneous costs
        misc_cost = self.estimate_miscellaneous_costs(preferences.budget_level, days)
        
        return CostBreakdown(
            accommodation=accommodation_cost,
            activities=activity_cost,
            dining=dining_cost,
            transportation=transportation_cost,
            miscellaneous=misc_cost
        )
    
    def optimize_for_budget(self, total_budget: float, 
                          cost_breakdown: CostBreakdown,
                          preferences: TravelPreferences) -> Dict[str, float]:
        """Optimize costs to fit within budget"""
        current_total = cost_breakdown.total
        budget_difference = total_budget - current_total
        
        if budget_difference >= 0:
            # Budget is sufficient, return current breakdown
            return cost_breakdown.dict()
        
        # Need to reduce costs
        reduction_needed = abs(budget_difference)
        
        # Priority order for cost reduction (least important first)
        reduction_priorities = [
            ("miscellaneous", 0.5),  # Reduce by 50%
            ("activities", 0.3),     # Reduce by 30%
            ("dining", 0.2),         # Reduce by 20%
            ("transportation", 0.1), # Reduce by 10%
            ("accommodation", 0.1)   # Reduce by 10%
        ]
        
        optimized_costs = cost_breakdown.dict()
        
        for category, reduction_factor in reduction_priorities:
            if reduction_needed <= 0:
                break
                
            current_cost = optimized_costs[category]
            max_reduction = current_cost * reduction_factor
            actual_reduction = min(reduction_needed, max_reduction)
            
            optimized_costs[category] = current_cost - actual_reduction
            reduction_needed -= actual_reduction
        
        return optimized_costs
    
    def suggest_budget_adjustments(self, cost_breakdown: CostBreakdown,
                                 target_budget: float) -> List[str]:
        """Suggest ways to adjust the budget"""
        suggestions = []
        total_cost = cost_breakdown.total
        
        if total_cost > target_budget:
            overspend = total_cost - target_budget
            suggestions.append(f"Budget exceeded by ${overspend:.2f}")
            
            # Suggest specific reductions
            if cost_breakdown.accommodation > target_budget * 0.4:
                suggestions.append("Consider more budget-friendly accommodation options")
            
            if cost_breakdown.activities > target_budget * 0.3:
                suggestions.append("Reduce number of paid activities or choose free alternatives")
            
            if cost_breakdown.dining > target_budget * 0.25:
                suggestions.append("Mix fine dining with casual restaurants to reduce dining costs")
        
        elif total_cost < target_budget * 0.8:
            suggestions.append("You have room to upgrade your experience!")
            suggestions.append("Consider adding more activities or upgrading accommodation")
        
        return suggestions
    
    def calculate_real_accommodation_costs(self, available_hotels: List[Dict], 
                                         nights: int, budget_level: BudgetLevel) -> Dict[str, Any]:
        """
        Calculate accommodation costs using real availability data.
        
        Args:
            available_hotels: List of hotels with real pricing from Amadeus API
            nights: Number of nights
            budget_level: Budget level for filtering
            
        Returns:
            Dictionary with real cost breakdown
        """
        if not available_hotels:
            return {
                "total_cost": 0.0,
                "available_hotels": 0,
                "cost_range": {"min": 0.0, "max": 0.0, "average": 0.0},
                "recommendations": [],
                "availability_status": "no_hotels_available"
            }
        
        # Extract pricing data
        total_costs = []
        recommendations = []
        
        for hotel in available_hotels:
            price_data = hotel.get('price_range', {})
            if price_data.get('available', False):
                total_cost = price_data.get('total', 0)
                total_costs.append(total_cost)
                
                # Create recommendation
                recommendation = {
                    'name': hotel.get('name', 'Unknown'),
                    'total_cost': total_cost,
                    'cost_per_night': total_cost / nights if nights > 0 else 0,
                    'rating': hotel.get('rating'),
                    'amenities': hotel.get('amenities', []),
                    'location': hotel.get('location', {}),
                    'hotel_id': hotel.get('hotel_id')
                }
                recommendations.append(recommendation)
        
        if not total_costs:
            return {
                "total_cost": 0.0,
                "available_hotels": 0,
                "cost_range": {"min": 0.0, "max": 0.0, "average": 0.0},
                "recommendations": [],
                "availability_status": "no_pricing_available"
            }
        
        # Calculate cost statistics
        min_cost = min(total_costs)
        max_cost = max(total_costs)
        avg_cost = sum(total_costs) / len(total_costs)
        
        # Filter recommendations by budget level
        budget_thresholds = {
            BudgetLevel.BUDGET: avg_cost * 0.7,
            BudgetLevel.MODERATE: avg_cost * 1.3,
            BudgetLevel.LUXURY: float('inf')
        }
        
        threshold = budget_thresholds.get(budget_level, avg_cost)
        filtered_recommendations = [
            rec for rec in recommendations 
            if rec['total_cost'] <= threshold
        ]
        
        # Sort by cost
        filtered_recommendations.sort(key=lambda x: x['total_cost'])
        
        return {
            "total_cost": min_cost,  # Use cheapest available option
            "available_hotels": len(available_hotels),
            "cost_range": {
                "min": min_cost,
                "max": max_cost,
                "average": avg_cost
            },
            "recommendations": filtered_recommendations[:5],  # Top 5 recommendations
            "availability_status": "available",
            "budget_level": budget_level.value
        } 