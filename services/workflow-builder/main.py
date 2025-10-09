"""
Workflow Builder Service
Standalone microservice for visual workflow creation and execution
Port: 8008
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import httpx
import structlog
import os

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title="Workflow Builder Service",
    description="Visual workflow creation and execution engine",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# ============ Models ============

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = "smoothstep"
    animated: Optional[bool] = True


class WorkflowExecuteRequest(BaseModel):
    workflow_id: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]


class WorkflowSaveRequest(BaseModel):
    title: str
    description: Optional[str] = None
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    tags: Optional[List[str]] = []
    is_template: Optional[bool] = False


class WorkflowUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[WorkflowEdge] = None
    tags: Optional[List[str]] = None


class WorkflowExecutionStatus(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    nodes: Dict[str, Dict[str, Any]]


# ============ Workflow Persistence ============

class WorkflowPersistence:
    """Handle workflow storage in Neo4j"""
    
    def __init__(self):
        self.neo4j_uri = NEO4J_URI
        self.neo4j_user = NEO4J_USER
        self.neo4j_password = NEO4J_PASSWORD
    
    async def save_workflow(
        self, 
        title: str,
        description: str,
        nodes: List[Dict],
        edges: List[Dict],
        tags: List[str] = [],
        is_template: bool = False,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Save workflow to Neo4j"""
        try:
            workflow_id = f"wf_{int(datetime.now().timestamp() * 1000)}"
            
            # Prepare Cypher query
            cypher_query = """
            CREATE (w:Workflow {
                id: $workflow_id,
                title: $title,
                description: $description,
                nodes: $nodes,
                edges: $edges,
                tags: $tags,
                is_template: $is_template,
                created_by: $user_id,
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN w
            """
            
            # Execute via Neo4j HTTP API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.neo4j_uri.replace('bolt://', 'http://').replace(':7687', ':7474')}/db/neo4j/tx/commit",
                    json={
                        "statements": [{
                            "statement": cypher_query,
                            "parameters": {
                                "workflow_id": workflow_id,
                                "title": title,
                                "description": description or "",
                                "nodes": str(nodes),  # Store as JSON string
                                "edges": str(edges),
                                "tags": tags,
                                "is_template": is_template,
                                "user_id": user_id
                            }
                        }]
                    },
                    auth=(self.neo4j_user, self.neo4j_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Workflow saved: {workflow_id}")
                    return {
                        "success": True,
                        "workflow_id": workflow_id,
                        "message": "Workflow saved successfully"
                    }
                else:
                    logger.error(f"Failed to save workflow: {response.text}")
                    return {
                        "success": False,
                        "message": f"Failed to save workflow: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID"""
        try:
            cypher_query = """
            MATCH (w:Workflow {id: $workflow_id})
            RETURN w
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.neo4j_uri.replace('bolt://', 'http://').replace(':7687', ':7474')}/db/neo4j/tx/commit",
                    json={
                        "statements": [{
                            "statement": cypher_query,
                            "parameters": {"workflow_id": workflow_id}
                        }]
                    },
                    auth=(self.neo4j_user, self.neo4j_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results") and data["results"][0].get("data"):
                        workflow_data = data["results"][0]["data"][0]["row"][0]
                        
                        # Parse nodes and edges from JSON strings
                        import json
                        nodes = json.loads(workflow_data["nodes"].replace("'", '"'))
                        edges = json.loads(workflow_data["edges"].replace("'", '"'))
                        
                        return {
                            "success": True,
                            "workflow": {
                                "id": workflow_data["id"],
                                "title": workflow_data["title"],
                                "description": workflow_data["description"],
                                "nodes": nodes,
                                "edges": edges,
                                "tags": workflow_data.get("tags", []),
                                "is_template": workflow_data.get("is_template", False),
                                "created_at": workflow_data.get("created_at"),
                                "updated_at": workflow_data.get("updated_at")
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Workflow not found"
                        }
                        
        except Exception as e:
            logger.error(f"Error getting workflow: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def list_workflows(
        self, 
        is_template: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List all workflows"""
        try:
            # Build query based on filters
            where_clauses = []
            if is_template is not None:
                where_clauses.append(f"w.is_template = {str(is_template).lower()}")
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            cypher_query = f"""
            MATCH (w:Workflow)
            {where_clause}
            RETURN w
            ORDER BY w.updated_at DESC
            LIMIT {limit}
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.neo4j_uri.replace('bolt://', 'http://').replace(':7687', ':7474')}/db/neo4j/tx/commit",
                    json={
                        "statements": [{
                            "statement": cypher_query,
                            "parameters": {}
                        }]
                    },
                    auth=(self.neo4j_user, self.neo4j_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    workflows = []
                    
                    if data.get("results") and data["results"][0].get("data"):
                        for row in data["results"][0]["data"]:
                            workflow_data = row["row"][0]
                            workflows.append({
                                "id": workflow_data["id"],
                                "title": workflow_data["title"],
                                "description": workflow_data["description"],
                                "tags": workflow_data.get("tags", []),
                                "is_template": workflow_data.get("is_template", False),
                                "created_at": workflow_data.get("created_at"),
                                "updated_at": workflow_data.get("updated_at"),
                                "node_count": len(eval(workflow_data["nodes"])),
                                "edge_count": len(eval(workflow_data["edges"]))
                            })
                    
                    return {
                        "success": True,
                        "workflows": workflows,
                        "count": len(workflows)
                    }
                        
        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "workflows": []
            }
    
    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow"""
        try:
            cypher_query = """
            MATCH (w:Workflow {id: $workflow_id})
            DELETE w
            RETURN count(w) as deleted
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.neo4j_uri.replace('bolt://', 'http://').replace(':7687', ':7474')}/db/neo4j/tx/commit",
                    json={
                        "statements": [{
                            "statement": cypher_query,
                            "parameters": {"workflow_id": workflow_id}
                        }]
                    },
                    auth=(self.neo4j_user, self.neo4j_password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Workflow deleted successfully"
                    }
                        
        except Exception as e:
            logger.error(f"Error deleting workflow: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }


# ============ Workflow Executor ============

class WorkflowExecutor:
    """Execute visual workflows node by node"""
    
    def __init__(self):
        self.executions = {}
        self.node_handlers = {
            'upload': self._handle_upload,
            'aiProcessing': self._handle_ai_processing,
            'knowledgeGraph': self._handle_knowledge_graph,
            'report': self._handle_report,
        }
    
    async def execute_workflow(
        self, 
        workflow_id: str,
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute workflow in topological order"""
        try:
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Initialize execution state
            execution_id = f"exec_{workflow_id}_{datetime.now().timestamp()}"
            self.executions[execution_id] = {
                'workflow_id': workflow_id,
                'status': 'running',
                'nodes': {node['id']: {'status': 'pending', 'result': None} for node in nodes},
                'started_at': datetime.now().isoformat()
            }
            
            # Execute asynchronously
            asyncio.create_task(self._execute_nodes(execution_id, nodes, edges))
            
            return {
                'execution_id': execution_id,
                'status': 'running',
                'message': 'Workflow execution started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start workflow execution: {e}")
            raise
    
    async def _execute_nodes(
        self,
        execution_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ):
        """Execute nodes in topological order"""
        try:
            # Build execution order (topological sort)
            execution_order = self._topological_sort(nodes, edges)
            logger.info(f"Execution order: {execution_order}")
            
            # Execute nodes in order
            results = {}
            for node_id in execution_order:
                node = next(n for n in nodes if n['id'] == node_id)
                
                # Update status: running
                self._update_node_status(execution_id, node_id, 'running')
                logger.info(f"Executing node: {node_id} ({node['type']})")
                
                try:
                    # Get inputs from predecessor nodes
                    inputs = self._get_node_inputs(node_id, edges, results)
                    
                    # Execute node handler
                    handler = self.node_handlers.get(node['type'])
                    if not handler:
                        raise ValueError(f"No handler for node type: {node['type']}")
                    
                    result = await handler(node['data'], inputs)
                    results[node_id] = result
                    
                    # Update status: completed
                    self._update_node_status(execution_id, node_id, 'completed', result)
                    logger.info(f"Node completed: {node_id}")
                    
                except Exception as e:
                    logger.error(f"Node execution failed: {node_id} - {e}")
                    self._update_node_status(execution_id, node_id, 'failed', {'error': str(e)})
                    self.executions[execution_id]['status'] = 'failed'
                    self.executions[execution_id]['error'] = str(e)
                    return
            
            # Mark workflow as completed
            self.executions[execution_id]['status'] = 'completed'
            self.executions[execution_id]['completed_at'] = datetime.now().isoformat()
            self.executions[execution_id]['results'] = results
            logger.info(f"Workflow execution completed: {execution_id}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.executions[execution_id]['status'] = 'failed'
            self.executions[execution_id]['error'] = str(e)
    
    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """Sort nodes in execution order using topological sort"""
        graph = {node['id']: [] for node in nodes}
        in_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            graph[source].append(target)
            in_degree[target] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(nodes):
            raise ValueError("Workflow contains a cycle")
        
        return result
    
    def _get_node_inputs(
        self,
        node_id: str,
        edges: List[Dict],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get inputs for a node from its predecessors"""
        inputs = {}
        for edge in edges:
            if edge['target'] == node_id:
                source_id = edge['source']
                if source_id in results:
                    inputs[source_id] = results[source_id]
        return inputs
    
    def _update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        result: Optional[Dict] = None
    ):
        """Update node execution status"""
        if execution_id in self.executions:
            self.executions[execution_id]['nodes'][node_id] = {
                'status': status,
                'result': result,
                'updated_at': datetime.now().isoformat()
            }
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        return self.executions.get(execution_id)
    
    # ============ Node Handlers ============
    
    async def _handle_upload(self, config: Dict, inputs: Dict) -> Dict[str, Any]:
        """Handle document upload node - Query real documents from Elasticsearch"""
        logger.info("Executing upload node - fetching real documents")
        
        # Add delay to make status changes visible in UI
        await asyncio.sleep(1)
        
        try:
            # Query Elasticsearch for real documents
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ELASTICSEARCH_URL}/documents/_search",
                    json={
                        "size": 10,  # Get 10 documents
                        "query": {"match_all": {}},
                        "_source": ["id", "filename", "title"]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('hits', {}).get('hits', [])
                    document_ids = [hit['_id'] for hit in hits]
                    documents = [hit['_source'] for hit in hits]
                    
                    logger.info(f"Found {len(document_ids)} real documents")
                    
                    return {
                        'document_ids': document_ids,
                        'documents': documents,
                        'count': len(document_ids),
                        'message': f'Loaded {len(document_ids)} real documents from Elasticsearch'
                    }
                else:
                    logger.error(f"Failed to fetch documents: {response.status_code}")
                    return {
                        'document_ids': [],
                        'count': 0,
                        'message': 'Failed to fetch documents',
                        'error': f'HTTP {response.status_code}'
                    }
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            return {
                'document_ids': [],
                'count': 0,
                'message': f'Error: {str(e)}'
            }
    
    async def _handle_ai_processing(self, config: Dict, inputs: Dict) -> Dict[str, Any]:
        """Handle AI processing node - Get real AI results from documents"""
        logger.info("Executing AI processing node - analyzing real documents")
        
        # Add delay to make status changes visible in UI
        await asyncio.sleep(2)
        
        document_ids = []
        for input_data in inputs.values():
            if 'document_ids' in input_data:
                document_ids.extend(input_data['document_ids'])
        
        if not document_ids:
            return {
                'processed_count': 0,
                'entities_extracted': 0,
                'relationships_extracted': 0,
                'message': 'No documents to process'
            }
        
        try:
            # Query Elasticsearch for documents with AI results
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ELASTICSEARCH_URL}/documents/_search",
                    json={
                        "size": len(document_ids),
                        "query": {
                            "ids": {"values": document_ids}
                        },
                        "_source": ["openai_entities", "openai_relationships", "openai_key_concepts"]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('hits', {}).get('hits', [])
                    
                    total_entities = 0
                    total_relationships = 0
                    all_entities = []
                    all_relationships = []
                    
                    for hit in hits:
                        source = hit.get('_source', {})
                        entities = source.get('openai_entities', [])
                        relationships = source.get('openai_relationships', [])
                        
                        total_entities += len(entities)
                        total_relationships += len(relationships)
                        all_entities.extend(entities)
                        all_relationships.extend(relationships)
                    
                    logger.info(f"Extracted {total_entities} entities and {total_relationships} relationships")
                    
                    return {
                        'processed_count': len(document_ids),
                        'entities_extracted': total_entities,
                        'relationships_extracted': total_relationships,
                        'entities': all_entities[:50],  # Return first 50 for preview
                        'relationships': all_relationships[:50],
                        'message': f'Processed {len(document_ids)} documents - found {total_entities} entities and {total_relationships} relationships'
                    }
                else:
                    logger.error(f"Failed to fetch AI results: {response.status_code}")
                    return {
                        'processed_count': len(document_ids),
                        'entities_extracted': 0,
                        'relationships_extracted': 0,
                        'message': 'Failed to fetch AI results',
                        'error': f'HTTP {response.status_code}'
                    }
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return {
                'processed_count': 0,
                'entities_extracted': 0,
                'relationships_extracted': 0,
                'message': f'Error: {str(e)}'
            }
    
    async def _handle_knowledge_graph(self, config: Dict, inputs: Dict) -> Dict[str, Any]:
        """Handle knowledge graph building node - Query real Neo4j data"""
        logger.info("Executing knowledge graph node - querying Neo4j")
        
        # Add delay to make status changes visible in UI
        await asyncio.sleep(2)
        
        try:
            # Query Neo4j for current graph statistics
            async with httpx.AsyncClient() as client:
                # Use Neo4j HTTP API to get node/relationship counts
                cypher_query = """
                MATCH (n:Entity)
                WITH count(n) as nodeCount
                MATCH ()-[r]->()
                RETURN nodeCount, count(r) as relCount
                """
                
                response = await client.post(
                    f"{NEO4J_URI.replace('bolt://', 'http://').replace(':7687', ':7474')}/db/neo4j/tx/commit",
                    json={
                        "statements": [{
                            "statement": cypher_query
                        }]
                    },
                    auth=(NEO4J_USER, NEO4J_PASSWORD),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [{}])[0]
                    rows = results.get('data', [{}])
                    
                    if rows:
                        row_data = rows[0].get('row', [0, 0])
                        nodes_count = row_data[0] if len(row_data) > 0 else 0
                        rels_count = row_data[1] if len(row_data) > 1 else 0
                    else:
                        nodes_count = 0
                        rels_count = 0
                    
                    logger.info(f"Neo4j has {nodes_count} nodes and {rels_count} relationships")
                    
                    return {
                        'nodes_created': nodes_count,
                        'relationships_created': rels_count,
                        'message': f'Knowledge graph contains {nodes_count} entities and {rels_count} relationships'
                    }
                else:
                    logger.error(f"Failed to query Neo4j: {response.status_code}")
                    return {
                        'nodes_created': 0,
                        'relationships_created': 0,
                        'message': 'Failed to query Neo4j',
                        'error': f'HTTP {response.status_code}'
                    }
        except Exception as e:
            logger.error(f"Error querying Neo4j: {e}")
            return {
                'nodes_created': 0,
                'relationships_created': 0,
                'message': f'Error: {str(e)}'
            }
    
    async def _handle_report(self, config: Dict, inputs: Dict) -> Dict[str, Any]:
        """Handle report generation node"""
        logger.info("Executing report generation node")
        
        # Add delay to make status changes visible in UI
        await asyncio.sleep(2)
        
        summary = {
            'documents_uploaded': 0,
            'documents_processed': 0,
            'entities_extracted': 0,
            'relationships_created': 0
        }
        
        for input_data in inputs.values():
            if 'count' in input_data:
                summary['documents_uploaded'] += input_data['count']
            if 'processed_count' in input_data:
                summary['documents_processed'] += input_data['processed_count']
            if 'entities_extracted' in input_data:
                summary['entities_extracted'] += input_data['entities_extracted']
            if 'relationships_created' in input_data:
                summary['relationships_created'] += input_data['relationships_created']
        
        await asyncio.sleep(2)  # Simulate report generation
        
        return {
            'report_generated': True,
            'summary': summary,
            'message': 'Report generated successfully'
        }


# Initialize executor and persistence
executor = WorkflowExecutor()
persistence = WorkflowPersistence()


# ============ Workflow Templates ============

WORKFLOW_TEMPLATES = [
    {
        "id": "template_basic_ingestion",
        "title": "Basic Document Ingestion",
        "description": "Upload documents → AI processing → Knowledge graph → Report",
        "tags": ["ingestion", "basic", "recommended"],
        "nodes": [
            {"id": "node1", "type": "upload", "position": {"x": 100, "y": 200}, "data": {"label": "Upload Documents", "description": "Upload PDF files for processing", "type": "upload", "status": "pending"}},
            {"id": "node2", "type": "aiProcessing", "position": {"x": 400, "y": 200}, "data": {"label": "AI Processing", "description": "Extract entities & relationships using AI", "type": "aiProcessing", "status": "pending"}},
            {"id": "node3", "type": "knowledgeGraph", "position": {"x": 700, "y": 200}, "data": {"label": "Knowledge Graph", "description": "Build interactive graph visualization", "type": "knowledgeGraph", "status": "pending"}},
            {"id": "node4", "type": "report", "position": {"x": 1000, "y": 200}, "data": {"label": "Generate Report", "description": "Create comprehensive investigation report", "type": "report", "status": "pending"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "node1", "target": "node2", "type": "smoothstep", "animated": True},
            {"id": "e2-3", "source": "node2", "target": "node3", "type": "smoothstep", "animated": True},
            {"id": "e3-4", "source": "node3", "target": "node4", "type": "smoothstep", "animated": True}
        ]
    },
    {
        "id": "template_quick_analysis",
        "title": "Quick Document Analysis",
        "description": "Upload documents → AI processing → Report (skip graph)",
        "tags": ["analysis", "quick", "simple"],
        "nodes": [
            {"id": "node1", "type": "upload", "position": {"x": 200, "y": 250}, "data": {"label": "Upload Documents", "description": "Upload PDF files for processing", "type": "upload", "status": "pending"}},
            {"id": "node2", "type": "aiProcessing", "position": {"x": 500, "y": 250}, "data": {"label": "AI Processing", "description": "Extract entities & relationships using AI", "type": "aiProcessing", "status": "pending"}},
            {"id": "node3", "type": "report", "position": {"x": 800, "y": 250}, "data": {"label": "Generate Report", "description": "Create comprehensive investigation report", "type": "report", "status": "pending"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "node1", "target": "node2", "type": "smoothstep", "animated": True},
            {"id": "e2-3", "source": "node2", "target": "node3", "type": "smoothstep", "animated": True}
        ]
    },
    {
        "id": "template_graph_only",
        "title": "Knowledge Graph Builder",
        "description": "Upload documents → AI processing → Knowledge graph",
        "tags": ["graph", "visualization", "knowledge"],
        "nodes": [
            {"id": "node1", "type": "upload", "position": {"x": 200, "y": 250}, "data": {"label": "Upload Documents", "description": "Upload PDF files for processing", "type": "upload", "status": "pending"}},
            {"id": "node2", "type": "aiProcessing", "position": {"x": 500, "y": 250}, "data": {"label": "AI Processing", "description": "Extract entities & relationships using AI", "type": "aiProcessing", "status": "pending"}},
            {"id": "node3", "type": "knowledgeGraph", "position": {"x": 800, "y": 250}, "data": {"label": "Knowledge Graph", "description": "Build interactive graph visualization", "type": "knowledgeGraph", "status": "pending"}}
        ],
        "edges": [
            {"id": "e1-2", "source": "node1", "target": "node2", "type": "smoothstep", "animated": True},
            {"id": "e2-3", "source": "node2", "target": "node3", "type": "smoothstep", "animated": True}
        ]
    }
]


# ============ API Endpoints ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "workflow-builder",
        "version": "1.0.0"
    }


@app.post("/api/v1/workflows/execute")
async def execute_workflow(request: WorkflowExecuteRequest):
    """Execute a workflow"""
    try:
        logger.info(f"Executing workflow: {request.workflow_id}")
        
        nodes = [node.dict() for node in request.nodes]
        edges = [edge.dict() for edge in request.edges]
        
        result = await executor.execute_workflow(
            workflow_id=request.workflow_id,
            nodes=nodes,
            edges=edges
        )
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get workflow execution status"""
    try:
        execution = executor.get_execution_status(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {"success": True, "execution": execution}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/workflows/save")
async def save_workflow(request: WorkflowSaveRequest):
    """Save a workflow"""
    try:
        logger.info(f"Saving workflow: {request.title}")
        
        nodes = [node.dict() for node in request.nodes]
        edges = [edge.dict() for edge in request.edges]
        
        result = await persistence.save_workflow(
            title=request.title,
            description=request.description or "",
            nodes=nodes,
            edges=edges,
            tags=request.tags or [],
            is_template=request.is_template or False
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID"""
    try:
        result = await persistence.get_workflow(workflow_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/list")
async def list_workflows(is_template: Optional[bool] = None):
    """List all saved workflows"""
    try:
        result = await persistence.list_workflows(is_template=is_template)
        return result
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        result = await persistence.delete_workflow(workflow_id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/templates/list")
async def list_templates():
    """Get predefined workflow templates"""
    return {
        "success": True,
        "templates": WORKFLOW_TEMPLATES,
        "count": len(WORKFLOW_TEMPLATES)
    }


@app.post("/api/v1/workflows/templates/{template_id}/use")
async def use_template(template_id: str):
    """Load a template for use"""
    try:
        template = next((t for t in WORKFLOW_TEMPLATES if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "template": template
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
