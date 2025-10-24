"""
Optimization Integration
Integrates all optimization components into the RL training pipeline
"""

import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import structlog
from datetime import datetime
import json
from pathlib import Path

from .cache_manager import CacheManager, get_global_cache
from .performance_optimizer import PerformanceOptimizer, create_performance_optimizer
from .model_optimizer import ModelOptimizer, create_model_optimizer

logger = structlog.get_logger(__name__)

@dataclass
class OptimizationConfig:
    """Configuration for optimization integration"""
    enable_caching: bool = True
    enable_performance_optimization: bool = True
    enable_model_optimization: bool = True
    cache_size_mb: int = 500
    memory_threshold: float = 0.8
    gpu_memory_threshold: float = 0.9
    enable_profiling: bool = True
    profiling_output_dir: str = "optimization_output"
    enable_mixed_precision: bool = True
    enable_gradient_clipping: bool = True
    enable_lr_scheduling: bool = True
    enable_early_stopping: bool = True

class OptimizationIntegration:
    """
    Main optimization integration system
    - Coordinates all optimization components
    - Provides unified optimization interface
    - Monitors optimization effectiveness
    - Generates optimization reports
    """
    
    def __init__(self, config: OptimizationConfig):
        """
        Initialize optimization integration
        
        Args:
            config: Optimization configuration
        """
        self.config = config
        self.cache_manager = None
        self.performance_optimizer = None
        self.model_optimizer = None
        
        # Optimization state
        self.optimization_active = False
        self.optimization_thread = None
        self.optimization_metrics = {}
        
        # Initialize components
        self._initialize_components()
        
        logger.info("OptimizationIntegration initialized", 
                   caching=config.enable_caching,
                   performance=config.enable_performance_optimization,
                   model=config.enable_model_optimization)
    
    def _initialize_components(self):
        """Initialize optimization components"""
        try:
            # Initialize cache manager
            if self.config.enable_caching:
                self.cache_manager = CacheManager(
                    max_memory_size=self.config.cache_size_mb * 1024 * 1024,
                    cache_dir="optimization_cache"
                )
                # Set as global cache
                from .cache_manager import set_global_cache
                set_global_cache(self.cache_manager)
                logger.info("Cache manager initialized")
            
            # Initialize performance optimizer
            if self.config.enable_performance_optimization:
                self.performance_optimizer = create_performance_optimizer(
                    enable_memory_optimization=True,
                    enable_gpu_optimization=True,
                    enable_cpu_optimization=True,
                    enable_caching=self.config.enable_caching,
                    cache_size_mb=self.config.cache_size_mb,
                    memory_threshold=self.config.memory_threshold,
                    gpu_memory_threshold=self.config.gpu_memory_threshold,
                    enable_profiling=self.config.enable_profiling,
                    profiling_output_dir=self.config.profiling_output_dir
                )
                logger.info("Performance optimizer initialized")
            
            # Initialize model optimizer
            if self.config.enable_model_optimization:
                self.model_optimizer = create_model_optimizer(
                    enable_mixed_precision=self.config.enable_mixed_precision,
                    enable_gradient_clipping=self.config.enable_gradient_clipping,
                    enable_lr_scheduling=self.config.enable_lr_scheduling,
                    enable_early_stopping=self.config.enable_early_stopping
                )
                logger.info("Model optimizer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization components: {e}")
            raise
    
    def start_optimization(self):
        """Start optimization monitoring and management"""
        if self.optimization_active:
            logger.warning("Optimization already active")
            return
        
        self.optimization_active = True
        
        # Start performance monitoring
        if self.performance_optimizer:
            self.performance_optimizer.start_monitoring()
        
        # Start optimization thread
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()
        
        logger.info("Optimization started")
    
    def stop_optimization(self):
        """Stop optimization monitoring and management"""
        self.optimization_active = False
        
        # Stop performance monitoring
        if self.performance_optimizer:
            self.performance_optimizer.stop_monitoring()
        
        # Wait for optimization thread
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        
        logger.info("Optimization stopped")
    
    def _optimization_loop(self):
        """Main optimization loop"""
        while self.optimization_active:
            try:
                # Monitor optimization effectiveness
                self._monitor_optimization_effectiveness()
                
                # Cleanup expired cache entries
                if self.cache_manager:
                    self.cache_manager.cleanup_expired()
                
                # Sleep
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                time.sleep(30)
    
    def _monitor_optimization_effectiveness(self):
        """Monitor optimization effectiveness"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cache_stats': self.cache_manager.get_stats() if self.cache_manager else {},
                'performance_summary': self.performance_optimizer.get_performance_summary() if self.performance_optimizer else {},
                'model_optimization_summary': self.model_optimizer.get_optimization_summary() if self.model_optimizer else {}
            }
            
            self.optimization_metrics = metrics
            
        except Exception as e:
            logger.error(f"Failed to monitor optimization effectiveness: {e}")
    
    def optimize_training_data(self, data: Any) -> Any:
        """Optimize training data using caching and performance optimization"""
        try:
            if not self.cache_manager:
                return data
            
            # Generate cache key
            cache_key = f"training_data_{hash(str(data))}"
            
            # Try to get from cache
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.debug("Training data cache hit")
                return cached_data
            
            # Optimize data if not in cache
            optimized_data = self._optimize_data(data)
            
            # Cache optimized data
            self.cache_manager.put(cache_key, optimized_data, ttl=3600)  # 1 hour TTL
            
            return optimized_data
            
        except Exception as e:
            logger.error(f"Failed to optimize training data: {e}")
            return data
    
    def _optimize_data(self, data: Any) -> Any:
        """Optimize data structure and format"""
        # Placeholder for actual data optimization
        # This could include:
        # - Converting to optimal data types
        # - Compressing data
        # - Reorganizing memory layout
        # - GPU memory optimization
        
        return data
    
    def optimize_model_training(
        self,
        model,
        optimizer,
        loss_fn,
        inputs,
        targets
    ) -> Dict[str, Any]:
        """Optimize model training step"""
        try:
            if not self.model_optimizer:
                # Fallback to standard training
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = loss_fn(outputs, targets)
                loss.backward()
                optimizer.step()
                
                return {
                    'loss': loss.item(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Use model optimizer
            return self.model_optimizer.optimize_training_step(
                model, optimizer, loss_fn, inputs, targets
            )
            
        except Exception as e:
            logger.error(f"Failed to optimize model training: {e}")
            raise
    
    def optimize_batch_processing(self, batch_data: Any) -> Any:
        """Optimize batch processing using performance optimization"""
        try:
            if not self.performance_optimizer:
                return batch_data
            
            return self.performance_optimizer.optimize_training_batch(batch_data)
            
        except Exception as e:
            logger.error(f"Failed to optimize batch processing: {e}")
            return batch_data
    
    def setup_optimized_optimizer(self, model, learning_rate: float = 1e-3):
        """Setup optimized optimizer for model"""
        try:
            if not self.model_optimizer:
                # Fallback to standard optimizer
                import torch.optim as optim
                return optim.Adam(model.parameters(), lr=learning_rate)
            
            return self.model_optimizer.setup_optimizer(model, learning_rate)
            
        except Exception as e:
            logger.error(f"Failed to setup optimized optimizer: {e}")
            raise
    
    def should_stop_training(self, loss: float) -> bool:
        """Check if training should stop based on optimization criteria"""
        try:
            if not self.model_optimizer:
                return False
            
            return self.model_optimizer.should_stop_training(loss)
            
        except Exception as e:
            logger.error(f"Failed to check training stop condition: {e}")
            return False
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get comprehensive optimization summary"""
        try:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'optimization_active': self.optimization_active,
                'config': {
                    'caching': self.config.enable_caching,
                    'performance_optimization': self.config.enable_performance_optimization,
                    'model_optimization': self.config.enable_model_optimization
                },
                'cache_stats': self.cache_manager.get_stats() if self.cache_manager else {},
                'performance_summary': self.performance_optimizer.get_performance_summary() if self.performance_optimizer else {},
                'model_optimization_summary': self.model_optimizer.get_optimization_summary() if self.model_optimizer else {},
                'optimization_metrics': self.optimization_metrics
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get optimization summary: {e}")
            return {}
    
    def save_optimization_report(self, filepath: str = None):
        """Save comprehensive optimization report"""
        try:
            if filepath is None:
                filepath = f"optimization_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = {
                'summary': self.get_optimization_summary(),
                'config': self.config.__dict__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Save individual component reports
            if self.performance_optimizer:
                perf_report_path = filepath.replace('.json', '_performance.json')
                self.performance_optimizer.save_performance_report(perf_report_path)
            
            if self.model_optimizer:
                model_report_path = filepath.replace('.json', '_model.json')
                self.model_optimizer.save_optimization_report(model_report_path)
            
            # Save main report
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Optimization report saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save optimization report: {e}")
    
    def cleanup(self):
        """Cleanup optimization resources"""
        try:
            self.stop_optimization()
            
            if self.cache_manager:
                self.cache_manager.clear()
            
            if self.performance_optimizer:
                self.performance_optimizer.cleanup()
            
            logger.info("Optimization integration cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup optimization integration: {e}")

# Factory function for easy optimization integration setup
def create_optimization_integration(
    enable_caching: bool = True,
    enable_performance_optimization: bool = True,
    enable_model_optimization: bool = True,
    cache_size_mb: int = 500,
    **kwargs
) -> OptimizationIntegration:
    """
    Create optimization integration with default configuration
    
    Args:
        enable_caching: Enable caching
        enable_performance_optimization: Enable performance optimization
        enable_model_optimization: Enable model optimization
        cache_size_mb: Cache size in MB
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured OptimizationIntegration
    """
    config = OptimizationConfig(
        enable_caching=enable_caching,
        enable_performance_optimization=enable_performance_optimization,
        enable_model_optimization=enable_model_optimization,
        cache_size_mb=cache_size_mb,
        **kwargs
    )
    
    return OptimizationIntegration(config)
