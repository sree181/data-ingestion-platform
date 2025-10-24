"""
Enhanced Audit Logging API Routes
Comprehensive security event tracking and monitoring endpoints
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import StreamingResponse
import structlog

from models.audit_logging import (
    AuditEvent, AuditEventType, AuditSeverity, AuditCategory,
    AuditContext, AuditLogQuery, AuditLogResponse, AuditLogStats,
    AuditLogRetentionPolicy, AuditLogAlert, AuditLogExport
)
from services.audit_logging_service import AuditLoggingService
from auth.jwt_auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Logging"])

# Initialize audit logging service
audit_service = AuditLoggingService()

@router.post("/log", response_model=Dict[str, Any])
async def log_audit_event(
    event_type: AuditEventType,
    event_description: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    space_id: Optional[str] = None,
    space_name: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    context: Optional[AuditContext] = None,
    compliance_framework: Optional[str] = None,
    risk_score: Optional[float] = None,
    requires_review: bool = False,
    tags: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Log an audit event
    """
    try:
        event = await audit_service.log_event(
            event_type=event_type,
            event_description=event_description,
            user_id=user_id,
            username=username,
            user_email=user_email,
            session_id=session_id,
            space_id=space_id,
            space_name=space_name,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            event_data=event_data,
            context=context,
            compliance_framework=compliance_framework,
            risk_score=risk_score,
            requires_review=requires_review,
            tags=tags
        )
        
        return {
            "success": True,
            "event_id": str(event.id),
            "message": "Audit event logged successfully"
        }
        
    except Exception as e:
        logger.error("Failed to log audit event", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log audit event: {str(e)}"
        )

@router.get("/events", response_model=AuditLogResponse)
async def get_audit_events(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    event_types: Optional[List[AuditEventType]] = Query(None, description="Filter by event types"),
    categories: Optional[List[AuditCategory]] = Query(None, description="Filter by categories"),
    severities: Optional[List[AuditSeverity]] = Query(None, description="Filter by severities"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    space_id: Optional[str] = Query(None, description="Filter by space ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    requires_review: Optional[bool] = Query(None, description="Filter by review requirement"),
    compliance_framework: Optional[str] = Query(None, description="Filter by compliance framework"),
    search_text: Optional[str] = Query(None, description="Search in event descriptions"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Query audit events with filters
    """
    try:
        query = AuditLogQuery(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            categories=categories,
            severities=severities,
            user_id=user_id,
            space_id=space_id,
            resource_type=resource_type,
            resource_id=resource_id,
            requires_review=requires_review,
            compliance_framework=compliance_framework,
            search_text=search_text,
            limit=limit,
            offset=offset
        )
        
        response = await audit_service.query_events(query)
        return response
        
    except Exception as e:
        logger.error("Failed to query audit events", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query audit events: {str(e)}"
        )

@router.get("/statistics", response_model=AuditLogStats)
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    space_id: Optional[str] = Query(None, description="Filter by space ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit log statistics
    """
    try:
        stats = await audit_service.get_statistics(
            start_date=start_date,
            end_date=end_date,
            space_id=space_id
        )
        return stats
        
    except Exception as e:
        logger.error("Failed to get audit statistics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )

@router.post("/retention-policies", response_model=AuditLogRetentionPolicy)
async def create_retention_policy(
    policy: AuditLogRetentionPolicy,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a log retention policy
    """
    try:
        # Set created_by to current user
        policy.created_by = current_user.get("user_id", "system")
        
        created_policy = await audit_service.create_retention_policy(policy)
        return created_policy
        
    except Exception as e:
        logger.error("Failed to create retention policy", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create retention policy: {str(e)}"
        )

@router.post("/alerts", response_model=AuditLogAlert)
async def create_alert(
    alert: AuditLogAlert,
    current_user: dict = Depends(get_current_user)
):
    """
    Create an audit log alert
    """
    try:
        # Set created_by to current user
        alert.created_by = current_user.get("user_id", "system")
        
        created_alert = await audit_service.create_alert(alert)
        return created_alert
        
    except Exception as e:
        logger.error("Failed to create alert", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )

@router.post("/export", response_model=AuditLogExport)
async def export_audit_events(
    export_config: AuditLogExport,
    current_user: dict = Depends(get_current_user)
):
    """
    Export audit events to file
    """
    try:
        # Set created_by to current user
        export_config.created_by = current_user.get("user_id", "system")
        
        export_result = await audit_service.export_events(export_config)
        return export_result
        
    except Exception as e:
        logger.error("Failed to export audit events", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit events: {str(e)}"
        )

@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific audit event by ID
    """
    try:
        # Query for specific event
        query = AuditLogQuery(limit=1)
        query.event_types = None  # Remove type filtering
        
        # This is a simplified approach - in production, you'd want a more efficient query
        response = await audit_service.query_events(query)
        
        # Find the specific event
        for event in response.events:
            if str(event.id) == event_id:
                return event
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit event not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get audit event", event_id=event_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit event: {str(e)}"
        )

@router.get("/events/requiring-review", response_model=AuditLogResponse)
async def get_events_requiring_review(
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get events requiring manual review
    """
    try:
        query = AuditLogQuery(
            requires_review=True,
            limit=limit,
            offset=offset
        )
        
        response = await audit_service.query_events(query)
        return response
        
    except Exception as e:
        logger.error("Failed to get events requiring review", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events requiring review: {str(e)}"
        )

@router.get("/events/high-risk", response_model=AuditLogResponse)
async def get_high_risk_events(
    min_risk_score: float = Query(7.0, ge=0.0, le=10.0, description="Minimum risk score"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get high-risk events
    """
    try:
        # Query for high-risk events
        query = AuditLogQuery(
            limit=limit,
            offset=offset
        )
        
        response = await audit_service.query_events(query)
        
        # Filter by risk score (this should be done in the database query in production)
        high_risk_events = [
            event for event in response.events 
            if event.risk_score and event.risk_score >= min_risk_score
        ]
        
        return AuditLogResponse(
            events=high_risk_events,
            total_count=len(high_risk_events),
            has_more=len(high_risk_events) == limit,
            query_params=query
        )
        
    except Exception as e:
        logger.error("Failed to get high-risk events", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get high-risk events: {str(e)}"
        )

@router.get("/events/recent", response_model=AuditLogResponse)
async def get_recent_events(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent events within specified hours
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=hours)
        
        query = AuditLogQuery(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=0
        )
        
        response = await audit_service.query_events(query)
        return response
        
    except Exception as e:
        logger.error("Failed to get recent events", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent events: {str(e)}"
        )

@router.get("/events/export/{export_id}")
async def download_export(
    export_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download exported audit events file
    """
    try:
        # TODO: Implement actual file download
        # This would retrieve the file from storage and stream it
        
        return {"message": "Export download not yet implemented", "export_id": export_id}
        
    except Exception as e:
        logger.error("Failed to download export", export_id=export_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}"
        )

@router.get("/health")
async def audit_health_check():
    """
    Health check for audit logging service
    """
    try:
        # Check if audit service is responsive
        stats = await audit_service.get_statistics()
        
        return {
            "status": "healthy",
            "service": "audit-logging",
            "total_events": stats.total_events,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Audit health check failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Audit logging service unhealthy: {str(e)}"
        )

# Convenience endpoints for common audit events
@router.post("/log/login-success")
async def log_login_success(
    user_id: str,
    username: str,
    user_email: str,
    session_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log successful login"""
    context = AuditContext(
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id
    )
    
    return await log_audit_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        event_description=f"User {username} logged in successfully",
        user_id=user_id,
        username=username,
        user_email=user_email,
        session_id=session_id,
        context=context,
        current_user=current_user
    )

@router.post("/log/login-failure")
async def log_login_failure(
    username: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    failure_reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log failed login attempt"""
    context = AuditContext(
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    event_data = {"failure_reason": failure_reason} if failure_reason else None
    
    return await log_audit_event(
        event_type=AuditEventType.LOGIN_FAILURE,
        event_description=f"Failed login attempt for user {username}",
        username=username,
        context=context,
        event_data=event_data,
        current_user=current_user
    )

@router.post("/log/document-access")
async def log_document_access(
    user_id: str,
    username: str,
    space_id: str,
    space_name: str,
    resource_type: str,
    resource_id: str,
    resource_name: str,
    access_type: str,  # view, download, upload, modify, delete
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log document access event"""
    context = AuditContext(
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    event_type_mapping = {
        "view": AuditEventType.DOCUMENT_VIEW,
        "download": AuditEventType.DOCUMENT_DOWNLOAD,
        "upload": AuditEventType.DOCUMENT_UPLOAD,
        "modify": AuditEventType.DOCUMENT_MODIFY,
        "delete": AuditEventType.DOCUMENT_DELETE
    }
    
    event_type = event_type_mapping.get(access_type, AuditEventType.DOCUMENT_VIEW)
    
    return await log_audit_event(
        event_type=event_type,
        event_description=f"User {username} {access_type}ed {resource_name}",
        user_id=user_id,
        username=username,
        space_id=space_id,
        space_name=space_name,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        context=context,
        current_user=current_user
    )

@router.post("/log/security-event")
async def log_security_event(
    event_type: AuditEventType,
    event_description: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    space_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log security-related event"""
    context = AuditContext(
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return await log_audit_event(
        event_type=event_type,
        event_description=event_description,
        user_id=user_id,
        username=username,
        space_id=space_id,
        context=context,
        event_data=event_data,
        current_user=current_user
    )
