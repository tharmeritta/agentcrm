from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
import ssl
import certifi

mongo_url = os.environ['MONGO_URL']
client = None
db = None

async def get_database():
    global client, db
    if client is None:
        try:
            # Try MongoDB Atlas connection first
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                tlsAllowInvalidCertificates=True
            )
            db = client[os.environ.get('DB_NAME', 'agent_crm')]
            # Test connection
            await client.admin.command('ping')
            print("MongoDB Atlas connected successfully!")
        except Exception as e:
            print(f"MongoDB Atlas connection failed: {e}")
            try:
                # Fall back to local MongoDB
                client = AsyncIOMotorClient("mongodb://localhost:27017")
                db = client[os.environ.get('DB_NAME', 'agent_crm')]
                # Test local connection
                await client.admin.command('ping')
                print("Connected to local MongoDB instead")
            except Exception as local_e:
                print(f"Local MongoDB connection also failed: {local_e}")
                client = None
                db = None
                return None
    return db

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-fallback-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    AGENT = "agent"

class SaleAmount(str, Enum):
    SMALL = "100"
    MEDIUM = "250"
    LARGE = "500"

# Models
class UserBase(BaseModel):
    username: str
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    created_by: Optional[str] = None
    target_monthly: Optional[float] = 0.0
    is_active: bool = True

class Agent(User):
    coins: float = 0.0
    deposits: float = 0.0
    total_sales: float = 0.0
    can_access_shop: bool = True
    last_quarter_reset: Optional[datetime] = None
    target_monthly: float = 0.0

class SaleRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    sale_amount: SaleAmount
    coins_requested: float
    deposits_requested: float
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class Prize(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    coin_cost: float
    is_limited: bool = False
    quantity_available: Optional[int] = None
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RewardBagItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    prize_id: str
    prize_name: str
    status: str = "unused"  # unused, pending_use, used
    redeemed_at: datetime = Field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    approved_by: Optional[str] = None

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    user = await database.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert ObjectId to string to avoid serialization issues
    if "_id" in user:
        user["_id"] = str(user["_id"])
    
    return user

def require_role(required_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in required_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

def convert_objectid_to_string(document):
    """Convert MongoDB ObjectId fields to strings for JSON serialization"""
    if isinstance(document, dict):
        if "_id" in document:
            document["_id"] = str(document["_id"])
        return document
    elif isinstance(document, list):
        return [convert_objectid_to_string(doc) for doc in document]
    return document

def calculate_coins_and_deposits(sale_amount: str):
    amounts = {
        "100": {"coins": 0.5, "deposits": 1},
        "250": {"coins": 1, "deposits": 1.5},
        "500": {"coins": 3, "deposits": 3}
    }
    return amounts.get(sale_amount, {"coins": 0, "deposits": 0})

# Initialize database with super admin
async def initialize_super_admin():
    # Get database connection first
    database = await get_database()
    if database is None:
        print("Failed to initialize database connection")
        return
        
    existing_super_admin = await database.users.find_one({"role": "super_admin"})
    if not existing_super_admin:
        super_admin = User(
            username="tharme.ritta",
            role=UserRole.SUPER_ADMIN,
            name="Super Administrator",
            is_active=True
        )
        super_admin_dict = super_admin.dict()
        super_admin_dict["password_hash"] = hash_password("Tharme@789")
        await database.users.insert_one(super_admin_dict)
        print("Super Admin created successfully")

# Routes
@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    user = await database.users.find_one({"username": login_data.username})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    token = create_jwt_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "name": user.get("name", "")
        }
    }

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"],
        "name": current_user.get("name", ""),
        "coins": current_user.get("coins", 0) if current_user["role"] == "agent" else None,
        "deposits": current_user.get("deposits", 0) if current_user["role"] == "agent" else None
    }

# Super Admin Routes
@api_router.get("/super-admin/admins")
async def get_all_admins(current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    admins = await database.users.find({"role": "admin"}).to_list(1000)
    return convert_objectid_to_string(admins)

@api_router.get("/super-admin/all-users")
async def get_all_users(current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Get all users except super_admin
    users = await database.users.find({"role": {"$in": ["admin", "agent"]}}).to_list(1000)
    
    # Include credentials for super admin view
    for user in users:
        # Keep password_hash for super admin but don't send it in response
        # We'll return a placeholder indicating password exists
        user["has_password"] = bool(user.get("password_hash"))
        user.pop("password_hash", None)
    
    return convert_objectid_to_string(users)

@api_router.get("/super-admin/users/admins")
async def get_admin_users_with_credentials(current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    admins = await database.users.find({"role": "admin"}).to_list(1000)
    
    # Format for credentials view
    for admin in admins:
        admin["has_password"] = bool(admin.get("password_hash"))
        admin.pop("password_hash", None)
    
    return convert_objectid_to_string(admins)

@api_router.get("/super-admin/users/agents")
async def get_agent_users_with_credentials(current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    agents = await database.users.find({"role": "agent"}).to_list(1000)
    
    # Format for credentials view
    for agent in agents:
        agent["has_password"] = bool(agent.get("password_hash"))
        agent.pop("password_hash", None)
    
    return convert_objectid_to_string(agents)

@api_router.post("/super-admin/agents")
async def create_agent_by_super_admin(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    existing_user = await database.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_agent = Agent(
        username=user_data.username,
        role=UserRole.AGENT,
        name=user_data.name or user_data.username,
        created_by=current_user["id"]
    )
    agent_dict = new_agent.dict()
    agent_dict["password_hash"] = hash_password(user_data.password)
    
    await database.users.insert_one(agent_dict)
    return {"message": "Agent created successfully", "agent_id": agent_dict["id"]}

# Shop Management - Super Admin Only
@api_router.get("/super-admin/prizes")
async def get_all_prizes(current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    prizes = await database.prizes.find({}).to_list(1000)
    return convert_objectid_to_string(prizes)

@api_router.post("/super-admin/prizes")
async def create_prize(prize_data: dict, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    new_prize = Prize(
        name=prize_data.get("name"),
        description=prize_data.get("description", ""),
        coin_cost=prize_data.get("coin_cost"),
        is_limited=prize_data.get("is_limited", False),
        quantity_available=prize_data.get("quantity_available"),
        created_by=current_user["id"]
    )
    
    await database.prizes.insert_one(new_prize.dict())
    return {"message": "Prize created successfully", "prize_id": new_prize.id}

@api_router.put("/super-admin/prizes/{prize_id}")
async def update_prize(prize_id: str, prize_data: dict, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    update_data = {}
    if "name" in prize_data:
        update_data["name"] = prize_data["name"]
    if "description" in prize_data:
        update_data["description"] = prize_data["description"]
    if "coin_cost" in prize_data:
        update_data["coin_cost"] = prize_data["coin_cost"]
    if "is_limited" in prize_data:
        update_data["is_limited"] = prize_data["is_limited"]
    if "quantity_available" in prize_data:
        update_data["quantity_available"] = prize_data["quantity_available"]
    if "is_active" in prize_data:
        update_data["is_active"] = prize_data["is_active"]
    
    result = await database.prizes.update_one({"id": prize_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prize not found")
    
    return {"message": "Prize updated successfully"}

# User Credential Management
@api_router.put("/super-admin/users/{user_id}/credentials")
async def update_user_credentials(user_id: str, update_data: dict, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    user = await database.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent editing super admin
    if user.get("role") == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot edit super admin credentials")
    
    # Build update data
    updates = {}
    if "username" in update_data and update_data["username"]:
        # Check if username already exists
        existing = await database.users.find_one({"username": update_data["username"], "id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        updates["username"] = update_data["username"]
    
    if "password" in update_data and update_data["password"]:
        updates["password_hash"] = hash_password(update_data["password"])
    
    if "name" in update_data:
        updates["name"] = update_data["name"]
    
    if updates:
        result = await database.users.update_one({"id": user_id}, {"$set": updates})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User credentials updated successfully"}

@api_router.delete("/super-admin/prizes/{prize_id}")
async def delete_prize(prize_id: str, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    result = await database.prizes.delete_one({"id": prize_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prize not found")
    
    return {"message": "Prize deleted successfully"}

@api_router.post("/super-admin/admins")
async def create_admin(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    existing_user = await database.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_admin = User(
        username=user_data.username,
        role=UserRole.ADMIN,
        name=user_data.name or user_data.username,
        created_by=current_user["id"]
    )
    admin_dict = new_admin.dict()
    admin_dict["password_hash"] = hash_password(user_data.password)
    
    await database.users.insert_one(admin_dict)
    return {"message": "Admin created successfully", "admin_id": admin_dict["id"]}

@api_router.put("/super-admin/admins/{admin_id}/password")
async def change_admin_password(admin_id: str, password_data: dict, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    
    result = await database.users.update_one(
        {"id": admin_id, "role": "admin"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"message": "Password updated successfully"}

@api_router.delete("/super-admin/admins/{admin_id}")
async def delete_admin(admin_id: str, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    result = await database.users.delete_one({"id": admin_id, "role": "admin"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"message": "Admin deleted successfully"}

# Admin Routes
@api_router.get("/admin/agents")
async def get_all_agents(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    if current_user["role"] == "admin":
        # Admin sees agents they created + agents created by super admin
        agents = await database.users.find({
            "role": "agent",
            "$or": [
                {"created_by": current_user["id"]},
                {"created_by": {"$exists": False}},  # Legacy data
                {"created_by": {"$in": await get_super_admin_ids(database)}}
            ]
        }).to_list(1000)
    else:
        # Super admin sees all agents
        agents = await database.users.find({"role": "agent"}).to_list(1000)
    
    # Remove password_hash from response
    for agent in agents:
        agent.pop("password_hash", None)
    
    return convert_objectid_to_string(agents)

async def get_super_admin_ids(database):
    """Helper function to get super admin IDs"""
    super_admins = await database.users.find({"role": "super_admin"}).to_list(1000)
    return [sa["id"] for sa in super_admins]

@api_router.post("/admin/agents")
async def create_agent(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    existing_user = await database.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_agent = Agent(
        username=user_data.username,
        role=UserRole.AGENT,
        name=user_data.name or user_data.username,
        created_by=current_user["id"]
    )
    agent_dict = new_agent.dict()
    agent_dict["password_hash"] = hash_password(user_data.password)
    
    await database.users.insert_one(agent_dict)
    return {"message": "Agent created successfully", "agent_id": agent_dict["id"]}

@api_router.put("/admin/agents/{agent_id}/target")
async def update_agent_target(agent_id: str, target_data: dict, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    target_monthly = target_data.get("target_monthly")
    if target_monthly is None or target_monthly < 0:
        raise HTTPException(status_code=400, detail="Valid target_monthly is required")
    
    result = await database.users.update_one(
        {"id": agent_id, "role": "agent"},
        {"$set": {"target_monthly": target_monthly}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent target updated successfully"}

@api_router.get("/admin/sale-requests")
async def get_pending_sale_requests(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    requests = await database.sale_requests.find({"status": "pending"}).to_list(1000)
    
    # Add agent information to each request
    for request in requests:
        agent = await database.users.find_one({"id": request["agent_id"]})
        if agent:
            request["agent_name"] = agent.get("name", agent.get("username"))
            request["agent_username"] = agent.get("username")
    
    return convert_objectid_to_string(requests)

@api_router.put("/admin/sale-requests/{request_id}/approve")
async def approve_sale_request(request_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    sale_request = await database.sale_requests.find_one({"id": request_id})
    if not sale_request:
        raise HTTPException(status_code=404, detail="Sale request not found")
    
    # Update sale request
    await database.sale_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "approved",
            "approved_by": current_user["id"],
            "approved_at": datetime.utcnow()
        }}
    )
    
    # Update agent coins and deposits
    await database.users.update_one(
        {"id": sale_request["agent_id"]},
        {"$inc": {
            "coins": sale_request["coins_requested"],
            "deposits": sale_request["deposits_requested"],
            "total_sales": float(sale_request["sale_amount"])
        }}
    )
    
    return {"message": "Sale request approved successfully"}

# Agent Routes
@api_router.post("/agent/sale-request")
async def create_sale_request(sale_data: dict, current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    sale_amount = sale_data.get("sale_amount")
    if sale_amount not in ["100", "250", "500"]:
        raise HTTPException(status_code=400, detail="Invalid sale amount")
    
    calculation = calculate_coins_and_deposits(sale_amount)
    
    sale_request = SaleRequest(
        agent_id=current_user["id"],
        sale_amount=sale_amount,
        coins_requested=calculation["coins"],
        deposits_requested=calculation["deposits"]
    )
    
    await database.sale_requests.insert_one(sale_request.dict())
    return {"message": "Sale request submitted successfully"}

@api_router.get("/agent/dashboard")
async def get_agent_dashboard(current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    agent = await database.users.find_one({"id": current_user["id"]})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get pending requests
    pending_requests = await database.sale_requests.find({
        "agent_id": current_user["id"],
        "status": "pending"
    }).to_list(1000)
    
    # Calculate achievement percentage
    target_monthly = agent.get("target_monthly", 0)
    current_deposits = agent.get("deposits", 0)
    achievement_percentage = (current_deposits / target_monthly * 100) if target_monthly > 0 else 0
    
    return {
        "agent_info": {
            "name": agent.get("name", ""),
            "coins": agent.get("coins", 0),
            "deposits": agent.get("deposits", 0),
            "total_sales": agent.get("total_sales", 0),
            "target_monthly": target_monthly,
            "achievement_percentage": round(achievement_percentage, 2)
        },
        "pending_requests": len(pending_requests)
    }

@api_router.get("/agent/leaderboard")
async def get_agent_leaderboard(current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Get all agents sorted by deposits (highest first)
    agents = await database.users.find({"role": "agent"}).to_list(1000)
    
    # Sort by deposits and prepare leaderboard
    leaderboard = []
    for agent in agents:
        # Get total coins redeemed (from reward_bag)
        coins_redeemed = 0
        rewards = await database.reward_bag.find({"agent_id": agent["id"]}).to_list(1000)
        
        # Calculate total coins redeemed by looking at the coin cost of redeemed prizes
        for reward in rewards:
            prize = await database.prizes.find_one({"id": reward["prize_id"]})
            if prize:
                coins_redeemed += prize.get("coin_cost", 0)
        
        leaderboard.append({
            "name": agent.get("name", agent.get("username", "Unknown")),
            "deposits": agent.get("deposits", 0),
            "coins_redeemed": coins_redeemed,
            "total_sales": agent.get("total_sales", 0),
            "is_current_user": agent["id"] == current_user["id"]
        })
    
    # Sort by deposits (descending)
    leaderboard.sort(key=lambda x: x["deposits"], reverse=True)
    
    # Add rank
    for i, agent in enumerate(leaderboard):
        agent["rank"] = i + 1
    
    return leaderboard

@api_router.get("/shop/prizes")
async def get_shop_prizes(current_user: dict = Depends(get_current_user)):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    prizes = await database.prizes.find({"is_active": True}).to_list(1000)
    return convert_objectid_to_string(prizes)

@api_router.post("/shop/redeem")
async def redeem_prize(redeem_data: dict, current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    prize_id = redeem_data.get("prize_id")
    
    # Get prize and agent info
    prize = await database.prizes.find_one({"id": prize_id, "is_active": True})
    agent = await database.users.find_one({"id": current_user["id"]})
    
    if not prize:
        raise HTTPException(status_code=404, detail="Prize not found")
    
    if agent.get("coins", 0) < prize["coin_cost"]:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    # Check quantity if limited
    if prize.get("is_limited", False) and prize.get("quantity_available", 0) <= 0:
        raise HTTPException(status_code=400, detail="Prize out of stock")
    
    # Create reward bag item
    reward_item = RewardBagItem(
        agent_id=current_user["id"],
        prize_id=prize_id,
        prize_name=prize["name"]
    )
    
    # Update agent coins and prize quantity
    await database.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {"coins": -prize["coin_cost"]}}
    )
    
    if prize.get("is_limited", False):
        await database.prizes.update_one(
            {"id": prize_id},
            {"$inc": {"quantity_available": -1}}
        )
    
    await database.reward_bag.insert_one(reward_item.dict())
    return {"message": "Prize redeemed successfully"}

@api_router.get("/agent/reward-bag")
async def get_reward_bag(current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    rewards = await database.reward_bag.find({"agent_id": current_user["id"]}).to_list(1000)
    return convert_objectid_to_string(rewards)

@api_router.post("/agent/reward-bag/{reward_id}/request-use")
async def request_use_reward(reward_id: str, current_user: dict = Depends(require_role([UserRole.AGENT]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    reward = await database.reward_bag.find_one({"id": reward_id, "agent_id": current_user["id"]})
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    if reward["status"] != "unused":
        raise HTTPException(status_code=400, detail="Reward is not available for use")
    
    # Update status to pending_use
    await database.reward_bag.update_one(
        {"id": reward_id},
        {"$set": {"status": "pending_use"}}
    )
    
    return {"message": "Use request submitted for admin approval"}

@api_router.get("/admin/reward-requests")
async def get_pending_reward_requests(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    rewards = await database.reward_bag.find({"status": "pending_use"}).to_list(1000)
    
    # Add agent information
    for reward in rewards:
        agent = await database.users.find_one({"id": reward["agent_id"]})
        if agent:
            reward["agent_name"] = agent.get("name", agent.get("username"))
    
    return convert_objectid_to_string(rewards)

@api_router.put("/admin/reward-requests/{reward_id}/approve")
async def approve_reward_use(reward_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    database = await get_database()
    if database is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    result = await database.reward_bag.update_one(
        {"id": reward_id, "status": "pending_use"},
        {"$set": {
            "status": "used",
            "used_at": datetime.utcnow(),
            "approved_by": current_user["id"]
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reward request not found")
    
    return {"message": "Reward use approved successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await initialize_super_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
