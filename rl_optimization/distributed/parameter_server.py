"""
Parameter Server for Distributed Training
Centralized parameter management with weight synchronization
"""

import ray
import torch
import numpy as np
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import structlog
import threading
from collections import deque
import json

logger = structlog.get_logger(__name__)

@dataclass
class ParameterUpdate:
    """Parameter update from worker"""
    worker_id: int
    parameters: Dict[str, Any]
    timestamp: datetime
    episode: int
    metadata: Dict[str, Any]

@dataclass
class ParameterStats:
    """Parameter server statistics"""
    total_updates: int
    successful_updates: int
    failed_updates: int
    last_update: Optional[datetime]
    average_update_time_ms: float
    parameter_size_mb: float

@ray.remote
class ParameterServer:
    """
    Centralized parameter management
    - Store and serve model weights
    - Aggregate gradients from workers
    - Implement synchronous/asynchronous updates
    - Handle worker failures gracefully
    """
    
    def __init__(self, sync_mode: str = "async"):
        """
        Initialize parameter server
        
        Args:
            sync_mode: Synchronization mode ("sync" or "async")
        """
        self.sync_mode = sync_mode
        self.current_parameters = {}
        self.parameter_history = deque(maxlen=1000)
        self.update_queue = deque()
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = ParameterStats(
            total_updates=0,
            successful_updates=0,
            failed_updates=0,
            last_update=None,
            average_update_time_ms=0.0,
            parameter_size_mb=0.0
        )
        
        # Worker tracking
        self.worker_updates = {}
        self.worker_episodes = {}
        
        logger.info(f"ParameterServer initialized with {sync_mode} mode")
    
    def initialize_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Initialize parameters
        
        Args:
            parameters: Initial parameter values
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                self.current_parameters = parameters.copy()
                self.parameter_history.append({
                    'parameters': parameters,
                    'timestamp': datetime.utcnow(),
                    'episode': 0,
                    'source': 'initialization'
                })
                
                # Calculate parameter size
                self._update_parameter_size()
                
                logger.info("Parameters initialized", 
                           num_parameters=len(parameters),
                           size_mb=self.stats.parameter_size_mb)
                return True
                
        except Exception as e:
            logger.error(f"Parameter initialization failed: {e}")
            return False
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current parameters
        
        Returns:
            Current parameter dictionary
        """
        with self.lock:
            return self.current_parameters.copy()
    
    def update_parameters(
        self, 
        worker_id: int, 
        parameters: Dict[str, Any], 
        episode: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update parameters from worker
        
        Args:
            worker_id: Worker identifier
            parameters: New parameters
            episode: Episode number
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        start_time = time.time()
        
        try:
            with self.lock:
                # Track worker update
                self.worker_updates[worker_id] = {
                    'parameters': parameters,
                    'timestamp': datetime.utcnow(),
                    'episode': episode,
                    'metadata': metadata or {}
                }
                self.worker_episodes[worker_id] = episode
                
                # Update statistics
                self.stats.total_updates += 1
                
                if self.sync_mode == "sync":
                    # Synchronous update - wait for all workers
                    success = self._synchronous_update(worker_id, parameters, episode)
                else:
                    # Asynchronous update - immediate update
                    success = self._asynchronous_update(worker_id, parameters, episode)
                
                if success:
                    self.stats.successful_updates += 1
                    self.stats.last_update = datetime.utcnow()
                    
                    # Update timing statistics
                    update_time = (time.time() - start_time) * 1000
                    self._update_average_time(update_time)
                    
                    logger.info(f"Parameters updated from worker {worker_id}",
                               episode=episode,
                               update_time_ms=update_time)
                else:
                    self.stats.failed_updates += 1
                    logger.warning(f"Parameter update failed for worker {worker_id}")
                
                return success
                
        except Exception as e:
            self.stats.failed_updates += 1
            logger.error(f"Parameter update error for worker {worker_id}: {e}")
            return False
    
    def _synchronous_update(
        self, 
        worker_id: int, 
        parameters: Dict[str, Any], 
        episode: int
    ) -> bool:
        """Synchronous parameter update"""
        try:
            # Add to update queue
            update = ParameterUpdate(
                worker_id=worker_id,
                parameters=parameters,
                timestamp=datetime.utcnow(),
                episode=episode,
                metadata={}
            )
            self.update_queue.append(update)
            
            # Check if we have updates from all workers
            if len(self.update_queue) >= len(self.worker_updates):
                # Aggregate all updates
                aggregated_params = self._aggregate_parameters()
                if aggregated_params:
                    self.current_parameters = aggregated_params
                    self.parameter_history.append({
                        'parameters': aggregated_params,
                        'timestamp': datetime.utcnow(),
                        'episode': episode,
                        'source': 'synchronous_aggregation'
                    })
                    
                    # Clear update queue
                    self.update_queue.clear()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Synchronous update failed: {e}")
            return False
    
    def _asynchronous_update(
        self, 
        worker_id: int, 
        parameters: Dict[str, Any], 
        episode: int
    ) -> bool:
        """Asynchronous parameter update"""
        try:
            # Immediate update with weighted average
            if self.current_parameters:
                # Weighted average with existing parameters
                weight = 0.1  # Learning rate for parameter updates
                self.current_parameters = self._weighted_average(
                    self.current_parameters, 
                    parameters, 
                    weight
                )
            else:
                # First update
                self.current_parameters = parameters.copy()
            
            # Add to history
            self.parameter_history.append({
                'parameters': self.current_parameters,
                'timestamp': datetime.utcnow(),
                'episode': episode,
                'source': f'asynchronous_worker_{worker_id}'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Asynchronous update failed: {e}")
            return False
    
    def _aggregate_parameters(self) -> Optional[Dict[str, Any]]:
        """Aggregate parameters from all workers"""
        try:
            if not self.update_queue:
                return None
            
            # Simple averaging (in practice, use more sophisticated aggregation)
            all_parameters = [update.parameters for update in self.update_queue]
            
            if not all_parameters:
                return None
            
            # Average parameters
            aggregated = {}
            for key in all_parameters[0].keys():
                values = [params[key] for params in all_parameters if key in params]
                if values:
                    if isinstance(values[0], (int, float)):
                        aggregated[key] = np.mean(values)
                    elif isinstance(values[0], np.ndarray):
                        aggregated[key] = np.mean(values, axis=0)
                    elif isinstance(values[0], torch.Tensor):
                        aggregated[key] = torch.mean(torch.stack(values), dim=0)
                    else:
                        aggregated[key] = values[0]  # Take first value for non-numeric types
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Parameter aggregation failed: {e}")
            return None
    
    def _weighted_average(
        self, 
        current: Dict[str, Any], 
        new: Dict[str, Any], 
        weight: float
    ) -> Dict[str, Any]:
        """Calculate weighted average of parameters"""
        result = {}
        
        for key in current.keys():
            if key in new:
                if isinstance(current[key], (int, float)):
                    result[key] = (1 - weight) * current[key] + weight * new[key]
                elif isinstance(current[key], np.ndarray):
                    result[key] = (1 - weight) * current[key] + weight * new[key]
                elif isinstance(current[key], torch.Tensor):
                    result[key] = (1 - weight) * current[key] + weight * new[key]
                else:
                    result[key] = new[key]  # Use new value for non-numeric types
            else:
                result[key] = current[key]
        
        return result
    
    def _update_parameter_size(self):
        """Update parameter size statistics"""
        try:
            total_size = 0
            for key, value in self.current_parameters.items():
                if isinstance(value, np.ndarray):
                    total_size += value.nbytes
                elif isinstance(value, torch.Tensor):
                    total_size += value.element_size() * value.nelement()
                elif isinstance(value, (int, float)):
                    total_size += 8  # Assume 8 bytes for numeric types
            
            self.stats.parameter_size_mb = total_size / (1024 * 1024)
            
        except Exception as e:
            logger.warning(f"Failed to calculate parameter size: {e}")
    
    def _update_average_time(self, update_time_ms: float):
        """Update average update time"""
        if self.stats.successful_updates == 1:
            self.stats.average_update_time_ms = update_time_ms
        else:
            # Running average
            self.stats.average_update_time_ms = (
                (self.stats.average_update_time_ms * (self.stats.successful_updates - 1) + update_time_ms) /
                self.stats.successful_updates
            )
    
    def get_parameter_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get parameter update history"""
        with self.lock:
            return list(self.parameter_history)[-limit:]
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        with self.lock:
            status = {}
            for worker_id, update in self.worker_updates.items():
                status[worker_id] = {
                    'last_update': update['timestamp'].isoformat(),
                    'episode': update['episode'],
                    'metadata': update['metadata']
                }
            return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parameter server statistics"""
        with self.lock:
            return {
                'total_updates': self.stats.total_updates,
                'successful_updates': self.stats.successful_updates,
                'failed_updates': self.stats.failed_updates,
                'success_rate': (
                    self.stats.successful_updates / max(self.stats.total_updates, 1)
                ),
                'last_update': (
                    self.stats.last_update.isoformat() if self.stats.last_update else None
                ),
                'average_update_time_ms': self.stats.average_update_time_ms,
                'parameter_size_mb': self.stats.parameter_size_mb,
                'num_workers': len(self.worker_updates),
                'sync_mode': self.sync_mode
            }
    
    def reset_statistics(self):
        """Reset parameter server statistics"""
        with self.lock:
            self.stats = ParameterStats(
                total_updates=0,
                successful_updates=0,
                failed_updates=0,
                last_update=None,
                average_update_time_ms=0.0,
                parameter_size_mb=0.0
            )
            logger.info("Parameter server statistics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        with self.lock:
            return {
                'status': 'healthy',
                'num_parameters': len(self.current_parameters),
                'parameter_size_mb': self.stats.parameter_size_mb,
                'total_updates': self.stats.total_updates,
                'num_workers': len(self.worker_updates),
                'timestamp': datetime.utcnow().isoformat()
            }
