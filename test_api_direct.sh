#!/bin/bash
# Get a valid JWT token first
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r '.access_token')

echo "Token: ${TOKEN:0:50}..."
echo ""

# Test the API endpoint
curl -s "http://localhost:8000/api/v1/knowledge-hub/entities/Medical%20Condition_pheochromocytoma%20multisystem%20crisis_upload_1/source-documents" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
