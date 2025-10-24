"""
Adaptive Multi-Objective Reward Shaping (AMORS)
Novel algorithm for dynamic reward weight adjustment based on real-time performance feedback
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque
import structlog
from datetime import datetime
import json

logger = structlog.get_logger(__name__)

@dataclass
class PerformanceTargets:
    """Performance targets for each objective"""
    accuracy: float = 0.95
    cost_efficiency: float = 0.9
    processing_speed: float = 0.8
    stability: float = 0.85
    domain_specialization: float = 0.9

@dataclass
class AdaptationConfig:
    """Configuration for adaptive reward shaping"""
    adaptation_rate: float = 0.01
    history_window: int = 1000
    min_weight: float = 0.05
    max_weight: float = 0.5
    convergence_threshold: float = 0.01
    stability_period: int = 100

class AdaptiveMultiObjectiveRewardShaping:
    """
    Novel algorithm for adaptive multi-objective reward shaping
    Dynamically adjusts reward weights based on real-time performance feedback
    """
    
    def __init__(self, 
                 initial_weights: Optional[Dict[str, float]] = None,
                 performance_targets: Optional[PerformanceTargets] = None,
                 adaptation_config: Optional[AdaptationConfig] = None):
        
        # Initialize reward weights
        self.reward_weights = initial_weights or {
            'accuracy': 0.3,
            'cost_efficiency': 0.25,
            'processing_speed': 0.2,
            'stability': 0.15,
            'domain_specialization': 0.1
        }
        
        # Performance targets
        self.performance_targets = performance_targets or PerformanceTargets()
        
        # Adaptation configuration
        self.config = adaptation_config or AdaptationConfig()
        
        # Performance history
        self.performance_history = deque(maxlen=self.config.history_window)
        self.weight_history = deque(maxlen=self.config.history_window)
        
        # Adaptation state
        self.adaptation_count = 0
        self.last_adaptation = None
        self.convergence_achieved = False
        
        # Performance tracking
        self.performance_gaps = {}
        self.adaptation_effectiveness = {}
        
        logger.info("Adaptive Multi-Objective Reward Shaping initialized",
                   initial_weights=self.reward_weights,
                   adaptation_rate=self.config.adaptation_rate)
    
    def adapt_weights(self, current_performance: Dict[str, float]) -> Dict[str, float]:
        """
        Novel method: Dynamically adjust reward weights based on performance gaps
        
        Args:
            current_performance: Current performance metrics
            
        Returns:
            Updated reward weights
        """
        # Store current performance
        self.performance_history.append({
            'timestamp': datetime.utcnow(),
            'performance': current_performance.copy(),
            'weights': self.reward_weights.copy()
        })
        
        # Calculate performance gaps
        gaps = self._calculate_performance_gaps(current_performance)
        self.performance_gaps = gaps
        
        # Check if adaptation is needed
        if not self._should_adapt(gaps):
            return self.reward_weights
        
        # Perform adaptive weight adjustment
        new_weights = self._adaptive_weight_adjustment(gaps)
        
        # Validate and normalize weights
        new_weights = self._validate_and_normalize_weights(new_weights)
        
        # Update weights
        old_weights = self.reward_weights.copy()
        self.reward_weights = new_weights
        
        # Track adaptation
        self._track_adaptation(old_weights, new_weights, gaps)
        
        logger.info("Reward weights adapted",
                   old_weights=old_weights,
                   new_weights=new_weights,
                   gaps=gaps,
                   adaptation_count=self.adaptation_count)
        
        return self.reward_weights
    
    def _calculate_performance_gaps(self, current_performance: Dict[str, float]) -> Dict[str, float]:
        """Calculate performance gaps for each objective"""
        gaps = {}
        
        for objective, target in self.performance_targets.__dict__.items():
            current_value = current_performance.get(objective, 0.0)
            gap = target - current_value
            gaps[objective] = max(0.0, gap)  # Only consider positive gaps
        
        return gaps
    
    def _should_adapt(self, gaps: Dict[str, float]) -> bool:
        """Determine if weight adaptation is needed"""
        # Check if any gap exceeds threshold
        max_gap = max(gaps.values()) if gaps else 0.0
        if max_gap < self.config.convergence_threshold:
            return False
        
        # Check stability period
        if len(self.performance_history) < self.config.stability_period:
            return True
        
        # Check if performance has been stable
        recent_performance = list(self.performance_history)[-self.config.stability_period:]
        performance_variance = self._calculate_performance_variance(recent_performance)
        
        return performance_variance > self.config.convergence_threshold
    
    def _adaptive_weight_adjustment(self, gaps: Dict[str, float]) -> Dict[str, float]:
        """
        Novel adaptive weight adjustment algorithm
        """
        new_weights = self.reward_weights.copy()
        
        # Calculate total gap
        total_gap = sum(gaps.values())
        if total_gap == 0:
            return new_weights
        
        # Adaptive adjustment based on gap magnitude and direction
        for objective, gap in gaps.items():
            if gap > 0:
                # Calculate adjustment magnitude
                gap_ratio = gap / total_gap
                adjustment = self.config.adaptation_rate * gap_ratio
                
                # Apply exponential adjustment for large gaps
                if gap > 0.1:  # Large gap
                    adjustment *= 2.0
                elif gap > 0.05:  # Medium gap
                    adjustment *= 1.5
                
                # Apply adjustment
                new_weights[objective] += adjustment
        
        return new_weights
    
    def _validate_and_normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Validate and normalize weights to ensure they sum to 1.0"""
        # Apply min/max constraints
        for objective in weights:
            weights[objective] = max(self.config.min_weight, 
                                   min(self.config.max_weight, weights[objective]))
        
        # Normalize to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            for objective in weights:
                weights[objective] /= total_weight
        
        return weights
    
    def _track_adaptation(self, old_weights: Dict[str, float], 
                         new_weights: Dict[str, float], 
                         gaps: Dict[str, float]):
        """Track adaptation effectiveness"""
        self.adaptation_count += 1
        self.last_adaptation = datetime.utcnow()
        
        # Calculate weight changes
        weight_changes = {}
        for objective in old_weights:
            weight_changes[objective] = new_weights[objective] - old_weights[objective]
        
        # Store adaptation record
        self.weight_history.append({
            'timestamp': datetime.utcnow(),
            'old_weights': old_weights,
            'new_weights': new_weights,
            'weight_changes': weight_changes,
            'gaps': gaps,
            'adaptation_count': self.adaptation_count
        })
        
        # Check for convergence
        self._check_convergence()
    
    def _check_convergence(self):
        """Check if the system has converged"""
        if len(self.weight_history) < self.config.stability_period:
            return
        
        # Check if weights have been stable
        recent_weights = list(self.weight_history)[-self.config.stability_period:]
        weight_variance = self._calculate_weight_variance(recent_weights)
        
        if weight_variance < self.config.convergence_threshold:
            self.convergence_achieved = True
            logger.info("Adaptive reward shaping converged",
                       convergence_threshold=self.config.convergence_threshold,
                       weight_variance=weight_variance)
    
    def _calculate_performance_variance(self, performance_history: List[Dict]) -> float:
        """Calculate variance in performance metrics"""
        if len(performance_history) < 2:
            return 0.0
        
        # Extract performance values
        performance_values = []
        for record in performance_history:
            perf = record['performance']
            performance_values.append(list(perf.values()))
        
        # Calculate variance across all objectives
        performance_array = np.array(performance_values)
        variance = np.var(performance_array, axis=0)
        
        return np.mean(variance)
    
    def _calculate_weight_variance(self, weight_history: List[Dict]) -> float:
        """Calculate variance in weight changes"""
        if len(weight_history) < 2:
            return 0.0
        
        # Extract weight values
        weight_values = []
        for record in weight_history:
            weights = record['new_weights']
            weight_values.append(list(weights.values()))
        
        # Calculate variance across all weights
        weight_array = np.array(weight_values)
        variance = np.var(weight_array, axis=0)
        
        return np.mean(variance)
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive adaptation statistics"""
        if not self.performance_history:
            return {}
        
        # Calculate performance trends
        recent_performance = list(self.performance_history)[-100:] if len(self.performance_history) > 100 else list(self.performance_history)
        
        # Calculate average performance
        avg_performance = {}
        for objective in self.performance_targets.__dict__:
            values = [record['performance'].get(objective, 0.0) for record in recent_performance]
            avg_performance[objective] = np.mean(values) if values else 0.0
        
        # Calculate weight evolution
        weight_evolution = {}
        for objective in self.reward_weights:
            values = [record['weights'].get(objective, 0.0) for record in recent_performance]
            weight_evolution[objective] = {
                'current': self.reward_weights[objective],
                'average': np.mean(values) if values else 0.0,
                'variance': np.var(values) if values else 0.0
            }
        
        return {
            'adaptation_count': self.adaptation_count,
            'convergence_achieved': self.convergence_achieved,
            'current_weights': self.reward_weights,
            'average_performance': avg_performance,
            'weight_evolution': weight_evolution,
            'performance_gaps': self.performance_gaps,
            'history_length': len(self.performance_history)
        }
    
    def save_adaptation_state(self, filepath: str):
        """Save adaptation state to file"""
        state = {
            'reward_weights': self.reward_weights,
            'performance_targets': self.performance_targets.__dict__,
            'adaptation_config': self.config.__dict__,
            'adaptation_count': self.adaptation_count,
            'convergence_achieved': self.convergence_achieved,
            'performance_history': list(self.performance_history),
            'weight_history': list(self.weight_history),
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info("Adaptation state saved", filepath=filepath)
    
    def load_adaptation_state(self, filepath: str):
        """Load adaptation state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.reward_weights = state['reward_weights']
        self.adaptation_count = state['adaptation_count']
        self.convergence_achieved = state['convergence_achieved']
        
        # Restore history
        self.performance_history = deque(state['performance_history'], maxlen=self.config.history_window)
        self.weight_history = deque(state['weight_history'], maxlen=self.config.history_window)
        
        logger.info("Adaptation state loaded", filepath=filepath)
    
    def reset_adaptation(self):
        """Reset adaptation state"""
        self.adaptation_count = 0
        self.convergence_achieved = False
        self.performance_history.clear()
        self.weight_history.clear()
        self.performance_gaps = {}
        self.adaptation_effectiveness = {}
        
        logger.info("Adaptation state reset")
    
    def get_recommended_weights(self, performance_context: Dict[str, Any]) -> Dict[str, float]:
        """
        Novel method: Get recommended weights based on performance context
        """
        # Analyze performance context
        domain = performance_context.get('domain', 'general_medicine')
        complexity = performance_context.get('complexity_score', 0.5)
        urgency = performance_context.get('urgency', 'normal')
        
        # Adjust weights based on context
        context_weights = self.reward_weights.copy()
        
        # Domain-specific adjustments
        if domain in ['hepatology', 'cardiology', 'neurology']:
            context_weights['domain_specialization'] *= 1.5
            context_weights['accuracy'] *= 1.2
        
        # Complexity-based adjustments
        if complexity > 0.7:  # High complexity
            context_weights['processing_speed'] *= 0.8
            context_weights['accuracy'] *= 1.3
        elif complexity < 0.3:  # Low complexity
            context_weights['cost_efficiency'] *= 1.2
            context_weights['processing_speed'] *= 1.2
        
        # Urgency-based adjustments
        if urgency == 'high':
            context_weights['processing_speed'] *= 1.5
            context_weights['stability'] *= 0.8
        elif urgency == 'low':
            context_weights['cost_efficiency'] *= 1.3
            context_weights['stability'] *= 1.2
        
        # Normalize weights
        total_weight = sum(context_weights.values())
        for objective in context_weights:
            context_weights[objective] /= total_weight
        
        return context_weights
