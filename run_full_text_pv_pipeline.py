#!/usr/bin/env python3
"""
Complete PV Pipeline: Full-Text PubMed → Classification → ICSR Extraction → ES/Neo4j
"""

import sys
import os
sys.path.append('services/pubmed-integration')

from full_text_pubmed_ingestor import FullTextPubMedIngestor, PV_QUERIES
import requests
import json
# from elasticsearch import Elasticsearch
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ELASTICSEARCH_HOST = "http://localhost:9200"
PV_CLASSIFICATION_SERVICE = "http://localhost:8012"
API_GATEWAY = "http://localhost:8000"


def send_to_elasticsearch(article):
    """Store article in Elasticsearch using requests"""
    
    document = {
        "document_id": f"pubmed_{article.pmid}",
        "pmid": article.pmid,
        "pmcid": article.pmcid,
        "title": article.title,
        "abstract": article.abstract,
        "content": article.full_text or article.abstract,  # Use full text if available
        "authors": [{"name": author, "affiliation": None} for author in (article.authors or [])],
        "journal": article.journal,
        "publication_date": article.pub_date,
        "doi": article.doi,
        "mesh_terms": article.mesh_terms,
        "publication_types": article.publication_types,
        "source": "pubmed",
        "file_type": "pubmed_article",
        "has_full_text": article.has_full_text,
        "created_at": datetime.utcnow().isoformat(),
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/",
        "ai_processed": False
    }
    
    try:
        # Index document using requests
        response = requests.put(
            f"{ELASTICSEARCH_HOST}/documents/_doc/pubmed_{article.pmid}",
            json=document,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"✅ Stored {article.pmid} in Elasticsearch")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to store {article.pmid}: {str(e)}")
        return False


def classify_document(article):
    """Classify document using PV Classification Service"""
    
    payload = {
        "document": {
            "id": f"pubmed_{article.pmid}",
            "title": article.title,
            "abstract": article.full_text or article.abstract,  # Use full text
            "mesh_terms": article.mesh_terms,
            "publication_types": article.publication_types
        }
    }
    
    try:
        # Use ensemble endpoint for better performance (2.2x faster, 75% cost savings)
        response = requests.post(
            f"{PV_CLASSIFICATION_SERVICE}/api/v1/classify/ensemble",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            classification_data = result.get("classification", {})
            ensemble_metadata = result.get("ensemble_metadata", {})
            
            models_used = ensemble_metadata.get("models_used", [])
            processing_time = ensemble_metadata.get("processing_time_ms", 0)
            cost = ensemble_metadata.get("cost_estimate", 0.0)
            
            logger.info(
                f"✅ Classified {article.pmid}: "
                f"{classification_data.get('classification')} "
                f"({classification_data.get('confidence', 0):.2f}) | "
                f"Models: {', '.join(models_used)} | "
                f"Time: {processing_time}ms | "
                f"Cost: ${cost:.4f}"
            )
            
            # Return both classification and ensemble metadata
            return {
                **classification_data,
                "ensemble_models_used": models_used,
                "processing_time_ms": processing_time,
                "classification_cost": cost
            }
        else:
            logger.error(f"❌ Classification failed for {article.pmid}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Classification error for {article.pmid}: {str(e)}")
        return None


def update_classification_in_es(article, classification_data):
    """Update Elasticsearch with classification results"""
    
    if not classification_data:
        return False
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_HOST}/documents/_update/pubmed_{article.pmid}",
            json={
                "doc": {
                    "classification": classification_data.get("classification"),
                    "classification_confidence": classification_data.get("confidence"),
                    "classification_reasoning": classification_data.get("reasoning"),
                    "classification_entities": classification_data.get("key_entities", []),
                    "regulatory_elements": classification_data.get("regulatory_elements", {}),
                    "ensemble_models_used": classification_data.get("ensemble_models_used", []),
                    "processing_time_ms": classification_data.get("processing_time_ms", 0),
                    "classification_cost": classification_data.get("classification_cost", 0.0),
                    "classified_at": datetime.utcnow().isoformat()
                }
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"✅ Updated classification for {article.pmid}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update classification for {article.pmid}: {str(e)}")
        return False


def extract_icsr_data(article, classification):
    """Extract ICSR data if classified as ICSR"""
    
    if classification.get("classification") != "ICSR":
        logger.info(f"ℹ️  Skipping ICSR extraction for {article.pmid} (not an ICSR)")
        return None
    
    payload = {
        "document_id": f"pubmed_{article.pmid}",
        "title": article.title,
        "abstract": article.abstract,
        "full_text": article.full_text,
        "pmid": article.pmid,
        "doi": article.doi
    }
    
    try:
        response = requests.post(
            f"{PV_CLASSIFICATION_SERVICE}/api/v1/extract/icsr",
            json=payload,
            timeout=180  # 3 minutes for GPT-4 extraction
        )
        
        if response.status_code == 200:
            result = response.json()
            icsr_data = result.get("icsr_data", {})
            
            logger.info(
                f"✅ Extracted ICSR data for {article.pmid}: "
                f"{len(icsr_data.get('events', []))} events, "
                f"{len(icsr_data.get('suspect_products', []))} products"
            )
            
            return result
        else:
            logger.error(f"❌ ICSR extraction failed for {article.pmid}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ ICSR extraction error for {article.pmid}: {str(e)}")
        return None


def update_icsr_in_es(article, icsr_result):
    """Update Elasticsearch with ICSR data"""
    
    if not icsr_result:
        return False
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_HOST}/documents/_update/pubmed_{article.pmid}",
            json={
                "doc": {
                    "icsr_data": icsr_result.get("icsr_data"),
                    "icsr_narrative": icsr_result.get("narrative"),
                    "icsr_xml": icsr_result.get("xml"),
                    "icsr_extraction_date": icsr_result.get("extraction_date"),
                    "ai_processed": True
                }
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"✅ Stored ICSR data for {article.pmid}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to store ICSR data for {article.pmid}: {str(e)}")
        return False


def run_full_pipeline(query_name="drug_induced_liver_injury", max_articles=10, require_full_text=True):
    """
    Run the complete PV pipeline
    """
    
    print("=" * 80)
    print("🚀 FULL-TEXT PV PIPELINE")
    print("=" * 80)
    print(f"Query: {query_name}")
    print(f"Max articles: {max_articles}")
    print(f"Require full text: {require_full_text}")
    print("=" * 80)
    
    # Initialize services
    ingestor = FullTextPubMedIngestor()
    
    # Step 1: Ingest full-text articles from PubMed/PMC
    print("\n📥 STEP 1: Ingesting full-text articles from PubMed/PMC...")
    
    query = PV_QUERIES.get(query_name)
    if not query:
        print(f"❌ Unknown query: {query_name}")
        return
    
    articles = ingestor.ingest_articles(
        query=query,
        max_results=max_articles,
        require_full_text=require_full_text
    )
    
    if not articles:
        print("❌ No articles found")
        return
    
    print(f"\n✅ Ingested {len(articles)} articles")
    print(f"   With full text: {sum(1 for a in articles if a.has_full_text)}")
    
    # Statistics
    stats = {
        "total": len(articles),
        "stored_in_es": 0,
        "classified": 0,
        "icsr_count": 0,
        "non_icsr_count": 0,
        "icsr_extracted": 0,
        "failed": 0
    }
    
    # Process each article
    for idx, article in enumerate(articles, 1):
        print(f"\n{'='*80}")
        print(f"📄 Processing {idx}/{len(articles)}: {article.title[:80]}...")
        print(f"{'='*80}")
        print(f"PMID: {article.pmid} | PMCID: {article.pmcid or 'N/A'}")
        print(f"Full text: {'Yes' if article.has_full_text else 'No'} ({len(article.full_text or '')} chars)")
        
        # Step 2: Store in Elasticsearch
        print(f"\n📊 STEP 2: Storing in Elasticsearch...")
        if send_to_elasticsearch(article):
            stats["stored_in_es"] += 1
        else:
            stats["failed"] += 1
            continue
        
        # Step 3: Classify
        print(f"\n🤖 STEP 3: Classifying with AI...")
        classification = classify_document(article)
        if classification:
            stats["classified"] += 1
            
            # Update Elasticsearch with classification
            update_classification_in_es(article, classification)
            
            if classification.get("classification") == "ICSR":
                stats["icsr_count"] += 1
                
                # Step 4: Extract ICSR data
                print(f"\n🔬 STEP 4: Extracting ICSR data...")
                icsr_result = extract_icsr_data(article, classification)
                
                if icsr_result:
                    stats["icsr_extracted"] += 1
                    
                    # Update Elasticsearch with ICSR data
                    update_icsr_in_es(article, icsr_result)
                    
                    print(f"✅ Complete ICSR processing for {article.pmid}")
                else:
                    print(f"⚠️  ICSR extraction failed for {article.pmid}")
            else:
                stats["non_icsr_count"] += 1
                print(f"ℹ️  {article.pmid} classified as {classification.get('classification')}")
        else:
            stats["failed"] += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 PIPELINE SUMMARY")
    print(f"{'='*80}")
    print(f"Total articles processed: {stats['total']}")
    print(f"Stored in Elasticsearch: {stats['stored_in_es']}")
    print(f"Classified: {stats['classified']}")
    print(f"  ├─ ICSR: {stats['icsr_count']}")
    print(f"  └─ Non-ICSR: {stats['non_icsr_count']}")
    print(f"ICSR data extracted: {stats['icsr_extracted']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*80}")
    
    print(f"\n✅ Pipeline complete!")
    print(f"🌐 View documents at: http://localhost:3000/documents")


if __name__ == "__main__":
    # Run with 50 documents
    run_full_pipeline(
        query_name="drug_induced_liver_injury",
        max_articles=50,
        require_full_text=True
    )

