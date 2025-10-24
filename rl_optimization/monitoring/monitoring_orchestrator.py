"""
Monitoring Orchestrator
Comprehensive monitoring system integrating metrics, tracing, anomaly detection, and alerting
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import structlog
import threading
import json
import os
from pathlib import Path

from .metrics_exporter import MetricsExporter, MetricConfig
from .tracer import DistributedTracer, TraceConfig
from .anomaly_detector import AnomalyDetector, AnomalyConfig
from .alert_manager import AlertManager, AlertConfig

logger = structlog.get_logger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for monitoring orchestrator"""
    # Metrics configuration
    metrics_port: int = 8000
    metrics_enabled: bool = True
    
    # Tracing configuration
    tracing_enabled: bool = True
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    
    # Anomaly detection configuration
    anomaly_detection_enabled: bool = True
    anomaly_window_size: int = 100
    anomaly_sensitivity: float = 0.1
    
    # Alerting configuration
    alerting_enabled: bool = True
    email_recipients: List[str] = None
    slack_webhook_url: str = ""
    
    # General configuration
    update_interval: float = 1.0
    output_dir: str = "monitoring_output"
    enable_file_exports: bool = True
    export_interval: int = 300  # seconds

class MonitoringOrchestrator:
    """
    Comprehensive monitoring system
    - Integrate metrics, tracing, anomaly detection, and alerting
    - Real-time monitoring dashboard
    - Automated alerting and escalation
    - Performance optimization recommendations
    """
    
    def __init__(self, config: MonitoringConfig):
        """
        Initialize monitoring orchestrator
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self.is_running = False
        self.monitoring_thread = None
        
        # Initialize components
        self.metrics_exporter = None
        self.tracer = None
        self.anomaly_detector = None
        self.alert_manager = None
        
        # Monitoring state
        self.monitoring_data = {}
        self.performance_history = []
        self.health_status = "unknown"
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Initialize components
        self._initialize_components()
        
        logger.info("MonitoringOrchestrator initialized", 
                   metrics_enabled=config.metrics_enabled,
                   tracing_enabled=config.tracing_enabled,
                   anomaly_detection_enabled=config.anomaly_detection_enabled)
    
    def _initialize_components(self):
        """Initialize monitoring components"""
        try:
            # Initialize metrics exporter
            if self.config.metrics_enabled:
                metrics_config = MetricConfig(
                    port=self.config.metrics_port,
                    enable_system_metrics=True,
                    enable_business_metrics=True
                )
                self.metrics_exporter = MetricsExporter(metrics_config)
                self.metrics_exporter.start_server()
                logger.info("Metrics exporter initialized")
            
            # Initialize tracer
            if self.config.tracing_enabled:
                trace_config = TraceConfig(
                    service_name="rl-training-monitoring",
                    jaeger_endpoint=self.config.jaeger_endpoint
                )
                self.tracer = DistributedTracer(trace_config)
                logger.info("Distributed tracer initialized")
            
            # Initialize anomaly detector
            if self.config.anomaly_detection_enabled:
                anomaly_config = AnomalyConfig(
                    window_size=self.config.anomaly_window_size,
                    sensitivity=self.config.anomaly_sensitivity
                )
                self.anomaly_detector = AnomalyDetector(anomaly_config)
                logger.info("Anomaly detector initialized")
            
            # Initialize alert manager
            if self.config.alerting_enabled:
                alert_config = AlertConfig(
                    email_enabled=True,
                    slack_enabled=bool(self.config.slack_webhook_url),
                    webhook_enabled=False,
                    email_recipients=self.config.email_recipients or [],
                    slack_webhook_url=self.config.slack_webhook_url
                )
                self.alert_manager = AlertManager(alert_config)
                logger.info("Alert manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring components: {e}")
            raise
    
    def start_monitoring(self):
        """Start comprehensive monitoring"""
        if self.is_running:
            logger.warning("Monitoring already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Comprehensive monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        # Stop components
        if self.metrics_exporter:
            self.metrics_exporter.stop_server()
        
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check for anomalies
                if self.anomaly_detector:
                    self._check_anomalies()
                
                # Update health status
                self._update_health_status()
                
                # Export data if enabled
                if self.config.enable_file_exports:
                    self._export_monitoring_data()
                
                # Sleep
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'timestamp': datetime.utcnow(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.used,
                'memory_percent': memory.percent,
                'disk_usage': disk.used,
                'disk_percent': (disk.used / disk.total) * 100
            }
            
            # Add to monitoring data
            self.monitoring_data.update(metrics)
            
            # Record metrics
            if self.metrics_exporter:
                self.metrics_exporter.record_business_metrics(
                    operation_type="system_monitoring",
                    cost_efficiency=1.0 - (cpu_percent / 100.0)
                )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _check_anomalies(self):
        """Check for anomalies"""
        try:
            if not self.anomaly_detector:
                return
            
            # Add current metrics to anomaly detector
            self.anomaly_detector.add_metrics(self.monitoring_data)
            
            # Get anomaly summary
            anomaly_summary = self.anomaly_detector.get_anomaly_summary()
            
            # Check for new anomalies
            if anomaly_summary['total_anomalies'] > 0:
                recent_anomalies = anomaly_summary.get('recent_anomalies', [])
                for anomaly in recent_anomalies:
                    if self.alert_manager:
                        self.alert_manager.send_alert(
                            title=f"Anomaly Detected: {anomaly['type']}",
                            message=anomaly.get('description', 'Anomaly detected'),
                            severity=anomaly.get('severity', 'medium'),
                            source="anomaly_detector",
                            metadata=anomaly
                        )
            
        except Exception as e:
            logger.error(f"Failed to check anomalies: {e}")
    
    def _update_health_status(self):
        """Update overall health status"""
        try:
            # Check component health
            health_checks = {
                'metrics_exporter': self._check_metrics_health(),
                'tracer': self._check_tracer_health(),
                'anomaly_detector': self._check_anomaly_detector_health(),
                'alert_manager': self._check_alert_manager_health()
            }
            
            # Determine overall health
            healthy_components = sum(1 for health in health_checks.values() if health)
            total_components = len(health_checks)
            
            if healthy_components == total_components:
                self.health_status = "healthy"
            elif healthy_components >= total_components * 0.5:
                self.health_status = "degraded"
            else:
                self.health_status = "unhealthy"
            
            # Update monitoring data
            self.monitoring_data['health_status'] = self.health_status
            self.monitoring_data['component_health'] = health_checks
            
        except Exception as e:
            logger.error(f"Failed to update health status: {e}")
            self.health_status = "error"
    
    def _check_metrics_health(self) -> bool:
        """Check metrics exporter health"""
        try:
            if not self.metrics_exporter:
                return False
            
            # Simple health check
            return self.metrics_exporter.is_running
            
        except Exception:
            return False
    
    def _check_tracer_health(self) -> bool:
        """Check tracer health"""
        try:
            if not self.tracer:
                return False
            
            # Simple health check
            stats = self.tracer.get_trace_statistics()
            return stats is not None
            
        except Exception:
            return False
    
    def _check_anomaly_detector_health(self) -> bool:
        """Check anomaly detector health"""
        try:
            if not self.anomaly_detector:
                return False
            
            # Simple health check
            summary = self.anomaly_detector.get_anomaly_summary()
            return summary is not None
            
        except Exception:
            return False
    
    def _check_alert_manager_health(self) -> bool:
        """Check alert manager health"""
        try:
            if not self.alert_manager:
                return False
            
            # Simple health check
            summary = self.alert_manager.get_alert_summary()
            return summary is not None
            
        except Exception:
            return False
    
    def _export_monitoring_data(self):
        """Export monitoring data to files"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Export metrics
            if self.metrics_exporter:
                metrics_file = os.path.join(self.config.output_dir, f"metrics_{timestamp}.json")
                self.metrics_exporter.export_metrics_to_file(metrics_file)
            
            # Export traces
            if self.tracer:
                traces_file = os.path.join(self.config.output_dir, f"traces_{timestamp}.json")
                self.tracer.export_traces_to_file(traces_file)
            
            # Export anomalies
            if self.anomaly_detector:
                anomalies_file = os.path.join(self.config.output_dir, f"anomalies_{timestamp}.json")
                self.anomaly_detector.export_anomalies_to_file(anomalies_file)
            
            # Export alerts
            if self.alert_manager:
                alerts_file = os.path.join(self.config.output_dir, f"alerts_{timestamp}.json")
                self.alert_manager.export_alerts_to_file(alerts_file)
            
            # Export comprehensive monitoring data
            monitoring_file = os.path.join(self.config.output_dir, f"monitoring_{timestamp}.json")
            self._export_comprehensive_data(monitoring_file)
            
        except Exception as e:
            logger.error(f"Failed to export monitoring data: {e}")
    
    def _export_comprehensive_data(self, filepath: str):
        """Export comprehensive monitoring data"""
        try:
            comprehensive_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'config': self.config.__dict__,
                'health_status': self.health_status,
                'monitoring_data': self.monitoring_data,
                'metrics_summary': self.metrics_exporter.get_metrics_summary() if self.metrics_exporter else {},
                'trace_statistics': self.tracer.get_trace_statistics() if self.tracer else {},
                'anomaly_summary': self.anomaly_detector.get_anomaly_summary() if self.anomaly_detector else {},
                'alert_summary': self.alert_manager.get_alert_summary() if self.alert_manager else {}
            }
            
            with open(filepath, 'w') as f:
                json.dump(comprehensive_data, f, indent=2, default=str)
            
            logger.info(f"Comprehensive monitoring data exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export comprehensive data: {e}")
    
    def record_training_metrics(
        self,
        worker_id: str,
        episode_reward: float,
        episode_length: int,
        training_loss: float,
        epsilon: float,
        memory_size: int,
        domain: str = "general_medicine"
    ):
        """Record training metrics"""
        try:
            # Record in metrics exporter
            if self.metrics_exporter:
                self.metrics_exporter.record_episode_metrics(
                    worker_id=worker_id,
                    reward=episode_reward,
                    length=episode_length,
                    loss=training_loss,
                    epsilon=epsilon,
                    memory_size=memory_size,
                    domain=domain
                )
            
            # Add to anomaly detector
            if self.anomaly_detector:
                metrics = {
                    'episode_reward': episode_reward,
                    'episode_length': episode_length,
                    'training_loss': training_loss,
                    'epsilon': epsilon,
                    'memory_size': memory_size,
                    'domain': domain
                }
                self.anomaly_detector.add_metrics(metrics)
            
            # Update monitoring data
            self.monitoring_data.update({
                'latest_episode_reward': episode_reward,
                'latest_episode_length': episode_length,
                'latest_training_loss': training_loss,
                'latest_epsilon': epsilon,
                'latest_memory_size': memory_size
            })
            
        except Exception as e:
            logger.error(f"Failed to record training metrics: {e}")
    
    def record_classification_metrics(
        self,
        model_name: str,
        accuracy: float,
        latency_seconds: float,
        cost: float,
        domain: str = "general_medicine"
    ):
        """Record classification metrics"""
        try:
            # Record in metrics exporter
            if self.metrics_exporter:
                self.metrics_exporter.record_classification_metrics(
                    model_name=model_name,
                    accuracy=accuracy,
                    latency_seconds=latency_seconds,
                    cost=cost,
                    domain=domain
                )
            
            # Add to anomaly detector
            if self.anomaly_detector:
                metrics = {
                    'accuracy': accuracy,
                    'latency_seconds': latency_seconds,
                    'cost': cost,
                    'model_name': model_name,
                    'domain': domain
                }
                self.anomaly_detector.add_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record classification metrics: {e}")
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get monitoring dashboard data"""
        try:
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'health_status': self.health_status,
                'monitoring_data': self.monitoring_data,
                'metrics_endpoint': self.metrics_exporter.get_metrics_endpoint() if self.metrics_exporter else None,
                'active_traces': self.tracer.get_active_traces() if self.tracer else {},
                'anomaly_summary': self.anomaly_detector.get_anomaly_summary() if self.anomaly_detector else {},
                'alert_summary': self.alert_manager.get_alert_summary() if self.alert_manager else {},
                'component_status': {
                    'metrics_exporter': self._check_metrics_health(),
                    'tracer': self._check_tracer_health(),
                    'anomaly_detector': self._check_anomaly_detector_health(),
                    'alert_manager': self._check_alert_manager_health()
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get monitoring dashboard: {e}")
            return {}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            'overall_health': self.health_status,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'metrics_exporter': self._check_metrics_health(),
                'tracer': self._check_tracer_health(),
                'anomaly_detector': self._check_anomaly_detector_health(),
                'alert_manager': self._check_alert_manager_health()
            },
            'monitoring_data': self.monitoring_data
        }

# Factory function for easy monitoring setup
def create_monitoring_orchestrator(
    output_dir: str = "monitoring_output",
    metrics_port: int = 8000,
    email_recipients: List[str] = None,
    slack_webhook_url: str = "",
    **kwargs
) -> MonitoringOrchestrator:
    """
    Create monitoring orchestrator with default configuration
    
    Args:
        output_dir: Output directory for monitoring data
        metrics_port: Port for metrics server
        email_recipients: Email recipients for alerts
        slack_webhook_url: Slack webhook URL for alerts
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured MonitoringOrchestrator
    """
    config = MonitoringConfig(
        output_dir=output_dir,
        metrics_port=metrics_port,
        email_recipients=email_recipients or [],
        slack_webhook_url=slack_webhook_url,
        **kwargs
    )
    
    return MonitoringOrchestrator(config)
