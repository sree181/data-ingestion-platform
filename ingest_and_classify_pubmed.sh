#!/bin/bash

# Script to ingest PubMed articles and classify them for PV
# Uses the existing working PubMed integration service

echo "🔐 Logging in..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Logged in successfully"
echo ""

# Step 1: Ingest PubMed articles using existing service
echo "📚 Step 1: Ingesting PubMed articles (Drug-Induced Liver Injury)..."
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8005/api/v1/pubmed/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Drug-Induced Liver Injury[MeSH] AND Case Reports[PT]",
    "max_results": 5,
    "space_id": "icsr",
    "article_types": ["Case Reports"]
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "  Job ID: $JOB_ID"
echo "  Waiting for ingestion to complete..."

# Poll for completion
for i in {1..30}; do
  sleep 2
  STATUS=$(curl -s "http://localhost:8005/api/v1/pubmed/jobs/$JOB_ID" | jq -r '.status')
  PROCESSED=$(curl -s "http://localhost:8005/api/v1/pubmed/jobs/$JOB_ID" | jq -r '.processed_articles')
  TOTAL=$(curl -s "http://localhost:8005/api/v1/pubmed/jobs/$JOB_ID" | jq -r '.total_articles')
  
  echo "  Status: $STATUS | Processed: $PROCESSED/$TOTAL"
  
  if [ "$STATUS" == "completed" ]; then
    echo "✅ Ingestion completed!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "❌ Ingestion failed"
    exit 1
  fi
done

echo ""

# Step 2: Get ingested document IDs from Elasticsearch
echo "📊 Step 2: Finding ingested documents..."
DOC_IDS=$(curl -s -X GET "http://localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"term": {"metadata.source.keyword": "pubmed"}},
    "size": 100,
    "_source": ["document_id", "title"],
    "sort": [{"upload_date": {"order": "desc"}}]
  }' | jq -r '.hits.hits[]._source.document_id')

DOC_COUNT=$(echo "$DOC_IDS" | wc -l | tr -d ' ')
echo "  Found $DOC_COUNT documents"
echo ""

# Step 3: Classify each document
echo "🤖 Step 3: Classifying documents with OpenAI GPT-4..."
CLASSIFIED=0
FAILED=0

for DOC_ID in $DOC_IDS; do
  # Get document details
  DOC=$(curl -s -X GET "http://localhost:9200/documents/_search" \
    -H "Content-Type: application/json" \
    -d "{
      \"query\": {\"term\": {\"document_id.keyword\": \"$DOC_ID\"}},
      \"size\": 1
    }" | jq -r '.hits.hits[0]._source')
  
  TITLE=$(echo "$DOC" | jq -r '.title // ""')
  ABSTRACT=$(echo "$DOC" | jq -r '.abstract // .content // ""')
  PMID=$(echo "$DOC" | jq -r '.metadata.pmid // ""')
  
  echo "  Classifying: $TITLE"
  
  # Call classification service
  CLASSIFICATION=$(curl -s -X POST "http://localhost:8012/api/v1/classify" \
    -H "Content-Type: application/json" \
    -d "{
      \"document\": {
        \"id\": \"$DOC_ID\",
        \"title\": $(echo "$TITLE" | jq -R .),
        \"abstract\": $(echo "$ABSTRACT" | jq -R .),
        \"mesh_terms\": [],
        \"publication_types\": [\"Case Reports\"]
      }
    }")
  
  if [ $? -eq 0 ]; then
    CLASS=$(echo "$CLASSIFICATION" | jq -r '.classification.classification // "unknown"')
    CONF=$(echo "$CLASSIFICATION" | jq -r '.classification.confidence // 0')
    ENTITIES=$(echo "$CLASSIFICATION" | jq -r '.classification.key_entities // []')
    
    if [ "$CLASS" != "unknown" ] && [ "$CLASS" != "null" ]; then
      # Update Elasticsearch with classification
      curl -s -X POST "http://localhost:9200/documents/_update_by_query" \
        -H "Content-Type: application/json" \
        -d "{
          \"script\": {
            \"source\": \"ctx._source.classification = params.classification; ctx._source.classification_confidence = params.confidence; ctx._source.classification_entities = params.entities; ctx._source.classified_at = params.classified_at\",
            \"params\": {
              \"classification\": \"$CLASS\",
              \"confidence\": $CONF,
              \"entities\": $ENTITIES,
              \"classified_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
            }
          },
          \"query\": {\"term\": {\"document_id.keyword\": \"$DOC_ID\"}}
        }" > /dev/null
      
      echo "    ✅ $CLASS ($CONF confidence)"
      CLASSIFIED=$((CLASSIFIED + 1))
    else
      echo "    ❌ Classification failed"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "    ❌ API error"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "🎉 Classification complete!"
echo "  ✅ Classified: $CLASSIFIED"
echo "  ❌ Failed: $FAILED"
echo ""
echo "📊 View results at: http://localhost:3000/documents"

