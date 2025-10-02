#!/bin/bash

# Frontend Startup Script - Always runs on port 3000
# This script ensures the frontend always runs on port 3000 consistently

echo "🚀 Starting Frontend on Port 3000..."

# Stop any existing frontend containers
echo "🛑 Stopping existing frontend containers..."
docker-compose down frontend 2>/dev/null || true

# Start frontend with explicit port configuration
echo "🔧 Starting frontend on port 3000..."
docker-compose up -d frontend --build --force-recreate

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
sleep 10

# Check if frontend is accessible
echo "🔍 Checking frontend accessibility..."
if curl -s -f http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running successfully on http://localhost:3000"
    echo "🌐 Open your browser and go to: http://localhost:3000"
else
    echo "❌ Frontend failed to start on port 3000"
    echo "🔍 Checking Docker logs..."
    docker-compose logs frontend
    exit 1
fi

echo "🎉 Frontend startup complete!"
echo "📍 URL: http://localhost:3000"
