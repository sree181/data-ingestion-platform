#!/bin/bash

echo "======================================"
echo "Phase 2 Backend: Entity Chat API Test"
echo "======================================"
echo ""

# Wait for API Gateway
echo "⏳ Waiting for API Gateway to start..."
sleep 15

# Get JWT token
echo "🔐 Getting JWT token..."
JWT_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"admin123"}' | jq -r '.access_token')

if [ "$JWT_TOKEN" == "null" ] || [ -z "$JWT_TOKEN" ]; then
  echo "❌ Failed to get JWT token"
  exit 1
fi
echo "✅ JWT token obtained"
echo ""

# Test: Chat with entity
echo "💬 Test: Chat with entity 'Adverse drug reaction'"
CHAT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this entity about?",
    "conversation_history": [],
    "space_id": null
  }' \
  "http://localhost:8000/api/v1/knowledge-hub/entity/Adverse%20drug%20reaction/chat")

echo "$CHAT_RESPONSE" | jq '{
  success,
  entity_name,
  response_preview: (.response[:150] + "..."),
  source_count: (.sources | length),
  first_source: .sources[0].title
}'

echo ""
echo "Full response:"
echo "$CHAT_RESPONSE" | jq '.response'

echo ""
echo "======================================"
if echo "$CHAT_RESPONSE" | jq -e '.success == true' > /dev/null; then
  echo "✅ Phase 2 Backend: CHAT API WORKING!"
else
  echo "❌ Phase 2 Backend: CHAT API FAILED"
  echo "Error details:"
  echo "$CHAT_RESPONSE" | jq '.error // .detail // "Unknown error"'
fi
echo "======================================"

