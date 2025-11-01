#!/usr/bin/env python3
"""
Debug script to check what entities are in Elasticsearch documents
"""
import asyncio
import os
from elasticsearch import AsyncElasticsearch

async def check_entities():
    """Check entities in Elasticsearch"""
    
    # Connect to Elasticsearch
    es = AsyncElasticsearch(
        hosts=[os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")],
        verify_certs=False
    )
    
    try:
        # Search for documents that mention "hypoxemia"
        query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"content": "hypoxemia"}},
                        {"match": {"title": "hypoxemia"}},
                        {"match": {"openai_entities.name": "hypoxemia"}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 5,
            "_source": ["doc_id", "title", "openai_entities", "source_type"]
        }
        
        result = await es.search(index="documents", body=query)
        
        print("\n" + "="*80)
        print("DOCUMENTS MENTIONING 'HYPOXEMIA'")
        print("="*80)
        
        hits = result.get("hits", {}).get("hits", [])
        if not hits:
            print("❌ No documents found mentioning 'hypoxemia'")
            print("\nLet's check what entities DO exist...")
            
            # Get a sample document
            sample_query = {
                "query": {"match_all": {}},
                "size": 1,
                "_source": ["doc_id", "title", "openai_entities"]
            }
            sample_result = await es.search(index="documents", body=sample_query)
            sample_hits = sample_result.get("hits", {}).get("hits", [])
            
            if sample_hits:
                doc = sample_hits[0]["_source"]
                print(f"\nSample Document: {doc.get('title', 'Untitled')}")
                print(f"Doc ID: {doc.get('doc_id')}")
                print(f"\nEntities in this document:")
                entities = doc.get("openai_entities", [])
                if entities:
                    for i, entity in enumerate(entities[:10], 1):
                        print(f"  {i}. {entity.get('name')} ({entity.get('type')})")
                else:
                    print("  ❌ No openai_entities field found!")
                    print("  💡 Documents need to be processed with entity extraction")
        else:
            print(f"✅ Found {len(hits)} documents")
            for i, hit in enumerate(hits, 1):
                source = hit["_source"]
                print(f"\n{i}. {source.get('title', 'Untitled')}")
                print(f"   Doc ID: {source.get('doc_id')}")
                print(f"   Source: {source.get('source_type', 'unknown')}")
                
                entities = source.get("openai_entities", [])
                if entities:
                    # Find hypoxemia
                    hypoxemia_entities = [e for e in entities if 'hypoxemia' in e.get('name', '').lower()]
                    if hypoxemia_entities:
                        print(f"   ✅ Entity extraction found 'hypoxemia':")
                        for entity in hypoxemia_entities:
                            print(f"      - Name: {entity.get('name')}")
                            print(f"      - Type: {entity.get('type')}")
                            print(f"      - Confidence: {entity.get('confidence')}")
                    else:
                        print(f"   ⚠️  'hypoxemia' in content but NOT in openai_entities")
                        print(f"   Total entities: {len(entities)}")
                        print(f"   Sample entities: {[e.get('name') for e in entities[:5]]}")
                else:
                    print(f"   ❌ No openai_entities field")
        
        # Check Neo4j entity structure
        print("\n" + "="*80)
        print("NEO4J ENTITY CHECK")
        print("="*80)
        print("\n💡 To check Neo4j, run:")
        print("docker exec neo4j cypher-shell -u neo4j -p pharmacovigilance2024")
        print('MATCH (e) WHERE toLower(e.name) CONTAINS "hypoxemia" OR toLower(e.normalized_name) CONTAINS "hypoxemia"')
        print('RETURN e.id, e.name, e.normalized_name, e.type, labels(e);')
        
    finally:
        await es.close()

if __name__ == "__main__":
    asyncio.run(check_entities())

