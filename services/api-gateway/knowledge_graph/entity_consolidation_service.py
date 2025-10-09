"""
Neo4j Entity Consolidation Service
Handles cross-source entity consolidation and relationship building
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import json
from dataclasses import dataclass
from neo4j import AsyncGraphDatabase
import httpx

logger = logging.getLogger(__name__)

@dataclass
class ConsolidatedEntity:
    """Represents a consolidated entity across multiple sources"""
    id: str
    name: str
    entity_type: str
    normalized_name: str
    sources: List[str]
    source_entities: List[Dict[str, Any]]
    confidence_score: float
    properties: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class EntityConsolidationService:
    """Service for consolidating entities across multiple sources"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "password123"):
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.elasticsearch_client = None
        self._init_elasticsearch()
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client for document retrieval"""
        try:
            self.elasticsearch_client = httpx.AsyncClient(
                base_url="http://localhost:9200",
                timeout=30.0
            )
            logger.info("Elasticsearch client initialized for entity consolidation")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
    
    async def close(self):
        """Close database connections"""
        await self.driver.close()
        if self.elasticsearch_client:
            await self.elasticsearch_client.aclose()
    
    async def sync_entities_from_elasticsearch(self, space_id: str = None) -> Dict[str, Any]:
        """Sync all AI-processed entities from Elasticsearch to Neo4j"""
        try:
            logger.info(f"Starting entity sync from Elasticsearch for space: {space_id}")
            
            # Query Elasticsearch for AI-processed documents
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"ai_processed": True}},
                            {"term": {"external_source": True}}
                        ]
                    }
                },
                "size": 1000,  # Process in batches
                "_source": [
                    "title", "source", "document_type", "openai_entities", 
                    "openai_relationships", "openai_key_concepts", "space_id",
                    "url", "doi", "pmid", "pmcid", "publication_date", "authors"
                ]
            }
            
            if space_id:
                query["query"]["bool"]["must"].append({"term": {"space_id.keyword": space_id}})
            
            response = await self.elasticsearch_client.post(
                "/documents/_search",
                json=query
            )
            
            if response.status_code != 200:
                raise Exception(f"Elasticsearch query failed: {response.status_code}")
            
            data = response.json()
            documents = data.get("hits", {}).get("hits", [])
            
            logger.info(f"Found {len(documents)} AI-processed documents to sync")
            
            # Process each document
            stats = {
                "documents_processed": 0,
                "entities_created": 0,
                "relationships_created": 0,
                "entities_consolidated": 0,
                "errors": []
            }
            
            for doc in documents:
                try:
                    doc_stats = await self._process_document_entities(doc)
                    stats["documents_processed"] += 1
                    stats["entities_created"] += doc_stats["entities_created"]
                    stats["relationships_created"] += doc_stats["relationships_created"]
                    stats["entities_consolidated"] += doc_stats["entities_consolidated"]
                except Exception as e:
                    logger.error(f"Failed to process document {doc.get('_id')}: {e}")
                    stats["errors"].append({
                        "document_id": doc.get("_id"),
                        "error": str(e)
                    })
            
            logger.info(f"Entity sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to sync entities from Elasticsearch: {e}")
            raise
    
    async def _process_document_entities(self, doc: Dict[str, Any]) -> Dict[str, int]:
        """Process entities and relationships from a single document"""
        stats = {
            "entities_created": 0,
            "relationships_created": 0,
            "entities_consolidated": 0
        }
        
        try:
            doc_id = doc["_id"]
            doc_source = doc["_source"]
            
            # Create document node
            await self._create_document_node(doc_id, doc_source)
            
            # Process entities
            entities = doc_source.get("openai_entities", [])
            for entity in entities:
                if entity and len(entity) > 0:
                    consolidated = await self._consolidate_entity(entity, doc_id, doc_source)
                    if consolidated:
                        stats["entities_consolidated"] += 1
                    else:
                        stats["entities_created"] += 1
            
            # Process relationships
            relationships = doc_source.get("openai_relationships", [])
            for rel in relationships:
                if rel and len(rel) > 0:
                    await self._create_relationship(rel, doc_id, doc_source)
                    stats["relationships_created"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to process document entities: {e}")
            raise
    
    async def _create_document_node(self, doc_id: str, doc_source: Dict[str, Any]):
        """Create a document node in Neo4j"""
        try:
            # Determine document type
            doc_type = doc_source.get("document_type", "unknown")
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
                d.created_at = datetime(),
                d.updated_at = datetime()
            RETURN d
            """
            
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "doc_id": doc_id,
                    "title": doc_source.get("title", ""),
                    "source": doc_source.get("source", ""),
                    "document_type": doc_type,
                    "url": doc_source.get("url"),
                    "doi": doc_source.get("doi"),
                    "pmid": doc_source.get("pmid"),
                    "pmcid": doc_source.get("pmcid"),
                    "publication_date": doc_source.get("publication_date"),
                    "authors": doc_source.get("authors", []),
                    "space_id": doc_source.get("space_id")
                })
            
            logger.debug(f"Created document node: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to create document node {doc_id}: {e}")
            raise
    
    async def _consolidate_entity(self, entity: Dict[str, Any], doc_id: str, doc_source: Dict[str, Any]) -> bool:
        """Consolidate entity with existing entities or create new one"""
        try:
            entity_text = entity.get("text", "").strip()
            entity_type = entity.get("type", "UNKNOWN")
            
            if not entity_text:
                return False
            
            # Normalize entity name for matching
            normalized_name = self._normalize_entity_name(entity_text, entity_type)
            
            # Check if similar entity already exists
            existing_entity = await self._find_similar_entity(normalized_name, entity_type)
            
            if existing_entity:
                # Update existing entity
                await self._update_existing_entity(existing_entity, entity, doc_id, doc_source)
                return True
            else:
                # Create new entity
                await self._create_new_entity(entity, doc_id, doc_source, normalized_name)
                return False
                
        except Exception as e:
            logger.error(f"Failed to consolidate entity {entity}: {e}")
            return False
    
    def _normalize_entity_name(self, name: str, entity_type: str) -> str:
        """Normalize entity name for matching across sources"""
        # Basic normalization
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
        
        # Handle drug names (remove common suffixes)
        if entity_type in ["DRUG", "MEDICATION"]:
            drug_suffixes = ["tablet", "capsule", "injection", "solution", "cream", "gel", "patch"]
            for suffix in drug_suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)].strip()
        
        return normalized
    
    async def _find_similar_entity(self, normalized_name: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """Find similar entity in Neo4j"""
        try:
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
            
            cypher = f"""
            MATCH (e:{label})
            WHERE e.normalized_name = $normalized_name
               OR e.name =~ $name_pattern
               OR e.name = $exact_name
            RETURN e
            ORDER BY e.confidence_score DESC
            LIMIT 1
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {
                    "normalized_name": normalized_name,
                    "name_pattern": f"(?i).*{normalized_name}.*",
                    "exact_name": normalized_name
                })
                
                record = await result.single()
                if record:
                    return dict(record["e"])
                return None
                
        except Exception as e:
            logger.error(f"Failed to find similar entity: {e}")
            return None
    
    async def _update_existing_entity(self, existing_entity: Dict[str, Any], 
                                    new_entity: Dict[str, Any], doc_id: str, doc_source: Dict[str, Any]):
        """Update existing entity with new information"""
        try:
            entity_id = existing_entity["id"]
            entity_type = new_entity.get("type", "UNKNOWN")
            
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
            
            # Update entity properties
            cypher = f"""
            MATCH (e:{label} {{id: $entity_id}})
            SET e.source_count = e.source_count + 1,
                e.confidence_score = (e.confidence_score * e.source_count + $confidence) / (e.source_count + 1),
                e.updated_at = datetime(),
                e += $properties
            RETURN e
            """
            
            # Prepare properties
            properties = {
                "description": new_entity.get("description", existing_entity.get("description", "")),
                "confidence": new_entity.get("confidence", 0.5),
                "context": new_entity.get("context", existing_entity.get("context", ""))
            }
            
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "entity_id": entity_id,
                    "confidence": new_entity.get("confidence", 0.5),
                    "properties": properties
                })
            
            # Create relationship between document and entity
            await self._create_document_entity_relationship(doc_id, entity_id, label, new_entity)
            
            logger.debug(f"Updated existing entity: {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to update existing entity: {e}")
            raise
    
    async def _create_new_entity(self, entity: Dict[str, Any], doc_id: str, 
                               doc_source: Dict[str, Any], normalized_name: str):
        """Create new entity in Neo4j"""
        try:
            entity_type = entity.get("type", "UNKNOWN")
            entity_text = entity.get("text", "")
            
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
            entity_id = f"{entity_type}_{normalized_name}_{str(uuid.uuid4())[:8]}"
            
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
            
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "entity_id": entity_id,
                    "name": entity_text,
                    "normalized_name": normalized_name,
                    "entity_type": entity_type,
                    "description": entity.get("description", ""),
                    "confidence": entity.get("confidence", 0.5),
                    "source": doc_source.get("source", "unknown")
                })
            
            # Create relationship between document and entity
            await self._create_document_entity_relationship(doc_id, entity_id, label, entity)
            
            logger.debug(f"Created new entity: {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to create new entity: {e}")
            raise
    
    async def _create_document_entity_relationship(self, doc_id: str, entity_id: str, 
                                                 entity_label: str, entity: Dict[str, Any]):
        """Create relationship between document and entity"""
        try:
            cypher = f"""
            MATCH (d:Document {{id: $doc_id}}), (e:{entity_label} {{id: $entity_id}})
            MERGE (d)-[r:MENTIONS]->(e)
            SET r.frequency = coalesce(r.frequency, 0) + 1,
                r.confidence = $confidence,
                r.context = $context,
                r.updated_at = datetime()
            """
            
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "doc_id": doc_id,
                    "entity_id": entity_id,
                    "confidence": entity.get("confidence", 0.5),
                    "context": entity.get("context", "")
                })
            
        except Exception as e:
            logger.error(f"Failed to create document-entity relationship: {e}")
            raise
    
    async def _create_relationship(self, rel: Dict[str, Any], doc_id: str, doc_source: Dict[str, Any]):
        """Create relationship between entities"""
        try:
            # Extract relationship components
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
            
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "subject_id": subject_entity["id"],
                    "object_id": object_entity_node["id"],
                    "confidence": rel.get("confidence", 0.5),
                    "context": rel.get("context", "")
                })
            
            logger.debug(f"Created relationship: {subject} -[{rel_type}]-> {object_entity}")
            
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            raise
    
    async def _find_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find entity by name across all types"""
        try:
            cypher = """
            MATCH (e)
            WHERE e.name = $name OR e.normalized_name = $normalized_name
            RETURN e
            ORDER BY e.confidence_score DESC
            LIMIT 1
            """
            
            normalized_name = self._normalize_entity_name(name, "UNKNOWN")
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {
                    "name": name,
                    "normalized_name": normalized_name
                })
                
                record = await result.single()
                if record:
                    return dict(record["e"])
                return None
                
        except Exception as e:
            logger.error(f"Failed to find entity by name {name}: {e}")
            return None
    
    async def get_consolidated_entities(self, entity_type: str = None, 
                                      limit: int = 100) -> List[ConsolidatedEntity]:
        """Get consolidated entities from Neo4j"""
        try:
            if entity_type:
                label_mapping = {
                    "PERSON": "Person",
                    "ORG": "Organization",
                    "DRUG": "Drug", 
                    "DISEASE": "Disease",
                    "SYMPTOM": "Symptom",
                    "PROCEDURE": "Procedure",
                    "TRIAL": "ClinicalTrial"
                }
                label = label_mapping.get(entity_type, "Entity")
                cypher = f"MATCH (e:{label}) RETURN e ORDER BY e.confidence_score DESC LIMIT $limit"
            else:
                cypher = "MATCH (e) WHERE e:Person OR e:Organization OR e:Drug OR e:Disease RETURN e ORDER BY e.confidence_score DESC LIMIT $limit"
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {"limit": limit})
                entities = []
                
                async for record in result:
                    entity_data = dict(record["e"])
                    entities.append(ConsolidatedEntity(
                        id=entity_data["id"],
                        name=entity_data["name"],
                        entity_type=entity_data.get("type", "UNKNOWN"),
                        normalized_name=entity_data.get("normalized_name", ""),
                        sources=entity_data.get("sources", []),
                        source_entities=[],
                        confidence_score=entity_data.get("confidence_score", 0.0),
                        properties=entity_data,
                        relationships=[],
                        created_at=datetime.fromisoformat(entity_data.get("created_at", "2024-01-01T00:00:00")),
                        updated_at=datetime.fromisoformat(entity_data.get("updated_at", "2024-01-01T00:00:00"))
                    ))
                
                return entities
                
        except Exception as e:
            logger.error(f"Failed to get consolidated entities: {e}")
            return []
    
    async def get_entity_relationships(self, entity_id: str, 
                                     relationship_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get relationships for a specific entity"""
        try:
            if relationship_types:
                rel_filter = "|".join(relationship_types)
                cypher = f"""
                MATCH (e {{id: $entity_id}})-[r:{rel_filter}]-(related)
                RETURN r, related
                ORDER BY r.confidence DESC
                """
            else:
                cypher = """
                MATCH (e {id: $entity_id})-[r]-(related)
                RETURN r, related
                ORDER BY r.confidence DESC
                """
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {"entity_id": entity_id})
                relationships = []
                
                async for record in result:
                    rel_data = dict(record["r"])
                    related_entity = dict(record["related"])
                    relationships.append({
                        "relationship": rel_data,
                        "related_entity": related_entity
                    })
                
                return relationships
                
        except Exception as e:
            logger.error(f"Failed to get entity relationships: {e}")
            return []
    
    async def create_knowledge_hub(self, seed_entity_id: str, 
                                 max_hops: int = 2) -> Dict[str, Any]:
        """Create a knowledge hub around a seed entity"""
        try:
            # Get seed entity
            cypher = "MATCH (e {id: $entity_id}) RETURN e"
            async with self.driver.session() as session:
                result = await session.run(cypher, {"entity_id": seed_entity_id})
                seed_record = await result.single()
                
                if not seed_record:
                    raise Exception(f"Entity {seed_entity_id} not found")
                
                seed_entity = dict(seed_record["e"])
            
            # Get connected entities within max_hops
            cypher = f"""
            MATCH (e {{id: $entity_id}})-[r*1..{max_hops}]-(connected)
            RETURN DISTINCT connected, 
                   length(shortestPath((e)-[*]-(connected))) as distance
            ORDER BY connected.confidence_score DESC
            LIMIT 100
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {"entity_id": seed_entity_id})
                connected_entities = []
                
                async for record in result:
                    entity_data = dict(record["connected"])
                    connected_entities.append({
                        "entity": entity_data,
                        "distance": record["distance"]
                    })
            
            # Get relationships between entities
            cypher = """
            MATCH (e {id: $entity_id})-[r]-(connected)
            RETURN r, connected
            ORDER BY r.confidence DESC
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher, {"entity_id": seed_entity_id})
                relationships = []
                
                async for record in result:
                    rel_data = dict(record["r"])
                    related_entity = dict(record["connected"])
                    relationships.append({
                        "relationship": rel_data,
                        "related_entity": related_entity
                    })
            
            return {
                "seed_entity": seed_entity,
                "connected_entities": connected_entities,
                "relationships": relationships,
                "total_entities": len(connected_entities) + 1,
                "total_relationships": len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Failed to create knowledge hub: {e}")
            raise
