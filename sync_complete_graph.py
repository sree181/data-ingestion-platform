"""
Complete sync with PROPER relationship handling
Uses subject/object keys and case-insensitive matching
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

print("=" * 70)
print("🔍 ANALYZING RELATIONSHIP STRUCTURE")
print("=" * 70)

# Get sample relationships to understand structure
resp = requests.post(f"{ES_URL}/documents/_search", json={
    "query": {"exists": {"field": "openai_relationships"}},
    "size": 1,
    "_source": ["openai_relationships"]
})

sample_rels = resp.json()['hits']['hits'][0]['_source'].get('openai_relationships', [])
if sample_rels:
    print(f"\n✅ Relationship structure detected:")
    print(f"   Keys: {list(sample_rels[0].keys())}")
    print(f"   Sample: {json.dumps(sample_rels[0], indent=2)}")

print("\n" + "=" * 70)
print("🗑️  CLEARING NEO4J")
print("=" * 70)
run_neo4j_query("MATCH (n) DETACH DELETE n")
print("✅ Cleared!")

print("\n" + "=" * 70)
print("🔨 STEP 1: CREATING ENTITIES WITH PROPER LABELS")
print("=" * 70)

# Get all documents
resp = requests.post(f"{ES_URL}/documents/_search", json={
    "query": {"exists": {"field": "openai_entities"}},
    "size": 100,
    "_source": ["openai_entities", "openai_relationships", "title"]
})

docs = resp.json()['hits']['hits']
print(f"📊 Found {len(docs)} documents with entities")

total_entities = 0
entity_names = set()

# Label mapping
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

for doc in docs:
    source = doc['_source']
    entities = source.get('openai_entities', [])
    
    for entity in entities:
        name = entity.get('name') or entity.get('text')
        entity_type = entity.get('type') or entity.get('label')
        confidence = entity.get('confidence') or entity.get('confidence_score', 0.5)
        
        if not name or not entity_type:
            continue
        
        neo4j_label = label_map.get(entity_type, "Entity")
        
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
        
        entity_names.add(name.lower())
        total_entities += 1
        
        if total_entities % 50 == 0:
            print(f"   ✓ Created {total_entities} entities...")

print(f"✅ Created {total_entities} entities")

print("\n" + "=" * 70)
print("🔗 STEP 2: CREATING RELATIONSHIPS")
print("=" * 70)

total_relationships = 0
failed_matches = []
successful_matches = []

for doc in docs:
    source = doc['_source']
    relationships = source.get('openai_relationships', [])
    doc_title = source.get('title', 'Unknown')[:50]
    
    print(f"\n📄 Processing: {doc_title}...")
    print(f"   Found {len(relationships)} relationships")
    
    for rel in relationships:
        # CORRECT KEYS: subject and object
        source_name = rel.get('subject')
        target_name = rel.get('object')
        predicate = rel.get('predicate', 'RELATED_TO')
        confidence = rel.get('confidence', 0.5)
        
        if not source_name or not target_name:
            print(f"   ⚠️  Skipping relationship with missing source/target")
            continue
        
        # Normalize relationship type
        rel_type = predicate.upper().replace(' ', '_').replace('-', '_')
        
        # Try case-insensitive match
        cypher = """
        MATCH (source) WHERE toLower(source.name) = toLower($source_name)
        MATCH (target) WHERE toLower(target.name) = toLower($target_name)
        MERGE (source)-[r:RELATED_TO]->(target)
        SET r.type = $rel_type,
            r.predicate = $predicate,
            r.confidence = $confidence
        RETURN source.name as source, target.name as target, type(r) as rel_type
        """
        
        result = run_neo4j_query(cypher, {
            "source_name": source_name,
            "target_name": target_name,
            "rel_type": rel_type,
            "predicate": predicate,
            "confidence": float(confidence)
        })
        
        if result['results'][0]['data']:
            total_relationships += 1
            successful_matches.append({
                'source': source_name,
                'predicate': predicate,
                'target': target_name
            })
            print(f"   ✅ {source_name} → {predicate} → {target_name}")
        else:
            failed_matches.append({
                'source': source_name,
                'target': target_name,
                'reason': 'Entity name not found in Neo4j'
            })
            print(f"   ❌ Failed: {source_name} → {target_name}")

print(f"\n✅ Created {total_relationships} relationships")
print(f"❌ Failed to create {len(failed_matches)} relationships")

if failed_matches and len(failed_matches) <= 5:
    print(f"\n⚠️  Failed relationship examples:")
    for fail in failed_matches[:5]:
        print(f"   • {fail['source']} → {fail['target']}")
        print(f"     Reason: {fail['reason']}")

print("\n" + "=" * 70)
print("📊 FINAL NEO4J STATISTICS")
print("=" * 70)

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

# Sample relationships
if rel_count > 0:
    print(f"\n🔗 Sample Relationships:")
    result = run_neo4j_query("""
        MATCH (source)-[r]->(target) 
        RETURN source.name, r.predicate, target.name 
        LIMIT 10
    """)
    for row in result['results'][0]['data']:
        source = row['row'][0]
        pred = row['row'][1]
        target = row['row'][2]
        print(f"   • {source} → {pred} → {target}")

print("\n" + "=" * 70)
print("🎉 SYNC COMPLETE!")
print("=" * 70)
print(f"\nRefresh Knowledge Hub and search for any entity!")
print(f"Recommended searches:")
print(f"  • 'vaccine'")
print(f"  • 'COVID'")  
print(f"  • 'pancreatitis'")


