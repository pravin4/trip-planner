#!/usr/bin/env python3
"""
Test runner for the Trip Planner application
"""

import sys
import os
import subprocess
import glob
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Run all test files in the tests directory"""
    
    print("Running Trip Planner Tests")
    print("=" * 50)
    
    # Get all test files
    test_files = glob.glob("test_*.py")
    test_files.sort()
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        try:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {test_file} PASSED")
                passed += 1
                # Print output if any
                if result.stdout.strip():
                    print(result.stdout)
            else:
                print(f"❌ {test_file} FAILED")
                print(f"Error: {result.stderr}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_file} ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test file"""
    
    test_file = f"test_{test_name}.py"
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found!")
        return False
    
    print(f"Running {test_file}...")
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"✅ {test_file} PASSED")
            print(result.stdout)
            return True
        else:
            print(f"❌ {test_file} FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {test_file} ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        # Run all tests
        run_all_tests() 