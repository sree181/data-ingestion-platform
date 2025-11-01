#!/usr/bin/env python3
"""
Test the two-tier source document fetching for an entity
"""
import asyncio
import sys
import os

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api-gateway'))

from services.knowledge_hub_service import KnowledgeHubService
from services.elasticsearch_service import ElasticsearchService
from services.neo4j_service import Neo4jService

async def test_entity_source_documents(entity_name_or_id: str):
    """Test fetching source documents for an entity"""
    
    # Initialize services
    es_service = ElasticsearchService()
    neo4j_service = Neo4jService()
    kb_service = KnowledgeHubService(es_service, neo4j_service)
    
    try:
        # Connect to services
        await es_service.connect()
        await neo4j_service.connect()
        
        print("\n" + "="*80)
        print(f"TESTING SOURCE DOCUMENTS FOR: {entity_name_or_id}")
        print("="*80)
        
        # First, try to find the entity in Neo4j
        print("\n1. Finding entity in Neo4j...")
        cypher = """
        MATCH (e)
        WHERE e.id = $entity_id 
           OR toLower(coalesce(e.name, '')) CONTAINS toLower($search_term)
           OR toLower(coalesce(e.normalized_name, '')) CONTAINS toLower($search_term)
        RETURN e.id as id, 
               coalesce(e.normalized_name, e.name) as name, 
               e.type as type,
               labels(e) as labels
        LIMIT 5
        """
        
        result = await kb_service._execute_cypher(cypher, {
            "entity_id": entity_name_or_id,
            "search_term": entity_name_or_id
        })
        
        if not result or not result.get('results') or not result['results'][0].get('data'):
            print(f"❌ Entity not found in Neo4j: {entity_name_or_id}")
            return
        
        # Show all matching entities
        print(f"✅ Found {len(result['results'][0]['data'])} matching entities:")
        entities = []
        for i, row_data in enumerate(result['results'][0]['data'], 1):
            row = row_data['row']
            entity_id = row[0]
            entity_name = row[1]
            entity_type = row[2]
            labels = row[3]
            entities.append((entity_id, entity_name, entity_type))
            print(f"   {i}. ID: {entity_id}")
            print(f"      Name: {entity_name}")
            print(f"      Type: {entity_type}")
            print(f"      Labels: {labels}")
        
        # Test with the first entity
        test_entity_id, test_entity_name, test_entity_type = entities[0]
        
        print(f"\n2. Testing source document fetch for: {test_entity_name} ({test_entity_id})")
        print("-"*80)
        
        # Call the two-tier method
        results = await kb_service.get_entity_source_documents_by_id(
            entity_id=test_entity_id,
            space_id=None,
            limit=10
        )
        
        # Display results
        print(f"\n3. RESULTS")
        print("="*80)
        print(f"Success: {results.get('success')}")
        print(f"Method used: {results.get('method', 'elasticsearch')}")
        print(f"Document count: {results.get('document_count', 0)}")
        
        if results.get('document_count', 0) > 0:
            print(f"\n✅ Found {results['document_count']} source documents:")
            for i, doc in enumerate(results['documents'], 1):
                print(f"\n   Document {i}:")
                print(f"   - Title: {doc.get('title')}")
                print(f"   - Doc ID: {doc.get('doc_id')}")
                print(f"   - Source Type: {doc.get('source_type')}")
                print(f"   - Confidence: {doc.get('entity_confidence')}")
                if doc.get('snippets'):
                    print(f"   - Snippets: {len(doc['snippets'])}")
                    for j, snippet in enumerate(doc['snippets'][:2], 1):
                        print(f"     {j}. {snippet[:100]}...")
        else:
            print(f"\n❌ No source documents found")
            if results.get('error'):
                print(f"Error: {results['error']}")
        
    finally:
        # Cleanup
        await es_service.close()
        await neo4j_service.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        entity = sys.argv[1]
    else:
        entity = "hypoxemia"  # Default test case
    
    print(f"\n🔍 Testing entity: {entity}")
    asyncio.run(test_entity_source_documents(entity))

