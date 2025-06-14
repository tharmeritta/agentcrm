from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import ssl
import certifi
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
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                tlsAllowInvalidCertificates=True
            )
            db = client[os.environ['DB_NAME']]
            # Test connection
            await client.admin.command('ping')
            print("MongoDB Atlas connected successfully!")
        except Exception as e:
            print(f"MongoDB Atlas connection failed: {e}")
            # Fall back to local MongoDB
            client = AsyncIOMotorClient("mongodb://localhost:27017")
            db = client[os.environ['DB_NAME']]
            print("Connected to local MongoDB instead")
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
    user = await db.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(required_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in required_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

def calculate_coins_and_deposits(sale_amount: str):
    amounts = {
        "100": {"coins": 0.5, "deposits": 1},
        "250": {"coins": 1, "deposits": 1.5},
        "500": {"coins": 3, "deposits": 3}
    }
    return amounts.get(sale_amount, {"coins": 0, "deposits": 0})

# Initialize database with super admin
async def initialize_super_admin():
    db = await get_database()
    existing_super_admin = await db.users.find_one({"role": "super_admin"})
    if not existing_super_admin:
        super_admin = User(
            username="tharme.ritta",
            role=UserRole.SUPER_ADMIN,
            name="Super Administrator",
            is_active=True
        )
        super_admin_dict = super_admin.dict()
        super_admin_dict["password_hash"] = hash_password("Tharme@789")
        await db.users.insert_one(super_admin_dict)
        print("Super Admin created successfully")

# Routes
@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"username": login_data.username})
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
    admins = await db.users.find({"role": "admin"}).to_list(1000)
    return admins

@api_router.post("/super-admin/admins")
async def create_admin(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    existing_user = await db.users.find_one({"username": user_data.username})
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
    
    await db.users.insert_one(admin_dict)
    return {"message": "Admin created successfully", "admin_id": admin_dict["id"]}

@api_router.put("/super-admin/admins/{admin_id}/password")
async def change_admin_password(admin_id: str, password_data: dict, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    
    result = await db.users.update_one(
        {"id": admin_id, "role": "admin"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"message": "Password updated successfully"}

@api_router.delete("/super-admin/admins/{admin_id}")
async def delete_admin(admin_id: str, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))):
    result = await db.users.delete_one({"id": admin_id, "role": "admin"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"message": "Admin deleted successfully"}

# Admin Routes
@api_router.get("/admin/agents")
async def get_all_agents(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    if current_user["role"] == "admin":
        agents = await db.users.find({"role": "agent", "created_by": current_user["id"]}).to_list(1000)
    else:
        agents = await db.users.find({"role": "agent"}).to_list(1000)
    return agents

@api_router.post("/admin/agents")
async def create_agent(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    existing_user = await db.users.find_one({"username": user_data.username})
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
    
    await db.users.insert_one(agent_dict)
    return {"message": "Agent created successfully", "agent_id": agent_dict["id"]}

@api_router.get("/admin/sale-requests")
async def get_pending_sale_requests(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    requests = await db.sale_requests.find({"status": "pending"}).to_list(1000)
    return requests

@api_router.put("/admin/sale-requests/{request_id}/approve")
async def approve_sale_request(request_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
    sale_request = await db.sale_requests.find_one({"id": request_id})
    if not sale_request:
        raise HTTPException(status_code=404, detail="Sale request not found")
    
    # Update sale request
    await db.sale_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "approved",
            "approved_by": current_user["id"],
            "approved_at": datetime.utcnow()
        }}
    )
    
    # Update agent coins and deposits
    await db.users.update_one(
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
    
    await db.sale_requests.insert_one(sale_request.dict())
    return {"message": "Sale request submitted successfully"}

@api_router.get("/agent/dashboard")
async def get_agent_dashboard(current_user: dict = Depends(require_role([UserRole.AGENT]))):
    agent = await db.users.find_one({"id": current_user["id"]})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get pending requests
    pending_requests = await db.sale_requests.find({
        "agent_id": current_user["id"],
        "status": "pending"
    }).to_list(1000)
    
    return {
        "agent_info": {
            "name": agent.get("name", ""),
            "coins": agent.get("coins", 0),
            "deposits": agent.get("deposits", 0),
            "total_sales": agent.get("total_sales", 0),
            "target_monthly": agent.get("target_monthly", 0)
        },
        "pending_requests": len(pending_requests)
    }

@api_router.get("/shop/prizes")
async def get_shop_prizes(current_user: dict = Depends(get_current_user)):
    prizes = await db.prizes.find({"is_active": True}).to_list(1000)
    return prizes

@api_router.post("/shop/redeem")
async def redeem_prize(redeem_data: dict, current_user: dict = Depends(require_role([UserRole.AGENT]))):
    prize_id = redeem_data.get("prize_id")
    
    # Get prize and agent info
    prize = await db.prizes.find_one({"id": prize_id, "is_active": True})
    agent = await db.users.find_one({"id": current_user["id"]})
    
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
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {"coins": -prize["coin_cost"]}}
    )
    
    if prize.get("is_limited", False):
        await db.prizes.update_one(
            {"id": prize_id},
            {"$inc": {"quantity_available": -1}}
        )
    
    await db.reward_bag.insert_one(reward_item.dict())
    return {"message": "Prize redeemed successfully"}

@api_router.get("/agent/reward-bag")
async def get_reward_bag(current_user: dict = Depends(require_role([UserRole.AGENT]))):
    rewards = await db.reward_bag.find({"agent_id": current_user["id"]}).to_list(1000)
    return rewards

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
