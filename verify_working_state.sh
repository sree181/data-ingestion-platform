#!/bin/bash

# Data Ingestion Platform - Working State Verification Script
# This script verifies that all services are running and functional

echo "🚀 Data Ingestion Platform - Working State Verification"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to check if docker container is running
check_container() {
    local container_name=$1
    echo -n "Checking container $container_name... "
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not Running${NC}"
        return 1
    fi
}

echo ""
echo "📦 Checking Docker Containers:"
echo "------------------------------"
check_container "frontend-ui"
check_container "api-gateway"
check_container "elasticsearch"
check_container "postgres"
check_container "neo4j"
check_container "redis"
check_container "minio"
check_container "kafka"

echo ""
echo "🌐 Checking Service Endpoints:"
echo "------------------------------"
check_service "Frontend" "http://localhost:3002"
check_service "API Gateway Health" "http://localhost:8000/health"
check_service "API Gateway Spaces" "http://localhost:8000/api/v1/spaces"
check_service "Elasticsearch" "http://localhost:9200/_cluster/health"
check_service "Neo4j" "http://localhost:7474"
check_service "MinIO" "http://localhost:9001"

echo ""
echo "📊 Checking Document Count:"
echo "---------------------------"
doc_count=$(curl -s "http://localhost:9200/documents/_count" | jq -r '.count' 2>/dev/null)
if [ "$doc_count" ] && [ "$doc_count" -gt 0 ]; then
    echo -e "Documents in Elasticsearch: ${GREEN}$doc_count documents ✅${NC}"
else
    echo -e "Documents in Elasticsearch: ${RED}0 or unable to check ❌${NC}"
fi

echo ""
echo "🔍 Quick API Test:"
echo "------------------"
echo -n "Testing document search... "
search_result=$(curl -s "http://localhost:8000/api/v1/search?q=*&size=1&from=0" | jq -r '.total' 2>/dev/null)
if [ "$search_result" ] && [ "$search_result" -gt 0 ]; then
    echo -e "${GREEN}✅ $search_result documents found${NC}"
else
    echo -e "${RED}❌ Search failed or no documents${NC}"
fi

echo ""
echo "📋 Summary:"
echo "----------"
echo "If all checks show ✅, your Data Ingestion Platform is working correctly!"
echo ""
echo "🌐 Access Points:"
echo "• Frontend: http://localhost:3002"
echo "• API Docs: http://localhost:8000/docs"
echo "• Kibana: http://localhost:5601"
echo "• Neo4j: http://localhost:7474"
echo "• MinIO: http://localhost:9001"
echo ""
echo "⚠️  Remember: This is the STABLE MAIN BRANCH - use feature branches for development!"
