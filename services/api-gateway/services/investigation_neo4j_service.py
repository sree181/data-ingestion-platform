"""
Investigation Board Service using Neo4j
Stores investigation boards, pinned entities, findings, and connections as a graph
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
import os
import httpx

logger = logging.getLogger(__name__)


class InvestigationNeo4jService:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def _execute_query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            raise
    
    # ============ Board Operations ============
    
    async def create_board(self, user_id: str, title: str, description: str = None, 
                          space_id: str = None, status: str = "active") -> Dict[str, Any]:
        """Create a new investigation board"""
        board_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        cypher = """
        MERGE (u:User {id: $user_id})
        CREATE (b:InvestigationBoard {
            id: $board_id,
            title: $title,
            description: $description,
            space_id: $space_id,
            status: $status,
            created_at: $created_at,
            updated_at: $created_at
        })
        CREATE (u)-[:OWNS]->(b)
        RETURN b
        """
        
        result = self._execute_query(cypher, {
            "user_id": user_id,
            "board_id": board_id,
            "title": title,
            "description": description,
            "space_id": space_id,
            "status": status,
            "created_at": created_at
        })
        
        if result:
            return result[0]["b"]
        return None
    
    async def get_boards(self, user_id: str, space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all boards for a user, optionally filtered by space"""
        if space_id:
            cypher = """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:InvestigationBoard {space_id: $space_id})
            OPTIONAL MATCH (b)-[:CONTAINS]->(pe:PinnedEntity)
            RETURN b, count(pe) as entity_count
            ORDER BY b.updated_at DESC
            """
            params = {"user_id": user_id, "space_id": space_id}
        else:
            cypher = """
            MATCH (u:User {id: $user_id})-[:OWNS]->(b:InvestigationBoard)
            OPTIONAL MATCH (b)-[:CONTAINS]->(pe:PinnedEntity)
            RETURN b, count(pe) as entity_count
            ORDER BY b.updated_at DESC
            """
            params = {"user_id": user_id}
        
        results = self._execute_query(cypher, params)
        
        boards = []
        for row in results:
            board_data = row["b"]
            board_data["entity_count"] = row["entity_count"]
            boards.append(board_data)
        
        return boards
    
    async def get_board_by_id(self, board_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a board with all its entities, findings, and connections"""
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(b:InvestigationBoard {id: $board_id})
        OPTIONAL MATCH (b)-[:CONTAINS]->(pe:PinnedEntity)
        OPTIONAL MATCH (pe)-[:HAS_FINDING]->(f:Finding)
        WITH b, pe, collect(DISTINCT f) as findings
        OPTIONAL MATCH (pe)-[conn:CONNECTS_TO]->(target:PinnedEntity)
        RETURN b,
               collect(DISTINCT {
                   entity: pe,
                   findings: findings
               }) as entities,
               collect(DISTINCT {
                   source_id: pe.id,
                   target_id: target.id,
                   connection_type: conn.connection_type,
                   notes: conn.notes,
                   created_at: conn.created_at
               }) as connections
        """
        
        results = self._execute_query(cypher, {"board_id": board_id, "user_id": user_id})
        
        if not results:
            return None
        
        row = results[0]
        board = row["b"]
        
        # Filter out null entities
        entities = [e for e in row["entities"] if e["entity"] is not None]
        connections = [c for c in row["connections"] if c["source_id"] is not None and c["target_id"] is not None]
        
        board["pinned_entities"] = entities
        board["connections"] = connections
        
        return board
    
    async def update_board(self, board_id: str, user_id: str, title: str = None, 
                          description: str = None, status: str = None) -> Optional[Dict[str, Any]]:
        """Update a board's properties"""
        updates = []
        params = {"board_id": board_id, "user_id": user_id, "updated_at": datetime.now().isoformat()}
        
        if title is not None:
            updates.append("b.title = $title")
            params["title"] = title
        if description is not None:
            updates.append("b.description = $description")
            params["description"] = description
        if status is not None:
            updates.append("b.status = $status")
            params["status"] = status
        
        if not updates:
            return await self.get_board_by_id(board_id, user_id)
        
        updates.append("b.updated_at = $updated_at")
        
        cypher = f"""
        MATCH (u:User {{id: $user_id}})-[:OWNS]->(b:InvestigationBoard {{id: $board_id}})
        SET {', '.join(updates)}
        RETURN b
        """
        
        results = self._execute_query(cypher, params)
        return results[0]["b"] if results else None
    
    async def delete_board(self, board_id: str, user_id: str) -> bool:
        """Delete a board and all its contents"""
        cypher = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(b:InvestigationBoard {id: $board_id})
        OPTIONAL MATCH (b)-[:CONTAINS]->(pe:PinnedEntity)
        OPTIONAL MATCH (pe)-[:HAS_FINDING]->(f:Finding)
        DETACH DELETE f, pe, b
        RETURN count(b) as deleted
        """
        
        results = self._execute_query(cypher, {"board_id": board_id, "user_id": user_id})
        return results[0]["deleted"] > 0 if results else False
    
    # ============ Pinned Entity Operations ============
    
    async def pin_entity(self, board_id: str, entity_name: str, entity_type: str = None,
                        pin_reason: str = None, position_x: float = 0.0, 
                        position_y: float = 0.0, knowledge_hub_entity_id: str = None) -> Dict[str, Any]:
        """Pin an entity to a board"""
        pin_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        cypher = """
        MATCH (b:InvestigationBoard {id: $board_id})
        CREATE (pe:PinnedEntity {
            id: $pin_id,
            entity_name: $entity_name,
            entity_type: $entity_type,
            pin_reason: $pin_reason,
            position_x: $position_x,
            position_y: $position_y,
            knowledge_hub_entity_id: $knowledge_hub_entity_id,
            created_at: $created_at
        })
        CREATE (b)-[:CONTAINS]->(pe)
        SET b.updated_at = $created_at
        RETURN pe
        """
        
        results = self._execute_query(cypher, {
            "board_id": board_id,
            "pin_id": pin_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "pin_reason": pin_reason,
            "position_x": position_x,
            "position_y": position_y,
            "knowledge_hub_entity_id": knowledge_hub_entity_id,
            "created_at": created_at
        })
        
        return results[0]["pe"] if results else None
    
    async def get_pinned_entity(self, pin_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pinned entity by ID"""
        cypher = """
        MATCH (b:InvestigationBoard)-[:CONTAINS]->(pe:PinnedEntity {id: $pin_id})
        RETURN pe, b.id as board_id
        """
        
        results = self._execute_query(cypher, {"pin_id": pin_id})
        if not results:
            return None
        
        pe = results[0]["pe"]
        return {
            "id": pe.get("id"),
            "entity_name": pe.get("entity_name"),
            "entity_type": pe.get("entity_type"),
            "pin_reason": pe.get("pin_reason"),
            "position_x": pe.get("position_x"),
            "position_y": pe.get("position_y"),
            "knowledge_hub_entity_id": pe.get("knowledge_hub_entity_id"),
            "board_id": results[0]["board_id"],
            "created_at": pe.get("created_at")
        }
    
    async def unpin_entity(self, pin_id: str, board_id: str) -> bool:
        """Remove a pinned entity and its findings"""
        cypher = """
        MATCH (b:InvestigationBoard {id: $board_id})-[:CONTAINS]->(pe:PinnedEntity {id: $pin_id})
        OPTIONAL MATCH (pe)-[:HAS_FINDING]->(f:Finding)
        DETACH DELETE f, pe
        SET b.updated_at = $updated_at
        RETURN count(pe) as deleted
        """
        
        results = self._execute_query(cypher, {
            "pin_id": pin_id,
            "board_id": board_id,
            "updated_at": datetime.now().isoformat()
        })
        
        return results[0]["deleted"] > 0 if results else False
    
    async def update_pinned_entity(self, pin_id: str, board_id: str, 
                                  position_x: float = None, position_y: float = None,
                                  pin_reason: str = None) -> Optional[Dict[str, Any]]:
        """Update a pinned entity's position or reason"""
        updates = []
        params = {"pin_id": pin_id, "board_id": board_id, "updated_at": datetime.now().isoformat()}
        
        if position_x is not None:
            updates.append("pe.position_x = $position_x")
            params["position_x"] = position_x
        if position_y is not None:
            updates.append("pe.position_y = $position_y")
            params["position_y"] = position_y
        if pin_reason is not None:
            updates.append("pe.pin_reason = $pin_reason")
            params["pin_reason"] = pin_reason
        
        if not updates:
            return None
        
        cypher = f"""
        MATCH (b:InvestigationBoard {{id: $board_id}})-[:CONTAINS]->(pe:PinnedEntity {{id: $pin_id}})
        SET {', '.join(updates)}, b.updated_at = $updated_at
        RETURN pe
        """
        
        results = self._execute_query(cypher, params)
        return results[0]["pe"] if results else None
    
    # ============ Finding Operations ============
    
    async def add_finding(self, pin_id: str, user_id: str, finding_type: str,
                         content: str, tags: List[str] = None) -> Dict[str, Any]:
        """Add a finding/note to a pinned entity"""
        finding_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        cypher = """
        MATCH (pe:PinnedEntity {id: $pin_id})
        CREATE (f:Finding {
            id: $finding_id,
            user_id: $user_id,
            finding_type: $finding_type,
            content: $content,
            tags: $tags,
            created_at: $created_at,
            updated_at: $created_at
        })
        CREATE (pe)-[:HAS_FINDING]->(f)
        RETURN f
        """
        
        results = self._execute_query(cypher, {
            "pin_id": pin_id,
            "finding_id": finding_id,
            "user_id": user_id,
            "finding_type": finding_type,
            "content": content,
            "tags": tags or [],
            "created_at": created_at
        })
        
        return results[0]["f"] if results else None
    
    async def update_finding(self, finding_id: str, user_id: str,
                           finding_type: str = None, content: str = None,
                           tags: List[str] = None) -> Optional[Dict[str, Any]]:
        """Update a finding"""
        updates = []
        params = {"finding_id": finding_id, "user_id": user_id, "updated_at": datetime.now().isoformat()}
        
        if finding_type is not None:
            updates.append("f.finding_type = $finding_type")
            params["finding_type"] = finding_type
        if content is not None:
            updates.append("f.content = $content")
            params["content"] = content
        if tags is not None:
            updates.append("f.tags = $tags")
            params["tags"] = tags
        
        if not updates:
            return None
        
        updates.append("f.updated_at = $updated_at")
        
        cypher = f"""
        MATCH (f:Finding {{id: $finding_id, user_id: $user_id}})
        SET {', '.join(updates)}
        RETURN f
        """
        
        results = self._execute_query(cypher, params)
        return results[0]["f"] if results else None
    
    async def delete_finding(self, finding_id: str, user_id: str) -> bool:
        """Delete a finding"""
        cypher = """
        MATCH (f:Finding {id: $finding_id, user_id: $user_id})
        DETACH DELETE f
        RETURN count(f) as deleted
        """
        
        results = self._execute_query(cypher, {"finding_id": finding_id, "user_id": user_id})
        return results[0]["deleted"] > 0 if results else False
    
    # ============ Connection Operations ============
    
    async def create_connection(self, board_id: str, source_entity_id: str,
                               target_entity_id: str, connection_type: str = None,
                               notes: str = None) -> Dict[str, Any]:
        """Create a connection between two pinned entities"""
        created_at = datetime.now().isoformat()
        connection_id = str(uuid.uuid4())
        
        cypher = """
        MATCH (b:InvestigationBoard {id: $board_id})-[:CONTAINS]->(source:PinnedEntity {id: $source_id})
        MATCH (b)-[:CONTAINS]->(target:PinnedEntity {id: $target_id})
        MERGE (source)-[conn:CONNECTS_TO]->(target)
        SET conn.id = $connection_id,
            conn.connection_type = $connection_type,
            conn.notes = $notes,
            conn.created_at = $created_at,
            b.updated_at = $created_at
        RETURN conn, source.id as source_id, target.id as target_id
        """
        
        results = self._execute_query(cypher, {
            "board_id": board_id,
            "source_id": source_entity_id,
            "target_id": target_entity_id,
            "connection_id": connection_id,
            "connection_type": connection_type,
            "notes": notes,
            "created_at": created_at
        })
        
        if results and len(results) > 0:
            row = results[0]
            conn = row.get("conn")
            
            # Extract relationship properties
            conn_data = {
                "id": connection_id,
                "connection_type": connection_type,
                "notes": notes,
                "created_at": created_at,
                "source_entity_id": row.get("source_id"),
                "target_entity_id": row.get("target_id")
            }
            return conn_data
        return None
    
    async def delete_connection(self, board_id: str, source_entity_id: str, 
                               target_entity_id: str) -> bool:
        """Delete a connection between entities"""
        cypher = """
        MATCH (b:InvestigationBoard {id: $board_id})-[:CONTAINS]->(source:PinnedEntity {id: $source_id})
        MATCH (b)-[:CONTAINS]->(target:PinnedEntity {id: $target_id})
        MATCH (source)-[conn:CONNECTS_TO]->(target)
        DELETE conn
        SET b.updated_at = $updated_at
        RETURN count(conn) as deleted
        """
        
        results = self._execute_query(cypher, {
            "board_id": board_id,
            "source_id": source_entity_id,
            "target_id": target_entity_id,
            "updated_at": datetime.now().isoformat()
        })
        
        return results[0]["deleted"] > 0 if results else False
    
    # ============ AI Suggestions ============
    
    async def get_entity_suggestions(self, board_id: str, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get AI-powered entity suggestions using semantic similarity and graph relationships
        Returns entities from Knowledge Hub and Elasticsearch that are related but not yet pinned
        """
        try:
            # Get current board entities
            board = await self.get_board_by_id(board_id, user_id)
            if not board or not board.get("pinned_entities"):
                return {"suggestions": []}
            
            # Extract entity names from board
            pinned_entity_names = [ew["entity"]["entity_name"] for ew in board["pinned_entities"] if ew.get("entity")]
            pinned_entity_ids = [ew["entity"]["id"] for ew in board["pinned_entities"] if ew.get("entity")]
            
            suggestions = []
            
            # Strategy 1: Semantic similarity via Elasticsearch (co-occurrence in documents)
            es_suggestions = await self._get_semantic_suggestions(pinned_entity_names, limit * 2)
            
            # Strategy 2: Graph relationships via Neo4j
            graph_suggestions = await self._get_graph_suggestions(pinned_entity_names, pinned_entity_ids, limit)
            
            # Merge and deduplicate suggestions
            seen = set(pinned_entity_names)
            merged = {}
            
            # Add graph suggestions (higher priority)
            for sugg in graph_suggestions:
                name = sugg["entity_name"]
                if name not in seen:
                    merged[name] = sugg
                    seen.add(name)
            
            # Add semantic suggestions
            for sugg in es_suggestions:
                name = sugg["entity_name"]
                if name not in seen:
                    merged[name] = sugg
                    seen.add(name)
            
            # Sort by confidence and limit
            suggestions = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)[:limit]
            
            return {"suggestions": suggestions}
            
        except Exception as e:
            logger.error(f"Failed to get entity suggestions: {e}")
            return {"suggestions": [], "error": str(e)}
    
    async def _get_semantic_suggestions(self, entity_names: List[str], limit: int) -> List[Dict[str, Any]]:
        """Get entity suggestions based on co-occurrence in documents (Elasticsearch)"""
        try:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
            
            # Build query to find documents mentioning these entities
            should_clauses = []
            for name in entity_names:
                should_clauses.append({"match": {"content": {"query": name, "boost": 2.0}}})
                should_clauses.append({"match": {"openai_entities.name": {"query": name, "boost": 3.0}}})
            
            query = {
                "query": {
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                },
                "size": 50,  # Get more documents to find co-occurring entities
                "_source": ["openai_entities", "title"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{es_url}/documents/_search", json=query)
                response.raise_for_status()
                results = response.json()
            
            # Extract co-occurring entities
            entity_counts = {}
            entity_types = {}
            
            for hit in results.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                entities = source.get("openai_entities", [])
                
                for entity in entities:
                    name = entity.get("name")
                    if name and name not in entity_names:
                        entity_counts[name] = entity_counts.get(name, 0) + 1
                        entity_types[name] = entity.get("type", "Entity")
            
            # Convert to suggestions
            suggestions = []
            for name, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
                suggestions.append({
                    "entity_id": None,  # Elasticsearch entities don't have Neo4j IDs yet
                    "entity_name": name,
                    "entity_type": entity_types[name],
                    "confidence": min(0.9, 0.5 + (count / 20)),  # Scale confidence by frequency
                    "reason": f"Co-occurs with your entities in {count} document(s)",
                    "connections": [],
                    "total_connections": count,
                    "source": "elasticsearch"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get semantic suggestions: {e}")
            return []
    
    async def _get_graph_suggestions(self, entity_names: List[str], pinned_ids: List[str], limit: int) -> List[Dict[str, Any]]:
        """Get entity suggestions based on graph relationships (Neo4j)"""
        try:
            # Query Knowledge Hub for related entities (using fuzzy matching)
            cypher = """
            UNWIND $entity_names AS search_name
            MATCH (pinned)
            WHERE toLower(pinned.name) CONTAINS toLower(search_name)
               OR toLower(search_name) CONTAINS toLower(pinned.name)
            WITH pinned
            MATCH (pinned)-[r]-(related)
            WHERE NOT related.id IN $pinned_ids
              AND NOT toLower(related.name) IN [name IN $entity_names | toLower(name)]
            WITH related, 
                 collect(DISTINCT {source: pinned.name, rel_type: type(r), confidence: r.confidence}) as connections,
                 count(DISTINCT pinned) as common_neighbors,
                 avg(r.confidence) as avg_confidence
            RETURN DISTINCT related.id as id,
                   related.name as name,
                   related.type as type,
                   connections,
                   common_neighbors,
                   avg_confidence,
                   size(connections) as total_connections
            ORDER BY common_neighbors DESC, avg_confidence DESC
            LIMIT $limit
            """
            
            results = self._execute_query(cypher, {
                "entity_names": entity_names,
                "pinned_ids": pinned_ids,
                "limit": limit
            })
            
            suggestions = []
            for row in results:
                suggestions.append({
                    "entity_id": row["id"],
                    "entity_name": row["name"],
                    "entity_type": row["type"],
                    "confidence": row["avg_confidence"] or 0.7,
                    "reason": f"Connected to {row['common_neighbors']} entities in knowledge graph",
                    "connections": row["connections"][:3],
                    "total_connections": row["total_connections"],
                    "source": "neo4j"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get graph suggestions: {e}")
            return []
    
    async def get_missing_connections(self, board_id: str, user_id: str) -> Dict[str, Any]:
        """
        Detect missing connections between entities already on the board
        Uses semantic co-occurrence in documents to suggest relationships
        """
        try:
            # Get current board
            board = await self.get_board_by_id(board_id, user_id)
            if not board or not board.get("pinned_entities"):
                return {"missing_connections": []}
            
            # Extract pinned entity info
            pinned_entities = []
            existing_connections = set()
            
            for ew in board["pinned_entities"]:
                if ew.get("entity"):
                    pinned_entities.append({
                        "id": ew["entity"]["id"],
                        "name": ew["entity"]["entity_name"]
                    })
            
            # Track existing connections
            for conn in board.get("connections", []):
                if conn.get("source_id") and conn.get("target_id"):
                    existing_connections.add((conn["source_id"], conn["target_id"]))
                    existing_connections.add((conn["target_id"], conn["source_id"]))
            
            if len(pinned_entities) < 2:
                return {"missing_connections": []}
            
            # Get connections from both Neo4j and Elasticsearch
            graph_connections = await self._get_graph_connections(pinned_entities, existing_connections)
            semantic_connections = await self._get_semantic_connections(pinned_entities, existing_connections)
            
            # Merge and deduplicate
            all_connections = {}
            
            # Add graph connections (higher priority)
            for conn in graph_connections:
                key = (conn["source_entity_id"], conn["target_entity_id"])
                all_connections[key] = conn
            
            # Add semantic connections if not already present
            for conn in semantic_connections:
                key = (conn["source_entity_id"], conn["target_entity_id"])
                if key not in all_connections:
                    all_connections[key] = conn
            
            # Sort by confidence and limit
            missing = sorted(all_connections.values(), key=lambda x: x["confidence"], reverse=True)[:10]
            
            return {"missing_connections": missing}
            
        except Exception as e:
            logger.error(f"Failed to detect missing connections: {e}")
            return {"missing_connections": [], "error": str(e)}
    
    async def _get_graph_connections(self, pinned_entities: List[Dict], existing_connections: set) -> List[Dict[str, Any]]:
        """Get missing connections from Neo4j knowledge graph"""
        try:
            entity_names = [e["name"] for e in pinned_entities]
            
            cypher = """
            UNWIND $entity_names AS name1
            UNWIND $entity_names AS name2
            MATCH (e1)-[r]-(e2)
            WHERE (toLower(e1.name) CONTAINS toLower(name1) OR toLower(name1) CONTAINS toLower(e1.name))
              AND (toLower(e2.name) CONTAINS toLower(name2) OR toLower(name2) CONTAINS toLower(e2.name))
              AND e1.id <> e2.id
              AND id(e1) < id(e2)
            RETURN DISTINCT 
                e1.name as source_name,
                e2.name as target_name,
                type(r) as relationship_type,
                r.confidence as confidence
            ORDER BY r.confidence DESC
            LIMIT 20
            """
            
            results = self._execute_query(cypher, {"entity_names": entity_names})
            
            # Map back to board entity IDs
            name_to_id = {e["name"]: e["id"] for e in pinned_entities}
            
            connections = []
            for row in results:
                source_name = row["source_name"]
                target_name = row["target_name"]
                
                # Find matching board entities (fuzzy)
                source_id = None
                target_id = None
                
                for entity in pinned_entities:
                    if (source_name.lower() in entity["name"].lower() or 
                        entity["name"].lower() in source_name.lower()):
                        source_id = entity["id"]
                    if (target_name.lower() in entity["name"].lower() or 
                        entity["name"].lower() in target_name.lower()):
                        target_id = entity["id"]
                
                if source_id and target_id and source_id != target_id:
                    if (source_id, target_id) not in existing_connections:
                        connections.append({
                            "source_entity_id": source_id,
                            "source_entity_name": next(e["name"] for e in pinned_entities if e["id"] == source_id),
                            "target_entity_id": target_id,
                            "target_entity_name": next(e["name"] for e in pinned_entities if e["id"] == target_id),
                            "suggested_type": row["relationship_type"],
                            "confidence": row["confidence"] or 0.7,
                            "reason": f"Connected in knowledge graph ({row['relationship_type']})",
                            "source": "neo4j"
                        })
            
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get graph connections: {e}")
            return []
    
    async def _get_semantic_connections(self, pinned_entities: List[Dict], existing_connections: set) -> List[Dict[str, Any]]:
        """Get missing connections based on document co-occurrence"""
        try:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
            
            # For each pair of entities, check if they co-occur in documents
            connections = []
            
            for i, entity1 in enumerate(pinned_entities):
                for entity2 in pinned_entities[i+1:]:
                    if (entity1["id"], entity2["id"]) in existing_connections:
                        continue
                    
                    # Search for documents containing both entities
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {"match": {"content": entity1["name"]}},
                                                {"match": {"openai_entities.name": entity1["name"]}}
                                            ],
                                            "minimum_should_match": 1
                                        }
                                    },
                                    {
                                        "bool": {
                                            "should": [
                                                {"match": {"content": entity2["name"]}},
                                                {"match": {"openai_entities.name": entity2["name"]}}
                                            ],
                                            "minimum_should_match": 1
                                        }
                                    }
                                ]
                            }
                        },
                        "size": 10,
                        "_source": ["title", "openai_relationships"]
                    }
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(f"{es_url}/documents/_search", json=query)
                        results = response.json()
                    
                    doc_count = results.get("hits", {}).get("total", {}).get("value", 0)
                    
                    if doc_count > 0:
                        # Try to infer relationship type from documents
                        relationship_type = "related_to"
                        
                        # Check extracted relationships
                        for hit in results.get("hits", {}).get("hits", []):
                            rels = hit.get("_source", {}).get("openai_relationships", [])
                            for rel in rels:
                                if ((rel.get("source") == entity1["name"] and rel.get("target") == entity2["name"]) or
                                    (rel.get("source") == entity2["name"] and rel.get("target") == entity1["name"])):
                                    relationship_type = rel.get("type", "related_to")
                                    break
                        
                        confidence = min(0.9, 0.4 + (doc_count / 10))
                        
                        connections.append({
                            "source_entity_id": entity1["id"],
                            "source_entity_name": entity1["name"],
                            "target_entity_id": entity2["id"],
                            "target_entity_name": entity2["name"],
                            "suggested_type": relationship_type,
                            "confidence": confidence,
                            "reason": f"Co-occur in {doc_count} document(s)",
                            "source": "elasticsearch"
                        })
            
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get semantic connections: {e}")
            return []
    
    async def bulk_add_suggestions(self, board_id: str, user_id: str, 
                                   entity_suggestions: List[str],
                                   connection_suggestions: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Bulk add suggested entities and connections to a board
        """
        try:
            added_entities = []
            added_connections = []
            
            # Add entities
            for entity_name in entity_suggestions:
                try:
                    entity = await self.pin_entity(
                        board_id=board_id,
                        entity_name=entity_name,
                        pin_reason="Added from AI suggestions"
                    )
                    if entity:
                        added_entities.append(entity)
                except Exception as e:
                    logger.warning(f"Failed to add suggested entity {entity_name}: {e}")
            
            # Add connections
            for conn in connection_suggestions:
                try:
                    connection = await self.create_connection(
                        board_id=board_id,
                        source_entity_id=conn["source_entity_id"],
                        target_entity_id=conn["target_entity_id"],
                        connection_type=conn.get("suggested_type", "related_to"),
                        notes=conn.get("reason")
                    )
                    if connection:
                        added_connections.append(connection)
                except Exception as e:
                    logger.warning(f"Failed to add suggested connection: {e}")
            
            return {
                "success": True,
                "added_entities": len(added_entities),
                "added_connections": len(added_connections),
                "entities": added_entities,
                "connections": added_connections
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk add suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "added_entities": 0,
                "added_connections": 0
            }
    
    # ============ Export Operations ============
    
    async def get_entity_specific_suggestions(
        self, 
        pin_id: str,
        entity_name: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get AI suggestions specific to a single entity
        Returns entities related to this specific entity and potential connections
        """
        try:
            logger.info(f"Getting entity-specific suggestions for: {entity_name}")
            
            # Get related entities from Neo4j (entities connected to this one)
            graph_suggestions = await self._get_single_entity_graph_suggestions(entity_name, limit)
            logger.info(f"Found {len(graph_suggestions)} graph suggestions for {entity_name}")
            
            # Get related entities from Elasticsearch (entities co-occurring with this one)
            es_suggestions = await self._get_single_entity_semantic_suggestions(entity_name, limit)
            logger.info(f"Found {len(es_suggestions)} semantic suggestions for {entity_name}")
            
            # Get the board to check which entities are already pinned
            pinned_entity = await self.get_pinned_entity(pin_id)
            if not pinned_entity:
                logger.warning(f"Pinned entity not found for pin_id: {pin_id}")
                return {"related_entities": [], "suggested_connections": []}
            
            board_id = pinned_entity.get("board_id")
            logger.info(f"Fetching board: {board_id}")
            
            # Get pinned entities directly without user validation
            cypher = """
            MATCH (b:InvestigationBoard {id: $board_id})-[:CONTAINS]->(pe:PinnedEntity)
            RETURN collect(pe.entity_name) as entity_names
            """
            results = self._execute_query(cypher, {"board_id": board_id})
            pinned_entity_names = results[0]["entity_names"] if results else []
            logger.info(f"Found {len(pinned_entity_names)} pinned entities on board")
            
            # Merge and deduplicate suggestions
            seen = set(pinned_entity_names)
            merged = {}
            
            # Add graph suggestions (higher priority)
            for sugg in graph_suggestions:
                name = sugg["entity_name"]
                if name not in seen:
                    merged[name] = sugg
                    seen.add(name)
            
            # Add semantic suggestions
            for sugg in es_suggestions:
                name = sugg["entity_name"]
                if name not in seen:
                    merged[name] = sugg
                    seen.add(name)
            
            # Sort by confidence and limit
            related_entities = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)[:limit]
            
            # Get suggested connections between this entity and other pinned entities
            suggested_connections = await self._get_entity_connections_to_board(
                entity_name=entity_name,
                board_entities=pinned_entity_names,
                pin_id=pin_id
            )
            
            return {
                "related_entities": related_entities,
                "suggested_connections": suggested_connections
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to get entity-specific suggestions: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"related_entities": [], "suggested_connections": []}
    
    async def _get_single_entity_graph_suggestions(self, entity_name: str, limit: int) -> List[Dict[str, Any]]:
        """Get entities connected to this specific entity in the knowledge graph"""
        try:
            cypher = """
            MATCH (entity)
            WHERE toLower(entity.name) CONTAINS toLower($entity_name)
               OR toLower($entity_name) CONTAINS toLower(entity.name)
            WITH entity
            MATCH (entity)-[r]-(related)
            WITH related, 
                 type(r) as rel_type,
                 r.confidence as confidence,
                 entity.name as source_entity
            RETURN DISTINCT related.id as id,
                   related.name as name,
                   related.type as type,
                   rel_type,
                   confidence,
                   source_entity
            ORDER BY confidence DESC
            LIMIT $limit
            """
            
            results = self._execute_query(cypher, {"entity_name": entity_name, "limit": limit})
            
            suggestions = []
            for row in results:
                suggestions.append({
                    "entity_id": row["id"],
                    "entity_name": row["name"],
                    "entity_type": row["type"] or "Entity",
                    "confidence": row["confidence"] or 0.7,
                    "reason": f"Connected to {entity_name} via {row['rel_type']} in knowledge graph",
                    "source": "neo4j"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get graph suggestions for entity: {e}")
            return []
    
    async def _get_single_entity_semantic_suggestions(self, entity_name: str, limit: int) -> List[Dict[str, Any]]:
        """Get entities that co-occur with this entity in documents"""
        try:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
            
            # Build query to find documents mentioning this entity
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"content": {"query": entity_name, "boost": 2.0}}},
                            {"match": {"openai_entities.name": {"query": entity_name, "boost": 3.0}}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 50,
                "_source": ["openai_entities", "title"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{es_url}/documents/_search", json=query)
                response.raise_for_status()
                results = response.json()
            
            # Extract co-occurring entities
            entity_counts = {}
            entity_types = {}
            
            for hit in results.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                entities = source.get("openai_entities", [])
                
                for entity in entities:
                    name = entity.get("name")
                    if name and name.lower() != entity_name.lower():
                        entity_counts[name] = entity_counts.get(name, 0) + 1
                        entity_types[name] = entity.get("type", "Entity")
            
            # Convert to suggestions
            suggestions = []
            for name, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
                suggestions.append({
                    "entity_id": None,
                    "entity_name": name,
                    "entity_type": entity_types[name],
                    "confidence": min(0.9, 0.5 + (count / 20)),
                    "reason": f"Co-occurs with {entity_name} in {count} document(s)",
                    "source": "elasticsearch"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get semantic suggestions for entity: {e}")
            return []
    
    async def _get_entity_connections_to_board(
        self,
        entity_name: str,
        board_entities: List[str],
        pin_id: str
    ) -> List[Dict[str, Any]]:
        """Get suggested connections between this entity and other entities on the board"""
        try:
            connections = []
            es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
            
            # For each other entity on the board, check for connections
            for other_entity in board_entities:
                if other_entity.lower() == entity_name.lower():
                    continue
                
                # Check Neo4j for existing relationships
                cypher = """
                MATCH (e1)-[r]-(e2)
                WHERE (toLower(e1.name) CONTAINS toLower($entity1) OR toLower($entity1) CONTAINS toLower(e1.name))
                  AND (toLower(e2.name) CONTAINS toLower($entity2) OR toLower($entity2) CONTAINS toLower(e2.name))
                RETURN type(r) as rel_type, r.confidence as confidence
                LIMIT 1
                """
                
                results = self._execute_query(cypher, {"entity1": entity_name, "entity2": other_entity})
                
                if results:
                    for row in results:
                        connections.append({
                            "source_entity": entity_name,
                            "target_entity": other_entity,
                            "suggested_type": row["rel_type"],
                            "confidence": row["confidence"] or 0.7,
                            "reason": f"Connected in knowledge graph ({row['rel_type']})",
                            "source": "neo4j"
                        })
                else:
                    # Check Elasticsearch for co-occurrence
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {"match": {"content": entity_name}},
                                                {"match": {"openai_entities.name": entity_name}}
                                            ],
                                            "minimum_should_match": 1
                                        }
                                    },
                                    {
                                        "bool": {
                                            "should": [
                                                {"match": {"content": other_entity}},
                                                {"match": {"openai_entities.name": other_entity}}
                                            ],
                                            "minimum_should_match": 1
                                        }
                                    }
                                ]
                            }
                        },
                        "size": 5,
                        "_source": ["title", "openai_relationships"]
                    }
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(f"{es_url}/documents/_search", json=query)
                        doc_results = response.json()
                    
                    doc_count = doc_results.get("hits", {}).get("total", {}).get("value", 0)
                    
                    if doc_count > 0:
                        # Try to infer relationship type from documents
                        relationship_type = "related_to"
                        
                        for hit in doc_results.get("hits", {}).get("hits", []):
                            rels = hit.get("_source", {}).get("openai_relationships", [])
                            for rel in rels:
                                if ((rel.get("source") == entity_name and rel.get("target") == other_entity) or
                                    (rel.get("source") == other_entity and rel.get("target") == entity_name)):
                                    relationship_type = rel.get("type", "related_to")
                                    break
                        
                        confidence = min(0.9, 0.4 + (doc_count / 10))
                        
                        connections.append({
                            "source_entity": entity_name,
                            "target_entity": other_entity,
                            "suggested_type": relationship_type,
                            "confidence": confidence,
                            "reason": f"Co-occur in {doc_count} document(s)",
                            "source": "elasticsearch"
                        })
            
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get entity connections to board: {e}")
            return []
    
    async def export_board(self, board_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Export a board with all its data for download"""
        board = await self.get_board_by_id(board_id, user_id)
        
        if not board:
            return None
        
        return {
            "board": {
                "id": board["id"],
                "title": board["title"],
                "description": board["description"],
                "status": board["status"],
                "created_at": board["created_at"],
                "updated_at": board["updated_at"]
            },
            "entities": board.get("pinned_entities", []),
            "connections": board.get("connections", []),
            "export_date": datetime.now().isoformat()
        }

