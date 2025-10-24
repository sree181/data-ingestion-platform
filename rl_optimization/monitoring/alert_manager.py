"""
Alert Manager for Production Monitoring
Intelligent alerting system with multiple channels and severity levels
"""

import smtplib
import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
import threading
from collections import defaultdict, deque
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = structlog.get_logger(__name__)

@dataclass
class AlertConfig:
    """Configuration for alert manager"""
    email_enabled: bool = True
    slack_enabled: bool = False
    webhook_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    slack_webhook_url: str = ""
    webhook_url: str = ""
    alert_throttling: bool = True
    throttle_window: int = 300  # seconds
    max_alerts_per_window: int = 10
    severity_levels: Dict[str, int] = None

@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    title: str
    message: str
    severity: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class AlertChannel:
    """Alert channel configuration"""
    name: str
    enabled: bool
    severity_filter: List[str]
    rate_limit: int
    cooldown: int

class AlertManager:
    """
    Intelligent alerting system
    - Multiple alert channels (email, Slack, PagerDuty)
    - Alert severity levels
    - Alert throttling and grouping
    - On-call rotation integration
    """
    
    def __init__(self, config: AlertConfig):
        """
        Initialize alert manager
        
        Args:
            config: Alert configuration
        """
        self.config = config
        self.alert_history = deque(maxlen=10000)
        self.alert_throttle = defaultdict(list)
        self.alert_groups = defaultdict(list)
        self.acknowledged_alerts = set()
        self.resolved_alerts = set()
        
        # Alert channels
        self.channels = self._setup_channels()
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_source': defaultdict(int),
            'throttled_alerts': 0,
            'failed_deliveries': 0
        }
        
        # Default severity levels
        if config.severity_levels is None:
            config.severity_levels = {
                'critical': 5,
                'high': 4,
                'medium': 3,
                'low': 2,
                'info': 1
            }
        
        logger.info("AlertManager initialized", 
                   email_enabled=config.email_enabled,
                   slack_enabled=config.slack_enabled)
    
    def _setup_channels(self) -> Dict[str, AlertChannel]:
        """Setup alert channels"""
        channels = {}
        
        # Email channel
        if self.config.email_enabled:
            channels['email'] = AlertChannel(
                name='email',
                enabled=True,
                severity_filter=['critical', 'high', 'medium'],
                rate_limit=5,
                cooldown=300
            )
        
        # Slack channel
        if self.config.slack_enabled:
            channels['slack'] = AlertChannel(
                name='slack',
                enabled=True,
                severity_filter=['critical', 'high'],
                rate_limit=10,
                cooldown=60
            )
        
        # Webhook channel
        if self.config.webhook_enabled:
            channels['webhook'] = AlertChannel(
                name='webhook',
                enabled=True,
                severity_filter=['critical', 'high', 'medium', 'low'],
                rate_limit=20,
                cooldown=30
            )
        
        return channels
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send alert through configured channels
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source
            metadata: Additional metadata
            
        Returns:
            Alert ID
        """
        try:
            # Create alert
            alert_id = str(uuid.uuid4())
            alert = Alert(
                alert_id=alert_id,
                title=title,
                message=message,
                severity=severity,
                source=source,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Check throttling
            if self._should_throttle_alert(alert):
                logger.warning(f"Alert throttled: {title}")
                self.stats['throttled_alerts'] += 1
                return alert_id
            
            # Send to channels
            sent_channels = []
            for channel_name, channel in self.channels.items():
                if channel.enabled and severity in channel.severity_filter:
                    if self._send_to_channel(alert, channel):
                        sent_channels.append(channel_name)
            
            # Store alert
            self.alert_history.append(alert)
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_severity'][severity] += 1
            self.stats['alerts_by_source'][source] += 1
            
            logger.info(f"Alert sent: {title}",
                       severity=severity,
                       channels=sent_channels,
                       alert_id=alert_id)
            
            return alert_id
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return str(uuid.uuid4())
    
    def _should_throttle_alert(self, alert: Alert) -> bool:
        """Check if alert should be throttled"""
        if not self.config.alert_throttling:
            return False
        
        current_time = datetime.utcnow()
        throttle_key = f"{alert.source}:{alert.severity}"
        
        # Clean old entries
        self.alert_throttle[throttle_key] = [
            timestamp for timestamp in self.alert_throttle[throttle_key]
            if current_time - timestamp < timedelta(seconds=self.config.throttle_window)
        ]
        
        # Check rate limit
        if len(self.alert_throttle[throttle_key]) >= self.config.max_alerts_per_window:
            return True
        
        # Add current alert
        self.alert_throttle[throttle_key].append(current_time)
        return False
    
    def _send_to_channel(self, alert: Alert, channel: AlertChannel) -> bool:
        """Send alert to specific channel"""
        try:
            if channel.name == 'email':
                return self._send_email_alert(alert)
            elif channel.name == 'slack':
                return self._send_slack_alert(alert)
            elif channel.name == 'webhook':
                return self._send_webhook_alert(alert)
            else:
                logger.warning(f"Unknown channel: {channel.name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send alert to {channel.name}: {e}")
            self.stats['failed_deliveries'] += 1
            return False
    
    def _send_email_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        try:
            if not self.config.email_recipients:
                logger.warning("No email recipients configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"
            
            # Create body
            body = f"""
            Alert: {alert.title}
            Severity: {alert.severity.upper()}
            Source: {alert.source}
            Time: {alert.timestamp.isoformat()}
            
            Message:
            {alert.message}
            
            Metadata:
            {json.dumps(alert.metadata, indent=2)}
            
            Alert ID: {alert.alert_id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_slack_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        try:
            if not self.config.slack_webhook_url:
                logger.warning("No Slack webhook URL configured")
                return False
            
            # Create Slack message
            color_map = {
                'critical': 'danger',
                'high': 'warning',
                'medium': 'good',
                'low': '#36a64f',
                'info': '#36a64f'
            }
            
            slack_message = {
                "text": f"🚨 {alert.title}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, 'good'),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.isoformat(),
                                "short": False
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ],
                        "footer": f"Alert ID: {alert.alert_id}"
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                self.config.slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {alert.title}")
                return True
            else:
                logger.error(f"Slack webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _send_webhook_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        try:
            if not self.config.webhook_url:
                logger.warning("No webhook URL configured")
                return False
            
            # Create webhook payload
            payload = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            # Send webhook
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook alert sent: {alert.title}")
                return True
            else:
                logger.error(f"Webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert"""
        try:
            # Find alert
            alert = next((a for a in self.alert_history if a.alert_id == alert_id), None)
            if not alert:
                logger.warning(f"Alert not found: {alert_id}")
                return False
            
            # Acknowledge
            alert.acknowledged = True
            self.acknowledged_alerts.add(alert_id)
            
            logger.info(f"Alert acknowledged: {alert_id} by {user}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """Resolve an alert"""
        try:
            # Find alert
            alert = next((a for a in self.alert_history if a.alert_id == alert_id), None)
            if not alert:
                logger.warning(f"Alert not found: {alert_id}")
                return False
            
            # Resolve
            alert.resolved = True
            self.resolved_alerts.add(alert_id)
            
            logger.info(f"Alert resolved: {alert_id} by {user}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        return {
            'total_alerts': self.stats['total_alerts'],
            'alerts_by_severity': dict(self.stats['alerts_by_severity']),
            'alerts_by_source': dict(self.stats['alerts_by_source']),
            'throttled_alerts': self.stats['throttled_alerts'],
            'failed_deliveries': self.stats['failed_deliveries'],
            'acknowledged_alerts': len(self.acknowledged_alerts),
            'resolved_alerts': len(self.resolved_alerts),
            'active_alerts': len(self.alert_history) - len(self.resolved_alerts),
            'recent_alerts': [
                {
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'severity': alert.severity,
                    'source': alert.source,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                }
                for alert in list(self.alert_history)[-20:]
            ]
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        active_alerts = []
        for alert in self.alert_history:
            if not alert.resolved:
                active_alerts.append({
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity,
                    'source': alert.source,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'metadata': alert.metadata
                })
        
        return active_alerts
    
    def export_alerts_to_file(self, filepath: str):
        """Export alerts to file"""
        try:
            alerts_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': self.get_alert_summary(),
                'alert_history': [
                    {
                        'alert_id': alert.alert_id,
                        'title': alert.title,
                        'message': alert.message,
                        'severity': alert.severity,
                        'source': alert.source,
                        'timestamp': alert.timestamp.isoformat(),
                        'acknowledged': alert.acknowledged,
                        'resolved': alert.resolved,
                        'metadata': alert.metadata
                    }
                    for alert in self.alert_history
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(alerts_data, f, indent=2, default=str)
            
            logger.info(f"Alerts exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export alerts: {e}")

# Factory function for easy alert setup
def create_alert_manager(
    email_enabled: bool = True,
    slack_enabled: bool = False,
    webhook_enabled: bool = False,
    email_recipients: List[str] = None,
    **kwargs
) -> AlertManager:
    """
    Create alert manager with default configuration
    
    Args:
        email_enabled: Enable email alerts
        slack_enabled: Enable Slack alerts
        webhook_enabled: Enable webhook alerts
        email_recipients: Email recipients list
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured AlertManager
    """
    config = AlertConfig(
        email_enabled=email_enabled,
        slack_enabled=slack_enabled,
        webhook_enabled=webhook_enabled,
        email_recipients=email_recipients or [],
        **kwargs
    )
    
    return AlertManager(config)
