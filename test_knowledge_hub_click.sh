#!/bin/bash

# ============================================================================
# Knowledge Hub Node Click Test Script
# Tests the complete flow: Node Click → Source Documents → Chat
# ============================================================================

set -e

API_BASE="http://localhost:8000"
ENTITY_NAME="bnt162b2 vaccine"  # From the screenshot

echo "=============================================="
echo "  Knowledge Hub Node Click Test"
echo "=============================================="
echo ""

# Step 1: Get full graph to find entity ID
echo "📊 Step 1: Loading full knowledge graph..."
GRAPH_RESPONSE=$(curl -s "${API_BASE}/api/v1/knowledge-hub/full-graph?limit=500")
echo "✅ Graph loaded"
echo ""

# Extract entity ID for "bnt162b2 vaccine"
ENTITY_ID=$(echo "$GRAPH_RESPONSE" | jq -r '.graph.nodes[] | select(.name | ascii_downcase | contains("bnt162b2")) | .id' | head -1)

if [ -z "$ENTITY_ID" ] || [ "$ENTITY_ID" = "null" ]; then
    echo "❌ ERROR: Could not find entity 'bnt162b2 vaccine' in graph"
    echo "Available entities:"
    echo "$GRAPH_RESPONSE" | jq -r '.graph.nodes[].name' | head -20
    exit 1
fi

echo "✅ Found entity ID: $ENTITY_ID"
echo ""

# Step 2: Test source documents endpoint
echo "📄 Step 2: Testing source documents endpoint..."
echo "GET ${API_BASE}/api/v1/knowledge-hub/entities/${ENTITY_ID}/source-documents"
echo ""

SOURCES_RESPONSE=$(curl -s "${API_BASE}/api/v1/knowledge-hub/entities/${ENTITY_ID}/source-documents")
echo "$SOURCES_RESPONSE" | jq '.'
echo ""

# Check if documents were found
DOC_COUNT=$(echo "$SOURCES_RESPONSE" | jq -r '.document_count // 0')
SUCCESS=$(echo "$SOURCES_RESPONSE" | jq -r '.success // false')

if [ "$SUCCESS" = "true" ] && [ "$DOC_COUNT" -gt 0 ]; then
    echo "✅ SUCCESS: Found $DOC_COUNT source documents"
    echo ""
    echo "Sample documents:"
    echo "$SOURCES_RESPONSE" | jq -r '.documents[] | "  - \(.title // .filename)"' | head -5
else
    echo "⚠️  WARNING: No source documents found"
    echo "Response:"
    echo "$SOURCES_RESPONSE" | jq '.'
fi
echo ""

# Step 3: Test chat endpoint
echo "💬 Step 3: Testing chat with entity..."
CHAT_PAYLOAD=$(cat <<EOF
{
  "message": "What are the side effects?",
  "conversation_history": []
}
EOF
)

echo "POST ${API_BASE}/api/v1/knowledge-hub/entity/${ENTITY_NAME}/chat"
echo ""

CHAT_RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/knowledge-hub/entity/${ENTITY_NAME}/chat" \
  -H "Content-Type: application/json" \
  -d "$CHAT_PAYLOAD")

echo "$CHAT_RESPONSE" | jq '.'
echo ""

CHAT_SUCCESS=$(echo "$CHAT_RESPONSE" | jq -r '.success // false')
if [ "$CHAT_SUCCESS" = "true" ]; then
    echo "✅ Chat SUCCESS"
    echo "Response:"
    echo "$CHAT_RESPONSE" | jq -r '.response' | head -5
else
    echo "❌ Chat FAILED"
    echo "$CHAT_RESPONSE" | jq '.'
fi
echo ""

# Step 4: Summary
echo "=============================================="
echo "  Test Summary"
echo "=============================================="
echo ""
echo "Entity: $ENTITY_NAME"
echo "Entity ID: $ENTITY_ID"
echo "Source Documents: $DOC_COUNT"
echo "Chat Working: $CHAT_SUCCESS"
echo ""

if [ "$DOC_COUNT" -gt 0 ] && [ "$CHAT_SUCCESS" = "true" ]; then
    echo "✅ ALL TESTS PASSED - Ready for client demo!"
else
    echo "⚠️  SOME TESTS FAILED - Check logs above"
fi
echo ""
echo "=============================================="
echo ""
echo "🔍 To debug in browser:"
echo "1. Open http://localhost:3000/knowledge-hub"
echo "2. Switch to '3D WebGL' mode"
echo "3. Click on 'bnt162b2 vaccine' node"
echo "4. Open browser console (F12)"
echo "5. Check for logs starting with 🖱️, 📄, 💬"
echo ""
echo "Expected console logs:"
echo "  🖱️ Node clicked: bnt162b2 vaccine | Type: Drug | Node ID: $ENTITY_ID"
echo "  📄 Loading source documents for entity ID: $ENTITY_ID"
echo "  📦 Source documents API response: {...}"
echo "  ✅ Loaded X source documents"
echo ""

