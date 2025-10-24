"""
Compliance Framework API Routes

This module provides API endpoints for compliance framework configuration,
validation, and reporting.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime

from models.compliance import (
    ComplianceRequest, ComplianceUpdateRequest, ComplianceValidationRequest,
    ComplianceReportRequest, ComplianceConfiguration, ComplianceValidation,
    ComplianceReport, ComplianceFramework, DataCategory, RetentionPolicy
)
from services.compliance_service import ComplianceService
from models.project_spaces import SpacePermission
from auth.space_mfa_enforcement import require_space_mfa_verification
from auth.space_permissions import require_space_permission
from database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/compliance", tags=["Compliance Framework"])


@router.post("/configure")
async def configure_compliance(
    request: ComplianceRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.ADMIN))
):
    """
    Configure compliance frameworks for a project space.
    Requires ADMIN permission and MFA verification for sensitive spaces.
    """
    logger.info("Configuring compliance", space_id=request.space_id, user_id=current_user.get("user_id"))
    
    try:
        # Check MFA requirement for sensitive compliance frameworks
        sensitive_frameworks = [ComplianceFramework.HIPAA, ComplianceFramework.SOX, ComplianceFramework.PCI_DSS]
        if any(fw in request.frameworks for fw in sensitive_frameworks):
            await require_space_mfa_verification(request.space_id, None, current_user)
        
        compliance_service = ComplianceService(db_session)
        
        config = await compliance_service.configure_compliance(
            space_id=request.space_id,
            frameworks=request.frameworks,
            data_categories=request.data_categories,
            retention_policies=request.retention_policies,
            custom_requirements=request.custom_requirements,
            audit_schedule=request.audit_schedule,
            reporting_config=request.reporting_config
        )
        
        logger.info("Compliance configured successfully", space_id=request.space_id)
        
        return {
            "success": True,
            "message": "Compliance framework configured successfully",
            "configuration": config.dict()
        }
        
    except PermissionError as e:
        logger.warning("Permission denied for compliance configuration", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning("Invalid compliance configuration", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to configure compliance", 
                    space_id=request.space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure compliance: {str(e)}"
        )


@router.get("/config/{space_id}")
async def get_compliance_config(
    space_id: str,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Get compliance configuration for a project space.
    Requires READ permission.
    """
    logger.info("Getting compliance config", space_id=space_id, user_id=current_user.get("user_id"))
    
    try:
        compliance_service = ComplianceService(db_session)
        config = await compliance_service.get_compliance_config(space_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compliance configuration not found for this space"
            )
        
        logger.info("Compliance config retrieved", space_id=space_id)
        
        return {
            "success": True,
            "configuration": config.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get compliance config", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance configuration: {str(e)}"
        )


@router.put("/config/{space_id}")
async def update_compliance_config(
    space_id: str,
    request: ComplianceUpdateRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.ADMIN))
):
    """
    Update compliance configuration for a project space.
    Requires ADMIN permission and MFA verification for sensitive changes.
    """
    logger.info("Updating compliance config", space_id=space_id, user_id=current_user.get("user_id"))
    
    try:
        # Check MFA requirement for sensitive framework changes
        if request.frameworks:
            sensitive_frameworks = [ComplianceFramework.HIPAA, ComplianceFramework.SOX, ComplianceFramework.PCI_DSS]
            if any(fw in request.frameworks for fw in sensitive_frameworks):
                await require_space_mfa_verification(space_id, None, current_user)
        
        compliance_service = ComplianceService(db_session)
        
        config = await compliance_service.update_compliance_config(
            space_id=space_id,
            frameworks=request.frameworks,
            data_categories=request.data_categories,
            retention_policies=request.retention_policies,
            custom_requirements=request.custom_requirements,
            audit_schedule=request.audit_schedule,
            reporting_config=request.reporting_config
        )
        
        logger.info("Compliance config updated successfully", space_id=space_id)
        
        return {
            "success": True,
            "message": "Compliance configuration updated successfully",
            "configuration": config.dict()
        }
        
    except PermissionError as e:
        logger.warning("Permission denied for compliance update", 
                      space_id=space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning("Invalid compliance update", 
                      space_id=space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update compliance config", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update compliance configuration: {str(e)}"
        )


@router.post("/validate")
async def validate_compliance(
    request: ComplianceValidationRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Validate compliance for a project space.
    Requires READ permission.
    """
    logger.info("Validating compliance", space_id=request.space_id, user_id=current_user.get("user_id"))
    
    try:
        compliance_service = ComplianceService(db_session)
        
        validations = await compliance_service.validate_compliance(
            space_id=request.space_id,
            frameworks=request.frameworks
        )
        
        # Calculate overall compliance score
        overall_score = sum(v.score for v in validations) / len(validations) if validations else 0.0
        
        # Count statuses
        status_counts = {
            "passed": len([v for v in validations if v.status == "passed"]),
            "warning": len([v for v in validations if v.status == "warning"]),
            "failed": len([v for v in validations if v.status == "failed"])
        }
        
        logger.info("Compliance validation completed", 
                   space_id=request.space_id, overall_score=overall_score, status_counts=status_counts)
        
        return {
            "success": True,
            "overall_score": overall_score,
            "status_counts": status_counts,
            "validations": [v.dict() for v in validations],
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        logger.warning("Invalid compliance validation", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to validate compliance", 
                    space_id=request.space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate compliance: {str(e)}"
        )


@router.post("/report/generate")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Generate compliance report for a project space.
    Requires READ permission.
    """
    logger.info("Generating compliance report", space_id=request.space_id, user_id=current_user.get("user_id"))
    
    try:
        compliance_service = ComplianceService(db_session)
        
        report = await compliance_service.generate_compliance_report(
            space_id=request.space_id,
            frameworks=request.frameworks,
            include_recommendations=request.include_recommendations,
            format=request.format
        )
        
        logger.info("Compliance report generated", 
                   space_id=request.space_id, report_id=report.report_id, score=report.overall_score)
        
        return {
            "success": True,
            "message": "Compliance report generated successfully",
            "report": report.dict()
        }
        
    except ValueError as e:
        logger.warning("Invalid compliance report request", 
                      space_id=request.space_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to generate compliance report", 
                    space_id=request.space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.get("/reports/{space_id}")
async def get_compliance_reports(
    space_id: str,
    limit: int = 10,
    db_session=Depends(get_db),
    current_user: dict = Depends(require_space_permission(SpacePermission.READ))
):
    """
    Get compliance reports for a project space.
    Requires READ permission.
    """
    logger.info("Getting compliance reports", space_id=space_id, limit=limit, user_id=current_user.get("user_id"))
    
    try:
        compliance_service = ComplianceService(db_session)
        
        reports = await compliance_service.get_compliance_reports(space_id, limit)
        
        logger.info("Compliance reports retrieved", space_id=space_id, count=len(reports))
        
        return {
            "success": True,
            "reports": [r.dict() for r in reports],
            "total": len(reports)
        }
        
    except Exception as e:
        logger.error("Failed to get compliance reports", 
                    space_id=space_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance reports: {str(e)}"
        )


@router.get("/frameworks")
async def get_available_frameworks():
    """
    Get list of available compliance frameworks and their requirements.
    No authentication required.
    """
    logger.info("Getting available compliance frameworks")
    
    try:
        from models.compliance import COMPLIANCE_REQUIREMENTS_REGISTRY
        
        frameworks_info = {}
        for framework, requirements in COMPLIANCE_REQUIREMENTS_REGISTRY.items():
            frameworks_info[framework.value] = {
                "name": framework.value,
                "description": _get_framework_description(framework),
                "requirements_count": len(requirements),
                "requirements": [req.dict() for req in requirements]
            }
        
        return {
            "success": True,
            "frameworks": frameworks_info
        }
        
    except Exception as e:
        logger.error("Failed to get available frameworks", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available frameworks: {str(e)}"
        )


@router.get("/data-categories")
async def get_data_categories():
    """
    Get list of available data categories.
    No authentication required.
    """
    logger.info("Getting available data categories")
    
    try:
        categories = []
        for category in DataCategory:
            categories.append({
                "value": category.value,
                "name": category.value.replace("_", " ").title(),
                "description": _get_data_category_description(category)
            })
        
        return {
            "success": True,
            "categories": categories
        }
        
    except Exception as e:
        logger.error("Failed to get data categories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data categories: {str(e)}"
        )


def _get_framework_description(framework: ComplianceFramework) -> str:
    """Get description for a compliance framework"""
    descriptions = {
        ComplianceFramework.GDPR: "General Data Protection Regulation - EU data protection and privacy regulation",
        ComplianceFramework.HIPAA: "Health Insurance Portability and Accountability Act - US healthcare data protection",
        ComplianceFramework.SOX: "Sarbanes-Oxley Act - US financial reporting and corporate governance",
        ComplianceFramework.PCI_DSS: "Payment Card Industry Data Security Standard - Credit card data protection",
        ComplianceFramework.ISO27001: "ISO/IEC 27001 - International standard for information security management",
        ComplianceFramework.CCPA: "California Consumer Privacy Act - California data protection regulation",
        ComplianceFramework.FERPA: "Family Educational Rights and Privacy Act - US educational records protection",
        ComplianceFramework.CUSTOM: "Custom compliance framework - User-defined requirements"
    }
    return descriptions.get(framework, "Compliance framework")


def _get_data_category_description(category: DataCategory) -> str:
    """Get description for a data category"""
    descriptions = {
        DataCategory.PERSONAL_DATA: "Personal information that can identify an individual",
        DataCategory.SENSITIVE_PERSONAL_DATA: "Highly sensitive personal information requiring special protection",
        DataCategory.FINANCIAL_DATA: "Financial information including transactions, accounts, and payment data",
        DataCategory.HEALTH_DATA: "Health and medical information protected by healthcare regulations",
        DataCategory.BUSINESS_DATA: "Business information including trade secrets and proprietary data",
        DataCategory.PUBLIC_DATA: "Publicly available information with no privacy restrictions"
    }
    return descriptions.get(category, "Data category")
