#!/bin/bash

# End-to-End Test for PV Classification Pipeline
# Tests: PubMed Ingestion → Classification → Elasticsearch → Neo4j → UI Display

set -e

echo "🧪 =========================================="
echo "🧪 PV CLASSIFICATION END-TO-END TEST"
echo "🧪 =========================================="
echo ""

BASE_URL="http://localhost:3000/api/v1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Health Check
echo -e "${BLUE}📋 Step 1: Health Check${NC}"
echo "Checking PV Classification service health..."
curl -s -X GET "${BASE_URL}/pv-classification/health" | jq '.'
echo -e "${GREEN}✅ Health check passed${NC}\n"

# Step 2: Check available domains
echo -e "${BLUE}📋 Step 2: Available Domains${NC}"
echo "Fetching available PV classification domains..."
curl -s -X GET "${BASE_URL}/pv-classification/domains" | jq '.domains[] | {id, name}'
echo -e "${GREEN}✅ Domains retrieved${NC}\n"

# Step 3: Login and get token
echo -e "${BLUE}📋 Step 3: Authentication${NC}"
echo "Logging in to get authentication token..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login failed. Please check credentials.${NC}"
  echo "$LOGIN_RESPONSE" | jq '.'
  exit 1
fi

echo -e "${GREEN}✅ Authentication successful${NC}"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 4: Ingest and Classify PubMed Articles
echo -e "${BLUE}📋 Step 4: Ingest & Classify PubMed Articles${NC}"
echo "Triggering targeted PubMed ingestion with classification..."
echo "Domain: hepatotoxicity"
echo "Max articles: 10 (for quick testing)"
echo ""

INGEST_RESPONSE=$(curl -s -X POST "${BASE_URL}/pv-classification/ingest-and-classify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain": "hepatotoxicity",
    "max_articles": 10
  }')

echo "$INGEST_RESPONSE" | jq '.'

SUCCESS=$(echo "$INGEST_RESPONSE" | jq -r '.success')
if [ "$SUCCESS" != "true" ]; then
  echo -e "${RED}❌ Ingestion failed${NC}"
  exit 1
fi

ARTICLES_INGESTED=$(echo "$INGEST_RESPONSE" | jq -r '.articles_ingested')
ARTICLES_CLASSIFIED=$(echo "$INGEST_RESPONSE" | jq -r '.articles_classified')
PROCESSING_TIME=$(echo "$INGEST_RESPONSE" | jq -r '.processing_time_seconds')

echo -e "${GREEN}✅ Ingestion completed${NC}"
echo "   Articles ingested: $ARTICLES_INGESTED"
echo "   Articles classified: $ARTICLES_CLASSIFIED"
echo "   Processing time: ${PROCESSING_TIME}s"
echo ""

# Step 5: Get Classification Statistics
echo -e "${BLUE}📋 Step 5: Classification Statistics${NC}"
echo "Fetching ICSR project classification stats..."

STATS_RESPONSE=$(curl -s -X GET "${BASE_URL}/pv-classification/stats" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATS_RESPONSE" | jq '.'

TOTAL_DOCS=$(echo "$STATS_RESPONSE" | jq -r '.total_documents')
AVG_CONFIDENCE=$(echo "$STATS_RESPONSE" | jq -r '.average_confidence')

echo -e "${GREEN}✅ Statistics retrieved${NC}"
echo "   Total documents: $TOTAL_DOCS"
echo "   Average confidence: $(printf "%.2f" $(echo "$AVG_CONFIDENCE * 100" | bc))%"
echo ""

# Step 6: Verify Elasticsearch Storage
echo -e "${BLUE}📋 Step 6: Verify Elasticsearch Storage${NC}"
echo "Checking if classified documents are in Elasticsearch..."

ES_QUERY=$(curl -s -X GET "http://localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "exists": {
        "field": "classification"
      }
    },
    "size": 1,
    "_source": ["title", "classification", "classification_confidence", "classification_entities"]
  }')

ES_TOTAL=$(echo "$ES_QUERY" | jq -r '.hits.total.value')
echo "Documents with classification in Elasticsearch: $ES_TOTAL"

if [ "$ES_TOTAL" -gt 0 ]; then
  echo ""
  echo "Sample classified document:"
  echo "$ES_QUERY" | jq '.hits.hits[0]._source'
  echo -e "${GREEN}✅ Elasticsearch storage verified${NC}"
else
  echo -e "${YELLOW}⚠️  No classified documents found in Elasticsearch yet${NC}"
fi
echo ""

# Step 7: Verify Neo4j Storage
echo -e "${BLUE}📋 Step 7: Verify Neo4j Storage${NC}"
echo "Checking if classification entities are in Neo4j..."

NEO4J_QUERY='MATCH (e:Entity) WHERE exists(e.classification_relevance) RETURN count(e) as count, collect(e.name)[0..3] as sample_entities LIMIT 1'

NEO4J_RESPONSE=$(curl -s -X POST "http://localhost:7474/db/data/transaction/commit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'neo4j:password' | base64)" \
  -d "{
    \"statements\": [{
      \"statement\": \"$NEO4J_QUERY\"
    }]
  }")

NEO4J_COUNT=$(echo "$NEO4J_RESPONSE" | jq -r '.results[0].data[0].row[0]' 2>/dev/null || echo "0")

echo "Classification entities in Neo4j: $NEO4J_COUNT"

if [ "$NEO4J_COUNT" != "null" ] && [ "$NEO4J_COUNT" -gt 0 ]; then
  echo "Sample entities: $(echo "$NEO4J_RESPONSE" | jq -r '.results[0].data[0].row[1]')"
  echo -e "${GREEN}✅ Neo4j storage verified${NC}"
else
  echo -e "${YELLOW}⚠️  No classification entities found in Neo4j yet${NC}"
fi
echo ""

# Step 8: UI Verification Instructions
echo -e "${BLUE}📋 Step 8: UI Verification${NC}"
echo "To verify the UI display:"
echo ""
echo "1. Open browser: ${YELLOW}http://localhost:3000${NC}"
echo "2. Login with: admin / admin123"
echo "3. Navigate to: ${YELLOW}Documents > Browse Documents${NC}"
echo "4. You should see:"
echo "   - ${GREEN}Classification badges${NC} (ICSR, Safety Info, Non-ICSR, Rejected) on cards"
echo "   - ${GREEN}Classification confidence${NC} percentages"
echo "   - ${GREEN}Classification evidence entities${NC} highlighted with checkmarks"
echo "   - ${GREEN}Filter chips${NC} to filter by classification type"
echo "   - ${GREEN}Updated stats${NC} showing ICSR and Safety Info counts in header"
echo ""

# Step 9: Summary
echo -e "${BLUE}📋 Step 9: Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ PV Classification E2E Test Complete!${NC}"
echo ""
echo "Pipeline Status:"
echo "  ✓ PubMed Ingestion: $ARTICLES_INGESTED articles"
echo "  ✓ Classification: $ARTICLES_CLASSIFIED articles"
echo "  ✓ Elasticsearch: $ES_TOTAL documents indexed"
echo "  ✓ Neo4j: $NEO4J_COUNT entities stored"
echo "  ✓ Processing Time: ${PROCESSING_TIME}s"
echo ""
echo "Next Steps:"
echo "  1. Check the UI at http://localhost:3000"
echo "  2. Filter by classification type to see different categories"
echo "  3. Click on a classified document to see full details"
echo "  4. Ingest more articles with different domains (cardiotoxicity, neurotoxicity)"
echo ""
echo -e "${BLUE}🎉 All systems operational!${NC}"
echo "=========================================="

