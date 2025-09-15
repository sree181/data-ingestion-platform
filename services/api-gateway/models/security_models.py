"""
Enhanced Security Models for Project Spaces
Implements RBAC, Project Isolation, and Stakeholder Management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Dict, List, Optional
from pydantic import BaseModel

Base = declarative_base()

# Enums for Security Framework
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"          # Platform-wide access
    ORG_ADMIN = "org_admin"              # Organization-wide access
    PROJECT_OWNER = "project_owner"       # Full project control
    PROJECT_ADMIN = "project_admin"       # Project administration
    PROJECT_MANAGER = "project_manager"   # Project management
    SENIOR_ANALYST = "senior_analyst"     # Advanced analysis + limited admin
    ANALYST = "analyst"                   # Standard analysis access
    REVIEWER = "reviewer"                 # Read + comment access
    VIEWER = "viewer"                     # Read-only access
    GUEST = "guest"                       # Limited temporary access

class PermissionType(enum.Enum):
    # Document Permissions
    CREATE_DOCUMENT = "create_document"
    READ_DOCUMENT = "read_document"
    UPDATE_DOCUMENT = "update_document"
    DELETE_DOCUMENT = "delete_document"
    DOWNLOAD_DOCUMENT = "download_document"
    
    # Project Permissions
    CREATE_PROJECT = "create_project"
    READ_PROJECT = "read_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    ARCHIVE_PROJECT = "archive_project"
    
    # User Management
    INVITE_USER = "invite_user"
    REMOVE_USER = "remove_user"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    
    # Advanced Features
    EXPORT_DATA = "export_data"
    BULK_OPERATIONS = "bulk_operations"
    API_ACCESS = "api_access"
    SYSTEM_SETTINGS = "system_settings"

class SecurityClassification(enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class AuditAction(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    PROJECT_ACCESS = "project_access"
    ROLE_CHANGE = "role_change"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    DATA_EXPORT = "data_export"
    SECURITY_VIOLATION = "security_violation"

# Database Models
class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    subscription_tier = Column(String(50), default="enterprise")
    security_settings = Column(JSON, default={})
    compliance_requirements = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="organization")
    users = relationship("User", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Security Fields
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Profile
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    security_clearance = Column(Enum(SecurityClassification), default=SecurityClassification.INTERNAL)
    
    # Organizational
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    project_memberships = relationship("ProjectMember", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_code = Column(String(20), unique=True, nullable=False)
    
    # Security Settings
    security_classification = Column(Enum(SecurityClassification), default=SecurityClassification.INTERNAL)
    encryption_enabled = Column(Boolean, default=True)
    data_retention_days = Column(Integer, default=2555)  # 7 years default
    requires_mfa = Column(Boolean, default=False)
    ip_whitelist = Column(JSON, default=[])
    allowed_domains = Column(JSON, default=[])
    
    # Compliance
    compliance_frameworks = Column(JSON, default=[])  # SOX, GDPR, HIPAA, etc.
    data_location_restrictions = Column(JSON, default=[])
    
    # Organizational
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User")
    members = relationship("ProjectMember", back_populates="project")
    documents = relationship("Document", back_populates="project")
    audit_logs = relationship("AuditLog", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    
    # Access Control
    permissions = Column(JSON, default=[])  # Additional specific permissions
    access_restrictions = Column(JSON, default={})  # Time-based, IP-based restrictions
    
    # Delegation
    delegated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    delegation_expires_at = Column(DateTime, nullable=True)
    
    # Audit
    invited_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, nullable=True)
    last_access = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    delegator = relationship("User", foreign_keys=[delegated_by])
    
    # Indexes
    __table_args__ = (
        Index('ix_project_user', 'project_id', 'user_id', unique=True),
    )

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Security
    security_classification = Column(Enum(SecurityClassification), default=SecurityClassification.INTERNAL)
    encryption_key_id = Column(String(255), nullable=True)
    checksum = Column(String(64), nullable=False)
    
    # Access Control
    requires_approval = Column(Boolean, default=False)
    download_restrictions = Column(JSON, default={})
    
    # Organizational
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Event Details
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=True)  # document, project, user
    resource_id = Column(String(100), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Event Data
    details = Column(JSON, default={})
    risk_score = Column(Integer, default=0)  # 0-100 risk assessment
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    project = relationship("Project", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_project_timestamp', 'project_id', 'timestamp'),
        Index('ix_audit_action_timestamp', 'action', 'timestamp'),
    )

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    
    # Session Details
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)
    terminated_by = Column(String(50), nullable=True)  # user, admin, timeout, security
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# Pydantic Models for API
class ProjectSecurityConfig(BaseModel):
    classification: SecurityClassification
    encryption_enabled: bool = True
    requires_mfa: bool = False
    ip_whitelist: List[str] = []
    allowed_domains: List[str] = []
    compliance_frameworks: List[str] = []
    data_retention_days: int = 2555

class UserPermissions(BaseModel):
    role: UserRole
    permissions: List[PermissionType]
    access_restrictions: Dict = {}
    delegation_info: Optional[Dict] = None

class AuditLogEntry(BaseModel):
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict = {}
    risk_score: int = 0

class SecurityMetrics(BaseModel):
    total_users: int
    active_sessions: int
    failed_logins_24h: int
    high_risk_events: int
    compliance_score: float
    mfa_adoption_rate: float
