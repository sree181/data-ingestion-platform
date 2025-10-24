"""
Data Classification Management Models
Comprehensive data classification and handling policies
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class DataClassificationLevel(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class ClassificationMethod(str, Enum):
    """Methods used for classification"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    RULE_BASED = "rule_based"
    AI_POWERED = "ai_powered"
    POLICY_BASED = "policy_based"

class DataSensitivity(str, Enum):
    """Data sensitivity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DataCategory(str, Enum):
    """Data categories for classification"""
    PERSONAL_DATA = "personal_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    TRADE_SECRETS = "trade_secrets"
    LEGAL_DOCUMENTS = "legal_documents"
    RESEARCH_DATA = "research_data"
    OPERATIONAL_DATA = "operational_data"
    TECHNICAL_DATA = "technical_data"
    MARKETING_DATA = "marketing_data"

class ComplianceRequirement(str, Enum):
    """Compliance requirements for data handling"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    FERPA = "ferpa"
    CCPA = "ccpa"
    ISO_27001 = "iso_27001"
    NIST = "nist"

class DataHandlingAction(str, Enum):
    """Actions that can be taken on classified data"""
    ENCRYPT = "encrypt"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOG = "audit_log"
    RETENTION_POLICY = "retention_policy"
    BACKUP_REQUIRED = "backup_required"
    SHARING_RESTRICTED = "sharing_restricted"
    EXPORT_RESTRICTED = "export_restricted"
    ANONYMIZE = "anonymize"
    PSEUDONYMIZE = "pseudonymize"
    DELETE_AFTER_USE = "delete_after_use"

class DataClassificationRule(BaseModel):
    """Rule for automatic data classification"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    pattern: str = Field(..., description="Pattern to match (regex, keyword, etc.)")
    pattern_type: str = Field(..., description="Type of pattern (regex, keyword, nlp, etc.)")
    classification_level: DataClassificationLevel = Field(..., description="Classification level to apply")
    data_category: DataCategory = Field(..., description="Data category")
    sensitivity: DataSensitivity = Field(..., description="Data sensitivity level")
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence for rule application")
    handling_actions: List[DataHandlingAction] = Field(..., description="Actions to take when rule matches")
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list, description="Compliance requirements")
    is_active: bool = Field(True, description="Whether rule is active")
    priority: int = Field(100, description="Rule priority (lower = higher priority)")
    created_by: str = Field(..., description="User who created the rule")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DataClassificationPolicy(BaseModel):
    """Data classification policy"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    classification_level: DataClassificationLevel = Field(..., description="Classification level")
    data_category: DataCategory = Field(..., description="Data category")
    sensitivity: DataSensitivity = Field(..., description="Data sensitivity level")
    handling_actions: List[DataHandlingAction] = Field(..., description="Required handling actions")
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list, description="Compliance requirements")
    retention_period_days: Optional[int] = Field(None, description="Data retention period in days")
    access_controls: Dict[str, Any] = Field(default_factory=dict, description="Access control requirements")
    sharing_restrictions: Dict[str, Any] = Field(default_factory=dict, description="Data sharing restrictions")
    encryption_required: bool = Field(True, description="Whether encryption is required")
    audit_required: bool = Field(True, description="Whether audit logging is required")
    backup_required: bool = Field(True, description="Whether backup is required")
    is_active: bool = Field(True, description="Whether policy is active")
    created_by: str = Field(..., description="User who created the policy")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DataClassificationResult(BaseModel):
    """Result of data classification"""
    document_id: str = Field(..., description="Document ID")
    classification_level: DataClassificationLevel = Field(..., description="Assigned classification level")
    data_category: DataCategory = Field(..., description="Data category")
    sensitivity: DataSensitivity = Field(..., description="Data sensitivity level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    classification_method: ClassificationMethod = Field(..., description="Method used for classification")
    applied_rules: List[str] = Field(default_factory=list, description="Rules that were applied")
    handling_actions: List[DataHandlingAction] = Field(..., description="Required handling actions")
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list, description="Compliance requirements")
    classification_reasoning: str = Field(..., description="Reasoning for classification")
    classified_by: str = Field(..., description="User or system that performed classification")
    classified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_review: bool = Field(False, description="Whether classification requires manual review")
    review_notes: Optional[str] = Field(None, description="Notes from manual review")

class DataClassificationRequest(BaseModel):
    """Request for data classification"""
    document_id: str = Field(..., description="Document ID to classify")
    content: str = Field(..., description="Document content to analyze")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    force_reclassification: bool = Field(False, description="Force reclassification even if already classified")
    classification_method: Optional[ClassificationMethod] = Field(None, description="Specific method to use")
    user_id: str = Field(..., description="User requesting classification")

class BulkClassificationRequest(BaseModel):
    """Request for bulk data classification"""
    document_ids: List[str] = Field(..., description="List of document IDs to classify")
    classification_method: Optional[ClassificationMethod] = Field(None, description="Method to use for all documents")
    force_reclassification: bool = Field(False, description="Force reclassification")
    user_id: str = Field(..., description="User requesting bulk classification")

class ClassificationRuleRequest(BaseModel):
    """Request to create/update classification rule"""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    pattern: str = Field(..., description="Pattern to match")
    pattern_type: str = Field(..., description="Type of pattern")
    classification_level: DataClassificationLevel = Field(..., description="Classification level")
    data_category: DataCategory = Field(..., description="Data category")
    sensitivity: DataSensitivity = Field(..., description="Sensitivity level")
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Confidence threshold")
    handling_actions: List[DataHandlingAction] = Field(..., description="Handling actions")
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list, description="Compliance requirements")
    is_active: bool = Field(True, description="Whether rule is active")
    priority: int = Field(100, description="Rule priority")

class ClassificationPolicyRequest(BaseModel):
    """Request to create/update classification policy"""
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    classification_level: DataClassificationLevel = Field(..., description="Classification level")
    data_category: DataCategory = Field(..., description="Data category")
    sensitivity: DataSensitivity = Field(..., description="Sensitivity level")
    handling_actions: List[DataHandlingAction] = Field(..., description="Handling actions")
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list, description="Compliance requirements")
    retention_period_days: Optional[int] = Field(None, description="Retention period")
    access_controls: Dict[str, Any] = Field(default_factory=dict, description="Access controls")
    sharing_restrictions: Dict[str, Any] = Field(default_factory=dict, description="Sharing restrictions")
    encryption_required: bool = Field(True, description="Encryption required")
    audit_required: bool = Field(True, description="Audit required")
    backup_required: bool = Field(True, description="Backup required")
    is_active: bool = Field(True, description="Whether policy is active")

class ClassificationQuery(BaseModel):
    """Query parameters for classification data"""
    classification_level: Optional[DataClassificationLevel] = None
    data_category: Optional[DataCategory] = None
    sensitivity: Optional[DataSensitivity] = None
    compliance_requirement: Optional[ComplianceRequirement] = None
    classification_method: Optional[ClassificationMethod] = None
    requires_review: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class ClassificationStats(BaseModel):
    """Classification statistics"""
    total_documents: int
    classified_documents: int
    unclassified_documents: int
    classification_by_level: Dict[str, int]
    classification_by_category: Dict[str, int]
    classification_by_sensitivity: Dict[str, int]
    classification_by_method: Dict[str, int]
    compliance_coverage: Dict[str, int]
    requires_review_count: int
    average_confidence: float
    classification_accuracy: float

class ClassificationAuditLog(BaseModel):
    """Audit log for classification changes"""
    id: UUID = Field(default_factory=uuid4)
    document_id: str = Field(..., description="Document ID")
    action: str = Field(..., description="Action performed")
    old_classification: Optional[DataClassificationLevel] = Field(None, description="Previous classification")
    new_classification: Optional[DataClassificationLevel] = Field(None, description="New classification")
    old_category: Optional[DataCategory] = Field(None, description="Previous category")
    new_category: Optional[DataCategory] = Field(None, description="New category")
    old_sensitivity: Optional[DataSensitivity] = Field(None, description="Previous sensitivity")
    new_sensitivity: Optional[DataSensitivity] = Field(None, description="New sensitivity")
    reason: str = Field(..., description="Reason for change")
    changed_by: str = Field(..., description="User who made the change")
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = Field(None, description="IP address of user")
    user_agent: Optional[str] = Field(None, description="User agent")
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="Additional audit data")

class ClassificationReport(BaseModel):
    """Classification report"""
    id: UUID = Field(default_factory=uuid4)
    report_name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Type of report")
    query_params: ClassificationQuery = Field(..., description="Query parameters used")
    generated_by: str = Field(..., description="User who generated the report")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: Optional[str] = Field(None, description="Path to generated report file")
    file_size: Optional[int] = Field(None, description="Size of report file")
    expires_at: Optional[datetime] = Field(None, description="Report expiration date")
    is_public: bool = Field(False, description="Whether report is publicly accessible")
    access_token: Optional[str] = Field(None, description="Access token for report")
