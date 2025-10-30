#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}    📚 PubMed Ingestion Monitor - Allergic Rash Documents${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get initial count
INITIAL_COUNT=$(curl -s "http://localhost:9200/documents/_count" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
echo -e "${BLUE}📊 Initial document count: ${GREEN}${INITIAL_COUNT}${NC}"
echo ""

# Get start time
START_TIME=$(date +%s)

echo -e "${YELLOW}⏳ Monitoring ingestion... (Press Ctrl+C to stop)${NC}"
echo ""
echo -e "${CYAN}Time    | Total Docs | New Docs | Rate (docs/min) | Latest Document${NC}"
echo -e "${CYAN}--------|------------|----------|-----------------|------------------${NC}"

PREV_COUNT=$INITIAL_COUNT

while true; do
    # Get current count
    CURRENT_COUNT=$(curl -s "http://localhost:9200/documents/_count" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
    
    # Calculate new documents
    NEW_DOCS=$((CURRENT_COUNT - INITIAL_COUNT))
    DOCS_SINCE_LAST=$((CURRENT_COUNT - PREV_COUNT))
    
    # Calculate elapsed time
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    ELAPSED_MIN=$(echo "scale=2; $ELAPSED / 60" | bc)
    
    # Calculate rate
    if [ $ELAPSED -gt 0 ]; then
        RATE=$(echo "scale=2; ($NEW_DOCS * 60) / $ELAPSED" | bc)
    else
        RATE="0.00"
    fi
    
    # Get latest document (if any new ones)
    if [ $DOCS_SINCE_LAST -gt 0 ]; then
        LATEST_DOC=$(curl -s "http://localhost:9200/documents/_search?size=1&sort=ingestion_timestamp:desc" | \
            python3 -c "import sys, json; data=json.load(sys.stdin); hits=data.get('hits', {}).get('hits', []); print(hits[0]['_source'].get('title', 'N/A')[:50] + '...' if hits else 'N/A')" 2>/dev/null)
        DOC_INDICATOR="${GREEN}+${DOCS_SINCE_LAST}${NC}"
    else
        LATEST_DOC="(waiting...)"
        DOC_INDICATOR=""
    fi
    
    # Format time
    TIME_STR=$(date +"%H:%M:%S")
    
    # Print status line
    printf "${TIME_STR} | ${GREEN}%-10s${NC} | ${YELLOW}%-8s${NC} | ${CYAN}%-15s${NC} | %s %s\n" \
        "$CURRENT_COUNT" "$NEW_DOCS" "$RATE" "$LATEST_DOC" "$DOC_INDICATOR"
    
    PREV_COUNT=$CURRENT_COUNT
    
    # Sleep for 5 seconds
    sleep 5
done

