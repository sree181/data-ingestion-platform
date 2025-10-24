"""
Compliance Framework Models

This module defines Pydantic models for compliance framework configuration,
validation, and reporting across different regulatory standards.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import json


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOX = "SOX"
    PCI_DSS = "PCI_DSS"
    ISO27001 = "ISO27001"
    CCPA = "CCPA"
    FERPA = "FERPA"
    CUSTOM = "CUSTOM"


class DataCategory(str, Enum):
    """Data categories for compliance classification"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    BUSINESS_DATA = "business_data"
    PUBLIC_DATA = "public_data"


class RetentionPolicy(str, Enum):
    """Data retention policies"""
    IMMEDIATE_DELETE = "immediate_delete"
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"


class ComplianceRequirement(BaseModel):
    """Individual compliance requirement"""
    id: str = Field(..., description="Unique requirement ID")
    name: str = Field(..., description="Requirement name")
    description: str = Field(..., description="Detailed description")
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    category: str = Field(..., description="Requirement category")
    mandatory: bool = Field(default=True, description="Whether requirement is mandatory")
    data_categories: List[DataCategory] = Field(default=[], description="Applicable data categories")
    controls: List[str] = Field(default=[], description="Security controls required")
    validation_rules: Dict[str, Any] = Field(default={}, description="Validation rules")
    documentation_required: bool = Field(default=False, description="Whether documentation is required")


class ComplianceConfiguration(BaseModel):
    """Compliance configuration for a project space"""
    space_id: str = Field(..., description="Project space ID")
    frameworks: List[ComplianceFramework] = Field(..., description="Enabled compliance frameworks")
    data_categories: List[DataCategory] = Field(..., description="Data categories in use")
    retention_policies: Dict[DataCategory, RetentionPolicy] = Field(
        default={}, 
        description="Retention policies per data category"
    )
    requirements: List[ComplianceRequirement] = Field(default=[], description="Active requirements")
    custom_requirements: List[ComplianceRequirement] = Field(default=[], description="Custom requirements")
    audit_schedule: Dict[str, Any] = Field(default={}, description="Audit schedule configuration")
    reporting_config: Dict[str, Any] = Field(default={}, description="Reporting configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_audit: Optional[datetime] = Field(default=None, description="Last audit date")
    next_audit: Optional[datetime] = Field(default=None, description="Next audit date")


class ComplianceValidation(BaseModel):
    """Compliance validation result"""
    requirement_id: str = Field(..., description="Requirement ID")
    status: str = Field(..., description="Validation status: passed, failed, warning")
    score: float = Field(..., ge=0, le=100, description="Compliance score (0-100)")
    details: Dict[str, Any] = Field(default={}, description="Validation details")
    recommendations: List[str] = Field(default=[], description="Improvement recommendations")
    evidence: List[str] = Field(default=[], description="Evidence of compliance")
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceReport(BaseModel):
    """Compliance report"""
    space_id: str = Field(..., description="Project space ID")
    report_id: str = Field(..., description="Unique report ID")
    frameworks: List[ComplianceFramework] = Field(..., description="Frameworks covered")
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    validations: List[ComplianceValidation] = Field(..., description="Individual validations")
    summary: Dict[str, Any] = Field(default={}, description="Report summary")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="User who generated the report")
    valid_until: Optional[datetime] = Field(default=None, description="Report validity period")


class ComplianceAudit(BaseModel):
    """Compliance audit record"""
    audit_id: str = Field(..., description="Unique audit ID")
    space_id: str = Field(..., description="Project space ID")
    frameworks: List[ComplianceFramework] = Field(..., description="Frameworks audited")
    auditor: str = Field(..., description="Auditor name/ID")
    audit_type: str = Field(..., description="Type of audit: internal, external, self_assessment")
    findings: List[Dict[str, Any]] = Field(default=[], description="Audit findings")
    recommendations: List[str] = Field(default=[], description="Audit recommendations")
    status: str = Field(default="in_progress", description="Audit status")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, description="Audit completion date")
    report_url: Optional[str] = Field(default=None, description="Audit report URL")


class ComplianceRequest(BaseModel):
    """Request to configure compliance"""
    space_id: str = Field(..., description="Project space ID")
    frameworks: List[ComplianceFramework] = Field(..., description="Compliance frameworks to enable")
    data_categories: List[DataCategory] = Field(..., description="Data categories in use")
    retention_policies: Optional[Dict[DataCategory, RetentionPolicy]] = Field(
        default=None, 
        description="Custom retention policies"
    )
    custom_requirements: Optional[List[ComplianceRequirement]] = Field(
        default=None, 
        description="Custom compliance requirements"
    )
    audit_schedule: Optional[Dict[str, Any]] = Field(default=None, description="Audit schedule")
    reporting_config: Optional[Dict[str, Any]] = Field(default=None, description="Reporting config")


class ComplianceUpdateRequest(BaseModel):
    """Request to update compliance configuration"""
    frameworks: Optional[List[ComplianceFramework]] = Field(default=None, description="Frameworks to update")
    data_categories: Optional[List[DataCategory]] = Field(default=None, description="Data categories to update")
    retention_policies: Optional[Dict[DataCategory, RetentionPolicy]] = Field(
        default=None, 
        description="Retention policies to update"
    )
    custom_requirements: Optional[List[ComplianceRequirement]] = Field(
        default=None, 
        description="Custom requirements to update"
    )
    audit_schedule: Optional[Dict[str, Any]] = Field(default=None, description="Audit schedule to update")
    reporting_config: Optional[Dict[str, Any]] = Field(default=None, description="Reporting config to update")


class ComplianceValidationRequest(BaseModel):
    """Request to validate compliance"""
    space_id: str = Field(..., description="Project space ID")
    frameworks: Optional[List[ComplianceFramework]] = Field(default=None, description="Frameworks to validate")
    requirement_ids: Optional[List[str]] = Field(default=None, description="Specific requirements to validate")


class ComplianceReportRequest(BaseModel):
    """Request to generate compliance report"""
    space_id: str = Field(..., description="Project space ID")
    frameworks: Optional[List[ComplianceFramework]] = Field(default=None, description="Frameworks to include")
    include_recommendations: bool = Field(default=True, description="Include recommendations")
    format: str = Field(default="json", description="Report format: json, pdf, html")


# Pre-defined compliance requirements for each framework
GDPR_REQUIREMENTS = [
    ComplianceRequirement(
        id="gdpr_001",
        name="Data Minimization",
        description="Collect only data that is necessary for the stated purpose",
        framework=ComplianceFramework.GDPR,
        category="Data Collection",
        data_categories=[DataCategory.PERSONAL_DATA, DataCategory.SENSITIVE_PERSONAL_DATA],
        controls=["data_inventory", "purpose_limitation", "data_mapping"],
        validation_rules={"max_data_fields": 50, "purpose_justification_required": True}
    ),
    ComplianceRequirement(
        id="gdpr_002",
        name="Consent Management",
        description="Obtain explicit consent for data processing",
        framework=ComplianceFramework.GDPR,
        category="Consent",
        data_categories=[DataCategory.PERSONAL_DATA, DataCategory.SENSITIVE_PERSONAL_DATA],
        controls=["consent_tracking", "withdrawal_mechanism", "consent_records"],
        validation_rules={"explicit_consent_required": True, "withdrawal_available": True}
    ),
    ComplianceRequirement(
        id="gdpr_003",
        name="Right to Erasure",
        description="Implement data subject's right to erasure (right to be forgotten)",
        framework=ComplianceFramework.GDPR,
        category="Data Subject Rights",
        data_categories=[DataCategory.PERSONAL_DATA, DataCategory.SENSITIVE_PERSONAL_DATA],
        controls=["data_deletion", "backup_cleanup", "third_party_notification"],
        validation_rules={"deletion_timeframe_days": 30, "verification_required": True}
    ),
    ComplianceRequirement(
        id="gdpr_004",
        name="Data Portability",
        description="Enable data subjects to receive their data in a portable format",
        framework=ComplianceFramework.GDPR,
        category="Data Subject Rights",
        data_categories=[DataCategory.PERSONAL_DATA],
        controls=["data_export", "machine_readable_format", "secure_transfer"],
        validation_rules={"export_format": "json", "response_time_days": 30}
    ),
    ComplianceRequirement(
        id="gdpr_005",
        name="Privacy by Design",
        description="Implement privacy considerations from the start of system design",
        framework=ComplianceFramework.GDPR,
        category="System Design",
        data_categories=[DataCategory.PERSONAL_DATA, DataCategory.SENSITIVE_PERSONAL_DATA],
        controls=["privacy_impact_assessment", "default_privacy_settings", "encryption_at_rest"],
        validation_rules={"encryption_required": True, "pia_required": True}
    )
]

HIPAA_REQUIREMENTS = [
    ComplianceRequirement(
        id="hipaa_001",
        name="Administrative Safeguards",
        description="Implement administrative policies and procedures",
        framework=ComplianceFramework.HIPAA,
        category="Administrative",
        data_categories=[DataCategory.HEALTH_DATA],
        controls=["security_officer", "workforce_training", "access_management"],
        validation_rules={"security_officer_assigned": True, "training_frequency_months": 12}
    ),
    ComplianceRequirement(
        id="hipaa_002",
        name="Physical Safeguards",
        description="Implement physical access controls and workstation security",
        framework=ComplianceFramework.HIPAA,
        category="Physical",
        data_categories=[DataCategory.HEALTH_DATA],
        controls=["facility_access", "workstation_controls", "device_controls"],
        validation_rules={"access_logging": True, "workstation_encryption": True}
    ),
    ComplianceRequirement(
        id="hipaa_003",
        name="Technical Safeguards",
        description="Implement technical security measures",
        framework=ComplianceFramework.HIPAA,
        category="Technical",
        data_categories=[DataCategory.HEALTH_DATA],
        controls=["access_control", "audit_logs", "integrity", "transmission_security"],
        validation_rules={"encryption_in_transit": True, "audit_logging": True, "access_controls": True}
    ),
    ComplianceRequirement(
        id="hipaa_004",
        name="Breach Notification",
        description="Implement breach detection and notification procedures",
        framework=ComplianceFramework.HIPAA,
        category="Incident Response",
        data_categories=[DataCategory.HEALTH_DATA],
        controls=["breach_detection", "notification_procedures", "documentation"],
        validation_rules={"notification_timeframe_hours": 72, "documentation_required": True}
    )
]

SOX_REQUIREMENTS = [
    ComplianceRequirement(
        id="sox_001",
        name="Internal Controls",
        description="Implement adequate internal controls over financial reporting",
        framework=ComplianceFramework.SOX,
        category="Internal Controls",
        data_categories=[DataCategory.FINANCIAL_DATA, DataCategory.BUSINESS_DATA],
        controls=["control_documentation", "control_testing", "deficiency_management"],
        validation_rules={"control_documentation": True, "testing_frequency": "quarterly"}
    ),
    ComplianceRequirement(
        id="sox_002",
        name="Management Assessment",
        description="Management assessment of internal controls",
        framework=ComplianceFramework.SOX,
        category="Management",
        data_categories=[DataCategory.FINANCIAL_DATA],
        controls=["management_certification", "assessment_procedures", "documentation"],
        validation_rules={"annual_assessment": True, "certification_required": True}
    ),
    ComplianceRequirement(
        id="sox_003",
        name="Audit Trail",
        description="Maintain comprehensive audit trails for financial data",
        framework=ComplianceFramework.SOX,
        category="Audit",
        data_categories=[DataCategory.FINANCIAL_DATA],
        controls=["audit_logging", "log_integrity", "retention_management"],
        validation_rules={"log_retention_years": 7, "immutable_logs": True}
    )
]

# Registry of all compliance requirements
COMPLIANCE_REQUIREMENTS_REGISTRY = {
    ComplianceFramework.GDPR: GDPR_REQUIREMENTS,
    ComplianceFramework.HIPAA: HIPAA_REQUIREMENTS,
    ComplianceFramework.SOX: SOX_REQUIREMENTS,
    ComplianceFramework.PCI_DSS: [],  # To be implemented
    ComplianceFramework.ISO27001: [],  # To be implemented
    ComplianceFramework.CCPA: [],  # To be implemented
    ComplianceFramework.FERPA: [],  # To be implemented
}
