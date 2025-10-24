"""
Distributed RL Training with Ray
Multi-GPU training support with distributed experience replay and parameter synchronization
"""

import ray
import torch
import numpy as np
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import structlog
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty

from ..rl_training.rl_agent import MultiObjectiveRLAgent, RLState, RLAction, RLReward
from ..data.dataset import TrainingSample
from .worker import RLWorker
from .parameter_server import ParameterServer

logger = structlog.get_logger(__name__)

@dataclass
class DistributedConfig:
    """Configuration for distributed training"""
    num_workers: int = 4
    num_gpus: int = 1
    batch_size: int = 32
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon: float = 0.1
    memory_size: int = 10000
    sync_frequency: int = 10
    evaluation_frequency: int = 50
    save_frequency: int = 100
    max_episodes: int = 1000
    checkpoint_dir: str = "checkpoints"

@dataclass
class TrainingMetrics:
    """Distributed training metrics"""
    episode: int
    worker_id: int
    episode_reward: float
    episode_length: int
    training_loss: float
    epsilon: float
    timestamp: datetime
    metadata: Dict[str, Any]

class DistributedRLTrainer:
    """
    Distributed training using Ray
    - Multi-GPU training support
    - Distributed experience replay buffer
    - Parameter server for weight synchronization
    - Dynamic worker scaling
    - Fault tolerance with automatic recovery
    """
    
    def __init__(
        self,
        config: DistributedConfig,
        training_data_path: str,
        output_dir: str
    ):
        """
        Initialize distributed trainer
        
        Args:
            config: Distributed training configuration
            training_data_path: Path to training data
            output_dir: Output directory for results
        """
        self.config = config
        self.training_data_path = training_data_path
        self.output_dir = output_dir
        
        # Initialize Ray
        if not ray.is_initialized():
            ray.init(
                num_cpus=config.num_workers,
                num_gpus=config.num_gpus,
                ignore_reinit_error=True
            )
        
        # Create distributed components
        self.parameter_server = ParameterServer.remote()
        self.workers = []
        self.training_metrics = []
        self.global_episode = 0
        
        # Training state
        self.is_training = False
        self.training_thread = None
        
        logger.info("DistributedRLTrainer initialized",
                   num_workers=config.num_workers,
                   num_gpus=config.num_gpus)
    
    def start_training(self):
        """Start distributed training"""
        if self.is_training:
            logger.warning("Training already in progress")
            return
        
        self.is_training = True
        self.training_thread = threading.Thread(target=self._training_loop)
        self.training_thread.start()
        
        logger.info("Distributed training started")
    
    def stop_training(self):
        """Stop distributed training"""
        self.is_training = False
        if self.training_thread:
            self.training_thread.join()
        
        logger.info("Distributed training stopped")
    
    def _training_loop(self):
        """Main training loop"""
        try:
            # Create workers
            self._create_workers()
            
            # Training loop
            while self.is_training and self.global_episode < self.config.max_episodes:
                # Run episodes on all workers
                episode_results = self._run_episodes()
                
                # Collect metrics
                self._collect_metrics(episode_results)
                
                # Synchronize parameters
                if self.global_episode % self.config.sync_frequency == 0:
                    self._synchronize_parameters()
                
                # Evaluate model
                if self.global_episode % self.config.evaluation_frequency == 0:
                    self._evaluate_model()
                
                # Save checkpoint
                if self.global_episode % self.config.save_frequency == 0:
                    self._save_checkpoint()
                
                self.global_episode += 1
                
                # Log progress
                if self.global_episode % 10 == 0:
                    self._log_progress()
            
            # Final evaluation and save
            self._final_evaluation()
            self._save_final_model()
            
        except Exception as e:
            logger.error(f"Training loop error: {e}")
            raise
        finally:
            self._cleanup_workers()
    
    def _create_workers(self):
        """Create distributed workers"""
        self.workers = []
        
        for worker_id in range(self.config.num_workers):
            worker = RLWorker.remote(
                worker_id=worker_id,
                config=self.config,
                training_data_path=self.training_data_path,
                parameter_server=self.parameter_server
            )
            self.workers.append(worker)
        
        logger.info(f"Created {len(self.workers)} workers")
    
    def _run_episodes(self) -> List[Dict[str, Any]]:
        """Run episodes on all workers"""
        # Submit episodes to workers
        episode_futures = []
        for worker in self.workers:
            future = worker.run_episode.remote(self.global_episode)
            episode_futures.append(future)
        
        # Collect results
        episode_results = []
        for future in episode_futures:
            try:
                result = ray.get(future, timeout=300)  # 5 minute timeout
                episode_results.append(result)
            except Exception as e:
                logger.error(f"Worker episode failed: {e}")
                # Create fallback result
                episode_results.append({
                    'worker_id': -1,
                    'episode': self.global_episode,
                    'reward': 0.0,
                    'length': 0,
                    'loss': 0.0,
                    'error': str(e)
                })
        
        return episode_results
    
    def _collect_metrics(self, episode_results: List[Dict[str, Any]]):
        """Collect and store training metrics"""
        for result in episode_results:
            if 'error' in result:
                continue
            
            metric = TrainingMetrics(
                episode=result['episode'],
                worker_id=result['worker_id'],
                episode_reward=result['reward'],
                episode_length=result['length'],
                training_loss=result['loss'],
                epsilon=result.get('epsilon', 0.0),
                timestamp=datetime.utcnow(),
                metadata=result.get('metadata', {})
            )
            self.training_metrics.append(metric)
    
    def _synchronize_parameters(self):
        """Synchronize parameters across all workers"""
        try:
            # Get current parameters from parameter server
            current_params = ray.get(self.parameter_server.get_parameters.remote())
            
            # Update all workers with current parameters
            update_futures = []
            for worker in self.workers:
                future = worker.update_parameters.remote(current_params)
                update_futures.append(future)
            
            # Wait for all updates to complete
            ray.get(update_futures)
            
            logger.info("Parameters synchronized across all workers")
            
        except Exception as e:
            logger.error(f"Parameter synchronization failed: {e}")
    
    def _evaluate_model(self):
        """Evaluate model performance"""
        try:
            # Run evaluation on all workers
            eval_futures = []
            for worker in self.workers:
                future = worker.evaluate.remote()
                eval_futures.append(future)
            
            # Collect evaluation results
            eval_results = []
            for future in eval_futures:
                try:
                    result = ray.get(future, timeout=60)
                    eval_results.append(result)
                except Exception as e:
                    logger.warning(f"Worker evaluation failed: {e}")
            
            # Aggregate evaluation metrics
            if eval_results:
                self._aggregate_evaluation_metrics(eval_results)
            
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
    
    def _aggregate_evaluation_metrics(self, eval_results: List[Dict[str, Any]]):
        """Aggregate evaluation metrics from all workers"""
        # Calculate average metrics
        avg_accuracy = np.mean([r.get('accuracy', 0.0) for r in eval_results])
        avg_cost_efficiency = np.mean([r.get('cost_efficiency', 0.0) for r in eval_results])
        avg_processing_speed = np.mean([r.get('processing_speed', 0.0) for r in eval_results])
        avg_stability = np.mean([r.get('stability', 0.0) for r in eval_results])
        avg_domain_specialization = np.mean([r.get('domain_specialization', 0.0) for r in eval_results])
        
        evaluation_metrics = {
            'episode': self.global_episode,
            'accuracy': avg_accuracy,
            'cost_efficiency': avg_cost_efficiency,
            'processing_speed': avg_processing_speed,
            'stability': avg_stability,
            'domain_specialization': avg_domain_specialization,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Evaluation metrics", **evaluation_metrics)
    
    def _save_checkpoint(self):
        """Save training checkpoint"""
        try:
            # Get current parameters
            current_params = ray.get(self.parameter_server.get_parameters.remote())
            
            # Create checkpoint
            checkpoint = {
                'episode': self.global_episode,
                'parameters': current_params,
                'config': self.config,
                'metrics': [m.__dict__ for m in self.training_metrics[-100:]],  # Last 100 metrics
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Save checkpoint
            import os
            import json
            os.makedirs(self.output_dir, exist_ok=True)
            checkpoint_path = os.path.join(self.output_dir, f"checkpoint_episode_{self.global_episode}.json")
            
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=2, default=str)
            
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            
        except Exception as e:
            logger.error(f"Checkpoint saving failed: {e}")
    
    def _log_progress(self):
        """Log training progress"""
        if not self.training_metrics:
            return
        
        # Calculate recent metrics
        recent_metrics = self.training_metrics[-10:]  # Last 10 episodes
        avg_reward = np.mean([m.episode_reward for m in recent_metrics])
        avg_length = np.mean([m.episode_length for m in recent_metrics])
        avg_loss = np.mean([m.training_loss for m in recent_metrics])
        
        logger.info("Training progress",
                   episode=self.global_episode,
                   avg_reward=avg_reward,
                   avg_length=avg_length,
                   avg_loss=avg_loss,
                   num_workers=len(self.workers))
    
    def _final_evaluation(self):
        """Perform final evaluation"""
        logger.info("Performing final evaluation...")
        self._evaluate_model()
    
    def _save_final_model(self):
        """Save final trained model"""
        try:
            # Get final parameters
            final_params = ray.get(self.parameter_server.get_parameters.remote())
            
            # Create final model
            final_model = {
                'parameters': final_params,
                'config': self.config,
                'total_episodes': self.global_episode,
                'final_metrics': [m.__dict__ for m in self.training_metrics[-50:]],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Save final model
            import os
            import json
            final_model_path = os.path.join(self.output_dir, "final_model.json")
            
            with open(final_model_path, 'w') as f:
                json.dump(final_model, f, indent=2, default=str)
            
            logger.info(f"Final model saved: {final_model_path}")
            
        except Exception as e:
            logger.error(f"Final model saving failed: {e}")
    
    def _cleanup_workers(self):
        """Cleanup workers and resources"""
        try:
            # Stop all workers
            stop_futures = []
            for worker in self.workers:
                future = worker.stop.remote()
                stop_futures.append(future)
            
            # Wait for workers to stop
            ray.get(stop_futures, timeout=30)
            
            # Clear worker references
            self.workers.clear()
            
            logger.info("Workers cleaned up")
            
        except Exception as e:
            logger.error(f"Worker cleanup failed: {e}")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            'is_training': self.is_training,
            'global_episode': self.global_episode,
            'num_workers': len(self.workers),
            'total_metrics': len(self.training_metrics),
            'config': self.config.__dict__
        }
    
    def get_recent_metrics(self, num_episodes: int = 100) -> List[Dict[str, Any]]:
        """Get recent training metrics"""
        recent_metrics = self.training_metrics[-num_episodes:]
        return [m.__dict__ for m in recent_metrics]
    
    def shutdown(self):
        """Shutdown distributed trainer"""
        self.stop_training()
        
        # Shutdown Ray
        if ray.is_initialized():
            ray.shutdown()
        
        logger.info("DistributedRLTrainer shutdown complete")

# Factory function for easy distributed training
def create_distributed_trainer(
    num_workers: int = 4,
    num_gpus: int = 1,
    training_data_path: str = "data/training",
    output_dir: str = "outputs",
    **kwargs
) -> DistributedRLTrainer:
    """
    Create distributed trainer with default configuration
    
    Args:
        num_workers: Number of worker processes
        num_gpus: Number of GPUs to use
        training_data_path: Path to training data
        output_dir: Output directory
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured DistributedRLTrainer
    """
    config = DistributedConfig(
        num_workers=num_workers,
        num_gpus=num_gpus,
        **kwargs
    )
    
    return DistributedRLTrainer(
        config=config,
        training_data_path=training_data_path,
        output_dir=output_dir
    )
