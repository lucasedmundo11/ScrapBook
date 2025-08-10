"""
Pydantic and SQLAlchemy models for API request/response validation and database operations

This module defines all the data models used in the ScrapBook API
following the project specifications.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

# Database configuration
def get_database_url():
    """Get database URL with serverless environment handling."""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Use provided database URL (for production with external DB)
        return database_url
    
    # Check if we're in a serverless environment
    is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('NETLIFY')
    
    if is_serverless:
        # Use in-memory SQLite for serverless environments
        return "sqlite:///:memory:"
    else:
        # Use file-based SQLite for local development
        return "sqlite:///./data/scrapbook.db"

DATABASE_URL = get_database_url()

# Configure engine with proper settings for serverless environments
if ":memory:" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, 
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        pool_pre_ping=True,
        pool_recycle=300
    )
else:
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Models
class User(Base):
    """SQLAlchemy model for users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def set_password(self, password: str):
        """Set password hash"""
        self.hashed_password = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.hashed_password, password)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

# Create tables
def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def init_database():
    """Initialize database with tables for serverless environments"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
        
        # For in-memory databases, create default users
        is_memory_db = ":memory:" in DATABASE_URL
        if is_memory_db:
            create_default_users()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # Don't raise the exception to prevent app startup failure

def create_default_users():
    """Create default admin and user accounts for in-memory database"""
    try:
        db = SessionLocal()
        try:
            # Check if users already exist
            admin_exists = db.query(User).filter(User.username == "admin").first()
            user_exists = db.query(User).filter(User.username == "user").first()
            
            users_created = []
            
            # Create admin user if it doesn't exist
            if not admin_exists:
                admin_user = User(
                    username="admin",
                    email="admin@scrapbook.com",
                    is_active=True,
                    is_admin=True
                )
                admin_user.set_password("admin123")
                db.add(admin_user)
                users_created.append("admin")
            
            # Create regular user if it doesn't exist
            if not user_exists:
                regular_user = User(
                    username="user",
                    email="user@scrapbook.com",
                    is_active=True,
                    is_admin=False
                )
                regular_user.set_password("user123")
                db.add(regular_user)
                users_created.append("user")
            
            if users_created:
                db.commit()
                logger.info(f"Created default users: {', '.join(users_created)}")
            else:
                logger.info("Default users already exist")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating default users: {e}")
            raise e
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to create default users: {e}")
        # Don't raise the exception to prevent app startup failure

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models for API validation

class UserCreate(BaseModel):
    """Model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[str] = Field(None, description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    is_admin: bool = Field(default=False, description="Admin privileges")

class UserResponse(BaseModel):
    """Response model for user information"""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    is_active: bool = Field(..., description="User active status")
    is_admin: bool = Field(..., description="Admin privileges")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[str] = Field(None, description="Email address")
    is_active: Optional[bool] = Field(None, description="User active status")
    is_admin: Optional[bool] = Field(None, description="Admin privileges")

class LoginRequest(BaseModel):
    """Request model for user login"""
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=6, description="Password")

class PasswordChangeRequest(BaseModel):
    """Request model for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")

# User role enumeration
class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
