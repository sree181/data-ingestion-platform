#!/usr/bin/env python3
"""
Classify existing cardiotoxicity documents with ICSR classification
"""
import asyncio
import httpx
from elasticsearch import Elasticsearch

async def classify_cardiotoxicity_docs():
    """Classify cardiotoxicity documents"""
    
    print("🎯 Classifying cardiotoxicity documents...")
    print()
    
    # Connect to Elasticsearch
    es = Elasticsearch(['http://localhost:9200'])
    
    # Find cardiotoxicity documents without classification
    result = es.search(
        index='documents',
        body={
            'query': {
                'bool': {
                    'must': [
                        {'term': {'space_id.keyword': 'b2efb6e1-a2fa-4ce2-976c-15bc736579a4'}},
                        {'match': {'title': 'cardiotoxicity'}}
                    ],
                    'must_not': [
                        {'exists': {'field': 'icsr_classification'}}
                    ]
                }
            },
            'size': 20
        }
    )
    
    docs = result['hits']['hits']
    print(f"Found {len(docs)} documents to classify")
    print()
    
    # Classify each document
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, doc in enumerate(docs, 1):
            doc_id = doc['_id']
            doc_source = doc['_source']
            title = doc_source.get('title', 'Untitled')
            content = doc_source.get('content', '') or doc_source.get('abstract', '')
            
            print(f"[{i}/{len(docs)}] {title[:60]}...")
            
            if not content:
                print(f"   ⚠️  No content, skipping")
                continue
            
            try:
                # Call PV classification service
                response = await client.post(
                    'http://localhost:8001/api/v1/classify/ensemble',
                    json={
                        'document': {
                            'id': doc_id,
                            'title': title,
                            'abstract': content[:500]
                        }
                    }
                )
                
                if response.status_code == 200:
                    classification = response.json()
                    
                    # Update document in Elasticsearch
                    es.update(
                        index='documents',
                        id=doc_id,
                        body={
                            'doc': {
                                'icsr_classification': classification
                            }
                        }
                    )
                    
                    print(f"   ✅ {classification['classification']} ({classification['confidence']*100:.0f}%)")
                else:
                    print(f"   ❌ Classification failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            print()
    
    print("✅ Classification complete!")
    print()
    print("🔄 Refresh the Document Library to see ICSR badges!")

if __name__ == "__main__":
    asyncio.run(classify_cardiotoxicity_docs())

