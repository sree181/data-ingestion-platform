"""
Project Spaces Database Service
Handles all database operations for Virtual Project Spaces
"""

import asyncpg
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import structlog
import uuid
import json

from models.project_spaces import (
    ProjectSpace, ProjectSpaceCreate, ProjectSpaceUpdate,
    SpaceMember, SpaceMemberAdd, SpaceMemberUpdate,
    SpaceDocument, SpaceDocumentAdd, SpaceDocumentUpdate,
    SpaceAnalytics, SpaceRole, SpacePermission, SecurityClassification
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
                # Use the user_id from JWT token directly
                # The JWT token contains the actual user_id from the authentication system
                admin_user_id = created_by
                
                # Create the space with security fields
                space_id = str(uuid.uuid4())
                settings_json = json.dumps(space_data.settings) if space_data.settings else "{}"
                compliance_frameworks_json = json.dumps(space_data.compliance_frameworks)
                ip_whitelist_json = json.dumps(space_data.ip_whitelist)
                allowed_domains_json = json.dumps(space_data.allowed_domains)
                
                await conn.execute(
                    """
                    INSERT INTO project_spaces (
                        id, name, description, color, icon, settings, created_by,
                        security_classification, encryption_enabled, requires_mfa,
                        compliance_frameworks, ip_whitelist, data_retention_days, allowed_domains
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """,
                    space_id, space_data.name, space_data.description, 
                    space_data.color, space_data.icon, settings_json, admin_user_id,
                    space_data.security_classification.value, space_data.encryption_enabled, space_data.requires_mfa,
                    compliance_frameworks_json, ip_whitelist_json, space_data.data_retention_days, allowed_domains_json
                )
                
                # Add creator as owner
                permissions_json = json.dumps(["read", "write", "admin", "delete"])
                await conn.execute(
                    """
                    INSERT INTO space_members (space_id, user_id, role, permissions, added_by)
                    VALUES ($1, $2, 'owner', $3, $4)
                    """,
                    space_id, admin_user_id, permissions_json, admin_user_id
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
            # Use the user_id from JWT token directly
            actual_user_id = user_id
                
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
                    space_id, actual_user_id
                )
                
                if not row:
                    return None
                
                return ProjectSpace(
                    id=str(row['id']),
                    name=row['name'],
                    description=row['description'],
                    color=row['color'],
                    icon=row['icon'],
                    settings=json.loads(row['settings']) if row['settings'] else {},
                    created_by=str(row['created_by']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    document_count=row['document_count'],
                    member_count=row['member_count'],
                    user_role=SpaceRole(row['role']),
                    user_permissions=[SpacePermission(p) for p in (json.loads(row['permissions']) if isinstance(row['permissions'], str) else (row['permissions'] if isinstance(row['permissions'], list) else []))],
                    # Security fields
                    security_classification=SecurityClassification(row['security_classification']),
                    encryption_enabled=row['encryption_enabled'],
                    requires_mfa=row['requires_mfa'],
                    compliance_frameworks=json.loads(row['compliance_frameworks']) if row['compliance_frameworks'] else [],
                    ip_whitelist=json.loads(row['ip_whitelist']) if row['ip_whitelist'] else [],
                    data_retention_days=row['data_retention_days'],
                    allowed_domains=json.loads(row['allowed_domains']) if row['allowed_domains'] else []
                )
                
        except Exception as e:
            logger.error("Failed to get project space", error=str(e), space_id=space_id)
            raise
    
    async def get_user_spaces(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[ProjectSpace], int]:
        """Get all project spaces accessible to a user"""
        try:
            offset = (page - 1) * page_size
            
            # Use the user_id from JWT token directly
            actual_user_id = user_id
            
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
                    actual_user_id, page_size, offset
                )
                
                # Get total count
                total_count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM project_spaces ps
                    JOIN space_members sm ON ps.id = sm.space_id
                    WHERE sm.user_id = $1
                    """,
                    actual_user_id
                )
                
                spaces = []
                for row in rows:
                    spaces.append(ProjectSpace(
                        id=str(row['id']),
                        name=row['name'],
                        description=row['description'],
                        color=row['color'],
                        icon=row['icon'],
                        settings=json.loads(row['settings']) if row['settings'] else {},
                        created_by=str(row['created_by']),
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        document_count=row['document_count'],
                        member_count=row['member_count'],
                        user_role=SpaceRole(row['role']),
                        user_permissions=[SpacePermission(p) for p in (json.loads(row['permissions']) if isinstance(row['permissions'], str) else (row['permissions'] if isinstance(row['permissions'], list) else []))],
                        # Security fields
                        security_classification=SecurityClassification(row['security_classification']),
                        encryption_enabled=row['encryption_enabled'],
                        requires_mfa=row['requires_mfa'],
                        compliance_frameworks=json.loads(row['compliance_frameworks']) if row['compliance_frameworks'] else [],
                        ip_whitelist=json.loads(row['ip_whitelist']) if row['ip_whitelist'] else [],
                        data_retention_days=row['data_retention_days'],
                        allowed_domains=json.loads(row['allowed_domains']) if row['allowed_domains'] else []
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
    
    async def delete_space(self, space_id: str, user_id: str, auth_level: str = "owner", 
                          request_info: Dict = None) -> bool:
        """Delete a project space with comprehensive security checks
        
        Security Features:
        - Multi-level authentication verification
        - Role-based access control (RBAC)
        - Comprehensive audit logging
        - Transaction safety with rollback
        - Input validation and sanitization
        - Rate limiting
        - Business logic validation
        - Real-time security monitoring
        
        Args:
            space_id: ID of the space to delete
            user_id: ID of the user requesting deletion
            auth_level: Required authentication level (owner, admin, member, viewer)
            request_info: Additional request information (IP, user agent, etc.)
        """
        try:
            # Import security services
            from security.rate_limiter import rate_limiter, check_rate_limit
            from security.business_logic_validator import business_validator
            from security.security_monitor import security_monitor, SecurityEventType, ThreatLevel
            
            # Input validation
            if not space_id or not user_id:
                raise ValueError("Space ID and User ID are required")
            
            if auth_level not in ["owner", "admin", "member", "viewer"]:
                raise ValueError(f"Invalid authentication level: {auth_level}")
            
            logger.info(f"Delete space request - space_id={space_id}, user_id={user_id}, auth_level={auth_level}")
            
            # Rate limiting check
            if request_info:
                is_limited, rate_info = check_rate_limit(
                    request_info.get("request"), "sensitive", "delete_space", user_id
                )
                if is_limited:
                    await security_monitor.log_event(
                        SecurityEventType.RATE_LIMIT_EXCEEDED,
                        user_id,
                        request_info.get("ip_address", "unknown"),
                        request_info.get("user_agent", "unknown"),
                        f"project_space:{space_id}",
                        "delete_space",
                        {"rate_info": rate_info},
                        ThreatLevel.MEDIUM
                    )
                    raise PermissionError(f"Rate limit exceeded: {rate_info.get('reason', 'Too many requests')}")
            
            async with self.pool.acquire() as conn:
                # Start transaction for atomicity
                async with conn.transaction():
                    # Step 1: Verify space exists and get details
                    space_details = await conn.fetchrow(
                        """
                        SELECT id, name, created_by, created_at, security_classification, 
                               encryption_enabled, requires_mfa, compliance_frameworks
                        FROM project_spaces WHERE id = $1
                        """,
                        space_id
                    )
                    
                    if not space_details:
                        logger.warning(f"Delete attempt on non-existent space - space_id={space_id}, user_id={user_id}")
                        await security_monitor.log_event(
                            SecurityEventType.SUSPICIOUS_ACTIVITY,
                            user_id,
                            request_info.get("ip_address", "unknown") if request_info else "unknown",
                            request_info.get("user_agent", "unknown") if request_info else "unknown",
                            f"project_space:{space_id}",
                            "delete_nonexistent_space",
                            {"space_id": space_id},
                            ThreatLevel.MEDIUM
                        )
                        raise ValueError("Project space not found")
                    
                    # Step 2: Get user's role and permissions in this space
                    user_membership = await conn.fetchrow(
                        """
                        SELECT role, permissions, created_at as membership_start
                        FROM space_members 
                        WHERE space_id = $1 AND user_id = $2
                        """,
                        space_id, user_id
                    )
                    
                    if not user_membership:
                        logger.warning(f"Unauthorized delete attempt - space_id={space_id}, user_id={user_id}")
                        await security_monitor.log_event(
                            SecurityEventType.PRIVILEGE_ESCALATION,
                            user_id,
                            request_info.get("ip_address", "unknown") if request_info else "unknown",
                            request_info.get("user_agent", "unknown") if request_info else "unknown",
                            f"project_space:{space_id}",
                            "unauthorized_delete_attempt",
                            {"space_id": space_id, "space_name": space_details['name']},
                            ThreatLevel.HIGH
                        )
                        raise PermissionError("You don't have access to this space")
                    
                    user_role = user_membership['role']
                    user_permissions = json.loads(user_membership['permissions']) if user_membership['permissions'] else []
                    
                    # Step 3: Business logic validation (with admin override)
                    # Check if user is an admin to enable override
                    is_admin = user_role in ['admin', 'owner']
                    admin_override = is_admin and auth_level in ['admin', 'owner']
                    
                    logger.info(f"Delete validation check - user_role={user_role}, auth_level={auth_level}, is_admin={is_admin}, admin_override={admin_override}")
                    
                    business_validation = await business_validator.validate_deletion_request(
                        user_id, space_id, auth_level, user_role, {
                            **space_details,
                            "membership_start": user_membership['membership_start']
                        },
                        admin_override=admin_override
                    )
                    
                    if admin_override:
                        logger.info(f"Admin override applied for deletion - space_id={space_id}, user_id={user_id}, auth_level={auth_level}")
                    
                    if not business_validation.valid:
                        logger.warning(f"Business logic validation failed - space_id={space_id}, user_id={user_id}, reason={business_validation.reason}")
                        await security_monitor.log_event(
                            SecurityEventType.SUSPICIOUS_ACTIVITY,
                            user_id,
                            request_info.get("ip_address", "unknown") if request_info else "unknown",
                            request_info.get("user_agent", "unknown") if request_info else "unknown",
                            f"project_space:{space_id}",
                            "business_logic_violation",
                            {"reason": business_validation.reason, "details": business_validation.details},
                            ThreatLevel.MEDIUM
                        )
                        raise ValueError(f"Business logic validation failed: {business_validation.reason}")
                    
                    # Step 4: Comprehensive authorization check
                    can_delete = False
                    deletion_reason = ""
                    
                    if auth_level == "owner":
                        if user_role == "owner":
                            can_delete = True
                            deletion_reason = "User is space owner"
                        else:
                            deletion_reason = f"Only space owners can delete with {auth_level} level (user role: {user_role})"
                    
                    elif auth_level == "admin":
                        if user_role in ["owner", "admin"]:
                            can_delete = True
                            deletion_reason = f"User has {user_role} role"
                        else:
                            deletion_reason = f"Only space owners and admins can delete with {auth_level} level (user role: {user_role})"
                    
                    elif auth_level == "member":
                        if user_role in ["owner", "admin", "member"]:
                            can_delete = True
                            deletion_reason = f"User has {user_role} role"
                        else:
                            deletion_reason = f"Only space owners, admins, and members can delete with {auth_level} level (user role: {user_role})"
                    
                    elif auth_level == "viewer":
                        if "delete" in user_permissions:
                            can_delete = True
                            deletion_reason = "User has delete permission"
                        else:
                            deletion_reason = f"User lacks delete permission (permissions: {user_permissions})"
                    
                    if not can_delete:
                        logger.warning(f"Delete authorization failed - space_id={space_id}, user_id={user_id}, reason={deletion_reason}")
                        await security_monitor.log_event(
                            SecurityEventType.PRIVILEGE_ESCALATION,
                            user_id,
                            request_info.get("ip_address", "unknown") if request_info else "unknown",
                            request_info.get("user_agent", "unknown") if request_info else "unknown",
                            f"project_space:{space_id}",
                            "insufficient_privileges",
                            {"reason": deletion_reason, "user_role": user_role, "auth_level": auth_level},
                            ThreatLevel.HIGH
                        )
                        raise PermissionError(deletion_reason)
                    
                    # Step 5: Log the deletion attempt
                    await conn.execute(
                        """
                        INSERT INTO audit_logs (
                            user_id, action, resource_type, resource_id, 
                            details, ip_address, user_agent, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        user_id,
                        "DELETE_SPACE",
                        "project_space",
                        space_id,
                        json.dumps({
                            "space_name": space_details['name'],
                            "auth_level_used": auth_level,
                            "user_role": user_role,
                            "deletion_reason": deletion_reason,
                            "space_created_by": space_details['created_by'],
                            "space_created_at": space_details['created_at'].isoformat() if space_details['created_at'] else None,
                            "security_classification": space_details['security_classification'],
                            "business_validation": business_validation.to_dict()
                        }),
                        request_info.get("ip_address", "127.0.0.1") if request_info else "127.0.0.1",
                        request_info.get("user_agent", "API-Client") if request_info else "API-Client",
                        datetime.utcnow()
                    )
                    
                    # Step 6: Perform the deletion (cascades to members and documents)
                    result = await conn.execute(
                        "DELETE FROM project_spaces WHERE id = $1",
                        space_id
                    )
                    
                    if result == "DELETE 1":
                        # Log successful deletion
                        await security_monitor.log_event(
                            SecurityEventType.BULK_OPERATION if auth_level == "bulk" else SecurityEventType.SUSPICIOUS_ACTIVITY,
                            user_id,
                            request_info.get("ip_address", "unknown") if request_info else "unknown",
                            request_info.get("user_agent", "unknown") if request_info else "unknown",
                            f"project_space:{space_id}",
                            "space_deleted",
                            {
                                "space_name": space_details['name'],
                                "auth_level": auth_level,
                                "user_role": user_role
                            },
                            ThreatLevel.LOW
                        )
                        
                        logger.info(f"Space deleted successfully - space_id={space_id}, user_id={user_id}, auth_level={auth_level}")
                        return True
                    else:
                        logger.error(f"Unexpected deletion result - space_id={space_id}, result={result}")
                        return False
                
        except PermissionError:
            # Re-raise permission errors as-is
            raise
        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to delete project space - space_id={space_id}, user_id={user_id}, error={str(e)}")
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
            # Use the user_id from JWT token directly
            actual_user_id = user_id
            
            # Check permissions
            if not await self._check_space_permission(space_id, actual_user_id, SpacePermission.READ):
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
                
                logger.info(f"DEBUG: Role check - space_id={space_id}, user_id={user_id}, found_role={role}, required_role={required_role.value}")
                
                result = role == required_role.value
                logger.info(f"DEBUG: Role check result: {result}")
                return result
                
        except Exception as e:
            print(f"DEBUG: Role check exception: {e}")
            logger.error(f"Role check failed: {e}")
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
                
                # If no user found, return None instead of creating one
                # User creation should be handled by the authentication system
                return None
                
        except Exception:
            return None

