"""
Pydantic models for Project Spaces functionality
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class SpaceRole(str, Enum):
    """Project space member roles"""
    OWNER = "owner"
    ADMIN = "admin" 
    MEMBER = "member"
    VIEWER = "viewer"


class SpacePermission(str, Enum):
    """Project space permissions"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DELETE = "delete"


# Security Classification Enum
class SecurityClassification(str, Enum):
    """Security classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

# Project Space Models
class ProjectSpaceCreate(BaseModel):
    """Create project space request"""
    name: str = Field(..., min_length=1, max_length=255, description="Project space name")
    description: Optional[str] = Field(None, max_length=1000, description="Project space description")
    color: Optional[str] = Field("#1976d2", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field("folder", description="Icon name for UI")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Space-specific settings")
    
    # Security fields
    security_classification: SecurityClassification = Field(SecurityClassification.INTERNAL, description="Security classification level")
    encryption_enabled: bool = Field(True, description="Enable encryption at rest")
    requires_mfa: bool = Field(False, description="Require multi-factor authentication")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Compliance frameworks (SOX, GDPR, HIPAA, etc.)")
    ip_whitelist: List[str] = Field(default_factory=list, description="Allowed IP addresses/ranges")
    data_retention_days: int = Field(2555, ge=1, le=3650, description="Data retention period in days")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed email domains for invitations")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Project space name cannot be empty')
        return v.strip()
    
    @validator('compliance_frameworks')
    def validate_compliance_frameworks(cls, v):
        valid_frameworks = ['sox', 'gdpr', 'hipaa', 'iso27001', 'nist', 'pci_dss']
        for framework in v:
            if framework.lower() not in valid_frameworks:
                raise ValueError(f'Invalid compliance framework: {framework}')
        return [f.lower() for f in v]
    
    @validator('ip_whitelist')
    def validate_ip_whitelist(cls, v):
        # Basic IP validation - in production, use a proper IP validation library
        import re
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$')
        for ip in v:
            if not ip_pattern.match(ip.strip()):
                raise ValueError(f'Invalid IP address format: {ip}')
        return [ip.strip() for ip in v if ip.strip()]


class ProjectSpaceUpdate(BaseModel):
    """Update project space request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project space name")
    description: Optional[str] = Field(None, max_length=1000, description="Project space description")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, description="Icon name for UI")
    settings: Optional[Dict[str, Any]] = Field(None, description="Space-specific settings")


class ProjectSpace(BaseModel):
    """Project space response"""
    id: str = Field(..., description="Project space ID")
    name: str = Field(..., description="Project space name")
    description: Optional[str] = Field(None, description="Project space description")
    color: str = Field(..., description="Hex color code")
    icon: str = Field(..., description="Icon name")
    settings: Dict[str, Any] = Field(..., description="Space-specific settings")
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    document_count: Optional[int] = Field(None, description="Number of documents in space")
    member_count: Optional[int] = Field(None, description="Number of space members")
    user_role: Optional[SpaceRole] = Field(None, description="Current user's role in this space")
    user_permissions: Optional[List[SpacePermission]] = Field(None, description="Current user's permissions")
    
    # Security fields
    security_classification: SecurityClassification = Field(..., description="Security classification level")
    encryption_enabled: bool = Field(..., description="Encryption at rest enabled")
    requires_mfa: bool = Field(..., description="Multi-factor authentication required")
    compliance_frameworks: List[str] = Field(..., description="Compliance frameworks")
    ip_whitelist: List[str] = Field(..., description="Allowed IP addresses/ranges")
    data_retention_days: int = Field(..., description="Data retention period in days")
    allowed_domains: List[str] = Field(..., description="Allowed email domains for invitations")


class ProjectSpaceList(BaseModel):
    """List of project spaces response"""
    spaces: List[ProjectSpace] = Field(..., description="List of project spaces")
    total: int = Field(..., description="Total number of spaces")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


# Space Member Models
class SpaceMemberAdd(BaseModel):
    """Add member to space request"""
    user_id: Optional[str] = Field(None, description="User ID to add")
    username: Optional[str] = Field(None, description="Username to add (alternative to user_id)")
    email: Optional[str] = Field(None, description="Email to add (alternative to user_id)")
    role: SpaceRole = Field(SpaceRole.MEMBER, description="Member role")
    permissions: List[SpacePermission] = Field(default_factory=lambda: [SpacePermission.READ], description="Member permissions")
    
    @validator('permissions')
    def validate_permissions(cls, v, values):
        role = values.get('role')
        if role == SpaceRole.OWNER and SpacePermission.DELETE not in v:
            v.append(SpacePermission.DELETE)
        if role in [SpaceRole.OWNER, SpaceRole.ADMIN] and SpacePermission.ADMIN not in v:
            v.append(SpacePermission.ADMIN)
        return v


class SpaceMemberUpdate(BaseModel):
    """Update space member request"""
    role: Optional[SpaceRole] = Field(None, description="New member role")
    permissions: Optional[List[SpacePermission]] = Field(None, description="New member permissions")


class SpaceMember(BaseModel):
    """Space member response"""
    id: str = Field(..., description="Membership ID")
    space_id: str = Field(..., description="Project space ID")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    role: SpaceRole = Field(..., description="Member role")
    permissions: List[SpacePermission] = Field(..., description="Member permissions")
    added_by: str = Field(..., description="User ID who added this member")
    created_at: datetime = Field(..., description="Membership creation timestamp")


class SpaceMemberList(BaseModel):
    """List of space members response"""
    members: List[SpaceMember] = Field(..., description="List of space members")
    total: int = Field(..., description="Total number of members")


# Space Document Models
class SpaceDocumentAdd(BaseModel):
    """Add document to space request"""
    document_id: str = Field(..., description="Document ID to add to space")
    tags: Optional[List[str]] = Field(default_factory=list, description="Space-specific tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Space-specific metadata")


class SpaceDocumentUpdate(BaseModel):
    """Update document in space request"""
    tags: Optional[List[str]] = Field(None, description="Updated space-specific tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated space-specific metadata")


class SpaceDocument(BaseModel):
    """Space document response"""
    id: str = Field(..., description="Space document ID")
    space_id: str = Field(..., description="Project space ID")
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    status: str = Field(..., description="Document processing status")
    progress: float = Field(..., description="Processing progress")
    tags: List[str] = Field(..., description="Space-specific tags")
    metadata: Dict[str, Any] = Field(..., description="Space-specific metadata")
    added_by: str = Field(..., description="User ID who added document to space")
    created_at: datetime = Field(..., description="Addition timestamp")
    document_created_at: Optional[datetime] = Field(None, description="Original document creation timestamp")


class SpaceDocumentList(BaseModel):
    """List of space documents response"""
    documents: List[SpaceDocument] = Field(..., description="List of space documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


# Space Analytics Models
class SpaceAnalytics(BaseModel):
    """Space analytics response"""
    space_id: str = Field(..., description="Project space ID")
    space_name: str = Field(..., description="Project space name")
    total_documents: int = Field(..., description="Total documents in space")
    processed_documents: int = Field(..., description="Successfully processed documents")
    processing_documents: int = Field(..., description="Currently processing documents")
    failed_documents: int = Field(..., description="Failed processing documents")
    avg_progress: float = Field(..., description="Average processing progress")
    last_document_added: Optional[datetime] = Field(None, description="Last document addition timestamp")
    member_count: int = Field(..., description="Number of space members")


class SpaceAnalyticsList(BaseModel):
    """List of space analytics response"""
    analytics: List[SpaceAnalytics] = Field(..., description="List of space analytics")
    total_spaces: int = Field(..., description="Total number of spaces")


# Search Models
class SpaceSearchFilter(BaseModel):
    """Search filter for space-specific searches"""
    space_id: Optional[str] = Field(None, description="Filter by specific space")
    tags: Optional[List[str]] = Field(None, description="Filter by space-specific tags")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")


class SpaceSearchRequest(BaseModel):
    """Space-aware search request"""
    query: str = Field(..., description="Search query")
    space_id: Optional[str] = Field(None, description="Limit search to specific space")
    filters: Optional[SpaceSearchFilter] = Field(None, description="Additional filters")
    size: int = Field(10, ge=1, le=100, description="Number of results")
    from_: int = Field(0, alias="from", ge=0, description="Starting index")


# Error Models
class SpaceErrorResponse(BaseModel):
    """Space-specific error response"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    space_id: Optional[str] = Field(None, description="Related space ID")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Bulk Operations
class BulkDocumentMove(BaseModel):
    """Bulk move documents between spaces"""
    document_ids: List[str] = Field(..., min_items=1, description="List of document IDs to move")
    target_space_id: str = Field(..., description="Target space ID")
    preserve_tags: bool = Field(True, description="Whether to preserve existing tags")
    preserve_metadata: bool = Field(True, description="Whether to preserve existing metadata")


class BulkOperationResult(BaseModel):
    """Result of bulk operation"""
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(..., description="List of errors encountered")
    operation_id: str = Field(..., description="Operation tracking ID")

