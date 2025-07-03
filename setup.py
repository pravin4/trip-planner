#!/usr/bin/env python3
"""
Setup script for Smart Travel Planner
Helps users get started with the travel planning system.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    try:
        # Copy env.example to .env
        with open(env_example, 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        print("✅ Created .env file from template")
        print("   Please edit .env file and add your API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = ["outputs", "logs", "templates"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")

def check_api_keys():
    """Check if API keys are configured."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        required_keys = [
            "OPENAI_API_KEY",
            "GOOGLE_PLACES_API_KEY",
            "YELP_API_KEY"
        ]
        
        missing_keys = []
        for key in required_keys:
            if f"{key}=" in content and "your_" in content:
                missing_keys.append(key)
        
        if missing_keys:
            print("⚠️  Missing or placeholder API keys:")
            for key in missing_keys:
                print(f"   - {key}")
            print("   Please update your .env file with actual API keys")
            return False
        else:
            print("✅ API keys appear to be configured")
            return True
            
    except Exception as e:
        print(f"❌ Error checking API keys: {e}")
        return False

def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    
    try:
        subprocess.check_call([sys.executable, "test_travel_planner.py"])
        print("✅ Tests completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Setup completed!")
    print("\n📋 Next Steps:")
    print("1. Edit .env file and add your API keys:")
    print("   - OpenAI API Key (required)")
    print("   - Google Places API Key (required)")
    print("   - Yelp API Key (required)")
    print("   - Booking.com API Key (optional)")
    
    print("\n2. Test the system:")
    print("   python test_travel_planner.py")
    
    print("\n3. Run the main application:")
    print("   python main.py")
    
    print("\n4. Start the web API:")
    print("   python api.py")
    print("   Then visit: http://localhost:8000/docs")
    
    print("\n5. Create your first itinerary:")
    print("   from main import SmartTravelPlanner")
    print("   planner = SmartTravelPlanner()")
    print("   itinerary = planner.create_itinerary(")
    print("       destination='San Francisco, CA',")
    print("       start_date='2024-06-15',")
    print("       end_date='2024-06-20',")
    print("       budget=2000")
    print("   )")

def main():
    """Main setup function."""
    print("🧳 Smart Travel Planner - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed at .env file creation")
        sys.exit(1)
    
    # Check API keys
    check_api_keys()
    
    # Run tests
    print("\n" + "=" * 40)
    run_tests()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 