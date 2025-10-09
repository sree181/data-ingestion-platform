"""
Sync existing documents from Elasticsearch to Neo4j
"""
import requests
import json

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
    result = resp.json()
    if result.get('errors'):
        print(f"❌ Neo4j error: {result['errors']}")
    return result

# Get all documents with entities
resp = requests.post(f"{ES_URL}/documents/_search", json={
    "query": {"exists": {"field": "openai_entities"}},
    "size": 100,
    "_source": ["openai_entities", "openai_relationships", "title"]
})

docs = resp.json()['hits']['hits']
print(f"📊 Found {len(docs)} documents with entities")

total_entities = 0
total_relationships = 0

for doc in docs:
    source = doc['_source']
    doc_id = doc['_id']
    
    entities = source.get('openai_entities', [])
    relationships = source.get('openai_relationships', [])
    
    print(f"\n📄 Processing: {source.get('title', doc_id)}")
    print(f"   Entities: {len(entities)}, Relationships: {len(relationships)}")
    
    # Create entities
    for entity in entities:
        name = entity.get('name') or entity.get('text')
        entity_type = entity.get('type') or entity.get('label')
        confidence = entity.get('confidence') or entity.get('confidence_score', 0.5)
        
        if not name or not entity_type:
            continue
        
        cypher = """
        MERGE (e:Entity {name: $name})
        SET e.type = $type,
            e.confidence = $confidence,
            e.normalized_name = toLower($name)
        RETURN e.name
        """
        
        run_neo4j_query(cypher, {
            "name": name,
            "type": entity_type,
            "confidence": confidence
        })
        
        total_entities += 1
    
    # Create relationships
    for rel in relationships:
        source_name = rel.get('source_text') or rel.get('source')
        target_name = rel.get('target_text') or rel.get('target')
        rel_type = rel.get('relationship_type') or rel.get('type', 'RELATED_TO')
        confidence = rel.get('confidence_score') or rel.get('confidence', 0.5)
        
        if not source_name or not target_name:
            continue
        
        cypher = """
        MATCH (source:Entity {name: $source_name})
        MATCH (target:Entity {name: $target_name})
        MERGE (source)-[r:RELATED_TO]->(target)
        SET r.type = $rel_type,
            r.confidence = $confidence
        RETURN type(r)
        """
        
        run_neo4j_query(cypher, {
            "source_name": source_name,
            "target_name": target_name,
            "rel_type": rel_type,
            "confidence": confidence
        })
        
        total_relationships += 1

print(f"\n\n🎉 Sync complete!")
print(f"✅ Total entities created: {total_entities}")
print(f"✅ Total relationships created: {total_relationships}")

# Get final stats
result = run_neo4j_query("MATCH (n:Entity) RETURN count(n) as total")
node_count = result['results'][0]['data'][0]['row'][0] if result['results'][0]['data'] else 0

result = run_neo4j_query("MATCH ()-[r]->() RETURN count(r) as total")
rel_count = result['results'][0]['data'][0]['row'][0] if result['results'][0]['data'] else 0

print(f"\n📊 Neo4j Statistics:")
print(f"📈 Total nodes: {node_count}")
print(f"🔗 Total relationships: {rel_count}")

# Show sample entities
print(f"\n📋 Sample entities:")
result = run_neo4j_query("MATCH (n:Entity) RETURN n.name, n.type LIMIT 10")
for row in result['results'][0]['data']:
    print(f"   • {row['row'][0]} ({row['row'][1]})")


