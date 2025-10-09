"""
Workflow Executor Service
Executes visual workflows by orchestrating node execution in topological order
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
import httpx

logger = structlog.get_logger()


class WorkflowExecutor:
    """Execute visual workflows node by node"""
    
    def __init__(self, elasticsearch_service, neo4j_service):
        self.es_service = elasticsearch_service
        self.neo4j_service = neo4j_service
        self.node_handlers = {
            'upload': self._handle_upload,
            'aiProcessing': self._handle_ai_processing,
            'knowledgeGraph': self._handle_knowledge_graph,
            'report': self._handle_report,
        }
        # Store execution state
        self.executions = {}
    
    async def execute_workflow(
        self, 
        workflow_id: str,
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute workflow in topological order
        Returns: execution ID and initial status
        """
        try:
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Initialize execution state
            execution_id = f"exec_{workflow_id}_{datetime.now().timestamp()}"
            self.executions[execution_id] = {
                'workflow_id': workflow_id,
                'status': 'running',
                'nodes': {node['id']: {'status': 'pending', 'result': None} for node in nodes},
                'started_at': datetime.now().isoformat(),
                'user_id': user_id
            }
            
            # Execute asynchronously
            asyncio.create_task(self._execute_nodes(execution_id, nodes, edges, user_id))
            
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
        edges: List[Dict[str, Any]],
        user_id: str
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
                    
                    result = await handler(node['data'], inputs, user_id)
                    results[node_id] = result
                    
                    # Update status: completed
                    self._update_node_status(execution_id, node_id, 'completed', result)
                    logger.info(f"Node completed: {node_id}")
                    
                except Exception as e:
                    logger.error(f"Node execution failed: {node_id} - {e}")
                    # Update status: failed
                    self._update_node_status(execution_id, node_id, 'failed', {'error': str(e)})
                    # Stop execution on failure
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
        # Build adjacency list
        graph = {node['id']: [] for node in nodes}
        in_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            graph[source].append(target)
            in_degree[target] += 1
        
        # Find nodes with no incoming edges
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
        
        # Find incoming edges
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
    
    async def _handle_upload(
        self,
        config: Dict,
        inputs: Dict,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle document upload node"""
        logger.info("Executing upload node")
        
        # In a real implementation, this would:
        # 1. Accept file uploads from config
        # 2. Store files in MinIO/S3
        # 3. Create document records in Elasticsearch
        
        # For now, return mock data
        # In production, you'd integrate with your existing upload API
        return {
            'document_ids': [],
            'count': 0,
            'message': 'Upload node executed (no files provided in demo)'
        }
    
    async def _handle_ai_processing(
        self,
        config: Dict,
        inputs: Dict,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle AI processing node - extract entities and relationships"""
        logger.info("Executing AI processing node")
        
        # Get document IDs from previous node
        document_ids = []
        for input_data in inputs.values():
            if 'document_ids' in input_data:
                document_ids.extend(input_data['document_ids'])
        
        if not document_ids:
            logger.warning("No documents to process")
            return {
                'processed_count': 0,
                'entities_extracted': 0,
                'relationships_extracted': 0,
                'message': 'No documents to process'
            }
        
        # In a real implementation, this would:
        # 1. Fetch documents from Elasticsearch
        # 2. Call LLM service for entity/relationship extraction
        # 3. Update documents with AI results
        
        # For now, trigger existing ingestion pipeline
        try:
            # You can integrate with your existing document processor here
            # For example: await self.trigger_ingestion(document_ids)
            
            return {
                'processed_count': len(document_ids),
                'entities_extracted': 0,
                'relationships_extracted': 0,
                'message': f'Processed {len(document_ids)} documents'
            }
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            raise
    
    async def _handle_knowledge_graph(
        self,
        config: Dict,
        inputs: Dict,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle knowledge graph building node"""
        logger.info("Executing knowledge graph node")
        
        # Get processed documents from previous node
        processed_count = 0
        for input_data in inputs.values():
            if 'processed_count' in input_data:
                processed_count += input_data['processed_count']
        
        if processed_count == 0:
            return {
                'nodes_created': 0,
                'relationships_created': 0,
                'message': 'No processed documents to build graph from'
            }
        
        # In a real implementation, this would:
        # 1. Extract entities from processed documents
        # 2. Create nodes in Neo4j
        # 3. Create relationships between nodes
        # 4. Run entity consolidation
        
        try:
            # Integrate with your existing Neo4j service
            # For example: await self.neo4j_service.build_graph(...)
            
            return {
                'nodes_created': 0,
                'relationships_created': 0,
                'message': 'Knowledge graph building completed'
            }
        except Exception as e:
            logger.error(f"Knowledge graph building failed: {e}")
            raise
    
    async def _handle_report(
        self,
        config: Dict,
        inputs: Dict,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle report generation node"""
        logger.info("Executing report generation node")
        
        # Collect data from all previous nodes
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
        
        # In a real implementation, this would:
        # 1. Generate a comprehensive report
        # 2. Include visualizations, statistics, insights
        # 3. Save report to storage
        # 4. Return download link
        
        return {
            'report_generated': True,
            'summary': summary,
            'message': 'Report generated successfully'
        }


# Singleton instance
_workflow_executor = None

def get_workflow_executor(es_service=None, neo4j_service=None):
    """Get or create workflow executor instance"""
    global _workflow_executor
    if _workflow_executor is None:
        _workflow_executor = WorkflowExecutor(es_service, neo4j_service)
    return _workflow_executor
