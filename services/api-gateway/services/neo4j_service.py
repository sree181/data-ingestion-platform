"""
Neo4j service for knowledge graph operations
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, Neo4jError

from models.api_models import (
    GraphQueryResponse, GraphNode, GraphRelationship, 
    Entity, EntityType, GraphStats
)

logger = structlog.get_logger(__name__)


class Neo4jService:
    """Service for interacting with Neo4j Knowledge Graph"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None
    
    async def connect(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            
            # Test connection
            await self.driver.verify_connectivity()
            
            # Create constraints and indices
            await self._create_constraints()
            
            logger.info("Connected to Neo4j", uri=self.uri)
            
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e))
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j database health"""
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        try:
            async with self.driver.session() as session:
                result = await session.run("CALL dbms.components()")
                components = await result.single()
                
                return {
                    "status": "healthy",
                    "version": components["versions"][0],
                    "edition": components["edition"]
                }
        except Exception as e:
            logger.error("Neo4j health check failed", error=str(e))
            raise
    
    async def _create_constraints(self):
        """Create Neo4j constraints and indices"""
        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            
            # Property existence constraints
            "CREATE CONSTRAINT document_title IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS NOT NULL",
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS NOT NULL",
            
            # Indices for performance
            "CREATE INDEX document_created_at IF NOT EXISTS FOR (d:Document) ON (d.created_at)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX relationship_weight IF NOT EXISTS FOR ()-[r:RELATED]-() ON (r.weight)",
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    # Constraint might already exist, log but continue
                    logger.debug("Constraint creation info", query=constraint, info=str(e))
    
    async def query(
        self, 
        cypher_query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> GraphQueryResponse:
        """Execute a Cypher query and return structured results"""
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        
        # Add LIMIT if not present in query
        query_upper = cypher_query.upper()
        if 'LIMIT' not in query_upper and 'COUNT' not in query_upper:
            cypher_query += f" LIMIT {limit}"
        
        try:
            start_time = datetime.now()
            
            async with self.driver.session() as session:
                result = await session.run(cypher_query, parameters or {})
                records = await result.data()
            
            took = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Extract nodes and relationships from results
            nodes = {}
            relationships = []
            
            for record in records:
                for key, value in record.items():
                    if hasattr(value, 'labels'):  # Node
                        node_id = str(value.element_id)
                        if node_id not in nodes:
                            nodes[node_id] = GraphNode(
                                id=node_id,
                                labels=list(value.labels),
                                properties=dict(value)
                            )
                    elif hasattr(value, 'type'):  # Relationship
                        relationships.append(GraphRelationship(
                            id=str(value.element_id),
                            type=value.type,
                            start_node=str(value.start_node.element_id),
                            end_node=str(value.end_node.element_id),
                            properties=dict(value)
                        ))
            
            return GraphQueryResponse(
                nodes=list(nodes.values()),
                relationships=relationships,
                total=len(records),
                took=took
            )
            
        except Neo4jError as e:
            logger.error("Cypher query error", error=str(e), query=cypher_query)
            raise Exception(f"Query error: {str(e)}")
        except Exception as e:
            logger.error("Neo4j query failed", error=str(e), query=cypher_query)
            raise
    
    async def create_document_node(
        self, 
        document_id: str, 
        title: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Create a document node in the knowledge graph"""
        
        cypher = """
        MERGE (d:Document {id: $document_id})
        SET d.title = $title,
            d.created_at = datetime(),
            d.updated_at = datetime(),
            d += $metadata
        RETURN d
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "document_id": document_id,
                    "title": title,
                    "metadata": metadata
                })
            
            logger.info("Document node created", document_id=document_id)
            return True
            
        except Exception as e:
            logger.error("Failed to create document node", document_id=document_id, error=str(e))
            raise
    
    async def create_entity_node(
        self, 
        entity_id: str, 
        name: str, 
        entity_type: str, 
        properties: Dict[str, Any],
        confidence: float = 1.0
    ) -> bool:
        """Create an entity node in the knowledge graph"""
        
        # Determine label based on entity type
        label_mapping = {
            "PERSON": "Person",
            "ORG": "Organization", 
            "ORGANIZATION": "Organization",
            "GPE": "Location",
            "LOCATION": "Location",
            "DATE": "Date",
            "MONEY": "Money",
            "LAW": "Law",
            "LEGAL": "Legal"
        }
        
        label = label_mapping.get(entity_type.upper(), "Entity")
        
        cypher = f"""
        MERGE (e:{label} {{id: $entity_id}})
        SET e.name = $name,
            e.type = $entity_type,
            e.confidence = $confidence,
            e.created_at = datetime(),
            e.updated_at = datetime(),
            e += $properties
        RETURN e
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "entity_id": entity_id,
                    "name": name,
                    "entity_type": entity_type,
                    "confidence": confidence,
                    "properties": properties
                })
            
            logger.debug("Entity node created", entity_id=entity_id, name=name, type=entity_type)
            return True
            
        except Exception as e:
            logger.error("Failed to create entity node", entity_id=entity_id, error=str(e))
            raise
    
    async def create_relationship(
        self, 
        start_node_id: str, 
        end_node_id: str, 
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Create a relationship between two nodes"""
        
        cypher = f"""
        MATCH (a {{id: $start_id}}), (b {{id: $end_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "start_id": start_node_id,
                    "end_id": end_node_id,
                    "properties": properties or {}
                })
            
            logger.debug("Relationship created", 
                        start=start_node_id, 
                        end=end_node_id, 
                        type=relationship_type)
            return True
            
        except Exception as e:
            logger.error("Failed to create relationship", error=str(e))
            raise
    
    async def link_document_to_entities(
        self, 
        document_id: str, 
        entity_ids: List[str]
    ) -> bool:
        """Link a document to multiple entities"""
        
        cypher = """
        MATCH (d:Document {id: $document_id})
        UNWIND $entity_ids as entity_id
        MATCH (e {id: entity_id})
        MERGE (d)-[r:MENTIONS]->(e)
        SET r.created_at = datetime()
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(cypher, {
                    "document_id": document_id,
                    "entity_ids": entity_ids
                })
            
            logger.info("Document linked to entities", 
                       document_id=document_id, 
                       entity_count=len(entity_ids))
            return True
            
        except Exception as e:
            logger.error("Failed to link document to entities", error=str(e))
            raise
    
    async def search_entities(
        self, 
        query: str, 
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Entity]:
        """Search for entities by name"""
        
        cypher = """
        MATCH (e:Entity)
        WHERE e.name CONTAINS $query
        """
        
        if entity_type:
            cypher += " AND e.type = $entity_type"
        
        cypher += """
        RETURN e.id as id, e.name as name, e.type as type, 
               e.confidence as confidence, properties(e) as properties
        ORDER BY e.confidence DESC, e.name
        LIMIT $limit
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, {
                    "query": query,
                    "entity_type": entity_type,
                    "limit": limit
                })
                records = await result.data()
            
            entities = []
            for record in records:
                entity = Entity(
                    id=record["id"],
                    name=record["name"],
                    type=EntityType(record["type"]),
                    properties=record["properties"],
                    confidence=record.get("confidence")
                )
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error("Entity search failed", error=str(e))
            raise
    
    async def get_entity_relationships(
        self, 
        entity_id: str, 
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get entity relationships up to specified depth"""
        
        cypher = f"""
        MATCH path = (start {{id: $entity_id}})-[*1..{max_depth}]-(connected)
        RETURN start, connected, relationships(path) as rels
        LIMIT 100
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, {"entity_id": entity_id})
                records = await result.data()
            
            # Process and return relationship data
            relationships = {
                "entity_id": entity_id,
                "connections": [],
                "total_connections": len(records)
            }
            
            for record in records:
                connected = record["connected"]
                rels = record["rels"]
                
                connection = {
                    "entity": {
                        "id": connected["id"],
                        "name": connected.get("name"),
                        "type": connected.get("type")
                    },
                    "relationships": [
                        {
                            "type": rel.type,
                            "properties": dict(rel)
                        } for rel in rels
                    ]
                }
                relationships["connections"].append(connection)
            
            return relationships
            
        except Exception as e:
            logger.error("Failed to get entity relationships", error=str(e))
            raise
    
    async def get_stats(self) -> GraphStats:
        """Get knowledge graph statistics"""
        
        stats_queries = {
            "total_nodes": "MATCH (n) RETURN count(n) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "nodes_by_type": """
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """,
            "relationships_by_type": """
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """
        }
        
        try:
            async with self.driver.session() as session:
                results = {}
                
                # Get total counts
                for key, query in stats_queries.items():
                    if key in ["nodes_by_type", "relationships_by_type"]:
                        result = await session.run(query)
                        records = await result.data()
                        results[key] = {record["type"]: record["count"] for record in records}
                    else:
                        result = await session.run(query)
                        record = await result.single()
                        results[key] = record["count"] if record else 0
            
            return GraphStats(
                total_nodes=results["total_nodes"],
                total_relationships=results["total_relationships"],
                nodes_by_type=results["nodes_by_type"],
                relationships_by_type=results["relationships_by_type"]
            )
            
        except Exception as e:
            logger.error("Failed to get graph stats", error=str(e))
            raise
    
    async def find_similar_documents(
        self, 
        document_id: str, 
        similarity_threshold: float = 0.1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find documents similar to the given document based on shared entities"""
        
        cypher = """
        MATCH (d1:Document {id: $document_id})-[:MENTIONS]->(e)<-[:MENTIONS]-(d2:Document)
        WHERE d1 <> d2
        WITH d2, count(e) as shared_entities
        WHERE shared_entities >= $min_shared
        RETURN d2.id as document_id, d2.title as title, 
               shared_entities, 
               (shared_entities * 1.0) / 
               ((SELECT count(e1) FROM (d1)-[:MENTIONS]->(e1)) + 
                (SELECT count(e2) FROM (d2)-[:MENTIONS]->(e2)) - shared_entities) as similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        min_shared = max(1, int(similarity_threshold * 10))  # Convert threshold to min shared entities
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, {
                    "document_id": document_id,
                    "min_shared": min_shared,
                    "limit": limit
                })
                records = await result.data()
            
            return records
            
        except Exception as e:
            logger.error("Failed to find similar documents", error=str(e))
            raise
    
    async def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all entities mentioned in a document"""
        
        cypher = """
        MATCH (d:Document {id: $document_id})-[r:MENTIONS]->(e)
        RETURN e.id as entity_id, e.name as name, e.type as type, 
               e.confidence as confidence, r.frequency as frequency
        ORDER BY r.frequency DESC, e.confidence DESC
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, {"document_id": document_id})
                records = await result.data()
            
            return records
            
        except Exception as e:
            logger.error("Failed to get document entities", error=str(e))
            raise