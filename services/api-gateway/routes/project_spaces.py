"""
FastAPI routes for Project Spaces functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import structlog

from models.project_spaces import (
    ProjectSpace, ProjectSpaceCreate, ProjectSpaceUpdate, ProjectSpaceList,
    SpaceMember, SpaceMemberAdd, SpaceMemberUpdate, SpaceMemberList,
    SpaceDocument, SpaceDocumentAdd, SpaceDocumentUpdate, SpaceDocumentList,
    SpaceAnalytics, SpaceAnalyticsList, BulkDocumentMove, BulkOperationResult,
    SpaceSearchRequest
)
from services.project_spaces_service import ProjectSpacesService
# Mock auth for now - replace with your actual auth system
async def get_current_user():
    return {"user_id": "admin", "username": "admin"}

# Mock database for now - replace with your actual database
async def get_database():
    return None

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/spaces", tags=["Project Spaces"])


# Dependency to get project spaces service
async def get_spaces_service() -> ProjectSpacesService:
    db_pool = await get_database()
    return ProjectSpacesService(db_pool)


# Project Space Management Endpoints
@router.post("/", response_model=ProjectSpace)
async def create_project_space(
    space_data: ProjectSpaceCreate,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Create a new project space"""
    try:
        space = await spaces_service.create_space(space_data, user["user_id"])
        logger.info("Project space created", space_id=space.id, space_name=space.name, user_id=user["user_id"])
        return space
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create project space", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to create project space")


@router.get("/", response_model=ProjectSpaceList)
async def get_user_spaces(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get all project spaces accessible to the current user"""
    try:
        spaces, total = await spaces_service.get_user_spaces(user["user_id"], page, page_size)
        return ProjectSpaceList(
            spaces=spaces,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error("Failed to get user spaces", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve project spaces")


@router.get("/{space_id}", response_model=ProjectSpace)
async def get_project_space(
    space_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get a specific project space by ID"""
    try:
        space = await spaces_service.get_space_by_id(space_id, user["user_id"])
        if not space:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        return space
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get project space", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve project space")


@router.put("/{space_id}", response_model=ProjectSpace)
async def update_project_space(
    space_id: str,
    space_data: ProjectSpaceUpdate,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Update a project space"""
    try:
        space = await spaces_service.update_space(space_id, space_data, user["user_id"])
        logger.info("Project space updated", space_id=space_id, user_id=user["user_id"])
        return space
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update project space", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to update project space")


@router.delete("/{space_id}")
async def delete_project_space(
    space_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Delete a project space (owners only)"""
    try:
        success = await spaces_service.delete_space(space_id, user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        logger.info("Project space deleted", space_id=space_id, user_id=user["user_id"])
        return {"message": "Project space deleted successfully"}
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete project space", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to delete project space")


# Space Member Management Endpoints
@router.post("/{space_id}/members", response_model=SpaceMember)
async def add_space_member(
    space_id: str,
    member_data: SpaceMemberAdd,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Add a member to a project space"""
    try:
        member = await spaces_service.add_member(space_id, member_data, user["user_id"])
        logger.info("Space member added", space_id=space_id, member_user_id=member.user_id, added_by=user["user_id"])
        return member
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to add space member", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to add space member")


@router.get("/{space_id}/members", response_model=SpaceMemberList)
async def get_space_members(
    space_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get all members of a project space"""
    try:
        members = await spaces_service.get_space_members(space_id, user["user_id"])
        return SpaceMemberList(
            members=members,
            total=len(members)
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to get space members", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve space members")


@router.get("/{space_id}/members/{member_user_id}", response_model=SpaceMember)
async def get_space_member(
    space_id: str,
    member_user_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get a specific member of a project space"""
    try:
        member = await spaces_service.get_member(space_id, member_user_id)
        if not member:
            raise HTTPException(status_code=404, detail="Space member not found")
        
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get space member", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve space member")


# Space Document Management Endpoints
@router.post("/{space_id}/documents", response_model=SpaceDocument)
async def add_document_to_space(
    space_id: str,
    doc_data: SpaceDocumentAdd,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Add a document to a project space"""
    try:
        document = await spaces_service.add_document_to_space(space_id, doc_data, user["user_id"])
        logger.info("Document added to space", space_id=space_id, document_id=doc_data.document_id, user_id=user["user_id"])
        return document
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to add document to space", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to add document to space")


@router.get("/{space_id}/documents", response_model=SpaceDocumentList)
async def get_space_documents(
    space_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get all documents in a project space"""
    try:
        documents, total = await spaces_service.get_space_documents(space_id, user["user_id"], page, page_size)
        return SpaceDocumentList(
            documents=documents,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to get space documents", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve space documents")


@router.get("/{space_id}/documents/{document_id}", response_model=SpaceDocument)
async def get_space_document(
    space_id: str,
    document_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get a specific document in a space"""
    try:
        document = await spaces_service.get_space_document(space_id, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found in space")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get space document", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve space document")


@router.delete("/{space_id}/documents/{document_id}")
async def remove_document_from_space(
    space_id: str,
    document_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Remove a document from a project space"""
    try:
        # Check permissions first
        if not await spaces_service._check_space_permission(space_id, user["user_id"], "write"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Remove document from space
        async with spaces_service.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM space_documents WHERE space_id = $1 AND document_id = $2",
                space_id, document_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Document not found in space")
            
            # Clear space_id from document_status
            await conn.execute(
                "UPDATE document_status SET space_id = NULL WHERE document_id = $1",
                document_id
            )
        
        logger.info("Document removed from space", space_id=space_id, document_id=document_id, user_id=user["user_id"])
        return {"message": "Document removed from space successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove document from space", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to remove document from space")


# Analytics Endpoints
@router.get("/{space_id}/analytics", response_model=SpaceAnalytics)
async def get_space_analytics(
    space_id: str,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get analytics for a specific project space"""
    try:
        analytics = await spaces_service.get_space_analytics(space_id, user["user_id"])
        if not analytics:
            raise HTTPException(status_code=404, detail="Space analytics not found")
        
        return analytics
        
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Failed to get space analytics", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve space analytics")


@router.get("/analytics/overview", response_model=SpaceAnalyticsList)
async def get_all_spaces_analytics(
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Get analytics overview for all accessible spaces"""
    try:
        # Get user's spaces
        spaces, _ = await spaces_service.get_user_spaces(user["user_id"], page=1, page_size=100)
        
        # Get analytics for each space
        analytics_list = []
        for space in spaces:
            analytics = await spaces_service.get_space_analytics(space.id, user["user_id"])
            if analytics:
                analytics_list.append(analytics)
        
        return SpaceAnalyticsList(
            analytics=analytics_list,
            total_spaces=len(analytics_list)
        )
        
    except Exception as e:
        logger.error("Failed to get spaces analytics overview", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve spaces analytics")


# Bulk Operations
@router.post("/bulk/move-documents", response_model=BulkOperationResult)
async def bulk_move_documents(
    move_data: BulkDocumentMove,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Move multiple documents to a target space"""
    try:
        # Check write permission on target space
        if not await spaces_service._check_space_permission(move_data.target_space_id, user["user_id"], "write"):
            raise HTTPException(status_code=403, detail="Insufficient permissions for target space")
        
        success_count = 0
        error_count = 0
        errors = []
        operation_id = f"bulk_move_{user['user_id']}_{int(datetime.utcnow().timestamp())}"
        
        async with spaces_service.pool.acquire() as conn:
            for document_id in move_data.document_ids:
                try:
                    # Remove from current space
                    await conn.execute(
                        "DELETE FROM space_documents WHERE document_id = $1",
                        document_id
                    )
                    
                    # Add to target space
                    await conn.execute(
                        """
                        INSERT INTO space_documents (space_id, document_id, added_by, tags, metadata)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        move_data.target_space_id, document_id, user["user_id"],
                        [] if not move_data.preserve_tags else [],
                        {} if not move_data.preserve_metadata else {}
                    )
                    
                    # Update document_status
                    await conn.execute(
                        "UPDATE document_status SET space_id = $1 WHERE document_id = $2",
                        move_data.target_space_id, document_id
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append({
                        "document_id": document_id,
                        "error": str(e)
                    })
        
        logger.info("Bulk document move completed", 
                   operation_id=operation_id, 
                   success_count=success_count, 
                   error_count=error_count,
                   user_id=user["user_id"])
        
        return BulkOperationResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            operation_id=operation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to bulk move documents", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to move documents")


# Search within spaces
@router.post("/search", response_model=dict)
async def search_in_spaces(
    search_request: SpaceSearchRequest,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Search documents within specific project spaces"""
    try:
        # If space_id is provided, check access
        if search_request.space_id:
            if not await spaces_service._check_space_permission(search_request.space_id, user["user_id"], "read"):
                raise HTTPException(status_code=403, detail="Access denied to space")
        
        # This would integrate with your existing search service
        # For now, return a placeholder response
        return {
            "message": "Space-aware search functionality to be integrated with existing search service",
            "query": search_request.query,
            "space_id": search_request.space_id,
            "filters": search_request.filters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to search in spaces", error=str(e), user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to search in spaces")
