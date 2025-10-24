"""
Enhanced Audit Logging Models
Comprehensive security event tracking and monitoring system
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    MFA_SETUP = "mfa_setup"
    MFA_VERIFY = "mfa_verify"
    MFA_FAILURE = "mfa_failure"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Authorization Events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    
    # Data Access Events
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_MODIFY = "document_modify"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Configuration Events
    SECURITY_SETTINGS_CHANGE = "security_settings_change"
    POLICY_CREATED = "policy_created"
    POLICY_MODIFIED = "policy_modified"
    POLICY_DELETED = "policy_deleted"
    USER_CREATED = "user_created"
    USER_MODIFIED = "user_modified"
    USER_DELETED = "user_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_MODIFIED = "project_modified"
    PROJECT_DELETED = "project_deleted"
    
    # System Events
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    SERVICE_ERROR = "service_error"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    
    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALWARE_DETECTED = "malware_detected"
    
    # Compliance Events
    GDPR_DATA_REQUEST = "gdpr_data_request"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    HIPAA_ACCESS_LOG = "hipaa_access_log"
    SOX_AUDIT_EVENT = "sox_audit_event"
    COMPLIANCE_VIOLATION = "compliance_violation"

class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditCategory(str, Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    SECURITY = "security"
    COMPLIANCE = "compliance"

class AuditContext(BaseModel):
    """Additional context for audit events"""
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_code: Optional[int] = None
    processing_time_ms: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None

class AuditEvent(BaseModel):
    """Individual audit event"""
    id: UUID = Field(default_factory=uuid4)
    event_type: AuditEventType
    category: AuditCategory
    severity: AuditSeverity
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # User and session information
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    
    # Event details
    event_description: str
    event_data: Optional[Dict[str, Any]] = None
    context: Optional[AuditContext] = None
    
    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Project space context
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    
    # Compliance and security
    compliance_framework: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    requires_review: bool = False
    
    # System information
    service_name: str = "api-gateway"
    version: str = "1.0.0"
    environment: str = "production"
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    retention_days: Optional[int] = None
    archived: bool = False

class AuditLogQuery(BaseModel):
    """Query parameters for audit log search"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[AuditEventType]] = None
    categories: Optional[List[AuditCategory]] = None
    severities: Optional[List[AuditSeverity]] = None
    user_id: Optional[str] = None
    space_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    requires_review: Optional[bool] = None
    compliance_framework: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class AuditLogResponse(BaseModel):
    """Response for audit log queries"""
    events: List[AuditEvent]
    total_count: int
    has_more: bool
    query_params: AuditLogQuery

class AuditLogStats(BaseModel):
    """Audit log statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_user: Dict[str, int]
    events_by_space: Dict[str, int]
    high_risk_events: int
    events_requiring_review: int
    time_range: Dict[str, datetime]

class AuditLogRetentionPolicy(BaseModel):
    """Log retention policy configuration"""
    policy_name: str
    description: str
    event_types: List[AuditEventType]
    categories: List[AuditCategory]
    retention_days: int = Field(ge=1, le=3650)  # 1 day to 10 years
    archive_after_days: Optional[int] = Field(None, ge=1, le=3650)
    delete_after_days: Optional[int] = Field(None, ge=1, le=3650)
    compress_after_days: Optional[int] = Field(None, ge=1, le=3650)
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogAlert(BaseModel):
    """Audit log alert configuration"""
    alert_name: str
    description: str
    event_types: List[AuditEventType]
    conditions: Dict[str, Any]
    threshold: Optional[int] = None
    time_window_minutes: Optional[int] = None
    severity: AuditSeverity
    is_active: bool = True
    notification_channels: List[str] = Field(default_factory=list)
    escalation_rules: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogExport(BaseModel):
    """Audit log export configuration"""
    export_id: UUID = Field(default_factory=uuid4)
    query_params: AuditLogQuery
    export_format: str = Field(default="json", pattern="^(json|csv|excel|pdf)$")
    include_context: bool = True
    include_event_data: bool = True
    compression: bool = False
    password_protected: bool = False
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, processing, completed, failed
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    expires_at: Optional[datetime] = None
