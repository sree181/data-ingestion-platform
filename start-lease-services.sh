#!/bin/bash

# Start Lease Management Services
echo "🚀 Starting Lease Management Services..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one with OPENAI_API_KEY"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not found in .env file"
    exit 1
fi

echo "✅ Environment variables loaded"

# Start the services
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose-lease.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Lease Obligation Extractor
echo "Checking Lease Obligation Extractor..."
if curl -s http://localhost:8005/health > /dev/null; then
    echo "✅ Lease Obligation Extractor is running"
else
    echo "❌ Lease Obligation Extractor is not responding"
fi

# Check Lease Comparison Engine
echo "Checking Lease Comparison Engine..."
if curl -s http://localhost:8006/health > /dev/null; then
    echo "✅ Lease Comparison Engine is running"
else
    echo "❌ Lease Comparison Engine is not responding"
fi

# Check PostgreSQL
echo "Checking PostgreSQL..."
if docker exec lease-obligation-extractor_postgres_1 pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not responding"
fi

# Check Elasticsearch
echo "Checking Elasticsearch..."
if curl -s http://localhost:9201/_cluster/health > /dev/null; then
    echo "✅ Elasticsearch is running"
else
    echo "❌ Elasticsearch is not responding"
fi

echo ""
echo "🎉 Lease Management Services are ready!"
echo ""
echo "📋 Service URLs:"
echo "   Lease Obligation Extractor: http://localhost:8005"
echo "   Lease Comparison Engine: http://localhost:8006"
echo "   PostgreSQL: localhost:5433"
echo "   Elasticsearch: http://localhost:9201"
echo ""
echo "🌐 Frontend: http://localhost:3000/lease-management"
echo ""
echo "📚 API Documentation:"
echo "   Lease Extractor: http://localhost:8005/docs"
echo "   Comparison Engine: http://localhost:8006/docs"
echo ""
echo "To stop services: docker-compose -f docker-compose-lease.yml down"
