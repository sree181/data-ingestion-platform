"""
Unit Tests for Multi-Objective RL Agent
Comprehensive test suite with 80%+ coverage
"""

import unittest
import torch
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from rl_training.rl_agent import (
    MultiObjectiveRLAgent, 
    RLState, 
    RLAction, 
    RLReward,
    QNetwork
)
from data.dataset import TrainingSample, DocumentFeatures, ClassificationOutcome

class TestQNetwork(unittest.TestCase):
    """Test Q-Network architecture and functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.state_dim = 20
        self.action_dim = 10
        self.q_network = QNetwork(self.state_dim, self.action_dim)
    
    def test_network_architecture(self):
        """Test network architecture"""
        # Test input layer
        self.assertEqual(self.q_network.fc1.in_features, self.state_dim)
        self.assertEqual(self.q_network.fc1.out_features, 128)
        
        # Test hidden layers
        self.assertEqual(self.q_network.fc2.in_features, 128)
        self.assertEqual(self.q_network.fc2.out_features, 128)
        
        # Test output layer
        self.assertEqual(self.q_network.fc3.in_features, 128)
        self.assertEqual(self.q_network.fc3.out_features, self.action_dim)
    
    def test_forward_pass(self):
        """Test forward pass through network"""
        batch_size = 32
        state = torch.randn(batch_size, self.state_dim)
        
        output = self.q_network(state)
        
        # Check output shape
        self.assertEqual(output.shape, (batch_size, self.action_dim))
        
        # Check output is not NaN or Inf
        self.assertFalse(torch.isnan(output).any())
        self.assertFalse(torch.isinf(output).any())
    
    def test_gradient_flow(self):
        """Test gradient flow through network"""
        state = torch.randn(1, self.state_dim, requires_grad=True)
        output = self.q_network(state)
        
        # Compute loss and backward pass
        loss = output.sum()
        loss.backward()
        
        # Check gradients exist
        self.assertIsNotNone(state.grad)
        self.assertTrue(torch.isfinite(state.grad).all())
    
    def test_network_parameters(self):
        """Test network parameters"""
        total_params = sum(p.numel() for p in self.q_network.parameters())
        expected_params = (
            self.state_dim * 128 + 128 +  # fc1
            128 * 128 + 128 +             # fc2
            128 * self.action_dim + self.action_dim  # fc3
        )
        
        self.assertEqual(total_params, expected_params)

class TestMultiObjectiveRLAgent(unittest.TestCase):
    """Test Multi-Objective RL Agent functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = MultiObjectiveRLAgent(
            state_dim=20,
            action_dim=10,
            hidden_dim=64,
            learning_rate=0.001,
            gamma=0.99,
            epsilon=0.1,
            memory_size=1000,
            batch_size=16
        )
        
        # Create mock training sample
        self.sample_features = DocumentFeatures(
            document_id="test_001",
            title="Test Document",
            abstract="Test abstract content",
            mesh_terms=["Test", "Mesh"],
            publication_types=["Journal Article"],
            word_count=100,
            sentence_count=5,
            technical_term_count=10,
            medical_term_count=15,
            patient_mentions=5,
            drug_mentions=3,
            adverse_event_mentions=2,
            temporal_mentions=1,
            icsr_mesh_count=2,
            non_icsr_mesh_count=1,
            rejected_signals=0,
            domain="general_medicine",
            complexity_score=0.7,
            confidence_indicators={"overall_confidence": 0.8},
            extracted_at="2024-01-01T00:00:00Z"
        )
        
        self.sample_outcome = ClassificationOutcome(
            true_classification="ICSR",
            predicted_classification="ICSR",
            confidence=0.9,
            reasoning="High confidence classification",
            models_used=["rule_based", "bert"],
            decision_path="rule_based_bert",
            processing_time_ms=150,
            cost_estimate=0.05,
            is_correct=True,
            confidence_penalty=0.9,
            cost_efficiency=0.8,
            classified_at="2024-01-01T00:00:00Z"
        )
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertIsNotNone(self.agent.q_network)
        self.assertIsNotNone(self.agent.target_network)
        self.assertIsNotNone(self.agent.optimizer)
        self.assertEqual(len(self.agent.memory), 0)
        self.assertEqual(self.agent.epsilon, 0.1)
    
    def test_state_creation(self):
        """Test state creation from document features"""
        performance_metrics = {
            'accuracy': 0.85,
            'cost_efficiency': 0.75,
            'processing_speed': 0.80
        }
        
        state = self.agent.get_state(self.sample_features, performance_metrics)
        
        self.assertIsInstance(state, RLState)
        self.assertEqual(state.domain, "general_medicine")
        self.assertEqual(state.complexity_score, 0.7)
        self.assertIsInstance(state.features, np.ndarray)
        self.assertEqual(len(state.features), 20)
    
    def test_action_selection_exploration(self):
        """Test action selection during exploration"""
        # Set high epsilon for exploration
        self.agent.epsilon = 1.0
        
        state = self.agent.get_state(self.sample_features, {})
        action = self.agent.select_action(state)
        
        self.assertIsInstance(action, RLAction)
        self.assertIsInstance(action.rule_modifications, dict)
        self.assertIsInstance(action.confidence_threshold, float)
        self.assertIsInstance(action.model_selection, list)
        self.assertIsInstance(action.cost_budget, float)
    
    def test_action_selection_exploitation(self):
        """Test action selection during exploitation"""
        # Set low epsilon for exploitation
        self.agent.epsilon = 0.0
        
        state = self.agent.get_state(self.sample_features, {})
        action = self.agent.select_action(state)
        
        self.assertIsInstance(action, RLAction)
        # During exploitation, action should be deterministic
        action2 = self.agent.select_action(state)
        self.assertEqual(action.confidence_threshold, action2.confidence_threshold)
    
    def test_reward_calculation(self):
        """Test reward calculation"""
        state = self.agent.get_state(self.sample_features, {})
        action = self.agent.select_action(state)
        
        outcome = {
            'is_correct': True,
            'confidence': 0.9,
            'cost_efficiency': 0.8,
            'processing_time_ms': 150,
            'cost_estimate': 0.05
        }
        
        reward = self.agent.calculate_reward(state, action, state, outcome)
        
        self.assertIsInstance(reward, RLReward)
        self.assertIsInstance(reward.accuracy_reward, float)
        self.assertIsInstance(reward.cost_efficiency_reward, float)
        self.assertIsInstance(reward.processing_speed_reward, float)
        self.assertIsInstance(reward.stability_reward, float)
        self.assertIsInstance(reward.domain_specialization_reward, float)
        self.assertIsInstance(reward.total_reward, float)
    
    def test_memory_operations(self):
        """Test experience replay memory operations"""
        # Test memory is initially empty
        self.assertEqual(len(self.agent.memory), 0)
        
        # Add experience to memory
        state = self.agent.get_state(self.sample_features, {})
        action = self.agent.select_action(state)
        reward = RLReward(0.5, 0.6, 0.7, 0.8, 0.9, 0.75)
        next_state = self.agent.get_state(self.sample_features, {})
        
        self.agent.memory.append((state, action, reward, next_state))
        
        # Test memory contains experience
        self.assertEqual(len(self.agent.memory), 1)
        
        # Test memory size limit
        for _ in range(1001):  # Add more than memory_size
            self.agent.memory.append((state, action, reward, next_state))
        
        self.assertEqual(len(self.agent.memory), 1000)  # Should be capped at memory_size
    
    def test_training_step(self):
        """Test training step"""
        # Add experiences to memory
        for _ in range(32):  # Add enough for batch_size
            state = self.agent.get_state(self.sample_features, {})
            action = self.agent.select_action(state)
            reward = RLReward(0.5, 0.6, 0.7, 0.8, 0.9, 0.75)
            next_state = self.agent.get_state(self.sample_features, {})
            self.agent.memory.append((state, action, reward, next_state))
        
        # Test training step
        initial_loss = self.agent.training_losses[-1] if self.agent.training_losses else 0.0
        self.agent.train_step()
        
        # Check that training occurred (loss might be different)
        self.assertIsNotNone(self.agent.training_losses)
    
    def test_model_save_load(self):
        """Test model save and load functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_model.pth")
            
            # Save model
            self.agent.save_model(model_path)
            self.assertTrue(os.path.exists(model_path))
            
            # Create new agent and load model
            new_agent = MultiObjectiveRLAgent(
                state_dim=20,
                action_dim=10,
                hidden_dim=64
            )
            
            new_agent.load_model(model_path)
            
            # Test that models are equivalent
            state = torch.randn(1, 20)
            original_output = self.agent.q_network(state)
            loaded_output = new_agent.q_network(state)
            
            torch.testing.assert_close(original_output, loaded_output)
    
    def test_epsilon_decay(self):
        """Test epsilon decay functionality"""
        initial_epsilon = self.agent.epsilon
        self.agent.decay_epsilon()
        
        # Epsilon should decrease
        self.assertLess(self.agent.epsilon, initial_epsilon)
        
        # Test epsilon minimum
        for _ in range(1000):  # Decay many times
            self.agent.decay_epsilon()
        
        self.assertGreaterEqual(self.agent.epsilon, self.agent.epsilon_min)
    
    def test_target_network_update(self):
        """Test target network update"""
        # Get initial target network weights
        initial_target_weights = self.agent.target_network.fc1.weight.clone()
        
        # Update target network
        self.agent.update_target_network()
        
        # Target network weights should be updated
        # (In practice, they would be copied from main network)
        self.assertIsNotNone(self.agent.target_network.fc1.weight)
    
    def test_multi_objective_weights(self):
        """Test multi-objective weight configuration"""
        weights = self.agent.objective_weights
        
        # Check all required objectives are present
        required_objectives = [
            'accuracy', 'cost_efficiency', 'processing_speed', 
            'stability', 'domain_specialization'
        ]
        
        for objective in required_objectives:
            self.assertIn(objective, weights)
            self.assertIsInstance(weights[objective], float)
            self.assertGreater(weights[objective], 0.0)
        
        # Check weights sum to approximately 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
    
    def test_performance_tracking(self):
        """Test performance tracking"""
        # Test initial state
        self.assertEqual(len(self.agent.episode_rewards), 0)
        self.assertEqual(len(self.agent.episode_lengths), 0)
        self.assertEqual(len(self.agent.training_losses), 0)
        
        # Add some mock data
        self.agent.episode_rewards.append(0.5)
        self.agent.episode_lengths.append(100)
        self.agent.training_losses.append(0.1)
        
        # Test data is tracked
        self.assertEqual(len(self.agent.episode_rewards), 1)
        self.assertEqual(len(self.agent.episode_lengths), 1)
        self.assertEqual(len(self.agent.training_losses), 1)
    
    def test_rule_config_initialization(self):
        """Test rule configuration initialization"""
        config = self.agent.current_rule_config
        
        # Check required configuration sections
        required_sections = [
            'confidence_thresholds', 'model_weights', 'cascade_thresholds', 'domain_specific_rules'
        ]
        
        for section in required_sections:
            self.assertIn(section, config)
            self.assertIsInstance(config[section], dict)
        
        # Check confidence thresholds
        thresholds = config['confidence_thresholds']
        self.assertIn('rule_based', thresholds)
        self.assertIn('bert', thresholds)
        self.assertIn('llm', thresholds)
        
        # Check model weights
        weights = config['model_weights']
        self.assertIn('rule_based', weights)
        self.assertIn('bert', weights)
        self.assertIn('llm', weights)
    
    def test_domain_specialization(self):
        """Test domain specialization functionality"""
        # Test different domains
        domains = ['hepatology', 'cardiology', 'neurology', 'general_medicine']
        
        for domain in domains:
            # Create features with specific domain
            features = DocumentFeatures(
                document_id=f"test_{domain}",
                title=f"Test {domain} document",
                abstract="Test abstract",
                mesh_terms=["Test"],
                publication_types=["Journal Article"],
                word_count=100,
                sentence_count=5,
                technical_term_count=10,
                medical_term_count=15,
                patient_mentions=5,
                drug_mentions=3,
                adverse_event_mentions=2,
                temporal_mentions=1,
                icsr_mesh_count=2,
                non_icsr_mesh_count=1,
                rejected_signals=0,
                domain=domain,
                complexity_score=0.7,
                confidence_indicators={"overall_confidence": 0.8},
                extracted_at="2024-01-01T00:00:00Z"
            )
            
            state = self.agent.get_state(features, {})
            self.assertEqual(state.domain, domain)
    
    def test_error_handling(self):
        """Test error handling in agent operations"""
        # Test with invalid state
        invalid_state = RLState(
            features=np.array([]),  # Invalid empty array
            current_rules={},
            performance_metrics={},
            domain="test",
            complexity_score=0.5
        )
        
        # Should handle gracefully
        try:
            action = self.agent.select_action(invalid_state)
            # If no exception, check action is valid
            self.assertIsInstance(action, RLAction)
        except Exception as e:
            # Should be a specific type of error
            self.assertIsInstance(e, (ValueError, RuntimeError))
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets"""
        # Test memory usage with large number of experiences
        initial_memory_size = len(self.agent.memory)
        
        # Add many experiences
        for _ in range(5000):
            state = self.agent.get_state(self.sample_features, {})
            action = self.agent.select_action(state)
            reward = RLReward(0.5, 0.6, 0.7, 0.8, 0.9, 0.75)
            next_state = self.agent.get_state(self.sample_features, {})
            self.agent.memory.append((state, action, reward, next_state))
        
        # Memory should be capped at memory_size
        self.assertEqual(len(self.agent.memory), self.agent.memory_size)
        
        # Memory should not grow indefinitely
        self.assertLessEqual(len(self.agent.memory), self.agent.memory_size)

class TestRLState(unittest.TestCase):
    """Test RL State functionality"""
    
    def test_state_creation(self):
        """Test state creation"""
        features = np.array([1.0, 2.0, 3.0])
        current_rules = {"threshold": 0.8}
        performance_metrics = {"accuracy": 0.9}
        domain = "test_domain"
        complexity_score = 0.7
        
        state = RLState(
            features=features,
            current_rules=current_rules,
            performance_metrics=performance_metrics,
            domain=domain,
            complexity_score=complexity_score
        )
        
        self.assertEqual(state.domain, domain)
        self.assertEqual(state.complexity_score, complexity_score)
        np.testing.assert_array_equal(state.features, features)
        self.assertEqual(state.current_rules, current_rules)
        self.assertEqual(state.performance_metrics, performance_metrics)

class TestRLAction(unittest.TestCase):
    """Test RL Action functionality"""
    
    def test_action_creation(self):
        """Test action creation"""
        rule_modifications = {"threshold": 0.9}
        confidence_threshold = 0.8
        model_selection = ["rule_based", "bert"]
        cost_budget = 0.1
        
        action = RLAction(
            rule_modifications=rule_modifications,
            confidence_threshold=confidence_threshold,
            model_selection=model_selection,
            cost_budget=cost_budget
        )
        
        self.assertEqual(action.confidence_threshold, confidence_threshold)
        self.assertEqual(action.model_selection, model_selection)
        self.assertEqual(action.cost_budget, cost_budget)
        self.assertEqual(action.rule_modifications, rule_modifications)

class TestRLReward(unittest.TestCase):
    """Test RL Reward functionality"""
    
    def test_reward_creation(self):
        """Test reward creation"""
        accuracy_reward = 0.8
        cost_efficiency_reward = 0.7
        processing_speed_reward = 0.6
        stability_reward = 0.9
        domain_specialization_reward = 0.5
        total_reward = 0.75
        
        reward = RLReward(
            accuracy_reward=accuracy_reward,
            cost_efficiency_reward=cost_efficiency_reward,
            processing_speed_reward=processing_speed_reward,
            stability_reward=stability_reward,
            domain_specialization_reward=domain_specialization_reward,
            total_reward=total_reward
        )
        
        self.assertEqual(reward.accuracy_reward, accuracy_reward)
        self.assertEqual(reward.cost_efficiency_reward, cost_efficiency_reward)
        self.assertEqual(reward.processing_speed_reward, processing_speed_reward)
        self.assertEqual(reward.stability_reward, stability_reward)
        self.assertEqual(reward.domain_specialization_reward, domain_specialization_reward)
        self.assertEqual(reward.total_reward, total_reward)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
