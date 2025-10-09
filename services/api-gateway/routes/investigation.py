"""
Investigation Board API Routes (Neo4j-based)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from auth.jwt_auth import get_current_user
from services.investigation_neo4j_service import InvestigationNeo4jService
from schemas.investigation import (
    InvestigationBoardCreate,
    InvestigationBoardUpdate,
    PinnedEntityCreate,
    PinnedEntityUpdate,
    InvestigationFindingCreate,
    InvestigationFindingUpdate,
    EntityConnectionCreate
)

import os
from neo4j import GraphDatabase

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Boards"])
logger = logging.getLogger(__name__)

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Initialize Neo4j driver (reused across requests)
_neo4j_driver = None

def get_neo4j_driver():
    """Get or create Neo4j driver"""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _neo4j_driver


# Dependency to get investigation service
async def get_investigation_service() -> InvestigationNeo4jService:
    """Get Investigation service with Neo4j driver"""
    driver = get_neo4j_driver()
    return InvestigationNeo4jService(driver)


# ============ Board Endpoints ============

@router.get("/boards")
async def list_boards(
    space_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    List all investigation boards for the current user
    
    Optional filter by space_id
    """
    try:
        user_id = current_user["user_id"]
        boards = await service.get_boards(user_id, space_id)
        return {"success": True, "boards": boards}
    except Exception as e:
        logger.error(f"Failed to list boards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list boards: {str(e)}"
        )


@router.post("/boards", status_code=status.HTTP_201_CREATED)
async def create_board(
    board_data: InvestigationBoardCreate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Create a new investigation board
    """
    try:
        user_id = current_user["user_id"]
        board = await service.create_board(
            user_id=user_id,
            title=board_data.title,
            description=board_data.description,
            space_id=board_data.space_id,
            status=board_data.status or "active"
        )
        return {"success": True, "board": board}
    except Exception as e:
        logger.error(f"Failed to create board: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create board: {str(e)}"
        )


@router.get("/boards/{board_id}")
async def get_board(
    board_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Get detailed information about a board including all entities, findings, and connections
    """
    try:
        user_id = current_user["user_id"]
        board_data = await service.get_board_by_id(board_id, user_id)
        
        if not board_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found or access denied"
            )
        
        return {"success": True, "board": board_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get board: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get board: {str(e)}"
        )


@router.put("/boards/{board_id}")
async def update_board(
    board_id: str,
    board_data: InvestigationBoardUpdate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Update board details (title, description, status)
    """
    try:
        user_id = current_user["user_id"]
        updated_board = await service.update_board(
            board_id=board_id,
            user_id=user_id,
            title=board_data.title,
            description=board_data.description,
            status=board_data.status
        )
        
        if not updated_board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found or access denied"
            )
        
        return {"success": True, "board": updated_board}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update board: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update board: {str(e)}"
        )


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Delete a board and all its contents
    """
    try:
        user_id = current_user["user_id"]
        deleted = await service.delete_board(board_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found or access denied"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete board: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete board: {str(e)}"
        )


# ============ AI Suggestions Endpoints ============

@router.get("/boards/{board_id}/suggestions")
async def get_board_suggestions(
    board_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Get AI-powered entity suggestions for the board
    Suggests related entities from Knowledge Hub that aren't yet pinned
    """
    try:
        user_id = current_user["user_id"]
        suggestions = await service.get_entity_suggestions(board_id, user_id, limit)
        return {"success": True, **suggestions}
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/boards/{board_id}/missing-connections")
async def get_missing_connections(
    board_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Detect missing connections between entities already on the board
    Analyzes Knowledge Hub relationships to suggest connections
    """
    try:
        user_id = current_user["user_id"]
        missing = await service.get_missing_connections(board_id, user_id)
        return {"success": True, **missing}
    except Exception as e:
        logger.error(f"Failed to detect missing connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect missing connections: {str(e)}"
        )


@router.post("/boards/{board_id}/suggestions/batch-add")
async def batch_add_suggestions(
    board_id: str,
    entity_names: List[str] = [],
    connections: List[dict] = [],
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Bulk add suggested entities and connections to the board
    """
    try:
        user_id = current_user["user_id"]
        result = await service.bulk_add_suggestions(
            board_id=board_id,
            user_id=user_id,
            entity_suggestions=entity_names,
            connection_suggestions=connections
        )
        return result
    except Exception as e:
        logger.error(f"Failed to batch add suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch add suggestions: {str(e)}"
        )


@router.get("/pin/{pin_id}/suggestions")
async def get_entity_specific_suggestions(
    pin_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Get AI-powered entity suggestions specific to a single pinned entity
    Finds related entities and connections for this specific entity
    """
    try:
        # Get the pinned entity
        entity = await service.get_pinned_entity(pin_id)
        
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pinned entity not found"
            )
        
        # Get suggestions specific to this entity
        suggestions = await service.get_entity_specific_suggestions(
            pin_id=pin_id,
            entity_name=entity.get('entity_name'),
            limit=limit
        )
        
        return {"success": True, **suggestions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity-specific suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity-specific suggestions: {str(e)}"
        )


# ============ Pinned Entity Endpoints ============

@router.post("/pin", status_code=status.HTTP_201_CREATED)
async def pin_entity(
    entity_data: PinnedEntityCreate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Pin an entity to a board
    """
    try:
        pinned_entity = await service.pin_entity(
            board_id=str(entity_data.board_id),
            entity_name=entity_data.entity_name,
            entity_type=entity_data.entity_type,
            pin_reason=entity_data.pin_reason,
            position_x=entity_data.position_x,
            position_y=entity_data.position_y,
            knowledge_hub_entity_id=entity_data.knowledge_hub_entity_id
        )
        return {"success": True, "entity": pinned_entity}
    except Exception as e:
        logger.error(f"Failed to pin entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pin entity: {str(e)}"
        )


@router.delete("/pin/{pin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_entity(
    pin_id: str,
    board_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Remove a pinned entity from a board
    """
    try:
        deleted = await service.unpin_entity(pin_id, board_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pinned entity not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unpin entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unpin entity: {str(e)}"
        )


@router.put("/pin/{pin_id}")
async def update_pinned_entity(
    pin_id: str,
    entity_data: PinnedEntityUpdate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Update a pinned entity (position, reason)
    """
    try:
        updated_entity = await service.update_pinned_entity(
            pin_id=pin_id,
            board_id=str(entity_data.board_id),
            position_x=entity_data.position_x,
            position_y=entity_data.position_y,
            pin_reason=entity_data.pin_reason
        )
        
        if not updated_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pinned entity not found"
            )
        
        return {"success": True, "entity": updated_entity}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pinned entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pinned entity: {str(e)}"
        )


# ============ Finding Endpoints ============

@router.post("/findings", status_code=status.HTTP_201_CREATED)
async def add_finding(
    finding_data: InvestigationFindingCreate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Add a finding/note to a pinned entity
    """
    try:
        user_id = current_user["user_id"]
        finding = await service.add_finding(
            pin_id=str(finding_data.pinned_entity_id),
            user_id=user_id,
            finding_type=finding_data.finding_type,
            content=finding_data.content,
            tags=finding_data.tags
        )
        return {"success": True, "finding": finding}
    except Exception as e:
        logger.error(f"Failed to add finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add finding: {str(e)}"
        )


@router.put("/findings/{finding_id}")
async def update_finding(
    finding_id: str,
    finding_data: InvestigationFindingUpdate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Update a finding
    """
    try:
        user_id = current_user["user_id"]
        updated_finding = await service.update_finding(
            finding_id=finding_id,
            user_id=user_id,
            finding_type=finding_data.finding_type,
            content=finding_data.content,
            tags=finding_data.tags
        )
        
        if not updated_finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found or access denied"
            )
        
        return {"success": True, "finding": updated_finding}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update finding: {str(e)}"
        )


@router.delete("/findings/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    finding_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Delete a finding
    """
    try:
        user_id = current_user["user_id"]
        deleted = await service.delete_finding(finding_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found or access denied"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete finding: {str(e)}"
        )


# ============ Connection Endpoints ============

@router.post("/connections", status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: EntityConnectionCreate,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Create a connection between two entities on a board
    """
    try:
        connection = await service.create_connection(
            board_id=str(connection_data.board_id),
            source_entity_id=str(connection_data.source_entity_id),
            target_entity_id=str(connection_data.target_entity_id),
            connection_type=connection_data.connection_type,
            notes=connection_data.notes
        )
        return {"success": True, "connection": connection}
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}"
        )


@router.delete("/connections", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    board_id: str,
    source_entity_id: str,
    target_entity_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Delete a connection between entities
    """
    try:
        deleted = await service.delete_connection(board_id, source_entity_id, target_entity_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connection: {str(e)}"
        )


# ============ Knowledge Hub Integration ============

@router.get("/pin/{pin_id}/documents")
async def get_pinned_entity_documents(
    pin_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Get source documents for a pinned entity from Knowledge Hub
    """
    try:
        # Get the pinned entity to retrieve the knowledge_hub_entity_id
        entity = await service.get_pinned_entity(pin_id)
        
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pinned entity not found"
            )
        
        # Fetch documents from Elasticsearch via Knowledge Hub service
        # Search by entity name regardless of whether it has a knowledge_hub_entity_id
        from services.elasticsearch_service import ElasticsearchService
        from services.knowledge_hub_service import KnowledgeHubService
        import os
        
        es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        es_service = ElasticsearchService(elasticsearch_url=es_url)
        
        # Ensure Elasticsearch is connected
        if not es_service.client:
            await es_service.connect()
        
        kb_service = KnowledgeHubService(elasticsearch_service=es_service)
        
        entity_name = entity.get('entity_name')
        result = await kb_service.get_entity_source_documents(entity_name, limit=10)
        
        return {
            "success": True, 
            "documents": result.get("documents", []),
            "total": len(result.get("documents", []))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity documents: {str(e)}"
        )


# ============ Export Endpoint ============

@router.get("/boards/{board_id}/export")
async def export_board(
    board_id: str,
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Export a board with all its data as JSON
    """
    try:
        user_id = current_user["user_id"]
        export_data = await service.export_board(board_id, user_id)
        
        if not export_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found or access denied"
            )
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export board: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export board: {str(e)}"
        )


# ============ AI Report Generation ============

@router.post("/boards/{board_id}/generate-report")
async def generate_investigation_report(
    board_id: str,
    format: str = "markdown",
    template: str = "comprehensive",
    current_user: dict = Depends(get_current_user),
    service: InvestigationNeo4jService = Depends(get_investigation_service)
):
    """
    Generate an AI-powered investigation report
    
    Args:
        board_id: ID of the investigation board
        format: Output format (markdown, pdf, word, json)
        template: Report template (comprehensive, executive, technical, legal)
    
    Returns:
        Generated report with metadata
    """
    try:
        user_id = current_user["user_id"]
        
        # Get board data
        board = await service.get_board_by_id(board_id, user_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found or access denied"
            )
        
        # Get source documents for all entities
        from services.elasticsearch_service import ElasticsearchService
        from services.knowledge_hub_service import KnowledgeHubService
        from services.report_generator_service import ReportGeneratorService
        
        es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        es_service = ElasticsearchService(elasticsearch_url=es_url)
        
        if not es_service.client:
            await es_service.connect()
        
        kb_service = KnowledgeHubService(elasticsearch_service=es_service)
        
        # Collect all entity names
        entity_names = []
        for ew in board.get("pinned_entities", []):
            if ew.get("entity"):
                entity_names.append(ew["entity"]["entity_name"])
        
        # Get documents for all entities
        all_documents = []
        for entity_name in entity_names:
            result = await kb_service.get_entity_source_documents(entity_name, limit=20)
            all_documents.extend(result.get("documents", []))
        
        # Deduplicate documents by document_id
        seen_docs = set()
        unique_documents = []
        for doc in all_documents:
            doc_id = doc.get("document_id")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_documents.append(doc)
        
        # Generate report
        report_service = ReportGeneratorService()
        report_result = await report_service.generate_report(
            board_data=board,
            documents=unique_documents,
            format=format,
            template=template
        )
        
        return report_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
