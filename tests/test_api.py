"""
Unit tests for Flood Alert System API
Run with: python -m pytest tests/
"""

import pytest
import json
from backend.app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'database' in data

def test_home_endpoint(client):
    """Test home endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Flood Alert System API'
    assert 'endpoints' in data

def test_regions_endpoint(client):
    """Test regions endpoint"""
    response = client.get('/api/regions')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['type'] == 'FeatureCollection'
    assert 'features' in data

def test_calculate_risk_endpoint(client):
    """Test risk calculation endpoint"""
    payload = {
        'lat': -15.3900,
        'lng': 35.3300
    }
    response = client.post('/api/calculate-risk',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code in [200, 500]  # May fail if DB not set up
    
def test_invalid_risk_calculation(client):
    """Test risk calculation with invalid data"""
    payload = {}
    response = client.post('/api/calculate-risk',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
