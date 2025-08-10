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

# SQLAlchemy setup
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scrapbook.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
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

class Book(Base):
    """SQLAlchemy model for books (optional for future use)"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=False)
    rating = Column(Integer, nullable=False)
    availability = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    upc = Column(String(50), nullable=True)
    product_type = Column(String(100), nullable=True)
    tax = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=True)

# Create tables
def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

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

class BookBase(BaseModel):
    """Base book model with common fields"""
    title: str = Field(..., description="Book title")
    price: float = Field(..., ge=0, description="Book price")
    rating: int = Field(..., ge=1, le=5, description="Book rating (1-5 stars)")
    availability: str = Field(..., description="Book availability status")
    category: str = Field(..., description="Book category")
    image_url: Optional[str] = Field(None, description="Book cover image URL")

class BookResponse(BookBase):
    """Response model for book listings"""
    id: int = Field(..., description="Book ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True

class BookDetailResponse(BookResponse):
    """Detailed response model for individual book"""
    description: Optional[str] = Field(None, description="Book description")
    detail_url: Optional[str] = Field(None, description="Original book detail URL")
    product_info: Optional[Dict] = Field(None, description="Additional product information")
    upc: Optional[str] = Field(None, description="Universal Product Code")
    product_type: Optional[str] = Field(None, description="Product type")
    tax: Optional[float] = Field(None, description="Tax amount")
    scraped_at: Optional[str] = Field(None, description="Scraping timestamp")

class CategoryResponse(BaseModel):
    """Response model for categories"""
    name: str = Field(..., description="Category name")
    book_count: int = Field(..., ge=0, description="Number of books in category")
    avg_price: Optional[float] = Field(None, description="Average price in category")
    avg_rating: Optional[float] = Field(None, description="Average rating in category")

class StatsResponse(BaseModel):
    """Response model for statistics"""
    total_books: int = Field(..., ge=0, description="Total number of books")
    total_categories: int = Field(..., ge=0, description="Total number of categories")
    avg_price: float = Field(..., description="Average price across all books")
    avg_rating: float = Field(..., description="Average rating across all books")
    price_range: Dict[str, float] = Field(..., description="Min and max prices")
    rating_distribution: Dict[str, int] = Field(..., description="Distribution of ratings")
    last_updated: Optional[datetime] = Field(None, description="Last data update")

class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

class BookListResponse(BaseModel):
    """Response model for book listings with pagination"""
    books: List[BookResponse] = Field(..., description="List of books")
    pagination: PaginationInfo = Field(..., description="Pagination information")

class SearchResponse(BaseModel):
    """Response model for search results"""
    books: List[BookResponse] = Field(..., description="Search results")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    search_params: Dict[str, Any] = Field(..., description="Applied search parameters")
    total_matches: int = Field(..., ge=0, description="Total number of matches")

class TokenResponse(BaseModel):
    """Response model for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")

class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ErrorResponse(BaseModel):
    """Standardized error response model"""
    success: bool = Field(False, description="Success status")
    error: ErrorDetail = Field(..., description="Error information")
    timestamp: str = Field(..., description="Error timestamp")

class SuccessResponse(BaseModel):
    """Standardized success response model"""
    success: bool = Field(True, description="Success status")
    data: Any = Field(..., description="Response data")
    message: str = Field(..., description="Success message")
    timestamp: str = Field(..., description="Response timestamp")

class MLFeatureResponse(BaseModel):
    """Response model for ML features"""
    data: List[Dict[str, Any]] = Field(..., description="Feature data")
    feature_names: List[str] = Field(..., description="List of feature names")
    target_column: Optional[str] = Field(None, description="Target column for ML")
    data_shape: Dict[str, int] = Field(..., description="Data shape information")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")

class TrainingDataResponse(BaseModel):
    """Response model for ML training data"""
    format: str = Field(..., description="Data format (json/csv)")
    data: Union[List[Dict], str] = Field(..., description="Training data")
    features: List[str] = Field(..., description="Available features")
    target: Optional[str] = Field(None, description="Target variable")
    shape: Dict[str, int] = Field(..., description="Dataset shape")

class PredictionRequest(BaseModel):
    """Request model for ML predictions"""
    book_id: Optional[int] = Field(None, description="Book ID for prediction")
    features: Dict[str, Any] = Field(..., description="Feature values")
    model_version: Optional[str] = Field(None, description="Model version to use")

class PredictionResponse(BaseModel):
    """Response model for ML predictions"""
    model_version: str = Field(..., description="Model version used")
    predictions: List[Dict[str, Any]] = Field(..., description="Prediction results")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: Optional[float] = Field(None, description="Overall confidence score")

class ScrapingTriggerResponse(BaseModel):
    """Response model for scraping trigger"""
    job_id: str = Field(..., description="Scraping job ID")
    status: str = Field(..., description="Job status")
    started_at: datetime = Field(..., description="Job start time")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    database_connection: str = Field(..., description="Database connection status")
    total_books: int = Field(..., description="Total books in database")
    last_update: str = Field(..., description="Last data update timestamp")
    api_version: str = Field(..., description="API version")

# Enums for validation
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class DataFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

class BookStatus(str, Enum):
    IN_STOCK = "In stock"
    OUT_OF_STOCK = "Out of stock"

# Query parameter models
class BookQueryParams(BaseModel):
    """Query parameters for book endpoints"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")
    category: Optional[str] = Field(None, description="Filter by category")
    sort_by: str = Field(default="title", description="Sort by field")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

class SearchQueryParams(BaseModel):
    """Query parameters for search endpoints"""
    title: Optional[str] = Field(None, description="Search by title")
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Filter by rating")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

class PriceRangeParams(BaseModel):
    """Query parameters for price range endpoint"""
    min: float = Field(..., ge=0, description="Minimum price")
    max: float = Field(..., ge=0, description="Maximum price")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

class TopRatedParams(BaseModel):
    """Query parameters for top rated books"""
    limit: int = Field(default=10, ge=1, le=50, description="Number of top books")
    min_rating: int = Field(default=4, ge=1, le=5, description="Minimum rating")
