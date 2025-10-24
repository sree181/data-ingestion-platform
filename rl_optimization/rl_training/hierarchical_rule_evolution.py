"""
Hierarchical Rule Evolution (HRE)
Novel algorithm for multi-level rule optimization with domain hierarchy
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog
from datetime import datetime
import json
import random
from collections import defaultdict, deque

logger = structlog.get_logger(__name__)

class EvolutionStrategy(Enum):
    """Evolution strategies for different rule levels"""
    GENETIC_ALGORITHM = "genetic_algorithm"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    GRADIENT_DESCENT = "gradient_descent"
    ONLINE_LEARNING = "online_learning"
    SIMULATED_ANNEALING = "simulated_annealing"

class RuleLevel(Enum):
    """Rule hierarchy levels"""
    GLOBAL = "global"
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    DOCUMENT = "document"

@dataclass
class RuleConfiguration:
    """Rule configuration at a specific level"""
    level: RuleLevel
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    rules: Dict[str, Any] = None
    performance_metrics: Dict[str, float] = None
    last_updated: datetime = None
    evolution_count: int = 0

@dataclass
class EvolutionConfig:
    """Configuration for rule evolution"""
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    selection_pressure: float = 0.5
    population_size: int = 50
    generations: int = 100
    convergence_threshold: float = 0.01
    learning_rate: float = 0.01
    temperature: float = 1.0
    cooling_rate: float = 0.95

class HierarchicalRuleEvolution:
    """
    Novel algorithm for hierarchical rule optimization
    Multi-level rule evolution with different strategies for each level
    """
    
    def __init__(self, evolution_config: Optional[EvolutionConfig] = None):
        self.config = evolution_config or EvolutionConfig()
        
        # Rule hierarchy
        self.rule_hierarchy = {
            RuleLevel.GLOBAL: {},
            RuleLevel.DOMAIN: defaultdict(dict),
            RuleLevel.SUBDOMAIN: defaultdict(lambda: defaultdict(dict)),
            RuleLevel.DOCUMENT: defaultdict(dict)
        }
        
        # Evolution strategies for each level
        self.evolution_strategies = {
            RuleLevel.GLOBAL: EvolutionStrategy.GENETIC_ALGORITHM,
            RuleLevel.DOMAIN: EvolutionStrategy.REINFORCEMENT_LEARNING,
            RuleLevel.SUBDOMAIN: EvolutionStrategy.GRADIENT_DESCENT,
            RuleLevel.DOCUMENT: EvolutionStrategy.ONLINE_LEARNING
        }
        
        # Performance tracking
        self.performance_history = defaultdict(list)
        self.evolution_history = defaultdict(list)
        self.convergence_status = defaultdict(bool)
        
        # Evolution state
        self.current_generation = 0
        self.evolution_active = False
        
        logger.info("Hierarchical Rule Evolution initialized",
                   evolution_strategies={level.value: strategy.value for level, strategy in self.evolution_strategies.items()})
    
    def evolve_rules(self, level: RuleLevel, 
                    domain: Optional[str] = None,
                    subdomain: Optional[str] = None,
                    performance_feedback: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Novel method: Evolve rules at a specific hierarchy level
        
        Args:
            level: Rule hierarchy level
            domain: Medical domain (for domain/subdomain levels)
            subdomain: Medical subdomain (for subdomain level)
            performance_feedback: Performance metrics for evolution
            
        Returns:
            Evolved rule configuration
        """
        strategy = self.evolution_strategies[level]
        
        # Get current rules
        current_rules = self._get_rules_at_level(level, domain, subdomain)
        
        # Perform evolution based on strategy
        if strategy == EvolutionStrategy.GENETIC_ALGORITHM:
            evolved_rules = self._genetic_evolution(level, current_rules, performance_feedback)
        elif strategy == EvolutionStrategy.REINFORCEMENT_LEARNING:
            evolved_rules = self._rl_evolution(level, current_rules, performance_feedback)
        elif strategy == EvolutionStrategy.GRADIENT_DESCENT:
            evolved_rules = self._gradient_evolution(level, current_rules, performance_feedback)
        elif strategy == EvolutionStrategy.ONLINE_LEARNING:
            evolved_rules = self._online_evolution(level, current_rules, performance_feedback)
        elif strategy == EvolutionStrategy.SIMULATED_ANNEALING:
            evolved_rules = self._simulated_annealing_evolution(level, current_rules, performance_feedback)
        else:
            raise ValueError(f"Unknown evolution strategy: {strategy}")
        
        # Update rule hierarchy
        self._update_rules_at_level(level, evolved_rules, domain, subdomain)
        
        # Track evolution
        self._track_evolution(level, domain, subdomain, current_rules, evolved_rules, performance_feedback)
        
        logger.info("Rules evolved",
                   level=level.value,
                   domain=domain,
                   subdomain=subdomain,
                   strategy=strategy.value,
                   evolution_count=self._get_evolution_count(level, domain, subdomain))
        
        return evolved_rules
    
    def _genetic_evolution(self, level: RuleLevel, 
                          current_rules: Dict[str, Any], 
                          performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """
        Genetic algorithm evolution for global rules
        """
        # Initialize population
        population = self._initialize_population(current_rules, self.config.population_size)
        
        # Evolution loop
        for generation in range(self.config.generations):
            # Evaluate fitness
            fitness_scores = self._evaluate_fitness(population, performance_feedback)
            
            # Check convergence
            if self._check_convergence(fitness_scores):
                break
            
            # Selection
            selected = self._selection(population, fitness_scores)
            
            # Crossover
            offspring = self._crossover(selected)
            
            # Mutation
            mutated_offspring = self._mutation(offspring)
            
            # Update population
            population = self._update_population(population, mutated_offspring, fitness_scores)
        
        # Return best individual
        final_fitness = self._evaluate_fitness(population, performance_feedback)
        best_idx = np.argmax(final_fitness)
        return population[best_idx]
    
    def _initialize_population(self, current_rules: Dict[str, Any], population_size: int) -> List[Dict[str, Any]]:
        """Initialize population for genetic algorithm"""
        population = []
        
        # Add current rules as first individual
        population.append(current_rules.copy())
        
        # Generate random variations
        for i in range(population_size - 1):
            individual = current_rules.copy()
            
            # Mutate each rule parameter
            for key, value in individual.items():
                if isinstance(value, (int, float)):
                    # Numeric mutation
                    mutation_factor = np.random.uniform(0.8, 1.2)
                    individual[key] = value * mutation_factor
                elif isinstance(value, dict):
                    # Nested rule mutation
                    individual[key] = self._mutate_nested_rule(value)
            
            population.append(individual)
        
        return population
    
    def _evaluate_fitness(self, population: List[Dict[str, Any]], 
                          performance_feedback: Dict[str, float]) -> List[float]:
        """Evaluate fitness of population"""
        fitness_scores = []
        
        for individual in population:
            # Calculate fitness based on performance feedback
            fitness = 0.0
            
            # Weight by performance metrics
            weights = {
                'accuracy': 0.3,
                'cost_efficiency': 0.25,
                'processing_speed': 0.2,
                'stability': 0.15,
                'domain_specialization': 0.1
            }
            
            for metric, weight in weights.items():
                if metric in performance_feedback:
                    fitness += performance_feedback[metric] * weight
            
            # Add rule complexity penalty
            complexity_penalty = self._calculate_complexity_penalty(individual)
            fitness -= complexity_penalty
            
            fitness_scores.append(max(0.0, fitness))
        
        return fitness_scores
    
    def _check_convergence(self, fitness_scores: List[float]) -> bool:
        """Check if population has converged"""
        if len(fitness_scores) < 2:
            return False
        
        # Check if fitness variance is below threshold
        fitness_variance = np.var(fitness_scores)
        return fitness_variance < self.config.convergence_threshold
    
    def _selection(self, population: List[Dict[str, Any]], 
                  fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Select individuals for reproduction"""
        # Tournament selection
        selected = []
        tournament_size = 3
        
        for _ in range(len(population)):
            # Random tournament
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            
            # Select best from tournament
            best_tournament_idx = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(population[best_tournament_idx])
        
        return selected
    
    def _crossover(self, selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform crossover between selected individuals"""
        offspring = []
        
        for i in range(0, len(selected), 2):
            if i + 1 < len(selected):
                parent1 = selected[i]
                parent2 = selected[i + 1]
                
                # Create offspring by combining parents
                child1 = self._combine_individuals(parent1, parent2)
                child2 = self._combine_individuals(parent2, parent1)
                
                offspring.extend([child1, child2])
            else:
                offspring.append(selected[i])
        
        return offspring
    
    def _mutation(self, offspring: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply mutation to offspring"""
        mutated = []
        
        for individual in offspring:
            if np.random.random() < self.config.mutation_rate:
                mutated_individual = individual.copy()
                
                # Mutate each parameter
                for key, value in mutated_individual.items():
                    if isinstance(value, (int, float)):
                        # Numeric mutation
                        mutation_factor = np.random.uniform(0.9, 1.1)
                        mutated_individual[key] = value * mutation_factor
                    elif isinstance(value, dict):
                        # Nested rule mutation
                        mutated_individual[key] = self._mutate_nested_rule(value)
                
                mutated.append(mutated_individual)
            else:
                mutated.append(individual)
        
        return mutated
    
    def _update_population(self, population: List[Dict[str, Any]], 
                          offspring: List[Dict[str, Any]], 
                          fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Update population with offspring"""
        # Combine population and offspring
        combined = population + offspring
        
        # Evaluate fitness of combined population
        all_fitness = self._evaluate_fitness(combined, {})
        
        # Select best individuals
        sorted_indices = np.argsort(all_fitness)[::-1]  # Descending order
        new_population = [combined[i] for i in sorted_indices[:len(population)]]
        
        return new_population
    
    def _mutate_nested_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate nested rule structure"""
        mutated_rule = rule.copy()
        
        for key, value in mutated_rule.items():
            if isinstance(value, (int, float)):
                mutation_factor = np.random.uniform(0.9, 1.1)
                mutated_rule[key] = value * mutation_factor
            elif isinstance(value, dict):
                mutated_rule[key] = self._mutate_nested_rule(value)
        
        return mutated_rule
    
    def _combine_individuals(self, parent1: Dict[str, Any], 
                            parent2: Dict[str, Any]) -> Dict[str, Any]:
        """Combine two individuals to create offspring"""
        child = parent1.copy()
        
        for key, value in parent2.items():
            if key in child:
                if isinstance(value, (int, float)) and isinstance(child[key], (int, float)):
                    # Average numeric values
                    child[key] = (child[key] + value) / 2
                elif isinstance(value, dict) and isinstance(child[key], dict):
                    # Combine nested structures
                    child[key] = self._combine_nested_structures(child[key], value)
            else:
                child[key] = value
        
        return child
    
    def _combine_nested_structures(self, struct1: Dict[str, Any], 
                                  struct2: Dict[str, Any]) -> Dict[str, Any]:
        """Combine nested rule structures"""
        combined = struct1.copy()
        
        for key, value in struct2.items():
            if key in combined:
                if isinstance(value, (int, float)) and isinstance(combined[key], (int, float)):
                    combined[key] = (combined[key] + value) / 2
                elif isinstance(value, dict) and isinstance(combined[key], dict):
                    combined[key] = self._combine_nested_structures(combined[key], value)
            else:
                combined[key] = value
        
        return combined
    
    def _calculate_complexity_penalty(self, individual: Dict[str, Any]) -> float:
        """Calculate complexity penalty for individual"""
        penalty = 0.0
        
        # Count number of parameters
        param_count = 0
        for value in individual.values():
            if isinstance(value, (int, float)):
                param_count += 1
            elif isinstance(value, dict):
                param_count += self._count_nested_params(value)
        
        # Penalty increases with parameter count
        penalty = param_count * 0.01
        
        return penalty
    
    def _count_nested_params(self, nested_dict: Dict[str, Any]) -> int:
        """Count parameters in nested dictionary"""
        count = 0
        for value in nested_dict.values():
            if isinstance(value, (int, float)):
                count += 1
            elif isinstance(value, dict):
                count += self._count_nested_params(value)
        return count
    
    def _rl_evolution(self, level: RuleLevel, 
                     current_rules: Dict[str, Any], 
                     performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """
        Reinforcement learning evolution for domain rules
        """
        # Convert rules to state representation
        state = self._rules_to_state(current_rules)
        
        # Calculate reward based on performance feedback
        reward = self._calculate_evolution_reward(performance_feedback)
        
        # Update rule parameters using RL
        updated_state = self._rl_update(state, reward)
        
        # Convert back to rules
        evolved_rules = self._state_to_rules(updated_state)
        
        return evolved_rules
    
    def _rules_to_state(self, rules: Dict[str, Any]) -> np.ndarray:
        """Convert rules to state representation"""
        state_vector = []
        
        # Handle None case
        if rules is None:
            return np.array([0.0] * 20)  # Return default state
        
        for key, value in rules.items():
            if value is None:
                state_vector.append(0.0)
            elif isinstance(value, (int, float)):
                state_vector.append(value)
            elif isinstance(value, dict):
                # Flatten nested dictionary
                nested_values = self._flatten_dict(value)
                state_vector.extend(nested_values)
            elif isinstance(value, list):
                # Convert list to numeric values
                for item in value:
                    if item is None:
                        state_vector.append(0.0)
                    elif isinstance(item, (int, float)):
                        state_vector.append(item)
                    else:
                        state_vector.append(0.0)
            else:
                # Convert other types to numeric
                state_vector.append(0.0)
        
        # Pad or truncate to fixed size
        target_size = 20
        if len(state_vector) < target_size:
            state_vector.extend([0.0] * (target_size - len(state_vector)))
        elif len(state_vector) > target_size:
            state_vector = state_vector[:target_size]
        
        return np.array(state_vector)
    
    def _flatten_dict(self, nested_dict: Dict[str, Any]) -> List[float]:
        """Flatten nested dictionary to list of numeric values"""
        values = []
        
        # Handle None case
        if nested_dict is None:
            return [0.0] * 5  # Return default values
        
        for value in nested_dict.values():
            if value is None:
                values.append(0.0)
            elif isinstance(value, (int, float)):
                values.append(float(value))
            elif isinstance(value, dict):
                values.extend(self._flatten_dict(value))
            elif isinstance(value, list):
                for item in value:
                    if item is None:
                        values.append(0.0)
                    elif isinstance(item, (int, float)):
                        values.append(float(item))
                    else:
                        values.append(0.0)
            else:
                values.append(0.0)
        
        return values
    
    def _calculate_evolution_reward(self, performance_feedback: Dict[str, float]) -> float:
        """Calculate reward for rule evolution"""
        reward = 0.0
        
        # Weight by performance metrics
        weights = {
            'accuracy': 0.3,
            'cost_efficiency': 0.25,
            'processing_speed': 0.2,
            'stability': 0.15,
            'domain_specialization': 0.1
        }
        
        for metric, weight in weights.items():
            if metric in performance_feedback:
                reward += performance_feedback[metric] * weight
        
        return reward
    
    def _rl_update(self, state: np.ndarray, reward: float) -> np.ndarray:
        """Update state using reinforcement learning"""
        # Simple Q-learning update
        learning_rate = self.config.learning_rate
        
        # Calculate state update based on reward
        if reward > 0.5:  # Good performance
            # Encourage current state
            state_update = state * (1 + learning_rate)
        else:  # Poor performance
            # Discourage current state
            state_update = state * (1 - learning_rate)
        
        # Normalize state
        state_update = np.clip(state_update, 0.0, 1.0)
        
        return state_update
    
    def _state_to_rules(self, state: np.ndarray) -> Dict[str, Any]:
        """Convert state back to rules"""
        # Simple mapping from state to rules
        rules = {
            'confidence_threshold': float(state[0]) if len(state) > 0 else 0.5,
            'model_weight': float(state[1]) if len(state) > 1 else 0.5,
            'cascade_threshold': float(state[2]) if len(state) > 2 else 0.6,
            'domain_specific_weight': float(state[3]) if len(state) > 3 else 1.0,
            'complexity_factor': float(state[4]) if len(state) > 4 else 0.5
        }
        
        return rules
    
    def _gradient_evolution(self, level: RuleLevel, 
                           current_rules: Dict[str, Any], 
                           performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """
        Gradient descent evolution for subdomain rules
        """
        # Convert rules to parameter vector
        params = self._rules_to_parameters(current_rules)
        
        # Calculate gradient
        gradient = self._calculate_gradient(params, performance_feedback)
        
        # Update parameters
        updated_params = params - self.config.learning_rate * gradient
        
        # Convert back to rules
        evolved_rules = self._parameters_to_rules(updated_params)
        
        return evolved_rules
    
    def _rules_to_parameters(self, rules: Dict[str, Any]) -> np.ndarray:
        """Convert rules to parameter vector"""
        params = []
        
        # Handle None case
        if rules is None:
            return np.array([0.5] * 5)  # Return default parameters
        
        for key, value in rules.items():
            if value is None:
                params.append(0.5)  # Default parameter value
            elif isinstance(value, (int, float)):
                params.append(float(value))
            elif isinstance(value, dict):
                # Flatten nested dictionary
                nested_params = self._flatten_dict(value)
                params.extend(nested_params)
            elif isinstance(value, list):
                # Convert list to numeric values
                for item in value:
                    if item is None:
                        params.append(0.5)
                    elif isinstance(item, (int, float)):
                        params.append(float(item))
                    else:
                        params.append(0.5)
            else:
                params.append(0.5)
        
        return np.array(params)
    
    def _calculate_gradient(self, params: np.ndarray, 
                           performance_feedback: Dict[str, float]) -> np.ndarray:
        """Calculate gradient for parameter optimization"""
        # Simple numerical gradient approximation
        epsilon = 1e-6
        gradient = np.zeros_like(params)
        
        # Calculate gradient for each parameter
        for i in range(len(params)):
            # Forward difference
            params_plus = params.copy()
            params_plus[i] += epsilon
            
            # Calculate performance difference
            perf_plus = self._evaluate_parameters(params_plus, performance_feedback)
            perf_current = self._evaluate_parameters(params, performance_feedback)
            
            gradient[i] = (perf_plus - perf_current) / epsilon
        
        return gradient
    
    def _evaluate_parameters(self, params: np.ndarray, 
                            performance_feedback: Dict[str, float]) -> float:
        """Evaluate parameter performance"""
        # Simple performance evaluation
        performance = 0.0
        
        # Weight by performance metrics
        weights = {
            'accuracy': 0.3,
            'cost_efficiency': 0.25,
            'processing_speed': 0.2,
            'stability': 0.15,
            'domain_specialization': 0.1
        }
        
        for metric, weight in weights.items():
            if metric in performance_feedback:
                performance += performance_feedback[metric] * weight
        
        # Add parameter complexity penalty
        complexity_penalty = np.sum(np.abs(params)) * 0.01
        performance -= complexity_penalty
        
        return performance
    
    def _parameters_to_rules(self, params: np.ndarray) -> Dict[str, Any]:
        """Convert parameters back to rules"""
        # Simple mapping from parameters to rules
        rules = {}
        
        if len(params) >= 1:
            rules['confidence_threshold'] = float(np.clip(params[0], 0.0, 1.0))
        if len(params) >= 2:
            rules['model_weight'] = float(np.clip(params[1], 0.0, 1.0))
        if len(params) >= 3:
            rules['cascade_threshold'] = float(np.clip(params[2], 0.0, 1.0))
        if len(params) >= 4:
            rules['domain_specific_weight'] = float(np.clip(params[3], 0.0, 1.0))
        if len(params) >= 5:
            rules['complexity_factor'] = float(np.clip(params[4], 0.0, 1.0))
        
        # Fill remaining parameters with defaults
        while len(rules) < 5:
            rules[f'param_{len(rules)}'] = 0.5
        
        return rules
    
    def _online_evolution(self, level: RuleLevel, 
                         current_rules: Dict[str, Any], 
                         performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """
        Online learning evolution for document-specific rules
        """
        # Calculate performance improvement
        improvement = self._calculate_performance_improvement(performance_feedback)
        
        # Adaptive learning rate
        learning_rate = self._adaptive_learning_rate(improvement)
        
        # Update rules incrementally
        evolved_rules = current_rules.copy()
        for rule_key, rule_value in current_rules.items():
            if isinstance(rule_value, (int, float)):
                # Numeric rule - update based on performance
                if improvement > 0:
                    evolved_rules[rule_key] = rule_value * (1 + learning_rate)
                else:
                    evolved_rules[rule_key] = rule_value * (1 - learning_rate)
            elif isinstance(rule_value, dict):
                # Nested rule - recursive update
                evolved_rules[rule_key] = self._update_nested_rule(rule_value, learning_rate, improvement)
        
        return evolved_rules
    
    def _simulated_annealing_evolution(self, level: RuleLevel, 
                                     current_rules: Dict[str, Any], 
                                     performance_feedback: Dict[str, float]) -> Dict[str, Any]:
        """
        Simulated annealing evolution
        """
        best_rules = current_rules.copy()
        best_performance = self._evaluate_performance(current_rules, performance_feedback)
        
        temperature = self.config.temperature
        
        for iteration in range(self.config.generations):
            # Generate neighbor solution
            neighbor_rules = self._generate_neighbor(current_rules)
            neighbor_performance = self._evaluate_performance(neighbor_rules, performance_feedback)
            
            # Accept or reject based on temperature
            if self._accept_solution(best_performance, neighbor_performance, temperature):
                current_rules = neighbor_rules
                if neighbor_performance > best_performance:
                    best_rules = neighbor_rules
                    best_performance = neighbor_performance
            
            # Cool down
            temperature *= self.config.cooling_rate
        
        return best_rules
    
    def _get_rules_at_level(self, level: RuleLevel, 
                           domain: Optional[str] = None, 
                           subdomain: Optional[str] = None) -> Dict[str, Any]:
        """Get rules at a specific hierarchy level"""
        if level == RuleLevel.GLOBAL:
            return self.rule_hierarchy[level]
        elif level == RuleLevel.DOMAIN and domain:
            return self.rule_hierarchy[level][domain]
        elif level == RuleLevel.SUBDOMAIN and domain and subdomain:
            return self.rule_hierarchy[level][domain][subdomain]
        elif level == RuleLevel.DOCUMENT and domain:
            return self.rule_hierarchy[level][domain]
        else:
            # Return default rules if not found
            return {
                'confidence_threshold': 0.5,
                'model_weight': 0.5,
                'cascade_threshold': 0.6,
                'domain_specific_weight': 1.0,
                'complexity_factor': 0.5
            }
    
    def _update_rules_at_level(self, level: RuleLevel, 
                              rules: Dict[str, Any], 
                              domain: Optional[str] = None, 
                              subdomain: Optional[str] = None):
        """Update rules at a specific hierarchy level"""
        if level == RuleLevel.GLOBAL:
            self.rule_hierarchy[level].update(rules)
        elif level == RuleLevel.DOMAIN and domain:
            self.rule_hierarchy[level][domain].update(rules)
        elif level == RuleLevel.SUBDOMAIN and domain and subdomain:
            self.rule_hierarchy[level][domain][subdomain].update(rules)
        elif level == RuleLevel.DOCUMENT and domain:
            self.rule_hierarchy[level][domain].update(rules)
    
    def _track_evolution(self, level: RuleLevel, 
                        domain: Optional[str], 
                        subdomain: Optional[str],
                        old_rules: Dict[str, Any], 
                        new_rules: Dict[str, Any], 
                        performance_feedback: Dict[str, float]):
        """Track evolution history"""
        evolution_record = {
            'timestamp': datetime.utcnow(),
            'level': level.value,
            'domain': domain,
            'subdomain': subdomain,
            'old_rules': old_rules,
            'new_rules': new_rules,
            'performance_feedback': performance_feedback,
            'evolution_count': self._get_evolution_count(level, domain, subdomain)
        }
        
        key = f"{level.value}_{domain}_{subdomain}"
        self.evolution_history[key].append(evolution_record)
    
    def _get_evolution_count(self, level: RuleLevel, 
                            domain: Optional[str], 
                            subdomain: Optional[str]) -> int:
        """Get evolution count for a specific level"""
        key = f"{level.value}_{domain}_{subdomain}"
        return len(self.evolution_history[key])
    
    def synchronize_rules(self, cross_domain_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Novel method: Synchronize rules across domains
        """
        synchronized_rules = {}
        
        # Find common patterns across domains
        common_patterns = self._find_common_patterns(cross_domain_results)
        
        # Apply common patterns to global rules
        synchronized_rules['global'] = common_patterns
        
        # Domain-specific adaptations
        for domain, domain_rules in cross_domain_results.items():
            synchronized_rules[domain] = self._adapt_domain_rules(domain_rules, common_patterns)
        
        return synchronized_rules
    
    def _find_common_patterns(self, cross_domain_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Find common patterns across domain results"""
        if not cross_domain_results:
            return {}
        
        # Extract all rule keys
        all_keys = set()
        for domain_rules in cross_domain_results.values():
            all_keys.update(domain_rules.keys())
        
        common_patterns = {}
        for key in all_keys:
            values = []
            for domain_rules in cross_domain_results.values():
                if key in domain_rules:
                    values.append(domain_rules[key])
            
            if values:
                # Calculate common pattern (e.g., average for numeric values)
                if all(isinstance(v, (int, float)) for v in values):
                    common_patterns[key] = np.mean(values)
                elif all(isinstance(v, str) for v in values):
                    # Most common string value
                    common_patterns[key] = max(set(values), key=values.count)
                else:
                    # Mixed types - use most common
                    common_patterns[key] = max(set(values), key=values.count)
        
        return common_patterns
    
    def _adapt_domain_rules(self, domain_rules: Dict[str, Any], 
                           common_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt domain rules based on common patterns"""
        adapted_rules = domain_rules.copy()
        
        for key, common_value in common_patterns.items():
            if key in adapted_rules:
                # Blend domain-specific and common patterns
                if isinstance(common_value, (int, float)) and isinstance(adapted_rules[key], (int, float)):
                    adapted_rules[key] = 0.7 * adapted_rules[key] + 0.3 * common_value
                else:
                    # Use domain-specific value with common pattern influence
                    adapted_rules[key] = adapted_rules[key]
        
        return adapted_rules
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """Get comprehensive evolution statistics"""
        stats = {
            'total_evolutions': sum(len(history) for history in self.evolution_history.values()),
            'level_evolutions': {},
            'convergence_status': dict(self.convergence_status),
            'current_generation': self.current_generation,
            'evolution_active': self.evolution_active
        }
        
        # Level-specific statistics
        for level in RuleLevel:
            level_key = level.value
            level_evolutions = [h for k, h in self.evolution_history.items() if k.startswith(level_key)]
            stats['level_evolutions'][level_key] = len(level_evolutions)
        
        return stats
    
    def save_evolution_state(self, filepath: str):
        """Save evolution state to file"""
        state = {
            'rule_hierarchy': dict(self.rule_hierarchy),
            'evolution_strategies': {level.value: strategy.value for level, strategy in self.evolution_strategies.items()},
            'evolution_history': dict(self.evolution_history),
            'convergence_status': dict(self.convergence_status),
            'current_generation': self.current_generation,
            'evolution_active': self.evolution_active,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info("Evolution state saved", filepath=filepath)
    
    def load_evolution_state(self, filepath: str):
        """Load evolution state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore state
        self.rule_hierarchy = state['rule_hierarchy']
        self.evolution_history = defaultdict(list, state['evolution_history'])
        self.convergence_status = defaultdict(bool, state['convergence_status'])
        self.current_generation = state['current_generation']
        self.evolution_active = state['evolution_active']
        
        logger.info("Evolution state loaded", filepath=filepath)
