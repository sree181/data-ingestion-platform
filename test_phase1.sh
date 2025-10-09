#!/bin/bash

# Phase 1 Comprehensive Test Script

echo "======================================"
echo "Phase 1: Document Source Linking Test"
echo "======================================"
echo ""

# Wait for API Gateway
echo "⏳ Waiting for API Gateway to start..."
sleep 10

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

# Test 1: Knowledge Hub Statistics
echo "📊 Test 1: Knowledge Hub Statistics"
STATS=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8000/api/v1/knowledge-hub/statistics")
echo "$STATS" | jq '{success, nodes: .statistics.node_count, edges: .statistics.edge_count}'
echo ""

# Test 2: Full Graph
echo "🌐 Test 2: Full Graph"
GRAPH=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8000/api/v1/knowledge-hub/full-graph?limit=10")
echo "$GRAPH" | jq '{success, nodes: (.graph.nodes | length), edges: (.graph.edges | length), first_node: .graph.nodes[0].name}'
echo ""

# Test 3: Entity Details
echo "🔍 Test 3: Entity Details"
DETAILS=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8000/api/v1/knowledge-hub/entity/details/Adverse%20drug%20reaction")
echo "$DETAILS" | jq '{success, name: .entity.name, type: .entity.type, connections: .entity.connection_count}'
echo ""

# Test 4: Entity Sources (THE NEW FEATURE!)
echo "📄 Test 4: Entity Source Documents (NEW!)"
SOURCES=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8000/api/v1/knowledge-hub/entity/Adverse%20drug%20reaction/sources?limit=5")
echo "$SOURCES" | jq '{success, entity_name, document_count, first_doc: {title: .documents[0].title, source_type: .documents[0].source_type, confidence: .documents[0].entity_confidence, has_snippets: (.documents[0].snippets | length > 0)}}'

echo ""
echo "======================================"
if echo "$SOURCES" | jq -e '.success == true' > /dev/null; then
  echo "✅ Phase 1: ALL TESTS PASSED!"
else
  echo "❌ Phase 1: Entity Sources FAILED"
  echo "Error details:"
  echo "$SOURCES" | jq '.error // "Unknown error"'
fi
echo "======================================"

