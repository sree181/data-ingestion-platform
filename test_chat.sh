#!/bin/bash

# Get JWT token
JWT_TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"admin123"}' | jq -r '.access_token')

echo "🔑 JWT Token obtained"

# Test chat with entity
echo ""
echo "💬 Testing entity chat..."
curl -X POST "http://localhost:3000/api/v1/knowledge-hub/entity/Urinary%20tract%20infections/chat" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this entity about?",
    "conversation_history": [],
    "space_id": null
  }' | jq '.'

