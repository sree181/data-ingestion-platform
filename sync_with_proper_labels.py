"""
Sync documents to Neo4j with PROPER LABELS and RELATIONSHIPS
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

# Step 1: Clear existing data
print("🗑️  Clearing existing Neo4j data...")
run_neo4j_query("MATCH (n) DETACH DELETE n")
print("✅ Cleared!")

# Step 2: Get all documents
resp = requests.post(f"{ES_URL}/documents/_search", json={
    "query": {"exists": {"field": "openai_entities"}},
    "size": 100,
    "_source": ["openai_entities", "openai_relationships", "title"]
})

docs = resp.json()['hits']['hits']
print(f"\n📊 Found {len(docs)} documents with entities")

total_entities = 0
total_relationships = 0
skipped_entities = 0

# Step 3: Create entities with PROPER LABELS
print("\n🔨 Creating entities with proper labels...")
for doc in docs:
    source = doc['_source']
    entities = source.get('openai_entities', [])
    
    for entity in entities:
        name = entity.get('name') or entity.get('text')
        entity_type = entity.get('type') or entity.get('label')
        confidence = entity.get('confidence') or entity.get('confidence_score', 0.5)
        
        if not name or not entity_type:
            skipped_entities += 1
            continue
        
        # Map entity types to Neo4j labels
        label_map = {
            "Drug": "Drug",
            "Medication": "Drug",
            "Medical Condition": "Disease",
            "Disease": "Disease",
            "Symptom": "Disease",
            "Vaccine": "Drug",
            "Person": "Person",
            "Organization": "Organization",
            "Medical Procedure": "Procedure",
            "Procedure": "Procedure",
            "Protein": "Protein",
            "Gene": "Gene",
            "Virus": "Disease",
            "Clinical Trial": "ClinicalTrial"
        }
        
        neo4j_label = label_map.get(entity_type, "Entity")
        
        # Create with proper label using dynamic Cypher
        cypher = f"""
        MERGE (e:{neo4j_label} {{name: $name}})
        SET e.type = $type,
            e.confidence = $confidence,
            e.normalized_name = toLower($name)
        RETURN e.name
        """
        
        run_neo4j_query(cypher, {
            "name": name,
            "type": entity_type,
            "confidence": float(confidence)
        })
        
        total_entities += 1
        
        if total_entities % 50 == 0:
            print(f"   ✓ Created {total_entities} entities...")

print(f"✅ Created {total_entities} entities (skipped {skipped_entities})")

# Step 4: Create relationships
print("\n🔗 Creating relationships...")
for doc in docs:
    source = doc['_source']
    relationships = source.get('openai_relationships', [])
    
    for rel in relationships:
        source_name = rel.get('source_text') or rel.get('source')
        target_name = rel.get('target_text') or rel.get('target')
        rel_type = (rel.get('relationship_type') or rel.get('type', 'RELATED_TO')).upper().replace(' ', '_')
        confidence = rel.get('confidence_score') or rel.get('confidence', 0.5)
        
        if not source_name or not target_name:
            continue
        
        # Try to match entities regardless of label
        cypher = """
        MATCH (source {name: $source_name})
        MATCH (target {name: $target_name})
        MERGE (source)-[r:RELATED_TO]->(target)
        SET r.type = $rel_type,
            r.confidence = $confidence
        RETURN type(r)
        """
        
        result = run_neo4j_query(cypher, {
            "source_name": source_name,
            "target_name": target_name,
            "rel_type": rel_type,
            "confidence": float(confidence)
        })
        
        if result['results'][0]['data']:
            total_relationships += 1
            
        if total_relationships % 20 == 0 and total_relationships > 0:
            print(f"   ✓ Created {total_relationships} relationships...")

print(f"✅ Created {total_relationships} relationships")

# Step 5: Get final stats
print("\n📊 Final Neo4j Statistics:")

result = run_neo4j_query("MATCH (n) RETURN count(n) as total")
node_count = result['results'][0]['data'][0]['row'][0] if result['results'][0]['data'] else 0
print(f"📈 Total nodes: {node_count}")

result = run_neo4j_query("MATCH ()-[r]->() RETURN count(r) as total")
rel_count = result['results'][0]['data'][0]['row'][0] if result['results'][0]['data'] else 0
print(f"🔗 Total relationships: {rel_count}")

# Entity type breakdown
result = run_neo4j_query("MATCH (n) RETURN DISTINCT labels(n)[0] as label, count(*) as count ORDER BY count DESC")
print(f"\n📋 Entity Types:")
for row in result['results'][0]['data']:
    label = row['row'][0]
    count = row['row'][1]
    print(f"   • {label}: {count}")

# Sample entities
print(f"\n📋 Sample Entities:")
result = run_neo4j_query("MATCH (n) RETURN labels(n)[0] as type, n.name as name LIMIT 10")
for row in result['results'][0]['data']:
    entity_type = row['row'][0]
    name = row['row'][1]
    print(f"   • {name} [{entity_type}]")

print("\n🎉 Sync complete! Test Knowledge Hub now!")


