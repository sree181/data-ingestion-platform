"""
Search Spaces for Hyperparameter Optimization
Define hyperparameter search spaces for different algorithms
"""

import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class SearchSpace:
    """
    Define hyperparameter search spaces
    - Learning rate: log-uniform
    - Network architecture: categorical
    - Batch size: discrete choices
    - Reward weights: continuous
    """
    
    def __init__(self):
        """Initialize search space with default ranges"""
        self.learning_rate_range = (1e-5, 1e-1)
        self.gamma_range = (0.8, 0.99)
        self.epsilon_range = (0.01, 0.3)
        self.batch_size_choices = [16, 32, 64, 128]
        self.hidden_dim_choices = [64, 128, 256, 512]
        self.memory_size_choices = [5000, 10000, 20000, 50000]
        self.network_layers_choices = [2, 3, 4, 5]
        self.activation_choices = ["relu", "tanh", "elu", "swish"]
        self.dropout_range = (0.0, 0.5)
        self.weight_decay_range = (1e-6, 1e-3)
        
        # Reward weight ranges
        self.reward_weight_ranges = {
            'accuracy': (0.1, 0.5),
            'cost_efficiency': (0.1, 0.4),
            'processing_speed': (0.1, 0.3),
            'stability': (0.1, 0.3),
            'domain_specialization': (0.1, 0.3)
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get Ray Tune configuration for search space
        
        Returns:
            Configuration dictionary for Ray Tune
        """
        return {
            # Learning parameters
            "learning_rate": self._log_uniform(*self.learning_rate_range),
            "gamma": self._uniform(*self.gamma_range),
            "epsilon": self._uniform(*self.epsilon_range),
            
            # Architecture parameters
            "batch_size": self._choice(self.batch_size_choices),
            "hidden_dim": self._choice(self.hidden_dim_choices),
            "memory_size": self._choice(self.memory_size_choices),
            "network_layers": self._choice(self.network_layers_choices),
            "activation": self._choice(self.activation_choices),
            "dropout": self._uniform(*self.dropout_range),
            "weight_decay": self._log_uniform(*self.weight_decay_range),
            
            # Reward weights
            "accuracy_weight": self._uniform(*self.reward_weight_ranges['accuracy']),
            "cost_efficiency_weight": self._uniform(*self.reward_weight_ranges['cost_efficiency']),
            "processing_speed_weight": self._uniform(*self.reward_weight_ranges['processing_speed']),
            "stability_weight": self._uniform(*self.reward_weight_ranges['stability']),
            "domain_specialization_weight": self._uniform(*self.reward_weight_ranges['domain_specialization']),
            
            # Training parameters
            "target_update_frequency": self._choice([50, 100, 200, 500]),
            "epsilon_decay": self._uniform(0.99, 0.999),
            "epsilon_min": self._uniform(0.001, 0.01),
            
            # Data parameters
            "cache_size": self._choice([1000, 5000, 10000, 20000]),
            "prefetch_factor": self._choice([1, 2, 4, 8]),
            "num_workers": self._choice([1, 2, 4, 8])
        }
    
    def _uniform(self, low: float, high: float) -> Dict[str, Any]:
        """Create uniform distribution"""
        return {
            "type": "uniform",
            "low": low,
            "high": high
        }
    
    def _log_uniform(self, low: float, high: float) -> Dict[str, Any]:
        """Create log-uniform distribution"""
        return {
            "type": "log_uniform",
            "low": low,
            "high": high
        }
    
    def _choice(self, choices: List[Any]) -> Dict[str, Any]:
        """Create categorical choice"""
        return {
            "type": "choice",
            "choices": choices
        }
    
    def _normal(self, mean: float, std: float) -> Dict[str, Any]:
        """Create normal distribution"""
        return {
            "type": "normal",
            "mean": mean,
            "std": std
        }
    
    def get_grid_search_config(self) -> Dict[str, Any]:
        """
        Get configuration for grid search
        
        Returns:
            Grid search configuration
        """
        return {
            "learning_rate": [1e-4, 1e-3, 1e-2],
            "gamma": [0.9, 0.95, 0.99],
            "epsilon": [0.1, 0.2, 0.3],
            "batch_size": [32, 64, 128],
            "hidden_dim": [128, 256, 512],
            "memory_size": [10000, 20000],
            "network_layers": [2, 3, 4],
            "activation": ["relu", "tanh"],
            "dropout": [0.0, 0.1, 0.2],
            "weight_decay": [1e-5, 1e-4, 1e-3]
        }
    
    def get_bayesian_search_config(self) -> Dict[str, Any]:
        """
        Get configuration for Bayesian optimization
        
        Returns:
            Bayesian search configuration
        """
        return {
            # Continuous parameters for Bayesian optimization
            "learning_rate": self._log_uniform(*self.learning_rate_range),
            "gamma": self._uniform(*self.gamma_range),
            "epsilon": self._uniform(*self.epsilon_range),
            "dropout": self._uniform(*self.dropout_range),
            "weight_decay": self._log_uniform(*self.weight_decay_range),
            
            # Discrete parameters
            "batch_size": self._choice(self.batch_size_choices),
            "hidden_dim": self._choice(self.hidden_dim_choices),
            "memory_size": self._choice(self.memory_size_choices),
            "network_layers": self._choice(self.network_layers_choices),
            "activation": self._choice(self.activation_choices)
        }
    
    def get_asha_search_config(self) -> Dict[str, Any]:
        """
        Get configuration for ASHA (Asynchronous Successive Halving Algorithm)
        
        Returns:
            ASHA search configuration
        """
        return {
            # Resource parameters
            "max_episodes": 1000,
            "grace_period": 10,
            "reduction_factor": 2,
            
            # Search space
            "learning_rate": self._log_uniform(*self.learning_rate_range),
            "gamma": self._uniform(*self.gamma_range),
            "epsilon": self._uniform(*self.epsilon_range),
            "batch_size": self._choice(self.batch_size_choices),
            "hidden_dim": self._choice(self.hidden_dim_choices),
            "memory_size": self._choice(self.memory_size_choices),
            "network_layers": self._choice(self.network_layers_choices),
            "activation": self._choice(self.activation_choices),
            "dropout": self._uniform(*self.dropout_range),
            "weight_decay": self._log_uniform(*self.weight_decay_range)
        }
    
    def validate_hyperparameters(self, hyperparameters: Dict[str, Any]) -> bool:
        """
        Validate hyperparameters against search space
        
        Args:
            hyperparameters: Hyperparameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required parameters
            required_params = [
                "learning_rate", "gamma", "epsilon", "batch_size",
                "hidden_dim", "memory_size", "network_layers",
                "activation", "dropout", "weight_decay"
            ]
            
            for param in required_params:
                if param not in hyperparameters:
                    logger.warning(f"Missing required parameter: {param}")
                    return False
            
            # Validate ranges
            if not (self.learning_rate_range[0] <= hyperparameters["learning_rate"] <= self.learning_rate_range[1]):
                logger.warning(f"Learning rate out of range: {hyperparameters['learning_rate']}")
                return False
            
            if not (self.gamma_range[0] <= hyperparameters["gamma"] <= self.gamma_range[1]):
                logger.warning(f"Gamma out of range: {hyperparameters['gamma']}")
                return False
            
            if not (self.epsilon_range[0] <= hyperparameters["epsilon"] <= self.epsilon_range[1]):
                logger.warning(f"Epsilon out of range: {hyperparameters['epsilon']}")
                return False
            
            if hyperparameters["batch_size"] not in self.batch_size_choices:
                logger.warning(f"Invalid batch size: {hyperparameters['batch_size']}")
                return False
            
            if hyperparameters["hidden_dim"] not in self.hidden_dim_choices:
                logger.warning(f"Invalid hidden dimension: {hyperparameters['hidden_dim']}")
                return False
            
            if hyperparameters["memory_size"] not in self.memory_size_choices:
                logger.warning(f"Invalid memory size: {hyperparameters['memory_size']}")
                return False
            
            if hyperparameters["network_layers"] not in self.network_layers_choices:
                logger.warning(f"Invalid network layers: {hyperparameters['network_layers']}")
                return False
            
            if hyperparameters["activation"] not in self.activation_choices:
                logger.warning(f"Invalid activation: {hyperparameters['activation']}")
                return False
            
            if not (self.dropout_range[0] <= hyperparameters["dropout"] <= self.dropout_range[1]):
                logger.warning(f"Dropout out of range: {hyperparameters['dropout']}")
                return False
            
            if not (self.weight_decay_range[0] <= hyperparameters["weight_decay"] <= self.weight_decay_range[1]):
                logger.warning(f"Weight decay out of range: {hyperparameters['weight_decay']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Hyperparameter validation failed: {e}")
            return False
    
    def get_default_hyperparameters(self) -> Dict[str, Any]:
        """
        Get default hyperparameters
        
        Returns:
            Default hyperparameter values
        """
        return {
            "learning_rate": 0.001,
            "gamma": 0.99,
            "epsilon": 0.1,
            "batch_size": 32,
            "hidden_dim": 128,
            "memory_size": 10000,
            "network_layers": 3,
            "activation": "relu",
            "dropout": 0.1,
            "weight_decay": 1e-5,
            "target_update_frequency": 100,
            "epsilon_decay": 0.995,
            "epsilon_min": 0.01,
            "cache_size": 10000,
            "prefetch_factor": 2,
            "num_workers": 4
        }
    
    def get_hyperparameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """
        Get bounds for all hyperparameters
        
        Returns:
            Dictionary of parameter bounds
        """
        return {
            "learning_rate": self.learning_rate_range,
            "gamma": self.gamma_range,
            "epsilon": self.epsilon_range,
            "dropout": self.dropout_range,
            "weight_decay": self.weight_decay_range
        }
    
    def get_categorical_choices(self) -> Dict[str, List[Any]]:
        """
        Get categorical choices for all parameters
        
        Returns:
            Dictionary of categorical choices
        """
        return {
            "batch_size": self.batch_size_choices,
            "hidden_dim": self.hidden_dim_choices,
            "memory_size": self.memory_size_choices,
            "network_layers": self.network_layers_choices,
            "activation": self.activation_choices
        }
    
    def sample_hyperparameters(self, num_samples: int = 1) -> List[Dict[str, Any]]:
        """
        Sample hyperparameters from search space
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            List of sampled hyperparameters
        """
        samples = []
        
        for _ in range(num_samples):
            sample = {}
            
            # Sample continuous parameters
            sample["learning_rate"] = np.random.uniform(*self.learning_rate_range)
            sample["gamma"] = np.random.uniform(*self.gamma_range)
            sample["epsilon"] = np.random.uniform(*self.epsilon_range)
            sample["dropout"] = np.random.uniform(*self.dropout_range)
            sample["weight_decay"] = np.random.uniform(*self.weight_decay_range)
            
            # Sample discrete parameters
            sample["batch_size"] = np.random.choice(self.batch_size_choices)
            sample["hidden_dim"] = np.random.choice(self.hidden_dim_choices)
            sample["memory_size"] = np.random.choice(self.memory_size_choices)
            sample["network_layers"] = np.random.choice(self.network_layers_choices)
            sample["activation"] = np.random.choice(self.activation_choices)
            
            # Add other parameters
            sample["target_update_frequency"] = np.random.choice([50, 100, 200, 500])
            sample["epsilon_decay"] = np.random.uniform(0.99, 0.999)
            sample["epsilon_min"] = np.random.uniform(0.001, 0.01)
            sample["cache_size"] = np.random.choice([1000, 5000, 10000, 20000])
            sample["prefetch_factor"] = np.random.choice([1, 2, 4, 8])
            sample["num_workers"] = np.random.choice([1, 2, 4, 8])
            
            samples.append(sample)
        
        return samples
