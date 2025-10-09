"""
Knowledge Hub API Routes
Provides endpoints for knowledge graph exploration and visualization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from services.knowledge_hub_service import KnowledgeHubService
from services.elasticsearch_service import ElasticsearchService
from services.entity_chat_service import EntityChatService
from auth.jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-hub", tags=["knowledge-hub"])

# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class EntityChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    space_id: Optional[str] = None

# Dependency for Knowledge Hub service
def get_knowledge_hub_service() -> KnowledgeHubService:
    import os
    es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    es_service = ElasticsearchService(elasticsearch_url=es_url)
    return KnowledgeHubService(elasticsearch_service=es_service)

# Dependency for Entity Chat service
def get_entity_chat_service(kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)) -> EntityChatService:
    return EntityChatService(knowledge_hub_service=kb_service)

@router.get("/entity/{entity_name}")
async def get_entity_hub(
    entity_name: str,
    depth: int = Query(default=2, ge=1, le=3, description="Graph traversal depth (1-3 hops)"),
    limit: int = Query(default=100, ge=10, le=500, description="Maximum nodes to return"),
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get knowledge hub for a specific entity
    
    Returns all connected nodes and relationships up to the specified depth
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting knowledge hub for: {entity_name}")
        
        graph_data = await kb_service.get_knowledge_hub(
            entity_name=entity_name,
            depth=depth,
            limit=limit,
            space_id=space_id
        )
        
        return {
            "success": True,
            "entity_name": entity_name,
            "depth": depth,
            "graph": graph_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge hub for {entity_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve knowledge hub: {str(e)}")

@router.get("/search")
async def search_entities(
    query: str = Query(..., min_length=2, description="Search query"),
    types: Optional[str] = Query(default=None, description="Comma-separated entity types (Drug,Disease,etc.)"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Search for entities by name
    
    Returns list of matching entities with basic information
    """
    try:
        logger.info(f"User {current_user.get('email')} searching entities: {query}")
        
        # Parse entity types
        entity_types = None
        if types:
            entity_types = [t.strip() for t in types.split(",")]
        
        entities = await kb_service.search_entities(
            query=query,
            entity_types=entity_types,
            limit=limit,
            space_id=space_id
        )
        
        return {
            "success": True,
            "query": query,
            "types": entity_types,
            "count": len(entities),
            "entities": entities
        }
        
    except Exception as e:
        logger.error(f"Failed to search entities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search entities: {str(e)}")

@router.get("/entity/details/{entity_id}")
async def get_entity_details(
    entity_id: str,
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get detailed information about a specific entity
    
    Returns entity details with all connections
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting details for entity: {entity_id}")
        
        entity_details = await kb_service.get_entity_details(entity_id)
        
        if not entity_details:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
        return {
            "success": True,
            "entity": entity_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entity details: {str(e)}")

@router.get("/path")
async def find_shortest_path(
    source: str = Query(..., description="Source entity name"),
    target: str = Query(..., description="Target entity name"),
    max_depth: int = Query(default=5, ge=1, le=10, description="Maximum path length"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Find shortest path between two entities
    
    Returns the path with all intermediate nodes and relationships
    """
    try:
        logger.info(f"User {current_user.get('email')} finding path: {source} -> {target}")
        
        path_data = await kb_service.get_shortest_path(
            source_entity=source,
            target_entity=target,
            max_depth=max_depth
        )
        
        return {
            "success": True,
            "source": source,
            "target": target,
            "path": path_data
        }
        
    except Exception as e:
        logger.error(f"Failed to find shortest path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find path: {str(e)}")

@router.get("/full-graph")
async def get_full_graph(
    limit: int = Query(default=500, ge=50, le=1000, description="Maximum nodes to return"),
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get the entire knowledge graph
    
    Returns all nodes and relationships (up to limit)
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting full knowledge graph")
        
        graph_data = await kb_service.get_full_graph(limit=limit, space_id=space_id)
        
        # Return the graph data directly (nodes and edges at top level for frontend)
        return graph_data
        
    except Exception as e:
        logger.error(f"Failed to get full knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve full graph: {str(e)}")

@router.get("/statistics")
async def get_graph_statistics(
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get statistics about the knowledge graph
    
    Returns node counts, relationship counts, and other metrics
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting graph statistics")
        
        stats = await kb_service.get_graph_statistics(space_id=space_id)
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get graph statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

@router.get("/entity-types")
async def get_available_entity_types(
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get list of available entity types in the knowledge graph
    
    Returns list of entity types with counts
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting entity types")
        
        stats = await kb_service.get_graph_statistics(space_id=space_id)
        
        entity_types = [
            {"type": entity_type, "count": count}
            for entity_type, count in stats.get("node_counts", {}).items()
        ]
        
        return {
            "success": True,
            "entity_types": entity_types
        }
        
    except Exception as e:
        logger.error(f"Failed to get entity types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entity types: {str(e)}")

@router.get("/entity/{entity_name}/sources")
async def get_entity_sources(
    entity_name: str,
    space_id: Optional[str] = Query(default=None, description="Filter by space ID"),
    limit: int = Query(default=20, ge=5, le=100, description="Maximum documents to return"),
    current_user: dict = Depends(get_current_user),
    kb_service: KnowledgeHubService = Depends(get_knowledge_hub_service)
):
    """
    Get source documents that mention a specific entity
    
    Returns list of documents with highlighted snippets where the entity appears
    """
    try:
        logger.info(f"User {current_user.get('email')} requesting sources for entity: {entity_name}")
        
        result = await kb_service.get_entity_source_documents(
            entity_name=entity_name,
            space_id=space_id,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get entity sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entity sources: {str(e)}")


@router.post("/entity/{entity_name}/chat")
async def chat_with_entity(
    entity_name: str,
    chat_request: EntityChatRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: EntityChatService = Depends(get_entity_chat_service)
):
    """
    Chat with an entity using RAG-based Q&A
    
    Ask questions about the entity and get answers based on source documents
    with citations and references.
    
    **Request Body:**
    - message: The user's question
    - conversation_history: Previous conversation messages (optional)
    - space_id: Filter by space ID (optional)
    
    **Response:**
    - response: AI-generated answer with citations
    - sources: List of source documents referenced
    - entity_name: Name of the entity
    """
    try:
        logger.info(f"User {current_user.get('email')} chatting with entity: {entity_name}")
        
        # Convert Pydantic models to dicts for service
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in chat_request.conversation_history
        ] if chat_request.conversation_history else []
        
        result = await chat_service.chat_with_entity(
            entity_name=entity_name,
            message=chat_request.message,
            conversation_history=conversation_history,
            space_id=chat_request.space_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404 if "not found" in result.get("error", "").lower() else 500, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to chat with entity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")

