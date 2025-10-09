#!/bin/bash

echo "======================================================================"
echo "PV Classification Service - Quick Test Script"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: PV Classification Service Health Check${NC}"
echo "----------------------------------------------------------------------"
curl -s http://localhost:8012/health | jq '.'
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service is healthy${NC}"
else
    echo -e "${RED}✗ Service health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Get Available Domains
echo -e "${YELLOW}Test 2: Get Available Domains${NC}"
echo "----------------------------------------------------------------------"
curl -s http://localhost:3000/api/v1/pv-classification/domains | jq '.domains[] | {id, name}'
echo ""

# Test 3: Classify Test Document (ICSR)
echo -e "${YELLOW}Test 3: Classify Test Document - ICSR Case${NC}"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8012/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "document": {
      "id": "test_icsr_001",
      "title": "Severe hepatotoxicity following paracetamol overdose in a 32-year-old male",
      "abstract": "We report a case of acute liver failure in a 32-year-old male patient following accidental paracetamol overdose. Patient presented with jaundice, elevated liver enzymes (ALT 2500 U/L), and altered mental status 48 hours after ingestion of 20g paracetamol. Patient was hospitalized and treated with N-acetylcysteine. Liver function gradually improved over 2 weeks.",
      "mesh_terms": ["Chemical and Drug Induced Liver Injury", "Acetaminophen", "Acute Liver Failure"],
      "publication_types": ["Case Reports"]
    }
  }' | jq '{
    classification: .classification.classification,
    confidence: .classification.confidence,
    reasoning: .classification.reasoning,
    entities: .classification.key_entities | length
  }'
echo ""

# Test 4: Classify Test Document (Non-ICSR)
echo -e "${YELLOW}Test 4: Classify Test Document - Non-ICSR (Review)${NC}"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8012/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "document": {
      "id": "test_non_icsr_001",
      "title": "Systematic review and meta-analysis of drug-induced liver injury",
      "abstract": "This systematic review examines the epidemiology and risk factors of drug-induced liver injury across multiple studies. We analyzed 45 randomized controlled trials involving 15,000 patients. Results showed varying incidence rates across different drug classes.",
      "mesh_terms": ["Chemical and Drug Induced Liver Injury", "Systematic Review"],
      "publication_types": ["Review", "Meta-Analysis"]
    }
  }' | jq '{
    classification: .classification.classification,
    confidence: .classification.confidence,
    reasoning: .classification.reasoning
  }'
echo ""

# Test 5: Get Service Statistics
echo -e "${YELLOW}Test 5: Get Service Statistics${NC}"
echo "----------------------------------------------------------------------"
curl -s http://localhost:8012/api/v1/stats | jq '.'
echo ""

echo "======================================================================"
echo -e "${GREEN}All tests completed!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Run full ingestion: curl -X POST http://localhost:3000/api/v1/pv-classification/ingest-and-classify"
echo "2. Check Elasticsearch: curl http://localhost:9200/documents/_search?q=project_id:icsr"
echo "3. View in Document Library UI"
echo ""


