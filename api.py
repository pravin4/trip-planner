#!/usr/bin/env python3
"""
FastAPI Web Interface for Smart Travel Planner
Provides REST API endpoints for travel planning functionality.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import date
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from main import SmartTravelPlanner
from utils.helpers import (
    validate_date_format, validate_date_range, format_location,
    sanitize_preferences, format_error_message, generate_trip_summary,
    format_activity_summary, format_restaurant_summary
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Travel Planner API",
    description="An intelligent, agentic travel planning system using LangGraph and multi-agent coordination",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize travel planner
try:
    planner = SmartTravelPlanner()
    logger.info("Smart Travel Planner API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Smart Travel Planner: {e}")
    planner = None


# Pydantic models for API requests/responses
class ItineraryRequest(BaseModel):
    destination: str = Field(..., description="Travel destination (e.g., 'San Francisco, CA')")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    budget: float = Field(..., gt=0, le=100000, description="Total budget for the trip")
    preferences: Optional[Dict[str, Any]] = Field(default={}, description="Travel preferences")


class DestinationInsightsRequest(BaseModel):
    destination: str = Field(..., description="Destination to research")





class OptimizeBudgetRequest(BaseModel):
    itinerary_id: str = Field(..., description="Itinerary ID to optimize")
    target_budget: float = Field(..., gt=0, le=100000, description="Target budget")


class ItineraryResponse(BaseModel):
    success: bool
    itinerary_id: str
    summary: Dict[str, Any]
    message: str


class DestinationInsightsResponse(BaseModel):
    success: bool
    destination: str
    insights: Dict[str, Any]
    message: str





class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str


# In-memory storage for itineraries (in production, use a database)
itinerary_storage = {}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Smart Travel Planner API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "create_itinerary": "/itinerary/create",
            "get_insights": "/destination/insights",
            "optimize_budget": "/itinerary/optimize",
            "download_pdf": "/itinerary/{itinerary_id}/pdf"
        }
    }


@app.post("/itinerary/create", response_model=ItineraryResponse)
async def create_itinerary(request: ItineraryRequest):
    """Create a new travel itinerary."""
    try:
        if not planner:
            raise HTTPException(status_code=503, detail="Travel planner not available")
        
        # Validate dates
        if not validate_date_format(request.start_date):
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if not validate_date_format(request.end_date):
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        if not validate_date_range(request.start_date, request.end_date):
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Format and validate destination
        formatted_destination = format_location(request.destination)
        
        # Sanitize preferences
        sanitized_preferences = sanitize_preferences(request.preferences)
        
        # Create itinerary
        itinerary = planner.create_itinerary(
            destination=formatted_destination,
            start_date=request.start_date,
            end_date=request.end_date,
            budget=request.budget,
            preferences=sanitized_preferences
        )
        
        # Generate unique ID and store itinerary
        import uuid
        itinerary_id = str(uuid.uuid4())
        itinerary_storage[itinerary_id] = itinerary
        
        # Generate summary
        summary = generate_trip_summary(itinerary)
        
        return ItineraryResponse(
            success=True,
            itinerary_id=itinerary_id,
            summary=summary,
            message="Itinerary created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e)
        logger.error(f"Error creating itinerary: {e}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/destination/insights", response_model=DestinationInsightsResponse)
async def get_destination_insights(request: DestinationInsightsRequest):
    """Get insights about a destination."""
    try:
        if not planner:
            raise HTTPException(status_code=503, detail="Travel planner not available")
        
        # Format destination
        formatted_destination = format_location(request.destination)
        
        # Get insights
        insights = planner.get_destination_insights(formatted_destination)
        
        if insights["success"]:
            return DestinationInsightsResponse(
                success=True,
                destination=formatted_destination,
                insights=insights,
                message="Destination insights retrieved successfully"
            )
        else:
            raise HTTPException(status_code=404, detail=insights.get("error", "Destination not found"))
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e)
        logger.error(f"Error getting destination insights: {e}")
        raise HTTPException(status_code=500, detail=error_msg)





@app.post("/itinerary/optimize")
async def optimize_itinerary_budget(request: OptimizeBudgetRequest):
    """Optimize an itinerary to fit within a target budget."""
    try:
        if not planner:
            raise HTTPException(status_code=503, detail="Travel planner not available")
        
        # Get itinerary from storage
        itinerary = itinerary_storage.get(request.itinerary_id)
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # Optimize for budget
        optimization_result = planner.optimize_for_budget(itinerary, request.target_budget)
        
        return {
            "success": True,
            "itinerary_id": request.itinerary_id,
            "optimization": optimization_result,
            "message": "Itinerary optimized successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e)
        logger.error(f"Error optimizing itinerary: {e}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/itinerary/{itinerary_id}")
async def get_itinerary(itinerary_id: str):
    """Get itinerary details by ID."""
    try:
        itinerary = itinerary_storage.get(itinerary_id)
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # Generate detailed response
        summary = generate_trip_summary(itinerary)
        
        # Add day-by-day details
        daily_plans = []
        for i, day_plan in enumerate(itinerary.day_plans, 1):
            day_details = {
                "day": i,
                "date": day_plan.date.strftime("%Y-%m-%d"),
                "day_name": day_plan.date.strftime("%A"),
                "activities": [format_activity_summary(act) for act in day_plan.activities],
                "restaurants": [format_restaurant_summary(rest) for rest in day_plan.restaurants],
                "transportation": day_plan.transportation,
                "notes": day_plan.notes
            }
            daily_plans.append(day_details)
        
        return {
            "success": True,
            "itinerary_id": itinerary_id,
            "summary": summary,
            "daily_plans": daily_plans,
            "preferences": {
                "accommodation_types": [t.value for t in itinerary.preferences.accommodation_types],
                "activity_types": [t.value for t in itinerary.preferences.activity_types],
                "budget_level": itinerary.preferences.budget_level.value,
                "group_size": itinerary.preferences.group_size,
                "children": itinerary.preferences.children,
                "dietary_restrictions": itinerary.preferences.dietary_restrictions
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e)
        logger.error(f"Error getting itinerary: {e}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/itinerary/{itinerary_id}/pdf")
async def download_itinerary_pdf(itinerary_id: str, background_tasks: BackgroundTasks):
    """Download itinerary as PDF."""
    try:
        itinerary = itinerary_storage.get(itinerary_id)
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # Create outputs directory
        os.makedirs("outputs", exist_ok=True)
        
        # Generate PDF filename
        pdf_filename = f"itinerary_{itinerary_id[:8]}_{itinerary.destination.replace(' ', '_')}.pdf"
        pdf_path = f"outputs/{pdf_filename}"
        
        # Generate PDF
        success = planner.generate_pdf(itinerary, pdf_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Return file response
        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = format_error_message(e)
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "planner_available": planner is not None,
        "timestamp": str(date.today())
    }


@app.get("/destinations/popular")
async def get_popular_destinations():
    """Get list of popular destinations."""
    popular_destinations = [
        {"name": "San Francisco, CA", "country": "USA", "category": "City"},
        {"name": "New York, NY", "country": "USA", "category": "City"},
        {"name": "Los Angeles, CA", "country": "USA", "category": "City"},
        {"name": "Miami, FL", "country": "USA", "category": "Beach"},
        {"name": "Las Vegas, NV", "country": "USA", "category": "Entertainment"},
        {"name": "Seattle, WA", "country": "USA", "category": "City"},
        {"name": "Denver, CO", "country": "USA", "category": "Outdoor"},
        {"name": "Austin, TX", "country": "USA", "category": "City"},
        {"name": "Nashville, TN", "country": "USA", "category": "Music"},
        {"name": "Portland, OR", "country": "USA", "category": "City"}
    ]
    
    return {
        "success": True,
        "destinations": popular_destinations,
        "count": len(popular_destinations)
    }


@app.get("/preferences/options")
async def get_preference_options():
    """Get available preference options."""
    return {
        "success": True,
        "accommodation_types": [
            {"value": "hotel", "label": "Hotel"},
            {"value": "hostel", "label": "Hostel"},
            {"value": "camping", "label": "Camping"},
            {"value": "glamping", "label": "Glamping"},
            {"value": "resort", "label": "Resort"},
            {"value": "cabin", "label": "Cabin"}
        ],
        "activity_types": [
            {"value": "outdoor", "label": "Outdoor"},
            {"value": "cultural", "label": "Cultural"},
            {"value": "adventure", "label": "Adventure"},
            {"value": "relaxation", "label": "Relaxation"},
            {"value": "food", "label": "Food & Dining"},
            {"value": "shopping", "label": "Shopping"},
            {"value": "nightlife", "label": "Nightlife"}
        ],
        "budget_levels": [
            {"value": "budget", "label": "Budget"},
            {"value": "moderate", "label": "Moderate"},
            {"value": "luxury", "label": "Luxury"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        exit(1)
    
    print("🚀 Starting Smart Travel Planner API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc Documentation: http://localhost:8000/redoc")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 