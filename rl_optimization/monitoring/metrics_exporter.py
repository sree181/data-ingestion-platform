"""
Metrics Exporter for Production Monitoring
Export metrics to Prometheus with custom RL metrics
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import structlog
import threading
from collections import defaultdict, deque
import json
import os

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning("Prometheus client not available. Install with: pip install prometheus_client")

logger = structlog.get_logger(__name__)

@dataclass
class MetricConfig:
    """Configuration for metrics export"""
    port: int = 8000
    endpoint: str = "/metrics"
    update_interval: float = 1.0
    max_metrics_history: int = 1000
    enable_custom_metrics: bool = True
    enable_system_metrics: bool = True
    enable_business_metrics: bool = True

class MetricsExporter:
    """
    Export metrics to monitoring systems
    - Prometheus metrics (Counter, Gauge, Histogram)
    - Custom metrics for RL (episode rewards, epsilon, loss)
    - System metrics (CPU, GPU, memory)
    - Business metrics (throughput, latency)
    """
    
    def __init__(self, config: MetricConfig):
        """
        Initialize metrics exporter
        
        Args:
            config: Metrics configuration
        """
        self.config = config
        self.registry = CollectorRegistry()
        self.metrics = {}
        self.metrics_history = defaultdict(lambda: deque(maxlen=config.max_metrics_history))
        self.is_running = False
        self.metrics_thread = None
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, using mock metrics")
            self._create_mock_metrics()
        else:
            self._create_prometheus_metrics()
        
        logger.info("MetricsExporter initialized", port=config.port)
    
    def _create_prometheus_metrics(self):
        """Create Prometheus metrics"""
        # RL Training Metrics
        self.metrics['episode_reward'] = Histogram(
            'rl_episode_reward',
            'Episode reward distribution',
            ['worker_id', 'domain'],
            registry=self.registry
        )
        
        self.metrics['episode_length'] = Histogram(
            'rl_episode_length',
            'Episode length distribution',
            ['worker_id'],
            registry=self.registry
        )
        
        self.metrics['training_loss'] = Histogram(
            'rl_training_loss',
            'Training loss distribution',
            ['worker_id'],
            registry=self.registry
        )
        
        self.metrics['epsilon'] = Gauge(
            'rl_epsilon',
            'Current epsilon value',
            ['worker_id'],
            registry=self.registry
        )
        
        self.metrics['memory_size'] = Gauge(
            'rl_memory_size',
            'Experience replay buffer size',
            ['worker_id'],
            registry=self.registry
        )
        
        # Classification Metrics
        self.metrics['classification_accuracy'] = Gauge(
            'classification_accuracy',
            'Classification accuracy',
            ['model_name', 'domain'],
            registry=self.registry
        )
        
        self.metrics['classification_latency'] = Histogram(
            'classification_latency_seconds',
            'Classification latency',
            ['model_name', 'domain'],
            registry=self.registry
        )
        
        self.metrics['classification_cost'] = Histogram(
            'classification_cost',
            'Classification cost',
            ['model_name'],
            registry=self.registry
        )
        
        # System Metrics
        if self.config.enable_system_metrics:
            self.metrics['cpu_usage'] = Gauge(
                'system_cpu_usage_percent',
                'CPU usage percentage',
                registry=self.registry
            )
            
            self.metrics['memory_usage'] = Gauge(
                'system_memory_usage_bytes',
                'Memory usage in bytes',
                registry=self.registry
            )
            
            self.metrics['gpu_usage'] = Gauge(
                'system_gpu_usage_percent',
                'GPU usage percentage',
                ['gpu_id'],
                registry=self.registry
            )
        
        # Business Metrics
        if self.config.enable_business_metrics:
            self.metrics['throughput'] = Counter(
                'business_throughput_total',
                'Total throughput',
                ['operation_type'],
                registry=self.registry
            )
            
            self.metrics['error_rate'] = Gauge(
                'business_error_rate',
                'Error rate',
                ['error_type'],
                registry=self.registry
            )
            
            self.metrics['cost_efficiency'] = Gauge(
                'business_cost_efficiency',
                'Cost efficiency',
                registry=self.registry
            )
    
    def _create_mock_metrics(self):
        """Create mock metrics when Prometheus is not available"""
        self.metrics = {
            'episode_reward': MockMetric('episode_reward'),
            'episode_length': MockMetric('episode_length'),
            'training_loss': MockMetric('training_loss'),
            'epsilon': MockMetric('epsilon'),
            'memory_size': MockMetric('memory_size'),
            'classification_accuracy': MockMetric('classification_accuracy'),
            'classification_latency': MockMetric('classification_latency'),
            'classification_cost': MockMetric('classification_cost'),
            'cpu_usage': MockMetric('cpu_usage'),
            'memory_usage': MockMetric('memory_usage'),
            'throughput': MockMetric('throughput'),
            'error_rate': MockMetric('error_rate'),
            'cost_efficiency': MockMetric('cost_efficiency')
        }
    
    def start_server(self):
        """Start metrics server"""
        if not self.is_running:
            if PROMETHEUS_AVAILABLE:
                start_http_server(self.config.port, registry=self.registry)
                logger.info(f"Prometheus metrics server started on port {self.config.port}")
            else:
                logger.info("Mock metrics server started")
            
            self.is_running = True
            
            # Start metrics update thread
            self.metrics_thread = threading.Thread(target=self._update_metrics_loop, daemon=True)
            self.metrics_thread.start()
    
    def stop_server(self):
        """Stop metrics server"""
        self.is_running = False
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        
        logger.info("Metrics server stopped")
    
    def _update_metrics_loop(self):
        """Update metrics in background thread"""
        while self.is_running:
            try:
                if self.config.enable_system_metrics:
                    self._update_system_metrics()
                
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                time.sleep(5)
    
    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].set(memory.used)
            
            # GPU usage (if available)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    self.metrics['gpu_usage'].labels(gpu_id=i).set(gpu.load * 100)
            except ImportError:
                pass  # GPU monitoring not available
            
        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")
    
    def record_episode_metrics(
        self, 
        worker_id: str, 
        reward: float, 
        length: int, 
        loss: float,
        epsilon: float,
        memory_size: int,
        domain: str = "general_medicine"
    ):
        """Record episode metrics"""
        try:
            # Record episode reward
            self.metrics['episode_reward'].labels(
                worker_id=worker_id, 
                domain=domain
            ).observe(reward)
            
            # Record episode length
            self.metrics['episode_length'].labels(worker_id=worker_id).observe(length)
            
            # Record training loss
            self.metrics['training_loss'].labels(worker_id=worker_id).observe(loss)
            
            # Update epsilon
            self.metrics['epsilon'].labels(worker_id=worker_id).set(epsilon)
            
            # Update memory size
            self.metrics['memory_size'].labels(worker_id=worker_id).set(memory_size)
            
            # Store in history
            self.metrics_history['episode_reward'].append({
                'timestamp': datetime.utcnow(),
                'worker_id': worker_id,
                'value': reward,
                'domain': domain
            })
            
        except Exception as e:
            logger.error(f"Failed to record episode metrics: {e}")
    
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
            # Record accuracy
            self.metrics['classification_accuracy'].labels(
                model_name=model_name,
                domain=domain
            ).set(accuracy)
            
            # Record latency
            self.metrics['classification_latency'].labels(
                model_name=model_name,
                domain=domain
            ).observe(latency_seconds)
            
            # Record cost
            self.metrics['classification_cost'].labels(model_name=model_name).observe(cost)
            
            # Store in history
            self.metrics_history['classification_accuracy'].append({
                'timestamp': datetime.utcnow(),
                'model_name': model_name,
                'value': accuracy,
                'domain': domain
            })
            
        except Exception as e:
            logger.error(f"Failed to record classification metrics: {e}")
    
    def record_business_metrics(
        self,
        operation_type: str,
        error_type: Optional[str] = None,
        cost_efficiency: Optional[float] = None
    ):
        """Record business metrics"""
        try:
            # Record throughput
            self.metrics['throughput'].labels(operation_type=operation_type).inc()
            
            # Record error rate
            if error_type:
                self.metrics['error_rate'].labels(error_type=error_type).set(0.1)  # Placeholder
            
            # Record cost efficiency
            if cost_efficiency is not None:
                self.metrics['cost_efficiency'].set(cost_efficiency)
            
        except Exception as e:
            logger.error(f"Failed to record business metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            summary = {}
            
            # Get recent metrics from history
            for metric_name, history in self.metrics_history.items():
                if history:
                    recent_values = list(history)[-10:]  # Last 10 values
                    summary[metric_name] = {
                        'count': len(recent_values),
                        'latest': recent_values[-1] if recent_values else None,
                        'average': sum(v['value'] for v in recent_values) / len(recent_values) if recent_values else 0.0
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    def export_metrics_to_file(self, filepath: str):
        """Export metrics to file"""
        try:
            metrics_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'config': self.config.__dict__,
                'metrics_summary': self.get_metrics_summary(),
                'metrics_history': {
                    name: list(history) for name, history in self.metrics_history.items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_metrics_endpoint(self) -> str:
        """Get metrics endpoint URL"""
        return f"http://localhost:{self.config.port}{self.config.endpoint}"

class MockMetric:
    """Mock metric class when Prometheus is not available"""
    
    def __init__(self, name: str):
        self.name = name
        self.value = 0.0
        self.labels = {}
    
    def set(self, value: float):
        self.value = value
    
    def observe(self, value: float):
        self.value = value
    
    def inc(self, amount: float = 1.0):
        self.value += amount
    
    def labels(self, **kwargs):
        self.labels.update(kwargs)
        return self

# Factory function for easy metrics setup
def create_metrics_exporter(
    port: int = 8000,
    enable_system_metrics: bool = True,
    enable_business_metrics: bool = True,
    **kwargs
) -> MetricsExporter:
    """
    Create metrics exporter with default configuration
    
    Args:
        port: Port for metrics server
        enable_system_metrics: Enable system metrics
        enable_business_metrics: Enable business metrics
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured MetricsExporter
    """
    config = MetricConfig(
        port=port,
        enable_system_metrics=enable_system_metrics,
        enable_business_metrics=enable_business_metrics,
        **kwargs
    )
    
    return MetricsExporter(config)
