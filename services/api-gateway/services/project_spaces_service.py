"""
Project Spaces Database Service
Handles all database operations for Virtual Project Spaces
"""

import asyncpg
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import structlog
import uuid

from models.project_spaces import (
    ProjectSpace, ProjectSpaceCreate, ProjectSpaceUpdate,
    SpaceMember, SpaceMemberAdd, SpaceMemberUpdate,
    SpaceDocument, SpaceDocumentAdd, SpaceDocumentUpdate,
    SpaceAnalytics, SpaceRole, SpacePermission
)

logger = structlog.get_logger(__name__)


class ProjectSpacesService:
    """Service for managing project spaces in the database"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
    
    # Project Space Management
    async def create_space(self, space_data: ProjectSpaceCreate, created_by: str) -> ProjectSpace:
        """Create a new project space"""
        try:
            async with self.pool.acquire() as conn:
                # Create the space
                space_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO project_spaces (id, name, description, color, icon, settings, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    space_id, space_data.name, space_data.description, 
                    space_data.color, space_data.icon, space_data.settings, created_by
                )
                
                # Add creator as owner
                await conn.execute(
                    """
                    INSERT INTO space_members (space_id, user_id, role, permissions, added_by)
                    VALUES ($1, $2, 'owner', $3, $4)
                    """,
                    space_id, created_by, ["read", "write", "admin", "delete"], created_by
                )
                
                # Fetch and return the created space
                return await self.get_space_by_id(space_id, created_by)
                
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Project space '{space_data.name}' already exists")
        except Exception as e:
            logger.error("Failed to create project space", error=str(e), space_name=space_data.name)
            raise
    
    async def get_space_by_id(self, space_id: str, user_id: str) -> Optional[ProjectSpace]:
        """Get a project space by ID (with user permissions)"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT ps.*, sm.role, sm.permissions,
                           (SELECT COUNT(*) FROM space_documents sd WHERE sd.space_id = ps.id) as document_count,
                           (SELECT COUNT(*) FROM space_members sm2 WHERE sm2.space_id = ps.id) as member_count
                    FROM project_spaces ps
                    JOIN space_members sm ON ps.id = sm.space_id
                    WHERE ps.id = $1 AND sm.user_id = $2
                    """,
                    space_id, user_id
                )
                
                if not row:
                    return None
                
                return ProjectSpace(
                    id=str(row['id']),
                    name=row['name'],
                    description=row['description'],
                    color=row['color'],
                    icon=row['icon'],
                    settings=row['settings'] or {},
                    created_by=str(row['created_by']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    document_count=row['document_count'],
                    member_count=row['member_count'],
                    user_role=SpaceRole(row['role']),
                    user_permissions=[SpacePermission(p) for p in row['permissions']]
                )
                
        except Exception as e:
            logger.error("Failed to get project space", error=str(e), space_id=space_id)
            raise
    
    async def get_user_spaces(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[ProjectSpace], int]:
        """Get all project spaces accessible to a user"""
        try:
            offset = (page - 1) * page_size
            
            async with self.pool.acquire() as conn:
                # Get spaces with pagination
                rows = await conn.fetch(
                    """
                    SELECT ps.*, sm.role, sm.permissions,
                           (SELECT COUNT(*) FROM space_documents sd WHERE sd.space_id = ps.id) as document_count,
                           (SELECT COUNT(*) FROM space_members sm2 WHERE sm2.space_id = ps.id) as member_count
                    FROM project_spaces ps
                    JOIN space_members sm ON ps.id = sm.space_id
                    WHERE sm.user_id = $1
                    ORDER BY ps.updated_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    user_id, page_size, offset
                )
                
                # Get total count
                total_count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM project_spaces ps
                    JOIN space_members sm ON ps.id = sm.space_id
                    WHERE sm.user_id = $1
                    """,
                    user_id
                )
                
                spaces = []
                for row in rows:
                    spaces.append(ProjectSpace(
                        id=str(row['id']),
                        name=row['name'],
                        description=row['description'],
                        color=row['color'],
                        icon=row['icon'],
                        settings=row['settings'] or {},
                        created_by=str(row['created_by']),
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        document_count=row['document_count'],
                        member_count=row['member_count'],
                        user_role=SpaceRole(row['role']),
                        user_permissions=[SpacePermission(p) for p in row['permissions']]
                    ))
                
                return spaces, total_count
                
        except Exception as e:
            logger.error("Failed to get user spaces", error=str(e), user_id=user_id)
            raise
    
    async def update_space(self, space_id: str, space_data: ProjectSpaceUpdate, user_id: str) -> ProjectSpace:
        """Update a project space"""
        try:
            # Check permissions
            if not await self._check_space_permission(space_id, user_id, SpacePermission.ADMIN):
                raise PermissionError("Insufficient permissions to update space")
            
            # Build update query dynamically
            update_fields = []
            params = []
            param_count = 1
            
            if space_data.name is not None:
                update_fields.append(f"name = ${param_count}")
                params.append(space_data.name)
                param_count += 1
            
            if space_data.description is not None:
                update_fields.append(f"description = ${param_count}")
                params.append(space_data.description)
                param_count += 1
            
            if space_data.color is not None:
                update_fields.append(f"color = ${param_count}")
                params.append(space_data.color)
                param_count += 1
            
            if space_data.icon is not None:
                update_fields.append(f"icon = ${param_count}")
                params.append(space_data.icon)
                param_count += 1
            
            if space_data.settings is not None:
                update_fields.append(f"settings = ${param_count}")
                params.append(space_data.settings)
                param_count += 1
            
            if not update_fields:
                return await self.get_space_by_id(space_id, user_id)
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([space_id])
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE project_spaces 
                    SET {', '.join(update_fields)}
                    WHERE id = ${param_count}
                    """,
                    *params
                )
                
                return await self.get_space_by_id(space_id, user_id)
                
        except Exception as e:
            logger.error("Failed to update project space", error=str(e), space_id=space_id)
            raise
    
    async def delete_space(self, space_id: str, user_id: str) -> bool:
        """Delete a project space (only owners can delete)"""
        try:
            # Check if user is owner
            if not await self._check_space_role(space_id, user_id, SpaceRole.OWNER):
                raise PermissionError("Only space owners can delete spaces")
            
            async with self.pool.acquire() as conn:
                # Delete space (cascades to members and documents)
                result = await conn.execute(
                    "DELETE FROM project_spaces WHERE id = $1",
                    space_id
                )
                
                return result == "DELETE 1"
                
        except Exception as e:
            logger.error("Failed to delete project space", error=str(e), space_id=space_id)
            raise
    
    # Space Member Management
    async def add_member(self, space_id: str, member_data: SpaceMemberAdd, added_by: str) -> SpaceMember:
        """Add a member to a project space"""
        try:
            # Check permissions
            if not await self._check_space_permission(space_id, added_by, SpacePermission.ADMIN):
                raise PermissionError("Insufficient permissions to add members")
            
            # Find user by provided identifier
            user_id = await self._find_user_id(member_data.user_id, member_data.username, member_data.email)
            if not user_id:
                raise ValueError("User not found")
            
            async with self.pool.acquire() as conn:
                # Add member
                await conn.execute(
                    """
                    INSERT INTO space_members (space_id, user_id, role, permissions, added_by)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    space_id, user_id, member_data.role.value, 
                    [p.value for p in member_data.permissions], added_by
                )
                
                # Return member info
                return await self.get_member(space_id, user_id)
                
        except asyncpg.UniqueViolationError:
            raise ValueError("User is already a member of this space")
        except Exception as e:
            logger.error("Failed to add space member", error=str(e), space_id=space_id)
            raise
    
    async def get_space_members(self, space_id: str, user_id: str) -> List[SpaceMember]:
        """Get all members of a project space"""
        try:
            # Check if user has access to the space
            if not await self._check_space_permission(space_id, user_id, SpacePermission.READ):
                raise PermissionError("Access denied to space")
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT sm.*, u.username, u.email
                    FROM space_members sm
                    JOIN users u ON sm.user_id = u.id
                    WHERE sm.space_id = $1
                    ORDER BY sm.role, u.username
                    """,
                    space_id
                )
                
                members = []
                for row in rows:
                    members.append(SpaceMember(
                        id=str(row['id']),
                        space_id=str(row['space_id']),
                        user_id=str(row['user_id']),
                        username=row['username'],
                        email=row['email'],
                        role=SpaceRole(row['role']),
                        permissions=[SpacePermission(p) for p in row['permissions']],
                        added_by=str(row['added_by']),
                        created_at=row['created_at']
                    ))
                
                return members
                
        except Exception as e:
            logger.error("Failed to get space members", error=str(e), space_id=space_id)
            raise
    
    async def get_member(self, space_id: str, member_user_id: str) -> Optional[SpaceMember]:
        """Get a specific member of a project space"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT sm.*, u.username, u.email
                    FROM space_members sm
                    JOIN users u ON sm.user_id = u.id
                    WHERE sm.space_id = $1 AND sm.user_id = $2
                    """,
                    space_id, member_user_id
                )
                
                if not row:
                    return None
                
                return SpaceMember(
                    id=str(row['id']),
                    space_id=str(row['space_id']),
                    user_id=str(row['user_id']),
                    username=row['username'],
                    email=row['email'],
                    role=SpaceRole(row['role']),
                    permissions=[SpacePermission(p) for p in row['permissions']],
                    added_by=str(row['added_by']),
                    created_at=row['created_at']
                )
                
        except Exception as e:
            logger.error("Failed to get space member", error=str(e), space_id=space_id)
            raise
    
    # Space Document Management
    async def add_document_to_space(self, space_id: str, doc_data: SpaceDocumentAdd, added_by: str) -> SpaceDocument:
        """Add a document to a project space"""
        try:
            # Check permissions
            if not await self._check_space_permission(space_id, added_by, SpacePermission.WRITE):
                raise PermissionError("Insufficient permissions to add documents")
            
            async with self.pool.acquire() as conn:
                # Add document to space
                await conn.execute(
                    """
                    INSERT INTO space_documents (space_id, document_id, added_by, tags, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    space_id, doc_data.document_id, added_by, doc_data.tags, doc_data.metadata
                )
                
                # Update document_status table with space_id
                await conn.execute(
                    """
                    UPDATE document_status 
                    SET space_id = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = $2
                    """,
                    space_id, doc_data.document_id
                )
                
                # Return document info
                return await self.get_space_document(space_id, doc_data.document_id)
                
        except asyncpg.UniqueViolationError:
            raise ValueError("Document is already in this space")
        except Exception as e:
            logger.error("Failed to add document to space", error=str(e), space_id=space_id)
            raise
    
    async def get_space_documents(self, space_id: str, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[SpaceDocument], int]:
        """Get all documents in a project space"""
        try:
            # Check permissions
            if not await self._check_space_permission(space_id, user_id, SpacePermission.READ):
                raise PermissionError("Access denied to space")
            
            offset = (page - 1) * page_size
            
            async with self.pool.acquire() as conn:
                # Get documents with pagination
                rows = await conn.fetch(
                    """
                    SELECT sd.*, ds.filename, ds.status, ds.progress, ds.created_at as document_created_at
                    FROM space_documents sd
                    JOIN document_status ds ON sd.document_id = ds.document_id
                    WHERE sd.space_id = $1
                    ORDER BY sd.created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    space_id, page_size, offset
                )
                
                # Get total count
                total_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM space_documents WHERE space_id = $1",
                    space_id
                )
                
                documents = []
                for row in rows:
                    documents.append(SpaceDocument(
                        id=str(row['id']),
                        space_id=str(row['space_id']),
                        document_id=row['document_id'],
                        filename=row['filename'],
                        status=row['status'],
                        progress=row['progress'],
                        tags=row['tags'] or [],
                        metadata=row['metadata'] or {},
                        added_by=str(row['added_by']),
                        created_at=row['created_at'],
                        document_created_at=row['document_created_at']
                    ))
                
                return documents, total_count
                
        except Exception as e:
            logger.error("Failed to get space documents", error=str(e), space_id=space_id)
            raise
    
    async def get_space_document(self, space_id: str, document_id: str) -> Optional[SpaceDocument]:
        """Get a specific document in a space"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT sd.*, ds.filename, ds.status, ds.progress, ds.created_at as document_created_at
                    FROM space_documents sd
                    JOIN document_status ds ON sd.document_id = ds.document_id
                    WHERE sd.space_id = $1 AND sd.document_id = $2
                    """,
                    space_id, document_id
                )
                
                if not row:
                    return None
                
                return SpaceDocument(
                    id=str(row['id']),
                    space_id=str(row['space_id']),
                    document_id=row['document_id'],
                    filename=row['filename'],
                    status=row['status'],
                    progress=row['progress'],
                    tags=row['tags'] or [],
                    metadata=row['metadata'] or {},
                    added_by=str(row['added_by']),
                    created_at=row['created_at'],
                    document_created_at=row['document_created_at']
                )
                
        except Exception as e:
            logger.error("Failed to get space document", error=str(e), space_id=space_id)
            raise
    
    # Analytics
    async def get_space_analytics(self, space_id: str, user_id: str) -> Optional[SpaceAnalytics]:
        """Get analytics for a specific space"""
        try:
            # Check permissions
            if not await self._check_space_permission(space_id, user_id, SpacePermission.READ):
                raise PermissionError("Access denied to space")
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM space_analytics WHERE space_id = $1",
                    space_id
                )
                
                if not row:
                    return None
                
                return SpaceAnalytics(
                    space_id=str(row['space_id']),
                    space_name=row['space_name'],
                    total_documents=row['total_documents'] or 0,
                    processed_documents=row['processed_documents'] or 0,
                    processing_documents=row['processing_documents'] or 0,
                    failed_documents=row['failed_documents'] or 0,
                    avg_progress=row['avg_progress'] or 0.0,
                    last_document_added=row['last_document_added'],
                    member_count=row['member_count'] or 0
                )
                
        except Exception as e:
            logger.error("Failed to get space analytics", error=str(e), space_id=space_id)
            raise
    
    # Helper Methods
    async def _check_space_permission(self, space_id: str, user_id: str, required_permission: SpacePermission) -> bool:
        """Check if user has required permission for a space"""
        try:
            async with self.pool.acquire() as conn:
                permissions = await conn.fetchval(
                    """
                    SELECT permissions
                    FROM space_members
                    WHERE space_id = $1 AND user_id = $2
                    """,
                    space_id, user_id
                )
                
                return permissions and required_permission.value in permissions
                
        except Exception:
            return False
    
    async def _check_space_role(self, space_id: str, user_id: str, required_role: SpaceRole) -> bool:
        """Check if user has required role for a space"""
        try:
            async with self.pool.acquire() as conn:
                role = await conn.fetchval(
                    """
                    SELECT role
                    FROM space_members
                    WHERE space_id = $1 AND user_id = $2
                    """,
                    space_id, user_id
                )
                
                return role == required_role.value
                
        except Exception:
            return False
    
    async def _find_user_id(self, user_id: Optional[str], username: Optional[str], email: Optional[str]) -> Optional[str]:
        """Find user ID by various identifiers"""
        try:
            if user_id:
                return user_id
            
            async with self.pool.acquire() as conn:
                if username:
                    result = await conn.fetchval("SELECT id FROM users WHERE username = $1", username)
                    if result:
                        return str(result)
                
                if email:
                    result = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
                    if result:
                        return str(result)
                
                return None
                
        except Exception:
            return None

