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

# Store test data
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

def test_shop_reward_bag_with_affordable_prize():
    """Test the shop and reward bag functionality with a prize the agent can afford"""
    print_separator()
    print("TESTING SHOP AND REWARD BAG WITH AFFORDABLE PRIZE")
    print_separator()
    
    # Step 1: Login as Super Admin
    if not login_user(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, "super_admin"):
        print("Failed to login as Super Admin")
        return False
    
    super_admin_headers = {"Authorization": f"Bearer {tokens['super_admin']}"}
    
    # Step 2: Create a new admin and agent
    print_step("Creating test admin and agent")
    
    # Create admin
    admin_username = f"admin_{generate_random_string()}"
    admin_password = "Admin@123"
    test_data["admin_username"] = admin_username
    test_data["admin_password"] = admin_password
    
    create_admin_url = f"{BASE_URL}/super-admin/admins"
    admin_data = {
        "username": admin_username,
        "password": admin_password,
        "role": "admin",
        "name": "Shop Test Admin"
    }
    
    response = requests.post(create_admin_url, json=admin_data, headers=super_admin_headers)
    if response.status_code == 200:
        response_data = response.json()
        user_ids["admin"] = response_data.get("admin_id")
        print(f"Admin created with ID: {user_ids['admin']}")
    else:
        print(f"Failed to create admin: {response.text}")
        return False
    
    # Create agent
    agent_username = f"agent_{generate_random_string()}"
    agent_password = "Agent@123"
    test_data["agent_username"] = agent_username
    test_data["agent_password"] = agent_password
    
    create_agent_url = f"{BASE_URL}/super-admin/agents"
    agent_data = {
        "username": agent_username,
        "password": agent_password,
        "role": "agent",
        "name": "Shop Test Agent"
    }
    
    response = requests.post(create_agent_url, json=agent_data, headers=super_admin_headers)
    if response.status_code == 200:
        response_data = response.json()
        user_ids["agent"] = response_data.get("agent_id")
        print(f"Agent created with ID: {user_ids['agent']}")
    else:
        print(f"Failed to create agent: {response.text}")
        return False
    
    # Step 3: Create a low-cost prize (0.5 coins)
    print_step("Creating a low-cost prize (0.5 coins)")
    create_prize_url = f"{BASE_URL}/super-admin/prizes"
    prize_data = {
        "name": "Small Badge",
        "description": "A small badge that costs only 0.5 coins",
        "coin_cost": 0.5,
        "is_limited": False
    }
    
    response = requests.post(create_prize_url, json=prize_data, headers=super_admin_headers)
    if response.status_code == 200:
        response_data = response.json()
        test_data["prize_id"] = response_data.get("prize_id")
        print(f"Low-cost prize created with ID: {test_data['prize_id']}")
    else:
        print(f"Failed to create low-cost prize: {response.text}")
        return False
    
    # Step 4: Login as agent
    if not login_user(agent_username, agent_password, "agent"):
        print("Failed to login as agent")
        return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    # Step 5: Agent submits a sale request
    print_step("Agent submitting a sale request")
    sale_request_url = f"{BASE_URL}/agent/sale-request"
    sale_data = {
        "sale_amount": "100"  # $100 sale = 0.5 coins
    }
    
    response = requests.post(sale_request_url, json=sale_data, headers=agent_headers)
    if response.status_code == 200:
        print("Sale request submitted successfully")
    else:
        print(f"Failed to submit sale request: {response.text}")
        return False
    
    # Step 6: Login as admin
    if not login_user(admin_username, admin_password, "admin"):
        print("Failed to login as admin")
        return False
    
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    
    # Step 7: Admin approves the sale request
    print_step("Admin approving sale request")
    pending_requests_url = f"{BASE_URL}/admin/sale-requests"
    
    response = requests.get(pending_requests_url, headers=admin_headers)
    if response.status_code == 200:
        requests_data = response.json()
        print(f"Found {len(requests_data)} pending requests")
        
        # Find our agent's request
        for req in requests_data:
            if req.get("agent_id") == user_ids["agent"]:
                test_data["sale_request_id"] = req.get("id")
                print(f"Found our agent's request with ID: {test_data['sale_request_id']}")
                break
    else:
        print(f"Failed to get pending requests: {response.text}")
        return False
    
    if not test_data["sale_request_id"]:
        print("Could not find our agent's sale request")
        return False
    
    # Approve the request
    approve_url = f"{BASE_URL}/admin/sale-requests/{test_data['sale_request_id']}/approve"
    response = requests.put(approve_url, headers=admin_headers)
    if response.status_code == 200:
        print("Sale request approved successfully")
    else:
        print(f"Failed to approve sale request: {response.text}")
        return False
    
    # Step 8: Login as agent again
    if not login_user(agent_username, agent_password, "agent"):
        print("Failed to login as agent")
        return False
    
    agent_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    
    # Step 9: Verify agent has coins
    print_step("Verifying agent has coins")
    dashboard_url = f"{BASE_URL}/agent/dashboard"
    
    response = requests.get(dashboard_url, headers=agent_headers)
    if response.status_code == 200:
        dashboard_data = response.json()
        agent_info = dashboard_data.get("agent_info", {})
        coins = agent_info.get("coins", 0)
        print(f"Agent has {coins} coins")
        
        if coins < 0.5:
            print("Agent doesn't have enough coins for the prize")
            return False
    else:
        print(f"Failed to get agent dashboard: {response.text}")
        return False
    
    # Step 10: Agent redeems the low-cost prize
    print_step("Agent redeeming the low-cost prize")
    redeem_url = f"{BASE_URL}/shop/redeem"
    redeem_data = {
        "prize_id": test_data["prize_id"]
    }
    
    response = requests.post(redeem_url, json=redeem_data, headers=agent_headers)
    if response.status_code == 200:
        print("Prize redeemed successfully")
    else:
        print(f"Failed to redeem prize: {response.text}")
        return False
    
    # Step 11: Verify prize is in reward bag
    print_step("Checking agent's reward bag")
    reward_bag_url = f"{BASE_URL}/agent/reward-bag"
    
    response = requests.get(reward_bag_url, headers=agent_headers)
    if response.status_code == 200:
        rewards = response.json()
        print(f"Found {len(rewards)} rewards in bag")
        
        # Find our redeemed prize
        for reward in rewards:
            if reward.get("prize_id") == test_data["prize_id"]:
                test_data["reward_bag_item_id"] = reward.get("id")
                print(f"Found our redeemed prize in reward bag with ID: {test_data['reward_bag_item_id']}")
                break
        
        if not test_data["reward_bag_item_id"]:
            print("Our redeemed prize was not found in reward bag")
            return False
    else:
        print(f"Failed to get reward bag: {response.text}")
        return False
    
    # Step 12: Agent requests to use the reward
    print_step("Agent requesting to use reward")
    use_request_url = f"{BASE_URL}/agent/reward-bag/{test_data['reward_bag_item_id']}/request-use"
    
    response = requests.post(use_request_url, headers=agent_headers)
    if response.status_code == 200:
        print("Use request submitted successfully")
    else:
        print(f"Failed to submit use request: {response.text}")
        return False
    
    # Step 13: Admin approves reward use request
    if not login_user(admin_username, admin_password, "admin"):
        print("Failed to login as admin")
        return False
    
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    
    print_step("Admin checking pending reward requests")
    reward_requests_url = f"{BASE_URL}/admin/reward-requests"
    
    response = requests.get(reward_requests_url, headers=admin_headers)
    if response.status_code == 200:
        requests_data = response.json()
        print(f"Found {len(requests_data)} pending reward requests")
        
        # Find our reward request
        found = False
        for req in requests_data:
            if req.get("id") == test_data["reward_bag_item_id"]:
                found = True
                print(f"Found our reward request: {json.dumps(req, indent=2)}")
                break
        
        if not found:
            print("Our reward request was not found")
            return False
    else:
        print(f"Failed to get pending reward requests: {response.text}")
        return False
    
    # Approve the reward use request
    print_step("Admin approving reward use request")
    approve_reward_url = f"{BASE_URL}/admin/reward-requests/{test_data['reward_bag_item_id']}/approve"
    
    response = requests.put(approve_reward_url, headers=admin_headers)
    if response.status_code == 200:
        print("Reward use request approved successfully")
    else:
        print(f"Failed to approve reward use request: {response.text}")
        return False
    
    print_separator()
    print("✅ SHOP AND REWARD BAG TEST COMPLETED SUCCESSFULLY")
    print_separator()
    return True

if __name__ == "__main__":
    test_shop_reward_bag_with_affordable_prize()