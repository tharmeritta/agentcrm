from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env.production for deployment
env_path = Path(__file__).parent.parent / '.env.production'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to local .env
    load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from enum import Enum

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'sales_crm_production')
client = None
db = None

async def get_database():
    global client, db
    if client is None:
        try:
            # Try MongoDB Atlas connection
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=10,
                tlsAllowInvalidCertificates=True
            )
            db = client[db_name]
            # Test connection
            await client.admin.command('ping')
            print(f"MongoDB Atlas connected successfully to {db_name}!")
        except Exception as e:
            print(f"MongoDB Atlas connection failed: {e}")
            try:
                # Fall back to local MongoDB
                client = AsyncIOMotorClient("mongodb://localhost:27017")
                db = client[db_name]
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
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'your-fallback-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(
    title="Sales CRM System API",
    description="Comprehensive Sales CRM with role-based access",
    version="1.0.0"
)

# CORS middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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