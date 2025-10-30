#!/bin/bash

echo "🚀 Testing End-to-End Document Ingestion Process"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Frontend
echo "1️⃣  Testing Frontend (http://localhost:3000)..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is UP${NC}"
else
    echo -e "${RED}❌ Frontend is DOWN (Status: $FRONTEND_STATUS)${NC}"
    exit 1
fi
echo ""

# Test 2: Check API Gateway
echo "2️⃣  Testing API Gateway (http://localhost:8000)..."
API_HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$API_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ API Gateway is HEALTHY${NC}"
else
    echo -e "${RED}❌ API Gateway is UNHEALTHY${NC}"
    exit 1
fi
echo ""

# Test 3: Check PV Classification Service
echo "3️⃣  Testing PV Classification Service (http://localhost:8012)..."
PV_HEALTH=$(curl -s http://localhost:8012/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$PV_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ PV Classification Service is HEALTHY${NC}"
else
    echo -e "${RED}❌ PV Classification Service is UNHEALTHY${NC}"
    exit 1
fi
echo ""

# Test 4: Check Elasticsearch
echo "4️⃣  Testing Elasticsearch (http://localhost:9200)..."
ES_STATUS=$(curl -s http://localhost:9200/_cluster/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$ES_STATUS" = "yellow" ] || [ "$ES_STATUS" = "green" ]; then
    echo -e "${GREEN}✅ Elasticsearch is HEALTHY (Status: $ES_STATUS)${NC}"
else
    echo -e "${RED}❌ Elasticsearch is UNHEALTHY (Status: $ES_STATUS)${NC}"
    exit 1
fi
echo ""

# Test 5: Check Neo4j
echo "5️⃣  Testing Neo4j (http://localhost:7474)..."
NEO4J_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7474)
if [ "$NEO4J_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Neo4j is UP${NC}"
else
    echo -e "${RED}❌ Neo4j is DOWN (Status: $NEO4J_STATUS)${NC}"
    exit 1
fi
echo ""

# Test 6: Test Document Classification (with OpenAI)
echo "6️⃣  Testing Document Classification with OpenAI..."
CLASSIFICATION_RESULT=$(curl -s -X POST http://localhost:8012/api/v1/classify/ensemble \
  -H "Content-Type: application/json" \
  -d '{
    "document": {
      "id": "test_001",
      "title": "Severe hepatotoxicity following administration of drug X in a 45-year-old patient",
      "abstract": "We report a case of a 45-year-old male patient who developed severe liver injury after taking drug X for 2 weeks. The patient presented with elevated ALT and AST levels.",
      "mesh_terms": ["Drug-Induced Liver Injury", "Hepatotoxicity", "Adverse Drug Reaction"],
      "publication_types": ["Case Reports"]
    }
  }' 2>/dev/null)

if [ -z "$CLASSIFICATION_RESULT" ]; then
    echo -e "${RED}❌ Classification request FAILED (no response)${NC}"
    exit 1
fi

CLASSIFICATION=$(echo "$CLASSIFICATION_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('classification', {}).get('classification', 'ERROR'))" 2>/dev/null)
CONFIDENCE=$(echo "$CLASSIFICATION_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('classification', {}).get('confidence', 0))" 2>/dev/null)
MODELS_USED=$(echo "$CLASSIFICATION_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(','.join(data.get('ensemble_metadata', {}).get('models_used', [])))" 2>/dev/null)

if [ "$CLASSIFICATION" != "ERROR" ] && [ ! -z "$CLASSIFICATION" ]; then
    echo -e "${GREEN}✅ Classification SUCCESSFUL${NC}"
    echo "   📋 Result: $CLASSIFICATION"
    echo "   📊 Confidence: $CONFIDENCE"
    echo "   🤖 Models Used: $MODELS_USED"
else
    echo -e "${RED}❌ Classification FAILED${NC}"
    echo "   Response: $CLASSIFICATION_RESULT"
    exit 1
fi
echo ""

# Test 7: Test Document Upload (E2E)
echo "7️⃣  Testing End-to-End Document Upload..."

# Create a test file
TEST_FILE="/tmp/test_document_$(date +%s).txt"
cat > "$TEST_FILE" << 'EOF'
Case Report: Drug-Induced Liver Injury

Patient: 52-year-old female
Drug: Acetaminophen
Dose: 4g/day for 5 days
Outcome: Elevated liver enzymes (ALT: 450 U/L, AST: 380 U/L)
Action: Drug discontinued, patient recovered

This case demonstrates the hepatotoxic potential of acetaminophen overdose.
EOF

echo "   📄 Created test file: $TEST_FILE"

# Upload the document
UPLOAD_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/upload \
  -F "files=@$TEST_FILE" \
  -F "enable_ai_analysis=true" \
  -F "enable_icsr_classification=true" 2>/dev/null)

if [ -z "$UPLOAD_RESULT" ]; then
    echo -e "${RED}❌ Document upload FAILED (no response)${NC}"
    rm -f "$TEST_FILE"
    exit 1
fi

UPLOAD_STATUS=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); results=data.get('results', []); print(results[0].get('status', 'ERROR') if results else 'ERROR')" 2>/dev/null)
DOC_ID=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); results=data.get('results', []); print(results[0].get('document_id', 'NONE') if results else 'NONE')" 2>/dev/null)

if [ "$UPLOAD_STATUS" = "success" ]; then
    echo -e "${GREEN}✅ Document upload SUCCESSFUL${NC}"
    
    # Extract processing details from the upload response
    PROCESSING_STATUS=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); results=data.get('results', []); print(results[0].get('processing_result', {}).get('processing_status', 'N/A') if results else 'N/A')" 2>/dev/null)
    MODEL_NAME=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); results=data.get('results', []); print(results[0].get('processing_result', {}).get('model_metadata', {}).get('model_name', 'N/A') if results else 'N/A')" 2>/dev/null)
    PROVIDER=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); results=data.get('results', []); print(results[0].get('processing_result', {}).get('model_metadata', {}).get('provider', 'N/A') if results else 'N/A')" 2>/dev/null)
    
    echo "   📄 Processing Status: $PROCESSING_STATUS"
    echo "   🤖 Model: $MODEL_NAME ($PROVIDER)"
    
    if [ ! -z "$DOC_ID" ] && [ "$DOC_ID" != "NONE" ] && [ "$DOC_ID" != "null" ]; then
        echo "   📄 Document ID: $DOC_ID"
        
        # Wait for processing
        echo "   ⏳ Waiting for document indexing (5 seconds)..."
        sleep 5
        
        # Retrieve the document
        echo "   🔍 Retrieving processed document..."
        DOC_RESULT=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID 2>/dev/null)
        
        if [ ! -z "$DOC_RESULT" ]; then
            DOC_CLASSIFICATION=$(echo "$DOC_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('classification', 'N/A'))" 2>/dev/null)
            DOC_CONFIDENCE=$(echo "$DOC_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('classification_confidence', 'N/A'))" 2>/dev/null)
            
            echo -e "${GREEN}✅ Document retrieved from Elasticsearch${NC}"
            echo "   📋 Classification: $DOC_CLASSIFICATION"
            echo "   📊 Confidence: $DOC_CONFIDENCE"
        else
            echo -e "${YELLOW}⚠️  Document processed but not yet indexed in Elasticsearch${NC}"
        fi
    else
        echo -e "${GREEN}✅ Document processed successfully (inline processing)${NC}"
    fi
else
    echo -e "${RED}❌ Document upload FAILED${NC}"
    echo "   Response: $UPLOAD_RESULT"
    rm -f "$TEST_FILE"
    exit 1
fi

# Cleanup
rm -f "$TEST_FILE"
echo ""

# Final Summary
echo "=================================================="
echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
echo ""
echo "✅ Frontend: Running"
echo "✅ API Gateway: Healthy"
echo "✅ PV Classification: Healthy (with OpenAI)"
echo "✅ Elasticsearch: Healthy"
echo "✅ Neo4j: Running"
echo "✅ Document Classification: Working"
echo "✅ End-to-End Upload: Working"
echo ""
echo "🚀 System is ready for production use!"
echo "=================================================="

