#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

print("🔧 FINAL FIX: Linking entities to documents by title matching")
print()

with driver.session() as session:
    # Get all entities
    result = session.run("""
        MATCH (e)
        WHERE e.id CONTAINS '_upload_'
        AND NOT (e:Document)
        AND e.name IS NOT NULL
        AND e.name <> ''
        RETURN e.id as id, e.name as name
    """)
    entities = list(result)
    print(f"Found {len(entities)} entities with names")
    
    # For each entity, find documents by searching title/content
    created = 0
    for entity in entities:
        entity_id = entity["id"]
        entity_name = entity["name"]
        
        # Find documents that mention this entity in their title
        find_docs = session.run("""
            MATCH (d:Document)
            WHERE d.title =~ $pattern
            RETURN d.id as doc_id
            LIMIT 5
        """, {"pattern": f"(?i).*{entity_name}.*"})
        
        docs = list(find_docs)
        
        if docs:
            for doc in docs:
                # Create relationship
                session.run("""
                    MATCH (d:Document {id: $doc_id})
                    MATCH (e {id: $entity_id})
                    MERGE (d)-[r:CONTAINS]->(e)
                    SET r.confidence = 0.9,
                        r.source = 'title_match'
                """, {"doc_id": doc["doc_id"], "entity_id": entity_id})
                created += 1
    
    print(f"✅ Created {created} relationships")
    
    # Verify the specific entity
    result = session.run("""
        MATCH (d:Document)-[r:CONTAINS]->(e {id: "Medical Condition_pheochromocytoma multisystem crisis_upload_1"})
        RETURN d.title
    """)
    doc = result.single()
    if doc:
        print(f"\n✅ pheochromocytoma multisystem crisis → {doc['d.title']}")
    else:
        print(f"\n⚠️  pheochromocytoma still not linked")

driver.close()
print("\n✅ Done!")
