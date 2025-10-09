"""
FAST sync script - runs on host, uses HTTP APIs
Syncs AI-processed documents from Elasticsearch to Neo4j
"""

import requests
import json

# Config
ES_URL = "http://localhost:9200"
NEO4J_URL = "http://localhost:7474/db/neo4j/tx/commit"
NEO4J_AUTH = ("neo4j", "password123")

def run_neo4j_query(cypher, params=None):
    """Execute Cypher query via HTTP"""
    payload = {
        "statements": [{
            "statement": cypher,
            "parameters": params or {}
        }]
    }
    resp = requests.post(NEO4J_URL, json=payload, auth=NEO4J_AUTH)
    return resp.json()

def sync_documents():
    """Sync AI-processed documents to Neo4j"""
    
    print("🔍 Querying Elasticsearch for AI-processed documents...")
    
    # Get AI-processed documents via HTTP
    query = {
        "query": {"term": {"ai_processed": True}},
        "size": 236,
        "_source": ["openai_entities", "openai_relationships", "title", "source"]
    }
    
    resp = requests.post(f"{ES_URL}/documents/_search", json=query)
    results = resp.json()
    total = results['hits']['total']['value']
    
    print(f"📊 Found {total} AI-processed documents")
    
    entity_count = 0
    relationship_count = 0
    
    for i, hit in enumerate(results['hits']['hits']):
        doc_id = hit['_id']
        source = hit['_source']
        
        entities = source.get("openai_entities", [])
        relationships = source.get("openai_relationships", [])
        
        if not entities:
            continue
        
        # Create entities
        for entity in entities:
            if not entity.get('text') or not entity.get('label'):
                continue
                
            try:
                # Create or merge entity node
                cypher = """
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e.confidence = $confidence,
                    e.normalized_name = toLower($name)
                RETURN e.name
                """
                
                run_neo4j_query(cypher, {
                    "name": entity['text'],
                    "type": entity['label'],
                    "confidence": entity.get('confidence_score', 0.5)
                })
                
                entity_count += 1
                
            except Exception as e:
                print(f"❌ Error creating entity: {e}")
        
        # Create relationships
        for rel in relationships:
            if not rel.get('source_text') or not rel.get('target_text'):
                continue
                
            try:
                cypher = """
                MATCH (source {name: $source_name})
                MATCH (target {name: $target_name})
                MERGE (source)-[r:RELATED_TO]->(target)
                SET r.type = $rel_type,
                    r.confidence = $confidence
                RETURN type(r)
                """
                
                run_neo4j_query(cypher, {
                    "source_name": rel['source_text'],
                    "target_name": rel['target_text'],
                    "rel_type": rel.get('relationship_type', 'RELATED_TO'),
                    "confidence": rel.get('confidence_score', 0.5)
                })
                
                relationship_count += 1
                
            except Exception as e:
                print(f"❌ Error creating relationship: {e}")
        
        if (i + 1) % 10 == 0:
            print(f"✅ Processed {i + 1}/{total} documents ({entity_count} entities, {relationship_count} relationships)")
    
    print(f"\n🎉 Sync complete!")
    print(f"✅ Total entities created: {entity_count}")
    print(f"✅ Total relationships created: {relationship_count}")
    
    # Get final count
    result = run_neo4j_query("MATCH (n) RETURN count(n) as total")
    total_nodes = result['results'][0]['data'][0]['row'][0]
    
    result = run_neo4j_query("MATCH ()-[r]->() RETURN count(r) as total")
    total_rels = result['results'][0]['data'][0]['row'][0]
    
    print(f"\n📊 Neo4j Statistics:")
    print(f"📈 Total nodes: {total_nodes}")
    print(f"🔗 Total relationships: {total_rels}")

if __name__ == "__main__":
    sync_documents()

