#!/bin/bash

# Production-Ready Data Ingestion Platform Startup Script
# Hybrid Elasticsearch + Neo4j Architecture

set -e

echo "🚀 Starting Data Ingestion Platform (Hybrid Architecture)"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating environment configuration...${NC}"
    cat > .env << EOF
# API Keys (set these for full functionality)
LLAMAPARSE_API_KEY=llx-CAZ1cTYFHKvUUKgGoqwnguYMsdYujutBDIGsnSo5Crwsa8Q2
OPENAI_API_KEY= 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

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Feature Flags
USE_LLAMAPARSE=true
ENABLE_OCR=true
ENABLE_VECTOR_SEARCH=true

# Performance Settings
MAX_WORKERS=4
BATCH_SIZE=10
CHUNK_SIZE=1000

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✅ Environment file created (.env)${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your API keys before production use${NC}"
fi

# Ensure required directories exist
echo -e "${BLUE}📁 Creating required directories...${NC}"
mkdir -p data logs sql elasticsearch/config monitoring/grafana/dashboards monitoring/grafana/datasources

# Create SQL initialization script
if [ ! -f sql/init.sql ]; then
    echo -e "${YELLOW}📝 Creating database initialization script...${NC}"
    cat > sql/init.sql << 'EOF'
-- Data Platform Database Initialization

-- Create document processing status table
CREATE TABLE IF NOT EXISTS document_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    progress FLOAT DEFAULT 0,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB NOT NULL,
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_document_status_user_id ON document_status(user_id);
CREATE INDEX IF NOT EXISTS idx_document_status_status ON document_status(status);
CREATE INDEX IF NOT EXISTS idx_document_status_created_at ON document_status(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON processing_jobs(job_type);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role, permissions) 
VALUES (
    'admin', 
    'admin@dataplatform.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewA8pQgKzOxcG3Dq', 
    'admin', 
    '["read", "write", "admin"]'
) ON CONFLICT (username) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for auto-updating timestamps
DROP TRIGGER IF EXISTS update_document_status_updated_at ON document_status;
CREATE TRIGGER update_document_status_updated_at 
    BEFORE UPDATE ON document_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF
fi

# Create Elasticsearch configuration
if [ ! -f elasticsearch/config/elasticsearch.yml ]; then
    echo -e "${YELLOW}📝 Creating Elasticsearch configuration...${NC}"
    cat > elasticsearch/config/elasticsearch.yml << 'EOF'
cluster.name: "data-platform"
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# Performance settings
indices.memory.index_buffer_size: 20%
indices.queries.cache.size: 10%

# Ingest pipelines
ingest.geoip.downloader.enabled: false
EOF
fi

# Create monitoring configuration
if [ ! -f monitoring/prometheus.yml ]; then
    echo -e "${YELLOW}📝 Creating monitoring configuration...${NC}"
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
  
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    metrics_path: '/_prometheus/metrics'
  
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']
    metrics_path: '/metrics'
EOF
fi

# Check if already running
if docker-compose -f docker-compose-optimized.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services are already running${NC}"
    echo -e "${BLUE}🔄 Stopping existing services...${NC}"
    docker-compose -f docker-compose-optimized.yml down
fi

# Start the platform
echo -e "${BLUE}🚀 Starting Data Ingestion Platform...${NC}"
docker-compose -f docker-compose-optimized.yml up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"

# Function to check if a service is ready
check_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready${NC}"
            return 0
        fi
        echo -e "${YELLOW}⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to start${NC}"
    return 1
}

# Check core services
echo -e "${BLUE}🔍 Checking service health...${NC}"

check_service "Elasticsearch" "http://localhost:9200/_cluster/health"
check_service "Neo4j" "http://localhost:7474/browser/"
check_service "MinIO" "http://localhost:9001/minio/health/live"
check_service "PostgreSQL" "localhost:5432" # Special case for postgres

# Wait a bit more for dependent services
sleep 10

check_service "API Gateway" "http://localhost:8000/health"

echo ""
echo -e "${GREEN}🎉 Data Ingestion Platform is ready!${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}📊 Service URLs:${NC}"
echo "  🎨 Frontend UI:        http://localhost:3000"
echo "  🌐 API Gateway:        http://localhost:8000"
echo "  📖 API Documentation:  http://localhost:8000/docs"
echo "  🔍 Elasticsearch:      http://localhost:9200"
echo "  🕸️  Neo4j Browser:      http://localhost:7474"
echo "  🗂️  MinIO Console:      http://localhost:9001"
echo "  📊 Kafka UI:           http://localhost:8080"
echo "  📈 Grafana:            http://localhost:3001"
echo "  🔧 Prometheus:         http://localhost:9090"
echo ""
echo -e "${BLUE}🔑 Default Credentials:${NC}"
echo "  MinIO:     admin / minio123"
echo "  Neo4j:     neo4j / password123"
echo "  Grafana:   admin / admin123"
echo "  Platform:  admin / admin123"
echo ""
echo -e "${BLUE}📋 Quick Commands:${NC}"
echo "  View logs:    docker-compose -f docker-compose-optimized.yml logs -f"
echo "  Stop all:     docker-compose -f docker-compose-optimized.yml down"
echo "  Restart:      ./start.sh"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "  1. Visit http://localhost:3000 for the main UI"
echo "  2. Visit http://localhost:8000/docs for API documentation"
echo "  3. Upload test documents via the UI or API"
echo "  4. Explore the knowledge graph in Neo4j"
echo "  5. Set up monitoring dashboards in Grafana"
echo ""
echo -e "${GREEN}✨ Happy data ingesting! ✨${NC}"
EOF