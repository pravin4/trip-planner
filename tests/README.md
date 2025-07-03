# Trip Planner Test Suite

This directory contains all test files for the Trip Planner application.

## Test Files

- `test_transportation.py` - Tests the transportation planning system
- `test_geographic_logic.py` - Tests geographic clustering and validation
- `test_travel_planner.py` - Tests the main travel planning workflow
- `test_booking_api.py` - Tests Booking.com API integration
- `test_availability.py` - Tests Amadeus API for hotel availability
- `test_api_key.py` - Tests API key validation
- `test_correct_api.py` - Tests API endpoint corrections
- `test_deprecated_endpoint.py` - Tests handling of deprecated endpoints
- `test_exact_rapidapi.py` - Tests RapidAPI integrations
- `test_rate_limit.py` - Tests rate limiting handling

## Running Tests

### Run All Tests
```bash
cd tests
python run_tests.py
```

### Run Specific Test
```bash
cd tests
python run_tests.py transportation  # Runs test_transportation.py
python run_tests.py geographic_logic  # Runs test_geographic_logic.py
```

### Run Individual Test Files
```bash
cd tests
python test_transportation.py
python test_geographic_logic.py
```

## Test Categories

### Unit Tests
- `test_transportation.py` - Transportation planning logic
- `test_geographic_logic.py` - Geographic utilities and clustering
- `test_api_key.py` - API key validation

### Integration Tests
- `test_travel_planner.py` - Full travel planning workflow
- `test_booking_api.py` - Booking.com API integration
- `test_availability.py` - Amadeus API integration

### API Tests
- `test_correct_api.py` - API endpoint validation
- `test_deprecated_endpoint.py` - Deprecated endpoint handling
- `test_exact_rapidapi.py` - RapidAPI service tests
- `test_rate_limit.py` - Rate limiting and error handling

## Test Requirements

Make sure you have:
1. All dependencies installed (`pip install -r requirements.txt`)
2. Environment variables set up (`.env` file with API keys)
3. Python 3.8+ installed

## Adding New Tests

When adding new test files:
1. Follow the naming convention: `test_*.py`
2. Update the import paths to include the parent directory
3. Add a description in this README
4. Ensure tests can run independently

## Test Output

Tests will show:
- ✅ PASSED - Test completed successfully
- ❌ FAILED - Test failed with errors
- ⚠️ ERROR - Test encountered an exception

The test runner will provide a summary of passed/failed tests at the end. 