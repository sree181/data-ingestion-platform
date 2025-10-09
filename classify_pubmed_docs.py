#!/usr/bin/env python3
"""
Classify existing PubMed documents using OpenAI GPT-4
"""
import requests
import json
from datetime import datetime

ELASTICSEARCH_URL = "http://localhost:9200"
# Use ensemble endpoint for better performance (2.2x faster, 75% cost savings)
CLASSIFICATION_URL = "http://localhost:8012/api/v1/classify/ensemble"

def get_pubmed_documents():
    """Get all PubMed documents from Elasticsearch"""
    response = requests.get(
        f"{ELASTICSEARCH_URL}/documents/_search",
        headers={"Content-Type": "application/json"},
        json={
            "query": {"wildcard": {"title.keyword": "PubMed:*"}},
            "size": 100,
            "_source": ["document_id", "title", "content", "abstract"]
        }
    )
    
    if response.status_code == 200:
        hits = response.json()["hits"]["hits"]
        return [hit["_source"] for hit in hits]
    return []

def classify_document(doc):
    """Classify a document using the PV classification service"""
    doc_id = doc.get("document_id", "unknown")
    title = doc.get("title", "")
    content = doc.get("content", doc.get("abstract", ""))
    
    # Limit content to first 2000 characters
    content = content[:2000] if content else ""
    
    print(f"\n📄 Classifying: {title}")
    print(f"   ID: {doc_id}")
    
    try:
        response = requests.post(
            CLASSIFICATION_URL,
            headers={"Content-Type": "application/json"},
            json={
                "document": {
                    "id": doc_id,
                    "title": title,
                    "abstract": content,
                    "mesh_terms": [],
                    "publication_types": ["Case Reports"]
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            classification = result["classification"]
            ensemble_meta = result.get("ensemble_metadata", {})
            
            label = classification["classification"]
            confidence = classification["confidence"]
            entities = classification.get("key_entities", [])
            
            # Log ensemble information
            models_used = ensemble_meta.get("models_used", [])
            processing_time = ensemble_meta.get("processing_time_ms", 0)
            cost = ensemble_meta.get("cost_estimate", 0.0)
            
            print(f"   ✅ {label} ({confidence:.2f} confidence)")
            print(f"   ⚡ Models: {', '.join(models_used)} | Time: {processing_time}ms | Cost: ${cost:.4f}")
            print(f"   📊 {len(entities)} entities extracted")
            
            return {
                "classification": label,
                "confidence": confidence,
                "entities": entities,
                "classified_at": datetime.utcnow().isoformat(),
                "ensemble_models_used": models_used,
                "processing_time_ms": processing_time,
                "classification_cost": cost
            }
        else:
            print(f"   ❌ Classification API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def update_elasticsearch(doc_id, classification_data):
    """Update document in Elasticsearch with classification"""
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/documents/_update_by_query",
            headers={"Content-Type": "application/json"},
            json={
                "script": {
                    "source": """
                        ctx._source.classification = params.classification;
                        ctx._source.classification_confidence = params.confidence;
                        ctx._source.classification_entities = params.entities;
                        ctx._source.classified_at = params.classified_at;
                        ctx._source.ensemble_models_used = params.ensemble_models_used;
                        ctx._source.processing_time_ms = params.processing_time_ms;
                        ctx._source.classification_cost = params.classification_cost;
                    """,
                    "params": classification_data
                },
                "query": {"term": {"document_id.keyword": doc_id}}
            }
        )
        
        if response.status_code == 200:
            updated = response.json().get("updated", 0)
            print(f"   💾 Updated {updated} document(s) in Elasticsearch")
            return True
        else:
            print(f"   ❌ Elasticsearch update failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Elasticsearch error: {str(e)}")
        return False

def main():
    print("🔍 Finding PubMed documents...")
    documents = get_pubmed_documents()
    print(f"   Found {len(documents)} PubMed documents")
    
    if not documents:
        print("   No documents to classify")
        return
    
    print("\n🤖 Starting classification...")
    
    classified = 0
    failed = 0
    
    for doc in documents:
        doc_id = doc.get("document_id")
        if not doc_id:
            print(f"\n⚠️  Skipping document without ID: {doc.get('title', 'unknown')}")
            continue
        
        classification_data = classify_document(doc)
        
        if classification_data:
            if update_elasticsearch(doc_id, classification_data):
                classified += 1
            else:
                failed += 1
        else:
            failed += 1
    
    print(f"\n\n🎉 Classification complete!")
    print(f"   ✅ Classified: {classified}")
    print(f"   ❌ Failed: {failed}")
    print(f"\n📊 View results at: http://localhost:3000/documents")

if __name__ == "__main__":
    main()
