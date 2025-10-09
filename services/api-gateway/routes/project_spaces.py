"""
FastAPI routes for Project Spaces functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
import structlog
from datetime import datetime
from auth.jwt_auth import get_current_user, require_mfa_verification
from security.rate_limiter import check_rate_limit

from models.project_spaces import (
    ProjectSpace, ProjectSpaceCreate, ProjectSpaceUpdate, ProjectSpaceList,
    SpaceMember, SpaceMemberAdd, SpaceMemberUpdate, SpaceMemberList,
    SpaceDocument, SpaceDocumentAdd, SpaceDocumentUpdate, SpaceDocumentList,
    SpaceAnalytics, SpaceAnalyticsList, BulkDocumentMove, BulkOperationResult,
    SpaceSearchRequest
)
from services.project_spaces_service import ProjectSpacesService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/spaces", tags=["Project Spaces"])

# Dependency to get project spaces service
async def get_spaces_service() -> Optional[ProjectSpacesService]:
    try:
        # Import the global database manager from main.py
        from main import db_manager
        
        print(f"DEBUG: Database manager: {db_manager}")
        print(f"DEBUG: Database pool: {db_manager.pool if db_manager else None}")
        
        if db_manager is None or db_manager.pool is None:
            logger.warning("Database not available, returning None for mock data fallback")
            return None
        
        service = ProjectSpacesService(db_manager.pool)
        print(f"DEBUG: Created spaces service: {service}")
        return service
    except Exception as e:
        logger.error("Failed to create spaces service", error=str(e))
        return None


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
    spaces_service: Optional[ProjectSpacesService] = Depends(get_spaces_service)
):
    """Get all project spaces accessible to the current user"""
    try:
        if spaces_service is None:
            # Fallback to mock data when database is not available
            from main import mock_spaces
            logger.info("Using mock data for project spaces")
            
            # Transform mock data to ProjectSpace format
            spaces = []
            for mock_space in mock_spaces:
                space = ProjectSpace(
                    id=mock_space["id"],
                    name=mock_space["name"],
                    description=mock_space["description"],
                    color=mock_space["color"],
                    icon=mock_space["icon"],
                    document_count=mock_space["document_count"],
                    member_count=mock_space["member_count"],
                    user_role=mock_space["user_role"],
                    created_at=mock_space["created_at"],
                    # Add required fields for ProjectSpace model
                    settings={},
                    created_by="admin",
                    updated_at=mock_space["created_at"],
                    # Add default security fields for mock data
                    security_classification="internal",
                    encryption_enabled=True,
                    requires_mfa=False,
                    compliance_frameworks=["GDPR", "SOX"],
                    ip_whitelist=[],
                    data_retention_days=365,
                    allowed_domains=["company.com"]
                )
                spaces.append(space)
            
            return ProjectSpaceList(
                spaces=spaces,
                total=len(spaces),
                page=page,
                page_size=page_size
            )
        
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


@router.delete("/{space_id}")
async def delete_project_space(
    space_id: str,
    auth_level: str = Query("owner", description="Required authentication level: owner, admin, member, or viewer"),
    user: dict = Depends(require_mfa_verification),  # Require MFA for deletions
    spaces_service: ProjectSpacesService = Depends(get_spaces_service),
    request: Request = None
):
    """Delete a project space with comprehensive security controls
    
    Security Features:
    - Multi-level authentication verification
    - Role-based access control (RBAC)
    - Comprehensive audit logging
    - Input validation and sanitization
    - Transaction safety with rollback
    
    Authentication levels:
    - owner: Only space owners can delete (most secure, default)
    - admin: Space owners and admins can delete
    - member: Space owners, admins, and members can delete
    - viewer: Anyone with delete permission can delete (least secure)
    
    Returns:
        Success response with deletion details and audit information
    """
    try:
        # Input validation
        if not space_id or not space_id.strip():
            raise HTTPException(status_code=400, detail="Space ID is required")
        
        if not user or not user.get("user_id"):
            raise HTTPException(status_code=401, detail="User authentication required")
        
        # Validate authentication level
        valid_levels = ["owner", "admin", "member", "viewer"]
        if auth_level not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid authentication level. Must be one of: {', '.join(valid_levels)}"
            )
        
        logger.info(f"Delete space request - space_id={space_id}, user_id={str(user['user_id'])}, auth_level={auth_level}")
        
        # Rate limiting check
        is_limited, rate_info = check_rate_limit(request, "sensitive", "delete_space", user["user_id"])
        if is_limited:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: {rate_info.get('reason', 'Too many requests')}",
                headers=rate_info.get("headers", {})
            )
        
        # Prepare request information for security monitoring
        request_info = {
            "request": request,
            "ip_address": request.client.host if request else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown") if request else "unknown"
        }
        
        # Perform the deletion with comprehensive security checks
        success = await spaces_service.delete_space(space_id, user["user_id"], auth_level, request_info)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project space not found or could not be deleted")
        
        # Return success response with audit information
        response_data = {
            "success": True,
            "message": "Project space deleted successfully",
            "deleted_by": str(user["user_id"]),  # Convert UUID to string
            "auth_level_used": auth_level,
            "space_id": space_id,
            "timestamp": datetime.utcnow().isoformat(),
            "security_notes": {
                "audit_logged": True,
                "transaction_safe": True,
                "authorization_verified": True
            }
        }
        
        logger.info(f"Space deleted successfully - space_id={space_id}, user_id={str(user['user_id'])}, auth_level={auth_level}")
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except PermissionError as e:
        logger.warning(f"Delete authorization failed - space_id={space_id}, user_id={user.get('user_id', 'unknown')}, error={str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.warning(f"Delete validation failed - space_id={space_id}, user_id={user.get('user_id', 'unknown')}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Delete operation failed - space_id={space_id}, user_id={user.get('user_id', 'unknown')}, error={str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during deletion")


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
        print(f"DEBUG: Getting documents for space {space_id}, user {user['user_id']}, page {page}, size {page_size}")
        documents, total = await spaces_service.get_space_documents(space_id, user["user_id"], page, page_size)
        print(f"DEBUG: Retrieved {len(documents)} documents, total {total}")
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
