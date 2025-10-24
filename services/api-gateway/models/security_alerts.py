"""
Security Alerts and Notifications Models
Comprehensive security alerting and notification systems
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"

class AlertCategory(str, Enum):
    """Alert categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_BREACH = "data_breach"
    SYSTEM_SECURITY = "system_security"
    NETWORK_SECURITY = "network_security"
    COMPLIANCE = "compliance"
    MALWARE = "malware"
    INTRUSION = "intrusion"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POLICY_VIOLATION = "policy_violation"
    CONFIGURATION_CHANGE = "configuration_change"
    VULNERABILITY = "vulnerability"

class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    MOBILE_APP = "mobile_app"
    PAGER_DUTY = "pager_duty"

class AlertSource(str, Enum):
    """Alert sources"""
    SIEM = "siem"
    IDS_IPS = "ids_ips"
    FIREWALL = "firewall"
    ANTIVIRUS = "antivirus"
    DLP = "dlp"
    IAM = "iam"
    AUDIT_LOG = "audit_log"
    MANUAL = "manual"
    API = "api"
    SCHEDULED_SCAN = "scheduled_scan"
    REAL_TIME_MONITORING = "real_time_monitoring"

class EscalationLevel(str, Enum):
    """Escalation levels"""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"
    EXECUTIVE = "executive"

class SecurityAlert(BaseModel):
    """Security alert model"""
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: AlertCategory = Field(..., description="Alert category")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Alert status")
    source: AlertSource = Field(..., description="Alert source")
    source_id: Optional[str] = Field(None, description="Source-specific alert ID")
    user_id: Optional[str] = Field(None, description="User associated with alert")
    ip_address: Optional[str] = Field(None, description="IP address associated with alert")
    user_agent: Optional[str] = Field(None, description="User agent associated with alert")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    resource_name: Optional[str] = Field(None, description="Name of resource affected")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for related alerts")
    tags: List[str] = Field(default_factory=list, description="Alert tags")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")
    resolved_by: Optional[str] = Field(None, description="Who resolved the alert")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    escalation_level: EscalationLevel = Field(default=EscalationLevel.LEVEL_1, description="Current escalation level")
    escalation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Escalation history")
    false_positive: bool = Field(False, description="Whether alert is a false positive")
    suppression_until: Optional[datetime] = Field(None, description="Suppression end time")
    risk_score: float = Field(0.0, ge=0.0, le=10.0, description="Risk score (0-10)")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")

class AlertRule(BaseModel):
    """Alert rule model"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    condition: str = Field(..., description="Alert condition (SQL-like or expression)")
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: AlertCategory = Field(..., description="Alert category")
    source: AlertSource = Field(..., description="Alert source")
    enabled: bool = Field(True, description="Whether rule is enabled")
    threshold: Optional[float] = Field(None, description="Threshold value for numeric conditions")
    time_window: Optional[int] = Field(None, description="Time window in minutes")
    aggregation: Optional[str] = Field(None, description="Aggregation method (count, sum, avg, etc.)")
    notification_channels: List[NotificationChannel] = Field(default_factory=list, description="Notification channels")
    escalation_enabled: bool = Field(True, description="Whether escalation is enabled")
    escalation_delay_minutes: int = Field(30, description="Escalation delay in minutes")
    escalation_levels: List[EscalationLevel] = Field(default_factory=list, description="Escalation levels")
    suppression_enabled: bool = Field(True, description="Whether suppression is enabled")
    suppression_duration_minutes: int = Field(60, description="Suppression duration in minutes")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    created_by: str = Field(..., description="User who created the rule")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: Optional[datetime] = Field(None, description="When rule was last triggered")
    trigger_count: int = Field(0, description="Number of times rule has been triggered")

class NotificationTemplate(BaseModel):
    """Notification template model"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    channel: NotificationChannel = Field(..., description="Notification channel")
    subject_template: Optional[str] = Field(None, description="Subject template")
    body_template: str = Field(..., description="Body template")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    enabled: bool = Field(True, description="Whether template is enabled")
    created_by: str = Field(..., description="User who created the template")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationSubscription(BaseModel):
    """Notification subscription model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    user_phone: Optional[str] = Field(None, description="User phone number")
    channels: List[NotificationChannel] = Field(..., description="Subscribed channels")
    severity_filter: List[AlertSeverity] = Field(default_factory=list, description="Severity filter")
    category_filter: List[AlertCategory] = Field(default_factory=list, description="Category filter")
    source_filter: List[AlertSource] = Field(default_factory=list, description="Source filter")
    time_filter: Optional[Dict[str, Any]] = Field(None, description="Time-based filter")
    enabled: bool = Field(True, description="Whether subscription is enabled")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlertCorrelation(BaseModel):
    """Alert correlation model"""
    id: UUID = Field(default_factory=uuid4)
    correlation_id: str = Field(..., description="Correlation ID")
    alert_ids: List[str] = Field(..., description="List of correlated alert IDs")
    correlation_type: str = Field(..., description="Type of correlation")
    correlation_score: float = Field(0.0, ge=0.0, le=1.0, description="Correlation confidence score")
    pattern_description: str = Field(..., description="Description of correlation pattern")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlertSuppression(BaseModel):
    """Alert suppression model"""
    id: UUID = Field(default_factory=uuid4)
    rule_id: Optional[str] = Field(None, description="Rule ID to suppress")
    condition: str = Field(..., description="Suppression condition")
    reason: str = Field(..., description="Suppression reason")
    suppressed_by: str = Field(..., description="User who created suppression")
    suppressed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Suppression expiration")
    is_active: bool = Field(True, description="Whether suppression is active")

class AlertRequest(BaseModel):
    """Request to create an alert"""
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: AlertCategory = Field(..., description="Alert category")
    source: AlertSource = Field(..., description="Alert source")
    source_id: Optional[str] = Field(None, description="Source-specific alert ID")
    user_id: Optional[str] = Field(None, description="User associated with alert")
    ip_address: Optional[str] = Field(None, description="IP address associated with alert")
    user_agent: Optional[str] = Field(None, description="User agent associated with alert")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    resource_name: Optional[str] = Field(None, description="Name of resource affected")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for related alerts")
    tags: List[str] = Field(default_factory=list, description="Alert tags")
    risk_score: float = Field(0.0, ge=0.0, le=10.0, description="Risk score (0-10)")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")

class AlertUpdateRequest(BaseModel):
    """Request to update an alert"""
    status: Optional[AlertStatus] = Field(None, description="New alert status")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    false_positive: Optional[bool] = Field(None, description="Whether alert is false positive")
    suppression_until: Optional[datetime] = Field(None, description="Suppression end time")

class AlertRuleRequest(BaseModel):
    """Request to create/update an alert rule"""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    condition: str = Field(..., description="Alert condition")
    severity: AlertSeverity = Field(..., description="Alert severity")
    category: AlertCategory = Field(..., description="Alert category")
    source: AlertSource = Field(..., description="Alert source")
    enabled: bool = Field(True, description="Whether rule is enabled")
    threshold: Optional[float] = Field(None, description="Threshold value")
    time_window: Optional[int] = Field(None, description="Time window in minutes")
    aggregation: Optional[str] = Field(None, description="Aggregation method")
    notification_channels: List[NotificationChannel] = Field(default_factory=list, description="Notification channels")
    escalation_enabled: bool = Field(True, description="Whether escalation is enabled")
    escalation_delay_minutes: int = Field(30, description="Escalation delay in minutes")
    escalation_levels: List[EscalationLevel] = Field(default_factory=list, description="Escalation levels")
    suppression_enabled: bool = Field(True, description="Whether suppression is enabled")
    suppression_duration_minutes: int = Field(60, description="Suppression duration in minutes")
    tags: List[str] = Field(default_factory=list, description="Rule tags")

class AlertQuery(BaseModel):
    """Query parameters for alerts"""
    severity: Optional[AlertSeverity] = None
    category: Optional[AlertCategory] = None
    status: Optional[AlertStatus] = None
    source: Optional[AlertSource] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class AlertStats(BaseModel):
    """Alert statistics"""
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    false_positives: int
    alerts_by_severity: Dict[str, int]
    alerts_by_category: Dict[str, int]
    alerts_by_status: Dict[str, int]
    alerts_by_source: Dict[str, int]
    average_resolution_time_minutes: float
    escalation_rate: float
    false_positive_rate: float
    top_alert_sources: List[Dict[str, Any]]
    recent_trends: Dict[str, Any]

class NotificationRequest(BaseModel):
    """Request to send notification"""
    alert_id: str = Field(..., description="Alert ID")
    channels: List[NotificationChannel] = Field(..., description="Notification channels")
    recipients: List[str] = Field(..., description="Recipient list")
    custom_message: Optional[str] = Field(None, description="Custom message")
    priority: str = Field("normal", description="Notification priority")

class EscalationRequest(BaseModel):
    """Request to escalate alert"""
    alert_id: str = Field(..., description="Alert ID")
    escalation_level: EscalationLevel = Field(..., description="Target escalation level")
    reason: str = Field(..., description="Escalation reason")
    escalated_by: str = Field(..., description="User escalating the alert")

class SuppressionRequest(BaseModel):
    """Request to suppress alerts"""
    condition: str = Field(..., description="Suppression condition")
    reason: str = Field(..., description="Suppression reason")
    duration_minutes: int = Field(60, description="Suppression duration in minutes")
    suppressed_by: str = Field(..., description="User creating suppression")
