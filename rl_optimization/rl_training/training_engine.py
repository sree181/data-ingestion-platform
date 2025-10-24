"""
RL Training Engine for Multi-Objective Optimization
Orchestrates the training process and manages the RL agent
"""

import os
import json
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import structlog
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

from rl_agent import MultiObjectiveRLAgent, RLState, RLAction, RLReward
# from data_collection.feature_extractor import DocumentFeatures, ClassificationOutcome
from monitoring.training_monitor import TrainingMonitor, create_training_monitor
from optimization import create_optimization_integration
from security import create_security_manager, create_data_protection_manager

logger = structlog.get_logger(__name__)

class RLTrainingEngine:
    """
    Main training engine for the RL optimization system
    """
    
    def __init__(self, 
                 training_data_path: str,
                 output_dir: str = "rl_optimization/training_results",
                 episodes: int = 1000,
                 max_steps_per_episode: int = 100,
                 evaluation_frequency: int = 50,
                 save_frequency: int = 100,
                 enable_monitoring: bool = True,
                 monitoring_output_dir: str = "monitoring_output"):
        
        self.training_data_path = training_data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.episodes = episodes
        self.max_steps_per_episode = max_steps_per_episode
        self.evaluation_frequency = evaluation_frequency
        self.save_frequency = save_frequency
        
        # Initialize RL agent
        self.agent = MultiObjectiveRLAgent()
        
        # Initialize monitoring
        self.monitor = create_training_monitor(
            enable_monitoring=enable_monitoring,
            output_dir=monitoring_output_dir
        )
        
        # Initialize optimization
        self.optimization = create_optimization_integration(
            enable_caching=True,
            enable_performance_optimization=True,
            enable_model_optimization=True,
            cache_size_mb=500
        )
        
        # Initialize security
        self.security_manager = create_security_manager(
            enable_encryption=True,
            enable_authentication=True,
            enable_authorization=True,
            enable_audit_logging=True,
            enable_compliance=True
        )
        
        # Initialize data protection
        self.data_protection = create_data_protection_manager(
            enable_anonymization=True,
            enable_masking=True,
            enable_differential_privacy=True,
            enable_retention=True,
            enable_classification=True
        )
        
        # Load training data
        self.training_data = self._load_training_data()
        
        # Training metrics
        self.training_metrics = {
            'episode_rewards': [],
            'episode_lengths': [],
            'accuracy_scores': [],
            'cost_efficiency_scores': [],
            'processing_speed_scores': [],
            'stability_scores': [],
            'domain_specialization_scores': [],
            'pareto_front_sizes': [],
            'rule_config_evolution': []
        }
        
        # Performance tracking
        self.best_performance = {
            'accuracy': 0.0,
            'cost_efficiency': 0.0,
            'processing_speed': 0.0,
            'stability': 0.0,
            'domain_specialization': 0.0,
            'total_reward': 0.0
        }
        
        logger.info("RL Training Engine initialized", 
                   episodes=episodes, 
                   training_data_size=len(self.training_data))
    
    def _load_training_data(self) -> List[Dict[str, Any]]:
        """Load training data from JSON files"""
        training_data = []
        
        # Load all training data files
        data_dir = Path(self.training_data_path)
        for file_path in data_dir.glob("real_pubmed_training_data_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    training_data.extend(data)
                logger.info("Loaded training data", file=str(file_path), size=len(data))
            except Exception as e:
                logger.error("Failed to load training data", file=str(file_path), error=str(e))
        
        logger.info("Total training data loaded", size=len(training_data))
        return training_data
    
    def train(self):
        """Main training loop"""
        logger.info("Starting RL training", episodes=self.episodes)
        
        # Start monitoring session
        session_id = f"training_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.monitor.start_training_session(session_id, {
            'episodes': self.episodes,
            'max_steps_per_episode': self.max_steps_per_episode,
            'evaluation_frequency': self.evaluation_frequency,
            'save_frequency': self.save_frequency
        })
        
        # Start optimization
        self.optimization.start_optimization()
        
        try:
            for episode in range(self.episodes):
                episode_reward, episode_length = self._run_episode(episode)
                
                # Store metrics
                self.training_metrics['episode_rewards'].append(episode_reward)
                self.training_metrics['episode_lengths'].append(episode_length)
                
                # Record episode in monitoring
                self.monitor.record_episode(
                    episode_idx=episode,
                    reward=episode_reward,
                    length=episode_length,
                    loss=self.agent.get_training_loss() if hasattr(self.agent, 'get_training_loss') else 0.0,
                    epsilon=self.agent.epsilon,
                    memory_size=len(self.agent.memory) if hasattr(self.agent, 'memory') else 0,
                    domain="general_medicine"
                )
                
                # Train the agent
                self.agent.train()
                
                # Evaluation
                if episode % self.evaluation_frequency == 0:
                    self._evaluate_agent(episode)
                
                # Save model
                if episode % self.save_frequency == 0:
                    self._save_checkpoint(episode)
                
                # Log progress
                if episode % 10 == 0:
                    logger.info("Training progress", 
                               episode=episode,
                               avg_reward=np.mean(self.training_metrics['episode_rewards'][-10:]),
                               epsilon=self.agent.epsilon)
            
            # Final evaluation and saving
            self._final_evaluation()
            self._save_final_model()
            self._generate_training_report()
            
            logger.info("RL training completed")
            
        finally:
            # Stop monitoring session
            self.monitor.stop_training_session()
            
            # Stop optimization
            self.optimization.stop_optimization()
    
    def _run_episode(self, episode: int) -> Tuple[float, int]:
        """Run a single training episode"""
        episode_reward = 0.0
        episode_length = 0
        
        # Sample random documents for this episode
        episode_documents = np.random.choice(
            self.training_data, 
            size=min(self.max_steps_per_episode, len(self.training_data)),
            replace=False
        )
        
        # Optimize episode documents
        episode_documents = self.optimization.optimize_training_data(episode_documents)
        
        # Apply data protection
        episode_documents = [
            self.data_protection.protect_data(doc, "medium") 
            for doc in episode_documents
        ]
        
        for step, document in enumerate(episode_documents):
            # Extract features and create state
            features = document['features']
            outcome = document['outcome']
            
            # Create current performance metrics (simulated)
            current_performance = self._get_current_performance()
            
            # Create RL state
            state = self.agent.get_state(features, current_performance)
            
            # Select action
            action = self.agent.select_action(state)
            
            # Apply action and get outcome
            reward = self._simulate_classification_outcome(features, action, outcome)
            
            # Create next state
            next_state = self.agent.get_state(features, current_performance)
            
            # Store experience
            self.agent.store_experience(state, action, reward, next_state, step == len(episode_documents) - 1)
            
            # Update rule configuration
            self.agent.update_rule_config(action)
            
            # Accumulate rewards
            episode_reward += reward.total_reward
            episode_length += 1
            
            # Update performance tracking
            self._update_performance_metrics(reward)
        
        return episode_reward, episode_length
    
    def _get_current_performance(self) -> Dict[str, float]:
        """Get current performance metrics"""
        return {
            'accuracy': np.mean(self.training_metrics['accuracy_scores'][-10:]) if self.training_metrics['accuracy_scores'] else 0.5,
            'cost_efficiency': np.mean(self.training_metrics['cost_efficiency_scores'][-10:]) if self.training_metrics['cost_efficiency_scores'] else 0.5,
            'processing_speed': np.mean(self.training_metrics['processing_speed_scores'][-10:]) if self.training_metrics['processing_speed_scores'] else 0.5,
            'stability': np.mean(self.training_metrics['stability_scores'][-10:]) if self.training_metrics['stability_scores'] else 0.5,
            'domain_specialization': np.mean(self.training_metrics['domain_specialization_scores'][-10:]) if self.training_metrics['domain_specialization_scores'] else 0.5
        }
    
    def _simulate_classification_outcome(self, features: Dict[str, Any], 
                                       action: RLAction, 
                                       true_outcome: Dict[str, Any]) -> RLReward:
        """Simulate classification outcome based on action and features"""
        
        # Simulate classification based on action parameters
        confidence = self._calculate_confidence(features, action)
        is_correct = self._determine_correctness(features, true_outcome, action)
        processing_time = self._calculate_processing_time(action)
        cost = self._calculate_cost(action)
        
        # Create outcome dictionary
        outcome = {
            'is_correct': is_correct,
            'confidence': confidence,
            'processing_time_ms': processing_time,
            'cost_efficiency': cost / max(processing_time, 1),
            'models_used': action.model_selection
        }
        
        # Calculate reward
        state = self.agent.get_state(features, self._get_current_performance())
        reward = self.agent.calculate_reward(state, action, state, outcome)
        
        return reward
    
    def _calculate_confidence(self, features: Dict[str, Any], action: RLAction) -> float:
        """Calculate classification confidence based on features and action"""
        base_confidence = 0.5
        
        # Adjust based on feature strength
        icsr_evidence = features.get('icsr_mesh_count', 0) / max(features.get('non_icsr_mesh_count', 1), 1)
        patient_mentions = features.get('patient_mentions', 0)
        adverse_events = features.get('adverse_event_mentions', 0)
        
        # Confidence calculation
        confidence = base_confidence + (icsr_evidence * 0.2) + (patient_mentions * 0.05) + (adverse_events * 0.1)
        
        # Apply action modifications
        confidence *= action.confidence_threshold
        
        return min(max(confidence, 0.0), 1.0)
    
    def _determine_correctness(self, features: Dict[str, Any], 
                              true_outcome: Dict[str, Any], 
                              action: RLAction) -> bool:
        """Determine if classification is correct"""
        predicted = true_outcome.get('predicted_classification', 'Unknown')
        true_class = true_outcome.get('true_classification', 'Unknown')
        
        # If we have ground truth, use it
        if true_class != 'Unknown':
            return predicted == true_class
        
        # Otherwise, simulate based on features and action
        # Higher confidence actions are more likely to be correct
        confidence_factor = action.confidence_threshold
        
        # Domain-specific accuracy
        domain = features.get('domain', 'general_medicine')
        if domain in ['hepatology', 'cardiology', 'neurology']:
            accuracy_base = 0.8
        else:
            accuracy_base = 0.7
        
        # Simulate correctness
        return np.random.random() < (accuracy_base * confidence_factor)
    
    def _calculate_processing_time(self, action: RLAction) -> float:
        """Calculate processing time based on action"""
        base_time = 1000  # 1 second base
        
        # Model selection affects time
        model_penalty = len(action.model_selection) * 500
        
        # Cost budget affects time (higher budget = faster processing)
        cost_factor = 1.0 - (action.cost_budget * 100)
        
        return base_time + model_penalty + (cost_factor * 2000)
    
    def _calculate_cost(self, action: RLAction) -> float:
        """Calculate cost based on action"""
        base_cost = 0.001
        
        # Model selection affects cost
        model_cost = len(action.model_selection) * 0.002
        
        # Cost budget directly affects cost
        cost_budget_factor = action.cost_budget
        
        return base_cost + model_cost + cost_budget_factor
    
    def _update_performance_metrics(self, reward: RLReward):
        """Update performance metrics"""
        self.training_metrics['accuracy_scores'].append(reward.accuracy_reward)
        self.training_metrics['cost_efficiency_scores'].append(reward.cost_efficiency_reward)
        self.training_metrics['processing_speed_scores'].append(reward.processing_speed_reward)
        self.training_metrics['stability_scores'].append(reward.stability_reward)
        self.training_metrics['domain_specialization_scores'].append(reward.domain_specialization_reward)
        
        # Update best performance
        if reward.total_reward > self.best_performance['total_reward']:
            self.best_performance.update({
                'accuracy': reward.accuracy_reward,
                'cost_efficiency': reward.cost_efficiency_reward,
                'processing_speed': reward.processing_speed_reward,
                'stability': reward.stability_reward,
                'domain_specialization': reward.domain_specialization_reward,
                'total_reward': reward.total_reward
            })
    
    def _evaluate_agent(self, episode: int):
        """Evaluate agent performance"""
        logger.info("Evaluating agent", episode=episode)
        
        # Get Pareto-optimal solutions
        pareto_solutions = self.agent.get_pareto_optimal_solutions()
        self.training_metrics['pareto_front_sizes'].append(len(pareto_solutions))
        
        # Store rule configuration evolution
        self.training_metrics['rule_config_evolution'].append({
            'episode': episode,
            'config': self.agent.current_rule_config.copy()
        })
        
        # Log evaluation results
        avg_reward = np.mean(self.training_metrics['episode_rewards'][-10:])
        logger.info("Evaluation results", 
                   episode=episode,
                   avg_reward=avg_reward,
                   pareto_solutions=len(pareto_solutions),
                   epsilon=self.agent.epsilon)
    
    def _save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        checkpoint_path = self.output_dir / f"checkpoint_episode_{episode}.pt"
        self.agent.save_model(str(checkpoint_path))
        
        # Save training metrics
        metrics_path = self.output_dir / f"metrics_episode_{episode}.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.training_metrics, f, indent=2, default=str)
        
        logger.info("Checkpoint saved", episode=episode, path=str(checkpoint_path))
    
    def _final_evaluation(self):
        """Perform final evaluation"""
        logger.info("Performing final evaluation")
        
        # Test on held-out data
        test_performance = self._test_on_held_out_data()
        
        # Generate final metrics
        final_metrics = {
            'final_performance': test_performance,
            'best_performance': self.best_performance,
            'training_metrics': self.training_metrics,
            'rule_config_evolution': self.training_metrics['rule_config_evolution']
        }
        
        # Save final metrics
        with open(self.output_dir / "final_metrics.json", 'w') as f:
            json.dump(final_metrics, f, indent=2, default=str)
        
        logger.info("Final evaluation completed", performance=test_performance)
    
    def _test_on_held_out_data(self) -> Dict[str, float]:
        """Test agent on held-out data"""
        # Use last 20% of training data as test set
        test_size = int(len(self.training_data) * 0.2)
        test_data = self.training_data[-test_size:]
        
        test_metrics = {
            'accuracy': 0.0,
            'cost_efficiency': 0.0,
            'processing_speed': 0.0,
            'stability': 0.0,
            'domain_specialization': 0.0,
            'total_reward': 0.0
        }
        
        for document in test_data:
            features = document['features']
            outcome = document['outcome']
            
            # Get current performance
            current_performance = self._get_current_performance()
            
            # Create state and select action
            state = self.agent.get_state(features, current_performance)
            action = self.agent.select_action(state)
            
            # Simulate outcome
            reward = self._simulate_classification_outcome(features, action, outcome)
            
            # Accumulate metrics
            test_metrics['accuracy'] += reward.accuracy_reward
            test_metrics['cost_efficiency'] += reward.cost_efficiency_reward
            test_metrics['processing_speed'] += reward.processing_speed_reward
            test_metrics['stability'] += reward.stability_reward
            test_metrics['domain_specialization'] += reward.domain_specialization_reward
            test_metrics['total_reward'] += reward.total_reward
        
        # Average the metrics
        for key in test_metrics:
            test_metrics[key] /= len(test_data)
        
        return test_metrics
    
    def _save_final_model(self):
        """Save the final trained model"""
        final_model_path = self.output_dir / "final_model.pt"
        self.agent.save_model(str(final_model_path))
        
        logger.info("Final model saved", path=str(final_model_path))
    
    def _generate_training_report(self):
        """Generate comprehensive training report"""
        logger.info("Generating training report")
        
        # Create plots
        self._create_training_plots()
        
        # Generate summary report
        report = {
            'training_summary': {
                'total_episodes': self.episodes,
                'total_training_data': len(self.training_data),
                'final_epsilon': self.agent.epsilon,
                'best_performance': self.best_performance
            },
            'training_metrics': self.training_metrics,
            'rule_configuration': self.agent.current_rule_config,
            'objective_weights': self.agent.objective_weights
        }
        
        # Save report
        with open(self.output_dir / "training_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Training report generated", path=str(self.output_dir / "training_report.json"))
    
    def _create_training_plots(self):
        """Create training visualization plots"""
        try:
            # Episode rewards plot
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 3, 1)
            plt.plot(self.training_metrics['episode_rewards'])
            plt.title('Episode Rewards')
            plt.xlabel('Episode')
            plt.ylabel('Reward')
            
            plt.subplot(2, 3, 2)
            plt.plot(self.training_metrics['accuracy_scores'])
            plt.title('Accuracy Scores')
            plt.xlabel('Step')
            plt.ylabel('Accuracy')
            
            plt.subplot(2, 3, 3)
            plt.plot(self.training_metrics['cost_efficiency_scores'])
            plt.title('Cost Efficiency Scores')
            plt.xlabel('Step')
            plt.ylabel('Cost Efficiency')
            
            plt.subplot(2, 3, 4)
            plt.plot(self.training_metrics['processing_speed_scores'])
            plt.title('Processing Speed Scores')
            plt.xlabel('Step')
            plt.ylabel('Processing Speed')
            
            plt.subplot(2, 3, 5)
            plt.plot(self.training_metrics['stability_scores'])
            plt.title('Stability Scores')
            plt.xlabel('Step')
            plt.ylabel('Stability')
            
            plt.subplot(2, 3, 6)
            plt.plot(self.training_metrics['domain_specialization_scores'])
            plt.title('Domain Specialization Scores')
            plt.xlabel('Step')
            plt.ylabel('Domain Specialization')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / 'training_plots.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Training plots created", path=str(self.output_dir / 'training_plots.png'))
            
        except Exception as e:
            logger.error("Failed to create training plots", error=str(e))
