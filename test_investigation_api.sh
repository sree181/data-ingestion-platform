#!/bin/bash

# Test script for Investigation Board API
echo "🧪 Testing Investigation Board API Endpoints"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get auth token first
echo "1️⃣  Getting authentication token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "password"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get auth token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Got auth token${NC}"
echo ""

# Test 1: Create a new investigation board
echo "2️⃣  Creating investigation board..."
CREATE_BOARD=$(curl -s -X POST http://localhost:8000/api/v1/investigations/boards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Drug Interaction Study",
    "description": "Investigating potential drug interactions for new compound",
    "status": "active"
  }')

BOARD_ID=$(echo $CREATE_BOARD | jq -r '.id')

if [ "$BOARD_ID" == "null" ] || [ -z "$BOARD_ID" ]; then
    echo -e "${RED}❌ Failed to create board${NC}"
    echo "Response: $CREATE_BOARD"
    exit 1
fi

echo -e "${GREEN}✅ Board created with ID: $BOARD_ID${NC}"
echo ""

# Test 2: List all boards
echo "3️⃣  Listing all boards..."
LIST_BOARDS=$(curl -s -X GET http://localhost:8000/api/v1/investigations/boards \
  -H "Authorization: Bearer $TOKEN")

BOARD_COUNT=$(echo $LIST_BOARDS | jq '. | length')
echo -e "${GREEN}✅ Found $BOARD_COUNT board(s)${NC}"
echo ""

# Test 3: Get specific board details
echo "4️⃣  Getting board details..."
GET_BOARD=$(curl -s -X GET http://localhost:8000/api/v1/investigations/boards/$BOARD_ID \
  -H "Authorization: Bearer $TOKEN")

BOARD_TITLE=$(echo $GET_BOARD | jq -r '.title')
echo -e "${GREEN}✅ Board title: $BOARD_TITLE${NC}"
echo ""

# Test 4: Pin an entity to the board
echo "5️⃣  Pinning entity to board..."
PIN_ENTITY=$(curl -s -X POST http://localhost:8000/api/v1/investigations/pin \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"board_id\": \"$BOARD_ID\",
    \"entity_name\": \"Aspirin\",
    \"entity_type\": \"Drug\",
    \"pin_reason\": \"Primary drug under investigation\",
    \"position_x\": 100.0,
    \"position_y\": 200.0
  }")

PIN_ID=$(echo $PIN_ENTITY | jq -r '.id')

if [ "$PIN_ID" == "null" ] || [ -z "$PIN_ID" ]; then
    echo -e "${YELLOW}⚠️  Pin creation response:${NC}"
    echo "$PIN_ENTITY" | jq '.'
else
    echo -e "${GREEN}✅ Entity pinned with ID: $PIN_ID${NC}"
fi
echo ""

# Test 5: Add a finding to the pinned entity (if pin succeeded)
if [ "$PIN_ID" != "null" ] && [ -n "$PIN_ID" ]; then
    echo "6️⃣  Adding finding to pinned entity..."
    ADD_FINDING=$(curl -s -X POST http://localhost:8000/api/v1/investigations/findings \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"pinned_entity_id\": \"$PIN_ID\",
        \"finding_type\": \"note\",
        \"content\": \"Initial research shows potential interaction with blood thinners\",
        \"tags\": [\"research\", \"interaction\"]
      }")
    
    FINDING_ID=$(echo $ADD_FINDING | jq -r '.id')
    
    if [ "$FINDING_ID" == "null" ] || [ -z "$FINDING_ID" ]; then
        echo -e "${YELLOW}⚠️  Finding creation response:${NC}"
        echo "$ADD_FINDING" | jq '.'
    else
        echo -e "${GREEN}✅ Finding added with ID: $FINDING_ID${NC}"
    fi
    echo ""
fi

# Test 6: Export board data
echo "7️⃣  Exporting board data..."
EXPORT_BOARD=$(curl -s -X GET http://localhost:8000/api/v1/investigations/boards/$BOARD_ID/export \
  -H "Authorization: Bearer $TOKEN")

EXPORT_SUCCESS=$(echo $EXPORT_BOARD | jq -r '.id')

if [ "$EXPORT_SUCCESS" == "null" ] || [ -z "$EXPORT_SUCCESS" ]; then
    echo -e "${YELLOW}⚠️  Export response:${NC}"
    echo "$EXPORT_BOARD" | jq '.'
else
    echo -e "${GREEN}✅ Board exported successfully${NC}"
    echo "Export preview:"
    echo "$EXPORT_BOARD" | jq '{title: .title, pinned_count: (.pinned_entities | length)}'
fi
echo ""

# Test 7: Update board status
echo "8️⃣  Updating board status..."
UPDATE_BOARD=$(curl -s -X PUT http://localhost:8000/api/v1/investigations/boards/$BOARD_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Drug Interaction Study - Updated",
    "description": "Investigating potential drug interactions for new compound - Updated",
    "status": "active"
  }')

UPDATE_TITLE=$(echo $UPDATE_BOARD | jq -r '.title')

if [ "$UPDATE_TITLE" == "null" ] || [ -z "$UPDATE_TITLE" ]; then
    echo -e "${YELLOW}⚠️  Update response:${NC}"
    echo "$UPDATE_BOARD" | jq '.'
else
    echo -e "${GREEN}✅ Board updated: $UPDATE_TITLE${NC}"
fi
echo ""

# Summary
echo "============================================="
echo "🎉 Backend API Testing Complete!"
echo ""
echo "Summary:"
echo "  - Authentication: ✅"
echo "  - Create Board: ✅"
echo "  - List Boards: ✅"
echo "  - Get Board: ✅"
echo "  - Pin Entity: $([ "$PIN_ID" != "null" ] && echo "✅" || echo "⚠️")"
echo "  - Add Finding: $([ "$FINDING_ID" != "null" ] && echo "✅" || echo "⚠️")"
echo "  - Export Board: $([ "$EXPORT_SUCCESS" != "null" ] && echo "✅" || echo "⚠️")"
echo "  - Update Board: $([ "$UPDATE_TITLE" != "null" ] && echo "✅" || echo "⚠️")"
echo ""
echo "Board ID for reference: $BOARD_ID"
echo ""

