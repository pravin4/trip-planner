# Smart Travel Planner 🧳✈️

An intelligent, agentic travel planning system that creates personalized itineraries using real-time data from multiple APIs.

## Features

- 🤖 **Multi-Agent System**: Coordinated agents for research, planning, and optimization
- 🏨 **Real Hotel Data**: Integration with Booking.com, Expedia, and Google Places APIs
- 🏕️ **Camping/Glamping**: Comprehensive accommodation options
- 💰 **Budget Optimization**: Smart cost estimation and budget management
- 📅 **Itinerary Generation**: Beautiful PDF and HTML itineraries
- 🗺️ **Location Intelligence**: Google Places integration for attractions and activities
- 🍽️ **Dining Recommendations**: Yelp API integration for restaurant suggestions

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Research      │    │   Planning      │    │   Optimization  │
│     Agent       │◄──►│     Agent       │◄──►│     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Google Places  │    │   Booking.com   │    │   Cost Estimator│
│     API         │    │     API         │    │     Module      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Yelp API    │    │   Itinerary     │    │   PDF/HTML      │
│                 │    │   Builder       │    │   Generator     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd trip-planner
   pip3 install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp env.example .env
   # Add your API keys to .env
   ```

3. **Run the Planner**
   ```bash
   python main.py
   ```

## API Keys Required

- OpenAI API Key
- Google Places API Key
- Yelp API Key
- Booking.com API Key (optional)

## Usage Example

```python
from travel_planner import SmartTravelPlanner

planner = SmartTravelPlanner()

itinerary = planner.create_itinerary(
    destination="San Francisco, CA",
    start_date="2024-06-15",
    end_date="2024-06-20",
    budget=2000,
    preferences={
        "accommodation_type": ["hotel", "glamping"],
        "activities": ["outdoor", "cultural"],
        "dining": ["local", "fine_dining"]
    }
)

# Generate PDF itinerary
planner.generate_pdf(itinerary, "my_trip.pdf")
```

## Project Structure

```
trip-planner/
├── agents/                 # Multi-agent system
│   ├── research_agent.py
│   ├── planning_agent.py
│   └── optimization_agent.py
├── api_integrations/       # External API clients
│   ├── google_places.py
│   ├── yelp_api.py
│   └── booking_api.py
├── core/                   # Core functionality
│   ├── cost_estimator.py
│   ├── itinerary_builder.py
│   └── pdf_generator.py
├── models/                 # Data models
│   └── travel_models.py
├── utils/                  # Utilities
│   └── helpers.py
├── main.py                 # Main entry point
├── requirements.txt
└── README.md
```

## Testing

Run the test suite:
```bash
# Run all tests
cd tests
python3 run_tests.py

# Run specific test
python3 run_tests.py transportation
python3 run_tests.py geographic_logic

# Run individual test files
python3 test_transportation.py
python3 test_geographic_logic.py
```

See `tests/README.md` for detailed testing information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Real Availability Checking

The system now supports **real-time hotel availability and pricing** using the Amadeus API.

### Getting Amadeus API Credentials

1. **Sign up for free API access** at [Amadeus for Developers](https://developers.amadeus.com/)
2. **Create a new application** in the developer portal
3. **Get your credentials**:
   - `AMADEUS_CLIENT_ID`
   - `AMADEUS_CLIENT_SECRET`
4. **Add to your `.env` file**:
   ```
   AMADEUS_CLIENT_ID=your_client_id_here
   AMADEUS_CLIENT_SECRET=your_client_secret_here
   ```

### Testing Real Availability

Run the availability test script:
```bash
python3 test_availability.py
```

This will:
- ✅ Check real hotel availability for specific dates
- ✅ Get actual pricing (not estimates)
- ✅ Show available rooms and rates
- ✅ Provide booking recommendations

### What Real Availability Provides

- **Real-time pricing** for specific dates
- **Actual room availability** (not estimates)
- **Multiple room types** and rates
- **Cancellation policies** and terms
- **Hotel amenities** and ratings
- **Location data** and contact info

### Limitations

- **Free tier limits**: 1000 API calls per month
- **Geographic coverage**: Limited to major cities
- **Hotel selection**: Not all hotels participate
- **Pricing accuracy**: Subject to change until booking

### Example Output

```
🏨 Real Hotel Availability Testing
============================================================
✅ Found 15 available hotels!

💰 Cost Breakdown:
   💵 Cheapest: $240.00
   💵 Most Expensive: $1,200.00
   💵 Average: $450.00

🏆 Top 3 Recommendations:

1. Hotel A
   💵 $240.00 total
   ⭐ Rating: 4.2

2. Hotel B  
   💵 $280.00 total
   ⭐ Rating: 4.5

3. Hotel C
   💵 $320.00 total
   ⭐ Rating: 4.1
``` 