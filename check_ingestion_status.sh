#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}    📊 Current Ingestion Status - $(date '+%H:%M:%S')${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get total document count
TOTAL_DOCS=$(curl -s "http://localhost:9200/documents/_count" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
echo -e "${BLUE}📚 Total documents in Elasticsearch: ${GREEN}${TOTAL_DOCS}${NC}"
echo ""

# Search for "allergic rash" related documents
echo -e "${YELLOW}🔍 Searching for 'Allergic rash' related documents...${NC}"
ALLERGIC_COUNT=$(curl -s -X GET "http://localhost:9200/documents/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "multi_match": {
        "query": "allergic rash",
        "fields": ["title^2", "abstract", "content"]
      }
    },
    "size": 0
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['hits']['total']['value'])" 2>/dev/null)

echo -e "${GREEN}✅ Found ${ALLERGIC_COUNT} documents related to 'Allergic rash'${NC}"
echo ""

# Get latest 5 documents
echo -e "${YELLOW}📄 Latest 5 documents ingested:${NC}"
curl -s -X GET "http://localhost:9200/documents/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {"match_all": {}},
    "size": 5,
    "sort": [{"ingestion_timestamp": {"order": "desc"}}]
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
hits = data.get('hits', {}).get('hits', [])
for i, hit in enumerate(hits, 1):
    source = hit['_source']
    title = source.get('title', 'N/A')[:80]
    timestamp = source.get('ingestion_timestamp', 'N/A')
    classification = source.get('classification', 'N/A')
    print(f'{i}. {title}...')
    print(f'   Time: {timestamp} | Classification: {classification}')
    print()
" 2>/dev/null

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Tip: Run this script again to see updated counts!${NC}"
echo -e "${CYAN}Command: ./check_ingestion_status.sh${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

