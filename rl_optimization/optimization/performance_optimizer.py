"""
Performance Optimizer
Advanced performance optimization for RL training pipeline
"""

import time
import threading
import psutil
import gc
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
import structlog
import numpy as np
import torch
from datetime import datetime
import json
from pathlib import Path

from .cache_manager import CacheManager, get_global_cache, cached

logger = structlog.get_logger(__name__)

@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    enable_memory_optimization: bool = True
    enable_gpu_optimization: bool = True
    enable_cpu_optimization: bool = True
    enable_caching: bool = True
    memory_threshold: float = 0.8  # 80% memory usage threshold
    gpu_memory_threshold: float = 0.9  # 90% GPU memory usage threshold
    cache_size_mb: int = 500
    enable_profiling: bool = True
    profiling_output_dir: str = "profiling_output"

class PerformanceProfiler:
    """Performance profiler for identifying bottlenecks"""
    
    def __init__(self, output_dir: str = "profiling_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profiles = {}
        self.active_profiles = {}
        
    def start_profile(self, name: str) -> str:
        """Start profiling a section of code"""
        profile_id = f"{name}_{int(time.time() * 1000)}"
        self.active_profiles[profile_id] = {
            'name': name,
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss,
            'start_cpu': psutil.cpu_percent()
        }
        return profile_id
    
    def end_profile(self, profile_id: str) -> Dict[str, Any]:
        """End profiling and return results"""
        if profile_id not in self.active_profiles:
            return {}
        
        profile_data = self.active_profiles[profile_id]
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_cpu = psutil.cpu_percent()
        
        result = {
            'name': profile_data['name'],
            'duration_seconds': end_time - profile_data['start_time'],
            'memory_delta_bytes': end_memory - profile_data['start_memory'],
            'cpu_usage_percent': (profile_data['start_cpu'] + end_cpu) / 2,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store profile
        self.profiles[profile_id] = result
        del self.active_profiles[profile_id]
        
        return result
    
    def save_profiles(self, filename: str = None):
        """Save all profiles to file"""
        if filename is None:
            filename = f"profiles_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(self.profiles, f, indent=2)
        
        logger.info(f"Profiles saved to {filepath}")

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.optimization_history = []
    
    def check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        memory = psutil.virtual_memory()
        return memory.percent / 100.0 > self.threshold
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        start_memory = psutil.Process().memory_info().rss
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear PyTorch cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Clear numpy cache
        try:
            import numpy as np
            np.finfo(np.dtype('float64'))  # Force numpy to clear internal caches
        except:
            pass
        
        end_memory = psutil.Process().memory_info().rss
        freed_bytes = start_memory - end_memory
        
        result = {
            'freed_bytes': freed_bytes,
            'collected_objects': collected,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.optimization_history.append(result)
        logger.info("Memory optimization completed", freed_bytes=freed_bytes, collected=collected)
        
        return result
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory': {
                'rss_bytes': memory_info.rss,
                'vms_bytes': memory_info.vms,
                'percent': memory_percent
            },
            'system_memory': {
                'total_bytes': system_memory.total,
                'available_bytes': system_memory.available,
                'percent': system_memory.percent
            },
            'optimization_history': self.optimization_history[-10:]  # Last 10 optimizations
        }

class GPUOptimizer:
    """GPU optimization utilities"""
    
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold
        self.optimization_history = []
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()
    
    def check_gpu_memory_pressure(self) -> bool:
        """Check if GPU is under memory pressure"""
        if not self.is_gpu_available():
            return False
        
        gpu_memory = torch.cuda.memory_allocated()
        gpu_memory_total = torch.cuda.get_device_properties(0).total_memory
        return gpu_memory / gpu_memory_total > self.threshold
    
    def optimize_gpu_memory(self) -> Dict[str, Any]:
        """Optimize GPU memory usage"""
        if not self.is_gpu_available():
            return {'error': 'GPU not available'}
        
        start_memory = torch.cuda.memory_allocated()
        
        # Clear GPU cache
        torch.cuda.empty_cache()
        
        # Synchronize
        torch.cuda.synchronize()
        
        end_memory = torch.cuda.memory_allocated()
        freed_bytes = start_memory - end_memory
        
        result = {
            'freed_bytes': freed_bytes,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.optimization_history.append(result)
        logger.info("GPU memory optimization completed", freed_bytes=freed_bytes)
        
        return result
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get GPU statistics"""
        if not self.is_gpu_available():
            return {'available': False}
        
        allocated = torch.cuda.memory_allocated()
        cached = torch.cuda.memory_reserved()
        total = torch.cuda.get_device_properties(0).total_memory
        
        return {
            'available': True,
            'allocated_bytes': allocated,
            'cached_bytes': cached,
            'total_bytes': total,
            'utilization': allocated / total,
            'optimization_history': self.optimization_history[-10:]
        }

class CPUOptimizer:
    """CPU optimization utilities"""
    
    def __init__(self):
        self.optimization_history = []
    
    def get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'usage_percent': cpu_percent,
            'count': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else None,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def optimize_cpu_usage(self) -> Dict[str, Any]:
        """Optimize CPU usage"""
        # Set thread affinity if possible
        try:
            import os
            # Set CPU affinity to use all available cores
            process = psutil.Process()
            process.cpu_affinity(list(range(psutil.cpu_count())))
        except Exception as e:
            logger.warning(f"Failed to set CPU affinity: {e}")
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_count': psutil.cpu_count()
        }
        
        self.optimization_history.append(result)
        return result

class PerformanceOptimizer:
    """
    Main performance optimization system
    - Memory optimization
    - GPU optimization
    - CPU optimization
    - Caching strategies
    - Performance profiling
    """
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize performance optimizer
        
        Args:
            config: Performance configuration
        """
        self.config = config
        self.cache_manager = None
        self.profiler = None
        self.memory_optimizer = None
        self.gpu_optimizer = None
        self.cpu_optimizer = None
        
        # Initialize components
        self._initialize_components()
        
        # Performance monitoring
        self.performance_history = []
        self.optimization_thread = None
        self.is_monitoring = False
        
        logger.info("PerformanceOptimizer initialized", 
                   memory_optimization=config.enable_memory_optimization,
                   gpu_optimization=config.enable_gpu_optimization,
                   cpu_optimization=config.enable_cpu_optimization,
                   caching=config.enable_caching)
    
    def _initialize_components(self):
        """Initialize optimization components"""
        try:
            # Initialize cache manager
            if self.config.enable_caching:
                self.cache_manager = CacheManager(
                    max_memory_size=self.config.cache_size_mb * 1024 * 1024,
                    cache_dir="performance_cache"
                )
                # Set as global cache
                from .cache_manager import set_global_cache
                set_global_cache(self.cache_manager)
                logger.info("Cache manager initialized")
            
            # Initialize profiler
            if self.config.enable_profiling:
                self.profiler = PerformanceProfiler(self.config.profiling_output_dir)
                logger.info("Performance profiler initialized")
            
            # Initialize optimizers
            if self.config.enable_memory_optimization:
                self.memory_optimizer = MemoryOptimizer(self.config.memory_threshold)
                logger.info("Memory optimizer initialized")
            
            if self.config.enable_gpu_optimization:
                self.gpu_optimizer = GPUOptimizer(self.config.gpu_memory_threshold)
                logger.info("GPU optimizer initialized")
            
            if self.config.enable_cpu_optimization:
                self.cpu_optimizer = CPUOptimizer()
                logger.info("CPU optimizer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize performance components: {e}")
            raise
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            logger.warning("Performance monitoring already running")
            return
        
        self.is_monitoring = True
        self.optimization_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.optimization_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check memory pressure
                if self.memory_optimizer and self.memory_optimizer.check_memory_pressure():
                    logger.warning("High memory usage detected, optimizing...")
                    self.memory_optimizer.optimize_memory()
                
                # Check GPU memory pressure
                if (self.gpu_optimizer and 
                    self.gpu_optimizer.is_gpu_available() and 
                    self.gpu_optimizer.check_gpu_memory_pressure()):
                    logger.warning("High GPU memory usage detected, optimizing...")
                    self.gpu_optimizer.optimize_gpu_memory()
                
                # Record performance metrics
                self._record_performance_metrics()
                
                # Sleep
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(10)
    
    def _record_performance_metrics(self):
        """Record current performance metrics"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'memory': self.memory_optimizer.get_memory_stats() if self.memory_optimizer else {},
                'gpu': self.gpu_optimizer.get_gpu_stats() if self.gpu_optimizer else {},
                'cpu': self.cpu_optimizer.get_cpu_stats() if self.cpu_optimizer else {},
                'cache': self.cache_manager.get_stats() if self.cache_manager else {}
            }
            
            self.performance_history.append(metrics)
            
            # Keep only recent history (last 1000 entries)
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
            
        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}")
    
    def profile_function(self, name: str):
        """Decorator for profiling functions"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                if not self.profiler:
                    return func(*args, **kwargs)
                
                profile_id = self.profiler.start_profile(name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profile_result = self.profiler.end_profile(profile_id)
                    logger.debug(f"Function {name} profiled", **profile_result)
            
            return wrapper
        return decorator
    
    def optimize_training_batch(self, batch_data: Any) -> Any:
        """Optimize training batch data"""
        try:
            # Check if we need memory optimization
            if (self.memory_optimizer and 
                self.memory_optimizer.check_memory_pressure()):
                self.memory_optimizer.optimize_memory()
            
            # Check if we need GPU optimization
            if (self.gpu_optimizer and 
                self.gpu_optimizer.is_gpu_available() and 
                self.gpu_optimizer.check_gpu_memory_pressure()):
                self.gpu_optimizer.optimize_gpu_memory()
            
            # Use cache if available
            if self.cache_manager:
                cache_key = f"batch_{hash(str(batch_data))}"
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Process batch (placeholder for actual optimization)
                optimized_batch = self._optimize_batch_data(batch_data)
                
                # Cache result
                self.cache_manager.put(cache_key, optimized_batch, ttl=3600)  # 1 hour TTL
                
                return optimized_batch
            
            return self._optimize_batch_data(batch_data)
            
        except Exception as e:
            logger.error(f"Failed to optimize training batch: {e}")
            return batch_data
    
    def _optimize_batch_data(self, batch_data: Any) -> Any:
        """Optimize batch data structure"""
        # Placeholder for actual optimization logic
        # This could include:
        # - Converting to optimal data types
        # - Compressing data
        # - Reorganizing memory layout
        # - GPU memory optimization
        
        return batch_data
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'monitoring_active': self.is_monitoring,
                'memory': self.memory_optimizer.get_memory_stats() if self.memory_optimizer else {},
                'gpu': self.gpu_optimizer.get_gpu_stats() if self.gpu_optimizer else {},
                'cpu': self.cpu_optimizer.get_cpu_stats() if self.cpu_optimizer else {},
                'cache': self.cache_manager.get_stats() if self.cache_manager else {},
                'profiles': len(self.profiler.profiles) if self.profiler else 0,
                'performance_history_length': len(self.performance_history)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    def save_performance_report(self, filename: str = None):
        """Save comprehensive performance report"""
        try:
            if filename is None:
                filename = f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = {
                'summary': self.get_performance_summary(),
                'performance_history': self.performance_history[-100:],  # Last 100 entries
                'profiles': self.profiler.profiles if self.profiler else {}
            }
            
            output_dir = Path(self.config.profiling_output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = output_dir / filename
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Performance report saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save performance report: {e}")
    
    def cleanup(self):
        """Cleanup optimization resources"""
        try:
            self.stop_monitoring()
            
            if self.cache_manager:
                self.cache_manager.clear()
            
            if self.profiler:
                self.profiler.save_profiles()
            
            logger.info("Performance optimizer cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup performance optimizer: {e}")

# Factory function for easy performance optimizer setup
def create_performance_optimizer(
    enable_memory_optimization: bool = True,
    enable_gpu_optimization: bool = True,
    enable_cpu_optimization: bool = True,
    enable_caching: bool = True,
    cache_size_mb: int = 500,
    **kwargs
) -> PerformanceOptimizer:
    """
    Create performance optimizer with default configuration
    
    Args:
        enable_memory_optimization: Enable memory optimization
        enable_gpu_optimization: Enable GPU optimization
        enable_cpu_optimization: Enable CPU optimization
        enable_caching: Enable caching
        cache_size_mb: Cache size in MB
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured PerformanceOptimizer
    """
    config = PerformanceConfig(
        enable_memory_optimization=enable_memory_optimization,
        enable_gpu_optimization=enable_gpu_optimization,
        enable_cpu_optimization=enable_cpu_optimization,
        enable_caching=enable_caching,
        cache_size_mb=cache_size_mb,
        **kwargs
    )
    
    return PerformanceOptimizer(config)
