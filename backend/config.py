"""
Configuration file for Flood Alert System
"""

import os

class Config:
    """Database and API configuration"""
    
    # Database Configuration
    DB_CONFIG = {
        'dbname': 'flood_alert',
        'user': 'postgres',
        'password': 'panda@55',  # CHANGE THIS to your PostgreSQL password
        'host': 'localhost',
        'port': '5432'
    }
    
    # API Configuration
    API_HOST = '0.0.0.0'
    API_PORT = 5000
    DEBUG = True
    
    # CORS Configuration (allows frontend to connect)
    CORS_ORIGINS = ['*']  # In production, specify exact domains
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    # Alert thresholds
    RAINFALL_THRESHOLD = 50.0  # mm in 24 hours
    CRITICAL_RISK_THRESHOLD = 75.0
    HIGH_RISK_THRESHOLD = 50.0
    
    @staticmethod
    def get_db_connection_string():
        """Get PostgreSQL connection string"""
        cfg = Config.DB_CONFIG
        return f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"