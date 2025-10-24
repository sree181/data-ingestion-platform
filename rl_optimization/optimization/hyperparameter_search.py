"""
Hyperparameter Optimization
Automated hyperparameter search using Ray Tune with multiple search algorithms
"""

import ray
from ray import tune
import numpy as np
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import structlog
import json
import os
from pathlib import Path

from ..rl_training.rl_agent import MultiObjectiveRLAgent
from ..rl_training.training_engine import RLTrainingEngine
from .search_spaces import SearchSpace
from .schedulers import ASHAScheduler

logger = structlog.get_logger(__name__)

@dataclass
class HyperparameterConfig:
    """Configuration for hyperparameter optimization"""
    search_algorithm: str = "random"  # random, grid, bayesian, asha
    num_trials: int = 100
    max_concurrent_trials: int = 4
    max_episodes_per_trial: int = 100
    evaluation_frequency: int = 10
    early_stopping: bool = True
    patience: int = 10
    output_dir: str = "hyperparameter_results"
    checkpoint_frequency: int = 20

@dataclass
class TrialResult:
    """Result of a hyperparameter trial"""
    trial_id: str
    hyperparameters: Dict[str, Any]
    final_score: float
    best_score: float
    episodes_completed: int
    training_time: float
    status: str  # completed, failed, stopped
    metrics: Dict[str, Any]
    timestamp: datetime

class HyperparameterOptimizer:
    """
    Automated hyperparameter optimization
    - Define search space
    - Multiple search strategies
    - Parallel trial execution
    - Early stopping
    - Result visualization
    """
    
    def __init__(
        self,
        config: HyperparameterConfig,
        training_data_path: str,
        search_space: SearchSpace
    ):
        """
        Initialize hyperparameter optimizer
        
        Args:
            config: Optimization configuration
            training_data_path: Path to training data
            search_space: Search space definition
        """
        self.config = config
        self.training_data_path = training_data_path
        self.search_space = search_space
        
        # Initialize Ray Tune
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        # Results storage
        self.trial_results = []
        self.best_trial = None
        self.optimization_history = []
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
        logger.info("HyperparameterOptimizer initialized",
                   search_algorithm=config.search_algorithm,
                   num_trials=config.num_trials)
    
    def optimize(self) -> Dict[str, Any]:
        """
        Run hyperparameter optimization
        
        Returns:
            Optimization results
        """
        start_time = time.time()
        
        try:
            # Configure search algorithm
            search_algorithm = self._get_search_algorithm()
            
            # Configure scheduler
            scheduler = self._get_scheduler()
            
            # Run optimization
            analysis = tune.run(
                self._trainable_function,
                config=self.search_space.get_config(),
                num_samples=self.config.num_trials,
                search_alg=search_algorithm,
                scheduler=scheduler,
                max_concurrent_trials=self.config.max_concurrent_trials,
                local_dir=self.config.output_dir,
                checkpoint_freq=self.config.checkpoint_frequency,
                stop={"episodes": self.config.max_episodes_per_trial}
            )
            
            # Process results
            self._process_results(analysis)
            
            # Save results
            self._save_results(analysis)
            
            optimization_time = time.time() - start_time
            
            logger.info("Hyperparameter optimization completed",
                       optimization_time=optimization_time,
                       num_trials=len(self.trial_results),
                       best_score=self.best_trial.final_score if self.best_trial else 0.0)
            
            return {
                'best_trial': self.best_trial.__dict__ if self.best_trial else None,
                'num_trials': len(self.trial_results),
                'optimization_time': optimization_time,
                'best_score': self.best_trial.final_score if self.best_trial else 0.0,
                'results': [result.__dict__ for result in self.trial_results]
            }
            
        except Exception as e:
            logger.error(f"Hyperparameter optimization failed: {e}")
            raise
    
    def _get_search_algorithm(self):
        """Get search algorithm based on configuration"""
        if self.config.search_algorithm == "random":
            return tune.suggest.RandomSearch()
        elif self.config.search_algorithm == "grid":
            return tune.suggest.GridSearch()
        elif self.config.search_algorithm == "bayesian":
            try:
                from ray.tune.suggest.bayesopt import BayesOptSearch
                return BayesOptSearch()
            except ImportError:
                logger.warning("BayesOpt not available, falling back to random search")
                return tune.suggest.RandomSearch()
        elif self.config.search_algorithm == "asha":
            return tune.suggest.ASHASearch()
        else:
            logger.warning(f"Unknown search algorithm: {self.config.search_algorithm}, using random")
            return tune.suggest.RandomSearch()
    
    def _get_scheduler(self):
        """Get scheduler based on configuration"""
        if self.config.early_stopping:
            return ASHAScheduler(
                metric="episode_reward_mean",
                mode="max",
                max_t=self.config.max_episodes_per_trial,
                grace_period=self.config.patience,
                reduction_factor=2
            )
        else:
            return None
    
    def _trainable_function(self, config: Dict[str, Any]) -> Dict[str, float]:
        """
        Trainable function for Ray Tune
        
        Args:
            config: Hyperparameter configuration
            
        Returns:
            Training metrics
        """
        try:
            # Extract hyperparameters
            learning_rate = config.get("learning_rate", 0.001)
            gamma = config.get("gamma", 0.99)
            epsilon = config.get("epsilon", 0.1)
            batch_size = config.get("batch_size", 32)
            hidden_dim = config.get("hidden_dim", 128)
            memory_size = config.get("memory_size", 10000)
            
            # Create RL agent with hyperparameters
            agent = MultiObjectiveRLAgent(
                state_dim=20,
                action_dim=10,
                hidden_dim=hidden_dim,
                learning_rate=learning_rate,
                gamma=gamma,
                epsilon=epsilon,
                batch_size=batch_size,
                memory_size=memory_size
            )
            
            # Create training engine
            training_engine = RLTrainingEngine(
                training_data_path=self.training_data_path,
                output_dir=f"trial_output_{tune.get_trial_id()}",
                episodes=self.config.max_episodes_per_trial,
                max_steps_per_episode=50,
                evaluation_frequency=self.config.evaluation_frequency,
                save_frequency=20
            )
            
            # Set agent in training engine
            training_engine.agent = agent
            
            # Run training
            training_engine.train()
            
            # Get final metrics
            final_metrics = training_engine._calculate_performance_metrics()
            
            # Return metrics for Ray Tune
            return {
                "episode_reward_mean": final_metrics.get("episode_reward_mean", 0.0),
                "episode_length_mean": final_metrics.get("episode_length_mean", 0.0),
                "training_loss": final_metrics.get("training_loss", 0.0),
                "accuracy": final_metrics.get("accuracy", 0.0),
                "cost_efficiency": final_metrics.get("cost_efficiency", 0.0),
                "processing_speed": final_metrics.get("processing_speed", 0.0),
                "stability": final_metrics.get("stability", 0.0),
                "domain_specialization": final_metrics.get("domain_specialization", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Trial failed: {e}")
            # Return default metrics for failed trials
            return {
                "episode_reward_mean": 0.0,
                "episode_length_mean": 0.0,
                "training_loss": float('inf'),
                "accuracy": 0.0,
                "cost_efficiency": 0.0,
                "processing_speed": 0.0,
                "stability": 0.0,
                "domain_specialization": 0.0
            }
    
    def _process_results(self, analysis):
        """Process optimization results"""
        try:
            # Get best trial
            best_trial = analysis.get_best_trial("episode_reward_mean", "max", "last")
            
            if best_trial:
                # Create trial result
                trial_result = TrialResult(
                    trial_id=best_trial.trial_id,
                    hyperparameters=best_trial.config,
                    final_score=best_trial.last_result.get("episode_reward_mean", 0.0),
                    best_score=best_trial.best_result.get("episode_reward_mean", 0.0),
                    episodes_completed=best_trial.last_result.get("episodes", 0),
                    training_time=best_trial.last_result.get("time_total_s", 0.0),
                    status="completed",
                    metrics=best_trial.last_result,
                    timestamp=datetime.utcnow()
                )
                
                self.best_trial = trial_result
                self.trial_results.append(trial_result)
            
            # Process all trials
            for trial in analysis.trials:
                if trial.status == "TERMINATED":
                    trial_result = TrialResult(
                        trial_id=trial.trial_id,
                        hyperparameters=trial.config,
                        final_score=trial.last_result.get("episode_reward_mean", 0.0),
                        best_score=trial.best_result.get("episode_reward_mean", 0.0),
                        episodes_completed=trial.last_result.get("episodes", 0),
                        training_time=trial.last_result.get("time_total_s", 0.0),
                        status="completed",
                        metrics=trial.last_result,
                        timestamp=datetime.utcnow()
                    )
                    self.trial_results.append(trial_result)
            
            # Sort by final score
            self.trial_results.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(f"Processed {len(self.trial_results)} trial results")
            
        except Exception as e:
            logger.error(f"Failed to process results: {e}")
    
    def _save_results(self, analysis):
        """Save optimization results"""
        try:
            # Save detailed results
            results_path = os.path.join(self.config.output_dir, "optimization_results.json")
            
            results_data = {
                'best_trial': self.best_trial.__dict__ if self.best_trial else None,
                'all_trials': [result.__dict__ for result in self.trial_results],
                'config': self.config.__dict__,
                'search_space': self.search_space.get_config(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(results_path, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            # Save best hyperparameters
            if self.best_trial:
                best_params_path = os.path.join(self.config.output_dir, "best_hyperparameters.json")
                with open(best_params_path, 'w') as f:
                    json.dump(self.best_trial.hyperparameters, f, indent=2)
            
            logger.info(f"Results saved to {self.config.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def get_best_hyperparameters(self) -> Optional[Dict[str, Any]]:
        """Get best hyperparameters found"""
        if self.best_trial:
            return self.best_trial.hyperparameters
        return None
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary"""
        if not self.trial_results:
            return {'error': 'No trials completed'}
        
        # Calculate statistics
        scores = [result.final_score for result in self.trial_results]
        
        return {
            'num_trials': len(self.trial_results),
            'best_score': max(scores),
            'worst_score': min(scores),
            'average_score': np.mean(scores),
            'std_score': np.std(scores),
            'best_hyperparameters': self.best_trial.hyperparameters if self.best_trial else None,
            'top_5_trials': [
                {
                    'trial_id': result.trial_id,
                    'score': result.final_score,
                    'hyperparameters': result.hyperparameters
                }
                for result in self.trial_results[:5]
            ]
        }
    
    def visualize_results(self, output_path: Optional[str] = None):
        """Create visualization of optimization results"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if not self.trial_results:
                logger.warning("No results to visualize")
                return
            
            # Create figure
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot 1: Score distribution
            scores = [result.final_score for result in self.trial_results]
            axes[0, 0].hist(scores, bins=20, alpha=0.7)
            axes[0, 0].set_title('Score Distribution')
            axes[0, 0].set_xlabel('Final Score')
            axes[0, 0].set_ylabel('Frequency')
            
            # Plot 2: Score vs Episodes
            episodes = [result.episodes_completed for result in self.trial_results]
            axes[0, 1].scatter(episodes, scores, alpha=0.6)
            axes[0, 1].set_title('Score vs Episodes')
            axes[0, 1].set_xlabel('Episodes Completed')
            axes[0, 1].set_ylabel('Final Score')
            
            # Plot 3: Training time distribution
            times = [result.training_time for result in self.trial_results]
            axes[1, 0].hist(times, bins=20, alpha=0.7)
            axes[1, 0].set_title('Training Time Distribution')
            axes[1, 0].set_xlabel('Training Time (seconds)')
            axes[1, 0].set_ylabel('Frequency')
            
            # Plot 4: Score vs Training time
            axes[1, 1].scatter(times, scores, alpha=0.6)
            axes[1, 1].set_title('Score vs Training Time')
            axes[1, 1].set_xlabel('Training Time (seconds)')
            axes[1, 1].set_ylabel('Final Score')
            
            plt.tight_layout()
            
            # Save plot
            if output_path is None:
                output_path = os.path.join(self.config.output_dir, "optimization_visualization.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Visualization saved to {output_path}")
            
        except ImportError:
            logger.warning("Matplotlib not available for visualization")
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
    
    def shutdown(self):
        """Shutdown optimizer"""
        if ray.is_initialized():
            ray.shutdown()
        
        logger.info("HyperparameterOptimizer shutdown complete")

# Factory function for easy hyperparameter optimization
def create_hyperparameter_optimizer(
    training_data_path: str,
    output_dir: str = "hyperparameter_results",
    num_trials: int = 100,
    search_algorithm: str = "random",
    **kwargs
) -> HyperparameterOptimizer:
    """
    Create hyperparameter optimizer with default configuration
    
    Args:
        training_data_path: Path to training data
        output_dir: Output directory for results
        num_trials: Number of trials to run
        search_algorithm: Search algorithm to use
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured HyperparameterOptimizer
    """
    config = HyperparameterConfig(
        search_algorithm=search_algorithm,
        num_trials=num_trials,
        output_dir=output_dir,
        **kwargs
    )
    
    search_space = SearchSpace()
    
    return HyperparameterOptimizer(
        config=config,
        training_data_path=training_data_path,
        search_space=search_space
    )
