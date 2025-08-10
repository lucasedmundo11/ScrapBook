"""
Database manager for the ScrapBook API

This module handles all data operations including reading CSV files,
processing data, and providing data for API endpoints.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging
import sys

# Add scripts path for config
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
from src.config.Scrapper import ScraperConfig

class DatabaseManager:
    """Manages data operations for the API"""
    
    def __init__(self):
        self.config = ScraperConfig()
        self.logger = logging.getLogger(__name__)
        self._data = None
        self._categories = None
        self._last_load = None
        
    def _load_latest_data(self) -> pd.DataFrame:
        """Load the latest books data from CSV files"""
        try:
            csv_files = list(Path(self.config.CSV_DIR).glob("books_detailed_*.csv"))
            
            if not csv_files:
                raise FileNotFoundError("No book data files found")
            
            # Get the latest file
            latest_file = max(csv_files, key=os.path.getctime)
            
            # Check if we need to reload
            file_modified = datetime.fromtimestamp(os.path.getctime(latest_file))
            
            if self._data is None or self._last_load is None or file_modified > self._last_load:
                self.logger.info(f"Loading data from {latest_file}")
                self._data = pd.read_csv(latest_file)
                
                # Clean and process data
                self._data = self._clean_data(self._data)
                self._last_load = datetime.now()
                
            return self._data
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and process the data"""
        # Add ID column if not present
        if 'id' not in df.columns:
            df['id'] = range(1, len(df) + 1)
        
        # Clean price column
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Clean rating column
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        # Fill missing values
        df['description'] = df['description'].fillna('')
        df['availability'] = df['availability'].fillna('Unknown')
        df['category'] = df['category'].fillna('Uncategorized')
        
        # Add timestamps if not present
        if 'created_at' not in df.columns:
            df['created_at'] = datetime.now().isoformat()
        
        if 'updated_at' not in df.columns:
            df['updated_at'] = datetime.now().isoformat()
        
        return df
    
    def _paginate_results(self, df: pd.DataFrame, page: int, limit: int) -> Dict:
        """Apply pagination to results"""
        total_items = len(df)
        total_pages = (total_items + limit - 1) // limit
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_df = df.iloc[start_idx:end_idx]
        
        return {
            "books": paginated_df.to_dict('records'),
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def get_all_books(self, page: int = 1, limit: int = 50, 
                     category: Optional[str] = None,
                     sort_by: str = "title", 
                     sort_order: str = "asc") -> Dict:
        """Get all books with pagination and filtering"""
        df = self._load_latest_data()
        
        # Apply category filter
        if category:
            df = df[df['category'].str.contains(category, case=False, na=False)]
        
        # Apply sorting
        ascending = sort_order.lower() == "asc"
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=ascending)
        
        return self._paginate_results(df, page, limit)
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get a specific book by ID"""
        df = self._load_latest_data()
        book_df = df[df['id'] == book_id]
        
        if book_df.empty:
            return None
        
        return book_df.iloc[0].to_dict()
    
    def search_books(self, title: Optional[str] = None,
                    category: Optional[str] = None,
                    min_price: Optional[float] = None,
                    max_price: Optional[float] = None,
                    rating: Optional[int] = None,
                    page: int = 1, limit: int = 50) -> Dict:
        """Search books with multiple filters"""
        df = self._load_latest_data()
        
        # Apply filters
        if title:
            df = df[df['title'].str.contains(title, case=False, na=False)]
        
        if category:
            df = df[df['category'].str.contains(category, case=False, na=False)]
        
        if min_price is not None:
            df = df[df['price'] >= min_price]
        
        if max_price is not None:
            df = df[df['price'] <= max_price]
        
        if rating is not None:
            df = df[df['rating'] == rating]
        
        result = self._paginate_results(df, page, limit)
        
        # Add search parameters to response
        result["search_params"] = {
            "title": title,
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "rating": rating
        }
        result["total_matches"] = len(df)
        
        return result
    
    def get_all_categories(self) -> List[Dict]:
        """Get all book categories with statistics"""
        df = self._load_latest_data()
        
        category_stats = df.groupby('category').agg({
            'id': 'count',
            'price': ['mean', 'min', 'max'],
            'rating': 'mean'
        }).round(2)
        
        category_stats.columns = ['book_count', 'avg_price', 'min_price', 'max_price', 'avg_rating']
        category_stats = category_stats.reset_index()
        
        return category_stats.to_dict('records')
    
    def get_overview_stats(self) -> Dict:
        """Get overview statistics"""
        df = self._load_latest_data()
        
        rating_dist = df['rating'].value_counts().sort_index().to_dict()
        
        stats = {
            "total_books": len(df),
            "total_categories": df['category'].nunique(),
            "avg_price": round(df['price'].mean(), 2),
            "avg_rating": round(df['rating'].mean(), 2),
            "price_range": {
                "min": float(df['price'].min()),
                "max": float(df['price'].max())
            },
            "rating_distribution": rating_dist,
            "last_updated": self._last_load.isoformat() if self._last_load else None
        }
        
        return stats
    
    def get_category_stats(self) -> List[Dict]:
        """Get detailed statistics by category"""
        df = self._load_latest_data()
        
        stats = df.groupby('category').agg({
            'id': 'count',
            'price': ['mean', 'min', 'max', 'std'],
            'rating': ['mean', 'min', 'max', 'std']
        }).round(2)
        
        stats.columns = [
            'book_count', 'avg_price', 'min_price', 'max_price', 'price_std',
            'avg_rating', 'min_rating', 'max_rating', 'rating_std'
        ]
        
        stats = stats.reset_index()
        return stats.to_dict('records')
    
    def get_top_rated_books(self, limit: int = 10, min_rating: int = 4) -> List[Dict]:
        """Get top rated books"""
        df = self._load_latest_data()
        
        # Filter by minimum rating and sort by rating (desc), then by title
        top_books = df[df['rating'] >= min_rating].sort_values(
            ['rating', 'title'], ascending=[False, True]
        ).head(limit)
        
        return top_books.to_dict('records')
    
    def get_books_by_price_range(self, min_price: float, max_price: float,
                                page: int = 1, limit: int = 50) -> Dict:
        """Get books within a price range"""
        df = self._load_latest_data()
        
        # Filter by price range
        df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
        
        # Sort by price
        df = df.sort_values('price')
        
        result = self._paginate_results(df, page, limit)
        result["price_range"] = {"min": min_price, "max": max_price}
        
        return result
    
    def get_ml_features(self) -> Dict:
        """Get data formatted for ML features"""
        df = self._load_latest_data()
        
        # Create feature columns
        features_df = df.copy()
        
        # Numerical features
        numerical_features = ['price', 'rating']
        
        # Categorical features (one-hot encode)
        categorical_features = ['category', 'availability']
        
        # Text features (basic preprocessing)
        features_df['title_length'] = features_df['title'].str.len()
        features_df['description_length'] = features_df['description'].str.len()
        features_df['has_description'] = (features_df['description'] != '').astype(int)
        
        # Category encoding
        category_encoded = pd.get_dummies(features_df['category'], prefix='category')
        features_df = pd.concat([features_df, category_encoded], axis=1)
        
        # Availability encoding
        availability_encoded = pd.get_dummies(features_df['availability'], prefix='availability')
        features_df = pd.concat([features_df, availability_encoded], axis=1)
        
        # Select feature columns
        feature_columns = (numerical_features + 
                          ['title_length', 'description_length', 'has_description'] +
                          list(category_encoded.columns) +
                          list(availability_encoded.columns))
        
        ml_data = features_df[['id'] + feature_columns].fillna(0)
        
        return {
            "data": ml_data.to_dict('records'),
            "feature_names": feature_columns,
            "target_column": "rating",
            "data_shape": {
                "rows": len(ml_data),
                "features": len(feature_columns)
            },
            "metadata": {
                "numerical_features": numerical_features,
                "categorical_features": categorical_features,
                "generated_features": ['title_length', 'description_length', 'has_description']
            }
        }
    
    def get_training_data(self, format: str = "json", features: Optional[List[str]] = None) -> Dict:
        """Get training data for ML models"""
        ml_features = self.get_ml_features()
        
        # Filter features if specified
        if features:
            available_features = ml_features["feature_names"]
            selected_features = [f for f in features if f in available_features]
            
            # Update data with selected features only
            filtered_data = []
            for record in ml_features["data"]:
                filtered_record = {"id": record["id"]}
                for feature in selected_features:
                    filtered_record[feature] = record.get(feature, 0)
                filtered_data.append(filtered_record)
            
            ml_features["data"] = filtered_data
            ml_features["feature_names"] = selected_features
        
        if format.lower() == "csv":
            # Convert to CSV format
            df = pd.DataFrame(ml_features["data"])
            csv_data = df.to_csv(index=False)
            
            return {
                "format": "csv",
                "data": csv_data,
                "features": ml_features["feature_names"],
                "target": ml_features["target_column"],
                "shape": ml_features["data_shape"]
            }
        
        return {
            "format": "json",
            "data": ml_features["data"],
            "features": ml_features["feature_names"],
            "target": ml_features["target_column"],
            "shape": ml_features["data_shape"]
        }
