#!/bin/bash

echo "🧪 Testing Workflow Builder with REAL DATA"
echo "=========================================="
echo ""

# Create a test workflow
WORKFLOW_JSON='{
  "workflow_id": "test_real_data_'$(date +%s)'",
  "nodes": [
    {
      "id": "node1",
      "type": "upload",
      "position": {"x": 100, "y": 200},
      "data": {"label": "Load Documents", "type": "upload"}
    },
    {
      "id": "node2",
      "type": "aiProcessing",
      "position": {"x": 400, "y": 200},
      "data": {"label": "AI Analysis", "type": "aiProcessing"}
    },
    {
      "id": "node3",
      "type": "knowledgeGraph",
      "position": {"x": 700, "y": 200},
      "data": {"label": "Knowledge Graph", "type": "knowledgeGraph"}
    },
    {
      "id": "node4",
      "type": "report",
      "position": {"x": 1000, "y": 200},
      "data": {"label": "Generate Report", "type": "report"}
    }
  ],
  "edges": [
    {"id": "e1-2", "source": "node1", "target": "node2"},
    {"id": "e2-3", "source": "node2", "target": "node3"},
    {"id": "e3-4", "source": "node3", "target": "node4"}
  ]
}'

echo "📤 Starting workflow execution..."
RESPONSE=$(curl -s -X POST http://localhost:8008/api/v1/workflows/execute \
  -H "Content-Type: application/json" \
  -d "$WORKFLOW_JSON")

echo "$RESPONSE" | jq .

EXECUTION_ID=$(echo "$RESPONSE" | jq -r '.execution_id')

if [ "$EXECUTION_ID" != "null" ]; then
  echo ""
  echo "✅ Workflow started! Execution ID: $EXECUTION_ID"
  echo ""
  echo "📊 Monitoring execution status..."
  echo ""
  
  for i in {1..15}; do
    sleep 2
    STATUS=$(curl -s "http://localhost:8008/api/v1/workflows/execution/$EXECUTION_ID/status")
    
    WORKFLOW_STATUS=$(echo "$STATUS" | jq -r '.execution.status')
    echo "[$i] Workflow Status: $WORKFLOW_STATUS"
    
    # Show node statuses
    echo "$STATUS" | jq -r '.execution.nodes | to_entries[] | "  - \(.key): \(.value.status)"'
    
    if [ "$WORKFLOW_STATUS" == "completed" ] || [ "$WORKFLOW_STATUS" == "failed" ]; then
      echo ""
      echo "🎉 Workflow $WORKFLOW_STATUS!"
      echo ""
      echo "📋 FINAL RESULTS:"
      echo "================"
      echo "$STATUS" | jq '.execution'
      break
    fi
  done
else
  echo "❌ Failed to start workflow"
fi
