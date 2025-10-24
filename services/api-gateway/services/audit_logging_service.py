"""
Enhanced Audit Logging Service
Comprehensive security event tracking and monitoring
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_logging import (
    AuditEvent, AuditEventType, AuditSeverity, AuditCategory,
    AuditContext, AuditLogQuery, AuditLogResponse, AuditLogStats,
    AuditLogRetentionPolicy, AuditLogAlert, AuditLogExport
)
# Database will be accessed through the main app's db_manager

logger = structlog.get_logger(__name__)

class AuditLoggingService:
    """Enhanced audit logging service"""
    
    def __init__(self):
        self.logger = logger
        self.retention_policies: Dict[str, AuditLogRetentionPolicy] = {}
        self.alerts: Dict[str, AuditLogAlert] = {}
        self.risk_thresholds = {
            "high_risk_score": 7.0,
            "suspicious_activity_threshold": 5,
            "failed_login_threshold": 3,
            "unauthorized_access_threshold": 1
        }
        
    async def log_event(
        self,
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
        tags: Optional[List[str]] = None
    ) -> AuditEvent:
        """Log an audit event"""
        
        # Determine category and severity
        category = self._get_category_for_event_type(event_type)
        severity = self._calculate_severity(event_type, risk_score, event_data)
        
        # Calculate risk score if not provided
        if risk_score is None:
            risk_score = self._calculate_risk_score(event_type, event_data, context)
        
        # Determine if review is required
        if not requires_review:
            requires_review = self._requires_review(event_type, severity, risk_score)
        
        # Create audit event
        audit_event = AuditEvent(
            event_type=event_type,
            category=category,
            severity=severity,
            user_id=user_id,
            username=username,
            user_email=user_email,
            session_id=session_id,
            space_id=space_id,
            space_name=space_name,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            event_description=event_description,
            event_data=event_data,
            context=context,
            compliance_framework=compliance_framework,
            risk_score=risk_score,
            requires_review=requires_review,
            tags=tags or []
        )
        
        # Store in database
        await self._store_audit_event(audit_event)
        
        # Check for alerts
        await self._check_alerts(audit_event)
        
        # Log to structured logger
        self.logger.info(
            "Audit event logged",
            event_id=str(audit_event.id),
            event_type=event_type.value,
            category=category.value,
            severity=severity.value,
            user_id=user_id,
            space_id=space_id,
            risk_score=risk_score,
            requires_review=requires_review
        )
        
        return audit_event
    
    async def query_events(self, query: AuditLogQuery) -> AuditLogResponse:
        """Query audit events with filters"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build SQL query
            sql_query = self._build_query_sql(query)
            params = self._build_query_params(query)
            
            # Execute query
            result = await db.execute(text(sql_query), params)
            rows = result.fetchall()
            
            # Get total count
            count_sql = self._build_count_sql(query)
            count_result = await db.execute(text(count_sql), params)
            total_count = count_result.scalar()
            
            # Convert rows to AuditEvent objects
            events = []
            for row in rows:
                event_data = json.loads(row.event_data) if row.event_data else None
                context_data = json.loads(row.context) if row.context else None
                
                event = AuditEvent(
                    id=row.id,
                    event_type=AuditEventType(row.event_type),
                    category=AuditCategory(row.category),
                    severity=AuditSeverity(row.severity),
                    timestamp=row.timestamp,
                    user_id=row.user_id,
                    username=row.username,
                    user_email=row.user_email,
                    session_id=row.session_id,
                    space_id=row.space_id,
                    space_name=row.space_name,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    resource_name=row.resource_name,
                    event_description=row.event_description,
                    event_data=event_data,
                    context=AuditContext(**context_data) if context_data else None,
                    compliance_framework=row.compliance_framework,
                    risk_score=row.risk_score,
                    requires_review=row.requires_review,
                    service_name=row.service_name,
                    version=row.version,
                    environment=row.environment,
                    tags=json.loads(row.tags) if row.tags else [],
                    retention_days=row.retention_days,
                    archived=row.archived
                )
                events.append(event)
            
            return AuditLogResponse(
                events=events,
                total_count=total_count,
                has_more=len(events) == query.limit,
                query_params=query
            )
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        space_id: Optional[str] = None
    ) -> AuditLogStats:
        """Get audit log statistics"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build base WHERE clause
            where_conditions = []
            params = {}
            
            if start_date:
                where_conditions.append("timestamp >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                where_conditions.append("timestamp <= :end_date")
                params["end_date"] = end_date
            
            if space_id:
                where_conditions.append("space_id = :space_id")
                params["space_id"] = space_id
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Get statistics
            stats_queries = {
                "total_events": f"SELECT COUNT(*) FROM enhanced_audit_logs WHERE {where_clause}",
                "events_by_type": f"SELECT event_type, COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} GROUP BY event_type",
                "events_by_category": f"SELECT category, COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} GROUP BY category",
                "events_by_severity": f"SELECT severity, COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} GROUP BY severity",
                "events_by_user": f"SELECT user_id, COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} AND user_id IS NOT NULL GROUP BY user_id",
                "events_by_space": f"SELECT space_id, COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} AND space_id IS NOT NULL GROUP BY space_id",
                "high_risk_events": f"SELECT COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} AND risk_score >= :high_risk_threshold",
                "events_requiring_review": f"SELECT COUNT(*) FROM enhanced_audit_logs WHERE {where_clause} AND requires_review = true"
            }
            
            params["high_risk_threshold"] = self.risk_thresholds["high_risk_score"]
            
            results = {}
            for stat_name, query in stats_queries.items():
                if stat_name in ["events_by_type", "events_by_category", "events_by_severity", "events_by_user", "events_by_space"]:
                    result = await db.execute(text(query), params)
                    rows = result.fetchall()
                    results[stat_name] = {row[0]: row[1] for row in rows}
                else:
                    result = await db.execute(text(query), params)
                    results[stat_name] = result.scalar()
            
            # Get time range
            time_range_query = f"SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM enhanced_audit_logs WHERE {where_clause}"
            time_result = await db.execute(text(time_range_query), params)
            time_row = time_result.fetchone()
            
            return AuditLogStats(
                total_events=results["total_events"],
                events_by_type=results["events_by_type"],
                events_by_category=results["events_by_category"],
                events_by_severity=results["events_by_severity"],
                events_by_user=results["events_by_user"],
                events_by_space=results["events_by_space"],
                high_risk_events=results["high_risk_events"],
                events_requiring_review=results["events_requiring_review"],
                time_range={
                    "start": time_row.min_time if time_row else None,
                    "end": time_row.max_time if time_row else None
                }
            )
    
    async def create_retention_policy(self, policy: AuditLogRetentionPolicy) -> AuditLogRetentionPolicy:
        """Create a log retention policy"""
        
        self.retention_policies[policy.policy_name] = policy
        
        # Store in database
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO audit_retention_policies 
                (policy_name, description, event_types, categories, retention_days, 
                 archive_after_days, delete_after_days, compress_after_days, 
                 is_active, created_by, created_at)
                VALUES (:policy_name, :description, :event_types, :categories, :retention_days,
                        :archive_after_days, :delete_after_days, :compress_after_days,
                        :is_active, :created_by, :created_at)
            """), {
                "policy_name": policy.policy_name,
                "description": policy.description,
                "event_types": json.dumps([t.value for t in policy.event_types]),
                "categories": json.dumps([c.value for c in policy.categories]),
                "retention_days": policy.retention_days,
                "archive_after_days": policy.archive_after_days,
                "delete_after_days": policy.delete_after_days,
                "compress_after_days": policy.compress_after_days,
                "is_active": policy.is_active,
                "created_by": policy.created_by,
                "created_at": policy.created_at
            })
            await db.commit()
        
        self.logger.info("Retention policy created", policy_name=policy.policy_name)
        return policy
    
    async def create_alert(self, alert: AuditLogAlert) -> AuditLogAlert:
        """Create an audit log alert"""
        
        self.alerts[alert.alert_name] = alert
        
        # Store in database
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO audit_alerts 
                (alert_name, description, event_types, conditions, threshold, 
                 time_window_minutes, severity, is_active, notification_channels, 
                 escalation_rules, created_by, created_at)
                VALUES (:alert_name, :description, :event_types, :conditions, :threshold,
                        :time_window_minutes, :severity, :is_active, :notification_channels,
                        :escalation_rules, :created_by, :created_at)
            """), {
                "alert_name": alert.alert_name,
                "description": alert.description,
                "event_types": json.dumps([t.value for t in alert.event_types]),
                "conditions": json.dumps(alert.conditions),
                "threshold": alert.threshold,
                "time_window_minutes": alert.time_window_minutes,
                "severity": alert.severity.value,
                "is_active": alert.is_active,
                "notification_channels": json.dumps(alert.notification_channels),
                "escalation_rules": json.dumps(alert.escalation_rules) if alert.escalation_rules else None,
                "created_by": alert.created_by,
                "created_at": alert.created_at
            })
            await db.commit()
        
        self.logger.info("Audit alert created", alert_name=alert.alert_name)
        return alert
    
    async def export_events(self, export_config: AuditLogExport) -> AuditLogExport:
        """Export audit events to file"""
        
        # Query events
        query_response = await self.query_events(export_config.query_params)
        
        # Generate export file
        export_file = await self._generate_export_file(export_config, query_response.events)
        
        # Update export status
        export_config.status = "completed"
        export_config.file_path = export_file["file_path"]
        export_config.file_size = export_file["file_size"]
        
        # Store export record
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO audit_exports 
                (export_id, query_params, export_format, include_context, include_event_data,
                 compression, password_protected, created_by, created_at, status, file_path, file_size)
                VALUES (:export_id, :query_params, :export_format, :include_context, :include_event_data,
                        :compression, :password_protected, :created_by, :created_at, :status, :file_path, :file_size)
            """), {
                "export_id": str(export_config.export_id),
                "query_params": json.dumps(export_config.query_params.dict()),
                "export_format": export_config.export_format,
                "include_context": export_config.include_context,
                "include_event_data": export_config.include_event_data,
                "compression": export_config.compression,
                "password_protected": export_config.password_protected,
                "created_by": export_config.created_by,
                "created_at": export_config.created_at,
                "status": export_config.status,
                "file_path": export_config.file_path,
                "file_size": export_config.file_size
            })
            await db.commit()
        
        self.logger.info("Audit events exported", export_id=str(export_config.export_id))
        return export_config
    
    def _get_category_for_event_type(self, event_type: AuditEventType) -> AuditCategory:
        """Get category for event type"""
        category_mapping = {
            # Authentication
            AuditEventType.LOGIN_SUCCESS: AuditCategory.AUTHENTICATION,
            AuditEventType.LOGIN_FAILURE: AuditCategory.AUTHENTICATION,
            AuditEventType.LOGOUT: AuditCategory.AUTHENTICATION,
            AuditEventType.MFA_SETUP: AuditCategory.AUTHENTICATION,
            AuditEventType.MFA_VERIFY: AuditCategory.AUTHENTICATION,
            AuditEventType.MFA_FAILURE: AuditCategory.AUTHENTICATION,
            AuditEventType.PASSWORD_CHANGE: AuditCategory.AUTHENTICATION,
            AuditEventType.PASSWORD_RESET: AuditCategory.AUTHENTICATION,
            AuditEventType.ACCOUNT_LOCKED: AuditCategory.AUTHENTICATION,
            AuditEventType.ACCOUNT_UNLOCKED: AuditCategory.AUTHENTICATION,
            
            # Authorization
            AuditEventType.PERMISSION_GRANTED: AuditCategory.AUTHORIZATION,
            AuditEventType.PERMISSION_DENIED: AuditCategory.AUTHORIZATION,
            AuditEventType.ROLE_ASSIGNED: AuditCategory.AUTHORIZATION,
            AuditEventType.ROLE_REVOKED: AuditCategory.AUTHORIZATION,
            AuditEventType.ACCESS_GRANTED: AuditCategory.AUTHORIZATION,
            AuditEventType.ACCESS_DENIED: AuditCategory.AUTHORIZATION,
            
            # Data Access
            AuditEventType.DOCUMENT_VIEW: AuditCategory.DATA_ACCESS,
            AuditEventType.DOCUMENT_DOWNLOAD: AuditCategory.DATA_ACCESS,
            AuditEventType.DOCUMENT_UPLOAD: AuditCategory.DATA_ACCESS,
            AuditEventType.DOCUMENT_DELETE: AuditCategory.DATA_ACCESS,
            AuditEventType.DOCUMENT_MODIFY: AuditCategory.DATA_ACCESS,
            AuditEventType.DATA_EXPORT: AuditCategory.DATA_ACCESS,
            AuditEventType.DATA_IMPORT: AuditCategory.DATA_ACCESS,
            
            # Configuration
            AuditEventType.SECURITY_SETTINGS_CHANGE: AuditCategory.CONFIGURATION,
            AuditEventType.POLICY_CREATED: AuditCategory.CONFIGURATION,
            AuditEventType.POLICY_MODIFIED: AuditCategory.CONFIGURATION,
            AuditEventType.POLICY_DELETED: AuditCategory.CONFIGURATION,
            AuditEventType.USER_CREATED: AuditCategory.CONFIGURATION,
            AuditEventType.USER_MODIFIED: AuditCategory.CONFIGURATION,
            AuditEventType.USER_DELETED: AuditCategory.CONFIGURATION,
            AuditEventType.PROJECT_CREATED: AuditCategory.CONFIGURATION,
            AuditEventType.PROJECT_MODIFIED: AuditCategory.CONFIGURATION,
            AuditEventType.PROJECT_DELETED: AuditCategory.CONFIGURATION,
            
            # System
            AuditEventType.SERVICE_START: AuditCategory.SYSTEM,
            AuditEventType.SERVICE_STOP: AuditCategory.SYSTEM,
            AuditEventType.SERVICE_ERROR: AuditCategory.SYSTEM,
            AuditEventType.SYSTEM_ERROR: AuditCategory.SYSTEM,
            AuditEventType.MAINTENANCE_START: AuditCategory.SYSTEM,
            AuditEventType.MAINTENANCE_END: AuditCategory.SYSTEM,
            
            # Security
            AuditEventType.SUSPICIOUS_ACTIVITY: AuditCategory.SECURITY,
            AuditEventType.BRUTE_FORCE_ATTEMPT: AuditCategory.SECURITY,
            AuditEventType.UNAUTHORIZED_ACCESS: AuditCategory.SECURITY,
            AuditEventType.DATA_BREACH_ATTEMPT: AuditCategory.SECURITY,
            AuditEventType.MALWARE_DETECTED: AuditCategory.SECURITY,
            
            # Compliance
            AuditEventType.GDPR_DATA_REQUEST: AuditCategory.COMPLIANCE,
            AuditEventType.GDPR_DATA_DELETION: AuditCategory.COMPLIANCE,
            AuditEventType.HIPAA_ACCESS_LOG: AuditCategory.COMPLIANCE,
            AuditEventType.SOX_AUDIT_EVENT: AuditCategory.COMPLIANCE,
            AuditEventType.COMPLIANCE_VIOLATION: AuditCategory.COMPLIANCE,
        }
        
        return category_mapping.get(event_type, AuditCategory.SYSTEM)
    
    def _calculate_severity(self, event_type: AuditEventType, risk_score: Optional[float], event_data: Optional[Dict[str, Any]]) -> AuditSeverity:
        """Calculate severity based on event type and risk score"""
        
        # High severity events
        if event_type in [
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.DATA_BREACH_ATTEMPT,
            AuditEventType.MALWARE_DETECTED,
            AuditEventType.COMPLIANCE_VIOLATION,
            AuditEventType.ACCOUNT_LOCKED
        ]:
            return AuditSeverity.CRITICAL
        
        # Medium-high severity events
        if event_type in [
            AuditEventType.BRUTE_FORCE_ATTEMPT,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.SYSTEM_ERROR
        ]:
            return AuditSeverity.HIGH
        
        # Medium severity events
        if event_type in [
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.MFA_FAILURE,
            AuditEventType.SECURITY_SETTINGS_CHANGE,
            AuditEventType.POLICY_DELETED,
            AuditEventType.USER_DELETED,
            AuditEventType.PROJECT_DELETED
        ]:
            return AuditSeverity.MEDIUM
        
        # Use risk score if available
        if risk_score is not None:
            if risk_score >= 8.0:
                return AuditSeverity.CRITICAL
            elif risk_score >= 6.0:
                return AuditSeverity.HIGH
            elif risk_score >= 4.0:
                return AuditSeverity.MEDIUM
            else:
                return AuditSeverity.LOW
        
        # Default to low severity
        return AuditSeverity.LOW
    
    def _calculate_risk_score(self, event_type: AuditEventType, event_data: Optional[Dict[str, Any]], context: Optional[AuditContext]) -> float:
        """Calculate risk score for an event"""
        
        base_scores = {
            # Authentication events
            AuditEventType.LOGIN_SUCCESS: 0.0,
            AuditEventType.LOGIN_FAILURE: 3.0,
            AuditEventType.LOGOUT: 0.0,
            AuditEventType.MFA_SETUP: 1.0,
            AuditEventType.MFA_VERIFY: 0.5,
            AuditEventType.MFA_FAILURE: 4.0,
            AuditEventType.PASSWORD_CHANGE: 2.0,
            AuditEventType.PASSWORD_RESET: 3.0,
            AuditEventType.ACCOUNT_LOCKED: 6.0,
            AuditEventType.ACCOUNT_UNLOCKED: 2.0,
            
            # Authorization events
            AuditEventType.PERMISSION_GRANTED: 1.0,
            AuditEventType.PERMISSION_DENIED: 4.0,
            AuditEventType.ROLE_ASSIGNED: 2.0,
            AuditEventType.ROLE_REVOKED: 3.0,
            AuditEventType.ACCESS_GRANTED: 0.5,
            AuditEventType.ACCESS_DENIED: 5.0,
            
            # Data access events
            AuditEventType.DOCUMENT_VIEW: 0.5,
            AuditEventType.DOCUMENT_DOWNLOAD: 2.0,
            AuditEventType.DOCUMENT_UPLOAD: 3.0,
            AuditEventType.DOCUMENT_DELETE: 6.0,
            AuditEventType.DOCUMENT_MODIFY: 4.0,
            AuditEventType.DATA_EXPORT: 5.0,
            AuditEventType.DATA_IMPORT: 4.0,
            
            # Configuration events
            AuditEventType.SECURITY_SETTINGS_CHANGE: 7.0,
            AuditEventType.POLICY_CREATED: 3.0,
            AuditEventType.POLICY_MODIFIED: 4.0,
            AuditEventType.POLICY_DELETED: 8.0,
            AuditEventType.USER_CREATED: 2.0,
            AuditEventType.USER_MODIFIED: 3.0,
            AuditEventType.USER_DELETED: 7.0,
            AuditEventType.PROJECT_CREATED: 1.0,
            AuditEventType.PROJECT_MODIFIED: 2.0,
            AuditEventType.PROJECT_DELETED: 6.0,
            
            # System events
            AuditEventType.SERVICE_START: 0.0,
            AuditEventType.SERVICE_STOP: 1.0,
            AuditEventType.SERVICE_ERROR: 3.0,
            AuditEventType.SYSTEM_ERROR: 4.0,
            AuditEventType.MAINTENANCE_START: 1.0,
            AuditEventType.MAINTENANCE_END: 0.0,
            
            # Security events
            AuditEventType.SUSPICIOUS_ACTIVITY: 8.0,
            AuditEventType.BRUTE_FORCE_ATTEMPT: 9.0,
            AuditEventType.UNAUTHORIZED_ACCESS: 10.0,
            AuditEventType.DATA_BREACH_ATTEMPT: 10.0,
            AuditEventType.MALWARE_DETECTED: 10.0,
            
            # Compliance events
            AuditEventType.GDPR_DATA_REQUEST: 3.0,
            AuditEventType.GDPR_DATA_DELETION: 4.0,
            AuditEventType.HIPAA_ACCESS_LOG: 2.0,
            AuditEventType.SOX_AUDIT_EVENT: 3.0,
            AuditEventType.COMPLIANCE_VIOLATION: 8.0,
        }
        
        base_score = base_scores.get(event_type, 1.0)
        
        # Adjust based on context
        if context:
            # High risk for external IPs
            if context.ip_address and not self._is_internal_ip(context.ip_address):
                base_score += 2.0
            
            # High risk for unusual user agents
            if context.user_agent and self._is_suspicious_user_agent(context.user_agent):
                base_score += 3.0
            
            # High risk for failed requests
            if context.response_code and context.response_code >= 400:
                base_score += 1.0
        
        # Adjust based on event data
        if event_data:
            # High risk for sensitive operations
            if event_data.get("sensitive_operation"):
                base_score += 2.0
            
            # High risk for bulk operations
            if event_data.get("bulk_operation"):
                base_score += 1.5
            
            # High risk for admin operations
            if event_data.get("admin_operation"):
                base_score += 2.5
        
        return min(base_score, 10.0)  # Cap at 10.0
    
    def _requires_review(self, event_type: AuditEventType, severity: AuditSeverity, risk_score: float) -> bool:
        """Determine if event requires manual review"""
        
        # Always require review for critical events
        if severity == AuditSeverity.CRITICAL:
            return True
        
        # Require review for high risk scores
        if risk_score >= self.risk_thresholds["high_risk_score"]:
            return True
        
        # Require review for specific event types
        if event_type in [
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.DATA_BREACH_ATTEMPT,
            AuditEventType.MALWARE_DETECTED,
            AuditEventType.COMPLIANCE_VIOLATION,
            AuditEventType.BRUTE_FORCE_ATTEMPT,
            AuditEventType.SUSPICIOUS_ACTIVITY
        ]:
            return True
        
        return False
    
    def _is_internal_ip(self, ip_address: str) -> bool:
        """Check if IP address is internal"""
        internal_ranges = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "127.0.0.0/8",
            "::1/128"
        ]
        
        # Simple check for common internal ranges
        if ip_address.startswith(("10.", "172.", "192.168.", "127.")):
            return True
        
        return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper",
            "curl", "wget", "python-requests",
            "sqlmap", "nmap", "nikto"
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    async def _store_audit_event(self, event: AuditEvent) -> None:
        """Store audit event in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO enhanced_audit_logs 
                (id, event_type, category, severity, timestamp, user_id, username, user_email,
                 session_id, space_id, space_name, resource_type, resource_id, resource_name,
                 event_description, event_data, context, compliance_framework, risk_score,
                 requires_review, service_name, version, environment, tags, retention_days, archived)
                VALUES (:id, :event_type, :category, :severity, :timestamp, :user_id, :username, :user_email,
                        :session_id, :space_id, :space_name, :resource_type, :resource_id, :resource_name,
                        :event_description, :event_data, :context, :compliance_framework, :risk_score,
                        :requires_review, :service_name, :version, :environment, :tags, :retention_days, :archived)
            """), {
                "id": str(event.id),
                "event_type": event.event_type.value,
                "category": event.category.value,
                "severity": event.severity.value,
                "timestamp": event.timestamp,
                "user_id": event.user_id,
                "username": event.username,
                "user_email": event.user_email,
                "session_id": event.session_id,
                "space_id": event.space_id,
                "space_name": event.space_name,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "resource_name": event.resource_name,
                "event_description": event.event_description,
                "event_data": json.dumps(event.event_data) if event.event_data else None,
                "context": json.dumps(event.context.dict()) if event.context else None,
                "compliance_framework": event.compliance_framework,
                "risk_score": event.risk_score,
                "requires_review": event.requires_review,
                "service_name": event.service_name,
                "version": event.version,
                "environment": event.environment,
                "tags": json.dumps(event.tags),
                "retention_days": event.retention_days,
                "archived": event.archived
            })
            await db.commit()
    
    def _build_query_sql(self, query: AuditLogQuery) -> str:
        """Build SQL query for audit log search"""
        
        where_conditions = []
        params = {}
        
        if query.start_date:
            where_conditions.append("timestamp >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("timestamp <= :end_date")
            params["end_date"] = query.end_date
        
        if query.event_types:
            where_conditions.append("event_type = ANY(:event_types)")
            params["event_types"] = [t.value for t in query.event_types]
        
        if query.categories:
            where_conditions.append("category = ANY(:categories)")
            params["categories"] = [c.value for c in query.categories]
        
        if query.severities:
            where_conditions.append("severity = ANY(:severities)")
            params["severities"] = [s.value for s in query.severities]
        
        if query.user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = query.user_id
        
        if query.space_id:
            where_conditions.append("space_id = :space_id")
            params["space_id"] = query.space_id
        
        if query.resource_type:
            where_conditions.append("resource_type = :resource_type")
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            where_conditions.append("resource_id = :resource_id")
            params["resource_id"] = query.resource_id
        
        if query.requires_review is not None:
            where_conditions.append("requires_review = :requires_review")
            params["requires_review"] = query.requires_review
        
        if query.compliance_framework:
            where_conditions.append("compliance_framework = :compliance_framework")
            params["compliance_framework"] = query.compliance_framework
        
        if query.search_text:
            where_conditions.append("(event_description ILIKE :search_text OR username ILIKE :search_text)")
            params["search_text"] = f"%{query.search_text}%"
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"""
            SELECT * FROM enhanced_audit_logs 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """
    
    def _build_count_sql(self, query: AuditLogQuery) -> str:
        """Build SQL query for count"""
        
        where_conditions = []
        params = {}
        
        if query.start_date:
            where_conditions.append("timestamp >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("timestamp <= :end_date")
            params["end_date"] = query.end_date
        
        if query.event_types:
            where_conditions.append("event_type = ANY(:event_types)")
            params["event_types"] = [t.value for t in query.event_types]
        
        if query.categories:
            where_conditions.append("category = ANY(:categories)")
            params["categories"] = [c.value for c in query.categories]
        
        if query.severities:
            where_conditions.append("severity = ANY(:severities)")
            params["severities"] = [s.value for s in query.severities]
        
        if query.user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = query.user_id
        
        if query.space_id:
            where_conditions.append("space_id = :space_id")
            params["space_id"] = query.space_id
        
        if query.resource_type:
            where_conditions.append("resource_type = :resource_type")
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            where_conditions.append("resource_id = :resource_id")
            params["resource_id"] = query.resource_id
        
        if query.requires_review is not None:
            where_conditions.append("requires_review = :requires_review")
            params["requires_review"] = query.requires_review
        
        if query.compliance_framework:
            where_conditions.append("compliance_framework = :compliance_framework")
            params["compliance_framework"] = query.compliance_framework
        
        if query.search_text:
            where_conditions.append("(event_description ILIKE :search_text OR username ILIKE :search_text)")
            params["search_text"] = f"%{query.search_text}%"
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"SELECT COUNT(*) FROM enhanced_audit_logs WHERE {where_clause}"
    
    def _build_query_params(self, query: AuditLogQuery) -> Dict[str, Any]:
        """Build query parameters"""
        
        params = {
            "limit": query.limit,
            "offset": query.offset
        }
        
        if query.start_date:
            params["start_date"] = query.start_date
        
        if query.end_date:
            params["end_date"] = query.end_date
        
        if query.event_types:
            params["event_types"] = [t.value for t in query.event_types]
        
        if query.categories:
            params["categories"] = [c.value for c in query.categories]
        
        if query.severities:
            params["severities"] = [s.value for s in query.severities]
        
        if query.user_id:
            params["user_id"] = query.user_id
        
        if query.space_id:
            params["space_id"] = query.space_id
        
        if query.resource_type:
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            params["resource_id"] = query.resource_id
        
        if query.requires_review is not None:
            params["requires_review"] = query.requires_review
        
        if query.compliance_framework:
            params["compliance_framework"] = query.compliance_framework
        
        if query.search_text:
            params["search_text"] = f"%{query.search_text}%"
        
        return params
    
    async def _check_alerts(self, event: AuditEvent) -> None:
        """Check if event triggers any alerts"""
        
        for alert_name, alert in self.alerts.items():
            if not alert.is_active:
                continue
            
            # Check if event type matches
            if event.event_type not in alert.event_types:
                continue
            
            # Check conditions
            if self._evaluate_alert_conditions(alert, event):
                await self._trigger_alert(alert, event)
    
    def _evaluate_alert_conditions(self, alert: AuditLogAlert, event: AuditEvent) -> bool:
        """Evaluate alert conditions"""
        
        conditions = alert.conditions
        
        # Check risk score threshold
        if "min_risk_score" in conditions:
            if event.risk_score < conditions["min_risk_score"]:
                return False
        
        # Check severity
        if "min_severity" in conditions:
            severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            if severity_levels.get(event.severity.value, 0) < severity_levels.get(conditions["min_severity"], 0):
                return False
        
        # Check specific event data
        if "event_data_conditions" in conditions:
            for condition in conditions["event_data_conditions"]:
                if not self._evaluate_event_data_condition(condition, event.event_data):
                    return False
        
        return True
    
    def _evaluate_event_data_condition(self, condition: Dict[str, Any], event_data: Optional[Dict[str, Any]]) -> bool:
        """Evaluate event data condition"""
        
        if not event_data:
            return False
        
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if field not in event_data:
            return False
        
        field_value = event_data[field]
        
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return str(value) in str(field_value)
        elif operator == "not_contains":
            return str(value) not in str(field_value)
        elif operator == "greater_than":
            return field_value > value
        elif operator == "less_than":
            return field_value < value
        
        return False
    
    async def _trigger_alert(self, alert: AuditLogAlert, event: AuditEvent) -> None:
        """Trigger alert notification"""
        
        self.logger.warning(
            "Audit alert triggered",
            alert_name=alert.alert_name,
            event_id=str(event.id),
            event_type=event.event_type.value,
            severity=event.severity.value,
            risk_score=event.risk_score
        )
        
        # TODO: Implement actual notification sending
        # This would integrate with email, Slack, webhook, etc.
    
    async def _generate_export_file(self, export_config: AuditLogExport, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate export file"""
        
        # TODO: Implement actual file generation
        # This would create JSON, CSV, Excel, or PDF files
        
        return {
            "file_path": f"/tmp/audit_export_{export_config.export_id}.{export_config.export_format}",
            "file_size": 1024  # Mock size
        }
