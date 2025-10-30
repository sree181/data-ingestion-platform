"""
Real-Time RL Metrics Dashboard
Provides comprehensive monitoring and analytics for RL-enhanced classification
"""

import asyncio
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import numpy as np
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque
import threading
import time

logger = structlog.get_logger(__name__)

@dataclass
class MetricDataPoint:
    """Single metric data point"""
    timestamp: datetime
    accuracy: float
    cost_efficiency: float
    processing_speed: float
    domain_specialization: float
    total_reward: float
    document_count: int
    rl_episodes: int

@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    metrics: Dict[str, float]

class RLMetricsDashboard:
    """
    Real-Time RL Metrics Dashboard
    Provides comprehensive monitoring and analytics
    """
    
    def __init__(self, 
                 max_history_size: int = 10000,
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 enable_visualization: bool = True):
        
        self.max_history_size = max_history_size
        self.enable_visualization = enable_visualization
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'accuracy_min': 0.7,
            'cost_efficiency_min': 0.5,
            'processing_speed_min': 0.5,
            'domain_specialization_min': 0.6
        }
        
        # Metrics storage
        self.metrics_history = deque(maxlen=max_history_size)
        self.alerts = deque(maxlen=1000)
        self.performance_summary = {}
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Visualization settings
        if self.enable_visualization:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        
        logger.info("RL Metrics Dashboard initialized", 
                   max_history=max_history_size,
                   visualization=enabled=self.enable_visualization)
    
    def start_monitoring(self, rl_controller):
        """Start real-time monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.rl_controller = rl_controller
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics from RL controller
                metrics = self.rl_controller.get_real_time_metrics()
                
                # Create data point
                current_metrics = metrics['current_metrics']
                data_point = MetricDataPoint(
                    timestamp=datetime.utcnow(),
                    accuracy=current_metrics['accuracy'],
                    cost_efficiency=current_metrics['cost_efficiency'],
                    processing_speed=current_metrics['processing_speed'],
                    domain_specialization=current_metrics['domain_specialization'],
                    total_reward=current_metrics.get('total_reward', 0.0),
                    document_count=current_metrics['document_count'],
                    rl_episodes=current_metrics.get('rl_episodes_completed', 0)
                )
                
                # Store metrics
                self.metrics_history.append(data_point)
                
                # Check for alerts
                self._check_alerts(data_point)
                
                # Update performance summary
                self._update_performance_summary()
                
                # Sleep for monitoring interval
                time.sleep(1.0)  # 1 second monitoring interval
                
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
                time.sleep(5.0)  # Wait before retrying
    
    def _check_alerts(self, data_point: MetricDataPoint):
        """Check for performance alerts"""
        alerts_triggered = []
        
        # Accuracy alert
        if data_point.accuracy < self.alert_thresholds['accuracy_min']:
            alerts_triggered.append(PerformanceAlert(
                alert_type='accuracy',
                severity='warning',
                message=f"Accuracy below threshold: {data_point.accuracy:.3f} < {self.alert_thresholds['accuracy_min']}",
                timestamp=datetime.utcnow(),
                metrics={'accuracy': data_point.accuracy}
            ))
        
        # Cost efficiency alert
        if data_point.cost_efficiency < self.alert_thresholds['cost_efficiency_min']:
            alerts_triggered.append(PerformanceAlert(
                alert_type='cost_efficiency',
                severity='warning',
                message=f"Cost efficiency below threshold: {data_point.cost_efficiency:.3f} < {self.alert_thresholds['cost_efficiency_min']}",
                timestamp=datetime.utcnow(),
                metrics={'cost_efficiency': data_point.cost_efficiency}
            ))
        
        # Processing speed alert
        if data_point.processing_speed < self.alert_thresholds['processing_speed_min']:
            alerts_triggered.append(PerformanceAlert(
                alert_type='processing_speed',
                severity='warning',
                message=f"Processing speed below threshold: {data_point.processing_speed:.3f} < {self.alert_thresholds['processing_speed_min']}",
                timestamp=datetime.utcnow(),
                metrics={'processing_speed': data_point.processing_speed}
            ))
        
        # Domain specialization alert
        if data_point.domain_specialization < self.alert_thresholds['domain_specialization_min']:
            alerts_triggered.append(PerformanceAlert(
                alert_type='domain_specialization',
                severity='warning',
                message=f"Domain specialization below threshold: {data_point.domain_specialization:.3f} < {self.alert_thresholds['domain_specialization_min']}",
                timestamp=datetime.utcnow(),
                metrics={'domain_specialization': data_point.domain_specialization}
            ))
        
        # Store alerts
        for alert in alerts_triggered:
            self.alerts.append(alert)
            logger.warning("Performance alert triggered", 
                         alert_type=alert.alert_type,
                         severity=alert.severity,
                         message=alert.message)
    
    def _update_performance_summary(self):
        """Update performance summary statistics"""
        if not self.metrics_history:
            return
        
        # Calculate statistics over last 100 data points
        recent_metrics = list(self.metrics_history)[-100:]
        
        self.performance_summary = {
            'current_metrics': {
                'accuracy': recent_metrics[-1].accuracy,
                'cost_efficiency': recent_metrics[-1].cost_efficiency,
                'processing_speed': recent_metrics[-1].processing_speed,
                'domain_specialization': recent_metrics[-1].domain_specialization,
                'total_reward': recent_metrics[-1].total_reward
            },
            'average_metrics': {
                'accuracy': np.mean([m.accuracy for m in recent_metrics]),
                'cost_efficiency': np.mean([m.cost_efficiency for m in recent_metrics]),
                'processing_speed': np.mean([m.processing_speed for m in recent_metrics]),
                'domain_specialization': np.mean([m.domain_specialization for m in recent_metrics]),
                'total_reward': np.mean([m.total_reward for m in recent_metrics])
            },
            'trends': {
                'accuracy_trend': self._calculate_trend([m.accuracy for m in recent_metrics]),
                'cost_efficiency_trend': self._calculate_trend([m.cost_efficiency for m in recent_metrics]),
                'processing_speed_trend': self._calculate_trend([m.processing_speed for m in recent_metrics]),
                'domain_specialization_trend': self._calculate_trend([m.domain_specialization for m in recent_metrics])
            },
            'statistics': {
                'total_documents': recent_metrics[-1].document_count,
                'total_rl_episodes': recent_metrics[-1].rl_episodes,
                'monitoring_duration': (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds(),
                'data_points_collected': len(recent_metrics)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend calculation
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            'performance_summary': self.performance_summary,
            'recent_alerts': [asdict(alert) for alert in list(self.alerts)[-10:]],
            'metrics_history': [asdict(metric) for metric in list(self.metrics_history)[-100:]],
            'monitoring_status': {
                'active': self.monitoring_active,
                'total_data_points': len(self.metrics_history),
                'total_alerts': len(self.alerts)
            }
        }
    
    def generate_performance_report(self, output_dir: str = "rl_optimization/monitoring_output") -> str:
        """Generate comprehensive performance report"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"rl_performance_report_{timestamp}.json"
        
        # Generate report data
        report_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'performance_summary': self.performance_summary,
            'metrics_history': [asdict(metric) for metric in self.metrics_history],
            'alerts': [asdict(alert) for alert in self.alerts],
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info("Performance report generated", file=str(report_file))
        return str(report_file)
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate performance recommendations"""
        recommendations = []
        
        if not self.performance_summary:
            return recommendations
        
        current = self.performance_summary.get('current_metrics', {})
        trends = self.performance_summary.get('trends', {})
        
        # Accuracy recommendations
        if current.get('accuracy', 0) < 0.8:
            recommendations.append({
                'category': 'accuracy',
                'priority': 'high',
                'recommendation': 'Consider increasing RL training episodes or adjusting confidence thresholds'
            })
        
        # Cost efficiency recommendations
        if current.get('cost_efficiency', 0) < 0.6:
            recommendations.append({
                'category': 'cost_efficiency',
                'priority': 'medium',
                'recommendation': 'Optimize model selection to reduce expensive LLM calls'
            })
        
        # Processing speed recommendations
        if current.get('processing_speed', 0) < 0.7:
            recommendations.append({
                'category': 'processing_speed',
                'priority': 'medium',
                'recommendation': 'Consider caching frequently used models or optimizing feature extraction'
            })
        
        # Trend-based recommendations
        if trends.get('accuracy_trend') == 'decreasing':
            recommendations.append({
                'category': 'trend',
                'priority': 'high',
                'recommendation': 'Accuracy is declining - investigate recent changes or retrain RL model'
            })
        
        return recommendations
    
    def create_visualization(self, output_dir: str = "rl_optimization/monitoring_output") -> List[str]:
        """Create performance visualizations"""
        if not self.enable_visualization or not self.metrics_history:
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        created_files = []
        
        try:
            # Extract data for plotting
            timestamps = [m.timestamp for m in self.metrics_history]
            accuracy = [m.accuracy for m in self.metrics_history]
            cost_efficiency = [m.cost_efficiency for m in self.metrics_history]
            processing_speed = [m.processing_speed for m in self.metrics_history]
            domain_specialization = [m.domain_specialization for m in self.metrics_history]
            
            # Create performance trends plot
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('RL-Enhanced Classification Performance Trends', fontsize=16)
            
            # Accuracy trend
            axes[0, 0].plot(timestamps, accuracy, 'b-', linewidth=2, label='Accuracy')
            axes[0, 0].axhline(y=self.alert_thresholds['accuracy_min'], color='r', linestyle='--', alpha=0.7, label='Threshold')
            axes[0, 0].set_title('Accuracy Trend')
            axes[0, 0].set_ylabel('Accuracy')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Cost efficiency trend
            axes[0, 1].plot(timestamps, cost_efficiency, 'g-', linewidth=2, label='Cost Efficiency')
            axes[0, 1].axhline(y=self.alert_thresholds['cost_efficiency_min'], color='r', linestyle='--', alpha=0.7, label='Threshold')
            axes[0, 1].set_title('Cost Efficiency Trend')
            axes[0, 1].set_ylabel('Cost Efficiency')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # Processing speed trend
            axes[1, 0].plot(timestamps, processing_speed, 'm-', linewidth=2, label='Processing Speed')
            axes[1, 0].axhline(y=self.alert_thresholds['processing_speed_min'], color='r', linestyle='--', alpha=0.7, label='Threshold')
            axes[1, 0].set_title('Processing Speed Trend')
            axes[1, 0].set_ylabel('Processing Speed')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # Domain specialization trend
            axes[1, 1].plot(timestamps, domain_specialization, 'c-', linewidth=2, label='Domain Specialization')
            axes[1, 1].axhline(y=self.alert_thresholds['domain_specialization_min'], color='r', linestyle='--', alpha=0.7, label='Threshold')
            axes[1, 1].set_title('Domain Specialization Trend')
            axes[1, 1].set_ylabel('Domain Specialization')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            # Rotate x-axis labels for better readability
            for ax in axes.flat:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save plot
            plot_file = output_path / f"rl_performance_trends_{timestamp}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(plot_file))
            
            # Create correlation heatmap
            metrics_data = np.array([accuracy, cost_efficiency, processing_speed, domain_specialization])
            correlation_matrix = np.corrcoef(metrics_data)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(correlation_matrix, 
                       annot=True, 
                       cmap='coolwarm', 
                       center=0,
                       xticklabels=['Accuracy', 'Cost Efficiency', 'Processing Speed', 'Domain Specialization'],
                       yticklabels=['Accuracy', 'Cost Efficiency', 'Processing Speed', 'Domain Specialization'],
                       ax=ax)
            ax.set_title('Performance Metrics Correlation Matrix')
            
            correlation_file = output_path / f"rl_metrics_correlation_{timestamp}.png"
            plt.savefig(correlation_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(str(correlation_file))
            
        except Exception as e:
            logger.error("Failed to create visualizations", error=str(e))
        
        return created_files
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        if not self.alerts:
            return {'total_alerts': 0, 'recent_alerts': []}
        
        # Count alerts by type
        alert_counts = {}
        for alert in self.alerts:
            alert_type = alert.alert_type
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        return {
            'total_alerts': len(self.alerts),
            'alerts_by_type': alert_counts,
            'recent_alerts': [asdict(alert) for alert in list(self.alerts)[-5:]],
            'alert_rate': len(self.alerts) / max(len(self.metrics_history), 1)
        }
    
    def export_metrics(self, output_file: str) -> str:
        """Export metrics to file"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'metrics_history': [asdict(metric) for metric in self.metrics_history],
            'alerts': [asdict(alert) for alert in self.alerts],
            'performance_summary': self.performance_summary
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info("Metrics exported", file=output_file)
        return output_file
