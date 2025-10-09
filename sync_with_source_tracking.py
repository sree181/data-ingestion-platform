"""
Sync with SOURCE TRACKING - tracks which documents mention each entity
Enables filtering by source type and color-coding in Knowledge Hub
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
print("🔍 SYNCING WITH SOURCE TRACKING")
print("=" * 70)

print("\n🗑️  Clearing Neo4j...")
run_neo4j_query("MATCH (n) DETACH DELETE n")
print("✅ Cleared!")

print("\n📊 Fetching documents from Elasticsearch...")
resp = requests.post(f"{ES_URL}/documents/_search", json={
    "query": {"exists": {"field": "openai_entities"}},
    "size": 100,
    "_source": ["openai_entities", "openai_relationships", "title", "source", "external_source", "document_type"]
})

docs = resp.json()['hits']['hits']
print(f"✅ Found {len(docs)} documents with entities\n")

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

print("=" * 70)
print("🔨 CREATING ENTITIES WITH SOURCE TRACKING")
print("=" * 70)

total_entities = 0
entity_sources = {}  # Track sources for each entity

for doc in docs:
    doc_id = doc['_id']
    source_data = doc['_source']
    entities = source_data.get('openai_entities', [])
    
    # Get document metadata for source tracking
    doc_source = source_data.get('source') or 'pdf'
    is_external = source_data.get('external_source', False)
    doc_type = source_data.get('document_type') or 'pdf'
    doc_title = (source_data.get('title') or 'Unknown')[:80]
    
    # Determine source type
    if is_external:
        source_type = doc_source  # 'clinicaltrials', 'pubmed', etc.
    else:
        source_type = 'pdf'
    
    for entity in entities:
        name = entity.get('name') or entity.get('text')
        entity_type = entity.get('type') or entity.get('label')
        confidence = entity.get('confidence') or entity.get('confidence_score', 0.5)
        description = entity.get('description', '')
        
        if not name or not entity_type:
            continue
        
        neo4j_label = label_map.get(entity_type, "Entity")
        normalized_name = name.lower()
        
        # Track sources for this entity
        if normalized_name not in entity_sources:
            entity_sources[normalized_name] = {
                'name': name,
                'type': entity_type,
                'label': neo4j_label,
                'sources': [],
                'source_types': set(),
                'max_confidence': confidence
            }
        
        # Add this source if not already added
        source_info = {
            'doc_id': doc_id,
            'doc_type': doc_type,
            'source_type': source_type,
            'title': doc_title,
            'is_external': is_external
        }
        
        # Check if this doc is already tracked
        already_tracked = any(s['doc_id'] == doc_id for s in entity_sources[normalized_name]['sources'])
        
        if not already_tracked:
            entity_sources[normalized_name]['sources'].append(source_info)
            entity_sources[normalized_name]['source_types'].add(source_type)
            entity_sources[normalized_name]['max_confidence'] = max(
                entity_sources[normalized_name]['max_confidence'],
                float(confidence)
            )

print(f"📊 Collected {len(entity_sources)} unique entities from {len(docs)} documents\n")

# Now create entities in Neo4j with source tracking
for normalized_name, entity_data in entity_sources.items():
    name = entity_data['name']
    entity_type = entity_data['type']
    neo4j_label = entity_data['label']
    confidence = entity_data['max_confidence']
    sources = entity_data['sources']
    source_types = list(entity_data['source_types'])
    source_count = len(sources)
    
    # Create entity with source tracking
    # Convert sources to JSON string since Neo4j doesn't support nested objects
    cypher = f"""
    MERGE (e:{neo4j_label} {{normalized_name: $normalized_name}})
    SET e.name = $name,
        e.type = $type,
        e.confidence = $confidence,
        e.sources_json = $sources_json,
        e.source_types = $source_types,
        e.source_count = $source_count,
        e.has_pdf = $has_pdf,
        e.has_external = $has_external
    RETURN e.name
    """
    
    has_pdf = 'pdf' in source_types
    has_external = any(st != 'pdf' for st in source_types)
    
    # Convert sources to JSON string
    sources_json = json.dumps(sources)
    
    run_neo4j_query(cypher, {
        "normalized_name": normalized_name,
        "name": name,
        "type": entity_type,
        "confidence": confidence,
        "sources_json": sources_json,
        "source_types": source_types,
        "source_count": source_count,
        "has_pdf": has_pdf,
        "has_external": has_external
    })
    
    total_entities += 1
    
    if total_entities % 50 == 0:
        print(f"   ✓ Created {total_entities} entities...")

print(f"\n✅ Created {total_entities} entities with source tracking\n")

print("=" * 70)
print("🔗 CREATING RELATIONSHIPS")
print("=" * 70)

def find_entity_node(entity_name):
    """Find entity by normalized name"""
    if not entity_name:
        return None
    normalized = entity_name.lower().strip()
    if normalized in entity_sources:
        return entity_sources[normalized]['name']
    return None

created_relationships = 0
failed_relationships = 0

for doc in docs:
    source_data = doc['_source']
    relationships = source_data.get('openai_relationships', [])
    
    for rel in relationships:
        # Handle different relationship formats
        subject = rel.get('subject') or rel.get('source_text') or rel.get('source')
        predicate = rel.get('predicate') or rel.get('type') or rel.get('relationship_type', 'RELATED_TO')
        obj = rel.get('object') or rel.get('target_text') or rel.get('target')
        confidence = rel.get('confidence', 0.5)
        
        if not subject or not obj:
            continue
        
        # Find matching entities
        source_entity = find_entity_node(subject)
        target_entity = find_entity_node(obj)
        
        if not source_entity or not target_entity:
            failed_relationships += 1
            continue
        
        # Create relationship
        cypher = """
        MATCH (a {name: $source})
        MATCH (b {name: $target})
        MERGE (a)-[r:RELATED_TO]->(b)
        SET r.predicate = $predicate,
            r.confidence = $confidence,
            r.type = $predicate
        """
        
        result = run_neo4j_query(cypher, {
            "source": source_entity,
            "target": target_entity,
            "predicate": predicate,
            "confidence": float(confidence)
        })
        
        if not result.get('errors'):
            created_relationships += 1

print(f"\n✅ Created {created_relationships} relationships")
print(f"❌ Failed to create {failed_relationships} relationships\n")

print("=" * 70)
print("📊 FINAL STATISTICS")
print("=" * 70)

# Get stats
stats_query = """
MATCH (n)
RETURN 
    count(n) as total_nodes,
    count(DISTINCT n.source_count) as entities_with_sources
"""
stats = run_neo4j_query(stats_query)

rel_query = "MATCH ()-[r]->() RETURN count(r) as total_rels"
rel_stats = run_neo4j_query(rel_query)

type_query = """
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC
"""
type_stats = run_neo4j_query(type_query)

source_query = """
MATCH (n)
WHERE n.source_types IS NOT NULL
UNWIND n.source_types as source_type
RETURN source_type, count(DISTINCT n) as count
ORDER BY count DESC
"""
source_stats = run_neo4j_query(source_query)

cross_source_query = """
MATCH (n)
WHERE size(n.source_types) > 1
RETURN count(n) as cross_source_entities
"""
cross_source_stats = run_neo4j_query(cross_source_query)

print(f"\n📈 Total nodes: {stats['results'][0]['data'][0]['row'][0]}")
print(f"🔗 Total relationships: {rel_stats['results'][0]['data'][0]['row'][0]}")

print(f"\n📋 Entity Types:")
for row in type_stats['results'][0]['data']:
    entity_type, count = row['row']
    print(f"   • {entity_type}: {count}")

print(f"\n📚 Source Types:")
for row in source_stats['results'][0]['data']:
    source_type, count = row['row']
    print(f"   • {source_type}: {count} entities")

if cross_source_stats['results'][0]['data']:
    cross_count = cross_source_stats['results'][0]['data'][0]['row'][0]
    print(f"\n🔗 Cross-source entities (mentioned in multiple source types): {cross_count}")

print("\n" + "=" * 70)
print("🎉 SYNC COMPLETE WITH SOURCE TRACKING!")
print("=" * 70)
print("\nEntities now have:")
print("  • sources: [{doc_id, doc_type, source_type, title}]")
print("  • source_types: ['pdf', 'clinicaltrials', etc.]")
print("  • source_count: number of documents mentioning this entity")
print("  • has_pdf: boolean")
print("  • has_external: boolean")
print("\nYou can now filter by source type in Knowledge Hub!")
print("=" * 70)
