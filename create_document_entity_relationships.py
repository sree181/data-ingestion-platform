#!/usr/bin/env python3
"""
Create Document-Entity Relationships from Elasticsearch Data
This script reads documents from Elasticsearch and creates CONTAINS relationships in Neo4j
"""

import os
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase

# Configuration
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class RelationshipCreator:
    def __init__(self):
        self.es = Elasticsearch([ES_URL], request_timeout=30, max_retries=3, retry_on_timeout=True)
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.es.close()
        self.neo4j_driver.close()
    
    def create_relationships(self):
        """Create CONTAINS relationships from Elasticsearch document metadata"""
        print("=" * 60)
        print("  Creating Document-Entity Relationships")
        print("=" * 60)
        print()
        
        # Get all documents from Elasticsearch
        print("📄 Fetching documents from Elasticsearch...")
        query = {"query": {"match_all": {}}, "size": 1000}
        response = self.es.search(index="documents", body=query)
        documents = [hit["_source"] for hit in response["hits"]["hits"]]
        print(f"✅ Found {len(documents)} documents")
        print()
        
        total_relationships = 0
        
        with self.neo4j_driver.session() as session:
            for i, doc in enumerate(documents, 1):
                # Use source_id which is the actual document ID in Neo4j
                doc_id = doc.get("source_id", doc.get("id", f"doc_{i}"))
                title = doc.get("title", doc.get("filename", "Untitled"))
                
                print(f"📄 [{i}/{len(documents)}] {title[:60]}... (ID: {doc_id})")
                
                # Check if document exists in Neo4j
                check_doc = session.run("MATCH (d:Document {id: $doc_id}) RETURN d", {"doc_id": doc_id})
                if not check_doc.single():
                    print(f"   ⚠️  Document not found in Neo4j with ID: {doc_id}")
                    continue
                
                # Get entities from various fields
                entities_to_link = []
                
                # From openai_entities
                if "openai_entities" in doc and doc["openai_entities"]:
                    for entity in doc["openai_entities"]:
                        if isinstance(entity, dict):
                            entity_name = entity.get("name", entity.get("text", ""))
                            entity_type = entity.get("type", "Entity")
                            if entity_name:
                                entities_to_link.append({
                                    "name": entity_name.lower().strip(),
                                    "type": entity_type,
                                    "confidence": entity.get("confidence", 0.9)
                                })
                
                # From extracted_entities
                if "extracted_entities" in doc and doc["extracted_entities"]:
                    for entity in doc["extracted_entities"]:
                        if isinstance(entity, dict):
                            entity_name = entity.get("name", entity.get("text", ""))
                            entity_type = entity.get("type", "Entity")
                            if entity_name:
                                entities_to_link.append({
                                    "name": entity_name.lower().strip(),
                                    "type": entity_type,
                                    "confidence": entity.get("confidence", 0.8)
                                })
                
                if not entities_to_link:
                    print(f"   ⚠️  No entities found")
                    continue
                
                print(f"   Found {len(entities_to_link)} entities to link")
                
                # Create relationships
                linked_count = 0
                for entity_data in entities_to_link:
                    entity_name = entity_data["name"]
                    confidence = entity_data["confidence"]
                    
                    # Find entity in Neo4j by normalized_name
                    cypher = """
                    MATCH (d:Document {id: $doc_id})
                    MATCH (e)
                    WHERE e.normalized_name = $entity_name
                    AND NOT (d)-[:CONTAINS]->(e)
                    MERGE (d)-[r:CONTAINS]->(e)
                    SET r.confidence = $confidence,
                        r.created_at = datetime()
                    RETURN e.name as entity_name
                    """
                    
                    result = session.run(cypher, {
                        "doc_id": doc_id,
                        "entity_name": entity_name,
                        "confidence": confidence
                    })
                    
                    if result.single():
                        linked_count += 1
                        total_relationships += 1
                
                if linked_count > 0:
                    print(f"   ✅ Created {linked_count} relationships")
                else:
                    print(f"   ⚠️  No matching entities found in Neo4j")
        
        print()
        print("=" * 60)
        print("  Summary")
        print("=" * 60)
        print(f"✅ Processed {len(documents)} documents")
        print(f"✅ Created {total_relationships} CONTAINS relationships")
        print()
        
        # Verify
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) as count")
            total_rels = result.single()["count"]
            print(f"📊 Total CONTAINS relationships in Neo4j: {total_rels}")
            
            # Show sample
            result = session.run("""
                MATCH (d:Document)-[r:CONTAINS]->(e)
                RETURN d.title as doc_title, e.name as entity_name, e.type as entity_type
                LIMIT 5
            """)
            
            print("\n📋 Sample relationships:")
            for record in result:
                print(f"   📄 {record['doc_title'][:50]}...")
                print(f"      → {record['entity_type']}: {record['entity_name']}")
        
        print()
        print("🎉 Relationships created successfully!")
        print()
        print("🔍 Next steps:")
        print("   1. Refresh Knowledge Hub: http://localhost:3000/knowledge-hub")
        print("   2. Hard refresh browser (Cmd+Shift+R)")
        print("   3. Click on 'pheochromocytoma multisystem crisis' node")
        print("   4. Source documents should now appear!")
        print()

def main():
    creator = RelationshipCreator()
    try:
        creator.create_relationships()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        creator.close()

if __name__ == "__main__":
    main()

