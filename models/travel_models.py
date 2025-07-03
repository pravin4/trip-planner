from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum


class AccommodationType(str, Enum):
    HOTEL = "hotel"
    CAMPING = "camping"
    GLAMPING = "glamping"
    HOSTEL = "hostel"
    RESORT = "resort"
    CABIN = "cabin"


class ActivityType(str, Enum):
    OUTDOOR = "outdoor"
    CULTURAL = "cultural"
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    FOOD = "food"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"
    ENTERTAINMENT = "entertainment"


class BudgetLevel(str, Enum):
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class Location(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None


class Accommodation(BaseModel):
    name: str
    location: Location
    type: AccommodationType
    price_per_night: float
    rating: Optional[float] = None
    amenities: List[str] = []
    booking_url: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = []


class Activity(BaseModel):
    name: str
    location: Location
    type: ActivityType
    duration_hours: float
    cost: float
    description: Optional[str] = None
    booking_required: bool = False
    booking_url: Optional[str] = None
    images: List[str] = []


class Restaurant(BaseModel):
    name: str
    location: Location
    cuisine_type: str
    price_level: int
    rating: Optional[float] = None
    cost_per_person: float
    description: Optional[str] = None
    booking_url: Optional[str] = None


class DayPlan(BaseModel):
    date: date
    accommodation: Optional[Accommodation] = None
    activities: List[Activity] = []
    restaurants: List[Restaurant] = []
    transportation: List[str] = []
    notes: Optional[str] = None


class TravelPreferences(BaseModel):
    accommodation_types: List[AccommodationType] = [AccommodationType.HOTEL]
    activity_types: List[ActivityType] = [ActivityType.CULTURAL]
    budget_level: BudgetLevel = BudgetLevel.MODERATE
    max_daily_budget: float = 200.0
    dietary_restrictions: List[str] = []
    accessibility_needs: List[str] = []
    group_size: int = 1
    children: bool = False


class Itinerary(BaseModel):
    destination: str
    start_date: date
    end_date: date
    total_budget: float
    preferences: TravelPreferences
    day_plans: List[DayPlan] = []
    total_cost: float = 0.0
    cost_breakdown: Dict[str, float] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1
    
    @property
    def remaining_budget(self) -> float:
        return self.total_budget - self.total_cost


class TravelRequest(BaseModel):
    destination: str
    start_date: date
    end_date: date
    budget: float
    preferences: TravelPreferences
    special_requests: Optional[str] = None


class CostBreakdown(BaseModel):
    accommodation: float = 0.0
    activities: float = 0.0
    dining: float = 0.0
    transportation: float = 0.0
    miscellaneous: float = 0.0
    
    @property
    def total(self) -> float:
        return sum([
            self.accommodation,
            self.activities,
            self.dining,
            self.transportation,
            self.miscellaneous
        ])


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 