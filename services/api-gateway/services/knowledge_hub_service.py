"""
Knowledge Hub Service
Provides knowledge graph exploration and visualization capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeHubService:
    """Service for knowledge graph exploration and visualization"""
    
    def __init__(self, neo4j_uri: str = "http://neo4j:7474",
                 neo4j_user: str = "neo4j", neo4j_password: str = "password",
                 elasticsearch_service=None):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.tx_endpoint = f"{neo4j_uri}/db/neo4j/tx/commit"
        self.elasticsearch_service = elasticsearch_service
    
    async def get_knowledge_hub(self, entity_name: str, depth: int = 2, 
                               limit: int = 100, space_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get knowledge hub for an entity with its connections
        
        Args:
            entity_name: Name of the central entity
            depth: How many hops to traverse (1 or 2)
            limit: Maximum number of nodes to return
            space_id: Optional filter by space_id
        
        Returns:
            Dictionary with nodes and relationships
        """
        try:
            logger.info(f"Getting knowledge hub for entity: {entity_name}, depth: {depth}")
            
            # Build Cypher query
            if depth == 1:
                cypher = """
                MATCH (center)
                WHERE toLower(center.name) CONTAINS toLower($entity_name)
                OPTIONAL MATCH (center)-[r]-(connected)
                WITH center,
                     collect(DISTINCT {source: startNode(r).id, target: endNode(r).id, type: type(r), confidence: r.confidence, frequency: r.frequency}) as rels,
                     collect(DISTINCT connected) as nodes
                RETURN center, 
                       [rel IN rels WHERE rel.source IS NOT NULL | rel] as relationships,
                       nodes
                LIMIT $limit
                """
            else:  # depth == 2
                cypher = """
                MATCH (center)
                WHERE toLower(center.name) CONTAINS toLower($entity_name)
                OPTIONAL MATCH path = (center)-[r1]-(n1)
                OPTIONAL MATCH (n1)-[r2]-(n2)
                WHERE n2 IS NULL OR n2 <> center
                WITH center, 
                     collect(DISTINCT {rel: r1, source: startNode(r1).id, target: endNode(r1).id, type: type(r1), confidence: r1.confidence, frequency: r1.frequency}) +
                     collect(DISTINCT {rel: r2, source: startNode(r2).id, target: endNode(r2).id, type: type(r2), confidence: r2.confidence, frequency: r2.frequency}) as allRels,
                     collect(DISTINCT n1) + collect(DISTINCT n2) as allNodes
                RETURN center,
                       [rel IN allRels WHERE rel.source IS NOT NULL | rel] as relationships,
                       [node IN allNodes WHERE node IS NOT NULL | node] as nodes
                LIMIT $limit
                """
            
            # Add space_id filter if provided
            if space_id:
                cypher = cypher.replace("WHERE", "WHERE center.space_id = $space_id AND")
            
            # Execute query
            result = await self._execute_cypher(cypher, {
                "entity_name": entity_name,
                "limit": limit,
                "space_id": space_id
            })
            
            # Parse and format results
            graph_data = self._format_graph_data(result)
            
            logger.info(f"Knowledge hub retrieved: {len(graph_data.get('nodes', []))} nodes, "
                       f"{len(graph_data.get('edges', []))} edges")
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Failed to get knowledge hub for {entity_name}: {e}")
            raise
    
    async def get_full_graph(self, limit: int = 500, space_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the entire knowledge graph
        
        Args:
            limit: Maximum number of nodes to return
            space_id: Optional filter by space_id
        
        Returns:
            Dictionary with all nodes and relationships
        """
        try:
            logger.info(f"Getting full knowledge graph, limit: {limit}")
            
            # Query to get all entity nodes + document nodes with their relationships
            # Documents will be shown as special nodes that "CONTAIN" entities
            cypher = """
            // Get entity nodes (excluding system nodes)
            MATCH (n)
            WHERE NOT n:User 
              AND NOT n:InvestigationBoard 
              AND NOT n:PinnedEntity 
              AND NOT n:Finding
              AND NOT n:ClinicalTrial
              AND NOT n:FDADocument
            WITH n LIMIT $limit
            
            // Get relationships between entities
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE NOT m:User 
              AND NOT m:InvestigationBoard 
              AND NOT m:PinnedEntity 
              AND NOT m:Finding
              AND NOT m:ClinicalTrial
              AND NOT m:FDADocument
            
            // Also get documents that contain these entities
            OPTIONAL MATCH (doc:Document)-[doc_rel:HAS_ENTITY]->(n)
            WHERE doc.id IS NOT NULL
            
            RETURN collect(DISTINCT {
                     node: n,
                     labels: labels(n),
                     internal_id: id(n)
                   }) as entity_nodes,
                   collect(DISTINCT {
                     node: doc,
                     labels: ['Document'],
                     internal_id: id(doc)
                   }) as document_nodes,
                   collect(DISTINCT {
                     source: id(startNode(r)), 
                     target: id(endNode(r)), 
                     type: type(r), 
                     predicate: coalesce(r.predicate, type(r)),
                     confidence: coalesce(r.confidence, 0.8)
                   }) as entity_relationships,
                   collect(DISTINCT {
                     source: id(doc),
                     target: id(n),
                     type: 'CONTAINS',
                     predicate: 'CONTAINS',
                     confidence: 1.0
                   }) as document_relationships
            """
            
            # Add space_id filter if provided
            if space_id:
                cypher = cypher.replace("MATCH (n)", "MATCH (n) WHERE n.space_id = $space_id")
            
            # Log the actual query being executed
            logger.info(f"Executing Cypher query:\n{cypher}")
            logger.info(f"With parameters: limit={limit}, space_id={space_id}")
            
            # Execute query
            result = await self._execute_cypher(cypher, {
                "limit": limit,
                "space_id": space_id
            })
            
            logger.info(f"Cypher result structure: {result.keys() if result else 'None'}")
            if result and result.get('results'):
                logger.info(f"Results length: {len(result['results'])}")
                if result['results'] and result['results'][0].get('data'):
                    logger.info(f"Data length: {len(result['results'][0]['data'])}")
            
            # Format results
            if result and result.get('results') and result['results'][0].get('data'):
                data_row = result['results'][0]['data'][0]['row']
                
                # Extract entity nodes, document nodes, and relationships
                entity_nodes_data = data_row[0] if len(data_row) > 0 else []
                document_nodes_data = data_row[1] if len(data_row) > 1 else []
                entity_rels_data = data_row[2] if len(data_row) > 2 else []
                document_rels_data = data_row[3] if len(data_row) > 3 else []
                
                # Combine all nodes
                all_nodes_data = entity_nodes_data + [doc for doc in document_nodes_data if doc and doc.get('node')]
                
                # Format nodes - Neo4j returns node objects, not dicts
                nodes = []
                node_ids = {}  # Map Neo4j internal IDs to our node IDs
                
                for i, node_data in enumerate(all_nodes_data):
                    try:
                        # Debug: log raw node_data structure for first few nodes
                        if i < 3:
                            logger.info(f"Raw node_data[{i}]: {str(node_data)[:200]}")
                        
                        # Extract node properties and labels
                        node_obj = node_data.get('node', {}) if isinstance(node_data, dict) else {}
                        node_labels = node_data.get('labels', []) if isinstance(node_data, dict) else []
                        neo4j_id = node_data.get('internal_id', i) if isinstance(node_data, dict) else i
                        
                        # Get node label/type (use first label, or 'Entity' as fallback)
                        node_type = node_labels[0] if node_labels else 'Entity'
                        
                        # Extract node ID (from 'id' property or generate one)
                        node_id = str(node_obj.get('id', f'node_{i}'))
                        node_ids[neo4j_id] = node_id
                        
                        if i < 3:
                            logger.info(f"Parsed node[{i}]: type={node_type}, labels={node_labels}, id={node_id[:30]}")
                        
                        # Special handling for Document nodes
                        if node_type == 'Document':
                            nodes.append({
                                'id': node_id,
                                'name': node_obj.get('title', node_obj.get('filename', f'Document {node_id[:8]}')),
                                'type': 'Document',
                                'confidence': 1.0,
                                'description': node_obj.get('abstract', '')[:200] if node_obj.get('abstract') else '',
                                'source_types': [node_obj.get('source', 'unknown')],
                                'source_count': 1,
                                'has_pdf': node_obj.get('source') == 'pdf',
                                'has_external': node_obj.get('source') != 'pdf',
                                'classification': node_obj.get('classification', ''),
                                'doc_metadata': {
                                    'source': node_obj.get('source', ''),
                                    'authors': node_obj.get('authors', []),
                                    'publication_date': node_obj.get('publication_date', '')
                                }
                            })
                        else:
                            # Regular entity node
                            nodes.append({
                                'id': node_id,
                                'name': node_obj.get('normalized_name', node_obj.get('name', node_obj.get('title', node_id))),
                                'type': node_type,
                                'confidence': float(node_obj.get('confidence', 0.8)),
                                'description': node_obj.get('description', ''),
                                'source_types': node_obj.get('source_types', []),
                                'source_count': int(node_obj.get('source_count', 1)),
                                'has_pdf': bool(node_obj.get('has_pdf', False)),
                                'has_external': bool(node_obj.get('external_source', False))
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse node[{i}]: {e}")
                        continue
                
                # Combine and format edges
                all_rels_data = entity_rels_data + document_rels_data
                edges = []
                for rel in all_rels_data:
                    if isinstance(rel, dict) and rel.get('source') is not None and rel.get('target') is not None:
                        source_id = node_ids.get(rel['source'], str(rel['source']))
                        target_id = node_ids.get(rel['target'], str(rel['target']))
                        
                        edges.append({
                            'source': source_id,
                            'target': target_id,
                            'type': rel.get('type', 'RELATED_TO'),
                            'predicate': rel.get('predicate', rel.get('type', '')),
                            'confidence': float(rel.get('confidence', 0.8))
                        })
                
                logger.info(f"Full graph retrieved: {len(nodes)} nodes ({sum(1 for n in nodes if n['type'] == 'Document')} documents), {len(edges)} edges")
                
                return {
                    'nodes': nodes,
                    'edges': edges
                }
            
            return {'nodes': [], 'edges': []}
            
        except Exception as e:
            logger.error(f"Failed to get full knowledge graph: {e}")
            raise
    
    async def search_entities(self, query: str, entity_types: Optional[List[str]] = None,
                            limit: int = 20, space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for entities by name or type
        
        Args:
            query: Search query
            entity_types: Optional list of entity types to filter (Drug, Disease, etc.)
            limit: Maximum number of results
            space_id: Optional filter by space_id
        
        Returns:
            List of matching entities
        """
        try:
            logger.info(f"Searching entities: query='{query}', types={entity_types}")
            
            # Build Cypher query
            if entity_types:
                labels = ":".join(entity_types)
                cypher = f"""
                MATCH (e:{labels})
                WHERE toLower(e.name) CONTAINS toLower($query)
                """
            else:
                cypher = """
                MATCH (e)
                WHERE toLower(e.name) CONTAINS toLower($query)
                """
            
            # Add space_id filter
            if space_id:
                cypher += " AND e.space_id = $space_id"
            
            cypher += """
            RETURN e.id as id, e.name as name, labels(e)[0] as type, 
                   e.confidence_score as confidence, e.description as description,
                   e.source_count as source_count
            ORDER BY e.source_count DESC, e.confidence_score DESC
            LIMIT $limit
            """
            
            result = await self._execute_cypher(cypher, {
                "query": query,
                "limit": limit,
                "space_id": space_id
            })
            
            # Parse results
            entities = []
            if result and result.get("results"):
                for row in result["results"][0].get("data", []):
                    if row.get("row"):
                        entities.append({
                            "id": row["row"][0],
                            "name": row["row"][1],
                            "type": row["row"][2],
                            "confidence": row["row"][3] if len(row["row"]) > 3 else 0.5,
                            "description": row["row"][4] if len(row["row"]) > 4 else "",
                            "source_count": row["row"][5] if len(row["row"]) > 5 else 0
                        })
            
            logger.info(f"Found {len(entities)} matching entities")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to search entities: {e}")
            raise
    
    async def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific entity
        
        Args:
            entity_id: Entity name or ID
        
        Returns:
            Entity details with connections
        """
        try:
            # Search by ID first, then fall back to name search
            cypher = """
            MATCH (e)
            WHERE e.id = $entity_id 
               OR toLower(e.normalized_name) = toLower($entity_id) 
               OR toLower(e.name) = toLower($entity_id)
            OPTIONAL MATCH (e)-[r]-(connected)
            WHERE NOT connected:Document 
              AND NOT connected:ClinicalTrial 
              AND NOT connected:FDADocument
            RETURN e, 
                   labels(e) as labels,
                   collect(DISTINCT {type: type(r), direction: CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END, target: coalesce(connected.normalized_name, connected.name, 'Unknown')}) as connections,
                   count(DISTINCT connected) as connection_count
            LIMIT 1
            """
            
            logger.info(f"Searching for entity by ID or name: {entity_id}")
            result = await self._execute_cypher(cypher, {"entity_id": entity_id})
            logger.info(f"Neo4j result: {result}")
            
            if result and result.get("results") and len(result["results"]) > 0 and result["results"][0].get("data") and len(result["results"][0]["data"]) > 0:
                row = result["results"][0]["data"][0]["row"]
                entity_data = row[0]
                
                logger.info(f"Found entity: {entity_data}")
                
                return {
                    "id": entity_data.get("id"),
                    "name": entity_data.get("normalized_name") or entity_data.get("name"),
                    "type": row[1][0] if row[1] else "Entity",
                    "description": entity_data.get("description", ""),
                    "confidence": entity_data.get("confidence_score", 0.5),
                    "source_count": entity_data.get("source_count", 0),
                    "connections": row[2],
                    "connection_count": row[3],
                    "created_at": entity_data.get("created_at"),
                    "updated_at": entity_data.get("updated_at")
                }
            
            logger.warning(f"Entity {entity_id} not found in Neo4j")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get entity details for {entity_id}: {e}")
            raise
    
    async def get_shortest_path(self, source_entity: str, target_entity: str, 
                               max_depth: int = 5) -> Optional[Dict[str, Any]]:
        """
        Find shortest path between two entities
        
        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            max_depth: Maximum path length
        
        Returns:
            Path information with nodes and relationships
        """
        try:
            cypher = """
            MATCH (source), (target)
            WHERE toLower(source.name) CONTAINS toLower($source_name)
              AND toLower(target.name) CONTAINS toLower($target_name)
            MATCH path = shortestPath((source)-[*..5]-(target))
            RETURN path, 
                   length(path) as path_length,
                   [node IN nodes(path) | {id: node.id, name: node.name, type: labels(node)[0]}] as path_nodes,
                   [rel IN relationships(path) | {type: type(rel), confidence: rel.confidence}] as path_relationships
            LIMIT 1
            """
            
            result = await self._execute_cypher(cypher, {
                "source_name": source_entity,
                "target_name": target_entity
            })
            
            if result and result.get("results") and result["results"][0].get("data"):
                row = result["results"][0]["data"][0]["row"]
                
                return {
                    "path_length": row[1],
                    "nodes": row[2],
                    "relationships": row[3],
                    "exists": True
                }
            
            return {"exists": False, "message": "No path found between entities"}
            
        except Exception as e:
            logger.error(f"Failed to find shortest path: {e}")
            raise
    
    async def get_graph_statistics(self, space_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph
        
        Args:
            space_id: Optional filter by space_id
        
        Returns:
            Graph statistics
        """
        try:
            # Build queries for different statistics
            queries = []
            
            # Total nodes by type
            if space_id:
                node_query = """
                MATCH (n)
                WHERE n.space_id = $space_id
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
                """
            else:
                node_query = """
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
                """
            
            # Total relationships by type
            if space_id:
                rel_query = """
                MATCH (n)-[r]->(m)
                WHERE n.space_id = $space_id AND m.space_id = $space_id
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
                """
            else:
                rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
                """
            
            # Execute queries
            node_result = await self._execute_cypher(node_query, {"space_id": space_id})
            rel_result = await self._execute_cypher(rel_query, {"space_id": space_id})
            
            # Parse results
            node_counts = {}
            total_nodes = 0
            if node_result and node_result.get("results"):
                for row in node_result["results"][0].get("data", []):
                    if row.get("row"):
                        node_type = row["row"][0] or "Unknown"
                        count = row["row"][1]
                        node_counts[node_type] = count
                        total_nodes += count
            
            rel_counts = {}
            total_relationships = 0
            if rel_result and rel_result.get("results"):
                for row in rel_result["results"][0].get("data", []):
                    if row.get("row"):
                        rel_type = row["row"][0]
                        count = row["row"][1]
                        rel_counts[rel_type] = count
                        total_relationships += count
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            raise
    
    def _format_graph_data(self, neo4j_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format Neo4j result into nodes and edges for visualization"""
        nodes = []
        edges = []
        node_ids = set()
        
        if not neo4j_result or not neo4j_result.get("results"):
            return {"nodes": [], "edges": []}
        
        try:
            for row_data in neo4j_result["results"][0].get("data", []):
                if not row_data.get("row"):
                    continue
                
                row = row_data["row"]
                
                # Process center node
                if row[0]:
                    center_node = row[0]
                    if center_node.get("id") not in node_ids:
                        nodes.append({
                            "id": center_node.get("id"),
                            "name": center_node.get("name", "Unknown"),
                            "type": center_node.get("type", "Entity"),
                            "confidence": center_node.get("confidence_score", 0.5),
                            "description": center_node.get("description", ""),
                            "is_center": True
                        })
                        node_ids.add(center_node.get("id"))
                
                # Process connected nodes
                if len(row) > 2 and row[2]:
                    for node in row[2]:
                        if node and node.get("id") not in node_ids:
                            nodes.append({
                                "id": node.get("id"),
                                "name": node.get("name", "Unknown"),
                                "type": node.get("type", "Entity"),
                                "confidence": node.get("confidence_score", 0.5),
                                "description": node.get("description", ""),
                                "is_center": False
                            })
                            node_ids.add(node.get("id"))
                
                # Process relationships
                if len(row) > 1 and row[1]:
                    for rel in row[1]:
                        if rel and rel.get("source") and rel.get("target"):
                            # Extract relationship data
                            source_id = rel.get("source")
                            target_id = rel.get("target")
                            edges.append({
                                "id": f"{source_id}_{target_id}",
                                "source": source_id,
                                "target": target_id,
                                "type": rel.get("type", "RELATED_TO"),
                                "confidence": rel.get("confidence", 0.5),
                                "frequency": rel.get("frequency", 1)
                            })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
            
        except Exception as e:
            logger.error(f"Failed to format graph data: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}
    
    async def _execute_cypher(self, cypher: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Cypher query against Neo4j"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.tx_endpoint,
                    auth=(self.neo4j_user, self.neo4j_password),
                    json={
                        "statements": [{
                            "statement": cypher,
                            "parameters": params
                        }]
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Neo4j query failed: {response.status_code} - {response.text}")
                    raise Exception(f"Neo4j query failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Failed to execute Cypher query: {e}")
            raise
    
    async def get_entity_source_documents(self, entity_name: str, space_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Get source documents that mention a specific entity
        
        Args:
            entity_name: Name of the entity to search for
            space_id: Optional filter by space_id
            limit: Maximum number of documents to return
        
        Returns:
            Dictionary with source documents and snippets
        """
        try:
            if not self.elasticsearch_service:
                logger.warning("Elasticsearch service not configured")
                return {"success": False, "documents": [], "error": "Elasticsearch not available"}
            
            logger.info(f"Searching for documents mentioning entity: {entity_name}")
            
            # Build Elasticsearch query
            must_clauses = [
                {
                    "bool": {
                        "should": [
                            {"match": {"content": entity_name}},
                            {"match": {"openai_entities.name": entity_name}},
                            {"match": {"title": entity_name}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                {"term": {"ai_processed": True}}  # Only AI-processed documents
            ]
            
            if space_id:
                must_clauses.append({"term": {"space_id.keyword": space_id}})
            
            query = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3,
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"]
                        }
                    }
                },
                "size": limit,
                "_source": [
                    "doc_id", "title", "content", "doc_type", "source_type", 
                    "is_external", "created_at", "openai_entities", "openai_summary"
                ]
            }
            
            # Execute search using raw Elasticsearch client
            if not self.elasticsearch_service.client:
                await self.elasticsearch_service.connect()
            results = await self.elasticsearch_service.client.search(
                index="documents",
                body=query
            )
            
            documents = []
            for hit in results.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                highlights = hit.get("highlight", {}).get("content", [])
                
                # Find the specific entity in openai_entities to get confidence
                entity_confidence = 0.5
                entity_type = "Entity"
                if source.get("openai_entities"):
                    for entity in source["openai_entities"]:
                        if entity.get("name", "").lower() == entity_name.lower():
                            entity_confidence = entity.get("confidence", 0.5)
                            entity_type = entity.get("type", "Entity")
                            break
                
                documents.append({
                    "doc_id": source.get("doc_id"),
                    "title": source.get("title", "Untitled"),
                    "doc_type": source.get("doc_type", "unknown"),
                    "source_type": source.get("source_type", "pdf"),
                    "is_external": source.get("is_external", False),
                    "created_at": source.get("created_at"),
                    "snippets": highlights[:3] if highlights else [],
                    "summary": source.get("openai_summary", "")[:200] + "..." if source.get("openai_summary") else "",
                    "entity_confidence": entity_confidence,
                    "entity_type": entity_type,
                    "score": hit.get("_score", 0)
                })
            
            logger.info(f"Found {len(documents)} documents mentioning entity: {entity_name}")
            
            return {
                "success": True,
                "entity_name": entity_name,
                "document_count": len(documents),
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Failed to get source documents for entity: {e}")
            return {
                "success": False,
                "documents": [],
                "error": str(e)
            }
    
    async def get_entity_source_documents_by_id(self, entity_id: str, space_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Get source documents for an entity by its ID
        
        Uses a two-tier approach:
        1. Try Elasticsearch search (fast, requires openai_entities field)
        2. Fallback to Neo4j relationships (reliable, works even if ES field missing)
        
        Args:
            entity_id: ID of the entity (e.g., "Drug_aspirin_13ce41e9")
            space_id: Optional filter by space_id
            limit: Maximum number of documents to return
        
        Returns:
            Dictionary with source documents
        """
        try:
            # First, get the entity name from Neo4j
            cypher = """
            MATCH (e {id: $entity_id})
            RETURN coalesce(e.normalized_name, e.name) as name, e.type as type
            LIMIT 1
            """
            
            result = await self._execute_cypher(cypher, {"entity_id": entity_id})
            
            if not result or not result.get('results') or not result['results'][0].get('data'):
                logger.warning(f"Entity not found with ID: {entity_id}")
                return {"success": False, "documents": [], "error": "Entity not found"}
            
            entity_name = result['results'][0]['data'][0]['row'][0]
            entity_type = result['results'][0]['data'][0]['row'][1] if len(result['results'][0]['data'][0]['row']) > 1 else "Entity"
            
            # TIER 1: Try Elasticsearch search (existing method - fast!)
            logger.info(f"Tier 1: Searching Elasticsearch for entity '{entity_name}'")
            es_results = await self.get_entity_source_documents(entity_name, space_id, limit)
            
            if es_results.get("document_count", 0) > 0:
                logger.info(f"✅ Tier 1 SUCCESS: Found {es_results['document_count']} documents via Elasticsearch")
                return es_results
            
            # TIER 2: Fallback to Neo4j relationships
            logger.info(f"Tier 1 returned 0 results. Trying Tier 2: Neo4j relationships for entity '{entity_name}'")
            neo4j_results = await self._get_documents_from_neo4j_relationships(entity_id, entity_name, entity_type, limit)
            
            if neo4j_results.get("document_count", 0) > 0:
                logger.info(f"✅ Tier 2 SUCCESS: Found {neo4j_results['document_count']} documents via Neo4j relationships")
                return neo4j_results
            
            # No results from either method
            logger.warning(f"⚠️  No source documents found for entity '{entity_name}' (ID: {entity_id}) via either method")
            return {
                "success": True,
                "entity_name": entity_name,
                "document_count": 0,
                "documents": [],
                "method": "none"
            }
            
        except Exception as e:
            logger.error(f"Failed to get source documents for entity ID {entity_id}: {e}")
            return {
                "success": False,
                "documents": [],
                "error": str(e)
            }
    
    async def _get_documents_from_neo4j_relationships(self, entity_id: str, entity_name: str, entity_type: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get source documents by traversing Neo4j relationships
        
        This method finds documents that have relationships to the entity:
        - (Document)-[:HAS_ENTITY]->(Entity)
        - (Document)-[:CONTAINS]->(Entity)
        
        Args:
            entity_id: ID of the entity
            entity_name: Name of the entity (for display)
            entity_type: Type of the entity (for display)
            limit: Maximum number of documents
        
        Returns:
            Dictionary with source documents
        """
        try:
            # Query Neo4j to find documents connected to this entity
            cypher = """
            MATCH (doc:Document)-[r]->(e {id: $entity_id})
            WHERE type(r) IN ['HAS_ENTITY', 'CONTAINS', 'MENTIONS']
            RETURN DISTINCT doc.id as doc_id, 
                   doc.title as title,
                   doc.source as source_type,
                   doc.abstract as abstract,
                   doc.filename as filename,
                   r.confidence as rel_confidence,
                   type(r) as rel_type
            LIMIT $limit
            """
            
            result = await self._execute_cypher(cypher, {"entity_id": entity_id, "limit": limit})
            
            if not result or not result.get('results') or not result['results'][0].get('data'):
                logger.info(f"No Neo4j relationships found for entity {entity_id}")
                return {"success": True, "documents": [], "document_count": 0, "method": "neo4j"}
            
            # Extract document IDs and metadata from Neo4j
            neo4j_docs = []
            doc_ids = []
            
            for row_data in result['results'][0]['data']:
                row = row_data['row']
                doc_id = row[0]
                if doc_id:
                    doc_ids.append(doc_id)
                    neo4j_docs.append({
                        "doc_id": doc_id,
                        "title": row[1] or "Untitled",
                        "source_type": row[2] or "unknown",
                        "abstract": row[3] or "",
                        "filename": row[4] or "",
                        "rel_confidence": row[5] or 0.8,
                        "rel_type": row[6] or "HAS_ENTITY"
                    })
            
            if not doc_ids:
                logger.info(f"Neo4j returned relationships but no valid document IDs for entity {entity_id}")
                return {"success": True, "documents": [], "document_count": 0, "method": "neo4j"}
            
            # Fetch full document details from Elasticsearch
            logger.info(f"Fetching {len(doc_ids)} documents from Elasticsearch by doc_id")
            
            if not self.elasticsearch_service.client:
                await self.elasticsearch_service.connect()
            
            # Query Elasticsearch by matching titles (since doc_ids don't match)
            # Build a query that searches for documents by title
            title_queries = []
            for neo4j_doc in neo4j_docs:
                if neo4j_doc["title"] and neo4j_doc["title"] != "Untitled":
                    # Clean the title (remove .pdf extension for matching)
                    clean_title = neo4j_doc["title"].replace(".pdf", "").strip()
                    title_queries.append({
                        "match": {
                            "title": {
                                "query": clean_title,
                                "fuzziness": "AUTO"
                            }
                        }
                    })
            
            if not title_queries:
                # Fallback: return Neo4j data only
                logger.warning(f"No valid titles to search in Elasticsearch, returning Neo4j data only")
                documents = []
                for neo4j_doc in neo4j_docs:
                    documents.append({
                        "id": neo4j_doc["doc_id"],
                        "title": neo4j_doc["title"],
                        "source": neo4j_doc["source_type"],
                        "abstract": neo4j_doc["abstract"],
                        "filename": neo4j_doc["filename"],
                        "confidence": neo4j_doc["rel_confidence"]
                    })
                return {
                    "success": True,
                    "entity_name": entity_name,
                    "document_count": len(documents),
                    "documents": documents,
                    "method": "neo4j_only"
                }
            
            es_query = {
                "query": {
                    "bool": {
                        "should": title_queries,
                        "minimum_should_match": 1
                    }
                },
                "size": limit,
                "_source": [
                    "source_id", "title", "content", "document_type", "source", 
                    "external_source", "created_at", "openai_summary", "abstract",
                    "classification", "classification_confidence"
                ]
            }
            
            es_result = await self.elasticsearch_service.client.search(
                index="documents",
                body=es_query
            )
            
            # Merge Neo4j metadata with Elasticsearch content
            documents = []
            for hit in es_result.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                doc_id = source.get("doc_id")
                
                # Find corresponding Neo4j metadata
                neo4j_meta = next((d for d in neo4j_docs if d["doc_id"] == doc_id), {})
                
                # Extract snippet around entity mention (if content exists)
                snippets = []
                content = source.get("content", "")
                if content and entity_name:
                    # Simple snippet extraction: find entity mentions
                    import re
                    pattern = re.compile(re.escape(entity_name), re.IGNORECASE)
                    matches = list(pattern.finditer(content))
                    for match in matches[:3]:  # Max 3 snippets
                        start = max(0, match.start() - 75)
                        end = min(len(content), match.end() + 75)
                        snippet = content[start:end]
                        # Highlight the entity
                        snippet = pattern.sub(f"<mark>{match.group()}</mark>", snippet)
                        snippets.append(f"...{snippet}...")
                
                documents.append({
                    "doc_id": doc_id,
                    "title": source.get("title") or neo4j_meta.get("title", "Untitled"),
                    "doc_type": source.get("doc_type", "unknown"),
                    "source_type": source.get("source_type") or neo4j_meta.get("source_type", "unknown"),
                    "is_external": source.get("is_external", False),
                    "created_at": source.get("created_at"),
                    "snippets": snippets,
                    "summary": (source.get("openai_summary") or source.get("abstract") or neo4j_meta.get("abstract", ""))[:200] + "...",
                    "entity_confidence": neo4j_meta.get("rel_confidence", 0.8),
                    "entity_type": entity_type,
                    "score": hit.get("_score", 0),
                    "relationship_type": neo4j_meta.get("rel_type", "HAS_ENTITY")
                })
            
            logger.info(f"Successfully fetched {len(documents)} documents from Elasticsearch for entity {entity_name}")
            
            return {
                "success": True,
                "entity_name": entity_name,
                "document_count": len(documents),
                "documents": documents,
                "method": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to get documents from Neo4j relationships: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "documents": [],
                "error": str(e),
                "method": "neo4j"
            }

