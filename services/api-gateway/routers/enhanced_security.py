"""
Enhanced Security API Endpoints
Integrates all security features: encryption, compliance, monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from models.security_models import User, Project
from auth.enhanced_auth import get_current_user, EnhancedAuthService
from security.encryption_service import EnterpriseEncryptionService, DocumentEncryptionManager
from compliance.compliance_engine import EnterpriseComplianceEngine, ComplianceFramework
from monitoring.security_monitor import SecurityIntegrationService
from database import get_db

router = APIRouter(prefix="/api/v1/security", tags=["Enhanced Security"])

@router.get("/dashboard", response_model=Dict)
async def get_security_dashboard(
    project_id: Optional[int] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive security dashboard"""
    
    # Initialize services
    compliance_engine = EnterpriseComplianceEngine(db)
    encryption_service = EnterpriseEncryptionService(db, "master-key-password")  # TODO: Use env var
    security_monitor = SecurityIntegrationService(db)
    
    # Get compliance dashboard
    compliance_data = compliance_engine.get_compliance_dashboard(project_id)
    
    # Get encryption metrics
    encryption_metrics = encryption_service.get_encryption_metrics(project_id)
    
    # Get security monitoring metrics
    monitoring_metrics = security_monitor.monitor.get_security_metrics(project_id)
    
    # Get active alerts
    active_alerts = security_monitor.monitor.get_active_alerts(project_id)
    
    return {
        "compliance": compliance_data,
        "encryption": encryption_metrics,
        "monitoring": monitoring_metrics,
        "active_alerts": active_alerts,
        "dashboard_generated_at": datetime.utcnow().isoformat()
    }

@router.get("/compliance/frameworks", response_model=List[Dict])
async def get_compliance_frameworks(
    current_user: Dict = Depends(get_current_user)
):
    """Get available compliance frameworks"""
    
    frameworks = [
        {
            "id": "sox",
            "name": "SOX (Sarbanes-Oxley)",
            "description": "Financial reporting compliance for public companies",
            "controls_count": 5,
            "industry": "Financial Services"
        },
        {
            "id": "gdpr",
            "name": "GDPR",
            "description": "EU General Data Protection Regulation",
            "controls_count": 5,
            "industry": "All (EU data processing)"
        },
        {
            "id": "hipaa",
            "name": "HIPAA",
            "description": "Healthcare Information Portability and Accountability Act",
            "controls_count": 4,
            "industry": "Healthcare"
        },
        {
            "id": "iso27001",
            "name": "ISO 27001",
            "description": "Information Security Management System",
            "controls_count": 3,
            "industry": "All industries"
        },
        {
            "id": "nist",
            "name": "NIST Cybersecurity Framework",
            "description": "NIST Cybersecurity Framework",
            "controls_count": 3,
            "industry": "All industries"
        }
    ]
    
    return frameworks

@router.post("/compliance/assess", response_model=Dict)
async def assess_compliance(
    assessment_request: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess project compliance against framework"""
    
    project_id = assessment_request.get("project_id")
    framework_id = assessment_request.get("framework")
    
    if not project_id or not framework_id:
        raise HTTPException(status_code=400, detail="project_id and framework are required")
    
    try:
        framework = ComplianceFramework(framework_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid compliance framework")
    
    compliance_engine = EnterpriseComplianceEngine(db)
    assessment_result = compliance_engine.assess_project_compliance(project_id, framework)
    
    return assessment_result

@router.post("/compliance/report", response_model=Dict)
async def generate_compliance_report(
    report_request: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive compliance report"""
    
    project_id = report_request.get("project_id")
    framework_id = report_request.get("framework")
    report_type = report_request.get("report_type", "assessment")
    
    try:
        framework = ComplianceFramework(framework_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid compliance framework")
    
    compliance_engine = EnterpriseComplianceEngine(db)
    report_id = compliance_engine.generate_compliance_report(project_id, framework, report_type)
    
    return {
        "report_id": report_id,
        "status": "generated",
        "download_url": f"/api/v1/security/compliance/report/{report_id}/download"
    }

@router.get("/encryption/keys", response_model=List[Dict])
async def get_encryption_keys(
    project_id: int = Query(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get encryption keys for project"""
    
    encryption_service = EnterpriseEncryptionService(db, "master-key-password")
    keys = encryption_service.get_project_keys(project_id)
    
    return keys

@router.post("/encryption/keys", response_model=Dict)
async def create_encryption_key(
    key_request: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new encryption key for project"""
    
    project_id = key_request.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    
    encryption_service = EnterpriseEncryptionService(db, "master-key-password")
    key_id = encryption_service.create_project_key(project_id, current_user["user_id"])
    
    return {
        "key_id": key_id,
        "status": "created",
        "project_id": project_id
    }

@router.post("/encryption/keys/{key_id}/rotate", response_model=Dict)
async def rotate_encryption_key(
    key_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rotate encryption key"""
    
    encryption_service = EnterpriseEncryptionService(db, "master-key-password")
    new_key_id = encryption_service.rotate_key(key_id, current_user["user_id"])
    
    return {
        "old_key_id": key_id,
        "new_key_id": new_key_id,
        "status": "rotated"
    }

@router.get("/monitoring/alerts", response_model=List[Dict])
async def get_security_alerts(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    threat_level: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security alerts"""
    
    security_monitor = SecurityIntegrationService(db)
    alerts = security_monitor.monitor.get_active_alerts(project_id)
    
    # Filter by status and threat level if provided
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    
    if threat_level:
        alerts = [a for a in alerts if a["threat_level"] == threat_level]
    
    return alerts[:limit]

@router.post("/monitoring/alerts/{alert_id}/resolve", response_model=Dict)
async def resolve_security_alert(
    alert_id: str,
    resolution_data: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve security alert"""
    
    from ..models.security_models import SecurityAlertLog
    
    alert = db.query(SecurityAlertLog).filter(
        SecurityAlertLog.alert_id == alert_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    
    # Add resolution notes if provided
    if "notes" in resolution_data:
        alert.description += f"\n\nResolution Notes: {resolution_data['notes']}"
    
    db.commit()
    
    return {
        "alert_id": alert_id,
        "status": "resolved",
        "resolved_by": current_user["user_id"],
        "resolved_at": alert.resolved_at.isoformat()
    }

@router.post("/monitoring/events", response_model=Dict)
async def log_security_event(
    event_data: Dict = Body(...),
    request: Request = None,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log security event for monitoring"""
    
    # Get client IP
    client_ip = request.client.host if request else "unknown"
    
    security_monitor = SecurityIntegrationService(db)
    security_monitor.log_security_event(
        event_type=event_data.get("event_type"),
        user_id=current_user["user_id"],
        source_ip=client_ip,
        details=event_data.get("details", {}),
        risk_score=event_data.get("risk_score", 0),
        project_id=event_data.get("project_id"),
        resource_type=event_data.get("resource_type"),
        resource_id=event_data.get("resource_id")
    )
    
    return {
        "status": "logged",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/audit/events", response_model=List[Dict])
async def get_audit_events(
    project_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit events"""
    
    from ..models.security_models import AuditLog
    
    query = db.query(AuditLog)
    
    if project_id:
        query = query.filter(AuditLog.project_id == project_id)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if event_type:
        query = query.filter(AuditLog.action == event_type)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(AuditLog.timestamp >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(AuditLog.timestamp <= end_dt)
    
    events = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return [{
        "id": event.id,
        "user_id": event.user_id,
        "project_id": event.project_id,
        "action": event.action.value if hasattr(event.action, 'value') else event.action,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "ip_address": event.ip_address,
        "details": event.details,
        "risk_score": event.risk_score,
        "timestamp": event.timestamp.isoformat()
    } for event in events]

@router.get("/health", response_model=Dict)
async def get_security_health(
    project_id: Optional[int] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall security health status"""
    
    # Initialize services
    compliance_engine = EnterpriseComplianceEngine(db)
    encryption_service = EnterpriseEncryptionService(db, "master-key-password")
    security_monitor = SecurityIntegrationService(db)
    
    # Get health scores
    compliance_data = compliance_engine.get_compliance_dashboard(project_id)
    encryption_metrics = encryption_service.get_encryption_metrics(project_id)
    monitoring_metrics = security_monitor.monitor.get_security_metrics(project_id)
    
    # Calculate overall health score
    compliance_score = compliance_data.get("overall_compliance_score", 0)
    encryption_score = encryption_metrics.get("encryption_health_score", 0)
    
    # Security incidents impact
    critical_alerts = monitoring_metrics.get("critical_alerts", 0)
    security_incident_penalty = min(critical_alerts * 10, 30)  # Max 30 point penalty
    
    overall_score = (compliance_score + encryption_score) / 2 - security_incident_penalty
    overall_score = max(0, min(100, overall_score))  # Clamp between 0-100
    
    # Determine health status
    if overall_score >= 90:
        health_status = "excellent"
    elif overall_score >= 80:
        health_status = "good"
    elif overall_score >= 70:
        health_status = "fair"
    elif overall_score >= 60:
        health_status = "poor"
    else:
        health_status = "critical"
    
    return {
        "overall_score": round(overall_score, 2),
        "health_status": health_status,
        "compliance_score": compliance_score,
        "encryption_score": encryption_score,
        "security_incidents": {
            "critical_alerts": critical_alerts,
            "high_alerts": monitoring_metrics.get("high_alerts", 0),
            "total_alerts_30d": monitoring_metrics.get("total_alerts_30d", 0)
        },
        "recommendations": self._get_health_recommendations(overall_score, compliance_score, encryption_score, critical_alerts),
        "last_updated": datetime.utcnow().isoformat()
    }

def _get_health_recommendations(overall_score: float, compliance_score: float, 
                              encryption_score: float, critical_alerts: int) -> List[str]:
    """Generate health improvement recommendations"""
    recommendations = []
    
    if compliance_score < 80:
        recommendations.append("Improve compliance posture by addressing non-compliant controls")
    
    if encryption_score < 80:
        recommendations.append("Enhance encryption implementation and key management")
    
    if critical_alerts > 0:
        recommendations.append(f"Address {critical_alerts} critical security alerts immediately")
    
    if overall_score < 70:
        recommendations.append("Implement comprehensive security improvement plan")
    
    if overall_score < 90:
        recommendations.append("Conduct security assessment and penetration testing")
    
    return recommendations

@router.get("/reports/executive-summary", response_model=Dict)
async def get_executive_security_summary(
    project_id: Optional[int] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get executive security summary report"""
    
    # Get comprehensive security data
    dashboard_data = await get_security_dashboard(project_id, current_user, db)
    health_data = await get_security_health(project_id, current_user, db)
    
    # Generate executive summary
    summary = {
        "report_title": f"Security Executive Summary - {datetime.utcnow().strftime('%B %Y')}",
        "report_date": datetime.utcnow().isoformat(),
        "project_id": project_id,
        
        "key_metrics": {
            "overall_security_score": health_data["overall_score"],
            "compliance_score": health_data["compliance_score"],
            "encryption_health": health_data["encryption_score"],
            "active_threats": dashboard_data["monitoring"]["critical_alerts"]
        },
        
        "risk_summary": {
            "risk_level": health_data["health_status"],
            "critical_issues": dashboard_data["monitoring"]["critical_alerts"],
            "high_priority_items": len(health_data["recommendations"]),
            "compliance_gaps": 100 - health_data["compliance_score"]
        },
        
        "achievements": [
            f"Maintained {health_data['encryption_score']:.1f}% encryption compliance",
            f"Processed {dashboard_data['monitoring']['total_alerts_30d']} security events",
            "Implemented enterprise-grade security controls"
        ],
        
        "priorities": health_data["recommendations"],
        
        "next_steps": [
            "Continue monitoring security metrics",
            "Address high-priority recommendations",
            "Conduct quarterly security review",
            "Update security policies and procedures"
        ]
    }
    
    return summary
