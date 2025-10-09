"""
Sync AI-processed documents from Elasticsearch to Neo4j
Reads documents with ai_processed=true and syncs entities/relationships
"""

import asyncio
import sys
import os
sys.path.insert(0, '/app')

from elasticsearch import Elasticsearch
from graph_db.integration_service import Neo4jIntegrationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_documents():
    """Sync all AI-processed documents from Elasticsearch to Neo4j"""
    
    # Initialize services
    es = Elasticsearch(['http://elasticsearch:9200'])
    neo4j_service = Neo4jIntegrationService(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    # Initialize Neo4j schema
    logger.info("🔧 Initializing Neo4j schema...")
    await neo4j_service.initialize_schema()
    
    # Query all AI-processed documents
    query = {
        "query": {
            "term": {"ai_processed": True}
        },
        "size": 1000,
        "_source": ["openai_entities", "openai_relationships", "metadata", "title", "source"]
    }
    
    logger.info("🔍 Querying Elasticsearch for AI-processed documents...")
    results = es.search(index="documents", body=query)
    total = results['hits']['total']['value']
    
    logger.info(f"📊 Found {total} AI-processed documents to sync")
    
    synced_count = 0
    error_count = 0
    
    for hit in results['hits']['hits']:
        doc_id = hit['_id']
        source = hit['_source']
        
        # Extract AI results
        entities = source.get("openai_entities", [])
        relationships = source.get("openai_relationships", [])
        
        # Skip if no entities
        if not entities:
            logger.debug(f"⏭️  Skipping {doc_id} - no entities")
            continue
        
        ai_results = {
            "entities": entities,
            "relationships": relationships
        }
        
        doc_metadata = {
            "title": source.get("title", ""),
            "source": source.get("source", "unknown"),
            **source.get("metadata", {})
        }
        
        try:
            # Sync to Neo4j
            await neo4j_service.process_document_to_neo4j(
                doc_id, 
                ai_results, 
                doc_metadata
            )
            synced_count += 1
            
            if synced_count % 10 == 0:
                logger.info(f"✅ Synced {synced_count}/{total} documents...")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error syncing document {doc_id}: {e}")
    
    logger.info(f"\n🎉 Sync complete!")
    logger.info(f"✅ Successfully synced: {synced_count}/{total}")
    logger.info(f"❌ Errors: {error_count}")
    
    # Get final statistics
    logger.info(f"\n📊 Fetching Neo4j statistics...")
    stats = await neo4j_service.consolidation_service.get_statistics()
    logger.info(f"📈 Total entities in Neo4j: {stats.get('total_nodes', 0)}")
    logger.info(f"🔗 Total relationships: {stats.get('total_relationships', 0)}")

if __name__ == "__main__":
    asyncio.run(sync_documents())


