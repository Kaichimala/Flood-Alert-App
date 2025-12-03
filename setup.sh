#!/bin/bash

# Flood Alert System - Setup Script
# This script sets up the database and initializes the system

echo "=================================="
echo "Flood Alert System - Setup"
echo "=================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed"
    exit 1
fi

# Create database
echo "Creating database..."
psql -U postgres -c "CREATE DATABASE flood_alert;"

# Run SQL setup
echo "Setting up database schema..."
psql -U postgres -d flood_alert -f database/schema.sql
psql -U postgres -d flood_alert -f database/sample_data.sql

echo "=================================="
echo "Setup complete!"
echo "=================================="
echo "Next steps:"
echo "1. Update backend/config.py with your database credentials"
echo "2. Run: cd backend && python app.py"
echo "3. Open frontend/index.html in your browser"
