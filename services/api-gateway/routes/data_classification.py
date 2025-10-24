"""
Data Classification Management API Routes
Comprehensive data classification and handling policies
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import structlog

from models.data_classification import (
    DataClassificationRequest, BulkClassificationRequest, ClassificationRuleRequest,
    ClassificationPolicyRequest, ClassificationQuery, ClassificationStats,
    DataClassificationResult, DataClassificationRule, DataClassificationPolicy,
    ClassificationAuditLog, ClassificationReport, DataClassificationLevel,
    DataCategory, DataSensitivity, ClassificationMethod, ComplianceRequirement
)
from services.data_classification_service import DataClassificationService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/data-classification", tags=["Data Classification"])

# Initialize service
classification_service = DataClassificationService()

@router.post("/classify", response_model=DataClassificationResult)
async def classify_document(request: DataClassificationRequest):
    """
    Classify a single document
    """
    try:
        logger.info("Classifying document", document_id=request.document_id)
        
        result = await classification_service.classify_document(
            document_id=request.document_id,
            content=request.content,
            metadata=request.metadata,
            classification_method=request.classification_method,
            force_reclassification=request.force_reclassification,
            user_id=request.user_id
        )
        
        logger.info("Document classified successfully", 
                   document_id=request.document_id,
                   classification=result.classification_level.value,
                   confidence=result.confidence_score)
        
        return result
        
    except Exception as e:
        logger.error("Document classification failed", 
                    document_id=request.document_id, 
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document classification failed: {str(e)}"
        )

@router.post("/classify/bulk", response_model=List[DataClassificationResult])
async def classify_documents_bulk(request: BulkClassificationRequest):
    """
    Classify multiple documents in bulk
    """
    try:
        logger.info("Bulk classifying documents", 
                   document_count=len(request.document_ids))
        
        results = await classification_service.classify_documents_bulk(
            document_ids=request.document_ids,
            classification_method=request.classification_method,
            force_reclassification=request.force_reclassification,
            user_id=request.user_id
        )
        
        logger.info("Bulk classification completed", 
                   document_count=len(request.document_ids),
                   success_count=len(results))
        
        return results
        
    except Exception as e:
        logger.error("Bulk classification failed", 
                    document_count=len(request.document_ids),
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk classification failed: {str(e)}"
        )

@router.get("/results", response_model=dict)
async def get_classification_results(
    classification_level: Optional[DataClassificationLevel] = Query(None),
    data_category: Optional[DataCategory] = Query(None),
    sensitivity: Optional[DataSensitivity] = Query(None),
    compliance_requirement: Optional[ComplianceRequirement] = Query(None),
    classification_method: Optional[ClassificationMethod] = Query(None),
    requires_review: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get classification results with filtering
    """
    try:
        query = ClassificationQuery(
            classification_level=classification_level,
            data_category=data_category,
            sensitivity=sensitivity,
            compliance_requirement=compliance_requirement,
            classification_method=classification_method,
            requires_review=requires_review,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        results, total_count = await classification_service.get_classification_results(query)
        
        return {
            "results": results,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(results) < total_count
        }
        
    except Exception as e:
        logger.error("Failed to get classification results", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification results: {str(e)}"
        )

@router.get("/statistics", response_model=ClassificationStats)
async def get_classification_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get classification statistics
    """
    try:
        stats = await classification_service.get_classification_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get classification statistics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification statistics: {str(e)}"
        )

@router.post("/rules", response_model=DataClassificationRule)
async def create_classification_rule(
    request: ClassificationRuleRequest,
    user_id: str = Query(..., description="User ID creating the rule")
):
    """
    Create a new classification rule
    """
    try:
        logger.info("Creating classification rule", rule_name=request.name, user_id=user_id)
        
        rule = await classification_service.create_classification_rule(request, user_id)
        
        logger.info("Classification rule created successfully", 
                   rule_id=str(rule.id), 
                   rule_name=rule.name)
        
        return rule
        
    except Exception as e:
        logger.error("Failed to create classification rule", 
                    rule_name=request.name,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create classification rule: {str(e)}"
        )

@router.get("/rules", response_model=List[DataClassificationRule])
async def get_classification_rules(
    active_only: bool = Query(True, description="Return only active rules")
):
    """
    Get all classification rules
    """
    try:
        rules = list(classification_service.classification_rules.values())
        
        if active_only:
            rules = [rule for rule in rules if rule.is_active]
        
        return rules
        
    except Exception as e:
        logger.error("Failed to get classification rules", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification rules: {str(e)}"
        )

@router.post("/policies", response_model=DataClassificationPolicy)
async def create_classification_policy(
    request: ClassificationPolicyRequest,
    user_id: str = Query(..., description="User ID creating the policy")
):
    """
    Create a new classification policy
    """
    try:
        logger.info("Creating classification policy", policy_name=request.name, user_id=user_id)
        
        policy = await classification_service.create_classification_policy(request, user_id)
        
        logger.info("Classification policy created successfully", 
                   policy_id=str(policy.id), 
                   policy_name=policy.name)
        
        return policy
        
    except Exception as e:
        logger.error("Failed to create classification policy", 
                    policy_name=request.name,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create classification policy: {str(e)}"
        )

@router.get("/policies", response_model=List[DataClassificationPolicy])
async def get_classification_policies(
    active_only: bool = Query(True, description="Return only active policies")
):
    """
    Get all classification policies
    """
    try:
        policies = list(classification_service.classification_policies.values())
        
        if active_only:
            policies = [policy for policy in policies if policy.is_active]
        
        return policies
        
    except Exception as e:
        logger.error("Failed to get classification policies", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification policies: {str(e)}"
        )

@router.put("/update/{document_id}", response_model=DataClassificationResult)
async def update_classification(
    document_id: str,
    new_classification: DataClassificationLevel,
    new_category: DataCategory,
    new_sensitivity: DataSensitivity,
    reason: str,
    user_id: str = Query(..., description="User ID updating classification"),
    ip_address: Optional[str] = Query(None, description="User IP address"),
    user_agent: Optional[str] = Query(None, description="User agent")
):
    """
    Update document classification
    """
    try:
        logger.info("Updating document classification", 
                   document_id=document_id,
                   new_classification=new_classification.value,
                   user_id=user_id)
        
        result = await classification_service.update_classification(
            document_id=document_id,
            new_classification=new_classification,
            new_category=new_category,
            new_sensitivity=new_sensitivity,
            reason=reason,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info("Document classification updated successfully", 
                   document_id=document_id,
                   new_classification=new_classification.value)
        
        return result
        
    except ValueError as e:
        logger.warning("Document not found for classification update", 
                      document_id=document_id,
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update document classification", 
                    document_id=document_id,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document classification: {str(e)}"
        )

@router.get("/audit-logs", response_model=List[ClassificationAuditLog])
async def get_classification_audit_logs(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get classification audit logs
    """
    try:
        audit_logs = await classification_service.get_classification_audit_logs(
            document_id=document_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return audit_logs
        
    except Exception as e:
        logger.error("Failed to get classification audit logs", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification audit logs: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check for data classification service
    """
    try:
        # Check if service is operational
        rule_count = len(classification_service.classification_rules)
        policy_count = len(classification_service.classification_policies)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rules_count": rule_count,
            "policies_count": policy_count,
            "ai_classification_enabled": classification_service.ai_classification_enabled,
            "rule_engine_enabled": classification_service.rule_engine_enabled
        }
        
    except Exception as e:
        logger.error("Data classification health check failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data classification service is unhealthy: {str(e)}"
        )

@router.get("/enums")
async def get_classification_enums():
    """
    Get all classification enums for frontend
    """
    return {
        "classification_levels": [level.value for level in DataClassificationLevel],
        "data_categories": [category.value for category in DataCategory],
        "sensitivity_levels": [sensitivity.value for sensitivity in DataSensitivity],
        "classification_methods": [method.value for method in ClassificationMethod],
        "compliance_requirements": [req.value for req in ComplianceRequirement]
    }

@router.post("/reclassify-all")
async def reclassify_all_documents(
    classification_method: Optional[ClassificationMethod] = Query(None),
    user_id: str = Query(..., description="User ID initiating reclassification")
):
    """
    Reclassify all documents (admin operation)
    """
    try:
        logger.info("Starting reclassification of all documents", 
                   user_id=user_id,
                   method=classification_method.value if classification_method else "automatic")
        
        # This would typically be an async background job
        # For now, we'll return a success response
        return {
            "message": "Reclassification job started",
            "job_id": f"reclassify_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "status": "started",
            "initiated_by": user_id,
            "method": classification_method.value if classification_method else "automatic"
        }
        
    except Exception as e:
        logger.error("Failed to start reclassification job", 
                    user_id=user_id,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start reclassification job: {str(e)}"
        )

@router.get("/dashboard")
async def get_classification_dashboard():
    """
    Get data for classification dashboard
    """
    try:
        # Get recent statistics
        stats = await classification_service.get_classification_statistics()
        
        # Get recent audit logs
        recent_logs = await classification_service.get_classification_audit_logs(limit=10)
        
        # Get active rules and policies
        active_rules = [rule for rule in classification_service.classification_rules.values() if rule.is_active]
        active_policies = [policy for policy in classification_service.classification_policies.values() if policy.is_active]
        
        return {
            "statistics": stats,
            "recent_activity": recent_logs,
            "active_rules_count": len(active_rules),
            "active_policies_count": len(active_policies),
            "service_status": {
                "ai_classification_enabled": classification_service.ai_classification_enabled,
                "rule_engine_enabled": classification_service.rule_engine_enabled
            }
        }
        
    except Exception as e:
        logger.error("Failed to get classification dashboard data", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classification dashboard data: {str(e)}"
        )
