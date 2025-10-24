"""
Rule Configuration Generator and Optimizer
Generates and optimizes rule configurations for the classification system
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import structlog
from pathlib import Path
import random

logger = structlog.get_logger(__name__)

@dataclass
class RuleConfiguration:
    """Rule configuration for the classification system"""
    confidence_thresholds: Dict[str, float]
    model_weights: Dict[str, float]
    cascade_thresholds: Dict[str, float]
    domain_specific_rules: Dict[str, Dict[str, Any]]
    keyword_weights: Dict[str, float]
    mesh_term_weights: Dict[str, float]
    publication_type_weights: Dict[str, float]

class RuleConfigurationGenerator:
    """
    Generates rule configurations for RL optimization
    """
    
    def __init__(self, base_config_path: Optional[str] = None):
        self.base_config = self._load_base_config(base_config_path)
        self.generation_history = []
        
        logger.info("Rule Configuration Generator initialized")
    
    def _load_base_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load base configuration from file or create default"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default base configuration
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
                'hepatology': {
                    'weight_multiplier': 1.0,
                    'confidence_boost': 0.0,
                    'special_keywords': ['liver', 'hepatotoxicity', 'hepatic']
                },
                'cardiology': {
                    'weight_multiplier': 1.0,
                    'confidence_boost': 0.0,
                    'special_keywords': ['cardiac', 'heart', 'cardiovascular']
                },
                'neurology': {
                    'weight_multiplier': 1.0,
                    'confidence_boost': 0.0,
                    'special_keywords': ['neurological', 'brain', 'neural']
                },
                'general_medicine': {
                    'weight_multiplier': 1.0,
                    'confidence_boost': 0.0,
                    'special_keywords': []
                }
            },
            'keyword_weights': {
                'patient': 0.3,
                'case': 0.4,
                'adverse': 0.5,
                'reaction': 0.4,
                'toxicity': 0.6,
                'injury': 0.5,
                'overdose': 0.7,
                'severe': 0.4,
                'acute': 0.3,
                'chronic': 0.2
            },
            'mesh_term_weights': {
                'Case Reports': 0.8,
                'Drug-Related Side Effects and Adverse Reactions': 0.9,
                'Chemical and Drug Induced Liver Injury': 0.9,
                'Adverse Drug Reaction Reporting Systems': 0.8,
                'Product Surveillance, Postmarketing': 0.7,
                'Pharmacovigilance': 0.8,
                'Drug Toxicity': 0.8,
                'Drug Hypersensitivity': 0.8,
                'Drug-Induced Liver Injury': 0.9,
                'Stevens-Johnson Syndrome': 0.9,
                'Anaphylaxis': 0.9,
                'Drug Eruptions': 0.8
            },
            'publication_type_weights': {
                'Case Reports': 0.9,
                'Journal Article': 0.3,
                'Review': 0.2,
                'Randomized Controlled Trial': 0.1,
                'Clinical Trial': 0.2,
                'Multicenter Study': 0.1,
                'Systematic Review': 0.1,
                'Meta-Analysis': 0.1
            }
        }
    
    def generate_random_config(self) -> RuleConfiguration:
        """Generate a random rule configuration"""
        config = RuleConfiguration(
            confidence_thresholds={
                'rule_based': random.uniform(0.6, 0.9),
                'bert': random.uniform(0.5, 0.8),
                'llm': random.uniform(0.4, 0.7)
            },
            model_weights={
                'rule_based': random.uniform(0.2, 0.6),
                'bert': random.uniform(0.2, 0.4),
                'llm': random.uniform(0.2, 0.4)
            },
            cascade_thresholds={
                'rule_to_bert': random.uniform(0.5, 0.8),
                'bert_to_llm': random.uniform(0.4, 0.7)
            },
            domain_specific_rules=self._generate_domain_rules(),
            keyword_weights=self._generate_keyword_weights(),
            mesh_term_weights=self._generate_mesh_weights(),
            publication_type_weights=self._generate_publication_weights()
        )
        
        # Normalize model weights
        total_weight = sum(config.model_weights.values())
        for model in config.model_weights:
            config.model_weights[model] /= total_weight
        
        self.generation_history.append({
            'timestamp': datetime.utcnow(),
            'config': config,
            'type': 'random'
        })
        
        return config
    
    def generate_mutated_config(self, base_config: RuleConfiguration, 
                            mutation_rate: float = 0.1) -> RuleConfiguration:
        """Generate a mutated version of a base configuration"""
        config = RuleConfiguration(
            confidence_thresholds=self._mutate_thresholds(
                base_config.confidence_thresholds, mutation_rate
            ),
            model_weights=self._mutate_weights(
                base_config.model_weights, mutation_rate
            ),
            cascade_thresholds=self._mutate_thresholds(
                base_config.cascade_thresholds, mutation_rate
            ),
            domain_specific_rules=self._mutate_domain_rules(
                base_config.domain_specific_rules, mutation_rate
            ),
            keyword_weights=self._mutate_weights(
                base_config.keyword_weights, mutation_rate
            ),
            mesh_term_weights=self._mutate_weights(
                base_config.mesh_term_weights, mutation_rate
            ),
            publication_type_weights=self._mutate_weights(
                base_config.publication_type_weights, mutation_rate
            )
        )
        
        # Normalize model weights
        total_weight = sum(config.model_weights.values())
        for model in config.model_weights:
            config.model_weights[model] /= total_weight
        
        self.generation_history.append({
            'timestamp': datetime.utcnow(),
            'config': config,
            'type': 'mutated',
            'base_config': base_config
        })
        
        return config
    
    def generate_crossover_config(self, config1: RuleConfiguration, 
                                config2: RuleConfiguration) -> RuleConfiguration:
        """Generate a crossover configuration from two parent configurations"""
        config = RuleConfiguration(
            confidence_thresholds=self._crossover_thresholds(
                config1.confidence_thresholds, config2.confidence_thresholds
            ),
            model_weights=self._crossover_weights(
                config1.model_weights, config2.model_weights
            ),
            cascade_thresholds=self._crossover_thresholds(
                config1.cascade_thresholds, config2.cascade_thresholds
            ),
            domain_specific_rules=self._crossover_domain_rules(
                config1.domain_specific_rules, config2.domain_specific_rules
            ),
            keyword_weights=self._crossover_weights(
                config1.keyword_weights, config2.keyword_weights
            ),
            mesh_term_weights=self._crossover_weights(
                config1.mesh_term_weights, config2.mesh_term_weights
            ),
            publication_type_weights=self._crossover_weights(
                config1.publication_type_weights, config2.publication_type_weights
            )
        )
        
        # Normalize model weights
        total_weight = sum(config.model_weights.values())
        for model in config.model_weights:
            config.model_weights[model] /= total_weight
        
        self.generation_history.append({
            'timestamp': datetime.utcnow(),
            'config': config,
            'type': 'crossover',
            'parent1': config1,
            'parent2': config2
        })
        
        return config
    
    def _generate_domain_rules(self) -> Dict[str, Dict[str, Any]]:
        """Generate domain-specific rules"""
        domains = ['hepatology', 'cardiology', 'neurology', 'general_medicine']
        domain_rules = {}
        
        for domain in domains:
            domain_rules[domain] = {
                'weight_multiplier': random.uniform(0.8, 1.2),
                'confidence_boost': random.uniform(-0.1, 0.1),
                'special_keywords': random.sample(
                    ['liver', 'cardiac', 'neural', 'patient', 'case', 'adverse'],
                    random.randint(0, 3)
                )
            }
        
        return domain_rules
    
    def _generate_keyword_weights(self) -> Dict[str, float]:
        """Generate keyword weights"""
        keywords = [
            'patient', 'case', 'adverse', 'reaction', 'toxicity', 'injury',
            'overdose', 'severe', 'acute', 'chronic', 'drug', 'medication',
            'treatment', 'therapy', 'dose', 'dosage', 'mg', 'tablet'
        ]
        
        return {keyword: random.uniform(0.1, 0.8) for keyword in keywords}
    
    def _generate_mesh_weights(self) -> Dict[str, float]:
        """Generate MeSH term weights"""
        mesh_terms = [
            'Case Reports', 'Drug-Related Side Effects and Adverse Reactions',
            'Chemical and Drug Induced Liver Injury', 'Adverse Drug Reaction Reporting Systems',
            'Product Surveillance, Postmarketing', 'Pharmacovigilance',
            'Drug Toxicity', 'Drug Hypersensitivity', 'Drug-Induced Liver Injury',
            'Stevens-Johnson Syndrome', 'Anaphylaxis', 'Drug Eruptions'
        ]
        
        return {term: random.uniform(0.3, 0.9) for term in mesh_terms}
    
    def _generate_publication_weights(self) -> Dict[str, float]:
        """Generate publication type weights"""
        pub_types = [
            'Case Reports', 'Journal Article', 'Review', 'Randomized Controlled Trial',
            'Clinical Trial', 'Multicenter Study', 'Systematic Review', 'Meta-Analysis'
        ]
        
        return {pub_type: random.uniform(0.1, 0.9) for pub_type in pub_types}
    
    def _mutate_thresholds(self, thresholds: Dict[str, float], 
                          mutation_rate: float) -> Dict[str, float]:
        """Mutate threshold values"""
        mutated = {}
        for key, value in thresholds.items():
            if random.random() < mutation_rate:
                # Add Gaussian noise
                noise = np.random.normal(0, 0.1)
                mutated[key] = max(0.0, min(1.0, value + noise))
            else:
                mutated[key] = value
        return mutated
    
    def _mutate_weights(self, weights: Dict[str, float], 
                       mutation_rate: float) -> Dict[str, float]:
        """Mutate weight values"""
        mutated = {}
        for key, value in weights.items():
            if random.random() < mutation_rate:
                # Add Gaussian noise
                noise = np.random.normal(0, 0.05)
                mutated[key] = max(0.0, min(1.0, value + noise))
            else:
                mutated[key] = value
        return mutated
    
    def _mutate_domain_rules(self, domain_rules: Dict[str, Dict[str, Any]], 
                           mutation_rate: float) -> Dict[str, Dict[str, Any]]:
        """Mutate domain-specific rules"""
        mutated = {}
        for domain, rules in domain_rules.items():
            if random.random() < mutation_rate:
                mutated[domain] = {
                    'weight_multiplier': max(0.5, min(1.5, 
                        rules['weight_multiplier'] + np.random.normal(0, 0.1))),
                    'confidence_boost': max(-0.2, min(0.2, 
                        rules['confidence_boost'] + np.random.normal(0, 0.05))),
                    'special_keywords': rules['special_keywords']  # Keep same for now
                }
            else:
                mutated[domain] = rules
        return mutated
    
    def _crossover_thresholds(self, thresholds1: Dict[str, float], 
                            thresholds2: Dict[str, float]) -> Dict[str, float]:
        """Crossover threshold values"""
        crossover = {}
        for key in thresholds1:
            if random.random() < 0.5:
                crossover[key] = thresholds1[key]
            else:
                crossover[key] = thresholds2[key]
        return crossover
    
    def _crossover_weights(self, weights1: Dict[str, float], 
                          weights2: Dict[str, float]) -> Dict[str, float]:
        """Crossover weight values"""
        crossover = {}
        for key in weights1:
            if random.random() < 0.5:
                crossover[key] = weights1[key]
            else:
                crossover[key] = weights2[key]
        return crossover
    
    def _crossover_domain_rules(self, rules1: Dict[str, Dict[str, Any]], 
                              rules2: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Crossover domain rules"""
        crossover = {}
        for domain in rules1:
            if random.random() < 0.5:
                crossover[domain] = rules1[domain]
            else:
                crossover[domain] = rules2[domain]
        return crossover
    
    def optimize_config(self, config: RuleConfiguration, 
                       performance_metrics: Dict[str, float],
                       optimization_steps: int = 100) -> RuleConfiguration:
        """Optimize configuration based on performance metrics"""
        best_config = config
        best_performance = self._evaluate_config(config, performance_metrics)
        
        for step in range(optimization_steps):
            # Generate mutated version
            mutated_config = self.generate_mutated_config(config, mutation_rate=0.2)
            
            # Evaluate performance
            performance = self._evaluate_config(mutated_config, performance_metrics)
            
            # Keep if better
            if performance > best_performance:
                best_config = mutated_config
                best_performance = performance
        
        logger.info("Configuration optimized", 
                   steps=optimization_steps,
                   improvement=best_performance)
        
        return best_config
    
    def _evaluate_config(self, config: RuleConfiguration, 
                        performance_metrics: Dict[str, float]) -> float:
        """Evaluate configuration performance"""
        # Simple evaluation based on confidence thresholds and weights
        confidence_score = np.mean(list(config.confidence_thresholds.values()))
        weight_balance = 1.0 - np.std(list(config.model_weights.values()))
        
        # Domain specialization score
        domain_scores = []
        for domain, rules in config.domain_specific_rules.items():
            domain_scores.append(rules['weight_multiplier'] * rules['confidence_boost'])
        domain_score = np.mean(domain_scores) if domain_scores else 0.0
        
        # Combined score
        total_score = (confidence_score * 0.4 + 
                      weight_balance * 0.3 + 
                      domain_score * 0.3)
        
        return total_score
    
    def save_config(self, config: RuleConfiguration, filepath: str):
        """Save configuration to file"""
        config_dict = {
            'confidence_thresholds': config.confidence_thresholds,
            'model_weights': config.model_weights,
            'cascade_thresholds': config.cascade_thresholds,
            'domain_specific_rules': config.domain_specific_rules,
            'keyword_weights': config.keyword_weights,
            'mesh_term_weights': config.mesh_term_weights,
            'publication_type_weights': config.publication_type_weights,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info("Configuration saved", filepath=filepath)
    
    def load_config(self, filepath: str) -> RuleConfiguration:
        """Load configuration from file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        config = RuleConfiguration(
            confidence_thresholds=config_dict['confidence_thresholds'],
            model_weights=config_dict['model_weights'],
            cascade_thresholds=config_dict['cascade_thresholds'],
            domain_specific_rules=config_dict['domain_specific_rules'],
            keyword_weights=config_dict['keyword_weights'],
            mesh_term_weights=config_dict['mesh_term_weights'],
            publication_type_weights=config_dict['publication_type_weights']
        )
        
        logger.info("Configuration loaded", filepath=filepath)
        return config
    
    def get_generation_history(self) -> List[Dict[str, Any]]:
        """Get configuration generation history"""
        return self.generation_history
