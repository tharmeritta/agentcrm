#!/usr/bin/env python3
import requests
import json
import sys
import os
import time
from datetime import datetime
import random
import string
import traceback

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://498e7a0a-3630-42db-bcc5-cc6cfa3ca9f7.preview.emergentagent.com"
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
    "shop_management": {"status": "Not tested", "details": ""},
    "user_management": {"status": "Not tested", "details": ""},
    "sales_request_workflow": {"status": "Not tested", "details": ""},
    "target_system": {"status": "Not tested", "details": ""},
    "shop_reward_bag": {"status": "Not tested", "details": ""},
    "leaderboard": {"status": "Not tested", "details": ""}
}

print("=" * 80)
print("TESTING FIXED CRM SYSTEM - MONGODB OBJECTID SERIALIZATION ISSUES")
print("=" * 80)
print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Backend URL: {BACKEND_URL}")
print(f"API URL: {BASE_URL}")
print("=" * 80)

# Store tokens and IDs for different users
tokens = {
    "super_admin": None,
    "admin": None,
    "agent": None
}

user_ids = {
    "admin": None,
    "agent": None,
    "agent2": None
}

# Store other test data
test_data = {
    "prize_id": None,
    "sale_request_id": None,
    "reward_bag_item_id": None,
    "admin_username": None,
    "admin_password": None,
    "agent_username": None,
    "agent_password": None
}

def print_separator():
    print("=" * 80)

def print_step(step_name):
    print(f"\n--- {step_name} ---")

def generate_random_string(length=8):
    """Generate a random string for usernames, etc."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

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

def login_user(username, password, user_type):
    """Login a user and store their token"""
    print_step(f"Logging in as {user_type} ({username})")
    
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            token = response_data.get("access_token")
            
            if token:
                tokens[user_type] = token
                print(f"Successfully logged in as {user_type}")
                print(f"User info: {response_data.get('user', {})}")
                
                # Store user ID if available
                user_info = response_data.get('user', {})
                if user_info and 'id' in user_info:
                    if user_type == 'admin':
                        user_ids['admin'] = user_info['id']
                    elif user_type == 'agent':
                        user_ids['agent'] = user_info['id']
                
                return True
            else:
                print(f"Login succeeded but no access token was returned for {user_type}")
                return False
        else:
            print(f"Login failed for {user_type}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during login for {user_type}: {str(e)}")
        return False

def test_authentication():
    """Test authentication with Super Admin credentials"""
    print_separator()
    print(f"Testing authentication with Super Admin credentials")
    
    if login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
        test_results["authentication"]["status"] = "Success"
        test_results["authentication"]["details"] = "Successfully authenticated as Super Admin"
        return True
    else:
        test_results["authentication"]["status"] = "Failed"
        test_results["authentication"]["details"] = "Failed to authenticate as Super Admin"
        return False

def test_user_info():
    """Test getting user info with the access token"""
    print_separator()
    print(f"Testing user info endpoint")
    
    if not tokens["super_admin"]:
        print("Cannot test user info without access token")
        test_results["user_info"]["status"] = "Skipped"
        test_results["user_info"]["details"] = "No access token available"
        return False
    
    user_info_url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
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

def test_shop_management():
    """Test shop management functionality (Super Admin)"""
    print_separator()
    print("Testing shop management functionality")
    
    if not tokens["super_admin"]:
        print("Cannot test shop management without Super Admin token")
        test_results["shop_management"]["status"] = "Skipped"
        test_results["shop_management"]["details"] = "No Super Admin token available"
        return False
    
    headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 1: Create a sample prize
    print_step("Creating a sample prize")
    create_prize_url = f"{BASE_URL}/super-admin/prizes"
    prize_data = {
        "name": "Gift Card",
        "description": "Amazon gift card",
        "coin_cost": 2,
        "is_limited": False
    }
    
    try:
        response = requests.post(create_prize_url, json=prize_data, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Prize creation response: {json.dumps(response_data, indent=2)}")
            
            if "prize_id" in response_data:
                test_data["prize_id"] = response_data["prize_id"]
                print(f"Prize created with ID: {test_data['prize_id']}")
            else:
                print("Prize created but no ID was returned")
        else:
            print(f"Failed to create prize: {response.text}")
            test_results["shop_management"]["status"] = "Failed"
            test_results["shop_management"]["details"] = f"Failed to create prize: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize creation: {str(e)}")
        test_results["shop_management"]["status"] = "Failed"
        test_results["shop_management"]["details"] = f"Connection error during prize creation: {str(e)}"
        return False
    
    # Step 2: List all prizes to verify creation
    print_step("Listing all prizes")
    list_prizes_url = f"{BASE_URL}/super-admin/prizes"
    
    try:
        response = requests.get(list_prizes_url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            prizes = response.json()
            print(f"Found {len(prizes)} prizes")
            
            # Check if our prize is in the list
            prize_found = False
            for prize in prizes:
                if test_data["prize_id"] and prize.get("id") == test_data["prize_id"]:
                    prize_found = True
                    print(f"Found our created prize: {prize.get('name')}")
                    break
            
            if not prize_found and test_data["prize_id"]:
                print("Our created prize was not found in the list")
                test_results["shop_management"]["status"] = "Failed"
                test_results["shop_management"]["details"] = "Created prize not found in prizes list"
                return False
        else:
            print(f"Failed to list prizes: {response.text}")
            # Continue with the test even if listing fails
            print("Continuing with the test despite listing failure")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize listing: {str(e)}")
        # Continue with the test even if listing fails
        print("Continuing with the test despite listing failure")
    
    # Step 3: Test prize creation with limited quantity
    print_step("Creating a prize with limited quantity")
    limited_prize_data = {
        "name": "Limited Edition Badge",
        "description": "Special badge with limited availability",
        "coin_cost": 5,
        "is_limited": True,
        "quantity_available": 10
    }
    
    try:
        response = requests.post(create_prize_url, json=limited_prize_data, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Limited prize creation response: {json.dumps(response_data, indent=2)}")
            print("Successfully created limited quantity prize")
            
            test_results["shop_management"]["status"] = "Success"
            test_results["shop_management"]["details"] = "Successfully created prizes"
            return True
        else:
            print(f"Failed to create limited prize: {response.text}")
            test_results["shop_management"]["status"] = "Failed"
            test_results["shop_management"]["details"] = f"Failed to create limited prize: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during limited prize creation: {str(e)}")
        test_results["shop_management"]["status"] = "Failed"
        test_results["shop_management"]["details"] = f"Connection error during limited prize creation: {str(e)}"
        return False

def test_user_management():
    """Test user management functionality"""
    print_separator()
    print("Testing user management functionality")
    
    if not tokens["super_admin"]:
        print("Cannot test user management without Super Admin token")
        test_results["user_management"]["status"] = "Skipped"
        test_results["user_management"]["details"] = "No Super Admin token available"
        return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 1: Super Admin creates an admin user
    print_step("Super Admin creating an admin user")
    admin_username = f"admin_{generate_random_string()}"
    admin_password = "Admin@123"
    
    # Store for later use
    test_data["admin_username"] = admin_username
    test_data["admin_password"] = admin_password
    
    create_admin_url = f"{BASE_URL}/super-admin/admins"
    admin_data = {
        "username": admin_username,
        "password": admin_password,
        "role": "admin",
        "name": "Test Admin"
    }
    
    try:
        response = requests.post(create_admin_url, json=admin_data, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Admin creation response: {json.dumps(response_data, indent=2)}")
            
            if "admin_id" in response_data:
                user_ids["admin"] = response_data["admin_id"]
                print(f"Admin created with ID: {user_ids['admin']}")
            else:
                print("Admin created but no ID was returned")
        else:
            print(f"Failed to create admin: {response.text}")
            test_results["user_management"]["status"] = "Failed"
            test_results["user_management"]["details"] = f"Failed to create admin: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during admin creation: {str(e)}")
        test_results["user_management"]["status"] = "Failed"
        test_results["user_management"]["details"] = f"Connection error during admin creation: {str(e)}"
        return False
    
    # Step 2: Super Admin creates an agent user directly
    print_step("Super Admin creating an agent user")
    agent_username = f"agent_{generate_random_string()}"
    agent_password = "Agent@123"
    
    # Store for later use
    test_data["agent_username"] = agent_username
    test_data["agent_password"] = agent_password
    
    create_agent_url = f"{BASE_URL}/super-admin/agents"
    agent_data = {
        "username": agent_username,
        "password": agent_password,
        "role": "agent",
        "name": "Test Agent"
    }
    
    try:
        response = requests.post(create_agent_url, json=agent_data, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Agent creation response: {json.dumps(response_data, indent=2)}")
            
            if "agent_id" in response_data:
                user_ids["agent"] = response_data["agent_id"]
                print(f"Agent created with ID: {user_ids['agent']}")
            else:
                print("Agent created but no ID was returned")
        else:
            print(f"Failed to create agent: {response.text}")
            test_results["user_management"]["status"] = "Failed"
            test_results["user_management"]["details"] = f"Failed to create agent: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during agent creation: {str(e)}")
        test_results["user_management"]["status"] = "Failed"
        test_results["user_management"]["details"] = f"Connection error during agent creation: {str(e)}"
        return False
    
    # Step 3: Login as admin
    if not login_user(admin_username, admin_password, "admin"):
        print("Failed to login as admin")
        test_results["user_management"]["status"] = "Failed"
        test_results["user_management"]["details"] = "Failed to login as admin"
        return False
    
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    
    # Step 4: Admin creates another agent user
    print_step("Admin creating another agent user")
    agent2_username = f"agent2_{generate_random_string()}"
    agent2_password = "Agent@123"
    
    admin_create_agent_url = f"{BASE_URL}/admin/agents"
    agent2_data = {
        "username": agent2_username,
        "password": agent2_password,
        "role": "agent",
        "name": "Test Agent 2"
    }
    
    try:
        response = requests.post(admin_create_agent_url, json=agent2_data, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Agent 2 creation response: {json.dumps(response_data, indent=2)}")
            
            if "agent_id" in response_data:
                user_ids["agent2"] = response_data["agent_id"]
                print(f"Agent 2 created with ID: {user_ids['agent2']}")
            else:
                print("Agent 2 created but no ID was returned")
        else:
            print(f"Failed to create agent 2: {response.text}")
            test_results["user_management"]["status"] = "Failed"
            test_results["user_management"]["details"] = f"Failed to create agent 2: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during agent 2 creation: {str(e)}")
        test_results["user_management"]["status"] = "Failed"
        test_results["user_management"]["details"] = f"Connection error during agent 2 creation: {str(e)}"
        return False
    
    # Step 5: Test GET /api/super-admin/all-users to see all credentials
    print_step("Super Admin getting all users")
    all_users_url = f"{BASE_URL}/super-admin/all-users"
    
    try:
        response = requests.get(all_users_url, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users")
            
            # Check if our created users are in the list
            admin_found = False
            agent_found = False
            agent2_found = False
            
            for user in users:
                if user_ids["admin"] and user.get("id") == user_ids["admin"]:
                    admin_found = True
                    print(f"Found our created admin: {user.get('username')}")
                
                if user_ids["agent"] and user.get("id") == user_ids["agent"]:
                    agent_found = True
                    print(f"Found our created agent: {user.get('username')}")
                
                if user_ids["agent2"] and user.get("id") == user_ids["agent2"]:
                    agent2_found = True
                    print(f"Found our created agent 2: {user.get('username')}")
            
            if not admin_found and user_ids["admin"]:
                print("Our created admin was not found in the list")
            
            if not agent_found and user_ids["agent"]:
                print("Our created agent was not found in the list")
            
            if not agent2_found and user_ids["agent2"]:
                print("Our created agent 2 was not found in the list")
            
            if (not admin_found and user_ids["admin"]) or (not agent_found and user_ids["agent"]) or (not agent2_found and user_ids["agent2"]):
                print("Not all created users were found in the users list, but continuing with the test")
        else:
            print(f"Failed to get all users: {response.text}")
            print("Continuing with the test despite failure to list all users")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during get all users: {str(e)}")
        print("Continuing with the test despite failure to list all users")
    
    # Login as the agent for future tests
    if not login_user(agent_username, agent_password, "agent"):
        print("Failed to login as agent")
        test_results["user_management"]["status"] = "Failed"
        test_results["user_management"]["details"] = "Failed to login as agent"
        return False
    
    test_results["user_management"]["status"] = "Success"
    test_results["user_management"]["details"] = "Successfully created users and logged in as admin and agent"
    return True

def test_sales_request_workflow():
    """Test the sales request workflow"""
    print_separator()
    print("Testing sales request workflow")
    
    if not tokens["agent"] or not tokens["admin"]:
        print("Cannot test sales request workflow without agent and admin tokens")
        test_results["sales_request_workflow"]["status"] = "Skipped"
        test_results["sales_request_workflow"]["details"] = "Missing agent or admin token"
        return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    
    # Step 1: Agent submits a sale request
    print_step("Agent submitting a sale request")
    sale_request_url = f"{BASE_URL}/agent/sale-request"
    sale_data = {
        "sale_amount": "100"  # $100 sale
    }
    
    try:
        response = requests.post(sale_request_url, json=sale_data, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Sale request response: {json.dumps(response_data, indent=2)}")
            print("Sale request submitted successfully")
        else:
            print(f"Failed to submit sale request: {response.text}")
            test_results["sales_request_workflow"]["status"] = "Failed"
            test_results["sales_request_workflow"]["details"] = f"Failed to submit sale request: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during sale request submission: {str(e)}")
        test_results["sales_request_workflow"]["status"] = "Failed"
        test_results["sales_request_workflow"]["details"] = f"Connection error during sale request submission: {str(e)}"
        return False
    
    # Step 2: Admin verifies sale request appears in pending requests with agent name
    print_step("Admin checking pending sale requests")
    pending_requests_url = f"{BASE_URL}/admin/sale-requests"
    
    try:
        response = requests.get(pending_requests_url, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            requests_data = response.json()
            print(f"Found {len(requests_data)} pending requests")
            
            # Find our agent's request
            agent_request = None
            for req in requests_data:
                if req.get("agent_id") == user_ids["agent"]:
                    agent_request = req
                    test_data["sale_request_id"] = req.get("id")
                    break
            
            if agent_request:
                print(f"Found our agent's request: {json.dumps(agent_request, indent=2)}")
                
                # Check if agent name is included
                if "agent_name" in agent_request:
                    print(f"Agent name is included: {agent_request['agent_name']}")
                else:
                    print("Agent name is NOT included in the request")
                    test_results["sales_request_workflow"]["status"] = "Failed"
                    test_results["sales_request_workflow"]["details"] = "Agent name not included in sale request"
                    return False
            else:
                print("Our agent's request was not found")
                test_results["sales_request_workflow"]["status"] = "Failed"
                test_results["sales_request_workflow"]["details"] = "Agent's sale request not found in pending requests"
                return False
        else:
            print(f"Failed to get pending requests: {response.text}")
            test_results["sales_request_workflow"]["status"] = "Failed"
            test_results["sales_request_workflow"]["details"] = f"Failed to get pending requests: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during pending requests check: {str(e)}")
        test_results["sales_request_workflow"]["status"] = "Failed"
        test_results["sales_request_workflow"]["details"] = f"Connection error during pending requests check: {str(e)}"
        return False
    
    # Step 3: Admin approves the sale request
    print_step("Admin approving the sale request")
    if not test_data["sale_request_id"]:
        print("Cannot approve sale request without request ID")
        test_results["sales_request_workflow"]["status"] = "Failed"
        test_results["sales_request_workflow"]["details"] = "Sale request ID not found"
        return False
    
    approve_url = f"{BASE_URL}/admin/sale-requests/{test_data['sale_request_id']}/approve"
    
    try:
        response = requests.put(approve_url, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Approval response: {json.dumps(response_data, indent=2)}")
            print("Sale request approved successfully")
        else:
            print(f"Failed to approve sale request: {response.text}")
            test_results["sales_request_workflow"]["status"] = "Failed"
            test_results["sales_request_workflow"]["details"] = f"Failed to approve sale request: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during sale request approval: {str(e)}")
        test_results["sales_request_workflow"]["status"] = "Failed"
        test_results["sales_request_workflow"]["details"] = f"Connection error during sale request approval: {str(e)}"
        return False
    
    # Step 4: Verify agent's coins and deposits are updated
    print_step("Verifying agent's updated coins and deposits")
    agent_info_url = f"{BASE_URL}/agent/dashboard"
    
    try:
        response = requests.get(agent_info_url, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            agent_info = response.json()
            print(f"Agent dashboard: {json.dumps(agent_info, indent=2)}")
            
            # Check if coins and deposits are updated
            agent_data = agent_info.get("agent_info", {})
            coins = agent_data.get("coins", 0)
            deposits = agent_data.get("deposits", 0)
            
            if coins > 0 and deposits > 0:
                print(f"Agent coins ({coins}) and deposits ({deposits}) have been updated")
                test_results["sales_request_workflow"]["status"] = "Success"
                test_results["sales_request_workflow"]["details"] = "Successfully completed sales request workflow"
                return True
            else:
                print("Agent coins or deposits were not updated")
                test_results["sales_request_workflow"]["status"] = "Failed"
                test_results["sales_request_workflow"]["details"] = "Agent coins or deposits were not updated after approval"
                return False
        else:
            print(f"Failed to get agent dashboard: {response.text}")
            test_results["sales_request_workflow"]["status"] = "Failed"
            test_results["sales_request_workflow"]["details"] = f"Failed to get agent dashboard: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during agent dashboard check: {str(e)}")
        test_results["sales_request_workflow"]["status"] = "Failed"
        test_results["sales_request_workflow"]["details"] = f"Connection error during agent dashboard check: {str(e)}"
        return False

def test_target_system():
    """Test the target system"""
    print_separator()
    print("Testing target system")
    
    if not tokens["admin"] or not tokens["agent"]:
        print("Cannot test target system without admin and agent tokens")
        test_results["target_system"]["status"] = "Skipped"
        test_results["target_system"]["details"] = "Missing admin or agent token"
        return False
    
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    # Step 1: Admin sets monthly target for agent
    print_step("Admin setting monthly target for agent")
    if not user_ids["agent"]:
        print("Cannot set target without agent ID")
        test_results["target_system"]["status"] = "Failed"
        test_results["target_system"]["details"] = "Agent ID not found"
        return False
    
    target_url = f"{BASE_URL}/admin/agents/{user_ids['agent']}/target"
    target_data = {
        "target_monthly": 5  # 5 deposits target
    }
    
    try:
        response = requests.put(target_url, json=target_data, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Target setting response: {json.dumps(response_data, indent=2)}")
            print("Target set successfully")
        else:
            print(f"Failed to set target: {response.text}")
            test_results["target_system"]["status"] = "Failed"
            test_results["target_system"]["details"] = f"Failed to set target: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during target setting: {str(e)}")
        test_results["target_system"]["status"] = "Failed"
        test_results["target_system"]["details"] = f"Connection error during target setting: {str(e)}"
        return False
    
    # Step 2: Agent checks dashboard to see achievement percentage
    print_step("Agent checking dashboard for achievement percentage")
    dashboard_url = f"{BASE_URL}/agent/dashboard"
    
    try:
        response = requests.get(dashboard_url, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            dashboard_data = response.json()
            print(f"Agent dashboard: {json.dumps(dashboard_data, indent=2)}")
            
            # Check if target and achievement percentage are included
            agent_info = dashboard_data.get("agent_info", {})
            target = agent_info.get("target_monthly")
            achievement = agent_info.get("achievement_percentage")
            
            if target is not None and achievement is not None:
                print(f"Target: {target}, Achievement: {achievement}%")
                test_results["target_system"]["status"] = "Success"
                test_results["target_system"]["details"] = "Successfully set and verified target system"
                return True
            else:
                print("Target or achievement percentage not found in dashboard")
                test_results["target_system"]["status"] = "Failed"
                test_results["target_system"]["details"] = "Target or achievement percentage not found in dashboard"
                return False
        else:
            print(f"Failed to get agent dashboard: {response.text}")
            test_results["target_system"]["status"] = "Failed"
            test_results["target_system"]["details"] = f"Failed to get agent dashboard: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during dashboard check: {str(e)}")
        test_results["target_system"]["status"] = "Failed"
        test_results["target_system"]["details"] = f"Connection error during dashboard check: {str(e)}"
        return False

def test_shop_reward_bag():
    """Test the shop and reward bag functionality"""
    print_separator()
    print("Testing shop and reward bag functionality")
    
    if not tokens["agent"] or not tokens["admin"]:
        print("Cannot test shop and reward bag without agent and admin tokens")
        test_results["shop_reward_bag"]["status"] = "Skipped"
        test_results["shop_reward_bag"]["details"] = "Missing agent or admin token"
        return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    
    # Step 1: Agent redeems a prize using coins
    print_step("Agent redeeming a prize")
    if not test_data["prize_id"]:
        print("Cannot redeem prize without prize ID")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = "Prize ID not found"
        return False
    
    redeem_url = f"{BASE_URL}/shop/redeem"
    redeem_data = {
        "prize_id": test_data["prize_id"]
    }
    
    try:
        response = requests.post(redeem_url, json=redeem_data, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Redemption response: {json.dumps(response_data, indent=2)}")
            print("Prize redeemed successfully")
        else:
            print(f"Failed to redeem prize: {response.text}")
            test_results["shop_reward_bag"]["status"] = "Failed"
            test_results["shop_reward_bag"]["details"] = f"Failed to redeem prize: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize redemption: {str(e)}")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = f"Connection error during prize redemption: {str(e)}"
        return False
    
    # Step 2: Verify prize goes to reward bag
    print_step("Checking agent's reward bag")
    reward_bag_url = f"{BASE_URL}/agent/reward-bag"
    
    try:
        response = requests.get(reward_bag_url, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            rewards = response.json()
            print(f"Found {len(rewards)} rewards in bag")
            
            # Find our redeemed prize
            redeemed_prize = None
            for reward in rewards:
                if reward.get("prize_id") == test_data["prize_id"]:
                    redeemed_prize = reward
                    test_data["reward_bag_item_id"] = reward.get("id")
                    break
            
            if redeemed_prize:
                print(f"Found our redeemed prize in reward bag: {json.dumps(redeemed_prize, indent=2)}")
            else:
                print("Our redeemed prize was not found in reward bag")
                test_results["shop_reward_bag"]["status"] = "Failed"
                test_results["shop_reward_bag"]["details"] = "Redeemed prize not found in reward bag"
                return False
        else:
            print(f"Failed to get reward bag: {response.text}")
            test_results["shop_reward_bag"]["status"] = "Failed"
            test_results["shop_reward_bag"]["details"] = f"Failed to get reward bag: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during reward bag check: {str(e)}")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = f"Connection error during reward bag check: {str(e)}"
        return False
    
    # Step 3: Agent requests to use the reward
    print_step("Agent requesting to use reward")
    if not test_data["reward_bag_item_id"]:
        print("Cannot request to use reward without reward ID")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = "Reward ID not found"
        return False
    
    use_request_url = f"{BASE_URL}/agent/reward-bag/{test_data['reward_bag_item_id']}/request-use"
    
    try:
        response = requests.post(use_request_url, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Use request response: {json.dumps(response_data, indent=2)}")
            print("Use request submitted successfully")
        else:
            print(f"Failed to submit use request: {response.text}")
            test_results["shop_reward_bag"]["status"] = "Failed"
            test_results["shop_reward_bag"]["details"] = f"Failed to submit use request: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during use request submission: {str(e)}")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = f"Connection error during use request submission: {str(e)}"
        return False
    
    # Step 4: Admin approves reward use request
    print_step("Admin checking pending reward requests")
    reward_requests_url = f"{BASE_URL}/admin/reward-requests"
    
    try:
        response = requests.get(reward_requests_url, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            requests_data = response.json()
            print(f"Found {len(requests_data)} pending reward requests")
            
            # Find our reward request
            our_request = None
            for req in requests_data:
                if req.get("id") == test_data["reward_bag_item_id"]:
                    our_request = req
                    break
            
            if our_request:
                print(f"Found our reward request: {json.dumps(our_request, indent=2)}")
                
                # Check if agent name is included
                if "agent_name" in our_request:
                    print(f"Agent name is included: {our_request['agent_name']}")
                else:
                    print("Agent name is NOT included in the reward request")
            else:
                print("Our reward request was not found")
                test_results["shop_reward_bag"]["status"] = "Failed"
                test_results["shop_reward_bag"]["details"] = "Reward use request not found in pending requests"
                return False
        else:
            print(f"Failed to get pending reward requests: {response.text}")
            test_results["shop_reward_bag"]["status"] = "Failed"
            test_results["shop_reward_bag"]["details"] = f"Failed to get pending reward requests: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during pending reward requests check: {str(e)}")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = f"Connection error during pending reward requests check: {str(e)}"
        return False
    
    # Step 5: Admin approves the reward use request
    print_step("Admin approving reward use request")
    approve_reward_url = f"{BASE_URL}/admin/reward-requests/{test_data['reward_bag_item_id']}/approve"
    
    try:
        response = requests.put(approve_reward_url, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Approval response: {json.dumps(response_data, indent=2)}")
            print("Reward use request approved successfully")
            
            test_results["shop_reward_bag"]["status"] = "Success"
            test_results["shop_reward_bag"]["details"] = "Successfully completed shop and reward bag workflow"
            return True
        else:
            print(f"Failed to approve reward use request: {response.text}")
            test_results["shop_reward_bag"]["status"] = "Failed"
            test_results["shop_reward_bag"]["details"] = f"Failed to approve reward use request: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during reward use approval: {str(e)}")
        test_results["shop_reward_bag"]["status"] = "Failed"
        test_results["shop_reward_bag"]["details"] = f"Connection error during reward use approval: {str(e)}"
        return False

def test_leaderboard():
    """Test the agent leaderboard"""
    print_separator()
    print("Testing agent leaderboard")
    
    if not tokens["agent"]:
        print("Cannot test leaderboard without agent token")
        test_results["leaderboard"]["status"] = "Skipped"
        test_results["leaderboard"]["details"] = "No agent token available"
        return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    # Check agent leaderboard endpoint
    print_step("Checking agent leaderboard")
    leaderboard_url = f"{BASE_URL}/agent/leaderboard"
    
    try:
        response = requests.get(leaderboard_url, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            leaderboard = response.json()
            print(f"Found {len(leaderboard)} agents in leaderboard")
            print(f"Leaderboard: {json.dumps(leaderboard, indent=2)}")
            
            # Check if our agent is in the leaderboard
            our_agent_found = False
            for entry in leaderboard:
                if entry.get("is_current_user", False):
                    our_agent_found = True
                    print(f"Found our agent in leaderboard: Rank {entry.get('rank')}")
                    break
            
            if our_agent_found:
                # Check if ranking is based on deposits
                is_sorted = True
                for i in range(1, len(leaderboard) - 1):
                    if leaderboard[i-1].get("deposits", 0) < leaderboard[i].get("deposits", 0):
                        is_sorted = False
                        break
                
                if is_sorted or len(leaderboard) <= 1:
                    print("Leaderboard is correctly sorted by deposits")
                    test_results["leaderboard"]["status"] = "Success"
                    test_results["leaderboard"]["details"] = "Successfully verified leaderboard functionality"
                    return True
                else:
                    print("Leaderboard is NOT correctly sorted by deposits")
                    test_results["leaderboard"]["status"] = "Failed"
                    test_results["leaderboard"]["details"] = "Leaderboard is not correctly sorted by deposits"
                    return False
            else:
                print("Our agent was not found in the leaderboard")
                test_results["leaderboard"]["status"] = "Failed"
                test_results["leaderboard"]["details"] = "Agent not found in leaderboard"
                return False
        else:
            print(f"Failed to get leaderboard: {response.text}")
            test_results["leaderboard"]["status"] = "Failed"
            test_results["leaderboard"]["details"] = f"Failed to get leaderboard: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during leaderboard check: {str(e)}")
        test_results["leaderboard"]["status"] = "Failed"
        test_results["leaderboard"]["details"] = f"Connection error during leaderboard check: {str(e)}"
        return False

def run_tests():
    """Run all tests in sequence"""
    print(f"Starting comprehensive backend tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API URL: {BASE_URL}")
    
    try:
        # Test basic connectivity first
        if not test_basic_connectivity():
            print("Basic connectivity test failed. Stopping tests.")
            return
        
        # Test authentication
        if not test_authentication():
            print("Authentication test failed. Stopping tests.")
            return
        
        # Test user info
        if not test_user_info():
            print("User info test failed. Continuing with other tests...")
        
        # Test shop management
        if not test_shop_management():
            print("Shop management test failed. Continuing with other tests...")
        
        # Test user management
        if not test_user_management():
            print("User management test failed. Continuing with other tests...")
        else:
            # Test sales request workflow
            if not test_sales_request_workflow():
                print("Sales request workflow test failed. Continuing with other tests...")
            
            # Test target system
            if not test_target_system():
                print("Target system test failed. Continuing with other tests...")
            
            # Test shop and reward bag
            if not test_shop_reward_bag():
                print("Shop and reward bag test failed. Continuing with other tests...")
            
            # Test leaderboard
            if not test_leaderboard():
                print("Leaderboard test failed. Continuing with other tests...")
    except Exception as e:
        print(f"Unexpected error during testing: {str(e)}")
        print(traceback.format_exc())
    
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
