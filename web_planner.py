#!/usr/bin/env python3
"""
Web-based Travel Planner
A simple Flask web interface for creating travel itineraries.
"""

import os
import sys
from datetime import date, datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SmartTravelPlanner
from utils.serialization_helper import serialize_itinerary

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize the travel planner
planner = SmartTravelPlanner()

@app.route('/')
def index():
    """Main page with the travel planning form."""
    return render_template('index.html')

@app.route('/plan', methods=['POST'])
def plan_trip():
    """Handle trip planning request."""
    try:
        data = request.get_json()
        
        # Extract form data
        destination = data.get('destination', '').strip()
        start_date = data.get('start_date', '').strip()
        end_date = data.get('end_date', '').strip()
        budget = float(data.get('budget', 0))
        group_size = int(data.get('group_size', 1))
        activity_types = data.get('activity_types', [])
        accommodation_types = data.get('accommodation_types', [])
        budget_level = data.get('budget_level', 'moderate')
        children = data.get('children', False)
        dietary_restrictions = data.get('dietary_restrictions', [])
        starting_point = data.get('starting_point', 'San Jose').strip()
        
        # Validate inputs
        if not destination:
            return jsonify({'error': 'Destination is required'}), 400
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if budget <= 0:
            return jsonify({'error': 'Budget must be greater than 0'}), 400
        
        if group_size <= 0:
            return jsonify({'error': 'Group size must be at least 1'}), 400
        
        # Calculate trip duration for budget calculations
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        duration = (end_dt - start_dt).days + 1
        daily_budget = budget / duration if duration > 0 else budget
        
        # Create preferences
        preferences = {
            "accommodation_types": accommodation_types,
            "activity_types": activity_types,
            "budget_level": budget_level,
            "group_size": group_size,
            "children": children,
            "dietary_restrictions": dietary_restrictions,
            "max_daily_budget": daily_budget,
            "total_budget": budget
        }
        
        # Create itinerary
        itinerary = planner.create_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            preferences=preferences,
            starting_point=starting_point
        )
        
        # Get travel guide
        guide = planner.get_wikivoyage_guide(destination)
        
        # Serialize itinerary for web response
        serialized_itinerary = serialize_itinerary(itinerary)
        
        # Prepare response
        response = {
            'success': True,
            'itinerary': serialized_itinerary,
            'travel_guide': guide.get('guide', {}).get('extract', '') if guide.get('success') else '',
            'message': 'Itinerary created successfully!'
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF itinerary."""
    try:
        data = request.get_json()
        itinerary = data.get('itinerary')
        
        if not itinerary:
            return jsonify({'error': 'No itinerary data provided'}), 400
        
        # Generate PDF
        filename = f"itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = f"outputs/{filename}"
        
        os.makedirs("outputs", exist_ok=True)
        
        if planner.generate_pdf(itinerary, pdf_path):
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'PDF generated successfully!'
            })
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/destinations')
def get_destinations():
    """Get list of popular destinations."""
    destinations = [
        "San Francisco, CA",
        "Big Sur, CA", 
        "Solvang, CA",
        "Napa Valley, CA",
        "Yosemite National Park, CA",
        "Lake Tahoe, CA",
        "Monterey, CA",
        "Santa Barbara, CA",
        "Palm Springs, CA",
        "San Diego, CA",
        "Los Angeles, CA",
        "New York, NY",
        "Las Vegas, NV",
        "Seattle, WA",
        "Portland, OR"
    ]
    return jsonify({'destinations': destinations})

if __name__ == '__main__':
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    print("🌐 Starting Web Travel Planner...")
    print("📱 Open your browser and go to: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001) 