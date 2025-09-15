"""
Real-time Security Monitoring and Alert System
Implements threat detection, anomaly detection, and automated response
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
import numpy as np
from collections import defaultdict, deque
import threading
import time

Base = declarative_base()

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    SECURITY_VIOLATION = "security_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_COMPROMISE = "system_compromise"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALICIOUS_ACTIVITY = "malicious_activity"

class AlertStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"

@dataclass
class SecurityEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    source_ip: str
    user_id: Optional[int]
    project_id: Optional[int]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    risk_score: int
    raw_data: Dict[str, Any]

@dataclass
class SecurityAlert:
    alert_id: str
    alert_type: AlertType
    threat_level: ThreatLevel
    title: str
    description: str
    events: List[SecurityEvent]
    affected_resources: List[str]
    recommended_actions: List[str]
    created_at: datetime
    status: AlertStatus = AlertStatus.OPEN
    assigned_to: Optional[int] = None
    resolved_at: Optional[datetime] = None

class SecurityAlertLog(Base):
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(64), unique=True, nullable=False)
    alert_type = Column(String(50), nullable=False)
    threat_level = Column(String(20), nullable=False)
    
    # Alert content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    events = Column(JSON, nullable=False)
    affected_resources = Column(JSON, nullable=False)
    recommended_actions = Column(JSON, nullable=False)
    
    # Context
    project_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    source_ip = Column(String(45), nullable=True)
    
    # Status and workflow
    status = Column(String(20), default="open")
    assigned_to = Column(Integer, nullable=True)
    escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Metadata
    correlation_id = Column(String(64), nullable=True)
    false_positive = Column(Boolean, default=False)
    suppressed = Column(Boolean, default=False)

class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"
    
    id = Column(Integer, primary_key=True)
    indicator_type = Column(String(20), nullable=False)  # ip, domain, hash, etc.
    indicator_value = Column(String(255), nullable=False)
    threat_type = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Threat details
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=[])
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    
    # Source information
    source = Column(String(100), nullable=False)
    source_reliability = Column(String(20), default="unknown")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SecurityMonitor:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.event_buffer = deque(maxlen=10000)
        self.alert_handlers = []
        self.running = False
        self.monitor_thread = None
        
        # Anomaly detection baselines
        self.user_baselines = defaultdict(dict)
        self.ip_baselines = defaultdict(dict)
        self.resource_baselines = defaultdict(dict)
        
        # Threat intelligence cache
        self.threat_indicators = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            "failed_logins": 5,
            "privilege_escalation": 1,
            "data_access_anomaly": 3,
            "suspicious_ip": 1,
            "off_hours_access": 10,
            "bulk_download": 100  # MB
        }
        
        # Initialize threat intelligence
        self._load_threat_intelligence()
    
    def start_monitoring(self):
        """Start real-time security monitoring"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Security monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Process events in buffer
                self._process_event_buffer()
                
                # Update baselines
                self._update_baselines()
                
                # Check for anomalies
                self._detect_anomalies()
                
                # Update threat intelligence
                self._update_threat_intelligence()
                
                # Sleep before next iteration
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def ingest_event(self, event: SecurityEvent):
        """Ingest security event for analysis"""
        self.event_buffer.append(event)
        
        # Immediate threat checks
        self._check_immediate_threats(event)
    
    def _check_immediate_threats(self, event: SecurityEvent):
        """Check for immediate security threats"""
        alerts_to_create = []
        
        # Check against threat intelligence
        if event.source_ip in self.threat_indicators:
            threat_info = self.threat_indicators[event.source_ip]
            alerts_to_create.append(self._create_threat_intel_alert(event, threat_info))
        
        # Check for privilege escalation
        if "role_change" in event.event_type and event.risk_score > 50:
            alerts_to_create.append(self._create_privilege_escalation_alert(event))
        
        # Check for failed login patterns
        if event.event_type == "login" and "failed" in event.details.get("status", ""):
            failed_count = self._count_failed_logins(event.source_ip, event.user_id)
            if failed_count >= self.alert_thresholds["failed_logins"]:
                alerts_to_create.append(self._create_brute_force_alert(event, failed_count))
        
        # Check for suspicious data access
        if event.event_type == "document_download" and event.risk_score > 70:
            alerts_to_create.append(self._create_suspicious_access_alert(event))
        
        # Check for off-hours access
        if self._is_off_hours_access(event):
            alerts_to_create.append(self._create_off_hours_alert(event))
        
        # Process alerts
        for alert in alerts_to_create:
            if alert:
                self._process_alert(alert)
    
    def _create_threat_intel_alert(self, event: SecurityEvent, threat_info: Dict) -> SecurityAlert:
        """Create alert for threat intelligence match"""
        return SecurityAlert(
            alert_id=f"threat_{event.event_id}",
            alert_type=AlertType.MALICIOUS_ACTIVITY,
            threat_level=ThreatLevel.CRITICAL,
            title=f"Known Malicious IP Detected: {event.source_ip}",
            description=f"Activity detected from known malicious IP {event.source_ip}. "
                       f"Threat type: {threat_info.get('threat_type', 'Unknown')}. "
                       f"Confidence: {threat_info.get('confidence_score', 0)}%",
            events=[event],
            affected_resources=[f"user:{event.user_id}", f"project:{event.project_id}"],
            recommended_actions=[
                "Block IP address immediately",
                "Review all activities from this IP",
                "Check for compromise of affected accounts",
                "Notify security team"
            ],
            created_at=datetime.utcnow()
        )
    
    def _create_privilege_escalation_alert(self, event: SecurityEvent) -> SecurityAlert:
        """Create alert for privilege escalation"""
        return SecurityAlert(
            alert_id=f"privesc_{event.event_id}",
            alert_type=AlertType.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.HIGH,
            title="Privilege Escalation Detected",
            description=f"User privileges were escalated for user {event.user_id}. "
                       f"Details: {event.details}",
            events=[event],
            affected_resources=[f"user:{event.user_id}", f"project:{event.project_id}"],
            recommended_actions=[
                "Verify authorization for privilege change",
                "Review user's recent activities",
                "Check if change was legitimate",
                "Monitor user behavior closely"
            ],
            created_at=datetime.utcnow()
        )
    
    def _create_brute_force_alert(self, event: SecurityEvent, failed_count: int) -> SecurityAlert:
        """Create alert for brute force attack"""
        return SecurityAlert(
            alert_id=f"bruteforce_{event.source_ip}_{int(datetime.utcnow().timestamp())}",
            alert_type=AlertType.UNAUTHORIZED_ACCESS,
            threat_level=ThreatLevel.HIGH,
            title=f"Brute Force Attack Detected from {event.source_ip}",
            description=f"Multiple failed login attempts ({failed_count}) detected from "
                       f"IP {event.source_ip} in the last 15 minutes.",
            events=[event],
            affected_resources=[f"ip:{event.source_ip}"],
            recommended_actions=[
                "Block IP address temporarily",
                "Review affected user accounts",
                "Check for successful logins from this IP",
                "Consider implementing additional MFA"
            ],
            created_at=datetime.utcnow()
        )
    
    def _create_suspicious_access_alert(self, event: SecurityEvent) -> SecurityAlert:
        """Create alert for suspicious data access"""
        return SecurityAlert(
            alert_id=f"suspicious_{event.event_id}",
            alert_type=AlertType.SECURITY_VIOLATION,
            threat_level=ThreatLevel.MEDIUM,
            title="Suspicious Data Access Detected",
            description=f"High-risk data access detected. User {event.user_id} accessed "
                       f"{event.resource_type} {event.resource_id} with risk score {event.risk_score}",
            events=[event],
            affected_resources=[f"user:{event.user_id}", f"{event.resource_type}:{event.resource_id}"],
            recommended_actions=[
                "Review user's access permissions",
                "Verify business justification for access",
                "Monitor user's subsequent activities",
                "Consider additional access controls"
            ],
            created_at=datetime.utcnow()
        )
    
    def _create_off_hours_alert(self, event: SecurityEvent) -> SecurityAlert:
        """Create alert for off-hours access"""
        return SecurityAlert(
            alert_id=f"offhours_{event.event_id}",
            alert_type=AlertType.ANOMALY_DETECTED,
            threat_level=ThreatLevel.LOW,
            title="Off-Hours System Access",
            description=f"User {event.user_id} accessed system outside normal business hours "
                       f"at {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            events=[event],
            affected_resources=[f"user:{event.user_id}"],
            recommended_actions=[
                "Verify legitimate business need",
                "Check if user is authorized for off-hours access",
                "Review activities performed during off-hours",
                "Update access policies if needed"
            ],
            created_at=datetime.utcnow()
        )
    
    def _process_alert(self, alert: SecurityAlert):
        """Process and store security alert"""
        # Store alert in database
        alert_record = SecurityAlertLog(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
            threat_level=alert.threat_level.value,
            title=alert.title,
            description=alert.description,
            events=[asdict(event) for event in alert.events],
            affected_resources=alert.affected_resources,
            recommended_actions=alert.recommended_actions,
            project_id=alert.events[0].project_id if alert.events else None,
            user_id=alert.events[0].user_id if alert.events else None,
            source_ip=alert.events[0].source_ip if alert.events else None
        )
        
        self.db.add(alert_record)
        self.db.commit()
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Error in alert handler: {e}")
        
        # Auto-escalate critical alerts
        if alert.threat_level == ThreatLevel.CRITICAL:
            self._escalate_alert(alert)
    
    def _escalate_alert(self, alert: SecurityAlert):
        """Escalate critical security alert"""
        # Update alert status
        alert_record = self.db.query(SecurityAlertLog).filter(
            SecurityAlertLog.alert_id == alert.alert_id
        ).first()
        
        if alert_record:
            alert_record.escalated = True
            alert_record.escalated_at = datetime.utcnow()
            self.db.commit()
        
        # Send notifications
        self._send_alert_notification(alert, escalated=True)
    
    def _send_alert_notification(self, alert: SecurityAlert, escalated: bool = False):
        """Send alert notification via email/webhook"""
        # Email notification
        subject = f"{'ESCALATED ' if escalated else ''}Security Alert: {alert.title}"
        body = f"""
        Security Alert Details:
        
        Alert ID: {alert.alert_id}
        Type: {alert.alert_type.value}
        Threat Level: {alert.threat_level.value}
        
        Description:
        {alert.description}
        
        Affected Resources:
        {', '.join(alert.affected_resources)}
        
        Recommended Actions:
        {chr(10).join(f'- {action}' for action in alert.recommended_actions)}
        
        Created: {alert.created_at}
        """
        
        self._send_email_alert(subject, body)
        
        # Webhook notification
        self._send_webhook_alert(alert, escalated)
    
    def _send_email_alert(self, subject: str, body: str):
        """Send email alert (mock implementation)"""
        # In production, configure SMTP settings
        print(f"EMAIL ALERT: {subject}")
        print(body)
    
    def _send_webhook_alert(self, alert: SecurityAlert, escalated: bool = False):
        """Send webhook alert (mock implementation)"""
        webhook_payload = {
            "alert_id": alert.alert_id,
            "type": alert.alert_type.value,
            "threat_level": alert.threat_level.value,
            "title": alert.title,
            "escalated": escalated,
            "timestamp": alert.created_at.isoformat()
        }
        
        # In production, send to configured webhook URLs
        print(f"WEBHOOK ALERT: {json.dumps(webhook_payload, indent=2)}")
    
    def _count_failed_logins(self, source_ip: str, user_id: Optional[int]) -> int:
        """Count failed login attempts in the last 15 minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        
        count = 0
        for event in self.event_buffer:
            if (event.timestamp >= cutoff_time and 
                event.event_type == "login" and
                event.source_ip == source_ip and
                "failed" in event.details.get("status", "")):
                count += 1
        
        return count
    
    def _is_off_hours_access(self, event: SecurityEvent) -> bool:
        """Check if event occurred during off-hours"""
        # Define business hours (9 AM - 5 PM, Monday-Friday)
        event_time = event.timestamp
        
        # Check if weekend
        if event_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return True
        
        # Check if outside business hours
        if event_time.hour < 9 or event_time.hour >= 17:
            return True
        
        return False
    
    def _process_event_buffer(self):
        """Process events in buffer for pattern detection"""
        if not self.event_buffer:
            return
        
        # Analyze patterns in recent events
        recent_events = [e for e in self.event_buffer 
                        if e.timestamp >= datetime.utcnow() - timedelta(minutes=10)]
        
        # Check for bulk data access patterns
        self._check_bulk_access_patterns(recent_events)
        
        # Check for geographic anomalies
        self._check_geographic_anomalies(recent_events)
        
        # Check for time-based anomalies
        self._check_temporal_anomalies(recent_events)
    
    def _check_bulk_access_patterns(self, events: List[SecurityEvent]):
        """Check for bulk data access patterns"""
        user_downloads = defaultdict(list)
        
        for event in events:
            if event.event_type == "document_download":
                user_downloads[event.user_id].append(event)
        
        for user_id, downloads in user_downloads.items():
            if len(downloads) >= 20:  # 20+ downloads in 10 minutes
                alert = SecurityAlert(
                    alert_id=f"bulk_{user_id}_{int(datetime.utcnow().timestamp())}",
                    alert_type=AlertType.ANOMALY_DETECTED,
                    threat_level=ThreatLevel.MEDIUM,
                    title=f"Bulk Data Access Detected - User {user_id}",
                    description=f"User {user_id} downloaded {len(downloads)} documents "
                               f"in the last 10 minutes",
                    events=downloads,
                    affected_resources=[f"user:{user_id}"],
                    recommended_actions=[
                        "Verify legitimate business need for bulk access",
                        "Check data sensitivity of accessed documents",
                        "Review user's access permissions",
                        "Monitor for data exfiltration"
                    ],
                    created_at=datetime.utcnow()
                )
                self._process_alert(alert)
    
    def _check_geographic_anomalies(self, events: List[SecurityEvent]):
        """Check for geographic access anomalies (mock implementation)"""
        # In production, would use IP geolocation services
        pass
    
    def _check_temporal_anomalies(self, events: List[SecurityEvent]):
        """Check for temporal access anomalies"""
        # Check for rapid successive logins from different IPs
        user_logins = defaultdict(list)
        
        for event in events:
            if event.event_type == "login" and "success" in event.details.get("status", ""):
                user_logins[event.user_id].append(event)
        
        for user_id, logins in user_logins.items():
            if len(logins) >= 3:
                # Check if logins are from different IPs within short time
                ips = set(login.source_ip for login in logins)
                if len(ips) >= 2:
                    time_diff = max(login.timestamp for login in logins) - min(login.timestamp for login in logins)
                    if time_diff <= timedelta(minutes=5):
                        alert = SecurityAlert(
                            alert_id=f"concurrent_{user_id}_{int(datetime.utcnow().timestamp())}",
                            alert_type=AlertType.ANOMALY_DETECTED,
                            threat_level=ThreatLevel.HIGH,
                            title=f"Concurrent Login Anomaly - User {user_id}",
                            description=f"User {user_id} logged in from {len(ips)} different "
                                       f"IP addresses within 5 minutes",
                            events=logins,
                            affected_resources=[f"user:{user_id}"],
                            recommended_actions=[
                                "Verify user's location and device",
                                "Check for account compromise",
                                "Consider forcing password reset",
                                "Enable additional MFA requirements"
                            ],
                            created_at=datetime.utcnow()
                        )
                        self._process_alert(alert)
    
    def _update_baselines(self):
        """Update behavioral baselines for anomaly detection"""
        # Update user behavior baselines
        # Update IP access patterns
        # Update resource access patterns
        # This would be implemented with machine learning in production
        pass
    
    def _detect_anomalies(self):
        """Detect behavioral anomalies"""
        # Implement statistical anomaly detection
        # This would use machine learning models in production
        pass
    
    def _load_threat_intelligence(self):
        """Load threat intelligence indicators"""
        # Load from database
        threats = self.db.query(ThreatIntelligence).filter(
            ThreatIntelligence.confidence_score >= 70
        ).all()
        
        for threat in threats:
            self.threat_indicators[threat.indicator_value] = {
                "threat_type": threat.threat_type,
                "confidence_score": threat.confidence_score,
                "description": threat.description,
                "tags": threat.tags
            }
    
    def _update_threat_intelligence(self):
        """Update threat intelligence from external sources"""
        # In production, would integrate with threat intel feeds
        pass
    
    def add_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
    
    def get_active_alerts(self, project_id: Optional[int] = None) -> List[Dict]:
        """Get active security alerts"""
        query = self.db.query(SecurityAlertLog).filter(
            SecurityAlertLog.status.in_(["open", "investigating"])
        )
        
        if project_id:
            query = query.filter(SecurityAlertLog.project_id == project_id)
        
        alerts = query.order_by(SecurityAlertLog.created_at.desc()).limit(50).all()
        
        return [{
            "alert_id": alert.alert_id,
            "type": alert.alert_type,
            "threat_level": alert.threat_level,
            "title": alert.title,
            "description": alert.description,
            "created_at": alert.created_at.isoformat(),
            "status": alert.status,
            "escalated": alert.escalated
        } for alert in alerts]
    
    def get_security_metrics(self, project_id: Optional[int] = None) -> Dict:
        """Get security monitoring metrics"""
        # Get alert counts by threat level
        query = self.db.query(SecurityAlertLog)
        if project_id:
            query = query.filter(SecurityAlertLog.project_id == project_id)
        
        recent_alerts = query.filter(
            SecurityAlertLog.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        metrics = {
            "total_alerts_30d": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a.threat_level == "critical"]),
            "high_alerts": len([a for a in recent_alerts if a.threat_level == "high"]),
            "medium_alerts": len([a for a in recent_alerts if a.threat_level == "medium"]),
            "low_alerts": len([a for a in recent_alerts if a.threat_level == "low"]),
            "open_alerts": len([a for a in recent_alerts if a.status == "open"]),
            "escalated_alerts": len([a for a in recent_alerts if a.escalated]),
            "threat_intelligence_indicators": len(self.threat_indicators),
            "monitoring_status": "active" if self.running else "inactive"
        }
        
        return metrics

# Example usage and integration
class SecurityIntegrationService:
    """Service to integrate security monitoring with the main application"""
    
    def __init__(self, db_session: Session):
        self.monitor = SecurityMonitor(db_session)
        self.monitor.start_monitoring()
        
        # Add custom alert handlers
        self.monitor.add_alert_handler(self._handle_critical_alert)
        self.monitor.add_alert_handler(self._log_alert_to_siem)
    
    def _handle_critical_alert(self, alert: SecurityAlert):
        """Handle critical security alerts"""
        if alert.threat_level == ThreatLevel.CRITICAL:
            # Implement automated response
            if alert.alert_type == AlertType.MALICIOUS_ACTIVITY:
                # Auto-block malicious IP
                self._block_ip(alert.events[0].source_ip)
            elif alert.alert_type == AlertType.DATA_BREACH:
                # Trigger incident response
                self._trigger_incident_response(alert)
    
    def _log_alert_to_siem(self, alert: SecurityAlert):
        """Log alert to SIEM system"""
        # In production, integrate with SIEM
        print(f"SIEM LOG: {alert.alert_id} - {alert.title}")
    
    def _block_ip(self, ip_address: str):
        """Block malicious IP address"""
        # In production, integrate with firewall/WAF
        print(f"BLOCKING IP: {ip_address}")
    
    def _trigger_incident_response(self, alert: SecurityAlert):
        """Trigger incident response procedures"""
        # In production, integrate with incident response platform
        print(f"INCIDENT RESPONSE TRIGGERED: {alert.alert_id}")
    
    def log_security_event(self, event_type: str, user_id: int, source_ip: str,
                          details: Dict, risk_score: int = 0, 
                          project_id: Optional[int] = None,
                          resource_type: Optional[str] = None,
                          resource_id: Optional[str] = None):
        """Log security event for monitoring"""
        event = SecurityEvent(
            event_id=f"{event_type}_{int(datetime.utcnow().timestamp())}_{user_id}",
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_id=user_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            risk_score=risk_score,
            raw_data=details
        )
        
        self.monitor.ingest_event(event)
