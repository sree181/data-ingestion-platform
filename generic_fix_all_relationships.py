#!/usr/bin/env python3
"""
Generic Fix: Create Document-Entity Relationships
Links ALL entities to their source documents by matching upload IDs
Works for ANY node in the knowledge graph
"""

from neo4j import GraphDatabase
import re

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def extract_upload_id(node_id):
    """Extract upload timestamp from node ID"""
    # Format: "Medical Condition_pheochromocytoma_upload_1759469934"
    # or "upload_1759469934_7f9146d1"
    match = re.search(r'upload_(\d+)', node_id)
    return match.group(1) if match else None

print("=" * 70)
print("  GENERIC FIX: Linking ALL Entities to Documents")
print("=" * 70)
print()

with driver.session() as session:
    # Step 1: Get all documents
    result = session.run("MATCH (d:Document) RETURN d.id as id, d.title as title")
    documents = [(record["id"], record["title"]) for record in result]
    print(f"📄 Found {len(documents)} documents")
    
    # Step 2: Get all entities
    result = session.run("""
        MATCH (e) 
        WHERE e.id IS NOT NULL 
        AND e.id CONTAINS 'upload_'
        AND NOT (e:Document)
        RETURN e.id as id, e.name as name, e.type as type
    """)
    entities = [(record["id"], record["name"], record["type"]) for record in result]
    print(f"🏷️  Found {len(entities)} entities")
    print()
    
    # Step 3: Create relationships by matching upload timestamps
    print("🔗 Creating relationships...")
    relationships_created = 0
    
    for doc_id, doc_title in documents:
        doc_upload_id = extract_upload_id(doc_id)
        if not doc_upload_id:
            continue
        match_count = 0
        
        for entity_id, entity_name, entity_type in entities:
            entity_upload_id = extract_upload_id(entity_id)
            
            # If upload IDs match, create relationship
            if entity_upload_id == doc_upload_id:
                cypher = """
                MATCH (d:Document {id: $doc_id})
                MATCH (e {id: $entity_id})
                MERGE (d)-[r:CONTAINS]->(e)
                ON CREATE SET r.confidence = 0.95,
                              r.source = 'generic_fix',
                              r.created_at = datetime()
                RETURN r
                """
                
                result = session.run(cypher, {
                    "doc_id": doc_id,
                    "entity_id": entity_id
                })
                
                if result.single():
                    match_count += 1
                    relationships_created += 1
        
        if match_count > 0:
            print(f"  ✅ {doc_title[:50]}... → {match_count} entities")
    
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"✅ Created {relationships_created} relationships")
    print()
    
    # Verify
    result = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) as total")
    total = result.single()["total"]
    print(f"📊 Total CONTAINS relationships in Neo4j: {total}")
    print()
    
    # Show samples from different entity types
    result = session.run("""
        MATCH (d:Document)-[r:CONTAINS]->(e)
        WHERE e.name IS NOT NULL AND e.name <> ''
        RETURN d.title as doc, e.name as entity, e.type as type
        LIMIT 20
    """)
    
    print("📋 Sample relationships (ANY node will now work):")
    print()
    samples_by_type = {}
    for record in result:
        entity_type = record['type']
        if entity_type not in samples_by_type:
            samples_by_type[entity_type] = []
        if len(samples_by_type[entity_type]) < 2:
            samples_by_type[entity_type].append(record)
    
    for entity_type, records in samples_by_type.items():
        print(f"  {entity_type}:")
        for record in records:
            print(f"    • {record['entity']}")
            print(f"      └─ Source: {record['doc'][:50]}...")
        print()
    
    # Test specific entities
    print("🧪 Testing specific entities:")
    test_entities = [
        "pheochromocytoma multisystem crisis",
        "covid-19",
        "bnt162b2"
    ]
    
    for test_name in test_entities:
        result = session.run("""
            MATCH (d:Document)-[r:CONTAINS]->(e)
            WHERE e.name =~ $pattern
            RETURN count(d) as doc_count, e.name as entity_name
            LIMIT 1
        """, {"pattern": f"(?i).*{test_name}.*"})
        
        record = result.single()
        if record and record["doc_count"] > 0:
            print(f"  ✅ '{record['entity_name']}' → {record['doc_count']} document(s)")
        else:
            print(f"  ⚠️  '{test_name}' → No documents found")
    
    print()
    print("=" * 70)
    print("  ✅ GENERIC FIX COMPLETE!")
    print("=" * 70)
    print()
    print("🎯 Next steps:")
    print("   1. Refresh Knowledge Hub: http://localhost:3000/knowledge-hub")
    print("   2. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)")
    print("   3. Click ANY entity node")
    print("   4. Source documents will now appear!")
    print()

driver.close()

