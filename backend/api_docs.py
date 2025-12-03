"""
API Documentation Generator
Generates interactive API documentation for the Flood Alert System
"""

from flask import Flask, render_template_string
import json

API_DOCS = {
    "title": "Flood Alert System API",
    "version": "1.0.0",
    "description": "Real-time flood risk monitoring API for Malawi",
    "base_url": "http://localhost:5000/api",
    "endpoints": [
        {
            "method": "GET",
            "path": "/health",
            "description": "Check API and database health status",
            "response": {
                "status": "healthy",
                "database": "connected"
            }
        },
        {
            "method": "GET",
            "path": "/regions",
            "description": "Get all regions with boundaries",
            "response": "GeoJSON FeatureCollection"
        },
        {
            "method": "GET",
            "path": "/risk-zones",
            "description": "Get flood risk zones",
            "parameters": {
                "region_id": "Filter by region",
                "risk_level": "Filter by risk level (low/moderate/high/critical)",
                "min_score": "Minimum risk score"
            }
        },
        {
            "method": "POST",
            "path": "/calculate-risk",
            "description": "Calculate flood risk for coordinates",
            "body": {
                "lat": "Latitude",
                "lng": "Longitude"
            }
        }
    ]
}

if __name__ == "__main__":
    print(json.dumps(API_DOCS, indent=2))
