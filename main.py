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

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'sales_crm_production')
client = None
db = None

async def get_database():
    global client, db
    if client is None:
        try:
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                maxPoolSize=10,
                tls=True,
                tlsAllowInvalidCertificates=False,
                retryWrites=True
            )
            db = client[db_name]
            await client.admin.command('ping')
            print(f"MongoDB connected successfully to {db_name}!")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            client = None
            db = None
            return None
    return db

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'your-fallback-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(
    title="Sales CRM System API",
    description="Comprehensive Sales CRM with role-based access",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create router
api_router = APIRouter(prefix="/api")
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
    can_create_prizes: bool = False
    can_edit_prizes: bool = False
    can_delete_prizes: bool = False

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
    status: str = "pending"
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
    status: str = "unused"
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

# Initialize super admin
async def initialize_super_admin():
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

# Add the router to the app
app.include_router(api_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    await initialize_super_admin()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Sales CRM API is running", "status": "online"}
