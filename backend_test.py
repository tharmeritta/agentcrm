#!/usr/bin/env python3
import requests
import json
import sys
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://9d436bfd-169d-4a6d-9d03-861b7fcf694e.preview.emergentagent.com"
API_PREFIX = "/api"
BASE_URL = f"{BACKEND_URL}{API_PREFIX}"

# Super Admin credentials
SUPER_ADMIN_USERNAME = "tharme.ritta"
SUPER_ADMIN_PASSWORD = "Tharme@789"

# Test results
test_results = {
    "basic_connectivity": {"status": "Not tested", "details": ""},
    "authentication": {"status": "Not tested", "details": ""},
    "user_info": {"status": "Not tested", "details": ""},
}

access_token = None

def print_separator():
    print("=" * 80)

def test_basic_connectivity():
    """Test basic connectivity to the server"""
    print_separator()
    print(f"Testing basic connectivity to {BASE_URL}")
    
    try:
        # The root endpoint might not be defined, so we'll try both / and /api
        response = requests.get(f"{BACKEND_URL}/")
        
        if response.status_code == 404:
            # Try the /api endpoint
            response = requests.get(BASE_URL)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")  # Print first 200 chars
        
        if response.status_code < 500:  # Accept any non-server error response
            test_results["basic_connectivity"]["status"] = "Success"
            test_results["basic_connectivity"]["details"] = f"Server responded with status code {response.status_code}"
            return True
        else:
            test_results["basic_connectivity"]["status"] = "Failed"
            test_results["basic_connectivity"]["details"] = f"Server error: {response.status_code}"
            return False
    except requests.exceptions.RequestException as e:
        test_results["basic_connectivity"]["status"] = "Failed"
        test_results["basic_connectivity"]["details"] = f"Connection error: {str(e)}"
        print(f"Connection error: {str(e)}")
        return False

def test_authentication():
    """Test authentication with Super Admin credentials"""
    global access_token
    
    print_separator()
    print(f"Testing authentication with Super Admin credentials")
    
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get("access_token")
            
            if access_token:
                print("Successfully obtained access token")
                print(f"User info: {response_data.get('user', {})}")
                test_results["authentication"]["status"] = "Success"
                test_results["authentication"]["details"] = "Successfully authenticated as Super Admin"
                return True
            else:
                print("Authentication succeeded but no access token was returned")
                test_results["authentication"]["status"] = "Failed"
                test_results["authentication"]["details"] = "No access token in response"
                return False
        else:
            print(f"Authentication failed: {response.text}")
            test_results["authentication"]["status"] = "Failed"
            test_results["authentication"]["details"] = f"Authentication failed with status {response.status_code}: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        test_results["authentication"]["status"] = "Failed"
        test_results["authentication"]["details"] = f"Connection error: {str(e)}"
        print(f"Connection error: {str(e)}")
        return False

def test_user_info():
    """Test getting user info with the access token"""
    print_separator()
    print(f"Testing user info endpoint")
    
    if not access_token:
        print("Cannot test user info without access token")
        test_results["user_info"]["status"] = "Skipped"
        test_results["user_info"]["details"] = "No access token available"
        return False
    
    user_info_url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(user_info_url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"User info: {json.dumps(user_info, indent=2)}")
            test_results["user_info"]["status"] = "Success"
            test_results["user_info"]["details"] = "Successfully retrieved user info"
            return True
        else:
            print(f"Failed to get user info: {response.text}")
            test_results["user_info"]["status"] = "Failed"
            test_results["user_info"]["details"] = f"Failed with status {response.status_code}: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        test_results["user_info"]["status"] = "Failed"
        test_results["user_info"]["details"] = f"Connection error: {str(e)}"
        print(f"Connection error: {str(e)}")
        return False

def run_tests():
    """Run all tests in sequence"""
    print(f"Starting backend tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API URL: {BASE_URL}")
    
    # Test basic connectivity first
    if not test_basic_connectivity():
        print("Basic connectivity test failed. Stopping tests.")
        return
    
    # Test authentication
    if not test_authentication():
        print("Authentication test failed. Continuing with other tests...")
    
    # Test user info
    test_user_info()
    
    # Print summary
    print_separator()
    print("TEST SUMMARY:")
    for test_name, result in test_results.items():
        status = result["status"]
        if status == "Success":
            status_str = f"✅ {status}"
        elif status == "Failed":
            status_str = f"❌ {status}"
        else:
            status_str = f"⚠️ {status}"
        
        print(f"{test_name}: {status_str}")
        print(f"  Details: {result['details']}")
    
    # Overall result
    if all(result["status"] == "Success" for result in test_results.values()):
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. See details above.")

if __name__ == "__main__":
    run_tests()
