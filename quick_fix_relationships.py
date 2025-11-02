#!/usr/bin/env python3
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # Create relationships by matching upload IDs
    cypher = """
    MATCH (d:Document), (e)
    WHERE d.id CONTAINS 'upload_'
    AND e.id CONTAINS 'upload_'
    AND e.id CONTAINS split(d.id, '_')[1]
    AND e.id CONTAINS split(d.id, '_')[2]
    AND NOT (d)-[:CONTAINS]->(e)
    MERGE (d)-[r:CONTAINS]->(e)
    SET r.confidence = 0.9
    RETURN count(r) as created
    """
    result = session.run(cypher)
    count = result.single()["created"]
    print(f"✅ Created {count} relationships")
    
    # Verify
    result = session.run("MATCH (d:Document)-[r:CONTAINS]->(e) RETURN count(r) as total")
    total = result.single()["total"]
    print(f"📊 Total relationships: {total}")
    
    # Show sample
    result = session.run("""
        MATCH (d:Document)-[r:CONTAINS]->(e)
        WHERE e.name =~ '(?i).*pheochromocytoma.*'
        RETURN d.title, e.name
        LIMIT 3
    """)
    print("\n📋 Sample (pheochromocytoma):")
    for record in result:
        print(f"  {record['d.title'][:50]}... → {record['e.name']}")

driver.close()
