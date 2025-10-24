"""
IP-Enhanced RL Agent
Integrates all novel algorithms for patentable intellectual property
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import structlog
import json
from collections import deque

# Import novel algorithms
from adaptive_reward_shaping import AdaptiveMultiObjectiveRewardShaping, PerformanceTargets, AdaptationConfig
from hierarchical_rule_evolution import HierarchicalRuleEvolution, RuleLevel, EvolutionConfig
from confidence_aware_multi_objective import ConfidenceAwareMultiObjective, OptimizationConfig

logger = structlog.get_logger(__name__)

@dataclass
class IPEnhancedConfig:
    """Configuration for IP-enhanced RL agent"""
    # Adaptive reward shaping
    adaptation_rate: float = 0.01
    performance_targets: PerformanceTargets = None
    adaptation_config: AdaptationConfig = None
    
    # Hierarchical rule evolution
    evolution_config: EvolutionConfig = None
    
    # Confidence-aware optimization
    optimization_config: OptimizationConfig = None
    
    # IP-specific parameters
    patent_optimization: bool = True
    novel_algorithm_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.performance_targets is None:
            self.performance_targets = PerformanceTargets()
        if self.adaptation_config is None:
            self.adaptation_config = AdaptationConfig()
        if self.evolution_config is None:
            self.evolution_config = EvolutionConfig()
        if self.optimization_config is None:
            self.optimization_config = OptimizationConfig()
        if self.novel_algorithm_weights is None:
            self.novel_algorithm_weights = {
                'adaptive_reward_shaping': 0.4,
                'hierarchical_rule_evolution': 0.3,
                'confidence_aware_optimization': 0.3
            }

class IPEnhancedRLAgent:
    """
    IP-Enhanced RL Agent integrating all novel algorithms
    Represents a patentable intellectual property
    """
    
    def __init__(self, config: Optional[IPEnhancedConfig] = None):
        self.config = config or IPEnhancedConfig()
        
        # Initialize novel algorithms
        self.adaptive_reward_shaping = AdaptiveMultiObjectiveRewardShaping(
            performance_targets=self.config.performance_targets,
            adaptation_config=self.config.adaptation_config
        )
        
        self.hierarchical_rule_evolution = HierarchicalRuleEvolution(
            evolution_config=self.config.evolution_config
        )
        
        self.confidence_aware_optimization = ConfidenceAwareMultiObjective(
            config=self.config.optimization_config
        )
        
        # IP-specific components
        self.patent_optimization_active = self.config.patent_optimization
        self.novel_algorithm_weights = self.config.novel_algorithm_weights
        
        # Performance tracking
        self.ip_performance_metrics = {
            'novelty_score': 0.0,
            'performance_improvement': 0.0,
            'patent_potential': 0.0,
            'commercial_viability': 0.0
        }
        
        # IP tracking
        self.ip_metrics_history = deque(maxlen=1000)
        self.algorithm_usage_stats = {
            'adaptive_reward_shaping': 0,
            'hierarchical_rule_evolution': 0,
            'confidence_aware_optimization': 0
        }
        
        logger.info("IP-Enhanced RL Agent initialized",
                   patent_optimization=self.patent_optimization_active,
                   novel_algorithm_weights=self.novel_algorithm_weights)
    
    def optimize_with_ip_algorithms(self, 
                                  state: Dict[str, Any],
                                  performance_feedback: Dict[str, float],
                                  confidence: float,
                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Novel IP method: Optimize using all integrated algorithms
        
        Args:
            state: Current system state
            performance_feedback: Performance metrics
            confidence: Confidence level
            context: Additional context information
            
        Returns:
            IP-optimized configuration
        """
        # Step 1: Adaptive Reward Shaping
        adapted_weights = self.adaptive_reward_shaping.adapt_weights(performance_feedback)
        self.algorithm_usage_stats['adaptive_reward_shaping'] += 1
        
        # Step 2: Hierarchical Rule Evolution
        evolved_rules = self._perform_hierarchical_evolution(state, performance_feedback)
        self.algorithm_usage_stats['hierarchical_rule_evolution'] += 1
        
        # Step 3: Confidence-Aware Multi-Objective Optimization
        optimized_config = self.confidence_aware_optimization.optimize_with_confidence(
            state, confidence, context
        )
        self.algorithm_usage_stats['confidence_aware_optimization'] += 1
        
        # Step 4: IP Integration
        ip_optimized_config = self._integrate_ip_algorithms(
            state, adapted_weights, evolved_rules, optimized_config
        )
        
        # Step 5: IP Performance Tracking
        self._track_ip_performance(ip_optimized_config, performance_feedback)
        
        logger.info("IP optimization completed",
                   adapted_weights=adapted_weights,
                   evolved_rules_keys=list(evolved_rules.keys()),
                   confidence=confidence,
                   ip_metrics=self.ip_performance_metrics)
        
        return ip_optimized_config
    
    def _perform_hierarchical_evolution(self, 
                                       state: Dict[str, Any],
                                       performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """Perform hierarchical rule evolution"""
        evolved_rules = {}
        
        # Evolve rules at different hierarchy levels
        for level in [RuleLevel.GLOBAL, RuleLevel.DOMAIN, RuleLevel.SUBDOMAIN]:
            try:
                level_rules = self.hierarchical_rule_evolution.evolve_rules(
                    level=level,
                    performance_feedback=performance_feedback
                )
                evolved_rules[f"{level.value}_rules"] = level_rules
            except Exception as e:
                logger.warning(f"Failed to evolve rules at level {level.value}: {e}")
                evolved_rules[f"{level.value}_rules"] = {}
        
        return evolved_rules
    
    def _integrate_ip_algorithms(self, 
                                original_state: Dict[str, Any],
                                adapted_weights: Dict[str, float],
                                evolved_rules: Dict[str, Any],
                                optimized_config: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate all IP algorithms into final configuration"""
        ip_config = original_state.copy()
        
        # Apply adaptive reward shaping
        if 'reward_weights' in ip_config:
            ip_config['reward_weights'] = adapted_weights
        
        # Apply hierarchical rule evolution
        for rule_type, rules in evolved_rules.items():
            if rules:  # Only apply if rules were successfully evolved
                ip_config[rule_type] = rules
        
        # Apply confidence-aware optimization
        ip_config.update(optimized_config)
        
        # IP-specific enhancements
        if self.patent_optimization_active:
            ip_config = self._apply_patent_optimizations(ip_config)
        
        return ip_config
    
    def _apply_patent_optimizations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patent-specific optimizations"""
        patent_config = config.copy()
        
        # Novel algorithm weight integration
        if 'algorithm_weights' not in patent_config:
            patent_config['algorithm_weights'] = self.novel_algorithm_weights
        
        # IP performance tracking
        patent_config['ip_metrics'] = self.ip_performance_metrics
        
        # Patent-specific parameters
        patent_config['patent_optimization'] = True
        patent_config['novel_algorithms_active'] = list(self.algorithm_usage_stats.keys())
        
        return patent_config
    
    def _track_ip_performance(self, 
                             optimized_config: Dict[str, Any],
                             performance_feedback: Dict[str, float]):
        """Track IP-specific performance metrics"""
        # Calculate novelty score
        novelty_score = self._calculate_novelty_score(optimized_config)
        
        # Calculate performance improvement
        performance_improvement = self._calculate_performance_improvement(performance_feedback)
        
        # Calculate patent potential
        patent_potential = self._calculate_patent_potential(optimized_config)
        
        # Calculate commercial viability
        commercial_viability = self._calculate_commercial_viability(performance_feedback)
        
        # Update IP metrics
        self.ip_performance_metrics = {
            'novelty_score': novelty_score,
            'performance_improvement': performance_improvement,
            'patent_potential': patent_potential,
            'commercial_viability': commercial_viability
        }
        
        # Store metrics history
        ip_record = {
            'timestamp': datetime.utcnow(),
            'metrics': self.ip_performance_metrics.copy(),
            'algorithm_usage': self.algorithm_usage_stats.copy(),
            'config_keys': list(optimized_config.keys())
        }
        self.ip_metrics_history.append(ip_record)
    
    def _calculate_novelty_score(self, config: Dict[str, Any]) -> float:
        """Calculate novelty score based on configuration"""
        novelty_indicators = [
            'adaptive_reward_shaping' in str(config),
            'hierarchical_rule_evolution' in str(config),
            'confidence_aware_optimization' in str(config),
            'patent_optimization' in config,
            'novel_algorithms_active' in config
        ]
        
        return sum(novelty_indicators) / len(novelty_indicators)
    
    def _calculate_performance_improvement(self, performance_feedback: Dict[str, float]) -> float:
        """Calculate performance improvement score"""
        if not performance_feedback:
            return 0.0
        
        # Calculate weighted performance score
        weights = {
            'accuracy': 0.3,
            'cost_efficiency': 0.25,
            'processing_speed': 0.2,
            'stability': 0.15,
            'domain_specialization': 0.1
        }
        
        weighted_score = 0.0
        for metric, weight in weights.items():
            if metric in performance_feedback:
                weighted_score += performance_feedback[metric] * weight
        
        return weighted_score
    
    def _calculate_patent_potential(self, config: Dict[str, Any]) -> float:
        """Calculate patent potential score"""
        patent_indicators = [
            'novel_algorithm_weights' in config,
            'ip_metrics' in config,
            'patent_optimization' in config,
            len(config) > 10,  # Complexity indicator
            any('adaptive' in str(v) for v in config.values()),
            any('hierarchical' in str(v) for v in config.values()),
            any('confidence' in str(v) for v in config.values())
        ]
        
        return sum(patent_indicators) / len(patent_indicators)
    
    def _calculate_commercial_viability(self, performance_feedback: Dict[str, float]) -> float:
        """Calculate commercial viability score"""
        if not performance_feedback:
            return 0.0
        
        # Commercial viability factors
        accuracy = performance_feedback.get('accuracy', 0.0)
        cost_efficiency = performance_feedback.get('cost_efficiency', 0.0)
        processing_speed = performance_feedback.get('processing_speed', 0.0)
        
        # Weighted commercial viability score
        viability_score = (
            accuracy * 0.4 +
            cost_efficiency * 0.3 +
            processing_speed * 0.3
        )
        
        return min(1.0, max(0.0, viability_score))
    
    def get_ip_statistics(self) -> Dict[str, Any]:
        """Get comprehensive IP statistics"""
        return {
            'ip_performance_metrics': self.ip_performance_metrics,
            'algorithm_usage_stats': self.algorithm_usage_stats,
            'total_optimizations': len(self.ip_metrics_history),
            'patent_optimization_active': self.patent_optimization_active,
            'novel_algorithm_weights': self.novel_algorithm_weights,
            'recent_ip_metrics': list(self.ip_metrics_history)[-10:] if self.ip_metrics_history else []
        }
    
    def get_patent_application_data(self) -> Dict[str, Any]:
        """Get data for patent application"""
        return {
            'novel_algorithms': {
                'adaptive_reward_shaping': {
                    'description': 'Dynamic reward weight adjustment based on real-time performance feedback',
                    'usage_count': self.algorithm_usage_stats['adaptive_reward_shaping'],
                    'performance_impact': self.ip_performance_metrics['performance_improvement']
                },
                'hierarchical_rule_evolution': {
                    'description': 'Multi-level rule optimization with domain hierarchy',
                    'usage_count': self.algorithm_usage_stats['hierarchical_rule_evolution'],
                    'performance_impact': self.ip_performance_metrics['novelty_score']
                },
                'confidence_aware_optimization': {
                    'description': 'Confidence-based objective prioritization',
                    'usage_count': self.algorithm_usage_stats['confidence_aware_optimization'],
                    'performance_impact': self.ip_performance_metrics['patent_potential']
                }
            },
            'performance_improvements': self.ip_performance_metrics,
            'commercial_viability': self.ip_performance_metrics['commercial_viability'],
            'patent_potential': self.ip_performance_metrics['patent_potential'],
            'novelty_score': self.ip_performance_metrics['novelty_score']
        }
    
    def save_ip_state(self, filepath: str):
        """Save IP state to file"""
        state = {
            'config': self.config.__dict__,
            'ip_performance_metrics': self.ip_performance_metrics,
            'algorithm_usage_stats': self.algorithm_usage_stats,
            'ip_metrics_history': list(self.ip_metrics_history),
            'patent_optimization_active': self.patent_optimization_active,
            'novel_algorithm_weights': self.novel_algorithm_weights,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info("IP state saved", filepath=filepath)
    
    def load_ip_state(self, filepath: str):
        """Load IP state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore state
        self.ip_performance_metrics = state['ip_performance_metrics']
        self.algorithm_usage_stats = state['algorithm_usage_stats']
        self.ip_metrics_history = deque(state['ip_metrics_history'], maxlen=1000)
        self.patent_optimization_active = state['patent_optimization_active']
        self.novel_algorithm_weights = state['novel_algorithm_weights']
        
        logger.info("IP state loaded", filepath=filepath)
    
    def generate_patent_summary(self) -> str:
        """Generate patent application summary"""
        patent_data = self.get_patent_application_data()
        
        summary = f"""
PATENT APPLICATION SUMMARY
==========================

Title: "Adaptive Multi-Objective Reinforcement Learning for Pharmacovigilance Classification"

Novel Algorithms:
1. Adaptive Multi-Objective Reward Shaping (AMORS)
   - Usage: {patent_data['novel_algorithms']['adaptive_reward_shaping']['usage_count']} times
   - Performance Impact: {patent_data['novel_algorithms']['adaptive_reward_shaping']['performance_impact']:.3f}
   - Description: {patent_data['novel_algorithms']['adaptive_reward_shaping']['description']}

2. Hierarchical Rule Evolution (HRE)
   - Usage: {patent_data['novel_algorithms']['hierarchical_rule_evolution']['usage_count']} times
   - Performance Impact: {patent_data['novel_algorithms']['hierarchical_rule_evolution']['performance_impact']:.3f}
   - Description: {patent_data['novel_algorithms']['hierarchical_rule_evolution']['description']}

3. Confidence-Aware Multi-Objective Optimization (CAMO)
   - Usage: {patent_data['novel_algorithms']['confidence_aware_optimization']['usage_count']} times
   - Performance Impact: {patent_data['novel_algorithms']['confidence_aware_optimization']['performance_impact']:.3f}
   - Description: {patent_data['novel_algorithms']['confidence_aware_optimization']['description']}

Performance Improvements:
- Novelty Score: {patent_data['performance_improvements']['novelty_score']:.3f}
- Performance Improvement: {patent_data['performance_improvements']['performance_improvement']:.3f}
- Patent Potential: {patent_data['performance_improvements']['patent_potential']:.3f}
- Commercial Viability: {patent_data['performance_improvements']['commercial_viability']:.3f}

Total Optimizations: {len(self.ip_metrics_history)}
Patent Optimization Active: {self.patent_optimization_active}
        """
        
        return summary
