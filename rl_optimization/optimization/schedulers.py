"""
Schedulers for Hyperparameter Optimization
Early stopping and resource allocation strategies
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class SchedulerConfig:
    """Configuration for schedulers"""
    metric: str = "episode_reward_mean"
    mode: str = "max"  # max or min
    max_t: int = 1000
    grace_period: int = 10
    reduction_factor: float = 2.0
    brackets: int = 1
    min_t: int = 1

class ASHAScheduler:
    """
    Asynchronous Successive Halving Algorithm
    - Early stopping for poor trials
    - Resource allocation optimization
    - Brackets for different resource levels
    """
    
    def __init__(self, config: SchedulerConfig):
        """
        Initialize ASHA scheduler
        
        Args:
            config: Scheduler configuration
        """
        self.config = config
        self.trials = {}
        self.brackets = self._create_brackets()
        
        logger.info("ASHAScheduler initialized",
                   metric=config.metric,
                   mode=config.mode,
                   max_t=config.max_t)
    
    def _create_brackets(self) -> List[Dict[str, Any]]:
        """Create brackets for different resource levels"""
        brackets = []
        
        for bracket_id in range(self.config.brackets):
            bracket = {
                'id': bracket_id,
                'max_t': self.config.max_t // (self.config.reduction_factor ** bracket_id),
                'min_t': self.config.min_t,
                'trials': [],
                'completed_trials': []
            }
            brackets.append(bracket)
        
        return brackets
    
    def on_trial_result(self, trial_id: str, result: Dict[str, Any]) -> str:
        """
        Handle trial result
        
        Args:
            trial_id: Trial identifier
            result: Trial result
            
        Returns:
            Action to take (CONTINUE, STOP, PAUSE)
        """
        try:
            # Get trial info
            if trial_id not in self.trials:
                self.trials[trial_id] = {
                    'bracket_id': 0,
                    'start_time': datetime.utcnow(),
                    'last_result': result,
                    'best_result': result,
                    'episodes': result.get('episodes', 0)
                }
            
            trial_info = self.trials[trial_id]
            bracket_id = trial_info['bracket_id']
            bracket = self.brackets[bracket_id]
            
            # Update trial info
            trial_info['last_result'] = result
            trial_info['episodes'] = result.get('episodes', 0)
            
            # Update best result
            if self._is_better_result(result, trial_info['best_result']):
                trial_info['best_result'] = result
            
            # Check if trial should be stopped
            if self._should_stop_trial(trial_info, bracket):
                logger.info(f"Stopping trial {trial_id} in bracket {bracket_id}")
                return "STOP"
            
            # Check if trial should be promoted to next bracket
            if self._should_promote_trial(trial_info, bracket):
                logger.info(f"Promoting trial {trial_id} to bracket {bracket_id + 1}")
                trial_info['bracket_id'] = min(bracket_id + 1, len(self.brackets) - 1)
                return "CONTINUE"
            
            return "CONTINUE"
            
        except Exception as e:
            logger.error(f"Error processing trial result for {trial_id}: {e}")
            return "CONTINUE"
    
    def _is_better_result(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> bool:
        """Check if result1 is better than result2"""
        metric = self.config.metric
        
        if metric not in result1 or metric not in result2:
            return False
        
        if self.config.mode == "max":
            return result1[metric] > result2[metric]
        else:
            return result1[metric] < result2[metric]
    
    def _should_stop_trial(self, trial_info: Dict[str, Any], bracket: Dict[str, Any]) -> bool:
        """Check if trial should be stopped"""
        episodes = trial_info['episodes']
        max_t = bracket['max_t']
        
        # Stop if exceeded maximum episodes
        if episodes >= max_t:
            return True
        
        # Stop if trial is performing poorly compared to other trials in bracket
        if episodes >= self.config.grace_period:
            return self._is_poor_performing_trial(trial_info, bracket)
        
        return False
    
    def _should_promote_trial(self, trial_info: Dict[str, Any], bracket: Dict[str, Any]) -> bool:
        """Check if trial should be promoted to next bracket"""
        episodes = trial_info['episodes']
        max_t = bracket['max_t']
        
        # Promote if trial has completed current bracket
        if episodes >= max_t:
            return True
        
        return False
    
    def _is_poor_performing_trial(self, trial_info: Dict[str, Any], bracket: Dict[str, Any]) -> bool:
        """Check if trial is performing poorly"""
        try:
            # Get all trials in bracket
            bracket_trials = [t for t in self.trials.values() if t['bracket_id'] == bracket['id']]
            
            if len(bracket_trials) < 2:
                return False
            
            # Get current trial's performance
            current_metric = trial_info['last_result'].get(self.config.metric, 0.0)
            
            # Get performance of other trials
            other_metrics = [
                t['last_result'].get(self.config.metric, 0.0)
                for t in bracket_trials
                if t != trial_info
            ]
            
            if not other_metrics:
                return False
            
            # Check if current trial is in bottom 50%
            if self.config.mode == "max":
                return current_metric < np.median(other_metrics)
            else:
                return current_metric > np.median(other_metrics)
            
        except Exception as e:
            logger.warning(f"Error checking trial performance: {e}")
            return False
    
    def get_bracket_info(self, bracket_id: int) -> Dict[str, Any]:
        """Get information about a specific bracket"""
        if bracket_id >= len(self.brackets):
            return {}
        
        bracket = self.brackets[bracket_id]
        trials_in_bracket = [t for t in self.trials.values() if t['bracket_id'] == bracket_id]
        
        return {
            'bracket_id': bracket_id,
            'max_t': bracket['max_t'],
            'min_t': bracket['min_t'],
            'num_trials': len(trials_in_bracket),
            'completed_trials': len([t for t in trials_in_bracket if t['episodes'] >= bracket['max_t']])
        }
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_trials = len(self.trials)
        completed_trials = len([t for t in self.trials.values() if t['episodes'] >= self.config.max_t])
        
        bracket_stats = []
        for i, bracket in enumerate(self.brackets):
            trials_in_bracket = [t for t in self.trials.values() if t['bracket_id'] == i]
            bracket_stats.append({
                'bracket_id': i,
                'num_trials': len(trials_in_bracket),
                'completed_trials': len([t for t in trials_in_bracket if t['episodes'] >= bracket['max_t']])
            })
        
        return {
            'total_trials': total_trials,
            'completed_trials': completed_trials,
            'completion_rate': completed_trials / max(total_trials, 1),
            'bracket_stats': bracket_stats,
            'config': self.config.__dict__
        }

class EarlyStoppingScheduler:
    """
    Early stopping scheduler
    - Stop trials that don't improve
    - Patience-based stopping
    - Performance threshold stopping
    """
    
    def __init__(
        self,
        metric: str = "episode_reward_mean",
        mode: str = "max",
        patience: int = 10,
        min_delta: float = 0.01,
        threshold: Optional[float] = None
    ):
        """
        Initialize early stopping scheduler
        
        Args:
            metric: Metric to monitor
            mode: max or min
            patience: Number of episodes to wait for improvement
            min_delta: Minimum change to qualify as improvement
            threshold: Performance threshold for stopping
        """
        self.metric = metric
        self.mode = mode
        self.patience = patience
        self.min_delta = min_delta
        self.threshold = threshold
        
        self.trials = {}
        
        logger.info("EarlyStoppingScheduler initialized",
                   metric=metric,
                   mode=mode,
                   patience=patience)
    
    def on_trial_result(self, trial_id: str, result: Dict[str, Any]) -> str:
        """
        Handle trial result
        
        Args:
            trial_id: Trial identifier
            result: Trial result
            
        Returns:
            Action to take (CONTINUE, STOP, PAUSE)
        """
        try:
            # Initialize trial if not exists
            if trial_id not in self.trials:
                self.trials[trial_id] = {
                    'best_score': float('-inf') if self.mode == "max" else float('inf'),
                    'patience_counter': 0,
                    'episodes': 0,
                    'last_score': None
                }
            
            trial_info = self.trials[trial_id]
            current_score = result.get(self.metric, 0.0)
            trial_info['episodes'] = result.get('episodes', 0)
            trial_info['last_score'] = current_score
            
            # Check threshold stopping
            if self.threshold is not None:
                if self._meets_threshold(current_score):
                    logger.info(f"Trial {trial_id} met threshold {self.threshold}")
                    return "STOP"
            
            # Check improvement
            if self._is_improvement(current_score, trial_info['best_score']):
                trial_info['best_score'] = current_score
                trial_info['patience_counter'] = 0
            else:
                trial_info['patience_counter'] += 1
            
            # Check patience
            if trial_info['patience_counter'] >= self.patience:
                logger.info(f"Trial {trial_id} stopped due to patience ({self.patience})")
                return "STOP"
            
            return "CONTINUE"
            
        except Exception as e:
            logger.error(f"Error processing trial result for {trial_id}: {e}")
            return "CONTINUE"
    
    def _is_improvement(self, current_score: float, best_score: float) -> bool:
        """Check if current score is an improvement"""
        if self.mode == "max":
            return current_score > best_score + self.min_delta
        else:
            return current_score < best_score - self.min_delta
    
    def _meets_threshold(self, score: float) -> bool:
        """Check if score meets threshold"""
        if self.threshold is None:
            return False
        
        if self.mode == "max":
            return score >= self.threshold
        else:
            return score <= self.threshold
    
    def get_trial_stats(self, trial_id: str) -> Dict[str, Any]:
        """Get statistics for a specific trial"""
        if trial_id not in self.trials:
            return {}
        
        trial_info = self.trials[trial_id]
        return {
            'trial_id': trial_id,
            'best_score': trial_info['best_score'],
            'last_score': trial_info['last_score'],
            'patience_counter': trial_info['patience_counter'],
            'episodes': trial_info['episodes'],
            'is_stopped': trial_info['patience_counter'] >= self.patience
        }
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_trials = len(self.trials)
        stopped_trials = len([t for t in self.trials.values() if t['patience_counter'] >= self.patience])
        
        return {
            'total_trials': total_trials,
            'stopped_trials': stopped_trials,
            'stopping_rate': stopped_trials / max(total_trials, 1),
            'metric': self.metric,
            'mode': self.mode,
            'patience': self.patience,
            'threshold': self.threshold
        }

class ResourceAllocationScheduler:
    """
    Resource allocation scheduler
    - Dynamic resource allocation
    - Performance-based resource distribution
    - Budget management
    """
    
    def __init__(
        self,
        total_budget: float = 1000.0,
        min_resource: float = 1.0,
        max_resource: float = 100.0,
        allocation_strategy: str = "performance_based"
    ):
        """
        Initialize resource allocation scheduler
        
        Args:
            total_budget: Total resource budget
            min_resource: Minimum resource per trial
            max_resource: Maximum resource per trial
            allocation_strategy: Strategy for resource allocation
        """
        self.total_budget = total_budget
        self.min_resource = min_resource
        self.max_resource = max_resource
        self.allocation_strategy = allocation_strategy
        
        self.trials = {}
        self.used_budget = 0.0
        
        logger.info("ResourceAllocationScheduler initialized",
                   total_budget=total_budget,
                   allocation_strategy=allocation_strategy)
    
    def allocate_resources(self, trial_id: str, result: Dict[str, Any]) -> float:
        """
        Allocate resources for a trial
        
        Args:
            trial_id: Trial identifier
            result: Trial result
            
        Returns:
            Allocated resources
        """
        try:
            # Initialize trial if not exists
            if trial_id not in self.trials:
                self.trials[trial_id] = {
                    'allocated_resources': 0.0,
                    'performance_history': [],
                    'episodes': 0
                }
            
            trial_info = self.trials[trial_id]
            trial_info['episodes'] = result.get('episodes', 0)
            trial_info['performance_history'].append(result.get('episode_reward_mean', 0.0))
            
            # Calculate resource allocation
            if self.allocation_strategy == "performance_based":
                allocation = self._performance_based_allocation(trial_info)
            elif self.allocation_strategy == "equal":
                allocation = self._equal_allocation()
            else:
                allocation = self.min_resource
            
            # Apply constraints
            allocation = max(self.min_resource, min(allocation, self.max_resource))
            allocation = min(allocation, self.total_budget - self.used_budget)
            
            # Update trial info
            trial_info['allocated_resources'] += allocation
            self.used_budget += allocation
            
            logger.info(f"Allocated {allocation} resources to trial {trial_id}")
            return allocation
            
        except Exception as e:
            logger.error(f"Error allocating resources for trial {trial_id}: {e}")
            return self.min_resource
    
    def _performance_based_allocation(self, trial_info: Dict[str, Any]) -> float:
        """Allocate resources based on performance"""
        performance_history = trial_info['performance_history']
        
        if not performance_history:
            return self.min_resource
        
        # Calculate performance score
        recent_performance = np.mean(performance_history[-5:])  # Last 5 episodes
        performance_score = max(0.0, min(1.0, recent_performance))
        
        # Allocate resources based on performance
        base_allocation = self.min_resource
        performance_bonus = (self.max_resource - self.min_resource) * performance_score
        
        return base_allocation + performance_bonus
    
    def _equal_allocation(self) -> float:
        """Equal resource allocation"""
        remaining_budget = self.total_budget - self.used_budget
        num_trials = len(self.trials)
        
        if num_trials == 0:
            return self.min_resource
        
        return min(self.max_resource, remaining_budget / num_trials)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get budget status"""
        return {
            'total_budget': self.total_budget,
            'used_budget': self.used_budget,
            'remaining_budget': self.total_budget - self.used_budget,
            'budget_utilization': self.used_budget / self.total_budget,
            'num_trials': len(self.trials)
        }
    
    def get_trial_allocation(self, trial_id: str) -> Dict[str, Any]:
        """Get resource allocation for a specific trial"""
        if trial_id not in self.trials:
            return {}
        
        trial_info = self.trials[trial_id]
        return {
            'trial_id': trial_id,
            'allocated_resources': trial_info['allocated_resources'],
            'episodes': trial_info['episodes'],
            'avg_performance': np.mean(trial_info['performance_history']) if trial_info['performance_history'] else 0.0
        }
