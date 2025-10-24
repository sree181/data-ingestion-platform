"""
Compliance Framework Service

This service handles compliance framework configuration, validation,
and reporting for project spaces.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.compliance import (
    ComplianceConfiguration, ComplianceRequirement, ComplianceValidation,
    ComplianceReport, ComplianceAudit, ComplianceFramework, DataCategory,
    RetentionPolicy, COMPLIANCE_REQUIREMENTS_REGISTRY
)
from models.project_spaces import ProjectSpace
from models.project_spaces import SpacePermission

logger = structlog.get_logger(__name__)


class ComplianceService:
    """Service for managing compliance frameworks"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def configure_compliance(
        self, 
        space_id: str, 
        frameworks: List[ComplianceFramework],
        data_categories: List[DataCategory],
        retention_policies: Optional[Dict[DataCategory, RetentionPolicy]] = None,
        custom_requirements: Optional[List[ComplianceRequirement]] = None,
        audit_schedule: Optional[Dict[str, Any]] = None,
        reporting_config: Optional[Dict[str, Any]] = None
    ) -> ComplianceConfiguration:
        """Configure compliance frameworks for a project space"""
        
        logger.info("Configuring compliance", space_id=space_id, frameworks=frameworks)
        
        try:
            # Get all requirements for selected frameworks
            requirements = []
            for framework in frameworks:
                if framework in COMPLIANCE_REQUIREMENTS_REGISTRY:
                    requirements.extend(COMPLIANCE_REQUIREMENTS_REGISTRY[framework])
            
            # Add custom requirements if provided
            if custom_requirements:
                requirements.extend(custom_requirements)
            
            # Set default retention policies if not provided
            if not retention_policies:
                retention_policies = self._get_default_retention_policies(data_categories)
            
            # Set default audit schedule if not provided
            if not audit_schedule:
                audit_schedule = {
                    "frequency": "quarterly",
                    "next_audit": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                    "auditor": "internal"
                }
            
            # Set default reporting config if not provided
            if not reporting_config:
                reporting_config = {
                    "format": "json",
                    "include_recommendations": True,
                    "auto_generate": True,
                    "frequency": "monthly"
                }
            
            # Create compliance configuration
            config = ComplianceConfiguration(
                space_id=space_id,
                frameworks=frameworks,
                data_categories=data_categories,
                retention_policies=retention_policies,
                requirements=requirements,
                custom_requirements=custom_requirements or [],
                audit_schedule=audit_schedule,
                reporting_config=reporting_config,
                next_audit=datetime.fromisoformat(audit_schedule["next_audit"]) if audit_schedule.get("next_audit") else None
            )
            
            # Store in database
            await self._store_compliance_config(config)
            
            logger.info("Compliance configured successfully", space_id=space_id)
            return config
            
        except Exception as e:
            logger.error("Failed to configure compliance", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def get_compliance_config(self, space_id: str) -> Optional[ComplianceConfiguration]:
        """Get compliance configuration for a project space"""
        
        logger.info("Getting compliance config", space_id=space_id)
        
        try:
            query = text("""
                SELECT compliance_config 
                FROM project_spaces 
                WHERE space_id = :space_id
            """)
            
            result = await self.db_session.execute(query, {"space_id": space_id})
            row = result.fetchone()
            
            if not row or not row[0]:
                return None
            
            config_data = json.loads(row[0])
            return ComplianceConfiguration(**config_data)
            
        except Exception as e:
            logger.error("Failed to get compliance config", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def update_compliance_config(
        self, 
        space_id: str, 
        frameworks: Optional[List[ComplianceFramework]] = None,
        data_categories: Optional[List[DataCategory]] = None,
        retention_policies: Optional[Dict[DataCategory, RetentionPolicy]] = None,
        custom_requirements: Optional[List[ComplianceRequirement]] = None,
        audit_schedule: Optional[Dict[str, Any]] = None,
        reporting_config: Optional[Dict[str, Any]] = None
    ) -> ComplianceConfiguration:
        """Update compliance configuration for a project space"""
        
        logger.info("Updating compliance config", space_id=space_id)
        
        try:
            # Get existing configuration
            existing_config = await self.get_compliance_config(space_id)
            if not existing_config:
                raise ValueError("Compliance configuration not found")
            
            # Update fields if provided
            if frameworks is not None:
                existing_config.frameworks = frameworks
                # Update requirements based on new frameworks
                requirements = []
                for framework in frameworks:
                    if framework in COMPLIANCE_REQUIREMENTS_REGISTRY:
                        requirements.extend(COMPLIANCE_REQUIREMENTS_REGISTRY[framework])
                existing_config.requirements = requirements
            
            if data_categories is not None:
                existing_config.data_categories = data_categories
            
            if retention_policies is not None:
                existing_config.retention_policies = retention_policies
            
            if custom_requirements is not None:
                existing_config.custom_requirements = custom_requirements
            
            if audit_schedule is not None:
                existing_config.audit_schedule = audit_schedule
                if audit_schedule.get("next_audit"):
                    existing_config.next_audit = datetime.fromisoformat(audit_schedule["next_audit"])
            
            if reporting_config is not None:
                existing_config.reporting_config = reporting_config
            
            existing_config.updated_at = datetime.utcnow()
            
            # Store updated configuration
            await self._store_compliance_config(existing_config)
            
            logger.info("Compliance config updated successfully", space_id=space_id)
            return existing_config
            
        except Exception as e:
            logger.error("Failed to update compliance config", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def validate_compliance(
        self, 
        space_id: str, 
        frameworks: Optional[List[ComplianceFramework]] = None
    ) -> List[ComplianceValidation]:
        """Validate compliance for a project space"""
        
        logger.info("Validating compliance", space_id=space_id, frameworks=frameworks)
        
        try:
            # Get compliance configuration
            config = await self.get_compliance_config(space_id)
            if not config:
                raise ValueError("Compliance configuration not found")
            
            # Filter requirements by frameworks if specified
            requirements_to_validate = config.requirements
            if frameworks:
                requirements_to_validate = [
                    req for req in config.requirements 
                    if req.framework in frameworks
                ]
            
            validations = []
            
            for requirement in requirements_to_validate:
                validation = await self._validate_requirement(space_id, requirement, config)
                validations.append(validation)
            
            logger.info("Compliance validation completed", space_id=space_id, validations_count=len(validations))
            return validations
            
        except Exception as e:
            logger.error("Failed to validate compliance", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def generate_compliance_report(
        self, 
        space_id: str, 
        frameworks: Optional[List[ComplianceFramework]] = None,
        include_recommendations: bool = True,
        format: str = "json"
    ) -> ComplianceReport:
        """Generate compliance report for a project space"""
        
        logger.info("Generating compliance report", space_id=space_id, frameworks=frameworks)
        
        try:
            # Get compliance configuration
            config = await self.get_compliance_config(space_id)
            if not config:
                raise ValueError("Compliance configuration not found")
            
            # Validate compliance
            validations = await self.validate_compliance(space_id, frameworks)
            
            # Calculate overall score
            if validations:
                overall_score = sum(v.score for v in validations) / len(validations)
            else:
                overall_score = 0.0
            
            # Generate report
            report_id = str(uuid.uuid4())
            report = ComplianceReport(
                space_id=space_id,
                report_id=report_id,
                frameworks=frameworks or config.frameworks,
                overall_score=overall_score,
                validations=validations,
                summary=self._generate_report_summary(validations, config),
                generated_by="system",  # TODO: Get from auth context
                valid_until=datetime.utcnow() + timedelta(days=30)
            )
            
            # Store report
            await self._store_compliance_report(report)
            
            logger.info("Compliance report generated", space_id=space_id, report_id=report_id, score=overall_score)
            return report
            
        except Exception as e:
            logger.error("Failed to generate compliance report", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def get_compliance_reports(self, space_id: str, limit: int = 10) -> List[ComplianceReport]:
        """Get compliance reports for a project space"""
        
        logger.info("Getting compliance reports", space_id=space_id, limit=limit)
        
        try:
            query = text("""
                SELECT report_data 
                FROM compliance_reports 
                WHERE space_id = :space_id 
                ORDER BY generated_at DESC 
                LIMIT :limit
            """)
            
            result = await self.db_session.execute(query, {"space_id": space_id, "limit": limit})
            rows = result.fetchall()
            
            reports = []
            for row in rows:
                report_data = json.loads(row[0])
                reports.append(ComplianceReport(**report_data))
            
            logger.info("Retrieved compliance reports", space_id=space_id, count=len(reports))
            return reports
            
        except Exception as e:
            logger.error("Failed to get compliance reports", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def _store_compliance_config(self, config: ComplianceConfiguration) -> None:
        """Store compliance configuration in database"""
        
        config_json = json.dumps(config.dict(), default=str)
        
        query = text("""
            UPDATE project_spaces 
            SET compliance_config = :config_json,
                updated_at = :updated_at
            WHERE space_id = :space_id
        """)
        
        await self.db_session.execute(query, {
            "space_id": config.space_id,
            "config_json": config_json,
            "updated_at": config.updated_at
        })
        await self.db_session.commit()
    
    async def _store_compliance_report(self, report: ComplianceReport) -> None:
        """Store compliance report in database"""
        
        report_json = json.dumps(report.dict(), default=str)
        
        query = text("""
            INSERT INTO compliance_reports (report_id, space_id, report_data, generated_at)
            VALUES (:report_id, :space_id, :report_data, :generated_at)
            ON CONFLICT (report_id) DO UPDATE SET
                report_data = EXCLUDED.report_data,
                generated_at = EXCLUDED.generated_at
        """)
        
        await self.db_session.execute(query, {
            "report_id": report.report_id,
            "space_id": report.space_id,
            "report_data": report_json,
            "generated_at": report.generated_at
        })
        await self.db_session.commit()
    
    async def _validate_requirement(
        self, 
        space_id: str, 
        requirement: ComplianceRequirement, 
        config: ComplianceConfiguration
    ) -> ComplianceValidation:
        """Validate a specific compliance requirement"""
        
        # This is a simplified validation - in production, this would check actual system state
        score = 0.0
        status = "failed"
        details = {}
        recommendations = []
        evidence = []
        
        # Check if data categories are properly configured
        if requirement.data_categories:
            for category in requirement.data_categories:
                if category in config.data_categories:
                    score += 20.0
                    evidence.append(f"Data category '{category.value}' is configured")
                else:
                    recommendations.append(f"Configure data category '{category.value}' for {requirement.framework.value}")
        
        # Check if security controls are implemented
        if requirement.controls:
            for control in requirement.controls:
                # Simplified check - in production, verify actual implementation
                if control in ["encryption_at_rest", "encryption_in_transit"]:
                    score += 15.0
                    evidence.append(f"Security control '{control}' is implemented")
                else:
                    score += 10.0
                    evidence.append(f"Security control '{control}' is configured")
        
        # Check validation rules
        if requirement.validation_rules:
            for rule, value in requirement.validation_rules.items():
                if rule == "encryption_required" and value:
                    score += 25.0
                    evidence.append("Encryption is properly configured")
                elif rule == "audit_logging" and value:
                    score += 20.0
                    evidence.append("Audit logging is enabled")
                else:
                    score += 10.0
                    evidence.append(f"Rule '{rule}' is configured")
        
        # Determine status based on score
        if score >= 80:
            status = "passed"
        elif score >= 60:
            status = "warning"
        else:
            status = "failed"
        
        # Add general recommendations if score is low
        if score < 80:
            recommendations.extend([
                f"Review {requirement.name} implementation",
                f"Ensure all required controls for {requirement.framework.value} are in place",
                "Consider conducting a compliance audit"
            ])
        
        return ComplianceValidation(
            requirement_id=requirement.id,
            status=status,
            score=score,
            details=details,
            recommendations=recommendations,
            evidence=evidence
        )
    
    def _get_default_retention_policies(self, data_categories: List[DataCategory]) -> Dict[DataCategory, RetentionPolicy]:
        """Get default retention policies for data categories"""
        
        defaults = {
            DataCategory.PERSONAL_DATA: RetentionPolicy.MEDIUM_TERM,
            DataCategory.SENSITIVE_PERSONAL_DATA: RetentionPolicy.SHORT_TERM,
            DataCategory.FINANCIAL_DATA: RetentionPolicy.LONG_TERM,
            DataCategory.HEALTH_DATA: RetentionPolicy.LONG_TERM,
            DataCategory.BUSINESS_DATA: RetentionPolicy.MEDIUM_TERM,
            DataCategory.PUBLIC_DATA: RetentionPolicy.PERMANENT
        }
        
        return {category: defaults.get(category, RetentionPolicy.MEDIUM_TERM) for category in data_categories}
    
    def _generate_report_summary(self, validations: List[ComplianceValidation], config: ComplianceConfiguration) -> Dict[str, Any]:
        """Generate summary for compliance report"""
        
        total_requirements = len(validations)
        passed = len([v for v in validations if v.status == "passed"])
        warnings = len([v for v in validations if v.status == "warning"])
        failed = len([v for v in validations if v.status == "failed"])
        
        framework_scores = {}
        for framework in config.frameworks:
            framework_validations = [v for v in validations if any(req.framework == framework for req in config.requirements if req.id == v.requirement_id)]
            if framework_validations:
                framework_scores[framework.value] = sum(v.score for v in framework_validations) / len(framework_validations)
        
        return {
            "total_requirements": total_requirements,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "compliance_percentage": (passed / total_requirements * 100) if total_requirements > 0 else 0,
            "framework_scores": framework_scores,
            "data_categories": [cat.value for cat in config.data_categories],
            "retention_policies": {cat.value: policy.value for cat, policy in config.retention_policies.items()}
        }
