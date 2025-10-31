#!/bin/bash
# Development server startup script
# This script sets up the environment for local development

echo "🚀 Starting Red Team WebApp in DEVELOPMENT mode"
echo ""

# Set development environment
export ENVIRONMENT=development

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Installing..."
    python3 -m pip install uvicorn[standard]
fi

# Create necessary directories
mkdir -p db

echo "✓ Environment: DEVELOPMENT"
echo "✓ Database: SQLite (db/redteam.db)"
echo "✓ Auth: Using dev SECRET_KEY (insecure)"
echo ""
echo "📡 Server will start on: http://0.0.0.0:5172"
echo "📝 API docs available at: http://0.0.0.0:5172/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5172
