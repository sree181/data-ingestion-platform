"""
Enterprise Compliance Engine
Implements SOX, GDPR, HIPAA compliance with automated reporting
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd
from jinja2 import Template

Base = declarative_base()

class ComplianceFramework(Enum):
    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    NIST = "nist"
    PCI_DSS = "pci_dss"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_APPLICABLE = "not_applicable"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceControl:
    control_id: str
    framework: ComplianceFramework
    title: str
    description: str
    requirement: str
    implementation_guidance: str
    risk_level: RiskLevel
    frequency: str  # daily, weekly, monthly, quarterly, annually
    automated: bool = True

@dataclass
class ComplianceAssessment:
    control_id: str
    status: ComplianceStatus
    score: float  # 0-100
    evidence: List[str]
    gaps: List[str]
    recommendations: List[str]
    last_assessed: datetime
    next_assessment_due: datetime

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True)
    report_id = Column(String(64), unique=True, nullable=False)
    project_id = Column(Integer, nullable=True)
    framework = Column(String(20), nullable=False)
    
    # Report metadata
    report_type = Column(String(50), nullable=False)  # assessment, audit, remediation
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Compliance scores
    overall_score = Column(Float, nullable=False)
    control_scores = Column(JSON, nullable=False)
    risk_assessment = Column(JSON, nullable=False)
    
    # Report content
    executive_summary = Column(Text, nullable=False)
    findings = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    
    # Status and workflow
    status = Column(String(20), default="draft")  # draft, final, approved
    generated_by = Column(Integer, nullable=False)
    approved_by = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

class ComplianceControlImplementation(Base):
    __tablename__ = "compliance_control_implementations"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, nullable=False)
    control_id = Column(String(50), nullable=False)
    framework = Column(String(20), nullable=False)
    
    # Implementation status
    status = Column(String(20), nullable=False)
    implementation_date = Column(DateTime, nullable=True)
    last_tested = Column(DateTime, nullable=True)
    next_test_due = Column(DateTime, nullable=True)
    
    # Assessment results
    current_score = Column(Float, default=0.0)
    evidence_collected = Column(JSON, default=[])
    gaps_identified = Column(JSON, default=[])
    remediation_plan = Column(JSON, default=[])
    
    # Responsible parties
    owner_id = Column(Integer, nullable=False)
    reviewer_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EnterpriseComplianceEngine:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.controls = self._load_compliance_controls()
        
    def _load_compliance_controls(self) -> Dict[ComplianceFramework, List[ComplianceControl]]:
        """Load compliance controls for each framework"""
        return {
            ComplianceFramework.SOX: self._get_sox_controls(),
            ComplianceFramework.GDPR: self._get_gdpr_controls(),
            ComplianceFramework.HIPAA: self._get_hipaa_controls(),
            ComplianceFramework.ISO27001: self._get_iso27001_controls(),
            ComplianceFramework.NIST: self._get_nist_controls()
        }
    
    def _get_sox_controls(self) -> List[ComplianceControl]:
        """SOX (Sarbanes-Oxley) compliance controls"""
        return [
            ComplianceControl(
                control_id="SOX-302",
                framework=ComplianceFramework.SOX,
                title="Management Assessment of Internal Controls",
                description="Principal executive and financial officers must certify internal controls",
                requirement="Quarterly assessment and certification of internal controls over financial reporting",
                implementation_guidance="Implement automated controls testing and management certification workflow",
                risk_level=RiskLevel.HIGH,
                frequency="quarterly"
            ),
            ComplianceControl(
                control_id="SOX-404",
                framework=ComplianceFramework.SOX,
                title="Management Assessment of Internal Controls",
                description="Annual management assessment of internal control over financial reporting",
                requirement="Document, test, and assess effectiveness of internal controls",
                implementation_guidance="Maintain comprehensive documentation of all financial controls and processes",
                risk_level=RiskLevel.CRITICAL,
                frequency="annually"
            ),
            ComplianceControl(
                control_id="SOX-ITGC-01",
                framework=ComplianceFramework.SOX,
                title="IT General Controls - Access Management",
                description="Proper access controls for financial systems and data",
                requirement="Implement role-based access controls with regular reviews",
                implementation_guidance="Use RBAC system with quarterly access reviews and segregation of duties",
                risk_level=RiskLevel.HIGH,
                frequency="quarterly"
            ),
            ComplianceControl(
                control_id="SOX-ITGC-02",
                framework=ComplianceFramework.SOX,
                title="IT General Controls - Change Management",
                description="Controlled changes to financial systems",
                requirement="All changes to financial systems must be authorized, tested, and documented",
                implementation_guidance="Implement change approval workflow with testing requirements",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="SOX-AUDIT-01",
                framework=ComplianceFramework.SOX,
                title="Audit Trail and Logging",
                description="Comprehensive audit trails for all financial transactions",
                requirement="Log all access to financial data with tamper-proof audit trails",
                implementation_guidance="Enable comprehensive audit logging with integrity protection",
                risk_level=RiskLevel.HIGH,
                frequency="daily"
            )
        ]
    
    def _get_gdpr_controls(self) -> List[ComplianceControl]:
        """GDPR compliance controls"""
        return [
            ComplianceControl(
                control_id="GDPR-ART-6",
                framework=ComplianceFramework.GDPR,
                title="Lawful Basis for Processing",
                description="Establish lawful basis for processing personal data",
                requirement="Document lawful basis for all personal data processing activities",
                implementation_guidance="Maintain data processing register with lawful basis documentation",
                risk_level=RiskLevel.CRITICAL,
                frequency="quarterly"
            ),
            ComplianceControl(
                control_id="GDPR-ART-25",
                framework=ComplianceFramework.GDPR,
                title="Data Protection by Design and Default",
                description="Implement privacy by design principles",
                requirement="Build privacy protections into systems and processes from the start",
                implementation_guidance="Implement privacy impact assessments and privacy-preserving technologies",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="GDPR-ART-32",
                framework=ComplianceFramework.GDPR,
                title="Security of Processing",
                description="Implement appropriate technical and organizational measures",
                requirement="Ensure appropriate security measures including encryption and access controls",
                implementation_guidance="Use encryption at rest and in transit, implement access controls",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="GDPR-ART-33",
                framework=ComplianceFramework.GDPR,
                title="Data Breach Notification",
                description="Notify supervisory authority of data breaches within 72 hours",
                requirement="Implement breach detection and notification procedures",
                implementation_guidance="Deploy automated breach detection with notification workflows",
                risk_level=RiskLevel.CRITICAL,
                frequency="daily"
            ),
            ComplianceControl(
                control_id="GDPR-ART-17",
                framework=ComplianceFramework.GDPR,
                title="Right to Erasure",
                description="Enable data subject right to erasure (right to be forgotten)",
                requirement="Implement processes to delete personal data upon request",
                implementation_guidance="Build automated data deletion capabilities with audit trails",
                risk_level=RiskLevel.MEDIUM,
                frequency="monthly"
            )
        ]
    
    def _get_hipaa_controls(self) -> List[ComplianceControl]:
        """HIPAA compliance controls"""
        return [
            ComplianceControl(
                control_id="HIPAA-164.308",
                framework=ComplianceFramework.HIPAA,
                title="Administrative Safeguards",
                description="Implement administrative safeguards for PHI",
                requirement="Assign security responsibility and conduct security training",
                implementation_guidance="Designate security officer and implement training program",
                risk_level=RiskLevel.HIGH,
                frequency="annually"
            ),
            ComplianceControl(
                control_id="HIPAA-164.310",
                framework=ComplianceFramework.HIPAA,
                title="Physical Safeguards",
                description="Implement physical safeguards for PHI",
                requirement="Control physical access to systems containing PHI",
                implementation_guidance="Implement facility access controls and workstation security",
                risk_level=RiskLevel.MEDIUM,
                frequency="quarterly"
            ),
            ComplianceControl(
                control_id="HIPAA-164.312",
                framework=ComplianceFramework.HIPAA,
                title="Technical Safeguards",
                description="Implement technical safeguards for PHI",
                requirement="Control access to PHI and implement audit controls",
                implementation_guidance="Use unique user identification, automatic logoff, and encryption",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="HIPAA-164.530",
                framework=ComplianceFramework.HIPAA,
                title="Access Control",
                description="Control access to PHI",
                requirement="Implement procedures to control access to PHI",
                implementation_guidance="Use role-based access with minimum necessary principle",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            )
        ]
    
    def _get_iso27001_controls(self) -> List[ComplianceControl]:
        """ISO 27001 compliance controls"""
        return [
            ComplianceControl(
                control_id="ISO-A.9.1.1",
                framework=ComplianceFramework.ISO27001,
                title="Access Control Policy",
                description="Establish access control policy",
                requirement="Document and implement access control policy",
                implementation_guidance="Create comprehensive access control policy with regular reviews",
                risk_level=RiskLevel.HIGH,
                frequency="annually"
            ),
            ComplianceControl(
                control_id="ISO-A.10.1.1",
                framework=ComplianceFramework.ISO27001,
                title="Cryptographic Controls",
                description="Implement cryptographic controls",
                requirement="Use cryptography to protect information confidentiality and integrity",
                implementation_guidance="Implement encryption for data at rest and in transit",
                risk_level=RiskLevel.HIGH,
                frequency="quarterly"
            ),
            ComplianceControl(
                control_id="ISO-A.12.4.1",
                framework=ComplianceFramework.ISO27001,
                title="Event Logging",
                description="Log security events",
                requirement="Record and regularly review security event logs",
                implementation_guidance="Implement comprehensive logging with automated analysis",
                risk_level=RiskLevel.MEDIUM,
                frequency="daily"
            )
        ]
    
    def _get_nist_controls(self) -> List[ComplianceControl]:
        """NIST Cybersecurity Framework controls"""
        return [
            ComplianceControl(
                control_id="NIST-ID.AM-1",
                framework=ComplianceFramework.NIST,
                title="Asset Management",
                description="Identify and manage organizational assets",
                requirement="Maintain inventory of all organizational assets",
                implementation_guidance="Use automated asset discovery and inventory management",
                risk_level=RiskLevel.MEDIUM,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="NIST-PR.AC-1",
                framework=ComplianceFramework.NIST,
                title="Access Control",
                description="Control access to assets and facilities",
                requirement="Implement identity and access management controls",
                implementation_guidance="Use multi-factor authentication and role-based access",
                risk_level=RiskLevel.HIGH,
                frequency="monthly"
            ),
            ComplianceControl(
                control_id="NIST-DE.AE-1",
                framework=ComplianceFramework.NIST,
                title="Anomaly Detection",
                description="Detect anomalous activity",
                requirement="Implement baseline network and system behavior monitoring",
                implementation_guidance="Deploy automated anomaly detection systems",
                risk_level=RiskLevel.MEDIUM,
                frequency="daily"
            )
        ]
    
    def assess_project_compliance(self, project_id: int, 
                                framework: ComplianceFramework) -> Dict:
        """Assess project compliance against specific framework"""
        controls = self.controls.get(framework, [])
        assessments = []
        total_score = 0.0
        
        for control in controls:
            assessment = self._assess_control_implementation(
                project_id, control
            )
            assessments.append(assessment)
            total_score += assessment.score
        
        overall_score = total_score / len(controls) if controls else 0.0
        
        # Categorize findings by risk level
        findings = self._categorize_findings(assessments)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(assessments)
        
        return {
            "project_id": project_id,
            "framework": framework.value,
            "overall_score": round(overall_score, 2),
            "total_controls": len(controls),
            "compliant_controls": len([a for a in assessments if a.status == ComplianceStatus.COMPLIANT]),
            "non_compliant_controls": len([a for a in assessments if a.status == ComplianceStatus.NON_COMPLIANT]),
            "assessments": [asdict(a) for a in assessments],
            "findings": findings,
            "recommendations": recommendations,
            "assessment_date": datetime.utcnow().isoformat()
        }
    
    def _assess_control_implementation(self, project_id: int, 
                                     control: ComplianceControl) -> ComplianceAssessment:
        """Assess implementation of specific control"""
        # Get current implementation status
        implementation = self.db.query(ComplianceControlImplementation).filter(
            ComplianceControlImplementation.project_id == project_id,
            ComplianceControlImplementation.control_id == control.control_id
        ).first()
        
        if not implementation:
            # Create new implementation record
            implementation = ComplianceControlImplementation(
                project_id=project_id,
                control_id=control.control_id,
                framework=control.framework.value,
                status=ComplianceStatus.NOT_APPLICABLE.value,
                owner_id=1  # Default system user
            )
            self.db.add(implementation)
            self.db.commit()
        
        # Perform automated assessment based on control type
        score, status, evidence, gaps = self._perform_automated_assessment(
            project_id, control, implementation
        )
        
        # Generate recommendations
        recommendations = self._generate_control_recommendations(control, gaps)
        
        # Calculate next assessment due date
        next_due = self._calculate_next_assessment_date(control.frequency)
        
        # Update implementation record
        implementation.current_score = score
        implementation.last_tested = datetime.utcnow()
        implementation.next_test_due = next_due
        implementation.evidence_collected = evidence
        implementation.gaps_identified = gaps
        self.db.commit()
        
        return ComplianceAssessment(
            control_id=control.control_id,
            status=status,
            score=score,
            evidence=evidence,
            gaps=gaps,
            recommendations=recommendations,
            last_assessed=datetime.utcnow(),
            next_assessment_due=next_due
        )
    
    def _perform_automated_assessment(self, project_id: int, 
                                    control: ComplianceControl,
                                    implementation: ComplianceControlImplementation) -> tuple:
        """Perform automated assessment of control implementation"""
        score = 0.0
        status = ComplianceStatus.NON_COMPLIANT
        evidence = []
        gaps = []
        
        # This would integrate with actual system checks
        # For demo purposes, we'll simulate assessments
        
        if "access" in control.control_id.lower():
            # Check access control implementation
            score, evidence, gaps = self._assess_access_controls(project_id)
        elif "encrypt" in control.description.lower():
            # Check encryption implementation
            score, evidence, gaps = self._assess_encryption(project_id)
        elif "audit" in control.description.lower() or "log" in control.description.lower():
            # Check audit logging
            score, evidence, gaps = self._assess_audit_logging(project_id)
        elif "backup" in control.description.lower():
            # Check backup procedures
            score, evidence, gaps = self._assess_backup_procedures(project_id)
        else:
            # Default assessment
            score = 75.0  # Assume partial compliance
            evidence = ["Manual review required"]
            gaps = ["Automated assessment not available"]
        
        # Determine status based on score
        if score >= 95:
            status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return score, status, evidence, gaps
    
    def _assess_access_controls(self, project_id: int) -> tuple:
        """Assess access control implementation"""
        # Mock assessment - would integrate with actual RBAC system
        score = 85.0
        evidence = [
            "RBAC system implemented",
            "MFA enabled for 87% of users",
            "Regular access reviews conducted"
        ]
        gaps = [
            "MFA adoption below 95% target",
            "Some privileged accounts lack MFA"
        ]
        return score, evidence, gaps
    
    def _assess_encryption(self, project_id: int) -> tuple:
        """Assess encryption implementation"""
        # Mock assessment - would integrate with encryption service
        score = 92.0
        evidence = [
            "AES-256 encryption implemented",
            "Data encrypted at rest and in transit",
            "Key rotation policy in place"
        ]
        gaps = [
            "Some legacy systems not encrypted",
            "Key rotation frequency could be improved"
        ]
        return score, evidence, gaps
    
    def _assess_audit_logging(self, project_id: int) -> tuple:
        """Assess audit logging implementation"""
        # Mock assessment - would integrate with audit system
        score = 78.0
        evidence = [
            "Comprehensive audit logging enabled",
            "Log integrity protection implemented",
            "Automated log analysis in place"
        ]
        gaps = [
            "Log retention policy needs documentation",
            "Some systems not sending logs to central system"
        ]
        return score, evidence, gaps
    
    def _assess_backup_procedures(self, project_id: int) -> tuple:
        """Assess backup procedures"""
        # Mock assessment
        score = 88.0
        evidence = [
            "Automated daily backups configured",
            "Backup integrity testing performed",
            "Offsite backup storage implemented"
        ]
        gaps = [
            "Recovery time objectives not documented",
            "Disaster recovery testing needs improvement"
        ]
        return score, evidence, gaps
    
    def _categorize_findings(self, assessments: List[ComplianceAssessment]) -> Dict:
        """Categorize findings by risk level and status"""
        findings = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for assessment in assessments:
            if assessment.status == ComplianceStatus.NON_COMPLIANT:
                risk_level = "high"  # Non-compliance is always high risk
            elif assessment.status == ComplianceStatus.PARTIALLY_COMPLIANT:
                risk_level = "medium"
            else:
                continue  # Skip compliant controls
            
            findings[risk_level].append({
                "control_id": assessment.control_id,
                "status": assessment.status.value,
                "score": assessment.score,
                "gaps": assessment.gaps
            })
        
        return findings
    
    def _generate_recommendations(self, assessments: List[ComplianceAssessment]) -> List[Dict]:
        """Generate compliance recommendations"""
        recommendations = []
        
        for assessment in assessments:
            if assessment.status != ComplianceStatus.COMPLIANT:
                for rec in assessment.recommendations:
                    recommendations.append({
                        "control_id": assessment.control_id,
                        "priority": "high" if assessment.score < 70 else "medium",
                        "recommendation": rec,
                        "estimated_effort": "TBD"
                    })
        
        return recommendations
    
    def _generate_control_recommendations(self, control: ComplianceControl, 
                                        gaps: List[str]) -> List[str]:
        """Generate recommendations for specific control"""
        recommendations = []
        
        for gap in gaps:
            if "mfa" in gap.lower():
                recommendations.append("Implement mandatory MFA for all users")
            elif "encrypt" in gap.lower():
                recommendations.append("Upgrade encryption to current standards")
            elif "log" in gap.lower():
                recommendations.append("Enhance logging coverage and retention")
            elif "backup" in gap.lower():
                recommendations.append("Improve backup and recovery procedures")
            else:
                recommendations.append(f"Address identified gap: {gap}")
        
        # Add implementation guidance
        recommendations.append(control.implementation_guidance)
        
        return recommendations
    
    def _calculate_next_assessment_date(self, frequency: str) -> datetime:
        """Calculate next assessment due date"""
        now = datetime.utcnow()
        
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        elif frequency == "quarterly":
            return now + timedelta(days=90)
        elif frequency == "annually":
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=30)  # Default to monthly
    
    def generate_compliance_report(self, project_id: int, 
                                 framework: ComplianceFramework,
                                 report_type: str = "assessment") -> str:
        """Generate comprehensive compliance report"""
        # Perform compliance assessment
        assessment_results = self.assess_project_compliance(project_id, framework)
        
        # Generate report ID
        report_id = f"{framework.value}_{project_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create executive summary
        executive_summary = self._generate_executive_summary(assessment_results)
        
        # Store report in database
        report = ComplianceReport(
            report_id=report_id,
            project_id=project_id,
            framework=framework.value,
            report_type=report_type,
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            overall_score=assessment_results["overall_score"],
            control_scores={a["control_id"]: a["score"] for a in assessment_results["assessments"]},
            risk_assessment=assessment_results["findings"],
            executive_summary=executive_summary,
            findings=assessment_results["findings"],
            recommendations=assessment_results["recommendations"],
            evidence=[a["evidence"] for a in assessment_results["assessments"]],
            generated_by=1  # System user
        )
        
        self.db.add(report)
        self.db.commit()
        
        return report_id
    
    def _generate_executive_summary(self, assessment_results: Dict) -> str:
        """Generate executive summary for compliance report"""
        template = Template("""
        EXECUTIVE SUMMARY
        
        Compliance Assessment: {{ framework.upper() }}
        Project ID: {{ project_id }}
        Assessment Date: {{ assessment_date }}
        
        OVERALL COMPLIANCE SCORE: {{ overall_score }}%
        
        KEY FINDINGS:
        - Total Controls Assessed: {{ total_controls }}
        - Compliant Controls: {{ compliant_controls }} ({{ (compliant_controls / total_controls * 100) | round(1) }}%)
        - Non-Compliant Controls: {{ non_compliant_controls }} ({{ (non_compliant_controls / total_controls * 100) | round(1) }}%)
        
        RISK SUMMARY:
        - Critical Issues: {{ findings.critical | length }}
        - High Risk Issues: {{ findings.high | length }}
        - Medium Risk Issues: {{ findings.medium | length }}
        
        RECOMMENDATIONS:
        {% for rec in recommendations[:5] %}
        - {{ rec.recommendation }}
        {% endfor %}
        
        This assessment provides a comprehensive view of compliance status and identifies
        areas requiring immediate attention to maintain regulatory compliance.
        """)
        
        return template.render(**assessment_results)
    
    def get_compliance_dashboard(self, project_id: int = None) -> Dict:
        """Get compliance dashboard data"""
        frameworks = [ComplianceFramework.SOX, ComplianceFramework.GDPR, ComplianceFramework.HIPAA]
        
        dashboard_data = {
            "overall_compliance_score": 0.0,
            "frameworks": [],
            "recent_assessments": [],
            "critical_findings": 0,
            "high_risk_findings": 0,
            "total_controls": 0,
            "compliant_controls": 0
        }
        
        total_score = 0.0
        total_frameworks = 0
        
        for framework in frameworks:
            if project_id:
                assessment = self.assess_project_compliance(project_id, framework)
            else:
                # Get organization-wide assessment
                assessment = self._get_organization_compliance(framework)
            
            dashboard_data["frameworks"].append({
                "name": framework.value.upper(),
                "score": assessment["overall_score"],
                "status": "compliant" if assessment["overall_score"] >= 95 else
                         "partially_compliant" if assessment["overall_score"] >= 70 else
                         "non_compliant",
                "last_assessed": assessment["assessment_date"]
            })
            
            total_score += assessment["overall_score"]
            total_frameworks += 1
            
            dashboard_data["critical_findings"] += len(assessment["findings"].get("critical", []))
            dashboard_data["high_risk_findings"] += len(assessment["findings"].get("high", []))
            dashboard_data["total_controls"] += assessment["total_controls"]
            dashboard_data["compliant_controls"] += assessment["compliant_controls"]
        
        dashboard_data["overall_compliance_score"] = round(total_score / total_frameworks, 2) if total_frameworks > 0 else 0.0
        
        return dashboard_data
    
    def _get_organization_compliance(self, framework: ComplianceFramework) -> Dict:
        """Get organization-wide compliance assessment"""
        # Mock implementation - would aggregate across all projects
        return {
            "framework": framework.value,
            "overall_score": 82.5,
            "total_controls": len(self.controls.get(framework, [])),
            "compliant_controls": 15,
            "non_compliant_controls": 3,
            "findings": {
                "critical": [],
                "high": [{"control_id": "SAMPLE-01", "issue": "Sample high risk finding"}],
                "medium": [],
                "low": []
            },
            "recommendations": [],
            "assessment_date": datetime.utcnow().isoformat()
        }
