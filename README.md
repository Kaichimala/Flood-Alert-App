# Flood Alert System - Zomba, Malawi

Real-time flood risk monitoring and alert system using PostgreSQL/PostGIS, Flask API, and web mapping.

## Team Members
1. [Name] - Database Developer
2. [Name] - Backend Developer
3. [Name] - Frontend Developer
4. [Name] - Data & Integration

## Problem Statement
Flooding is a recurring problem in Malawi, particularly in low-lying areas like Zomba. Communities need real-time information about flood risks to take preventive measures.

## Solution
A web-based flood alert system that:
- Analyzes spatial data (elevation, water bodies, rainfall)
- Calculates flood risk scores
- Displays risk zones on an interactive map
- Issues automated alerts for high-risk areas

## Technologies Used
- **Database:** PostgreSQL 16 with PostGIS 3.6
- **Backend:** Python Flask REST API
- **Frontend:** HTML, CSS, JavaScript, Leaflet.js
- **Spatial Analysis:** PostGIS spatial functions

## Setup Instructions

### 1. Database Setup
```sql
CREATE DATABASE flood_alert;
CREATE EXTENSION postgis;
-- Run schema.sql
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 3. Frontend
Open `frontend/index.html` in a web browser

## API Endpoints
- `GET /api/health` - Check API status
- `GET /api/statistics` - System statistics
- `GET /api/regions` - All regions
- `GET /api/risk-zones` - Flood risk zones
- `GET /api/alerts/active` - Active alerts
- `POST /api/calculate-risk` - Calculate risk for coordinates

## Demo Video
[Link to your presentation video]

## Future Improvements
- SMS alert integration
- Mobile application
- Machine learning for flood prediction
- Historical flood analysis dashboard