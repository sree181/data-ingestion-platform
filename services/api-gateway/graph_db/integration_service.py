"""
Neo4j Integration Service
Connects AI processing pipeline to Neo4j knowledge graph
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .schema import Neo4jSchema
from .entity_consolidation_service import EntityConsolidationService

logger = logging.getLogger(__name__)

class Neo4jIntegrationService:
    """Service for integrating AI processing results with Neo4j knowledge graph"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        self.schema = Neo4jSchema()
        self.consolidation_service = EntityConsolidationService(neo4j_uri, neo4j_user, neo4j_password)
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
    
    async def initialize_schema(self) -> bool:
        """Initialize Neo4j schema with constraints and indexes"""
        try:
            logger.info("Initializing Neo4j schema...")
            
            # Get schema creation statements
            schema_statements = self.schema.create_schema_cypher()
            
            # Execute schema creation
            import httpx
            async with httpx.AsyncClient() as client:
                for statement in schema_statements:
                    try:
                        response = await client.post(
                            f"http://neo4j:7474/db/neo4j/tx/commit",
                            auth=(self.neo4j_user, self.neo4j_password),
                            json={"statements": [{"statement": statement}]},
                            timeout=30.0
                        )
                        
                        if response.status_code != 200:
                            logger.warning(f"Schema statement failed: {statement[:100]}... - {response.status_code}")
                        else:
                            logger.debug(f"Schema statement executed: {statement[:50]}...")
                            
                    except Exception as e:
                        logger.warning(f"Failed to execute schema statement: {e}")
            
            logger.info("Neo4j schema initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
            return False
    
    async def sync_ai_results_to_neo4j(self, space_id: str = None) -> Dict[str, Any]:
        """Sync AI processing results from Elasticsearch to Neo4j"""
        try:
            logger.info(f"Starting AI results sync to Neo4j for space: {space_id}")
            
            # Use consolidation service to sync entities
            stats = await self.consolidation_service.sync_entities_from_elasticsearch(space_id)
            
            logger.info(f"AI results sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to sync AI results to Neo4j: {e}")
            raise
    
    async def process_document_to_neo4j(self, doc_id: str, ai_results: Dict[str, Any], 
                                      doc_metadata: Dict[str, Any]) -> bool:
        """Process a single document's AI results to Neo4j"""
        try:
            logger.info(f"Processing document {doc_id} to Neo4j")
            
            # Create document node
            await self._create_document_node(doc_id, doc_metadata)
            
            # Process entities
            entities = ai_results.get("entities", [])
            for entity in entities:
                if entity and len(entity) > 0:
                    await self._process_entity(entity, doc_id, doc_metadata)
            
            # Process relationships
            relationships = ai_results.get("relationships", [])
            for rel in relationships:
                if rel and len(rel) > 0:
                    await self._process_relationship(rel, doc_id, doc_metadata)
            
            logger.info(f"Document {doc_id} processed to Neo4j successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process document {doc_id} to Neo4j: {e}")
            return False
    
    async def _create_document_node(self, doc_id: str, doc_metadata: Dict[str, Any]):
        """Create document node in Neo4j"""
        try:
            # Determine document type and label
            doc_type = doc_metadata.get("document_type", "unknown")
            source = doc_metadata.get("source", "unknown")
            
            if doc_type == "research_paper":
                label = "ResearchPaper"
            elif doc_type == "clinical_trial":
                label = "ClinicalTrial"
            elif doc_type == "drug_label":
                label = "FDADocument"
            else:
                label = "Document"
            
            cypher = f"""
            MERGE (d:{label} {{id: $doc_id}})
            SET d.title = $title,
                d.source = $source,
                d.document_type = $document_type,
                d.url = $url,
                d.doi = $doi,
                d.pmid = $pmid,
                d.pmcid = $pmcid,
                d.publication_date = $publication_date,
                d.authors = $authors,
                d.space_id = $space_id,
                d.external_source = $external_source,
                d.ai_processed = $ai_processed,
                d.created_at = datetime(),
                d.updated_at = datetime()
            RETURN d
            """
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "doc_id": doc_id,
                                "title": doc_metadata.get("title", ""),
                                "source": source,
                                "document_type": doc_type,
                                "url": doc_metadata.get("url"),
                                "doi": doc_metadata.get("doi"),
                                "pmid": doc_metadata.get("pmid"),
                                "pmcid": doc_metadata.get("pmcid"),
                                "publication_date": doc_metadata.get("publication_date"),
                                "authors": doc_metadata.get("authors", []),
                                "space_id": doc_metadata.get("space_id"),
                                "external_source": doc_metadata.get("external_source", True),
                                "ai_processed": doc_metadata.get("ai_processed", True)
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to create document node: {response.status_code}")
            
            logger.debug(f"Created document node: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to create document node {doc_id}: {e}")
            raise
    
    async def _process_entity(self, entity: Dict[str, Any], doc_id: str, doc_metadata: Dict[str, Any]):
        """Process entity and create/update node in Neo4j"""
        try:
            # Support both "text" (old format) and "name" (new format)
            entity_text = entity.get("name", entity.get("text", "")).strip()
            entity_type = entity.get("type", "UNKNOWN")
            
            if not entity_text:
                return
            
            # Normalize entity name
            normalized_name = self._normalize_entity_name(entity_text, entity_type)
            
            # Map entity type to Neo4j label
            label_mapping = {
                "PERSON": "Person",
                "ORG": "Organization",
                "ORGANIZATION": "Organization",
                "GPE": "Location",
                "LOCATION": "Location",
                "DRUG": "Drug",
                "MEDICATION": "Drug",
                "DISEASE": "Disease",
                "CONDITION": "Disease",
                "SYMPTOM": "Symptom",
                "PROCEDURE": "Procedure",
                "TRIAL": "ClinicalTrial",
                "DATE": "Date",
                "MONEY": "Money",
                "LAW": "Legal",
                "LEGAL": "Legal"
            }
            
            label = label_mapping.get(entity_type, "Entity")
            entity_id = f"{entity_type}_{normalized_name}_{doc_id[:8]}"
            
            # Check if entity exists
            existing_entity = await self._find_entity_by_name(entity_text, label)
            
            if existing_entity:
                # Update existing entity
                await self._update_entity(existing_entity["id"], entity, doc_id, doc_metadata, label)
            else:
                # Create new entity
                await self._create_entity(entity_id, entity, doc_id, doc_metadata, label, normalized_name)
            
            # Create document-entity relationship
            await self._create_document_entity_relationship(doc_id, entity_id, label, entity)
            
        except Exception as e:
            logger.error(f"Failed to process entity {entity}: {e}")
            raise
    
    async def _process_relationship(self, rel: Dict[str, Any], doc_id: str, doc_metadata: Dict[str, Any]):
        """Process relationship and create edge in Neo4j"""
        try:
            subject = rel.get("subject", "")
            predicate = rel.get("predicate", "")
            object_entity = rel.get("object", "")
            
            if not all([subject, predicate, object_entity]):
                return
            
            # Find subject and object entities
            subject_entity = await self._find_entity_by_name(subject)
            object_entity_node = await self._find_entity_by_name(object_entity)
            
            if not subject_entity or not object_entity_node:
                logger.debug(f"Could not find entities for relationship: {subject} -> {object_entity}")
                return
            
            # Map predicate to relationship type
            rel_type_mapping = {
                "treats": "TREATS",
                "causes": "CAUSES",
                "associated_with": "ASSOCIATED_WITH",
                "studied_in": "STUDIED_IN",
                "approved_by": "APPROVED_BY",
                "researched_by": "RESEARCHED_BY",
                "similar_to": "SIMILAR_TO",
                "contraindicated_with": "CONTRAINDICATED_WITH",
                "enhances": "ENHANCES"
            }
            
            rel_type = rel_type_mapping.get(predicate.lower(), "RELATED_TO")
            
            cypher = f"""
            MATCH (s {{id: $subject_id}}), (o {{id: $object_id}})
            MERGE (s)-[r:{rel_type}]->(o)
            SET r.confidence = $confidence,
                r.context = $context,
                r.frequency = coalesce(r.frequency, 0) + 1,
                r.updated_at = datetime()
            """
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "subject_id": subject_entity["id"],
                                "object_id": object_entity_node["id"],
                                "confidence": rel.get("confidence", 0.5),
                                "context": rel.get("context", "")
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to create relationship: {response.status_code}")
            
            logger.debug(f"Created relationship: {subject} -[{rel_type}]-> {object_entity}")
            
        except Exception as e:
            logger.error(f"Failed to process relationship: {e}")
            raise
    
    def _normalize_entity_name(self, name: str, entity_type: str) -> str:
        """Normalize entity name for matching"""
        normalized = name.lower().strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ["dr.", "prof.", "mr.", "ms.", "mrs.", "dr ", "prof "]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        # Remove common suffixes
        suffixes_to_remove = ["inc.", "llc", "corp.", "ltd.", "co.", "phd", "md", "rn"]
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Handle drug names
        if entity_type in ["DRUG", "MEDICATION"]:
            drug_suffixes = ["tablet", "capsule", "injection", "solution", "cream", "gel", "patch"]
            for suffix in drug_suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)].strip()
        
        return normalized
    
    async def _find_entity_by_name(self, name: str, label: str = None) -> Optional[Dict[str, Any]]:
        """Find entity by name"""
        try:
            if label:
                cypher = f"""
                MATCH (e:{label})
                WHERE e.name = $name OR e.normalized_name = $normalized_name
                RETURN e
                ORDER BY e.confidence_score DESC
                LIMIT 1
                """
            else:
                cypher = """
                MATCH (e)
                WHERE e.name = $name OR e.normalized_name = $normalized_name
                RETURN e
                ORDER BY e.confidence_score DESC
                LIMIT 1
                """
            
            normalized_name = self._normalize_entity_name(name, "UNKNOWN")
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "name": name,
                                "normalized_name": normalized_name
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results") and data["results"][0].get("data"):
                        entity_data = data["results"][0]["data"][0]["row"][0]
                        return entity_data
                return None
                
        except Exception as e:
            logger.error(f"Failed to find entity by name {name}: {e}")
            return None
    
    async def _create_entity(self, entity_id: str, entity: Dict[str, Any], doc_id: str, 
                           doc_metadata: Dict[str, Any], label: str, normalized_name: str):
        """Create new entity in Neo4j"""
        try:
            cypher = f"""
            CREATE (e:{label} {{
                id: $entity_id,
                name: $name,
                normalized_name: $normalized_name,
                type: $entity_type,
                description: $description,
                confidence_score: $confidence,
                source_count: 1,
                sources: [$source],
                created_at: datetime(),
                updated_at: datetime()
            }})
            RETURN e
            """
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "entity_id": entity_id,
                                "name": entity.get("text", ""),
                                "normalized_name": normalized_name,
                                "entity_type": entity.get("type", "UNKNOWN"),
                                "description": entity.get("description", ""),
                                "confidence": entity.get("confidence", 0.5),
                                "source": doc_metadata.get("source", "unknown")
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to create entity: {response.status_code}")
            
            logger.debug(f"Created new entity: {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            raise
    
    async def _update_entity(self, entity_id: str, entity: Dict[str, Any], doc_id: str, 
                           doc_metadata: Dict[str, Any], label: str):
        """Update existing entity in Neo4j"""
        try:
            cypher = f"""
            MATCH (e:{label} {{id: $entity_id}})
            SET e.source_count = e.source_count + 1,
                e.confidence_score = (e.confidence_score * e.source_count + $confidence) / (e.source_count + 1),
                e.updated_at = datetime(),
                e.description = CASE WHEN $description <> '' THEN $description ELSE e.description END
            RETURN e
            """
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "entity_id": entity_id,
                                "confidence": entity.get("confidence", 0.5),
                                "description": entity.get("description", "")
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to update entity: {response.status_code}")
            
            logger.debug(f"Updated existing entity: {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to update entity: {e}")
            raise
    
    async def _create_document_entity_relationship(self, doc_id: str, entity_id: str, 
                                                 label: str, entity: Dict[str, Any]):
        """Create relationship between document and entity"""
        try:
            cypher = f"""
            MATCH (d:Document {{id: $doc_id}}), (e:{label} {{id: $entity_id}})
            MERGE (d)-[r:MENTIONS]->(e)
            SET r.frequency = coalesce(r.frequency, 0) + 1,
                r.confidence = $confidence,
                r.context = $context,
                r.updated_at = datetime()
            """
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://neo4j:7474/db/neo4j/tx/commit",
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": {
                                "doc_id": doc_id,
                                "entity_id": entity_id,
                                "confidence": entity.get("confidence", 0.5),
                                "context": entity.get("context", "")
                            }
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to create document-entity relationship: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Failed to create document-entity relationship: {e}")
            raise
    
    async def close(self):
        """Close connections"""
        await self.consolidation_service.close()
