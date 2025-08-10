"""
Authentication and user management service for ScrapBook API

This module handles user authentication, registration, and management
using SQLAlchemy for database operations.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.api.models import User, SessionLocal, create_tables
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user management operations"""
    
    def __init__(self):
        """Initialize the service and create tables if they don't exist"""
        create_tables()
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default admin and user accounts"""
        db = SessionLocal()
        try:
            # Check if users already exist
            admin_exists = db.query(User).filter(User.username == "admin").first()
            user_exists = db.query(User).filter(User.username == "user").first()
            
            if not admin_exists:
                admin = User(
                    username="admin",
                    email="admin@scrapbook.local",
                    is_admin=True,
                    is_active=True
                )
                admin.set_password("admin123")
                db.add(admin)
                logger.info("Created default admin user")
            
            if not user_exists:
                user = User(
                    username="user",
                    email="user@scrapbook.local",
                    is_admin=False,
                    is_active=True
                )
                user.set_password("user123")
                db.add(user)
                logger.info("Created default user")
            
            db.commit()
            
        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Default users already exist: {e}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating default users: {e}")
        finally:
            db.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if user and user.check_password(password):
                # Update last login
                user.last_login = datetime.utcnow()
                db.commit()
                db.refresh(user)
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
        finally:
            db.close()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, 
                   is_admin: bool = False) -> Optional[User]:
        """Create a new user"""
        db = SessionLocal()
        try:
            # Check if username already exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                logger.warning(f"User with username {username} already exists")
                return None
            
            # Check if email already exists
            if email:
                existing_email = db.query(User).filter(User.email == email).first()
                if existing_email:
                    logger.warning(f"User with email {email} already exists")
                    return None
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                is_admin=is_admin,
                is_active=True
            )
            new_user.set_password(password)
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"Created new user: {username}")
            return new_user
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            db.close()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update allowed fields
            for field, value in kwargs.items():
                if hasattr(user, field) and field not in ['id', 'hashed_password', 'created_at']:
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info(f"Updated user {user_id}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {e}")
            return None
        finally:
            db.close()
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Verify current password
            if not user.check_password(current_password):
                logger.warning(f"Invalid current password for user {user_id}")
                return False
            
            # Set new password
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error changing password: {e}")
            return False
        finally:
            db.close()
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Deactivated user {user_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating user: {e}")
            return False
        finally:
            db.close()
    
    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """Get all users"""
        db = SessionLocal()
        try:
            query = db.query(User)
            if not include_inactive:
                query = query.filter(User.is_active == True)
            
            users = query.order_by(User.created_at.desc()).all()
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            db.close()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user credentials (compatibility method)"""
        user = self.authenticate_user(username, password)
        return user is not None
    
    def get_user_roles(self, username: str) -> List[str]:
        """Get user roles (compatibility method)"""
        user = self.get_user_by_username(username)
        if not user:
            return []
        
        roles = ["user"]
        if user.is_admin:
            roles.append("admin")
        
        return roles

# Global user service instance
user_service = UserService()
