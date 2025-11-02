#!/usr/bin/env python3
"""
Fix Entity Names and Create Document Relationships
This script fixes entities that have IDs but no names, and creates CONTAINS relationships
"""

import os
from neo4j import GraphDatabase

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class EntityFixer:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.driver.close()
    
    def fix_entity_names(self):
        """Fix entities that have IDs but no names"""
        print("🔧 Fixing entity names...")
        
        with self.driver.session() as session:
            # Find entities with empty or missing names
            cypher = """
            MATCH (e)
            WHERE (e.name IS NULL OR e.name = '')
            AND e.id IS NOT NULL
            AND e.id CONTAINS '_upload_'
            RETURN e.id as id, e.type as type
            """
            
            result = session.run(cypher)
            entities = [{"id": record["id"], "type": record["type"]} for record in result]
            
            print(f"Found {len(entities)} entities with missing names")
            
            # Fix each entity
            fixed_count = 0
            for entity in entities:
                entity_id = entity["id"]
                entity_type = entity["type"]
                
                # Extract name from ID
                # Format: "Medical Condition_pheochromocytoma multisystem crisis_upload_1"
                # We want: "pheochromocytoma multisystem crisis"
                
                parts = entity_id.split("_upload_")
                if len(parts) == 2:
                    # Remove the type prefix
                    name_with_type = parts[0]
                    if "_" in name_with_type:
                        # Split by first underscore to remove type
                        type_and_name = name_with_type.split("_", 1)
                        if len(type_and_name) == 2:
                            name = type_and_name[1].replace("_", " ").strip()
                        else:
                            name = name_with_type.replace("_", " ").strip()
                    else:
                        name = name_with_type.replace("_", " ").strip()
                    
                    # Update the entity
                    update_cypher = """
                    MATCH (e {id: $entity_id})
                    SET e.name = $name,
                        e.normalized_name = $normalized_name
                    RETURN e.name
                    """
                    
                    normalized_name = name.lower().strip()
                    
                    session.run(update_cypher, {
                        "entity_id": entity_id,
                        "name": name,
                        "normalized_name": normalized_name
                    })
                    
                    fixed_count += 1
                    print(f"  ✅ Fixed: {name} (ID: {entity_id[:50]}...)")
            
            print(f"\n✅ Fixed {fixed_count} entity names")
            return fixed_count
    
    def create_relationships_from_elasticsearch(self):
        """Create CONTAINS relationships by matching entity names in document metadata"""
        print("\n🔗 Creating document-entity relationships...")
        
        # This is a simplified approach - we'll create relationships based on entity IDs
        # that contain document IDs (upload_X pattern)
        
        with self.driver.session() as session:
            cypher = """
            MATCH (d:Document), (e)
            WHERE e.id CONTAINS '_upload_'
            AND e.id CONTAINS split(d.id, '_')[1]
            AND NOT (d)-[:CONTAINS]->(e)
            MERGE (d)-[r:CONTAINS]->(e)
            SET r.confidence = 0.9,
                r.created_at = datetime()
            RETURN count(r) as relationships_created
            """
            
            result = session.run(cypher)
            record = result.single()
            count = record["relationships_created"] if record else 0
            
            print(f"✅ Created {count} CONTAINS relationships")
            return count
    
    def verify_fixes(self):
        """Verify the fixes worked"""
        print("\n📊 Verification:")
        
        with self.driver.session() as session:
            # Count entities with names
            result = session.run("MATCH (e) WHERE e.name IS NOT NULL AND e.name <> '' RETURN count(e) as count")
            entities_with_names = result.single()["count"]
            
            # Count total entities
            result = session.run("MATCH (e) WHERE e.id IS NOT NULL RETURN count(e) as count")
            total_entities = result.single()["count"]
            
            # Count CONTAINS relationships
            result = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) as count")
            contains_rels = result.single()["count"]
            
            # Count documents
            result = session.run("MATCH (d:Document) RETURN count(d) as count")
            total_docs = result.single()["count"]
            
            print(f"  Entities with names: {entities_with_names}/{total_entities}")
            print(f"  CONTAINS relationships: {contains_rels}")
            print(f"  Total documents: {total_docs}")
            
            # Show sample entity
            result = session.run("""
                MATCH (d:Document)-[r:CONTAINS]->(e)
                RETURN d.title as doc_title, e.name as entity_name, e.type as entity_type
                LIMIT 3
            """)
            
            print("\n  Sample relationships:")
            for record in result:
                print(f"    📄 {record['doc_title'][:60]}...")
                print(f"       → {record['entity_type']}: {record['entity_name']}")

def main():
    print("=" * 60)
    print("  Entity Name and Relationship Fixer")
    print("=" * 60)
    print()
    
    fixer = EntityFixer()
    try:
        # Fix entity names
        fixed_names = fixer.fix_entity_names()
        
        # Create relationships
        created_rels = fixer.create_relationships_from_elasticsearch()
        
        # Verify
        fixer.verify_fixes()
        
        print("\n" + "=" * 60)
        print("  Summary")
        print("=" * 60)
        print(f"✅ Fixed {fixed_names} entity names")
        print(f"✅ Created {created_rels} relationships")
        print("\n🎉 All fixes applied successfully!")
        print("\n🔍 Next steps:")
        print("   1. Refresh Knowledge Hub: http://localhost:3000/knowledge-hub")
        print("   2. Click on 'pheochromocytoma multisystem crisis' node")
        print("   3. Source documents should now appear!")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fixer.close()

if __name__ == "__main__":
    main()

