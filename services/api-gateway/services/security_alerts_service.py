"""
Security Alerts and Notifications Service
Comprehensive security alerting and notification systems
"""

import json
import asyncio
import smtplib
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.security_alerts import (
    SecurityAlert, AlertRule, NotificationTemplate, NotificationSubscription,
    AlertCorrelation, AlertSuppression, AlertRequest, AlertUpdateRequest,
    AlertRuleRequest, AlertQuery, AlertStats, NotificationRequest,
    EscalationRequest, SuppressionRequest, AlertSeverity, AlertStatus,
    AlertCategory, AlertSource, NotificationChannel, EscalationLevel
)
# Database will be accessed through the main app's db_manager

logger = structlog.get_logger(__name__)

class SecurityAlertsService:
    """Security alerts and notifications service"""
    
    def __init__(self):
        self.logger = logger
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_templates: Dict[str, NotificationTemplate] = {}
        self.notification_subscriptions: Dict[str, NotificationSubscription] = {}
        self.alert_suppressions: Dict[str, AlertSuppression] = {}
        self.correlation_engine_enabled = True
        self.escalation_engine_enabled = True
        self.notification_engine_enabled = True
        
        # Initialize default rules and templates
        self._initialize_default_rules()
        self._initialize_default_templates()
        self._initialize_default_subscriptions()
    
    async def create_alert(self, alert_request: AlertRequest) -> SecurityAlert:
        """Create a new security alert"""
        
        # Check for suppression
        if await self._is_alert_suppressed(alert_request):
            self.logger.info("Alert suppressed", title=alert_request.title, reason="Suppression rule matched")
            return None
        
        # Create alert
        alert = SecurityAlert(
            title=alert_request.title,
            description=alert_request.description,
            severity=alert_request.severity,
            category=alert_request.category,
            source=alert_request.source,
            source_id=alert_request.source_id,
            user_id=alert_request.user_id,
            ip_address=alert_request.ip_address,
            user_agent=alert_request.user_agent,
            resource_type=alert_request.resource_type,
            resource_id=alert_request.resource_id,
            resource_name=alert_request.resource_name,
            event_data=alert_request.event_data,
            correlation_id=alert_request.correlation_id,
            tags=alert_request.tags,
            risk_score=alert_request.risk_score,
            confidence_score=alert_request.confidence_score
        )
        
        # Store alert in database
        await self._store_alert(alert)
        
        # Check for correlation
        if self.correlation_engine_enabled:
            await self._check_alert_correlation(alert)
        
        # Send notifications
        if self.notification_engine_enabled:
            await self._send_alert_notifications(alert)
        
        # Start escalation timer if needed
        if self.escalation_engine_enabled and alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            await self._schedule_escalation(alert)
        
        self.logger.info("Security alert created", 
                        alert_id=str(alert.id), 
                        title=alert.title, 
                        severity=alert.severity.value)
        
        return alert
    
    async def update_alert(self, alert_id: str, update_request: AlertUpdateRequest, user_id: str) -> SecurityAlert:
        """Update an existing alert"""
        
        # Get current alert
        alert = await self._get_alert(alert_id)
        if not alert:
            raise ValueError("Alert not found")
        
        # Update fields
        if update_request.status:
            alert.status = update_request.status
            if update_request.status == AlertStatus.ACKNOWLEDGED:
                alert.acknowledged_at = datetime.now(timezone.utc)
                alert.acknowledged_by = user_id
            elif update_request.status == AlertStatus.RESOLVED:
                alert.resolved_at = datetime.now(timezone.utc)
                alert.resolved_by = user_id
        
        if update_request.resolution_notes:
            alert.resolution_notes = update_request.resolution_notes
        
        if update_request.tags:
            alert.tags = update_request.tags
        
        if update_request.false_positive is not None:
            alert.false_positive = update_request.false_positive
        
        if update_request.suppression_until:
            alert.suppression_until = update_request.suppression_until
        
        alert.updated_at = datetime.now(timezone.utc)
        
        # Store updated alert
        await self._store_alert(alert)
        
        # Log alert update
        await self._log_alert_update(alert, update_request, user_id)
        
        self.logger.info("Alert updated", 
                        alert_id=alert_id, 
                        status=alert.status.value,
                        updated_by=user_id)
        
        return alert
    
    async def get_alerts(self, query: AlertQuery) -> Tuple[List[SecurityAlert], int]:
        """Get alerts with filtering"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build SQL query
            sql_query = self._build_alert_query_sql(query)
            params = self._build_alert_query_params(query)
            
            # Execute query
            result = await db.execute(text(sql_query), params)
            rows = result.fetchall()
            
            # Get total count
            count_sql = self._build_alert_count_sql(query)
            count_result = await db.execute(text(count_sql), params)
            total_count = count_result.scalar()
            
            # Convert rows to SecurityAlert objects
            alerts = []
            for row in rows:
                alert = SecurityAlert(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    severity=AlertSeverity(row.severity),
                    category=AlertCategory(row.category),
                    status=AlertStatus(row.status),
                    source=AlertSource(row.source),
                    source_id=row.source_id,
                    user_id=row.user_id,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    resource_name=row.resource_name,
                    event_data=json.loads(row.event_data) if row.event_data else {},
                    correlation_id=row.correlation_id,
                    tags=json.loads(row.tags) if row.tags else [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    acknowledged_at=row.acknowledged_at,
                    acknowledged_by=row.acknowledged_by,
                    resolved_at=row.resolved_at,
                    resolved_by=row.resolved_by,
                    resolution_notes=row.resolution_notes,
                    escalation_level=EscalationLevel(row.escalation_level),
                    escalation_history=json.loads(row.escalation_history) if row.escalation_history else [],
                    false_positive=row.false_positive,
                    suppression_until=row.suppression_until,
                    risk_score=row.risk_score,
                    confidence_score=row.confidence_score
                )
                alerts.append(alert)
            
            return alerts, total_count
    
    async def get_alert_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AlertStats:
        """Get alert statistics"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            # Build base WHERE clause
            where_conditions = []
            params = {}
            
            if start_date:
                where_conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                where_conditions.append("created_at <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Get statistics
            stats_queries = {
                "total_alerts": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause}",
                "active_alerts": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause} AND status = 'active'",
                "resolved_alerts": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause} AND status = 'resolved'",
                "false_positives": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause} AND false_positive = true",
                "alerts_by_severity": f"SELECT severity, COUNT(*) FROM security_alerts WHERE {where_clause} GROUP BY severity",
                "alerts_by_category": f"SELECT category, COUNT(*) FROM security_alerts WHERE {where_clause} GROUP BY category",
                "alerts_by_status": f"SELECT status, COUNT(*) FROM security_alerts WHERE {where_clause} GROUP BY status",
                "alerts_by_source": f"SELECT source, COUNT(*) FROM security_alerts WHERE {where_clause} GROUP BY source",
                "average_resolution_time": f"SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60) FROM security_alerts WHERE {where_clause} AND resolved_at IS NOT NULL",
                "escalation_rate": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause} AND escalation_level != 'level_1'",
                "false_positive_rate": f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause} AND false_positive = true"
            }
            
            results = {}
            for stat_name, query in stats_queries.items():
                if stat_name in ["alerts_by_severity", "alerts_by_category", "alerts_by_status", "alerts_by_source"]:
                    result = await db.execute(text(query), params)
                    rows = result.fetchall()
                    results[stat_name] = {row[0]: row[1] for row in rows}
                else:
                    result = await db.execute(text(query), params)
                    results[stat_name] = result.scalar() or 0
            
            # Get top alert sources
            top_sources_query = f"""
                SELECT source, COUNT(*) as count, AVG(risk_score) as avg_risk
                FROM security_alerts 
                WHERE {where_clause}
                GROUP BY source
                ORDER BY count DESC
                LIMIT 5
            """
            result = await db.execute(text(top_sources_query), params)
            top_sources = [
                {"source": row[0], "count": row[1], "avg_risk": float(row[2]) if row[2] else 0}
                for row in result.fetchall()
            ]
            
            # Calculate rates
            total_alerts = results["total_alerts"]
            escalation_rate = results["escalation_rate"] / total_alerts if total_alerts > 0 else 0
            false_positive_rate = results["false_positive_rate"] / total_alerts if total_alerts > 0 else 0
            
            return AlertStats(
                total_alerts=results["total_alerts"],
                active_alerts=results["active_alerts"],
                resolved_alerts=results["resolved_alerts"],
                false_positives=results["false_positives"],
                alerts_by_severity=results["alerts_by_severity"],
                alerts_by_category=results["alerts_by_category"],
                alerts_by_status=results["alerts_by_status"],
                alerts_by_source=results["alerts_by_source"],
                average_resolution_time_minutes=results["average_resolution_time"] or 0,
                escalation_rate=escalation_rate,
                false_positive_rate=false_positive_rate,
                top_alert_sources=top_sources,
                recent_trends={}  # Would be calculated from time series data
            )
    
    async def create_alert_rule(self, rule_request: AlertRuleRequest, user_id: str) -> AlertRule:
        """Create a new alert rule"""
        
        rule = AlertRule(
            name=rule_request.name,
            description=rule_request.description,
            condition=rule_request.condition,
            severity=rule_request.severity,
            category=rule_request.category,
            source=rule_request.source,
            enabled=rule_request.enabled,
            threshold=rule_request.threshold,
            time_window=rule_request.time_window,
            aggregation=rule_request.aggregation,
            notification_channels=rule_request.notification_channels,
            escalation_enabled=rule_request.escalation_enabled,
            escalation_delay_minutes=rule_request.escalation_delay_minutes,
            escalation_levels=rule_request.escalation_levels,
            suppression_enabled=rule_request.suppression_enabled,
            suppression_duration_minutes=rule_request.suppression_duration_minutes,
            tags=rule_request.tags,
            created_by=user_id
        )
        
        # Store rule in database
        await self._store_alert_rule(rule)
        
        # Add to in-memory cache
        self.alert_rules[str(rule.id)] = rule
        
        self.logger.info("Alert rule created", rule_id=str(rule.id), name=rule.name)
        return rule
    
    async def send_notification(self, notification_request: NotificationRequest) -> bool:
        """Send notification for an alert"""
        
        alert = await self._get_alert(notification_request.alert_id)
        if not alert:
            raise ValueError("Alert not found")
        
        success_count = 0
        total_count = len(notification_request.channels)
        
        for channel in notification_request.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(alert, notification_request.recipients, notification_request.custom_message)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack_notification(alert, notification_request.recipients, notification_request.custom_message)
                elif channel == NotificationChannel.TEAMS:
                    await self._send_teams_notification(alert, notification_request.recipients, notification_request.custom_message)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(alert, notification_request.recipients, notification_request.custom_message)
                elif channel == NotificationChannel.SMS:
                    await self._send_sms_notification(alert, notification_request.recipients, notification_request.custom_message)
                
                success_count += 1
                
            except Exception as e:
                self.logger.error("Notification failed", 
                                channel=channel.value, 
                                alert_id=notification_request.alert_id, 
                                error=str(e))
        
        return success_count == total_count
    
    async def escalate_alert(self, escalation_request: EscalationRequest) -> SecurityAlert:
        """Escalate an alert"""
        
        alert = await self._get_alert(escalation_request.alert_id)
        if not alert:
            raise ValueError("Alert not found")
        
        # Update escalation level
        old_level = alert.escalation_level
        alert.escalation_level = escalation_request.escalation_level
        alert.updated_at = datetime.now(timezone.utc)
        
        # Add to escalation history
        escalation_entry = {
            "from_level": old_level.value,
            "to_level": escalation_request.escalation_level.value,
            "reason": escalation_request.reason,
            "escalated_by": escalation_request.escalated_by,
            "escalated_at": datetime.now(timezone.utc).isoformat()
        }
        alert.escalation_history.append(escalation_entry)
        
        # Store updated alert
        await self._store_alert(alert)
        
        # Send escalation notifications
        await self._send_escalation_notifications(alert, escalation_entry)
        
        self.logger.info("Alert escalated", 
                        alert_id=escalation_request.alert_id,
                        from_level=old_level.value,
                        to_level=escalation_request.escalation_level.value,
                        escalated_by=escalation_request.escalated_by)
        
        return alert
    
    async def create_suppression(self, suppression_request: SuppressionRequest) -> AlertSuppression:
        """Create alert suppression rule"""
        
        suppression = AlertSuppression(
            condition=suppression_request.condition,
            reason=suppression_request.reason,
            suppressed_by=suppression_request.suppressed_by,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=suppression_request.duration_minutes)
        )
        
        # Store suppression in database
        await self._store_alert_suppression(suppression)
        
        # Add to in-memory cache
        self.alert_suppressions[str(suppression.id)] = suppression
        
        self.logger.info("Alert suppression created", 
                        suppression_id=str(suppression.id),
                        condition=suppression.condition,
                        suppressed_by=suppression.suppressed_by)
        
        return suppression
    
    async def process_alert_rules(self, event_data: Dict[str, Any]) -> List[SecurityAlert]:
        """Process alert rules against event data"""
        
        triggered_alerts = []
        
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            try:
                if await self._evaluate_rule_condition(rule, event_data):
                    # Create alert from rule
                    alert_request = AlertRequest(
                        title=f"Rule Triggered: {rule.name}",
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        source=rule.source,
                        event_data=event_data,
                        tags=rule.tags
                    )
                    
                    alert = await self.create_alert(alert_request)
                    if alert:
                        triggered_alerts.append(alert)
                        
                        # Update rule trigger count
                        rule.trigger_count += 1
                        rule.last_triggered = datetime.now(timezone.utc)
                        await self._store_alert_rule(rule)
                        
            except Exception as e:
                self.logger.error("Rule evaluation failed", 
                                rule_id=str(rule.id), 
                                rule_name=rule.name, 
                                error=str(e))
        
        return triggered_alerts
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        
        default_rules = [
            {
                "name": "Multiple Failed Login Attempts",
                "description": "Alert when multiple failed login attempts detected",
                "condition": "failed_login_count > 5",
                "severity": AlertSeverity.HIGH,
                "category": AlertCategory.AUTHENTICATION,
                "source": AlertSource.IAM,
                "threshold": 5,
                "time_window": 15,
                "aggregation": "count",
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                "escalation_levels": [EscalationLevel.LEVEL_2, EscalationLevel.LEVEL_3]
            },
            {
                "name": "Unauthorized Data Access",
                "description": "Alert when unauthorized data access is attempted",
                "condition": "access_denied = true AND resource_type = 'sensitive'",
                "severity": AlertSeverity.CRITICAL,
                "category": AlertCategory.DATA_ACCESS,
                "source": AlertSource.AUDIT_LOG,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                "escalation_levels": [EscalationLevel.LEVEL_2, EscalationLevel.LEVEL_3, EscalationLevel.EXECUTIVE]
            },
            {
                "name": "Suspicious File Download",
                "description": "Alert when suspicious file download pattern detected",
                "condition": "download_size > 100000000 AND download_count > 10",
                "severity": AlertSeverity.MEDIUM,
                "category": AlertCategory.SUSPICIOUS_ACTIVITY,
                "source": AlertSource.DLP,
                "threshold": 100000000,
                "time_window": 60,
                "aggregation": "sum",
                "notification_channels": [NotificationChannel.EMAIL]
            },
            {
                "name": "Privilege Escalation Attempt",
                "description": "Alert when privilege escalation is attempted",
                "condition": "privilege_escalation = true",
                "severity": AlertSeverity.CRITICAL,
                "category": AlertCategory.PRIVILEGE_ESCALATION,
                "source": AlertSource.IAM,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                "escalation_levels": [EscalationLevel.LEVEL_2, EscalationLevel.LEVEL_3, EscalationLevel.EXECUTIVE]
            },
            {
                "name": "Data Exfiltration Pattern",
                "description": "Alert when data exfiltration pattern detected",
                "condition": "data_export_size > 50000000 AND export_frequency > 5",
                "severity": AlertSeverity.CRITICAL,
                "category": AlertCategory.DATA_EXFILTRATION,
                "source": AlertSource.DLP,
                "threshold": 50000000,
                "time_window": 120,
                "aggregation": "sum",
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                "escalation_levels": [EscalationLevel.LEVEL_2, EscalationLevel.LEVEL_3, EscalationLevel.EXECUTIVE]
            }
        ]
        
        for rule_data in default_rules:
            rule = AlertRule(
                name=rule_data["name"],
                description=rule_data["description"],
                condition=rule_data["condition"],
                severity=rule_data["severity"],
                category=rule_data["category"],
                source=rule_data["source"],
                threshold=rule_data.get("threshold"),
                time_window=rule_data.get("time_window"),
                aggregation=rule_data.get("aggregation"),
                notification_channels=rule_data.get("notification_channels", []),
                escalation_levels=rule_data.get("escalation_levels", []),
                created_by="system"
            )
            self.alert_rules[str(rule.id)] = rule
    
    def _initialize_default_templates(self):
        """Initialize default notification templates"""
        
        default_templates = [
            {
                "name": "Critical Alert Email",
                "description": "Email template for critical alerts",
                "channel": NotificationChannel.EMAIL,
                "subject_template": "🚨 CRITICAL SECURITY ALERT: {alert_title}",
                "body_template": """
                <h2>Critical Security Alert</h2>
                <p><strong>Alert:</strong> {alert_title}</p>
                <p><strong>Description:</strong> {alert_description}</p>
                <p><strong>Severity:</strong> {alert_severity}</p>
                <p><strong>Category:</strong> {alert_category}</p>
                <p><strong>Source:</strong> {alert_source}</p>
                <p><strong>Time:</strong> {alert_time}</p>
                <p><strong>Risk Score:</strong> {risk_score}/10</p>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p><strong>User:</strong> {user_id}</p>
                <hr>
                <p><em>This is an automated security alert. Please investigate immediately.</em></p>
                """,
                "variables": ["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score", "ip_address", "user_id"]
            },
            {
                "name": "High Alert Slack",
                "description": "Slack template for high severity alerts",
                "channel": NotificationChannel.SLACK,
                "body_template": """
                🚨 *HIGH SECURITY ALERT*
                *Alert:* {alert_title}
                *Description:* {alert_description}
                *Severity:* {alert_severity}
                *Category:* {alert_category}
                *Source:* {alert_source}
                *Time:* {alert_time}
                *Risk Score:* {risk_score}/10
                *IP Address:* {ip_address}
                *User:* {user_id}
                """,
                "variables": ["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score", "ip_address", "user_id"]
            },
            {
                "name": "Medium Alert Teams",
                "description": "Teams template for medium severity alerts",
                "channel": NotificationChannel.TEAMS,
                "body_template": """
                <h3>⚠️ Medium Security Alert</h3>
                <p><strong>Alert:</strong> {alert_title}</p>
                <p><strong>Description:</strong> {alert_description}</p>
                <p><strong>Severity:</strong> {alert_severity}</p>
                <p><strong>Category:</strong> {alert_category}</p>
                <p><strong>Source:</strong> {alert_source}</p>
                <p><strong>Time:</strong> {alert_time}</p>
                <p><strong>Risk Score:</strong> {risk_score}/10</p>
                """,
                "variables": ["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score"]
            }
        ]
        
        for template_data in default_templates:
            template = NotificationTemplate(
                name=template_data["name"],
                description=template_data["description"],
                channel=template_data["channel"],
                subject_template=template_data.get("subject_template"),
                body_template=template_data["body_template"],
                variables=template_data["variables"],
                created_by="system"
            )
            self.notification_templates[str(template.id)] = template
    
    def _initialize_default_subscriptions(self):
        """Initialize default notification subscriptions"""
        
        default_subscriptions = [
            {
                "user_id": "admin@company.com",
                "user_email": "admin@company.com",
                "channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                "severity_filter": [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                "category_filter": [AlertCategory.AUTHENTICATION, AlertCategory.DATA_ACCESS, AlertCategory.DATA_BREACH]
            },
            {
                "user_id": "security@company.com",
                "user_email": "security@company.com",
                "channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                "severity_filter": [AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                "category_filter": []  # All categories
            },
            {
                "user_id": "compliance@company.com",
                "user_email": "compliance@company.com",
                "channels": [NotificationChannel.EMAIL],
                "severity_filter": [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                "category_filter": [AlertCategory.COMPLIANCE, AlertCategory.POLICY_VIOLATION]
            }
        ]
        
        for sub_data in default_subscriptions:
            subscription = NotificationSubscription(
                user_id=sub_data["user_id"],
                user_email=sub_data["user_email"],
                channels=sub_data["channels"],
                severity_filter=sub_data["severity_filter"],
                category_filter=sub_data["category_filter"]
            )
            self.notification_subscriptions[subscription.user_id] = subscription
    
    async def _is_alert_suppressed(self, alert_request: AlertRequest) -> bool:
        """Check if alert should be suppressed"""
        
        for suppression in self.alert_suppressions.values():
            if not suppression.is_active:
                continue
            
            if suppression.expires_at and suppression.expires_at < datetime.now(timezone.utc):
                suppression.is_active = False
                continue
            
            # Simple condition matching - in production, this would be more sophisticated
            if suppression.condition.lower() in alert_request.title.lower():
                return True
        
        return False
    
    async def _check_alert_correlation(self, alert: SecurityAlert):
        """Check for alert correlation"""
        
        # Simple correlation logic - in production, this would be more sophisticated
        correlation_id = f"corr_{alert.user_id}_{alert.ip_address}_{alert.category.value}"
        alert.correlation_id = correlation_id
        
        # Store correlation
        await self._store_alert_correlation(alert)
    
    async def _send_alert_notifications(self, alert: SecurityAlert):
        """Send notifications for an alert"""
        
        # Get subscribers for this alert
        subscribers = self._get_subscribers_for_alert(alert)
        
        for subscriber in subscribers:
            for channel in subscriber.channels:
                try:
                    await self._send_notification_to_subscriber(alert, subscriber, channel)
                except Exception as e:
                    self.logger.error("Notification failed", 
                                    channel=channel.value, 
                                    subscriber=subscriber.user_id, 
                                    error=str(e))
    
    def _get_subscribers_for_alert(self, alert: SecurityAlert) -> List[NotificationSubscription]:
        """Get subscribers who should receive this alert"""
        
        subscribers = []
        
        for subscription in self.notification_subscriptions.values():
            if not subscription.enabled:
                continue
            
            # Check severity filter
            if subscription.severity_filter and alert.severity not in subscription.severity_filter:
                continue
            
            # Check category filter
            if subscription.category_filter and alert.category not in subscription.category_filter:
                continue
            
            # Check source filter
            if subscription.source_filter and alert.source not in subscription.source_filter:
                continue
            
            subscribers.append(subscription)
        
        return subscribers
    
    async def _send_notification_to_subscriber(self, alert: SecurityAlert, subscriber: NotificationSubscription, channel: NotificationChannel):
        """Send notification to a specific subscriber"""
        
        # Get template for channel
        template = self._get_template_for_channel(channel, alert.severity)
        if not template:
            return
        
        # Render template
        message = self._render_template(template, alert)
        
        # Send notification
        if channel == NotificationChannel.EMAIL:
            await self._send_email_notification(alert, [subscriber.user_email], message)
        elif channel == NotificationChannel.SLACK:
            await self._send_slack_notification(alert, [subscriber.user_id], message)
        elif channel == NotificationChannel.TEAMS:
            await self._send_teams_notification(alert, [subscriber.user_id], message)
        elif channel == NotificationChannel.SMS:
            await self._send_sms_notification(alert, [subscriber.user_phone], message)
    
    def _get_template_for_channel(self, channel: NotificationChannel, severity: AlertSeverity) -> Optional[NotificationTemplate]:
        """Get appropriate template for channel and severity"""
        
        for template in self.notification_templates.values():
            if template.channel == channel and template.enabled:
                # Simple severity matching - in production, this would be more sophisticated
                if severity == AlertSeverity.CRITICAL and "critical" in template.name.lower():
                    return template
                elif severity == AlertSeverity.HIGH and "high" in template.name.lower():
                    return template
                elif severity == AlertSeverity.MEDIUM and "medium" in template.name.lower():
                    return template
        
        return None
    
    def _render_template(self, template: NotificationTemplate, alert: SecurityAlert) -> str:
        """Render template with alert data"""
        
        message = template.body_template
        
        # Replace variables
        variables = {
            "alert_title": alert.title,
            "alert_description": alert.description,
            "alert_severity": alert.severity.value,
            "alert_category": alert.category.value,
            "alert_source": alert.source.value,
            "alert_time": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "risk_score": str(alert.risk_score),
            "ip_address": alert.ip_address or "N/A",
            "user_id": alert.user_id or "N/A"
        }
        
        for var, value in variables.items():
            message = message.replace(f"{{{var}}}", str(value))
        
        return message
    
    async def _send_email_notification(self, alert: SecurityAlert, recipients: List[str], message: str):
        """Send email notification"""
        
        # Mock email sending - in production, this would use a real email service
        self.logger.info("Email notification sent", 
                        alert_id=str(alert.id),
                        recipients=recipients,
                        subject=f"Security Alert: {alert.title}")
    
    async def _send_slack_notification(self, alert: SecurityAlert, recipients: List[str], message: str):
        """Send Slack notification"""
        
        # Mock Slack sending - in production, this would use Slack API
        self.logger.info("Slack notification sent", 
                        alert_id=str(alert.id),
                        recipients=recipients,
                        message=message[:100])
    
    async def _send_teams_notification(self, alert: SecurityAlert, recipients: List[str], message: str):
        """Send Teams notification"""
        
        # Mock Teams sending - in production, this would use Teams API
        self.logger.info("Teams notification sent", 
                        alert_id=str(alert.id),
                        recipients=recipients,
                        message=message[:100])
    
    async def _send_sms_notification(self, alert: SecurityAlert, recipients: List[str], message: str):
        """Send SMS notification"""
        
        # Mock SMS sending - in production, this would use SMS service
        self.logger.info("SMS notification sent", 
                        alert_id=str(alert.id),
                        recipients=recipients,
                        message=message[:100])
    
    async def _send_webhook_notification(self, alert: SecurityAlert, recipients: List[str], message: str):
        """Send webhook notification"""
        
        # Mock webhook sending - in production, this would use HTTP requests
        self.logger.info("Webhook notification sent", 
                        alert_id=str(alert.id),
                        recipients=recipients,
                        message=message[:100])
    
    async def _schedule_escalation(self, alert: SecurityAlert):
        """Schedule alert escalation"""
        
        # Mock escalation scheduling - in production, this would use a job queue
        self.logger.info("Escalation scheduled", 
                        alert_id=str(alert.id),
                        severity=alert.severity.value)
    
    async def _send_escalation_notifications(self, alert: SecurityAlert, escalation_entry: Dict[str, Any]):
        """Send escalation notifications"""
        
        # Mock escalation notification - in production, this would send to escalation contacts
        self.logger.info("Escalation notification sent", 
                        alert_id=str(alert.id),
                        escalation_level=alert.escalation_level.value)
    
    async def _evaluate_rule_condition(self, rule: AlertRule, event_data: Dict[str, Any]) -> bool:
        """Evaluate rule condition against event data"""
        
        # Simple condition evaluation - in production, this would be more sophisticated
        try:
            # Mock evaluation - in production, this would parse and evaluate the condition
            if "failed_login_count" in rule.condition and event_data.get("failed_login_count", 0) > (rule.threshold or 0):
                return True
            elif "access_denied" in rule.condition and event_data.get("access_denied", False):
                return True
            elif "download_size" in rule.condition and event_data.get("download_size", 0) > (rule.threshold or 0):
                return True
            elif "privilege_escalation" in rule.condition and event_data.get("privilege_escalation", False):
                return True
            elif "data_export_size" in rule.condition and event_data.get("data_export_size", 0) > (rule.threshold or 0):
                return True
            
            return False
        except Exception as e:
            self.logger.error("Rule condition evaluation failed", 
                            rule_id=str(rule.id), 
                            condition=rule.condition, 
                            error=str(e))
            return False
    
    async def _get_alert(self, alert_id: str) -> Optional[SecurityAlert]:
        """Get alert by ID"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            result = await db.execute(
                text("SELECT * FROM security_alerts WHERE id = :alert_id"),
                {"alert_id": alert_id}
            )
            row = result.fetchone()
            
            if row:
                return SecurityAlert(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    severity=AlertSeverity(row.severity),
                    category=AlertCategory(row.category),
                    status=AlertStatus(row.status),
                    source=AlertSource(row.source),
                    source_id=row.source_id,
                    user_id=row.user_id,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    resource_name=row.resource_name,
                    event_data=json.loads(row.event_data) if row.event_data else {},
                    correlation_id=row.correlation_id,
                    tags=json.loads(row.tags) if row.tags else [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    acknowledged_at=row.acknowledged_at,
                    acknowledged_by=row.acknowledged_by,
                    resolved_at=row.resolved_at,
                    resolved_by=row.resolved_by,
                    resolution_notes=row.resolution_notes,
                    escalation_level=EscalationLevel(row.escalation_level),
                    escalation_history=json.loads(row.escalation_history) if row.escalation_history else [],
                    false_positive=row.false_positive,
                    suppression_until=row.suppression_until,
                    risk_score=row.risk_score,
                    confidence_score=row.confidence_score
                )
        
        return None
    
    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO security_alerts 
                (id, title, description, severity, category, status, source, source_id,
                 user_id, ip_address, user_agent, resource_type, resource_id, resource_name,
                 event_data, correlation_id, tags, created_at, updated_at, acknowledged_at,
                 acknowledged_by, resolved_at, resolved_by, resolution_notes, escalation_level,
                 escalation_history, false_positive, suppression_until, risk_score, confidence_score)
                VALUES (:id, :title, :description, :severity, :category, :status, :source, :source_id,
                        :user_id, :ip_address, :user_agent, :resource_type, :resource_id, :resource_name,
                        :event_data, :correlation_id, :tags, :created_at, :updated_at, :acknowledged_at,
                        :acknowledged_by, :resolved_at, :resolved_by, :resolution_notes, :escalation_level,
                        :escalation_history, :false_positive, :suppression_until, :risk_score, :confidence_score)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    severity = EXCLUDED.severity,
                    category = EXCLUDED.category,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    source_id = EXCLUDED.source_id,
                    user_id = EXCLUDED.user_id,
                    ip_address = EXCLUDED.ip_address,
                    user_agent = EXCLUDED.user_agent,
                    resource_type = EXCLUDED.resource_type,
                    resource_id = EXCLUDED.resource_id,
                    resource_name = EXCLUDED.resource_name,
                    event_data = EXCLUDED.event_data,
                    correlation_id = EXCLUDED.correlation_id,
                    tags = EXCLUDED.tags,
                    updated_at = EXCLUDED.updated_at,
                    acknowledged_at = EXCLUDED.acknowledged_at,
                    acknowledged_by = EXCLUDED.acknowledged_by,
                    resolved_at = EXCLUDED.resolved_at,
                    resolved_by = EXCLUDED.resolved_by,
                    resolution_notes = EXCLUDED.resolution_notes,
                    escalation_level = EXCLUDED.escalation_level,
                    escalation_history = EXCLUDED.escalation_history,
                    false_positive = EXCLUDED.false_positive,
                    suppression_until = EXCLUDED.suppression_until,
                    risk_score = EXCLUDED.risk_score,
                    confidence_score = EXCLUDED.confidence_score
            """), {
                "id": str(alert.id),
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "status": alert.status.value,
                "source": alert.source.value,
                "source_id": alert.source_id,
                "user_id": alert.user_id,
                "ip_address": alert.ip_address,
                "user_agent": alert.user_agent,
                "resource_type": alert.resource_type,
                "resource_id": alert.resource_id,
                "resource_name": alert.resource_name,
                "event_data": json.dumps(alert.event_data),
                "correlation_id": alert.correlation_id,
                "tags": json.dumps(alert.tags),
                "created_at": alert.created_at,
                "updated_at": alert.updated_at,
                "acknowledged_at": alert.acknowledged_at,
                "acknowledged_by": alert.acknowledged_by,
                "resolved_at": alert.resolved_at,
                "resolved_by": alert.resolved_by,
                "resolution_notes": alert.resolution_notes,
                "escalation_level": alert.escalation_level.value,
                "escalation_history": json.dumps(alert.escalation_history),
                "false_positive": alert.false_positive,
                "suppression_until": alert.suppression_until,
                "risk_score": alert.risk_score,
                "confidence_score": alert.confidence_score
            })
            await db.commit()
    
    async def _store_alert_rule(self, rule: AlertRule):
        """Store alert rule in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO alert_rules 
                (id, name, description, condition, severity, category, source, enabled,
                 threshold, time_window, aggregation, notification_channels, escalation_enabled,
                 escalation_delay_minutes, escalation_levels, suppression_enabled,
                 suppression_duration_minutes, tags, created_by, created_at, updated_at,
                 last_triggered, trigger_count)
                VALUES (:id, :name, :description, :condition, :severity, :category, :source, :enabled,
                        :threshold, :time_window, :aggregation, :notification_channels, :escalation_enabled,
                        :escalation_delay_minutes, :escalation_levels, :suppression_enabled,
                        :suppression_duration_minutes, :tags, :created_by, :created_at, :updated_at,
                        :last_triggered, :trigger_count)
            """), {
                "id": str(rule.id),
                "name": rule.name,
                "description": rule.description,
                "condition": rule.condition,
                "severity": rule.severity.value,
                "category": rule.category.value,
                "source": rule.source.value,
                "enabled": rule.enabled,
                "threshold": rule.threshold,
                "time_window": rule.time_window,
                "aggregation": rule.aggregation,
                "notification_channels": json.dumps([ch.value for ch in rule.notification_channels]),
                "escalation_enabled": rule.escalation_enabled,
                "escalation_delay_minutes": rule.escalation_delay_minutes,
                "escalation_levels": json.dumps([level.value for level in rule.escalation_levels]),
                "suppression_enabled": rule.suppression_enabled,
                "suppression_duration_minutes": rule.suppression_duration_minutes,
                "tags": json.dumps(rule.tags),
                "created_by": rule.created_by,
                "created_at": rule.created_at,
                "updated_at": rule.updated_at,
                "last_triggered": rule.last_triggered,
                "trigger_count": rule.trigger_count
            })
            await db.commit()
    
    async def _store_alert_suppression(self, suppression: AlertSuppression):
        """Store alert suppression in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO alert_suppressions 
                (id, rule_id, condition, reason, suppressed_by, suppressed_at, expires_at, is_active)
                VALUES (:id, :rule_id, :condition, :reason, :suppressed_by, :suppressed_at, :expires_at, :is_active)
            """), {
                "id": str(suppression.id),
                "rule_id": suppression.rule_id,
                "condition": suppression.condition,
                "reason": suppression.reason,
                "suppressed_by": suppression.suppressed_by,
                "suppressed_at": suppression.suppressed_at,
                "expires_at": suppression.expires_at,
                "is_active": suppression.is_active
            })
            await db.commit()
    
    async def _store_alert_correlation(self, alert: SecurityAlert):
        """Store alert correlation in database"""
        
        # Get database session from main app's db_manager
        from main import db_manager
        async with db_manager.session_factory() as db:
            await db.execute(text("""
                INSERT INTO alert_correlations 
                (id, correlation_id, alert_ids, correlation_type, correlation_score, pattern_description, created_at, updated_at)
                VALUES (:id, :correlation_id, :alert_ids, :correlation_type, :correlation_score, :pattern_description, :created_at, :updated_at)
                ON CONFLICT (correlation_id) DO UPDATE SET
                    alert_ids = EXCLUDED.alert_ids,
                    updated_at = EXCLUDED.updated_at
            """), {
                "id": str(uuid4()),
                "correlation_id": alert.correlation_id,
                "alert_ids": json.dumps([str(alert.id)]),
                "correlation_type": "user_ip_category",
                "correlation_score": 0.8,
                "pattern_description": f"Alerts from user {alert.user_id} at IP {alert.ip_address} in category {alert.category.value}",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            await db.commit()
    
    async def _log_alert_update(self, alert: SecurityAlert, update_request: AlertUpdateRequest, user_id: str):
        """Log alert update for audit"""
        
        # Mock audit logging - in production, this would log to audit system
        self.logger.info("Alert update logged", 
                        alert_id=str(alert.id),
                        updates=update_request.dict(exclude_unset=True),
                        updated_by=user_id)
    
    def _build_alert_query_sql(self, query: AlertQuery) -> str:
        """Build SQL query for alerts"""
        
        where_conditions = []
        params = {}
        
        if query.severity:
            where_conditions.append("severity = :severity")
            params["severity"] = query.severity.value
        
        if query.category:
            where_conditions.append("category = :category")
            params["category"] = query.category.value
        
        if query.status:
            where_conditions.append("status = :status")
            params["status"] = query.status.value
        
        if query.source:
            where_conditions.append("source = :source")
            params["source"] = query.source.value
        
        if query.user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = query.user_id
        
        if query.ip_address:
            where_conditions.append("ip_address = :ip_address")
            params["ip_address"] = query.ip_address
        
        if query.resource_type:
            where_conditions.append("resource_type = :resource_type")
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            where_conditions.append("resource_id = :resource_id")
            params["resource_id"] = query.resource_id
        
        if query.correlation_id:
            where_conditions.append("correlation_id = :correlation_id")
            params["correlation_id"] = query.correlation_id
        
        if query.tags:
            for i, tag in enumerate(query.tags):
                where_conditions.append(f"tags LIKE :tag_{i}")
                params[f"tag_{i}"] = f"%{tag}%"
        
        if query.start_date:
            where_conditions.append("created_at >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("created_at <= :end_date")
            params["end_date"] = query.end_date
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"""
            SELECT * FROM security_alerts 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
    
    def _build_alert_count_sql(self, query: AlertQuery) -> str:
        """Build SQL query for alert count"""
        
        where_conditions = []
        params = {}
        
        if query.severity:
            where_conditions.append("severity = :severity")
            params["severity"] = query.severity.value
        
        if query.category:
            where_conditions.append("category = :category")
            params["category"] = query.category.value
        
        if query.status:
            where_conditions.append("status = :status")
            params["status"] = query.status.value
        
        if query.source:
            where_conditions.append("source = :source")
            params["source"] = query.source.value
        
        if query.user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = query.user_id
        
        if query.ip_address:
            where_conditions.append("ip_address = :ip_address")
            params["ip_address"] = query.ip_address
        
        if query.resource_type:
            where_conditions.append("resource_type = :resource_type")
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            where_conditions.append("resource_id = :resource_id")
            params["resource_id"] = query.resource_id
        
        if query.correlation_id:
            where_conditions.append("correlation_id = :correlation_id")
            params["correlation_id"] = query.correlation_id
        
        if query.tags:
            for i, tag in enumerate(query.tags):
                where_conditions.append(f"tags LIKE :tag_{i}")
                params[f"tag_{i}"] = f"%{tag}%"
        
        if query.start_date:
            where_conditions.append("created_at >= :start_date")
            params["start_date"] = query.start_date
        
        if query.end_date:
            where_conditions.append("created_at <= :end_date")
            params["end_date"] = query.end_date
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        return f"SELECT COUNT(*) FROM security_alerts WHERE {where_clause}"
    
    def _build_alert_query_params(self, query: AlertQuery) -> Dict[str, Any]:
        """Build query parameters for alerts"""
        
        params = {
            "limit": query.limit,
            "offset": query.offset
        }
        
        if query.severity:
            params["severity"] = query.severity.value
        
        if query.category:
            params["category"] = query.category.value
        
        if query.status:
            params["status"] = query.status.value
        
        if query.source:
            params["source"] = query.source.value
        
        if query.user_id:
            params["user_id"] = query.user_id
        
        if query.ip_address:
            params["ip_address"] = query.ip_address
        
        if query.resource_type:
            params["resource_type"] = query.resource_type
        
        if query.resource_id:
            params["resource_id"] = query.resource_id
        
        if query.correlation_id:
            params["correlation_id"] = query.correlation_id
        
        if query.tags:
            for i, tag in enumerate(query.tags):
                params[f"tag_{i}"] = f"%{tag}%"
        
        if query.start_date:
            params["start_date"] = query.start_date
        
        if query.end_date:
            params["end_date"] = query.end_date
        
        return params
