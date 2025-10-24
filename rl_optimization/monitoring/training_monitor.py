"""
Training Monitor Integration
Integrates monitoring into the RL training pipeline
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog
from datetime import datetime

from .monitoring_orchestrator import MonitoringOrchestrator, MonitoringConfig

logger = structlog.get_logger(__name__)

@dataclass
class TrainingMonitorConfig:
    """Configuration for training monitoring"""
    enable_monitoring: bool = True
    metrics_port: int = 8000
    output_dir: str = "monitoring_output"
    email_recipients: List[str] = None
    slack_webhook_url: str = ""
    update_interval: float = 1.0
    enable_anomaly_detection: bool = True
    enable_alerting: bool = True

class TrainingMonitor:
    """
    Training-specific monitoring integration
    - Monitors RL training progress
    - Tracks model performance
    - Detects training anomalies
    - Provides real-time feedback
    """
    
    def __init__(self, config: TrainingMonitorConfig):
        """
        Initialize training monitor
        
        Args:
            config: Training monitoring configuration
        """
        self.config = config
        self.monitoring_orchestrator = None
        self.training_metrics = {}
        self.episode_history = []
        self.performance_trends = {}
        
        if config.enable_monitoring:
            self._initialize_monitoring()
        
        logger.info("TrainingMonitor initialized", 
                   monitoring_enabled=config.enable_monitoring)
    
    def _initialize_monitoring(self):
        """Initialize monitoring orchestrator"""
        try:
            monitoring_config = MonitoringConfig(
                metrics_port=self.config.metrics_port,
                output_dir=self.config.output_dir,
                email_recipients=self.config.email_recipients or [],
                slack_webhook_url=self.config.slack_webhook_url,
                update_interval=self.config.update_interval,
                anomaly_detection_enabled=self.config.enable_anomaly_detection,
                alerting_enabled=self.config.enable_alerting
            )
            
            self.monitoring_orchestrator = MonitoringOrchestrator(monitoring_config)
            self.monitoring_orchestrator.start_monitoring()
            
            logger.info("Monitoring orchestrator initialized and started")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            self.monitoring_orchestrator = None
    
    def start_training_session(self, session_id: str, config: Dict[str, Any]):
        """Start monitoring a training session"""
        try:
            self.training_metrics = {
                'session_id': session_id,
                'start_time': datetime.utcnow(),
                'config': config,
                'episodes_completed': 0,
                'total_reward': 0.0,
                'average_reward': 0.0,
                'best_reward': float('-inf'),
                'worst_reward': float('inf'),
                'total_loss': 0.0,
                'average_loss': 0.0,
                'epsilon_history': [],
                'memory_size_history': [],
                'domain_performance': {}
            }
            
            # Record session start
            if self.monitoring_orchestrator:
                self.monitoring_orchestrator.record_training_metrics(
                    worker_id=session_id,
                    episode_reward=0.0,
                    episode_length=0,
                    training_loss=0.0,
                    epsilon=1.0,
                    memory_size=0,
                    domain="training_start"
                )
            
            logger.info("Training session monitoring started", session_id=session_id)
            
        except Exception as e:
            logger.error(f"Failed to start training session monitoring: {e}")
    
    def record_episode(
        self,
        episode_idx: int,
        reward: float,
        length: int,
        loss: float,
        epsilon: float,
        memory_size: int,
        domain: str = "general_medicine",
        additional_metrics: Optional[Dict[str, Any]] = None
    ):
        """Record episode metrics"""
        try:
            # Update training metrics
            self.training_metrics['episodes_completed'] = episode_idx + 1
            self.training_metrics['total_reward'] += reward
            self.training_metrics['average_reward'] = (
                self.training_metrics['total_reward'] / self.training_metrics['episodes_completed']
            )
            self.training_metrics['best_reward'] = max(self.training_metrics['best_reward'], reward)
            self.training_metrics['worst_reward'] = min(self.training_metrics['worst_reward'], reward)
            self.training_metrics['total_loss'] += loss
            self.training_metrics['average_loss'] = (
                self.training_metrics['total_loss'] / self.training_metrics['episodes_completed']
            )
            
            # Update histories
            self.training_metrics['epsilon_history'].append(epsilon)
            self.training_metrics['memory_size_history'].append(memory_size)
            
            # Update domain performance
            if domain not in self.training_metrics['domain_performance']:
                self.training_metrics['domain_performance'][domain] = {
                    'episodes': 0,
                    'total_reward': 0.0,
                    'average_reward': 0.0
                }
            
            domain_perf = self.training_metrics['domain_performance'][domain]
            domain_perf['episodes'] += 1
            domain_perf['total_reward'] += reward
            domain_perf['average_reward'] = domain_perf['total_reward'] / domain_perf['episodes']
            
            # Record in monitoring orchestrator
            if self.monitoring_orchestrator:
                self.monitoring_orchestrator.record_training_metrics(
                    worker_id=self.training_metrics['session_id'],
                    episode_reward=reward,
                    episode_length=length,
                    training_loss=loss,
                    epsilon=epsilon,
                    memory_size=memory_size,
                    domain=domain
                )
            
            # Store episode data
            episode_data = {
                'episode': episode_idx,
                'reward': reward,
                'length': length,
                'loss': loss,
                'epsilon': epsilon,
                'memory_size': memory_size,
                'domain': domain,
                'timestamp': datetime.utcnow(),
                'additional_metrics': additional_metrics or {}
            }
            
            self.episode_history.append(episode_data)
            
            # Keep only recent history (last 1000 episodes)
            if len(self.episode_history) > 1000:
                self.episode_history = self.episode_history[-1000:]
            
            # Update performance trends
            self._update_performance_trends()
            
        except Exception as e:
            logger.error(f"Failed to record episode metrics: {e}")
    
    def record_classification_performance(
        self,
        model_name: str,
        accuracy: float,
        latency_seconds: float,
        cost: float,
        domain: str = "general_medicine",
        additional_metrics: Optional[Dict[str, Any]] = None
    ):
        """Record classification performance metrics"""
        try:
            # Record in monitoring orchestrator
            if self.monitoring_orchestrator:
                self.monitoring_orchestrator.record_classification_metrics(
                    model_name=model_name,
                    accuracy=accuracy,
                    latency_seconds=latency_seconds,
                    cost=cost,
                    domain=domain
                )
            
            # Store classification metrics
            classification_data = {
                'model_name': model_name,
                'accuracy': accuracy,
                'latency_seconds': latency_seconds,
                'cost': cost,
                'domain': domain,
                'timestamp': datetime.utcnow(),
                'additional_metrics': additional_metrics or {}
            }
            
            # Add to training metrics
            if 'classification_performance' not in self.training_metrics:
                self.training_metrics['classification_performance'] = []
            
            self.training_metrics['classification_performance'].append(classification_data)
            
            # Keep only recent classification data (last 100)
            if len(self.training_metrics['classification_performance']) > 100:
                self.training_metrics['classification_performance'] = (
                    self.training_metrics['classification_performance'][-100:]
                )
            
        except Exception as e:
            logger.error(f"Failed to record classification performance: {e}")
    
    def _update_performance_trends(self):
        """Update performance trend analysis"""
        try:
            if len(self.episode_history) < 10:
                return
            
            # Calculate recent performance (last 10 episodes)
            recent_episodes = self.episode_history[-10:]
            recent_rewards = [ep['reward'] for ep in recent_episodes]
            recent_losses = [ep['loss'] for ep in recent_episodes]
            
            # Calculate trends
            self.performance_trends = {
                'recent_average_reward': sum(recent_rewards) / len(recent_rewards),
                'recent_average_loss': sum(recent_losses) / len(recent_losses),
                'reward_trend': self._calculate_trend(recent_rewards),
                'loss_trend': self._calculate_trend(recent_losses),
                'stability_score': self._calculate_stability_score(recent_rewards),
                'convergence_indicator': self._calculate_convergence_indicator()
            }
            
        except Exception as e:
            logger.error(f"Failed to update performance trends: {e}")
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        y = values
        
        # Calculate slope
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_stability_score(self, values: List[float]) -> float:
        """Calculate stability score (0-1, higher is more stable)"""
        if len(values) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / abs(mean_val)
        
        # Convert to stability score (0-1)
        stability_score = max(0.0, 1.0 - cv)
        return min(1.0, stability_score)
    
    def _calculate_convergence_indicator(self) -> float:
        """Calculate convergence indicator (0-1, higher means more converged)"""
        if len(self.episode_history) < 20:
            return 0.0
        
        # Use recent episodes to check convergence
        recent_episodes = self.episode_history[-20:]
        rewards = [ep['reward'] for ep in recent_episodes]
        
        # Calculate variance in recent rewards
        mean_reward = sum(rewards) / len(rewards)
        variance = sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)
        
        # Normalize variance (assuming rewards are in reasonable range)
        normalized_variance = min(1.0, variance / 100.0)  # Adjust divisor based on expected reward range
        
        # Convert to convergence indicator
        convergence = max(0.0, 1.0 - normalized_variance)
        return min(1.0, convergence)
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get comprehensive training summary"""
        try:
            summary = {
                'session_info': {
                    'session_id': self.training_metrics.get('session_id', 'unknown'),
                    'start_time': self.training_metrics.get('start_time'),
                    'episodes_completed': self.training_metrics.get('episodes_completed', 0),
                    'current_time': datetime.utcnow()
                },
                'performance_metrics': {
                    'total_reward': self.training_metrics.get('total_reward', 0.0),
                    'average_reward': self.training_metrics.get('average_reward', 0.0),
                    'best_reward': self.training_metrics.get('best_reward', 0.0),
                    'worst_reward': self.training_metrics.get('worst_reward', 0.0),
                    'average_loss': self.training_metrics.get('average_loss', 0.0)
                },
                'performance_trends': self.performance_trends,
                'domain_performance': self.training_metrics.get('domain_performance', {}),
                'recent_episodes': self.episode_history[-10:] if self.episode_history else [],
                'monitoring_status': {
                    'monitoring_enabled': self.monitoring_orchestrator is not None,
                    'health_status': self.monitoring_orchestrator.get_health_status() if self.monitoring_orchestrator else {}
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get training summary: {e}")
            return {}
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance improvement recommendations"""
        try:
            recommendations = []
            
            if not self.performance_trends:
                return ["Insufficient data for recommendations"]
            
            # Check reward trend
            if self.performance_trends.get('reward_trend') == 'decreasing':
                recommendations.append("Reward is decreasing - consider adjusting learning rate or exploration strategy")
            
            # Check stability
            stability = self.performance_trends.get('stability_score', 0.0)
            if stability < 0.3:
                recommendations.append("High variance in performance - consider reducing learning rate or increasing batch size")
            
            # Check convergence
            convergence = self.performance_trends.get('convergence_indicator', 0.0)
            if convergence > 0.8:
                recommendations.append("Model appears to be converging - consider reducing exploration or stopping training")
            
            # Check loss trend
            if self.performance_trends.get('loss_trend') == 'increasing':
                recommendations.append("Training loss is increasing - consider reducing learning rate or checking for overfitting")
            
            # Check domain performance
            domain_perf = self.training_metrics.get('domain_performance', {})
            for domain, perf in domain_perf.items():
                if perf.get('average_reward', 0.0) < 0.1:
                    recommendations.append(f"Poor performance in {domain} domain - consider domain-specific tuning")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get performance recommendations: {e}")
            return ["Error generating recommendations"]
    
    def stop_training_session(self):
        """Stop monitoring training session"""
        try:
            # Record session end
            if self.monitoring_orchestrator:
                self.monitoring_orchestrator.record_training_metrics(
                    worker_id=self.training_metrics.get('session_id', 'unknown'),
                    episode_reward=0.0,
                    episode_length=0,
                    training_loss=0.0,
                    epsilon=0.0,
                    memory_size=0,
                    domain="training_end"
                )
            
            # Update training metrics
            self.training_metrics['end_time'] = datetime.utcnow()
            self.training_metrics['duration_seconds'] = (
                self.training_metrics['end_time'] - self.training_metrics['start_time']
            ).total_seconds()
            
            logger.info("Training session monitoring stopped", 
                       session_id=self.training_metrics.get('session_id', 'unknown'))
            
        except Exception as e:
            logger.error(f"Failed to stop training session monitoring: {e}")
    
    def cleanup(self):
        """Cleanup monitoring resources"""
        try:
            if self.monitoring_orchestrator:
                self.monitoring_orchestrator.stop_monitoring()
            
            logger.info("Training monitor cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup training monitor: {e}")

# Factory function for easy training monitor setup
def create_training_monitor(
    enable_monitoring: bool = True,
    output_dir: str = "monitoring_output",
    metrics_port: int = 8000,
    **kwargs
) -> TrainingMonitor:
    """
    Create training monitor with default configuration
    
    Args:
        enable_monitoring: Whether to enable monitoring
        output_dir: Output directory for monitoring data
        metrics_port: Port for metrics server
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured TrainingMonitor
    """
    config = TrainingMonitorConfig(
        enable_monitoring=enable_monitoring,
        output_dir=output_dir,
        metrics_port=metrics_port,
        **kwargs
    )
    
    return TrainingMonitor(config)
