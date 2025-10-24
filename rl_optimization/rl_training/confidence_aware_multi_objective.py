"""
Confidence-Aware Multi-Objective Optimization (CAMO)
Novel algorithm for confidence-based objective prioritization
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import structlog
from datetime import datetime
import json
from collections import defaultdict, deque

logger = structlog.get_logger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for optimization"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"

class OptimizationStrategy(Enum):
    """Optimization strategies based on confidence"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    EXPLORATORY = "exploratory"

@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for different levels"""
    high: float = 0.8
    medium: float = 0.6
    low: float = 0.4
    very_low: float = 0.2

@dataclass
class ObjectivePriorities:
    """Objective priorities for different confidence levels"""
    high: List[str] = None
    medium: List[str] = None
    low: List[str] = None
    very_low: List[str] = None
    
    def __post_init__(self):
        if self.high is None:
            self.high = ['accuracy', 'stability']
        if self.medium is None:
            self.medium = ['accuracy', 'cost_efficiency', 'processing_speed']
        if self.low is None:
            self.low = ['cost_efficiency', 'processing_speed', 'domain_specialization']
        if self.very_low is None:
            self.very_low = ['processing_speed', 'domain_specialization']

@dataclass
class OptimizationConfig:
    """Configuration for confidence-aware optimization"""
    confidence_thresholds: ConfidenceThresholds = None
    objective_priorities: ObjectivePriorities = None
    adaptation_rate: float = 0.1
    exploration_rate: float = 0.2
    stability_weight: float = 0.3
    performance_weight: float = 0.7
    
    def __post_init__(self):
        if self.confidence_thresholds is None:
            self.confidence_thresholds = ConfidenceThresholds()
        if self.objective_priorities is None:
            self.objective_priorities = ObjectivePriorities()

class ConfidenceAwareMultiObjective:
    """
    Novel algorithm for confidence-aware multi-objective optimization
    Adjusts optimization strategy based on confidence level
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        
        # Confidence-based strategies
        self.strategies = {
            ConfidenceLevel.HIGH: OptimizationStrategy.CONSERVATIVE,
            ConfidenceLevel.MEDIUM: OptimizationStrategy.BALANCED,
            ConfidenceLevel.LOW: OptimizationStrategy.AGGRESSIVE,
            ConfidenceLevel.VERY_LOW: OptimizationStrategy.EXPLORATORY
        }
        
        # Performance tracking
        self.performance_history = defaultdict(list)
        self.confidence_history = deque(maxlen=1000)
        self.optimization_history = deque(maxlen=1000)
        
        # Confidence estimation
        self.confidence_estimator = ConfidenceEstimator()
        
        # Multi-objective optimizer
        self.multi_objective_optimizer = MultiObjectiveOptimizer()
        
        logger.info("Confidence-Aware Multi-Objective Optimization initialized",
                   confidence_thresholds=self.config.confidence_thresholds.__dict__,
                   strategies={level.value: strategy.value for level, strategy in self.strategies.items()})
    
    def optimize_with_confidence(self, state: Dict[str, Any], 
                                confidence: float,
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Novel method: Optimize based on confidence level
        
        Args:
            state: Current system state
            confidence: Confidence level (0.0-1.0)
            performance_context: Performance context information
            
        Returns:
            Optimized configuration
        """
        # Determine confidence level
        confidence_level = self._determine_confidence_level(confidence)
        
        # Get optimization strategy
        strategy = self.strategies[confidence_level]
        
        # Calculate objective priorities
        priorities = self._calculate_objective_priorities(confidence_level, context)
        
        # Perform optimization
        optimized_config = self._perform_optimization(state, strategy, priorities, confidence)
        
        # Track optimization
        self._track_optimization(state, optimized_config, confidence, confidence_level, strategy)
        
        logger.info("Optimization completed",
                   confidence=confidence,
                   confidence_level=confidence_level.value,
                   strategy=strategy.value,
                   priorities=priorities)
        
        return optimized_config
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level based on confidence value"""
        if confidence >= self.config.confidence_thresholds.high:
            return ConfidenceLevel.HIGH
        elif confidence >= self.config.confidence_thresholds.medium:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.config.confidence_thresholds.low:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _calculate_objective_priorities(self, confidence_level: ConfidenceLevel, 
                                      context: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate objective priorities based on confidence level"""
        base_priorities = getattr(self.config.objective_priorities, confidence_level.value)
        
        # Initialize priority weights
        priority_weights = {objective: 0.0 for objective in ['accuracy', 'cost_efficiency', 'processing_speed', 'stability', 'domain_specialization']}
        
        # Assign weights based on priority order
        for i, objective in enumerate(base_priorities):
            if objective in priority_weights:
                priority_weights[objective] = 1.0 / (i + 1)  # Decreasing weights
        
        # Adjust based on context
        if context:
            priority_weights = self._adjust_priorities_for_context(priority_weights, context)
        
        # Normalize weights
        total_weight = sum(priority_weights.values())
        if total_weight > 0:
            for objective in priority_weights:
                priority_weights[objective] /= total_weight
        
        return priority_weights
    
    def _adjust_priorities_for_context(self, priorities: Dict[str, float], 
                                     context: Dict[str, Any]) -> Dict[str, float]:
        """Adjust priorities based on performance context"""
        adjusted_priorities = priorities.copy()
        
        # Domain-specific adjustments
        domain = context.get('domain', 'general_medicine')
        if domain in ['hepatology', 'cardiology', 'neurology']:
            adjusted_priorities['domain_specialization'] *= 1.5
            adjusted_priorities['accuracy'] *= 1.2
        
        # Complexity-based adjustments
        complexity = context.get('complexity_score', 0.5)
        if complexity > 0.7:  # High complexity
            adjusted_priorities['accuracy'] *= 1.3
            adjusted_priorities['processing_speed'] *= 0.8
        elif complexity < 0.3:  # Low complexity
            adjusted_priorities['cost_efficiency'] *= 1.2
            adjusted_priorities['processing_speed'] *= 1.2
        
        # Urgency-based adjustments
        urgency = context.get('urgency', 'normal')
        if urgency == 'high':
            adjusted_priorities['processing_speed'] *= 1.5
            adjusted_priorities['stability'] *= 0.8
        elif urgency == 'low':
            adjusted_priorities['cost_efficiency'] *= 1.3
            adjusted_priorities['stability'] *= 1.2
        
        return adjusted_priorities
    
    def _perform_optimization(self, state: Dict[str, Any], 
                            strategy: OptimizationStrategy,
                            priorities: Dict[str, float],
                            confidence: float) -> Dict[str, Any]:
        """Perform optimization based on strategy and priorities"""
        
        if strategy == OptimizationStrategy.CONSERVATIVE:
            return self._conservative_optimization(state, priorities, confidence)
        elif strategy == OptimizationStrategy.BALANCED:
            return self._balanced_optimization(state, priorities, confidence)
        elif strategy == OptimizationStrategy.AGGRESSIVE:
            return self._aggressive_optimization(state, priorities, confidence)
        elif strategy == OptimizationStrategy.EXPLORATORY:
            return self._exploratory_optimization(state, priorities, confidence)
        else:
            return self._default_optimization(state, priorities, confidence)
    
    def _conservative_optimization(self, state: Dict[str, Any], 
                                  priorities: Dict[str, float],
                                  confidence: float) -> Dict[str, Any]:
        """Conservative optimization strategy for high confidence"""
        # Focus on stability and accuracy
        optimized_config = state.copy()
        
        # Increase confidence thresholds
        if 'confidence_thresholds' in optimized_config:
            for threshold in optimized_config['confidence_thresholds']:
                optimized_config['confidence_thresholds'][threshold] = min(0.9, 
                    optimized_config['confidence_thresholds'][threshold] + 0.05)
        
        # Reduce exploration
        if 'epsilon' in optimized_config:
            optimized_config['epsilon'] = max(0.01, optimized_config['epsilon'] * 0.8)
        
        # Increase stability weight
        optimized_config['stability_weight'] = self.config.stability_weight + 0.2
        
        return optimized_config
    
    def _balanced_optimization(self, state: Dict[str, Any], 
                             priorities: Dict[str, float],
                             confidence: float) -> Dict[str, Any]:
        """Balanced optimization strategy for medium confidence"""
        # Balance all objectives
        optimized_config = state.copy()
        
        # Moderate confidence thresholds
        if 'confidence_thresholds' in optimized_config:
            for threshold in optimized_config['confidence_thresholds']:
                optimized_config['confidence_thresholds'][threshold] = max(0.5, 
                    min(0.8, optimized_config['confidence_thresholds'][threshold]))
        
        # Balanced exploration
        if 'epsilon' in optimized_config:
            optimized_config['epsilon'] = max(0.05, min(0.2, optimized_config['epsilon']))
        
        # Balanced weights
        optimized_config['stability_weight'] = self.config.stability_weight
        optimized_config['performance_weight'] = self.config.performance_weight
        
        return optimized_config
    
    def _aggressive_optimization(self, state: Dict[str, Any], 
                               priorities: Dict[str, float],
                               confidence: float) -> Dict[str, Any]:
        """Aggressive optimization strategy for low confidence"""
        # Focus on performance improvement
        optimized_config = state.copy()
        
        # Lower confidence thresholds
        if 'confidence_thresholds' in optimized_config:
            for threshold in optimized_config['confidence_thresholds']:
                optimized_config['confidence_thresholds'][threshold] = max(0.3, 
                    optimized_config['confidence_thresholds'][threshold] - 0.1)
        
        # Increase exploration
        if 'epsilon' in optimized_config:
            optimized_config['epsilon'] = min(0.3, optimized_config['epsilon'] * 1.5)
        
        # Focus on performance
        optimized_config['stability_weight'] = self.config.stability_weight - 0.1
        optimized_config['performance_weight'] = self.config.performance_weight + 0.1
        
        return optimized_config
    
    def _exploratory_optimization(self, state: Dict[str, Any], 
                                priorities: Dict[str, float],
                                confidence: float) -> Dict[str, Any]:
        """Exploratory optimization strategy for very low confidence"""
        # Maximum exploration
        optimized_config = state.copy()
        
        # Very low confidence thresholds
        if 'confidence_thresholds' in optimized_config:
            for threshold in optimized_config['confidence_thresholds']:
                optimized_config['confidence_thresholds'][threshold] = max(0.2, 
                    optimized_config['confidence_thresholds'][threshold] - 0.2)
        
        # Maximum exploration
        if 'epsilon' in optimized_config:
            optimized_config['epsilon'] = min(0.5, optimized_config['epsilon'] * 2.0)
        
        # Focus on exploration
        optimized_config['stability_weight'] = 0.1
        optimized_config['performance_weight'] = 0.9
        
        return optimized_config
    
    def _default_optimization(self, state: Dict[str, Any], 
                            priorities: Dict[str, float],
                            confidence: float) -> Dict[str, Any]:
        """Default optimization strategy"""
        return state.copy()
    
    def _track_optimization(self, state: Dict[str, Any], 
                           optimized_config: Dict[str, Any],
                           confidence: float,
                           confidence_level: ConfidenceLevel,
                           strategy: OptimizationStrategy):
        """Track optimization history"""
        optimization_record = {
            'timestamp': datetime.utcnow(),
            'state': state,
            'optimized_config': optimized_config,
            'confidence': confidence,
            'confidence_level': confidence_level.value,
            'strategy': strategy.value,
            'changes': self._calculate_config_changes(state, optimized_config)
        }
        
        self.optimization_history.append(optimization_record)
        self.confidence_history.append(confidence)
    
    def _calculate_config_changes(self, original: Dict[str, Any], 
                                 optimized: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between original and optimized configurations"""
        changes = {}
        
        for key in optimized:
            if key in original:
                if isinstance(original[key], (int, float)) and isinstance(optimized[key], (int, float)):
                    changes[key] = optimized[key] - original[key]
                elif original[key] != optimized[key]:
                    changes[key] = f"{original[key]} -> {optimized[key]}"
            else:
                changes[key] = f"Added: {optimized[key]}"
        
        return changes
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        if not self.optimization_history:
            return {}
        
        # Calculate confidence statistics
        confidence_values = list(self.confidence_history)
        confidence_stats = {
            'mean': np.mean(confidence_values),
            'std': np.std(confidence_values),
            'min': np.min(confidence_values),
            'max': np.max(confidence_values)
        }
        
        # Calculate strategy usage
        strategy_usage = defaultdict(int)
        for record in self.optimization_history:
            strategy_usage[record['strategy']] += 1
        
        # Calculate confidence level distribution
        confidence_level_dist = defaultdict(int)
        for record in self.optimization_history:
            confidence_level_dist[record['confidence_level']] += 1
        
        return {
            'total_optimizations': len(self.optimization_history),
            'confidence_statistics': confidence_stats,
            'strategy_usage': dict(strategy_usage),
            'confidence_level_distribution': dict(confidence_level_dist),
            'recent_optimizations': list(self.optimization_history)[-10:]  # Last 10 optimizations
        }
    
    def save_optimization_state(self, filepath: str):
        """Save optimization state to file"""
        state = {
            'config': self.config.__dict__,
            'strategies': {level.value: strategy.value for level, strategy in self.strategies.items()},
            'optimization_history': list(self.optimization_history),
            'confidence_history': list(self.confidence_history),
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info("Optimization state saved", filepath=filepath)
    
    def load_optimization_state(self, filepath: str):
        """Load optimization state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore state
        self.optimization_history = deque(state['optimization_history'], maxlen=1000)
        self.confidence_history = deque(state['confidence_history'], maxlen=1000)
        
        logger.info("Optimization state loaded", filepath=filepath)

class ConfidenceEstimator:
    """Confidence estimation component"""
    
    def __init__(self):
        self.confidence_model = self._build_confidence_model()
    
    def _build_confidence_model(self) -> nn.Module:
        """Build confidence estimation model"""
        return nn.Sequential(
            nn.Linear(20, 64),  # Input features
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output confidence (0-1)
        )
    
    def estimate_confidence(self, features: np.ndarray) -> float:
        """Estimate confidence from features"""
        with torch.no_grad():
            features_tensor = torch.FloatTensor(features).unsqueeze(0)
            confidence = self.confidence_model(features_tensor)
            return confidence.item()

class MultiObjectiveOptimizer:
    """Multi-objective optimization component"""
    
    def __init__(self):
        self.optimizer = None
    
    def optimize(self, objectives: Dict[str, float], 
                constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimize multiple objectives"""
        # Simple weighted sum optimization
        # In practice, would use more sophisticated multi-objective optimization
        weighted_objectives = {}
        for obj, weight in objectives.items():
            weighted_objectives[obj] = weight
        
        return weighted_objectives
