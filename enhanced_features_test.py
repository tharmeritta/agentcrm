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
    "enhanced_shop_management": {"status": "Not tested", "details": ""},
    "advanced_user_credential_management": {"status": "Not tested", "details": ""},
    "super_admin_coin_requests": {"status": "Not tested", "details": ""},
    "coin_request_system": {"status": "Not tested", "details": ""},
    "complete_workflow": {"status": "Not tested", "details": ""}
}

print("=" * 80)
print("TESTING ENHANCED CRM SYSTEM FEATURES")
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
    "agent": None
}

# Store other test data
test_data = {
    "prize_id": None,
    "coin_request_id": None,
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

def test_enhanced_shop_management():
    """Test enhanced shop management (Super Admin)"""
    print_separator()
    print("Testing enhanced shop management")
    
    if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
        print("Failed to login as Super Admin")
        test_results["enhanced_shop_management"]["status"] = "Failed"
        test_results["enhanced_shop_management"]["details"] = "Failed to login as Super Admin"
        return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 1: Create a prize with POST /api/super-admin/prizes
    print_step("Creating a prize")
    create_prize_url = f"{BASE_URL}/super-admin/prizes"
    prize_data = {
        "name": "Test Prize",
        "description": "Prize for testing",
        "coin_cost": 1.0,
        "is_limited": False
    }
    
    try:
        response = requests.post(create_prize_url, json=prize_data, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Prize creation response: {json.dumps(response_data, indent=2)}")
            
            if "prize_id" in response_data:
                test_data["prize_id"] = response_data["prize_id"]
                print(f"Prize created with ID: {test_data['prize_id']}")
            else:
                print("Prize created but no ID was returned")
                test_results["enhanced_shop_management"]["status"] = "Failed"
                test_results["enhanced_shop_management"]["details"] = "Prize created but no ID was returned"
                return False
        else:
            print(f"Failed to create prize: {response.text}")
            test_results["enhanced_shop_management"]["status"] = "Failed"
            test_results["enhanced_shop_management"]["details"] = f"Failed to create prize: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize creation: {str(e)}")
        test_results["enhanced_shop_management"]["status"] = "Failed"
        test_results["enhanced_shop_management"]["details"] = f"Connection error during prize creation: {str(e)}"
        return False
    
    # Step 2: Edit prize with PUT /api/super-admin/prizes/{prize_id}
    print_step("Editing the prize")
    if not test_data["prize_id"]:
        print("Cannot edit prize without prize ID")
        test_results["enhanced_shop_management"]["status"] = "Failed"
        test_results["enhanced_shop_management"]["details"] = "Prize ID not found"
        return False
    
    edit_prize_url = f"{BASE_URL}/super-admin/prizes/{test_data['prize_id']}"
    edit_prize_data = {
        "name": "Updated Test Prize",
        "coin_cost": 0.5
    }
    
    try:
        response = requests.put(edit_prize_url, json=edit_prize_data, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Prize edit response: {json.dumps(response_data, indent=2)}")
            print("Prize edited successfully")
        else:
            print(f"Failed to edit prize: {response.text}")
            test_results["enhanced_shop_management"]["status"] = "Failed"
            test_results["enhanced_shop_management"]["details"] = f"Failed to edit prize: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize editing: {str(e)}")
        test_results["enhanced_shop_management"]["status"] = "Failed"
        test_results["enhanced_shop_management"]["details"] = f"Connection error during prize editing: {str(e)}"
        return False
    
    # Step 3: Verify prize changes persist
    print_step("Verifying prize changes")
    get_prizes_url = f"{BASE_URL}/super-admin/prizes"
    
    try:
        response = requests.get(get_prizes_url, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            prizes = response.json()
            print(f"Found {len(prizes)} prizes")
            
            # Find our edited prize
            edited_prize = None
            for prize in prizes:
                if prize.get("id") == test_data["prize_id"]:
                    edited_prize = prize
                    break
            
            if edited_prize:
                print(f"Found our edited prize: {json.dumps(edited_prize, indent=2)}")
                
                # Verify changes were applied
                if edited_prize.get("name") == "Updated Test Prize" and edited_prize.get("coin_cost") == 0.5:
                    print("Prize changes were successfully applied")
                    test_results["enhanced_shop_management"]["status"] = "Success"
                    test_results["enhanced_shop_management"]["details"] = "Successfully created and edited prize"
                    return True
                else:
                    print("Prize changes were not applied correctly")
                    test_results["enhanced_shop_management"]["status"] = "Failed"
                    test_results["enhanced_shop_management"]["details"] = "Prize changes were not applied correctly"
                    return False
            else:
                print("Our edited prize was not found")
                test_results["enhanced_shop_management"]["status"] = "Failed"
                test_results["enhanced_shop_management"]["details"] = "Edited prize not found in prizes list"
                return False
        else:
            print(f"Failed to get prizes: {response.text}")
            test_results["enhanced_shop_management"]["status"] = "Failed"
            test_results["enhanced_shop_management"]["details"] = f"Failed to get prizes: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during prize verification: {str(e)}")
        test_results["enhanced_shop_management"]["status"] = "Failed"
        test_results["enhanced_shop_management"]["details"] = f"Connection error during prize verification: {str(e)}"
        return False

def test_advanced_user_credential_management():
    """Test advanced user credential management"""
    print_separator()
    print("Testing advanced user credential management")
    
    if not tokens["super_admin"]:
        if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
            print("Failed to login as Super Admin")
            test_results["advanced_user_credential_management"]["status"] = "Failed"
            test_results["advanced_user_credential_management"]["details"] = "Failed to login as Super Admin"
            return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 1: Test GET /api/super-admin/users/admins - separate admin view
    print_step("Getting separate admin view")
    admins_url = f"{BASE_URL}/super-admin/users/admins"
    
    try:
        response = requests.get(admins_url, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            admins = response.json()
            print(f"Found {len(admins)} admins")
            print(f"Sample admin data: {json.dumps(admins[0] if admins else {}, indent=2)}")
            
            # Check if has_password field is present
            if admins and "has_password" in admins[0]:
                print("Admin view includes has_password field")
            else:
                print("Admin view does not include has_password field")
                if not admins:
                    print("No admins found, creating one for testing")
                    
                    # Create an admin user
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
                        if response.status_code == 200:
                            response_data = response.json()
                            if "admin_id" in response_data:
                                user_ids["admin"] = response_data["admin_id"]
                                print(f"Admin created with ID: {user_ids['admin']}")
                            else:
                                print("Admin created but no ID was returned")
                        else:
                            print(f"Failed to create admin: {response.text}")
                    except Exception as e:
                        print(f"Error creating admin: {str(e)}")
        else:
            print(f"Failed to get admins: {response.text}")
            test_results["advanced_user_credential_management"]["status"] = "Failed"
            test_results["advanced_user_credential_management"]["details"] = f"Failed to get admins: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during admin view: {str(e)}")
        test_results["advanced_user_credential_management"]["status"] = "Failed"
        test_results["advanced_user_credential_management"]["details"] = f"Connection error during admin view: {str(e)}"
        return False
    
    # Step 2: Test GET /api/super-admin/users/agents - separate agent view
    print_step("Getting separate agent view")
    agents_url = f"{BASE_URL}/super-admin/users/agents"
    
    try:
        response = requests.get(agents_url, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            agents = response.json()
            print(f"Found {len(agents)} agents")
            print(f"Sample agent data: {json.dumps(agents[0] if agents else {}, indent=2)}")
            
            # Check if has_password field is present
            if agents and "has_password" in agents[0]:
                print("Agent view includes has_password field")
            else:
                print("Agent view does not include has_password field")
                if not agents:
                    print("No agents found, creating one for testing")
                    
                    # Create an agent user
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
                        if response.status_code == 200:
                            response_data = response.json()
                            if "agent_id" in response_data:
                                user_ids["agent"] = response_data["agent_id"]
                                print(f"Agent created with ID: {user_ids['agent']}")
                            else:
                                print("Agent created but no ID was returned")
                        else:
                            print(f"Failed to create agent: {response.text}")
                    except Exception as e:
                        print(f"Error creating agent: {str(e)}")
        else:
            print(f"Failed to get agents: {response.text}")
            test_results["advanced_user_credential_management"]["status"] = "Failed"
            test_results["advanced_user_credential_management"]["details"] = f"Failed to get agents: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during agent view: {str(e)}")
        test_results["advanced_user_credential_management"]["status"] = "Failed"
        test_results["advanced_user_credential_management"]["details"] = f"Connection error during agent view: {str(e)}"
        return False
    
    # Step 3: Test PUT /api/super-admin/users/{user_id}/credentials - edit username, password, name
    print_step("Editing user credentials")
    
    # Make sure we have a user ID to edit
    user_id_to_edit = user_ids.get("agent")
    if not user_id_to_edit:
        print("No agent ID available for credential editing test")
        
        # Try to get an agent ID from the list
        if agents and len(agents) > 0:
            user_id_to_edit = agents[0].get("id")
            print(f"Using agent ID from list: {user_id_to_edit}")
        else:
            print("Cannot proceed with credential editing test without a user ID")
            test_results["advanced_user_credential_management"]["status"] = "Failed"
            test_results["advanced_user_credential_management"]["details"] = "No user ID available for credential editing"
            return False
    
    edit_credentials_url = f"{BASE_URL}/super-admin/users/{user_id_to_edit}/credentials"
    new_username = f"edited_{generate_random_string()}"
    new_password = "Edited@123"
    new_name = "Edited User Name"
    
    edit_data = {
        "username": new_username,
        "password": new_password,
        "name": new_name
    }
    
    try:
        response = requests.put(edit_credentials_url, json=edit_data, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Credential edit response: {json.dumps(response_data, indent=2)}")
            print("User credentials edited successfully")
            
            # Verify changes by logging in with new credentials
            if login_user(new_username, new_password, "agent"):
                print("Successfully logged in with new credentials")
                
                # Check if name was updated
                agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
                me_url = f"{BASE_URL}/auth/me"
                
                try:
                    me_response = requests.get(me_url, headers=agent_headers)
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        if me_data.get("name") == new_name:
                            print("Name was successfully updated")
                            test_results["advanced_user_credential_management"]["status"] = "Success"
                            test_results["advanced_user_credential_management"]["details"] = "Successfully edited and verified user credentials"
                            return True
                        else:
                            print(f"Name was not updated. Expected: {new_name}, Got: {me_data.get('name')}")
                    else:
                        print(f"Failed to get user info: {me_response.text}")
                except Exception as e:
                    print(f"Error checking user info: {str(e)}")
            else:
                print("Failed to login with new credentials")
                test_results["advanced_user_credential_management"]["status"] = "Failed"
                test_results["advanced_user_credential_management"]["details"] = "Failed to login with new credentials"
                return False
        else:
            print(f"Failed to edit credentials: {response.text}")
            test_results["advanced_user_credential_management"]["status"] = "Failed"
            test_results["advanced_user_credential_management"]["details"] = f"Failed to edit credentials: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during credential editing: {str(e)}")
        test_results["advanced_user_credential_management"]["status"] = "Failed"
        test_results["advanced_user_credential_management"]["details"] = f"Connection error during credential editing: {str(e)}"
        return False

def test_super_admin_coin_requests():
    """Test Super Admin access to coin requests"""
    print_separator()
    print("Testing Super Admin access to coin requests")
    
    if not tokens["super_admin"]:
        if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
            print("Failed to login as Super Admin")
            test_results["super_admin_coin_requests"]["status"] = "Failed"
            test_results["super_admin_coin_requests"]["details"] = "Failed to login as Super Admin"
            return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 1: Test GET /api/admin/coin-requests as Super Admin
    print_step("Super Admin accessing coin requests")
    coin_requests_url = f"{BASE_URL}/admin/coin-requests"
    
    try:
        response = requests.get(coin_requests_url, headers=super_admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            requests_data = response.json()
            print(f"Found {len(requests_data)} coin requests")
            print(f"Sample coin request data: {json.dumps(requests_data[0] if requests_data else {}, indent=2)}")
            
            # If no coin requests found, we'll create one in the next test
            if not requests_data:
                print("No coin requests found. Will create one in the next test.")
        else:
            print(f"Failed to get coin requests: {response.text}")
            test_results["super_admin_coin_requests"]["status"] = "Failed"
            test_results["super_admin_coin_requests"]["details"] = f"Failed to get coin requests: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during coin requests access: {str(e)}")
        test_results["super_admin_coin_requests"]["status"] = "Failed"
        test_results["super_admin_coin_requests"]["details"] = f"Connection error during coin requests access: {str(e)}"
        return False
    
    # For now, mark as success - we'll test approval in the complete workflow
    test_results["super_admin_coin_requests"]["status"] = "Success"
    test_results["super_admin_coin_requests"]["details"] = "Super Admin can access coin requests"
    return True

def test_coin_request_system():
    """Test the renamed 'Coin Request' system"""
    print_separator()
    print("Testing coin request system")
    
    # Make sure we have an agent token
    if not tokens["agent"]:
        # Try to login with the agent credentials we might have created
        if test_data["agent_username"] and test_data["agent_password"]:
            if not login_user(test_data["agent_username"], test_data["agent_password"], "agent"):
                print("Failed to login as agent with stored credentials")
                
                # Create a new agent
                if not tokens["super_admin"]:
                    if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
                        print("Failed to login as Super Admin")
                        test_results["coin_request_system"]["status"] = "Failed"
                        test_results["coin_request_system"]["details"] = "Failed to login as Super Admin to create agent"
                        return False
                
                super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
                
                # Create an agent user
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
                    if response.status_code == 200:
                        response_data = response.json()
                        if "agent_id" in response_data:
                            user_ids["agent"] = response_data["agent_id"]
                            print(f"Agent created with ID: {user_ids['agent']}")
                            
                            # Login with new agent
                            if not login_user(agent_username, agent_password, "agent"):
                                print("Failed to login with newly created agent")
                                test_results["coin_request_system"]["status"] = "Failed"
                                test_results["coin_request_system"]["details"] = "Failed to login with newly created agent"
                                return False
                        else:
                            print("Agent created but no ID was returned")
                            test_results["coin_request_system"]["status"] = "Failed"
                            test_results["coin_request_system"]["details"] = "Agent created but no ID was returned"
                            return False
                    else:
                        print(f"Failed to create agent: {response.text}")
                        test_results["coin_request_system"]["status"] = "Failed"
                        test_results["coin_request_system"]["details"] = f"Failed to create agent: {response.text}"
                        return False
                except Exception as e:
                    print(f"Error creating agent: {str(e)}")
                    test_results["coin_request_system"]["status"] = "Failed"
                    test_results["coin_request_system"]["details"] = f"Error creating agent: {str(e)}"
                    return False
        else:
            print("No agent credentials available")
            test_results["coin_request_system"]["status"] = "Failed"
            test_results["coin_request_system"]["details"] = "No agent credentials available"
            return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    # Step 1: Test POST /api/agent/coin-request - agent submits coin request
    print_step("Agent submitting coin request")
    coin_request_url = f"{BASE_URL}/agent/coin-request"
    coin_request_data = {
        "sale_amount": "100"  # $100 sale
    }
    
    try:
        response = requests.post(coin_request_url, json=coin_request_data, headers=agent_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Coin request response: {json.dumps(response_data, indent=2)}")
            print("Coin request submitted successfully")
        else:
            print(f"Failed to submit coin request: {response.text}")
            test_results["coin_request_system"]["status"] = "Failed"
            test_results["coin_request_system"]["details"] = f"Failed to submit coin request: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during coin request submission: {str(e)}")
        test_results["coin_request_system"]["status"] = "Failed"
        test_results["coin_request_system"]["details"] = f"Connection error during coin request submission: {str(e)}"
        return False
    
    # Step 2: Make sure we have an admin or super admin token to check coin requests
    admin_headers = None
    if tokens["admin"]:
        admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    elif tokens["super_admin"]:
        admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    else:
        if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
            print("Failed to login as Super Admin")
            test_results["coin_request_system"]["status"] = "Failed"
            test_results["coin_request_system"]["details"] = "Failed to login as Super Admin to check coin requests"
            return False
        admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 3: Test GET /api/admin/coin-requests - admin sees coin requests with agent names
    print_step("Admin checking coin requests")
    coin_requests_url = f"{BASE_URL}/admin/coin-requests"
    
    try:
        response = requests.get(coin_requests_url, headers=admin_headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            requests_data = response.json()
            print(f"Found {len(requests_data)} coin requests")
            
            # Find our agent's request
            agent_request = None
            for req in requests_data:
                if user_ids["agent"] and req.get("agent_id") == user_ids["agent"]:
                    agent_request = req
                    test_data["coin_request_id"] = req.get("id")
                    break
            
            if agent_request:
                print(f"Found our agent's coin request: {json.dumps(agent_request, indent=2)}")
                
                # Check if agent name is included
                if "agent_name" in agent_request:
                    print(f"Agent name is included: {agent_request['agent_name']}")
                else:
                    print("Agent name is NOT included in the request")
                    test_results["coin_request_system"]["status"] = "Failed"
                    test_results["coin_request_system"]["details"] = "Agent name not included in coin request"
                    return False
            else:
                print("Our agent's coin request was not found")
                test_results["coin_request_system"]["status"] = "Failed"
                test_results["coin_request_system"]["details"] = "Agent's coin request not found in pending requests"
                return False
        else:
            print(f"Failed to get coin requests: {response.text}")
            test_results["coin_request_system"]["status"] = "Failed"
            test_results["coin_request_system"]["details"] = f"Failed to get coin requests: {response.text}"
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during coin requests check: {str(e)}")
        test_results["coin_request_system"]["status"] = "Failed"
        test_results["coin_request_system"]["details"] = f"Connection error during coin requests check: {str(e)}"
        return False
    
    # For now, mark as success - we'll test approval in the complete workflow
    test_results["coin_request_system"]["status"] = "Success"
    test_results["coin_request_system"]["details"] = "Successfully submitted and verified coin request"
    return True

def test_complete_workflow():
    """Test the complete workflow"""
    print_separator()
    print("Testing complete workflow")
    
    # Step 1: Super Admin creates a prize (name: "Test Prize", cost: 1 coin)
    print_step("Super Admin creating a prize")
    
    if not tokens["super_admin"]:
        if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
            print("Failed to login as Super Admin")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = "Failed to login as Super Admin"
            return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    create_prize_url = f"{BASE_URL}/super-admin/prizes"
    prize_data = {
        "name": "Workflow Test Prize",
        "description": "Prize for workflow testing",
        "coin_cost": 1.0,
        "is_limited": False
    }
    
    try:
        response = requests.post(create_prize_url, json=prize_data, headers=super_admin_headers)
        if response.status_code == 200:
            response_data = response.json()
            if "prize_id" in response_data:
                test_data["prize_id"] = response_data["prize_id"]
                print(f"Prize created with ID: {test_data['prize_id']}")
            else:
                print("Prize created but no ID was returned")
                test_results["complete_workflow"]["status"] = "Failed"
                test_results["complete_workflow"]["details"] = "Prize created but no ID was returned"
                return False
        else:
            print(f"Failed to create prize: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to create prize: {response.text}"
            return False
    except Exception as e:
        print(f"Error creating prize: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error creating prize: {str(e)}"
        return False
    
    # Step 2: Super Admin edits the prize (change cost to 0.5 coins)
    print_step("Super Admin editing the prize")
    
    edit_prize_url = f"{BASE_URL}/super-admin/prizes/{test_data['prize_id']}"
    edit_prize_data = {
        "coin_cost": 0.5
    }
    
    try:
        response = requests.put(edit_prize_url, json=edit_prize_data, headers=super_admin_headers)
        if response.status_code != 200:
            print(f"Failed to edit prize: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to edit prize: {response.text}"
            return False
    except Exception as e:
        print(f"Error editing prize: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error editing prize: {str(e)}"
        return False
    
    # Step 3: Super Admin creates an agent account
    print_step("Super Admin creating an agent account")
    
    agent_username = f"workflow_agent_{generate_random_string()}"
    agent_password = "Agent@123"
    
    create_agent_url = f"{BASE_URL}/super-admin/agents"
    agent_data = {
        "username": agent_username,
        "password": agent_password,
        "role": "agent",
        "name": "Workflow Test Agent"
    }
    
    try:
        response = requests.post(create_agent_url, json=agent_data, headers=super_admin_headers)
        if response.status_code == 200:
            response_data = response.json()
            if "agent_id" in response_data:
                user_ids["agent"] = response_data["agent_id"]
                print(f"Agent created with ID: {user_ids['agent']}")
                
                # Login as the new agent
                if not login_user(agent_username, agent_password, "agent"):
                    print("Failed to login as newly created agent")
                    test_results["complete_workflow"]["status"] = "Failed"
                    test_results["complete_workflow"]["details"] = "Failed to login as newly created agent"
                    return False
            else:
                print("Agent created but no ID was returned")
                test_results["complete_workflow"]["status"] = "Failed"
                test_results["complete_workflow"]["details"] = "Agent created but no ID was returned"
                return False
        else:
            print(f"Failed to create agent: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to create agent: {response.text}"
            return False
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error creating agent: {str(e)}"
        return False
    
    # Step 4: Agent submits coin request ($100 = 0.5 coins + 1 deposit)
    print_step("Agent submitting coin request")
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    coin_request_url = f"{BASE_URL}/agent/coin-request"
    coin_request_data = {
        "sale_amount": "100"  # $100 sale
    }
    
    try:
        response = requests.post(coin_request_url, json=coin_request_data, headers=agent_headers)
        if response.status_code != 200:
            print(f"Failed to submit coin request: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to submit coin request: {response.text}"
            return False
    except Exception as e:
        print(f"Error submitting coin request: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error submitting coin request: {str(e)}"
        return False
    
    # Step 5: Super Admin sees and approves the coin request in "Coin Requests" tab
    print_step("Super Admin approving coin request")
    
    # First, get the coin request ID
    coin_requests_url = f"{BASE_URL}/admin/coin-requests"
    
    try:
        response = requests.get(coin_requests_url, headers=super_admin_headers)
        if response.status_code == 200:
            requests_data = response.json()
            
            # Find our agent's request
            agent_request = None
            for req in requests_data:
                if req.get("agent_id") == user_ids["agent"]:
                    agent_request = req
                    test_data["coin_request_id"] = req.get("id")
                    break
            
            if not agent_request:
                print("Our agent's coin request was not found")
                test_results["complete_workflow"]["status"] = "Failed"
                test_results["complete_workflow"]["details"] = "Agent's coin request not found in pending requests"
                return False
        else:
            print(f"Failed to get coin requests: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to get coin requests: {response.text}"
            return False
    except Exception as e:
        print(f"Error getting coin requests: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error getting coin requests: {str(e)}"
        return False
    
    # Now approve the coin request
    approve_url = f"{BASE_URL}/admin/coin-requests/{test_data['coin_request_id']}/approve"
    
    try:
        response = requests.put(approve_url, headers=super_admin_headers)
        if response.status_code != 200:
            print(f"Failed to approve coin request: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to approve coin request: {response.text}"
            return False
    except Exception as e:
        print(f"Error approving coin request: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error approving coin request: {str(e)}"
        return False
    
    # Step 6: Verify agent receives 0.5 coins and 1 deposit
    print_step("Verifying agent received coins and deposits")
    
    agent_dashboard_url = f"{BASE_URL}/agent/dashboard"
    
    try:
        response = requests.get(agent_dashboard_url, headers=agent_headers)
        if response.status_code == 200:
            dashboard_data = response.json()
            agent_info = dashboard_data.get("agent_info", {})
            coins = agent_info.get("coins", 0)
            deposits = agent_info.get("deposits", 0)
            
            print(f"Agent coins: {coins}, deposits: {deposits}")
            
            if coins == 0.5 and deposits == 1:
                print("Agent received correct coins and deposits")
            else:
                print(f"Agent did not receive correct coins and deposits. Expected: 0.5 coins, 1 deposit. Got: {coins} coins, {deposits} deposits")
                test_results["complete_workflow"]["status"] = "Failed"
                test_results["complete_workflow"]["details"] = f"Agent did not receive correct coins and deposits. Expected: 0.5 coins, 1 deposit. Got: {coins} coins, {deposits} deposits"
                return False
        else:
            print(f"Failed to get agent dashboard: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to get agent dashboard: {response.text}"
            return False
    except Exception as e:
        print(f"Error getting agent dashboard: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error getting agent dashboard: {str(e)}"
        return False
    
    # Step 7: Agent redeems the prize with coins
    print_step("Agent redeeming the prize")
    
    redeem_url = f"{BASE_URL}/shop/redeem"
    redeem_data = {
        "prize_id": test_data["prize_id"]
    }
    
    try:
        response = requests.post(redeem_url, json=redeem_data, headers=agent_headers)
        if response.status_code != 200:
            print(f"Failed to redeem prize: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to redeem prize: {response.text}"
            return False
    except Exception as e:
        print(f"Error redeeming prize: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error redeeming prize: {str(e)}"
        return False
    
    # Step 8: Test credential editing - change agent's username/name
    print_step("Editing agent's credentials")
    
    edit_credentials_url = f"{BASE_URL}/super-admin/users/{user_ids['agent']}/credentials"
    new_username = f"edited_{generate_random_string()}"
    new_password = "Edited@123"
    new_name = "Edited Agent Name"
    
    edit_data = {
        "username": new_username,
        "password": new_password,
        "name": new_name
    }
    
    try:
        response = requests.put(edit_credentials_url, json=edit_data, headers=super_admin_headers)
        if response.status_code != 200:
            print(f"Failed to edit credentials: {response.text}")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = f"Failed to edit credentials: {response.text}"
            return False
        
        # Verify by logging in with new credentials
        if login_user(new_username, new_password, "agent"):
            print("Successfully logged in with new credentials")
            
            # Check if name was updated
            agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
            me_url = f"{BASE_URL}/auth/me"
            
            try:
                me_response = requests.get(me_url, headers=agent_headers)
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    if me_data.get("name") == new_name:
                        print("Name was successfully updated")
                    else:
                        print(f"Name was not updated. Expected: {new_name}, Got: {me_data.get('name')}")
                        test_results["complete_workflow"]["status"] = "Failed"
                        test_results["complete_workflow"]["details"] = f"Name was not updated. Expected: {new_name}, Got: {me_data.get('name')}"
                        return False
                else:
                    print(f"Failed to get user info: {me_response.text}")
                    test_results["complete_workflow"]["status"] = "Failed"
                    test_results["complete_workflow"]["details"] = f"Failed to get user info: {me_response.text}"
                    return False
            except Exception as e:
                print(f"Error checking user info: {str(e)}")
                test_results["complete_workflow"]["status"] = "Failed"
                test_results["complete_workflow"]["details"] = f"Error checking user info: {str(e)}"
                return False
        else:
            print("Failed to login with new credentials")
            test_results["complete_workflow"]["status"] = "Failed"
            test_results["complete_workflow"]["details"] = "Failed to login with new credentials"
            return False
    except Exception as e:
        print(f"Error editing credentials: {str(e)}")
        test_results["complete_workflow"]["status"] = "Failed"
        test_results["complete_workflow"]["details"] = f"Error editing credentials: {str(e)}"
        return False
    
    # All steps completed successfully
    test_results["complete_workflow"]["status"] = "Success"
    test_results["complete_workflow"]["details"] = "Successfully completed the entire workflow"
    return True

def run_tests():
    """Run all tests in sequence"""
    print(f"Starting enhanced feature tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API URL: {BASE_URL}")
    
    try:
        # Test enhanced shop management
        test_enhanced_shop_management()
        
        # Test advanced user credential management
        test_advanced_user_credential_management()
        
        # Test Super Admin access to coin requests
        test_super_admin_coin_requests()
        
        # Test coin request system
        test_coin_request_system()
        
        # Test complete workflow
        test_complete_workflow()
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