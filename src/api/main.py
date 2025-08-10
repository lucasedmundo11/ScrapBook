"""
Main Flask application for ScrapBook API

This module implements a comprehensive RESTful API for the books scraping system
using Flask, Flask-JWT-Extended, and Flasgger for documentation.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import Swagger, swag_from
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import sys
from pathlib import Path
from functools import wraps
import threading
import sys

# Add the scripts directory to the path to import scraper modules
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

# Import configurations
from src.config.api import APIConfig, setup_api_logging
from src.api.database import DatabaseManager
from src.api.auth import user_service

# Import scraper
from src.scripts.main_scraper import ScrapingOrchestrator

# Initialize logging using the new API configuration
logger = setup_api_logging("scrapbook_api_main")

# Initialize Flask app
app = Flask(__name__)

# Load API configuration
api_config = APIConfig()
app.config['JWT_SECRET_KEY'] = api_config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = api_config.get_jwt_expire_delta()

# Initialize extensions
jwt = JWTManager(app)
CORS(
    app, origins=api_config.CORS_ORIGINS, methods=api_config.CORS_METHODS, 
    allow_headers=api_config.CORS_HEADERS
)

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "ScrapBook API",
        "description": "RESTful API for Books Web Scraping System with ML Engineering focus",
        "version": api_config.API_VERSION,
        "contact": {
            "name": "ScrapBook API Support",
            "email": "support@scrapbook-api.com"
        }
    },
    "host": f"{api_config.API_HOST}:{api_config.API_PORT}",
    "basePath": "/api/v1",
    "schemes": ["http"],
    "consumes": [
        "application/json",
    ],
    "produces": [
        "application/json",
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Initialize components
api_config.create_directories()
db_manager = DatabaseManager()

# Global variable to track scraping jobs
scraping_jobs = {}

def verify_password(username: str, password: str) -> bool:
    """Verify user credentials using SQLAlchemy"""
    return user_service.verify_password(username, password)

def create_success_response(data: Any, message: str = "Success") -> Dict:
    """Create standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def create_error_response(code: str, message: str, details: Dict = None) -> Dict:
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def log_request():
    """Decorator to log all requests using the new API logger"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.utcnow()
            
            # Process request
            try:
                response = f(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                else:
                    response_data = response[0] if isinstance(response, tuple) else response
                    status_code = response[1] if isinstance(response, tuple) and len(response) > 1 else 200
            except Exception as e:
                response = jsonify(create_error_response("INTERNAL_ERROR", str(e))), 500
                status_code = 500
            
            # Calculate processing time
            process_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Use the new API logger to log requests
            user_agent = request.headers.get("User-Agent", "unknown")
            user_id = None
            
            # Try to get user ID from JWT token
            try:
                if request.headers.get('Authorization'):
                    user_id = get_jwt_identity()
            except:
                pass
            
            # Log using the new structured API logging
            logger.info("API Request processed", extra={
                'event_type': 'api_request',
                'method': request.method,
                'url': request.url,
                'status_code': status_code,
                'response_time': process_time,
                'user_agent': user_agent,
                'user_id': user_id
            })
            
            return response
        return decorated_function
    return decorator

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.route('/api/v1/health', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/health.yaml')
def health_check():
    """Verify API status and data connectivity"""
    try:
        # Check if data files exist
        csv_files = list(Path(api_config.DATA_CSV_DIR).glob("books_detailed_*.csv"))
        
        if not csv_files:
            return jsonify(create_error_response(
                "DATA_NOT_FOUND",
                "No book data files found",
                {"csv_dir": str(api_config.DATA_CSV_DIR)}
            )), 500
        
        # Get latest file
        latest_file = max(csv_files, key=os.path.getctime)
        
        # Test data loading
        df = pd.read_csv(latest_file)
        
        health_data = {
            "status": "healthy",
            "database_connection": "active",
            "total_books": len(df),
            "last_update": datetime.fromtimestamp(os.path.getctime(latest_file)).isoformat(),
            "api_version": api_config.API_VERSION
        }
        
        return jsonify(create_success_response(health_data, "API is healthy"))
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify(create_error_response(
            "HEALTH_CHECK_FAILED",
            "Health check failed",
            {"error": str(e)}
        )), 500

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.route('/api/v1/books', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/books_list.yaml')
def get_books():
    """Lista todos os livros disponíveis na base de dados com paginação"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        category = request.args.get('category')
        sort_by = request.args.get('sort_by', 'title')
        sort_order = request.args.get('sort_order', 'asc')
        
        books_data = db_manager.get_all_books(
            page=page, 
            limit=limit, 
            category=category,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify(create_success_response(
            books_data,
            f"Retrieved {len(books_data['books'])} books"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching books: {str(e)}")
        return jsonify(create_error_response(
            "FETCH_BOOKS_ERROR",
            "Failed to fetch books",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/books/<int:book_id>', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/book_by_id.yaml')
def get_book_by_id(book_id):
    """Retorna detalhes completos de um livro específico pelo ID"""
    try:
        book = db_manager.get_book_by_id(book_id)
        
        if not book:
            return jsonify(create_error_response(
                "BOOK_NOT_FOUND",
                f"Book with ID {book_id} not found"
            )), 404
        
        return jsonify(create_success_response(book, "Book details retrieved successfully"))
        
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {str(e)}")
        return jsonify(create_error_response(
            "FETCH_BOOK_ERROR",
            f"Failed to fetch book {book_id}",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/books/search', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/books_search.yaml')
def search_books():
    """Busca livros por título, categoria e outros filtros"""
    try:
        title = request.args.get('title')
        category = request.args.get('category')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        rating = request.args.get('rating', type=int)
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if not any([title, category, min_price, max_price, rating]):
            return jsonify(create_error_response(
                "INVALID_SEARCH_PARAMS",
                "At least one search parameter is required"
            )), 400
        
        results = db_manager.search_books(
            title=title,
            category=category,
            min_price=min_price,
            max_price=max_price,
            rating=rating,
            page=page,
            limit=limit
        )
        
        return jsonify(create_success_response(
            results,
            f"Found {len(results['books'])} books matching search criteria"
        ))
        
    except Exception as e:
        logger.error(f"Error searching books: {str(e)}")
        return jsonify(create_error_response(
            "SEARCH_ERROR",
            "Failed to search books",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/categories', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/categories.yaml')
def get_categories():
    """Lista todas as categorias de livros disponíveis"""
    try:
        categories = db_manager.get_all_categories()
        
        return jsonify(create_success_response(
            {"categories": categories},
            f"Retrieved {len(categories)} categories"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify(create_error_response(
            "FETCH_CATEGORIES_ERROR",
            "Failed to fetch categories",
            {"error": str(e)}
        )), 500

# ============================================================================
# INSIGHTS ENDPOINTS
# ============================================================================

@app.route('/api/v1/stats/overview', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/stats_overview.yaml')
def get_stats_overview():
    """Estatísticas gerais da coleção"""
    try:
        stats = db_manager.get_overview_stats()
        
        return jsonify(create_success_response(
            stats,
            "Overview statistics retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching overview stats: {str(e)}")
        return jsonify(create_error_response(
            "STATS_ERROR",
            "Failed to fetch overview statistics",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/stats/categories', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/stats_categories.yaml')
def get_stats_categories():
    """Estatísticas detalhadas por categoria"""
    try:
        stats = db_manager.get_category_stats()
        
        return jsonify(create_success_response(
            {"category_stats": stats},
            f"Category statistics for {len(stats)} categories retrieved"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching category stats: {str(e)}")
        return jsonify(create_error_response(
            "CATEGORY_STATS_ERROR",
            "Failed to fetch category statistics",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/books/top-rated', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/books_top_rated.yaml')
def get_top_rated_books():
    """Lista os livros com melhor avaliação"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        min_rating = int(request.args.get('min_rating', 4))
        
        top_books = db_manager.get_top_rated_books(limit=limit, min_rating=min_rating)
        
        return jsonify(create_success_response(
            {"top_rated_books": top_books},
            f"Retrieved top {len(top_books)} rated books"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching top rated books: {str(e)}")
        return jsonify(create_error_response(
            "TOP_RATED_ERROR",
            "Failed to fetch top rated books",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/books/price-range', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/books_price_range.yaml')
def get_books_by_price_range():
    """Filtra livros dentro de uma faixa de preço específica"""
    try:
        min_price = request.args.get('min', type=float)
        max_price = request.args.get('max', type=float)
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if not min_price or not max_price or min_price < 0 or max_price < 0 or min_price > max_price:
            return jsonify(create_error_response(
                "INVALID_PRICE_RANGE",
                "Invalid price range. Min and max must be positive, and min <= max"
            )), 400
        
        results = db_manager.get_books_by_price_range(
            min_price=min_price,
            max_price=max_price,
            page=page,
            limit=limit
        )
        
        return jsonify(create_success_response(
            results,
            f"Found {len(results['books'])} books in price range ${min_price:.2f} - ${max_price:.2f}"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching books by price range: {str(e)}")
        return jsonify(create_error_response(
            "PRICE_RANGE_ERROR",
            "Failed to fetch books by price range",
            {"error": str(e)}
        )), 500

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/v1/auth/login', methods=['POST'])
@log_request()
@swag_from('../../docs/swagger/auth_login.yaml')
def login():
    """Obter token de autenticação"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
            
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return jsonify(create_error_response(
                "MISSING_CREDENTIALS",
                "Username and password are required"
            )), 400
        
        # Validate credentials
        if not verify_password(username, password):
            return jsonify(create_error_response(
                "INVALID_CREDENTIALS",
                "Invalid username or password"
            )), 401
        
        # Generate tokens
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": api_config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        return jsonify(create_success_response(token_data, "Login successful"))
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify(create_error_response(
            "LOGIN_ERROR",
            "Login failed",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/auth/refresh', methods=['POST'])
@log_request()
@swag_from('../../docs/swagger/auth_refresh.yaml')
def refresh_token():
    """Renovar token de acesso"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
            
        # For simplicity, create a new access token with the current user
        # In production, you would validate the refresh token properly
        access_token = create_access_token(identity="user")
        
        token_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": api_config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        return jsonify(create_success_response(token_data, "Token refreshed successfully"))
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify(create_error_response(
            "TOKEN_REFRESH_ERROR",
            "Failed to refresh token",
            {"error": str(e)}
        )), 401

# ============================================================================
# USER MANAGEMENT ENDPOINTS (PROTECTED)
# ============================================================================

@app.route('/api/v1/users', methods=['GET'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/users_list.yaml')
def get_users():
    """Lista todos os usuários (apenas admins)"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        if not current_user or not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Admin privileges required"
            )), 403
        
        users = user_service.get_all_users()
        user_list = [user.to_dict() for user in users]
        
        return jsonify(create_success_response(
            {"users": user_list},
            f"Retrieved {len(user_list)} users"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify(create_error_response(
            "FETCH_USERS_ERROR",
            "Failed to fetch users",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/users', methods=['POST'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/users_create.yaml')
def create_user():
    """Criar novo usuário (apenas admins)"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        if not current_user or not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Admin privileges required"
            )), 403
        
        data = request.get_json()
        if not data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
        
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        is_admin = data.get("is_admin", False)
        
        if not username or not password:
            return jsonify(create_error_response(
                "MISSING_REQUIRED_FIELDS",
                "Username and password are required"
            )), 400
        
        new_user = user_service.create_user(
            username=username,
            password=password,
            email=email,
            is_admin=is_admin
        )
        
        if not new_user:
            return jsonify(create_error_response(
                "USER_CREATION_FAILED",
                "Failed to create user (username or email may already exist)"
            )), 400
        
        return jsonify(create_success_response(
            new_user.to_dict(),
            "User created successfully"
        )), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify(create_error_response(
            "USER_CREATION_ERROR",
            "Failed to create user",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/users_update.yaml')
def update_user(user_id):
    """Atualizar usuário"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        if not current_user:
            return jsonify(create_error_response(
                "USER_NOT_FOUND",
                "Current user not found"
            )), 404
        
        # Users can update their own profile, admins can update anyone
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Cannot update other users"
            )), 403
        
        data = request.get_json()
        if not data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
        
        # Only allow certain fields to be updated
        allowed_fields = ["email", "is_active"]
        if current_user.is_admin:
            allowed_fields.append("is_admin")
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        updated_user = user_service.update_user(user_id, **update_data)
        
        if not updated_user:
            return jsonify(create_error_response(
                "USER_NOT_FOUND",
                f"User with ID {user_id} not found"
            )), 404
        
        return jsonify(create_success_response(
            updated_user.to_dict(),
            "User updated successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify(create_error_response(
            "USER_UPDATE_ERROR",
            "Failed to update user",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/users/<int:user_id>/password', methods=['PUT'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/users_update_password.yaml')
def change_user_password(user_id):
    """Alterar senha do usuário"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        if not current_user:
            return jsonify(create_error_response(
                "USER_NOT_FOUND",
                "Current user not found"
            )), 404
        
        # Users can only change their own password
        if current_user.id != user_id:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Cannot change other users' passwords"
            )), 403
        
        data = request.get_json()
        if not data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
        
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        
        if not current_password or not new_password:
            return jsonify(create_error_response(
                "MISSING_REQUIRED_FIELDS",
                "Current password and new password are required"
            )), 400
        
        success = user_service.change_password(user_id, current_password, new_password)
        
        if not success:
            return jsonify(create_error_response(
                "PASSWORD_CHANGE_FAILED",
                "Failed to change password (invalid current password or user not found)"
            )), 400
        
        return jsonify(create_success_response(
            {"message": "Password changed successfully"},
            "Password changed successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify(create_error_response(
            "PASSWORD_CHANGE_ERROR",
            "Failed to change password",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/users/me', methods=['GET'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/users_me.yaml')
def get_current_user():
    """Obter informações do usuário atual"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        if not current_user:
            return jsonify(create_error_response(
                "USER_NOT_FOUND",
                "Current user not found"
            )), 404
        
        return jsonify(create_success_response(
            current_user.to_dict(),
            "User information retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching current user: {str(e)}")
        return jsonify(create_error_response(
            "FETCH_USER_ERROR",
            "Failed to fetch user information",
            {"error": str(e)}
        )), 500

# ============================================================================
# ML ENDPOINTS
# ============================================================================

@app.route('/api/v1/ml/features', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/ml_features.yaml')
def get_ml_features():
    """Dados formatados para features de Machine Learning"""
    try:
        features = db_manager.get_ml_features()
        
        return jsonify(create_success_response(
            features,
            f"ML features for {len(features['data'])} books retrieved"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching ML features: {str(e)}")
        return jsonify(create_error_response(
            "ML_FEATURES_ERROR",
            "Failed to fetch ML features",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/ml/training-data', methods=['GET'])
@log_request()
@swag_from('../../docs/swagger/ml_training_data.yaml')
def get_training_data():
    """Dataset formatado para treinamento de modelos ML"""
    try:
        format_param = request.args.get('format', 'json')
        features = request.args.get('features')
        
        feature_list = features.split(",") if features else None
        training_data = db_manager.get_training_data(format=format_param, features=feature_list)
        
        return jsonify(create_success_response(
            training_data,
            f"Training data in {format_param} format retrieved"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
        return jsonify(create_error_response(
            "TRAINING_DATA_ERROR",
            "Failed to fetch training data",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/ml/predictions', methods=['POST'])
@log_request()
@swag_from('../../docs/swagger/ml_predictions.yaml')
def make_predictions():
    """Endpoint para receber e processar predições de modelos ML"""
    try:
        prediction_data = request.get_json()
        if not prediction_data:
            return jsonify(create_error_response(
                "MISSING_REQUEST_BODY",
                "Request body is required"
            )), 400
        
        # In a real implementation, this would integrate with ML models
        # For now, we'll return a mock response
        
        predictions = {
            "model_version": "1.0.0",
            "predictions": [
                {
                    "book_id": prediction_data.get("book_id"),
                    "predicted_rating": 4.2,
                    "confidence": 0.85,
                    "category_probability": {
                        "Fiction": 0.7,
                        "Mystery": 0.2,
                        "Romance": 0.1
                    }
                }
            ],
            "processing_time": 0.045
        }
        
        return jsonify(create_success_response(
            predictions,
            "Predictions generated successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error making predictions: {str(e)}")
        return jsonify(create_error_response(
            "PREDICTION_ERROR",
            "Failed to generate predictions",
            {"error": str(e)}
        )), 500

# ============================================================================
# ADMINISTRATIVE ENDPOINTS (PROTECTED)
# ============================================================================

@app.route('/api/v1/scraping/trigger', methods=['POST'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/scraping_trigger.yaml')
def trigger_scraping():
    """Disparar processo de scraping manualmente (requer autenticação)"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        # Check if user has admin privileges
        if not current_user or not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Admin privileges required to trigger scraping"
            )), 403
        
        # Generate job ID
        job_id = f"scraping_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get optional parameters from request
        data = request.get_json() if request.get_json() else {}
        extract_full_details = data.get('extract_full_details', True)
        max_pages = data.get('max_pages', None)
        
        # Initialize job status
        scraping_jobs[job_id] = {
            "job_id": job_id,
            "status": "started",
            "started_at": datetime.now().isoformat(),
            "started_by": current_user_username,
            "parameters": {
                "extract_full_details": extract_full_details,
                "max_pages": max_pages
            },
            "progress": {
                "current_step": "initializing",
                "total_steps": 3,
                "completed_steps": 0
            },
            "result": None,
            "error": None
        }
        
        def run_scraping_task():
            """Run the scraping in a separate thread"""
            try:
                # Update job status
                scraping_jobs[job_id]["status"] = "running"
                scraping_jobs[job_id]["progress"]["current_step"] = "scraping_categories"
                
                # Initialize scraper
                orchestrator = ScrapingOrchestrator()
                
                # Run the full scraping pipeline
                logger.info(f"Starting scraping job {job_id} by user {current_user_username}")
                
                result = orchestrator.run_full_scraping_pipeline(
                    extract_full_details=extract_full_details,
                    max_pages=max_pages
                )
                
                # Update job with results
                scraping_jobs[job_id].update({
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "progress": {
                        "current_step": "completed",
                        "total_steps": 3,
                        "completed_steps": 3
                    },
                    "result": {
                        "books_scraped": result.get('books', {}).get('count', 0),
                        "categories_found": result.get('categories', {}).get('count', 0),
                        "pipeline_duration": result.get('pipeline_duration_seconds', 0),
                        "started_at": result.get('pipeline_started_at'),
                        "completed_at": result.get('pipeline_completed_at')
                    }
                })
                
                logger.info(f"Scraping job {job_id} completed successfully")
                
            except Exception as e:
                # Update job with error
                scraping_jobs[job_id].update({
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__
                    }
                })
                logger.error(f"Scraping job {job_id} failed: {str(e)}")
        
        # Start scraping in background thread
        thread = threading.Thread(target=run_scraping_task, daemon=True)
        thread.start()
        
        # Return job information immediately
        return jsonify(create_success_response(
            {
                "job_id": job_id,
                "status": "started",
                "started_at": scraping_jobs[job_id]["started_at"],
                "parameters": scraping_jobs[job_id]["parameters"],
                "message": "Scraping job started successfully. Use GET /api/v1/scraping/status/{job_id} to check progress."
            },
            "Scraping process started successfully"
        )), 202
        
    except Exception as e:
        logger.error(f"Error triggering scraping: {str(e)}")
        return jsonify(create_error_response(
            "SCRAPING_TRIGGER_ERROR",
            "Failed to trigger scraping process",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/scraping/status/<job_id>', methods=['GET'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/scraping_status.yaml')
def get_scraping_status(job_id):
    """Verificar status de um job de scraping"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        # Check if user has admin privileges
        if not current_user or not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Admin privileges required to check scraping status"
            )), 403
        
        # Check if job exists
        if job_id not in scraping_jobs:
            return jsonify(create_error_response(
                "JOB_NOT_FOUND",
                f"Scraping job {job_id} not found"
            )), 404
        
        job_info = scraping_jobs[job_id]
        
        return jsonify(create_success_response(
            job_info,
            f"Scraping job status retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching scraping status: {str(e)}")
        return jsonify(create_error_response(
            "SCRAPING_STATUS_ERROR",
            "Failed to fetch scraping status",
            {"error": str(e)}
        )), 500

@app.route('/api/v1/scraping/jobs', methods=['GET'])
@jwt_required()
@log_request()
@swag_from('../../docs/swagger/scraping_jobs.yaml')
def get_scraping_jobs():
    """Listar todos os jobs de scraping"""
    try:
        current_user_username = get_jwt_identity()
        current_user = user_service.get_user_by_username(current_user_username)
        
        # Check if user has admin privileges
        if not current_user or not current_user.is_admin:
            return jsonify(create_error_response(
                "INSUFFICIENT_PERMISSIONS",
                "Admin privileges required to list scraping jobs"
            )), 403
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Convert scraping_jobs to list and apply pagination
        all_jobs = list(scraping_jobs.values())
        all_jobs.sort(key=lambda x: x['started_at'], reverse=True)  # Most recent first
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_jobs = all_jobs[start_idx:end_idx]
        
        return jsonify(create_success_response(
            {
                "jobs": paginated_jobs,
                "pagination": {
                    "current_page": page,
                    "total_jobs": len(all_jobs),
                    "jobs_per_page": limit,
                    "total_pages": (len(all_jobs) + limit - 1) // limit,
                    "has_next": end_idx < len(all_jobs),
                    "has_prev": page > 1
                }
            },
            f"Retrieved {len(paginated_jobs)} scraping jobs"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching scraping jobs: {str(e)}")
        return jsonify(create_error_response(
            "SCRAPING_JOBS_ERROR",
            "Failed to fetch scraping jobs",
            {"error": str(e)}
        )), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_handler(error):
    """Handle 404 errors"""
    return jsonify(create_error_response(
        "NOT_FOUND",
        f"Endpoint not found"
    )), 404

@app.errorhandler(500)
def internal_error_handler(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify(create_error_response(
        "INTERNAL_SERVER_ERROR",
        "Internal server error occurred"
    )), 500

@app.errorhandler(400)
def bad_request_handler(error):
    """Handle 400 errors"""
    return jsonify(create_error_response(
        "BAD_REQUEST",
        "Bad request"
    )), 400

@app.errorhandler(401)
def unauthorized_handler(error):
    """Handle 401 errors"""
    return jsonify(create_error_response(
        "UNAUTHORIZED",
        "Authentication required"
    )), 401

if __name__ == "__main__":
    app.run(
        host=api_config.API_HOST,
        port=api_config.API_PORT,
        debug=True
    )
