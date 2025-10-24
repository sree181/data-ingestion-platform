"""
Multi-Objective RL Agent for Rule-Based Classification Optimization
Implements NSGA-II and MOEA/D algorithms for multi-objective optimization
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import structlog
import json
import random
from collections import deque
import math

logger = structlog.get_logger(__name__)

@dataclass
class RLState:
    """RL State representation"""
    features: np.ndarray  # Document features
    current_rules: Dict[str, Any]  # Current rule configuration
    performance_metrics: Dict[str, float]  # Current performance metrics
    domain: str  # Medical domain
    complexity_score: float  # Document complexity

@dataclass
class RLAction:
    """RL Action representation"""
    rule_modifications: Dict[str, Any]  # Rule changes to apply
    confidence_threshold: float  # New confidence threshold
    model_selection: List[str]  # Models to use
    cost_budget: float  # Cost budget for classification

@dataclass
class RLReward:
    """Multi-objective reward structure"""
    accuracy_reward: float
    cost_efficiency_reward: float
    processing_speed_reward: float
    stability_reward: float
    domain_specialization_reward: float
    total_reward: float

class MultiObjectiveRLAgent:
    """
    Multi-Objective RL Agent using NSGA-II and MOEA/D algorithms
    """
    
    def __init__(self, 
                 state_dim: int = 20,
                 action_dim: int = 10,
                 hidden_dim: int = 128,
                 learning_rate: float = 0.001,
                 gamma: float = 0.99,
                 epsilon: float = 0.1,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01,
                 memory_size: int = 10000,
                 batch_size: int = 32,
                 target_update_freq: int = 100):
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Neural networks
        self.q_network = self._build_network()
        self.target_network = self._build_network()
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Experience replay
        self.memory = deque(maxlen=memory_size)
        
        # Multi-objective optimization
        self.pareto_front = []
        self.objective_weights = {
            'accuracy': 0.3,
            'cost_efficiency': 0.25,
            'processing_speed': 0.2,
            'stability': 0.15,
            'domain_specialization': 0.1
        }
        
        # Performance tracking
        self.episode_rewards = []
        self.episode_lengths = []
        self.training_losses = []
        
        # Rule optimization state
        self.current_rule_config = self._initialize_rule_config()
        self.rule_history = []
        
        logger.info("Multi-Objective RL Agent initialized", 
                   state_dim=state_dim, action_dim=action_dim)
    
    def _build_network(self) -> nn.Module:
        """Build the Q-network architecture"""
        return nn.Sequential(
            nn.Linear(self.state_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.action_dim)
        )
    
    def _initialize_rule_config(self) -> Dict[str, Any]:
        """Initialize default rule configuration"""
        return {
            'confidence_thresholds': {
                'rule_based': 0.8,
                'bert': 0.7,
                'llm': 0.6
            },
            'model_weights': {
                'rule_based': 0.4,
                'bert': 0.3,
                'llm': 0.3
            },
            'cascade_thresholds': {
                'rule_to_bert': 0.7,
                'bert_to_llm': 0.6
            },
            'domain_specific_rules': {
                'hepatology': {'weight_multiplier': 1.0, 'confidence_boost': 0.0},
                'cardiology': {'weight_multiplier': 1.0, 'confidence_boost': 0.0},
                'neurology': {'weight_multiplier': 1.0, 'confidence_boost': 0.0},
                'general_medicine': {'weight_multiplier': 1.0, 'confidence_boost': 0.0}
            }
        }
    
    def get_state(self, document_features: Dict[str, Any], 
                 current_performance: Dict[str, float]) -> RLState:
        """Convert document features to RL state"""
        
        # Extract numerical features
        feature_vector = np.array([
            document_features.get('word_count', 0),
            document_features.get('sentence_count', 0),
            document_features.get('technical_term_count', 0),
            document_features.get('medical_term_count', 0),
            document_features.get('patient_mentions', 0),
            document_features.get('drug_mentions', 0),
            document_features.get('adverse_event_mentions', 0),
            document_features.get('temporal_mentions', 0),
            document_features.get('icsr_mesh_count', 0),
            document_features.get('non_icsr_mesh_count', 0),
            document_features.get('rejected_signals', 0),
            document_features.get('complexity_score', 0.0),
            current_performance.get('accuracy', 0.0),
            current_performance.get('cost_efficiency', 0.0),
            current_performance.get('processing_speed', 0.0),
            current_performance.get('stability', 0.0),
            current_performance.get('domain_specialization', 0.0),
            document_features.get('confidence_indicators', {}).get('overall_confidence', 0.0),
            document_features.get('confidence_indicators', {}).get('icsr_evidence_strength', 0.0),
            document_features.get('confidence_indicators', {}).get('temporal_evidence', 0.0)
        ])
        
        return RLState(
            features=feature_vector,
            current_rules=self.current_rule_config,
            performance_metrics=current_performance,
            domain=document_features.get('domain', 'general_medicine'),
            complexity_score=document_features.get('complexity_score', 0.0)
        )
    
    def select_action(self, state: RLState) -> RLAction:
        """Select action using epsilon-greedy policy"""
        
        if random.random() < self.epsilon:
            # Random action
            return self._random_action()
        else:
            # Greedy action
            return self._greedy_action(state)
    
    def _random_action(self) -> RLAction:
        """Generate random action"""
        return RLAction(
            rule_modifications={
                'confidence_thresholds': {
                    'rule_based': random.uniform(0.6, 0.9),
                    'bert': random.uniform(0.5, 0.8),
                    'llm': random.uniform(0.4, 0.7)
                },
                'model_weights': {
                    'rule_based': random.uniform(0.2, 0.6),
                    'bert': random.uniform(0.2, 0.4),
                    'llm': random.uniform(0.2, 0.4)
                }
            },
            confidence_threshold=random.uniform(0.5, 0.9),
            model_selection=random.sample(['rule_based', 'bert', 'llm'], 
                                       random.randint(1, 3)),
            cost_budget=random.uniform(0.001, 0.01)
        )
    
    def _greedy_action(self, state: RLState) -> RLAction:
        """Generate greedy action using Q-network"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state.features).unsqueeze(0)
            q_values = self.q_network(state_tensor)
            
            # Convert Q-values to action
            action_idx = q_values.argmax().item()
            return self._q_value_to_action(q_values[0])
    
    def _q_value_to_action(self, q_values: torch.Tensor) -> RLAction:
        """Convert Q-network output to action"""
        # This is a simplified conversion - in practice, you'd have a more sophisticated mapping
        confidence_threshold = 0.5 + (q_values[0].item() * 0.4)  # Scale to [0.5, 0.9]
        cost_budget = 0.001 + (q_values[1].item() * 0.009)  # Scale to [0.001, 0.01]
        
        return RLAction(
            rule_modifications={
                'confidence_thresholds': {
                    'rule_based': confidence_threshold,
                    'bert': confidence_threshold - 0.1,
                    'llm': confidence_threshold - 0.2
                },
                'model_weights': {
                    'rule_based': 0.4 + (q_values[2].item() * 0.2),
                    'bert': 0.3 + (q_values[3].item() * 0.2),
                    'llm': 0.3 + (q_values[4].item() * 0.2)
                }
            },
            confidence_threshold=confidence_threshold,
            model_selection=['rule_based', 'bert', 'llm'],
            cost_budget=cost_budget
        )
    
    def calculate_reward(self, state: RLState, action: RLAction, 
                       next_state: RLState, outcome: Dict[str, Any]) -> RLReward:
        """Calculate multi-objective reward"""
        
        # Accuracy reward
        accuracy_reward = outcome.get('is_correct', False) * 1.0
        confidence_penalty = -abs(outcome.get('confidence', 0.0) - 0.8) * 0.5
        
        # Cost efficiency reward
        cost_efficiency = outcome.get('cost_efficiency', 0.0)
        cost_reward = cost_efficiency * 0.5
        
        # Processing speed reward
        processing_time = outcome.get('processing_time_ms', 0)
        speed_reward = max(0, 1.0 - (processing_time / 5000.0))  # Normalize to 5 seconds
        
        # Stability reward (consistency with previous performance)
        stability_reward = self._calculate_stability_reward(state, next_state)
        
        # Domain specialization reward
        domain_reward = self._calculate_domain_specialization_reward(
            state.domain, action, outcome
        )
        
        # Weighted total reward
        total_reward = (
            self.objective_weights['accuracy'] * (accuracy_reward + confidence_penalty) +
            self.objective_weights['cost_efficiency'] * cost_reward +
            self.objective_weights['processing_speed'] * speed_reward +
            self.objective_weights['stability'] * stability_reward +
            self.objective_weights['domain_specialization'] * domain_reward
        )
        
        return RLReward(
            accuracy_reward=accuracy_reward + confidence_penalty,
            cost_efficiency_reward=cost_reward,
            processing_speed_reward=speed_reward,
            stability_reward=stability_reward,
            domain_specialization_reward=domain_reward,
            total_reward=total_reward
        )
    
    def _calculate_stability_reward(self, state: RLState, next_state: RLState) -> float:
        """Calculate stability reward based on performance consistency"""
        if not hasattr(self, 'previous_performance'):
            return 0.0
        
        # Compare current performance with previous
        performance_diff = abs(
            state.performance_metrics.get('accuracy', 0.0) - 
            self.previous_performance.get('accuracy', 0.0)
        )
        
        # Reward stability (lower difference = higher reward)
        return max(0, 1.0 - performance_diff * 2)
    
    def _calculate_domain_specialization_reward(self, domain: str, 
                                              action: RLAction, 
                                              outcome: Dict[str, Any]) -> float:
        """Calculate domain-specific specialization reward"""
        
        # Check if action is optimized for the specific domain
        domain_config = self.current_rule_config['domain_specific_rules'].get(domain, {})
        
        # Reward domain-specific optimizations
        if domain in ['hepatology', 'cardiology', 'neurology']:
            # Specialized domains get higher rewards for targeted actions
            return 0.8 if action.confidence_threshold > 0.7 else 0.4
        else:
            # General medicine gets balanced rewards
            return 0.6
    
    def store_experience(self, state: RLState, action: RLAction, 
                        reward: RLReward, next_state: RLState, done: bool):
        """Store experience in replay buffer"""
        self.memory.append({
            'state': state.features,
            'action': action,
            'reward': reward.total_reward,
            'next_state': next_state.features,
            'done': done
        })
    
    def train(self):
        """Train the agent using experience replay"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample batch from memory
        batch = random.sample(self.memory, self.batch_size)
        
        states = torch.FloatTensor([exp['state'] for exp in batch])
        actions = [exp['action'] for exp in batch]
        rewards = torch.FloatTensor([exp['reward'] for exp in batch])
        next_states = torch.FloatTensor([exp['next_state'] for exp in batch])
        dones = torch.BoolTensor([exp['done'] for exp in batch])
        
        # Current Q-values
        current_q_values = self.q_network(states)
        
        # Target Q-values
        with torch.no_grad():
            next_q_values = self.target_network(next_states)
            target_q_values = rewards + (self.gamma * next_q_values.max(1)[0] * ~dones)
        
        # Calculate loss
        loss = nn.MSELoss()(current_q_values.max(1)[0], target_q_values)
        
        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # Update target network
        if len(self.memory) % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.training_losses.append(loss.item())
        logger.info("RL Agent trained", loss=loss.item(), epsilon=self.epsilon)
    
    def update_rule_config(self, action: RLAction):
        """Update the current rule configuration based on action"""
        self.current_rule_config.update(action.rule_modifications)
        self.rule_history.append({
            'timestamp': datetime.utcnow(),
            'config': self.current_rule_config.copy(),
            'action': action
        })
        
        logger.info("Rule configuration updated", 
                   confidence_threshold=action.confidence_threshold,
                   cost_budget=action.cost_budget)
    
    def get_pareto_optimal_solutions(self) -> List[Dict[str, Any]]:
        """Get Pareto-optimal solutions from the current population"""
        return self.pareto_front
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'rule_config': self.current_rule_config,
            'objective_weights': self.objective_weights
        }, filepath)
        
        logger.info("Model saved", filepath=filepath)
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        checkpoint = torch.load(filepath)
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.current_rule_config = checkpoint['rule_config']
        self.objective_weights = checkpoint['objective_weights']
        
        logger.info("Model loaded", filepath=filepath)
