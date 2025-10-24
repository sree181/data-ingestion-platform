"""
Security Alerts and Notifications API Routes
Comprehensive security alerting and notification systems
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import structlog

from models.security_alerts import (
    AlertRequest, AlertUpdateRequest, AlertRuleRequest, AlertQuery, AlertStats,
    NotificationRequest, EscalationRequest, SuppressionRequest, SecurityAlert,
    AlertRule, NotificationTemplate, NotificationSubscription, AlertCorrelation,
    AlertSuppression, AlertSeverity, AlertStatus, AlertCategory, AlertSource,
    NotificationChannel, EscalationLevel
)
from services.security_alerts_service import SecurityAlertsService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/security-alerts", tags=["Security Alerts"])

# Initialize service
alerts_service = SecurityAlertsService()

@router.post("/create", response_model=SecurityAlert)
async def create_alert(request: AlertRequest):
    """
    Create a new security alert
    """
    try:
        logger.info("Creating security alert", title=request.title, severity=request.severity.value)
        
        alert = await alerts_service.create_alert(request)
        
        if alert:
            logger.info("Security alert created successfully", 
                       alert_id=str(alert.id),
                       title=alert.title,
                       severity=alert.severity.value)
            return alert
        else:
            # Alert was suppressed
            return JSONResponse(
                status_code=200,
                content={"message": "Alert suppressed", "suppressed": True}
            )
        
    except Exception as e:
        logger.error("Security alert creation failed", 
                    title=request.title, 
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security alert creation failed: {str(e)}"
        )

@router.put("/update/{alert_id}", response_model=SecurityAlert)
async def update_alert(
    alert_id: str,
    request: AlertUpdateRequest,
    user_id: str = Query(..., description="User ID updating the alert")
):
    """
    Update an existing security alert
    """
    try:
        logger.info("Updating security alert", alert_id=alert_id, user_id=user_id)
        
        alert = await alerts_service.update_alert(alert_id, request, user_id)
        
        logger.info("Security alert updated successfully", 
                   alert_id=alert_id,
                   status=alert.status.value,
                   updated_by=user_id)
        
        return alert
        
    except ValueError as e:
        logger.warning("Alert not found for update", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Security alert update failed", 
                    alert_id=alert_id,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security alert update failed: {str(e)}"
        )

@router.get("/alerts", response_model=dict)
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None),
    category: Optional[AlertCategory] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    source: Optional[AlertSource] = Query(None),
    user_id: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get security alerts with filtering
    """
    try:
        query = AlertQuery(
            severity=severity,
            category=category,
            status=status,
            source=source,
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        alerts, total_count = await alerts_service.get_alerts(query)
        
        return {
            "alerts": alerts,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(alerts) < total_count
        }
        
    except Exception as e:
        logger.error("Failed to get security alerts", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security alerts: {str(e)}"
        )

@router.get("/statistics", response_model=AlertStats)
async def get_alert_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get security alert statistics
    """
    try:
        stats = await alerts_service.get_alert_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get alert statistics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert statistics: {str(e)}"
        )

@router.post("/rules", response_model=AlertRule)
async def create_alert_rule(
    request: AlertRuleRequest,
    user_id: str = Query(..., description="User ID creating the rule")
):
    """
    Create a new alert rule
    """
    try:
        logger.info("Creating alert rule", rule_name=request.name, user_id=user_id)
        
        rule = await alerts_service.create_alert_rule(request, user_id)
        
        logger.info("Alert rule created successfully", 
                   rule_id=str(rule.id), 
                   rule_name=rule.name)
        
        return rule
        
    except Exception as e:
        logger.error("Failed to create alert rule", 
                    rule_name=request.name,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert rule: {str(e)}"
        )

@router.get("/rules", response_model=List[AlertRule])
async def get_alert_rules(
    enabled_only: bool = Query(True, description="Return only enabled rules")
):
    """
    Get all alert rules
    """
    try:
        rules = list(alerts_service.alert_rules.values())
        
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        
        return rules
        
    except Exception as e:
        logger.error("Failed to get alert rules", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert rules: {str(e)}"
        )

@router.post("/notifications/send")
async def send_notification(request: NotificationRequest):
    """
    Send notification for an alert
    """
    try:
        logger.info("Sending notification", 
                   alert_id=request.alert_id,
                   channels=[ch.value for ch in request.channels])
        
        success = await alerts_service.send_notification(request)
        
        if success:
            logger.info("Notification sent successfully", alert_id=request.alert_id)
            return {"success": True, "message": "Notification sent successfully"}
        else:
            logger.warning("Some notifications failed", alert_id=request.alert_id)
            return {"success": False, "message": "Some notifications failed"}
        
    except ValueError as e:
        logger.warning("Alert not found for notification", alert_id=request.alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Notification sending failed", 
                    alert_id=request.alert_id,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification sending failed: {str(e)}"
        )

@router.post("/escalate")
async def escalate_alert(request: EscalationRequest):
    """
    Escalate an alert
    """
    try:
        logger.info("Escalating alert", 
                   alert_id=request.alert_id,
                   escalation_level=request.escalation_level.value,
                   escalated_by=request.escalated_by)
        
        alert = await alerts_service.escalate_alert(request)
        
        logger.info("Alert escalated successfully", 
                   alert_id=request.alert_id,
                   escalation_level=alert.escalation_level.value)
        
        return alert
        
    except ValueError as e:
        logger.warning("Alert not found for escalation", alert_id=request.alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Alert escalation failed", 
                    alert_id=request.alert_id,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert escalation failed: {str(e)}"
        )

@router.post("/suppress")
async def create_suppression(request: SuppressionRequest):
    """
    Create alert suppression rule
    """
    try:
        logger.info("Creating alert suppression", 
                   condition=request.condition,
                   suppressed_by=request.suppressed_by)
        
        suppression = await alerts_service.create_suppression(request)
        
        logger.info("Alert suppression created successfully", 
                   suppression_id=str(suppression.id),
                   condition=suppression.condition)
        
        return suppression
        
    except Exception as e:
        logger.error("Failed to create alert suppression", 
                    condition=request.condition,
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert suppression: {str(e)}"
        )

@router.post("/process-rules")
async def process_alert_rules(event_data: dict):
    """
    Process alert rules against event data
    """
    try:
        logger.info("Processing alert rules", event_keys=list(event_data.keys()))
        
        triggered_alerts = await alerts_service.process_alert_rules(event_data)
        
        logger.info("Alert rules processed", 
                   triggered_count=len(triggered_alerts))
        
        return {
            "triggered_alerts": triggered_alerts,
            "count": len(triggered_alerts)
        }
        
    except Exception as e:
        logger.error("Alert rule processing failed", 
                    error=str(e), 
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert rule processing failed: {str(e)}"
        )

@router.get("/templates", response_model=List[NotificationTemplate])
async def get_notification_templates(
    channel: Optional[NotificationChannel] = Query(None, description="Filter by notification channel"),
    enabled_only: bool = Query(True, description="Return only enabled templates")
):
    """
    Get notification templates
    """
    try:
        templates = list(alerts_service.notification_templates.values())
        
        if channel:
            templates = [t for t in templates if t.channel == channel]
        
        if enabled_only:
            templates = [t for t in templates if t.enabled]
        
        return templates
        
    except Exception as e:
        logger.error("Failed to get notification templates", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification templates: {str(e)}"
        )

@router.get("/subscriptions", response_model=List[NotificationSubscription])
async def get_notification_subscriptions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    enabled_only: bool = Query(True, description="Return only enabled subscriptions")
):
    """
    Get notification subscriptions
    """
    try:
        subscriptions = list(alerts_service.notification_subscriptions.values())
        
        if user_id:
            subscriptions = [s for s in subscriptions if s.user_id == user_id]
        
        if enabled_only:
            subscriptions = [s for s in subscriptions if s.enabled]
        
        return subscriptions
        
    except Exception as e:
        logger.error("Failed to get notification subscriptions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification subscriptions: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check for security alerts service
    """
    try:
        # Check if service is operational
        rules_count = len(alerts_service.alert_rules)
        templates_count = len(alerts_service.notification_templates)
        subscriptions_count = len(alerts_service.notification_subscriptions)
        suppressions_count = len(alerts_service.alert_suppressions)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rules_count": rules_count,
            "templates_count": templates_count,
            "subscriptions_count": subscriptions_count,
            "suppressions_count": suppressions_count,
            "correlation_engine_enabled": alerts_service.correlation_engine_enabled,
            "escalation_engine_enabled": alerts_service.escalation_engine_enabled,
            "notification_engine_enabled": alerts_service.notification_engine_enabled
        }
        
    except Exception as e:
        logger.error("Security alerts health check failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Security alerts service is unhealthy: {str(e)}"
        )

@router.get("/enums")
async def get_alert_enums():
    """
    Get all alert enums for frontend
    """
    return {
        "alert_severities": [severity.value for severity in AlertSeverity],
        "alert_statuses": [status.value for status in AlertStatus],
        "alert_categories": [category.value for category in AlertCategory],
        "alert_sources": [source.value for source in AlertSource],
        "notification_channels": [channel.value for channel in NotificationChannel],
        "escalation_levels": [level.value for level in EscalationLevel]
    }

@router.get("/dashboard")
async def get_alerts_dashboard():
    """
    Get data for alerts dashboard
    """
    try:
        # Get recent statistics
        stats = await alerts_service.get_alert_statistics()
        
        # Get active rules and templates
        active_rules = [rule for rule in alerts_service.alert_rules.values() if rule.enabled]
        active_templates = [template for template in alerts_service.notification_templates.values() if template.enabled]
        active_subscriptions = [sub for sub in alerts_service.notification_subscriptions.values() if sub.enabled]
        
        return {
            "statistics": stats,
            "active_rules_count": len(active_rules),
            "active_templates_count": len(active_templates),
            "active_subscriptions_count": len(active_subscriptions),
            "service_status": {
                "correlation_engine_enabled": alerts_service.correlation_engine_enabled,
                "escalation_engine_enabled": alerts_service.escalation_engine_enabled,
                "notification_engine_enabled": alerts_service.notification_engine_enabled
            }
        }
        
    except Exception as e:
        logger.error("Failed to get alerts dashboard data", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts dashboard data: {str(e)}"
        )

@router.get("/correlations")
async def get_alert_correlations(
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get alert correlations
    """
    try:
        # Mock correlation data - in production, this would query the database
        correlations = [
            {
                "correlation_id": "corr_user123_192.168.1.100_authentication",
                "alert_count": 3,
                "pattern_description": "Multiple authentication alerts from user user123 at IP 192.168.1.100",
                "correlation_score": 0.85,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "correlation_id": "corr_user456_10.0.0.50_data_access",
                "alert_count": 2,
                "pattern_description": "Data access alerts from user user456 at IP 10.0.0.50",
                "correlation_score": 0.72,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        if correlation_id:
            correlations = [c for c in correlations if c["correlation_id"] == correlation_id]
        
        return {
            "correlations": correlations[offset:offset + limit],
            "total_count": len(correlations),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to get alert correlations", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert correlations: {str(e)}"
        )

@router.get("/suppressions")
async def get_alert_suppressions(
    active_only: bool = Query(True, description="Return only active suppressions"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get alert suppressions
    """
    try:
        suppressions = list(alerts_service.alert_suppressions.values())
        
        if active_only:
            suppressions = [s for s in suppressions if s.is_active]
        
        return {
            "suppressions": suppressions[offset:offset + limit],
            "total_count": len(suppressions),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to get alert suppressions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert suppressions: {str(e)}"
        )
