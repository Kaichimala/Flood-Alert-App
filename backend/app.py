"""
Flood Alert System - Flask REST API
Author: Your Team Name
Date: December 2025

Run with: python app.py
API will be available at: http://localhost:5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
from config import Config

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

# Database connection helper
def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**Config.DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=None, fetch_one=False):
    """Execute query and return results"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        
        if fetch_one:
            result = cur.fetchone()
        else:
            result = cur.fetchall()
        
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Query error: {e}")
        if conn:
            conn.close()
        return None

def geojson_from_query(query, params=None):
    """Execute query and return GeoJSON FeatureCollection"""
    rows = execute_query(query, params)
    
    if rows is None:
        return {'type': 'FeatureCollection', 'features': []}
    
    features = []
    for row in rows:
        properties = {k: v for k, v in row.items() if k not in ['geom', 'geometry']}
        
        # Handle geometry column (can be 'geom' or 'geometry')
        geom_data = row.get('geom') or row.get('geometry')
        
        if geom_data:
            try:
                geometry = json.loads(geom_data)
                feature = {
                    'type': 'Feature',
                    'geometry': geometry,
                    'properties': properties
                }
                features.append(feature)
            except json.JSONDecodeError:
                print(f"Invalid GeoJSON for row: {properties}")
                continue
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """API documentation and welcome"""
    return jsonify({
        'name': 'Flood Alert System API',
        'version': '1.0.0',
        'description': 'Real-time flood risk monitoring for Malawi',
        'endpoints': {
            'GET /api/health': 'Check API health',
            'GET /api/regions': 'Get all regions',
            'GET /api/regions/<id>': 'Get specific region',
            'GET /api/risk-zones': 'Get flood risk zones',
            'GET /api/alerts': 'Get flood alerts',
            'GET /api/alerts/active': 'Get active alerts only',
            'GET /api/rainfall': 'Get rainfall data',
            'GET /api/rainfall/stations': 'Get all rainfall stations',
            'GET /api/water-bodies': 'Get water bodies',
            'GET /api/elevation': 'Get elevation data',
            'GET /api/statistics': 'Get system statistics',
            'POST /api/calculate-risk': 'Calculate flood risk for coordinates',
            'POST /api/rainfall/add': 'Add new rainfall measurement',
            'POST /api/update-risk-zones': 'Update risk zones for region',
            'POST /api/alerts/create': 'Create new alert'
        }
    })

@app.route('/api/health')
def health_check():
    """Check if API and database are working"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            })
        except:
            return jsonify({
                'status': 'unhealthy',
                'database': 'error',
                'timestamp': datetime.now().isoformat()
            }), 500
    else:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get all regions with their boundaries"""
    query = """
        SELECT 
            id, name, district, population,
            created_at,
            ST_AsGeoJSON(geom) as geom
        FROM regions
        ORDER BY name
    """
    return jsonify(geojson_from_query(query))

@app.route('/api/regions/<int:region_id>', methods=['GET'])
def get_region(region_id):
    """Get specific region details"""
    query = """
        SELECT 
            r.id, r.name, r.district, r.population,
            r.created_at,
            ST_AsGeoJSON(r.geom) as geom,
            COUNT(DISTINCT rs.id) as rainfall_stations,
            COUNT(DISTINCT fh.id) as historical_floods
        FROM regions r
        LEFT JOIN rainfall_stations rs ON r.id = rs.region_id
        LEFT JOIN flood_history fh ON r.id = fh.region_id
        WHERE r.id = %s
        GROUP BY r.id, r.name, r.district, r.population, r.created_at, r.geom
    """
    result = execute_query(query, (region_id,), fetch_one=True)
    
    if result:
        data = dict(result)
        if data.get('geom'):
            data['geometry'] = json.loads(data['geom'])
            del data['geom']
        return jsonify(data)
    else:
        return jsonify({'error': 'Region not found'}), 404

@app.route('/api/risk-zones', methods=['GET'])
def get_risk_zones():
    """Get flood risk zones with optional filters"""
    region_id = request.args.get('region_id', type=int)
    risk_level = request.args.get('risk_level')
    min_score = request.args.get('min_score', type=float)
    
    query = """
        SELECT 
            id, risk_level, risk_score, 
            factors, calculated_at, region_id,
            ST_AsGeoJSON(geom) as geom
        FROM flood_risk_zones
        WHERE 1=1
    """
    params = []
    
    if region_id:
        query += " AND region_id = %s"
        params.append(region_id)
    
    if risk_level:
        query += " AND risk_level = %s"
        params.append(risk_level)
    
    if min_score:
        query += " AND risk_score >= %s"
        params.append(min_score)
    
    query += " ORDER BY risk_score DESC, calculated_at DESC"
    
    return jsonify(geojson_from_query(query, params if params else None))

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get flood alerts"""
    active_only = request.args.get('active', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    
    query = """
        SELECT 
            a.id, a.alert_level, a.message,
            a.issued_at, a.expires_at, a.active,
            a.affected_population,
            r.name as region_name,
            r.district,
            ST_AsGeoJSON(a.affected_area) as geom
        FROM flood_alerts a
        JOIN regions r ON a.region_id = r.id
        WHERE 1=1
    """
    
    if active_only:
        query += " AND a.active = TRUE AND (a.expires_at IS NULL OR a.expires_at > NOW())"
    
    query += " ORDER BY a.issued_at DESC LIMIT %s"
    
    return jsonify(geojson_from_query(query, (limit,)))

@app.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    """Get only active alerts"""
    query = """
        SELECT 
            a.id, a.alert_level, a.message,
            a.issued_at, a.expires_at,
            a.affected_population,
            r.name as region_name,
            r.district,
            ST_AsGeoJSON(a.affected_area) as geom
        FROM flood_alerts a
        JOIN regions r ON a.region_id = r.id
        WHERE a.active = TRUE 
        AND (a.expires_at IS NULL OR a.expires_at > NOW())
        ORDER BY 
            CASE a.alert_level
                WHEN 'emergency' THEN 1
                WHEN 'warning' THEN 2
                WHEN 'watch' THEN 3
                ELSE 4
            END,
            a.issued_at DESC
    """
    return jsonify(geojson_from_query(query))

@app.route('/api/rainfall', methods=['GET'])
def get_rainfall():
    """Get rainfall data with filters"""
    hours = request.args.get('hours', 24, type=int)
    station_id = request.args.get('station_id', type=int)
    region_id = request.args.get('region_id', type=int)
    
    query = """
        SELECT 
            rd.id, rd.rainfall_mm, rd.recorded_at,
            rd.duration_hours,
            rs.name as station_name,
            rs.station_code,
            r.name as region_name,
            ST_AsGeoJSON(rs.geom) as geom
        FROM rainfall_data rd
        JOIN rainfall_stations rs ON rd.station_id = rs.id
        LEFT JOIN regions r ON rs.region_id = r.id
        WHERE rd.recorded_at > NOW() - INTERVAL '%s hours'
    """ % hours
    
    params = []
    if station_id:
        query += " AND rd.station_id = %s"
        params.append(station_id)
    
    if region_id:
        query += " AND rs.region_id = %s"
        params.append(region_id)
    
    query += " ORDER BY rd.recorded_at DESC"
    
    return jsonify(geojson_from_query(query, params if params else None))

@app.route('/api/rainfall/stations', methods=['GET'])
def get_rainfall_stations():
    """Get all rainfall stations"""
    query = """
        SELECT 
            rs.id, rs.name, rs.station_code, rs.active,
            r.name as region_name,
            ST_AsGeoJSON(rs.geom) as geom,
            COUNT(rd.id) as total_measurements,
            MAX(rd.recorded_at) as last_measurement
        FROM rainfall_stations rs
        LEFT JOIN regions r ON rs.region_id = r.id
        LEFT JOIN rainfall_data rd ON rs.id = rd.station_id
        GROUP BY rs.id, rs.name, rs.station_code, rs.active, r.name, rs.geom
        ORDER BY rs.name
    """
    return jsonify(geojson_from_query(query))

@app.route('/api/water-bodies', methods=['GET'])
def get_water_bodies():
    """Get water bodies (rivers, lakes)"""
    water_type = request.args.get('type')
    
    query = """
        SELECT 
            id, name, type, buffer_zone_m, created_at,
            ST_AsGeoJSON(geom) as geom
        FROM water_bodies
        WHERE 1=1
    """
    
    params = []
    if water_type:
        query += " AND type = %s"
        params.append(water_type)
    
    query += " ORDER BY name"
    
    return jsonify(geojson_from_query(query, params if params else None))

@app.route('/api/elevation', methods=['GET'])
def get_elevation():
    """Get elevation data points"""
    region_id = request.args.get('region_id', type=int)
    max_elevation = request.args.get('max_elevation', type=float)
    
    query = """
        SELECT 
            e.id, e.elevation_m,
            r.name as region_name,
            ST_AsGeoJSON(e.geom) as geom
        FROM elevation e
        LEFT JOIN regions r ON e.region_id = r.id
        WHERE 1=1
    """
    
    params = []
    if region_id:
        query += " AND e.region_id = %s"
        params.append(region_id)
    
    if max_elevation:
        query += " AND e.elevation_m <= %s"
        params.append(max_elevation)
    
    query += " ORDER BY e.elevation_m"
    
    return jsonify(geojson_from_query(query, params if params else None))

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    query = """
        SELECT 
            (SELECT COUNT(*) FROM regions) as total_regions,
            (SELECT COUNT(*) FROM rainfall_stations WHERE active = TRUE) as active_stations,
            (SELECT COUNT(*) FROM flood_alerts WHERE active = TRUE 
             AND (expires_at IS NULL OR expires_at > NOW())) as active_alerts,
            (SELECT COUNT(*) FROM flood_risk_zones WHERE risk_level = 'critical') as critical_zones,
            (SELECT COUNT(*) FROM flood_risk_zones WHERE risk_level = 'high') as high_risk_zones,
            (SELECT COALESCE(AVG(rainfall_mm), 0) FROM rainfall_data 
             WHERE recorded_at > NOW() - INTERVAL '24 hours') as avg_rainfall_24h,
            (SELECT COALESCE(MAX(rainfall_mm), 0) FROM rainfall_data 
             WHERE recorded_at > NOW() - INTERVAL '24 hours') as max_rainfall_24h,
            (SELECT COUNT(*) FROM flood_history) as historical_floods
    """
    
    result = execute_query(query, fetch_one=True)
    
    if result:
        return jsonify(dict(result))
    else:
        return jsonify({'error': 'Could not fetch statistics'}), 500

@app.route('/api/calculate-risk', methods=['POST'])
def calculate_risk():
    """Calculate flood risk for given coordinates"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not lat or not lng:
        return jsonify({'error': 'lat and lng required'}), 400
    
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    query = """
        SELECT calculate_flood_risk(
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        ) as risk_score
    """
    
    result = execute_query(query, (lng, lat), fetch_one=True)
    
    if result and result['risk_score'] is not None:
        risk_score = float(result['risk_score'])
        
        # Determine risk level
        if risk_score >= 75:
            risk_level = 'critical'
            risk_description = 'Severe flood risk - immediate action required'
        elif risk_score >= 50:
            risk_level = 'high'
            risk_description = 'High flood risk - stay alert and prepared'
        elif risk_score >= 25:
            risk_level = 'moderate'
            risk_description = 'Moderate flood risk - monitor conditions'
        else:
            risk_level = 'low'
            risk_description = 'Low flood risk'
        
        return jsonify({
            'success': True,
            'lat': lat,
            'lng': lng,
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'description': risk_description,
            'calculated_at': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Could not calculate risk - insufficient data'
        }), 500

@app.route('/api/rainfall/add', methods=['POST'])
def add_rainfall():
    """Add new rainfall measurement"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    station_id = data.get('station_id')
    rainfall_mm = data.get('rainfall_mm')
    duration_hours = data.get('duration_hours', 1)
    
    if not station_id or rainfall_mm is None:
        return jsonify({'error': 'station_id and rainfall_mm required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO rainfall_data 
            (station_id, recorded_at, rainfall_mm, duration_hours)
            VALUES (%s, NOW(), %s, %s)
            RETURNING id, recorded_at
        """, (station_id, rainfall_mm, duration_hours))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': result[0],
            'recorded_at': result[1].isoformat(),
            'station_id': station_id,
            'rainfall_mm': rainfall_mm
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """Create new flood alert"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    region_id = data.get('region_id')
    alert_level = data.get('alert_level', 'warning')
    message = data.get('message')
    duration_hours = data.get('duration_hours', 24)
    
    if not region_id or not message:
        return jsonify({'error': 'region_id and message required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO flood_alerts 
            (region_id, alert_level, message, affected_area, expires_at)
            SELECT 
                %s, %s, %s, geom,
                NOW() + INTERVAL '%s hours'
            FROM regions WHERE id = %s
            RETURNING id, issued_at, expires_at
        """, (region_id, alert_level, message, duration_hours, region_id))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'alert_id': result[0],
            'issued_at': result[1].isoformat(),
            'expires_at': result[2].isoformat()
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Run the application
if __name__ == '__main__':
    print("=" * 50)
    print("Flood Alert System API")
    print("=" * 50)
    print(f"Server starting on http://{Config.API_HOST}:{Config.API_PORT}")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.DEBUG
    )