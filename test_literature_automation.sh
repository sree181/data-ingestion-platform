#!/bin/bash

echo "🧪 Testing Literature Automation Module"
echo "========================================"
echo ""

# Test 1: Check service health
echo "1️⃣ Testing Literature Service Health..."
curl -s http://localhost:8009/health | jq '.'
echo ""

# Test 2: Get available sources
echo "2️⃣ Getting Available Literature Sources..."
curl -s http://localhost:8009/api/v1/literature/sources | jq '.'
echo ""

# Test 3: Search literature (PubMed)
echo "3️⃣ Searching PubMed for 'COVID-19 vaccine'..."
curl -s -X POST http://localhost:8009/api/v1/literature/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "COVID-19 vaccine adverse events",
    "sources": ["pubmed"],
    "max_results": 3,
    "date_from": "2020-01-01"
  }' | jq '.articles | length'
echo " articles found"
echo ""

# Test 4: Classify an article
echo "4️⃣ Testing Article Classification..."
curl -s -X POST http://localhost:8009/api/v1/literature/classify \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "title": "Severe allergic reaction to COVID-19 vaccine in a 45-year-old patient",
      "abstract": "A 45-year-old patient experienced anaphylaxis 30 minutes after receiving the first dose of COVID-19 vaccine. Patient was treated with epinephrine and recovered.",
      "authors": ["Smith J", "Johnson A"],
      "journal": "Journal of Adverse Events",
      "publication_date": "2021-06-15",
      "pmid": "12345678"
    }
  }' | jq '.classification'
echo ""

# Test 5: Through API Gateway
echo "5️⃣ Testing via API Gateway..."
curl -s http://localhost:8000/api/v1/literature/sources | jq '.sources | length'
echo " sources configured"
echo ""

echo "✅ Literature Automation tests completed!"
echo ""

