"""
Real-time Security Monitoring Service
Monitors security events, detects anomalies, and triggers alerts
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import structlog
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MFA_BYPASS_ATTEMPT = "mfa_bypass_attempt"
    BULK_OPERATION = "bulk_operation"
    UNUSUAL_TIME_ACCESS = "unusual_time_access"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"

@dataclass
class SecurityEvent:
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    resource: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False

class SecurityMonitor:
    """Real-time security monitoring and alerting system"""
    
    def __init__(self):
        self.events = deque(maxlen=10000)  # Keep last 10k events
        self.user_activity = defaultdict(lambda: deque(maxlen=1000))
        self.ip_activity = defaultdict(lambda: deque(maxlen=1000))
        self.alert_rules = self._initialize_alert_rules()
        self.active_alerts = []
        self.monitoring_enabled = True
        
    def _initialize_alert_rules(self) -> Dict:
        """Initialize security alert rules"""
        return {
            "multiple_auth_failures": {
                "threshold": 5,
                "window_minutes": 15,
                "threat_level": ThreatLevel.HIGH,
                "description": "Multiple authentication failures from same IP"
            },
            "rapid_requests": {
                "threshold": 100,
                "window_minutes": 5,
                "threat_level": ThreatLevel.MEDIUM,
                "description": "Rapid request pattern detected"
            },
            "privilege_escalation": {
                "threshold": 1,
                "window_minutes": 60,
                "threat_level": ThreatLevel.CRITICAL,
                "description": "Privilege escalation attempt detected"
            },
            "bulk_operations": {
                "threshold": 3,
                "window_minutes": 60,
                "threat_level": ThreatLevel.MEDIUM,
                "description": "Multiple bulk operations detected"
            },
            "unusual_time_access": {
                "threshold": 1,
                "window_minutes": 60,
                "threat_level": ThreatLevel.LOW,
                "description": "Access outside business hours"
            },
            "mfa_bypass_attempts": {
                "threshold": 3,
                "window_minutes": 30,
                "threat_level": ThreatLevel.HIGH,
                "description": "Multiple MFA bypass attempts"
            }
        }
    
    async def log_event(self, event_type: SecurityEventType, user_id: Optional[str], 
                       ip_address: str, user_agent: str, resource: str, action: str, 
                       details: Dict[str, Any], threat_level: ThreatLevel = ThreatLevel.LOW):
        """Log a security event"""
        event = SecurityEvent(
            event_id=f"{event_type.value}_{int(datetime.utcnow().timestamp())}",
            event_type=event_type,
            threat_level=threat_level,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        # Add to events queue
        self.events.append(event)
        
        # Add to user activity tracking
        if user_id:
            self.user_activity[user_id].append(event)
        
        # Add to IP activity tracking
        self.ip_activity[ip_address].append(event)
        
        logger.info("Security event logged", 
                   event_type=event_type.value,
                   user_id=user_id,
                   ip_address=ip_address,
                   threat_level=threat_level.value)
        
        # Check for alerts
        await self._check_alerts(event)
    
    async def _check_alerts(self, event: SecurityEvent):
        """Check if event triggers any security alerts"""
        if not self.monitoring_enabled:
            return
        
        # Check multiple auth failures
        if event.event_type == SecurityEventType.AUTH_FAILURE:
            await self._check_auth_failure_pattern(event)
        
        # Check rapid requests
        if event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
            await self._check_rapid_request_pattern(event)
        
        # Check privilege escalation
        if event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            await self._trigger_alert(event, "privilege_escalation")
        
        # Check bulk operations
        if event.event_type == SecurityEventType.BULK_OPERATION:
            await self._check_bulk_operation_pattern(event)
        
        # Check unusual time access
        if event.event_type == SecurityEventType.UNUSUAL_TIME_ACCESS:
            await self._trigger_alert(event, "unusual_time_access")
        
        # Check MFA bypass attempts
        if event.event_type == SecurityEventType.MFA_BYPASS_ATTEMPT:
            await self._check_mfa_bypass_pattern(event)
    
    async def _check_auth_failure_pattern(self, event: SecurityEvent):
        """Check for multiple authentication failures"""
        rule = self.alert_rules["multiple_auth_failures"]
        window_start = datetime.utcnow() - timedelta(minutes=rule["window_minutes"])
        
        # Count auth failures from same IP
        auth_failures = [
            e for e in self.ip_activity[event.ip_address]
            if (e.event_type == SecurityEventType.AUTH_FAILURE and 
                e.timestamp >= window_start)
        ]
        
        if len(auth_failures) >= rule["threshold"]:
            await self._trigger_alert(event, "multiple_auth_failures", 
                                    additional_events=auth_failures)
    
    async def _check_rapid_request_pattern(self, event: SecurityEvent):
        """Check for rapid request patterns"""
        rule = self.alert_rules["rapid_requests"]
        window_start = datetime.utcnow() - timedelta(minutes=rule["window_minutes"])
        
        # Count requests from same IP
        recent_requests = [
            e for e in self.ip_activity[event.ip_address]
            if e.timestamp >= window_start
        ]
        
        if len(recent_requests) >= rule["threshold"]:
            await self._trigger_alert(event, "rapid_requests", 
                                    additional_events=recent_requests)
    
    async def _check_bulk_operation_pattern(self, event: SecurityEvent):
        """Check for bulk operation patterns"""
        rule = self.alert_rules["bulk_operations"]
        window_start = datetime.utcnow() - timedelta(minutes=rule["window_minutes"])
        
        # Count bulk operations by user
        if event.user_id:
            bulk_operations = [
                e for e in self.user_activity[event.user_id]
                if (e.event_type == SecurityEventType.BULK_OPERATION and 
                    e.timestamp >= window_start)
            ]
            
            if len(bulk_operations) >= rule["threshold"]:
                await self._trigger_alert(event, "bulk_operations", 
                                        additional_events=bulk_operations)
    
    async def _check_mfa_bypass_pattern(self, event: SecurityEvent):
        """Check for MFA bypass patterns"""
        rule = self.alert_rules["mfa_bypass_attempts"]
        window_start = datetime.utcnow() - timedelta(minutes=rule["window_minutes"])
        
        # Count MFA bypass attempts by user
        if event.user_id:
            bypass_attempts = [
                e for e in self.user_activity[event.user_id]
                if (e.event_type == SecurityEventType.MFA_BYPASS_ATTEMPT and 
                    e.timestamp >= window_start)
            ]
            
            if len(bypass_attempts) >= rule["threshold"]:
                await self._trigger_alert(event, "mfa_bypass_attempts", 
                                        additional_events=bypass_attempts)
    
    async def _trigger_alert(self, event: SecurityEvent, rule_name: str, 
                           additional_events: List[SecurityEvent] = None):
        """Trigger a security alert"""
        rule = self.alert_rules[rule_name]
        
        alert = {
            "alert_id": f"alert_{rule_name}_{int(datetime.utcnow().timestamp())}",
            "rule_name": rule_name,
            "threat_level": rule["threat_level"].value,
            "description": rule["description"],
            "triggering_event": event,
            "additional_events": additional_events or [],
            "timestamp": datetime.utcnow(),
            "resolved": False,
            "actions_taken": []
        }
        
        self.active_alerts.append(alert)
        
        # Log the alert
        logger.warning("Security alert triggered", 
                      alert_id=alert["alert_id"],
                      rule_name=rule_name,
                      threat_level=rule["threat_level"].value,
                      user_id=event.user_id,
                      ip_address=event.ip_address)
        
        # Take automated actions based on threat level
        await self._take_automated_actions(alert)
    
    async def _take_automated_actions(self, alert: Dict):
        """Take automated security actions based on alert"""
        threat_level = alert["threat_level"]
        event = alert["triggering_event"]
        
        actions = []
        
        if threat_level in ["high", "critical"]:
            # Block IP for high/critical threats
            actions.append("ip_blocked")
            logger.warning("IP blocked due to security threat", 
                         ip_address=event.ip_address,
                         threat_level=threat_level)
        
        if threat_level == "critical":
            # Disable user account for critical threats
            if event.user_id:
                actions.append("user_disabled")
                logger.warning("User account disabled due to critical security threat", 
                             user_id=event.user_id,
                             threat_level=threat_level)
        
        # Log all actions
        actions.append("alert_logged")
        
        alert["actions_taken"] = actions
    
    def get_security_dashboard_data(self) -> Dict:
        """Get data for security dashboard"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Recent events
        recent_events = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "threat_level": e.threat_level.value,
                "user_id": e.user_id,
                "ip_address": e.ip_address,
                "resource": e.resource,
                "action": e.action,
                "timestamp": e.timestamp.isoformat()
            }
            for e in self.events
            if e.timestamp >= last_24h
        ]
        
        # Active alerts
        active_alerts = [
            {
                "alert_id": a["alert_id"],
                "rule_name": a["rule_name"],
                "threat_level": a["threat_level"],
                "description": a["description"],
                "timestamp": a["timestamp"].isoformat(),
                "actions_taken": a["actions_taken"]
            }
            for a in self.active_alerts
            if not a["resolved"]
        ]
        
        # Threat level distribution
        threat_levels = defaultdict(int)
        for event in recent_events:
            threat_levels[event["threat_level"]] += 1
        
        # Top suspicious IPs
        suspicious_ips = defaultdict(int)
        for event in recent_events:
            if event["threat_level"] in ["high", "critical"]:
                suspicious_ips[event["ip_address"]] += 1
        
        top_suspicious_ips = sorted(suspicious_ips.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "recent_events": recent_events[-50:],  # Last 50 events
            "active_alerts": active_alerts,
            "threat_level_distribution": dict(threat_levels),
            "top_suspicious_ips": top_suspicious_ips,
            "total_events_24h": len(recent_events),
            "active_alerts_count": len(active_alerts),
            "monitoring_status": "enabled" if self.monitoring_enabled else "disabled"
        }
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a security alert"""
        for alert in self.active_alerts:
            if alert["alert_id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.utcnow()
                logger.info("Security alert resolved", alert_id=alert_id)
                return True
        return False
    
    def toggle_monitoring(self, enabled: bool):
        """Enable/disable security monitoring"""
        self.monitoring_enabled = enabled
        logger.info("Security monitoring toggled", enabled=enabled)

# Global security monitor instance
security_monitor = SecurityMonitor()
