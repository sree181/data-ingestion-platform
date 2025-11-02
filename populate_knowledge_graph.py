#!/usr/bin/env python3
"""
Populate Knowledge Graph from Elasticsearch Documents
Extracts entities from documents and creates Neo4j graph
"""

import os
import sys
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
import json
from typing import List, Dict, Any

# Configuration
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class KnowledgeGraphPopulator:
    def __init__(self):
        # Use Elasticsearch 8.x compatible settings
        self.es = Elasticsearch([ES_URL], request_timeout=30, max_retries=3, retry_on_timeout=True)
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.es.close()
        self.neo4j_driver.close()
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Fetch all documents from Elasticsearch"""
        print("📄 Fetching documents from Elasticsearch...")
        
        query = {
            "query": {"match_all": {}},
            "size": 1000
        }
        
        response = self.es.search(index="documents", body=query)
        documents = [hit["_source"] for hit in response["hits"]["hits"]]
        
        print(f"✅ Found {len(documents)} documents")
        return documents
    
    def extract_entities_from_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from a document"""
        entities = []
        
        # Check for OpenAI entities
        if "openai_entities" in doc and doc["openai_entities"]:
            for entity in doc["openai_entities"]:
                if isinstance(entity, dict):
                    entities.append({
                        "name": entity.get("name", entity.get("text", "")),
                        "type": entity.get("type", "Entity"),
                        "confidence": entity.get("confidence", 0.9)
                    })
        
        # Check for extracted entities
        if "extracted_entities" in doc and doc["extracted_entities"]:
            for entity in doc["extracted_entities"]:
                if isinstance(entity, dict):
                    entities.append({
                        "name": entity.get("name", entity.get("text", "")),
                        "type": entity.get("type", "Entity"),
                        "confidence": entity.get("confidence", 0.8)
                    })
        
        # Check for classification entities
        if "classification_entities" in doc and doc["classification_entities"]:
            for entity in doc["classification_entities"]:
                if isinstance(entity, dict):
                    entities.append({
                        "name": entity.get("name", entity.get("text", "")),
                        "type": entity.get("type", "Entity"),
                        "confidence": entity.get("confidence", 0.7)
                    })
        
        return entities
    
    def create_document_node(self, session, doc: Dict[str, Any]):
        """Create a Document node in Neo4j"""
        doc_id = doc.get("id", doc.get("_id", "unknown"))
        title = doc.get("title", doc.get("filename", "Untitled"))
        
        cypher = """
        MERGE (d:Document {id: $doc_id})
        SET d.title = $title,
            d.filename = $filename,
            d.source = $source,
            d.classification = $classification,
            d.abstract = $abstract,
            d.created_at = $created_at
        RETURN d
        """
        
        session.run(cypher, {
            "doc_id": doc_id,
            "title": title,
            "filename": doc.get("filename", ""),
            "source": doc.get("source", "unknown"),
            "classification": doc.get("classification", ""),
            "abstract": doc.get("abstract", "")[:500] if doc.get("abstract") else "",
            "created_at": doc.get("created_at", "")
        })
    
    def create_entity_node(self, session, entity: Dict[str, Any], doc_id: str):
        """Create an Entity node and link it to a Document"""
        entity_name = entity["name"]
        entity_type = entity["type"]
        confidence = entity["confidence"]
        
        # Normalize entity name for ID
        normalized_name = entity_name.lower().strip().replace(" ", "_")
        entity_id = f"{entity_type}_{normalized_name}"[:100]  # Limit length
        
        cypher = """
        MERGE (e {id: $entity_id})
        SET e.name = $name,
            e.normalized_name = $normalized_name,
            e.type = $entity_type,
            e.confidence = $confidence,
            e:Entity
        WITH e
        MATCH (d:Document {id: $doc_id})
        MERGE (d)-[r:CONTAINS]->(e)
        SET r.confidence = $confidence
        RETURN e
        """
        
        # Add entity type label
        cypher = cypher.replace("e:Entity", f"e:Entity:{entity_type}")
        
        session.run(cypher, {
            "entity_id": entity_id,
            "name": entity_name,
            "normalized_name": normalized_name,
            "entity_type": entity_type,
            "confidence": confidence,
            "doc_id": doc_id
        })
        
        return entity_id
    
    def populate_graph(self):
        """Main function to populate the knowledge graph"""
        print("=" * 60)
        print("  Knowledge Graph Population")
        print("=" * 60)
        print()
        
        try:
            # Get all documents
            documents = self.get_all_documents()
            
            if not documents:
                print("❌ No documents found in Elasticsearch")
                return
            
            # Process each document
            with self.neo4j_driver.session() as session:
                total_entities = 0
                docs_with_entities = 0
                
                for i, doc in enumerate(documents, 1):
                    doc_id = doc.get("id", doc.get("_id", f"doc_{i}"))
                    title = doc.get("title", doc.get("filename", "Untitled"))
                    
                    print(f"\n📄 [{i}/{len(documents)}] Processing: {title[:60]}...")
                    
                    # Create document node
                    self.create_document_node(session, doc)
                    
                    # Extract and create entity nodes
                    entities = self.extract_entities_from_document(doc)
                    
                    if entities:
                        docs_with_entities += 1
                        print(f"   Found {len(entities)} entities")
                        
                        for entity in entities:
                            try:
                                self.create_entity_node(session, entity, doc_id)
                                total_entities += 1
                            except Exception as e:
                                print(f"   ⚠️  Failed to create entity {entity['name']}: {e}")
                    else:
                        print(f"   ⚠️  No entities found")
            
            print("\n" + "=" * 60)
            print("  Summary")
            print("=" * 60)
            print(f"✅ Processed {len(documents)} documents")
            print(f"✅ Created {total_entities} entity nodes")
            print(f"✅ {docs_with_entities} documents have entities")
            print()
            
            # Verify graph
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                record = result.single()
                total_nodes = record["count"]
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                record = result.single()
                total_relationships = record["count"]
                
                print(f"📊 Neo4j Graph Stats:")
                print(f"   Total Nodes: {total_nodes}")
                print(f"   Total Relationships: {total_relationships}")
                print()
            
            print("✅ Knowledge Graph population complete!")
            print()
            print("🔍 Next steps:")
            print("   1. Refresh Knowledge Hub: http://localhost:3000/knowledge-hub")
            print("   2. Click on any entity node")
            print("   3. Source documents should appear in right panel")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    populator = KnowledgeGraphPopulator()
    try:
        populator.populate_graph()
    finally:
        populator.close()

if __name__ == "__main__":
    main()

