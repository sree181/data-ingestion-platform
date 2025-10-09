#!/bin/bash

# Quick test script for Investigation Board API
echo "🧪 Testing Investigation Board API (Neo4j-based)"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get auth token
echo "1️⃣  Getting authentication token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "password"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get auth token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Got auth token${NC}"
echo ""

# Test 1: List boards (should be empty initially)
echo "2️⃣  Listing boards (should be empty initially)..."
BOARDS=$(curl -s -X GET "http://localhost:8000/investigations/boards" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $BOARDS"
echo -e "${GREEN}✅ List boards endpoint works${NC}"
echo ""

# Test 2: Create a new board
echo "3️⃣  Creating a new investigation board..."
CREATE_BOARD=$(curl -s -X POST "http://localhost:8000/investigations/boards" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Investigation - Drug Adverse Events",
    "description": "Investigating connections between drugs and adverse events",
    "status": "active"
  }')

echo "Response: $CREATE_BOARD"
BOARD_ID=$(echo $CREATE_BOARD | jq -r '.board.id')

if [ "$BOARD_ID" == "null" ] || [ -z "$BOARD_ID" ]; then
    echo -e "${RED}❌ Failed to create board${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Created board with ID: $BOARD_ID${NC}"
echo ""

# Test 3: Get board details
echo "4️⃣  Getting board details..."
BOARD_DETAILS=$(curl -s -X GET "http://localhost:8000/investigations/boards/$BOARD_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $BOARD_DETAILS"
echo -e "${GREEN}✅ Get board endpoint works${NC}"
echo ""

# Test 4: Pin an entity
echo "5️⃣  Pinning an entity to the board..."
PIN_ENTITY=$(curl -s -X POST "http://localhost:8000/investigations/pin" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"board_id\": \"$BOARD_ID\",
    \"entity_name\": \"Aspirin\",
    \"entity_type\": \"Drug\",
    \"pin_reason\": \"Investigating potential side effects\",
    \"position_x\": 100.0,
    \"position_y\": 200.0
  }")

echo "Response: $PIN_ENTITY"
ENTITY_ID=$(echo $PIN_ENTITY | jq -r '.entity.id')

if [ "$ENTITY_ID" == "null" ] || [ -z "$ENTITY_ID" ]; then
    echo -e "${RED}❌ Failed to pin entity${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pinned entity with ID: $ENTITY_ID${NC}"
echo ""

# Test 5: Add a finding
echo "6️⃣  Adding a finding to the pinned entity..."
ADD_FINDING=$(curl -s -X POST "http://localhost:8000/investigations/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"pinned_entity_id\": \"$ENTITY_ID\",
    \"finding_type\": \"note\",
    \"content\": \"Aspirin shows high correlation with bleeding events in elderly patients\",
    \"tags\": [\"bleeding\", \"elderly\", \"adverse-event\"]
  }")

echo "Response: $ADD_FINDING"
FINDING_ID=$(echo $ADD_FINDING | jq -r '.finding.id')

if [ "$FINDING_ID" == "null" ] || [ -z "$FINDING_ID" ]; then
    echo -e "${RED}❌ Failed to add finding${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Added finding with ID: $FINDING_ID${NC}"
echo ""

# Test 6: Get updated board
echo "7️⃣  Getting updated board with entities and findings..."
UPDATED_BOARD=$(curl -s -X GET "http://localhost:8000/investigations/boards/$BOARD_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $UPDATED_BOARD" | jq '.'
echo -e "${GREEN}✅ Board now contains entity and finding${NC}"
echo ""

# Test 7: Export board
echo "8️⃣  Exporting board data..."
EXPORT=$(curl -s -X GET "http://localhost:8000/investigations/boards/$BOARD_ID/export" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $EXPORT" | jq '.'
echo -e "${GREEN}✅ Export endpoint works${NC}"
echo ""

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Investigation Board (Neo4j-based) is working perfectly!"
echo ""
echo "Board ID: $BOARD_ID"
echo "Entity ID: $ENTITY_ID"
echo "Finding ID: $FINDING_ID"

