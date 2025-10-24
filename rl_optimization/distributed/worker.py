"""
RL Worker for Distributed Training
Individual training worker that runs episodes independently
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
import json
import os
from pathlib import Path

from ..rl_training.rl_agent import MultiObjectiveRLAgent, RLState, RLAction, RLReward
from ..data.dataset import PubMedStreamingDataset, TrainingSample
from ..data.data_loader import RLDataLoader, BatchConfig

logger = structlog.get_logger(__name__)

@dataclass
class WorkerConfig:
    """Configuration for RL worker"""
    state_dim: int = 20
    action_dim: int = 10
    hidden_dim: int = 128
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon: float = 0.1
    epsilon_min: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 32
    memory_size: int = 10000
    target_update_frequency: int = 100

@dataclass
class EpisodeResult:
    """Result of a single episode"""
    worker_id: int
    episode: int
    reward: float
    length: int
    loss: float
    epsilon: float
    timestamp: datetime
    metadata: Dict[str, Any]

@ray.remote
class RLWorker:
    """
    Individual training worker
    - Run episodes independently
    - Send experiences to shared buffer
    - Pull latest model weights
    - Report metrics to coordinator
    """
    
    def __init__(
        self,
        worker_id: int,
        config: WorkerConfig,
        training_data_path: str,
        parameter_server
    ):
        """
        Initialize RL worker
        
        Args:
            worker_id: Unique worker identifier
            config: Worker configuration
            training_data_path: Path to training data
            parameter_server: Ray remote parameter server
        """
        self.worker_id = worker_id
        self.config = config
        self.training_data_path = training_data_path
        self.parameter_server = parameter_server
        
        # Initialize RL agent
        self.agent = MultiObjectiveRLAgent(
            state_dim=config.state_dim,
            action_dim=config.action_dim,
            hidden_dim=config.hidden_dim,
            learning_rate=config.learning_rate,
            gamma=config.gamma,
            epsilon=config.epsilon,
            epsilon_min=config.epsilon_min,
            epsilon_decay=config.epsilon_decay,
            batch_size=config.batch_size,
            memory_size=config.memory_size
        )
        
        # Initialize data loader
        self.data_loader = self._create_data_loader()
        
        # Worker state
        self.is_running = False
        self.episode_count = 0
        self.total_reward = 0.0
        self.total_loss = 0.0
        
        logger.info(f"RLWorker {worker_id} initialized")
    
    def _create_data_loader(self) -> RLDataLoader:
        """Create data loader for this worker"""
        # Create dataset
        dataset = PubMedStreamingDataset(
            data_path=self.training_data_path,
            cache_size=1000,  # Smaller cache per worker
            num_workers=1,
            shuffle=True
        )
        
        # Create batch config
        batch_config = BatchConfig(
            batch_size=self.config.batch_size,
            dynamic_batching=True
        )
        
        # Create data loader
        return RLDataLoader(
            dataset=dataset,
            batch_config=batch_config,
            num_workers=1
        )
    
    def run_episode(self, episode: int) -> Dict[str, Any]:
        """
        Run a single training episode
        
        Args:
            episode: Episode number
            
        Returns:
            Episode result dictionary
        """
        start_time = time.time()
        episode_reward = 0.0
        episode_length = 0
        episode_loss = 0.0
        
        try:
            # Get current parameters from parameter server
            current_params = ray.get(self.parameter_server.get_parameters.remote())
            if current_params:
                self.agent.load_parameters(current_params)
            
            # Run episode
            for step in range(100):  # Max steps per episode
                # Get training sample
                try:
                    batch = next(iter(self.data_loader))
                    features = batch['features']
                    outcomes = batch['outcomes']
                    
                    # Process batch
                    for i in range(len(features)):
                        # Create state
                        state = self._create_state(features[i], outcomes[i])
                        
                        # Select action
                        action = self.agent.select_action(state)
                        
                        # Execute action (simplified)
                        reward = self._calculate_reward(state, action, outcomes[i])
                        next_state = state  # Simplified
                        
                        # Store experience
                        self.agent.memory.append((state, action, reward, next_state))
                        
                        # Train if enough experiences
                        if len(self.agent.memory) > self.config.batch_size:
                            loss = self.agent.train_step()
                            episode_loss += loss
                        
                        episode_reward += reward
                        episode_length += 1
                        
                        # Check episode termination
                        if self._should_terminate_episode(state, action, step):
                            break
                
                except StopIteration:
                    # No more data
                    break
                except Exception as e:
                    logger.warning(f"Worker {self.worker_id} step error: {e}")
                    continue
            
            # Update agent parameters
            self.agent.decay_epsilon()
            
            # Update worker state
            self.episode_count += 1
            self.total_reward += episode_reward
            self.total_loss += episode_loss
            
            # Create result
            result = {
                'worker_id': self.worker_id,
                'episode': episode,
                'reward': episode_reward,
                'length': episode_length,
                'loss': episode_loss / max(episode_length, 1),
                'epsilon': self.agent.epsilon,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    'total_episodes': self.episode_count,
                    'total_reward': self.total_reward,
                    'avg_reward': self.total_reward / max(self.episode_count, 1),
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            }
            
            logger.info(f"Worker {self.worker_id} episode {episode} completed",
                       reward=episode_reward,
                       length=episode_length,
                       loss=episode_loss)
            
            return result
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} episode {episode} failed: {e}")
            return {
                'worker_id': self.worker_id,
                'episode': episode,
                'reward': 0.0,
                'length': 0,
                'loss': 0.0,
                'epsilon': self.agent.epsilon,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _create_state(self, features: torch.Tensor, outcomes: torch.Tensor) -> RLState:
        """Create RL state from features and outcomes"""
        # Convert tensors to numpy
        features_np = features.detach().cpu().numpy()
        outcomes_np = outcomes.detach().cpu().numpy()
        
        # Create state
        state = RLState(
            features=features_np,
            current_rules={},  # Simplified
            performance_metrics={},  # Simplified
            domain="general_medicine",  # Simplified
            complexity_score=0.5  # Simplified
        )
        
        return state
    
    def _calculate_reward(
        self, 
        state: RLState, 
        action: RLAction, 
        outcome: torch.Tensor
    ) -> float:
        """Calculate reward for state-action-outcome"""
        # Simplified reward calculation
        # In practice, this would use the actual classification outcome
        
        # Extract outcome values
        outcome_np = outcome.detach().cpu().numpy()
        confidence = outcome_np[0] if len(outcome_np) > 0 else 0.0
        is_correct = outcome_np[1] if len(outcome_np) > 1 else 0.0
        cost_efficiency = outcome_np[2] if len(outcome_np) > 2 else 0.0
        
        # Calculate reward components
        accuracy_reward = is_correct * 1.0
        confidence_reward = confidence * 0.5
        efficiency_reward = cost_efficiency * 0.3
        
        total_reward = accuracy_reward + confidence_reward + efficiency_reward
        
        return total_reward
    
    def _should_terminate_episode(
        self, 
        state: RLState, 
        action: RLAction, 
        step: int
    ) -> bool:
        """Determine if episode should terminate"""
        # Simple termination conditions
        if step >= 50:  # Max steps
            return True
        
        # Add other termination conditions as needed
        return False
    
    def update_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Update worker parameters
        
        Args:
            parameters: New parameters from parameter server
            
        Returns:
            Success status
        """
        try:
            self.agent.load_parameters(parameters)
            logger.info(f"Worker {self.worker_id} parameters updated")
            return True
        except Exception as e:
            logger.error(f"Worker {self.worker_id} parameter update failed: {e}")
            return False
    
    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate worker performance
        
        Returns:
            Evaluation metrics
        """
        try:
            # Run evaluation episode
            eval_reward = 0.0
            eval_length = 0
            
            # Simple evaluation (in practice, use separate evaluation data)
            for _ in range(10):  # 10 evaluation steps
                try:
                    batch = next(iter(self.data_loader))
                    features = batch['features']
                    outcomes = batch['outcomes']
                    
                    for i in range(len(features)):
                        state = self._create_state(features[i], outcomes[i])
                        action = self.agent.select_action(state)
                        reward = self._calculate_reward(state, action, outcomes[i])
                        
                        eval_reward += reward
                        eval_length += 1
                        
                        if eval_length >= 10:
                            break
                    
                    if eval_length >= 10:
                        break
                        
                except StopIteration:
                    break
                except Exception as e:
                    logger.warning(f"Worker {self.worker_id} evaluation error: {e}")
                    continue
            
            # Calculate metrics
            avg_reward = eval_reward / max(eval_length, 1)
            
            # Simplified metrics (in practice, calculate actual performance)
            metrics = {
                'worker_id': self.worker_id,
                'accuracy': min(avg_reward, 1.0),
                'cost_efficiency': min(avg_reward * 0.8, 1.0),
                'processing_speed': min(avg_reward * 0.9, 1.0),
                'stability': min(avg_reward * 0.7, 1.0),
                'domain_specialization': min(avg_reward * 0.6, 1.0),
                'avg_reward': avg_reward,
                'episode_length': eval_length,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Worker {self.worker_id} evaluation completed", **metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} evaluation failed: {e}")
            return {
                'worker_id': self.worker_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get current worker status"""
        return {
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'episode_count': self.episode_count,
            'total_reward': self.total_reward,
            'avg_reward': self.total_reward / max(self.episode_count, 1),
            'epsilon': self.agent.epsilon,
            'memory_size': len(self.agent.memory),
            'config': self.config.__dict__
        }
    
    def stop(self) -> bool:
        """Stop the worker"""
        try:
            self.is_running = False
            logger.info(f"Worker {self.worker_id} stopped")
            return True
        except Exception as e:
            logger.error(f"Worker {self.worker_id} stop failed: {e}")
            return False
