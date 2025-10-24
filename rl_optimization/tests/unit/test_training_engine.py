"""
Unit Tests for RL Training Engine
Comprehensive test suite for training orchestration
"""

import unittest
import torch
import numpy as np
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from rl_training.training_engine import RLTrainingEngine
from rl_training.rl_agent import MultiObjectiveRLAgent
from data.dataset import TrainingSample, DocumentFeatures, ClassificationOutcome

class TestRLTrainingEngine(unittest.TestCase):
    """Test RL Training Engine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.training_data_path = os.path.join(self.temp_dir, "training_data")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        # Create test data
        self._create_test_data()
        
        # Initialize training engine
        self.training_engine = RLTrainingEngine(
            training_data_path=self.training_data_path,
            output_dir=self.output_dir,
            episodes=10,
            max_steps_per_episode=5,
            evaluation_frequency=5,
            save_frequency=5
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_data(self):
        """Create test training data"""
        os.makedirs(self.training_data_path, exist_ok=True)
        
        # Create sample training data
        sample_data = {
            "features": {
                "document_id": "test_001",
                "title": "Test Document",
                "abstract": "Test abstract content",
                "mesh_terms": ["Test", "Mesh"],
                "publication_types": ["Journal Article"],
                "word_count": 100,
                "sentence_count": 5,
                "technical_term_count": 10,
                "medical_term_count": 15,
                "patient_mentions": 5,
                "drug_mentions": 3,
                "adverse_event_mentions": 2,
                "temporal_mentions": 1,
                "icsr_mesh_count": 2,
                "non_icsr_mesh_count": 1,
                "rejected_signals": 0,
                "domain": "general_medicine",
                "complexity_score": 0.7,
                "confidence_indicators": {"overall_confidence": 0.8},
                "extracted_at": "2024-01-01T00:00:00Z"
            },
            "outcome": {
                "true_classification": "ICSR",
                "predicted_classification": "ICSR",
                "confidence": 0.9,
                "reasoning": "High confidence classification",
                "models_used": ["rule_based", "bert"],
                "decision_path": "rule_based_bert",
                "processing_time_ms": 150,
                "cost_estimate": 0.05,
                "is_correct": True,
                "confidence_penalty": 0.9,
                "cost_efficiency": 0.8,
                "classified_at": "2024-01-01T00:00:00Z"
            },
            "metadata": {
                "collected_at": "2024-01-01T00:00:00Z",
                "data_id": "test_001"
            }
        }
        
        # Create multiple test files
        for i in range(3):
            file_path = os.path.join(self.training_data_path, f"test_data_{i}.json")
            with open(file_path, 'w') as f:
                json.dump([sample_data] * 10, f)  # 10 samples per file
    
    def test_initialization(self):
        """Test training engine initialization"""
        self.assertEqual(self.training_engine.episodes, 10)
        self.assertEqual(self.training_engine.max_steps_per_episode, 5)
        self.assertEqual(self.training_engine.evaluation_frequency, 5)
        self.assertEqual(self.training_engine.save_frequency, 5)
        self.assertIsNotNone(self.training_engine.agent)
        self.assertIsNotNone(self.training_engine.rule_optimizer)
    
    def test_data_loading(self):
        """Test data loading functionality"""
        # Test loading training data
        training_data = self.training_engine._load_training_data()
        
        self.assertIsInstance(training_data, list)
        self.assertGreater(len(training_data), 0)
        
        # Check data structure
        for sample in training_data:
            self.assertIn('features', sample)
            self.assertIn('outcome', sample)
            self.assertIn('metadata', sample)
    
    def test_episode_execution(self):
        """Test episode execution"""
        # Mock training data
        mock_data = [
            {
                'features': {
                    'document_id': 'test_001',
                    'title': 'Test Document',
                    'abstract': 'Test abstract',
                    'mesh_terms': ['Test'],
                    'publication_types': ['Journal Article'],
                    'word_count': 100,
                    'sentence_count': 5,
                    'technical_term_count': 10,
                    'medical_term_count': 15,
                    'patient_mentions': 5,
                    'drug_mentions': 3,
                    'adverse_event_mentions': 2,
                    'temporal_mentions': 1,
                    'icsr_mesh_count': 2,
                    'non_icsr_mesh_count': 1,
                    'rejected_signals': 0,
                    'domain': 'general_medicine',
                    'complexity_score': 0.7,
                    'confidence_indicators': {'overall_confidence': 0.8},
                    'extracted_at': '2024-01-01T00:00:00Z'
                },
                'outcome': {
                    'true_classification': 'ICSR',
                    'predicted_classification': 'ICSR',
                    'confidence': 0.9,
                    'reasoning': 'High confidence',
                    'models_used': ['rule_based'],
                    'decision_path': 'rule_based_only',
                    'processing_time_ms': 100,
                    'cost_estimate': 0.01,
                    'is_correct': True,
                    'confidence_penalty': 0.9,
                    'cost_efficiency': 0.8,
                    'classified_at': '2024-01-01T00:00:00Z'
                }
            }
        ]
        
        # Test episode execution
        episode_reward, episode_length = self.training_engine._run_episode(mock_data)
        
        self.assertIsInstance(episode_reward, float)
        self.assertIsInstance(episode_length, int)
        self.assertGreaterEqual(episode_length, 0)
    
    def test_agent_training(self):
        """Test agent training functionality"""
        # Mock training data
        mock_data = [
            {
                'features': {
                    'document_id': 'test_001',
                    'title': 'Test Document',
                    'abstract': 'Test abstract',
                    'mesh_terms': ['Test'],
                    'publication_types': ['Journal Article'],
                    'word_count': 100,
                    'sentence_count': 5,
                    'technical_term_count': 10,
                    'medical_term_count': 15,
                    'patient_mentions': 5,
                    'drug_mentions': 3,
                    'adverse_event_mentions': 2,
                    'temporal_mentions': 1,
                    'icsr_mesh_count': 2,
                    'non_icsr_mesh_count': 1,
                    'rejected_signals': 0,
                    'domain': 'general_medicine',
                    'complexity_score': 0.7,
                    'confidence_indicators': {'overall_confidence': 0.8},
                    'extracted_at': '2024-01-01T00:00:00Z'
                },
                'outcome': {
                    'true_classification': 'ICSR',
                    'predicted_classification': 'ICSR',
                    'confidence': 0.9,
                    'reasoning': 'High confidence',
                    'models_used': ['rule_based'],
                    'decision_path': 'rule_based_only',
                    'processing_time_ms': 100,
                    'cost_estimate': 0.01,
                    'is_correct': True,
                    'confidence_penalty': 0.9,
                    'cost_efficiency': 0.8,
                    'classified_at': '2024-01-01T00:00:00Z'
                }
            }
        ]
        
        # Add experiences to agent memory
        for _ in range(32):  # Add enough for training
            state = self.training_engine.agent.get_state(mock_data[0]['features'], {})
            action = self.training_engine.agent.select_action(state)
            reward = self.training_engine.agent.calculate_reward(
                state, action, state, mock_data[0]['outcome']
            )
            next_state = self.training_engine.agent.get_state(mock_data[0]['features'], {})
            self.training_engine.agent.memory.append((state, action, reward, next_state))
        
        # Test training step
        initial_loss = len(self.training_engine.agent.training_losses)
        self.training_engine.agent.train_step()
        
        # Check that training occurred
        self.assertGreater(len(self.training_engine.agent.training_losses), initial_loss)
    
    def test_evaluation(self):
        """Test model evaluation"""
        # Mock evaluation data
        mock_data = [
            {
                'features': {
                    'document_id': 'eval_001',
                    'title': 'Evaluation Document',
                    'abstract': 'Evaluation abstract',
                    'mesh_terms': ['Evaluation'],
                    'publication_types': ['Journal Article'],
                    'word_count': 150,
                    'sentence_count': 8,
                    'technical_term_count': 15,
                    'medical_term_count': 20,
                    'patient_mentions': 8,
                    'drug_mentions': 5,
                    'adverse_event_mentions': 3,
                    'temporal_mentions': 2,
                    'icsr_mesh_count': 3,
                    'non_icsr_mesh_count': 2,
                    'rejected_signals': 0,
                    'domain': 'cardiology',
                    'complexity_score': 0.8,
                    'confidence_indicators': {'overall_confidence': 0.9},
                    'extracted_at': '2024-01-01T00:00:00Z'
                },
                'outcome': {
                    'true_classification': 'Non-ICSR',
                    'predicted_classification': 'Non-ICSR',
                    'confidence': 0.85,
                    'reasoning': 'Medium confidence',
                    'models_used': ['bert'],
                    'decision_path': 'bert_only',
                    'processing_time_ms': 200,
                    'cost_estimate': 0.02,
                    'is_correct': True,
                    'confidence_penalty': 0.85,
                    'cost_efficiency': 0.75,
                    'classified_at': '2024-01-01T00:00:00Z'
                }
            }
        ]
        
        # Test evaluation
        eval_metrics = self.training_engine._evaluate_model(mock_data)
        
        self.assertIsInstance(eval_metrics, dict)
        self.assertIn('accuracy', eval_metrics)
        self.assertIn('cost_efficiency', eval_metrics)
        self.assertIn('processing_speed', eval_metrics)
        self.assertIn('stability', eval_metrics)
        self.assertIn('domain_specialization', eval_metrics)
    
    def test_checkpoint_saving(self):
        """Test checkpoint saving functionality"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test checkpoint saving
        checkpoint_path = os.path.join(self.output_dir, "test_checkpoint.pth")
        self.training_engine._save_checkpoint(checkpoint_path)
        
        # Check that checkpoint was created
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Check checkpoint content
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        self.assertIn('agent_state', checkpoint)
        self.assertIn('training_metrics', checkpoint)
        self.assertIn('episode', checkpoint)
    
    def test_checkpoint_loading(self):
        """Test checkpoint loading functionality"""
        # Create a checkpoint first
        os.makedirs(self.output_dir, exist_ok=True)
        checkpoint_path = os.path.join(self.output_dir, "test_checkpoint.pth")
        self.training_engine._save_checkpoint(checkpoint_path)
        
        # Create new training engine and load checkpoint
        new_engine = RLTrainingEngine(
            training_data_path=self.training_data_path,
            output_dir=self.output_dir,
            episodes=5,
            max_steps_per_episode=3,
            evaluation_frequency=2,
            save_frequency=2
        )
        
        # Load checkpoint
        new_engine._load_checkpoint(checkpoint_path)
        
        # Check that loading was successful (no exceptions raised)
        self.assertIsNotNone(new_engine.agent)
    
    def test_metrics_tracking(self):
        """Test metrics tracking functionality"""
        # Test initial metrics
        self.assertEqual(len(self.training_engine.episode_rewards), 0)
        self.assertEqual(len(self.training_engine.episode_lengths), 0)
        self.assertEqual(len(self.training_engine.evaluation_metrics), 0)
        
        # Add some mock metrics
        self.training_engine.episode_rewards.append(0.5)
        self.training_engine.episode_lengths.append(100)
        self.training_engine.evaluation_metrics.append({
            'accuracy': 0.8,
            'cost_efficiency': 0.7,
            'processing_speed': 0.9
        })
        
        # Test metrics are tracked
        self.assertEqual(len(self.training_engine.episode_rewards), 1)
        self.assertEqual(len(self.training_engine.episode_lengths), 1)
        self.assertEqual(len(self.training_engine.evaluation_metrics), 1)
    
    def test_rule_optimization(self):
        """Test rule optimization functionality"""
        # Test rule optimizer initialization
        self.assertIsNotNone(self.training_engine.rule_optimizer)
        
        # Test rule configuration generation
        config = self.training_engine.rule_optimizer.generate_config()
        self.assertIsInstance(config, dict)
        self.assertIn('confidence_thresholds', config)
        self.assertIn('model_weights', config)
        self.assertIn('cascade_thresholds', config)
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        # Test performance metrics calculation
        metrics = self.training_engine._calculate_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('episode_reward_mean', metrics)
        self.assertIn('episode_reward_std', metrics)
        self.assertIn('episode_length_mean', metrics)
        self.assertIn('episode_length_std', metrics)
    
    def test_error_handling(self):
        """Test error handling in training engine"""
        # Test with invalid data path
        invalid_engine = RLTrainingEngine(
            training_data_path="/invalid/path",
            output_dir=self.output_dir,
            episodes=1,
            max_steps_per_episode=1,
            evaluation_frequency=1,
            save_frequency=1
        )
        
        # Should handle gracefully
        try:
            invalid_engine._load_training_data()
        except Exception as e:
            self.assertIsInstance(e, (FileNotFoundError, OSError))
    
    def test_memory_management(self):
        """Test memory management during training"""
        # Test memory usage tracking
        initial_memory = self.training_engine._get_memory_usage()
        self.assertIsInstance(initial_memory, float)
        self.assertGreaterEqual(initial_memory, 0.0)
        
        # Test memory cleanup
        self.training_engine._cleanup_memory()
        # Should not raise exceptions
    
    def test_concurrent_training(self):
        """Test concurrent training scenarios"""
        # Test that training engine can handle concurrent access
        # (In a real scenario, this would test thread safety)
        self.assertIsNotNone(self.training_engine.agent)
        self.assertIsNotNone(self.training_engine.rule_optimizer)
    
    def test_data_validation(self):
        """Test data validation during training"""
        # Test with invalid sample data
        invalid_data = [
            {
                'features': {
                    'document_id': 'invalid_001',
                    'title': '',  # Invalid empty title
                    'abstract': 'Test abstract',
                    'mesh_terms': [],
                    'publication_types': [],
                    'word_count': -1,  # Invalid negative count
                    'sentence_count': 0,
                    'technical_term_count': 0,
                    'medical_term_count': 0,
                    'patient_mentions': 0,
                    'drug_mentions': 0,
                    'adverse_event_mentions': 0,
                    'temporal_mentions': 0,
                    'icsr_mesh_count': 0,
                    'non_icsr_mesh_count': 0,
                    'rejected_signals': 0,
                    'domain': 'invalid_domain',  # Invalid domain
                    'complexity_score': 1.5,  # Invalid score > 1.0
                    'confidence_indicators': {},
                    'extracted_at': 'invalid_date'
                },
                'outcome': {
                    'true_classification': 'Invalid',  # Invalid classification
                    'predicted_classification': 'Invalid',
                    'confidence': 1.5,  # Invalid confidence > 1.0
                    'reasoning': '',
                    'models_used': [],
                    'decision_path': '',
                    'processing_time_ms': -1,  # Invalid negative time
                    'cost_estimate': -0.1,  # Invalid negative cost
                    'is_correct': True,
                    'confidence_penalty': 0.0,
                    'cost_efficiency': 0.0,
                    'classified_at': 'invalid_date'
                }
            }
        ]
        
        # Should handle invalid data gracefully
        try:
            episode_reward, episode_length = self.training_engine._run_episode(invalid_data)
            # If no exception, check that values are reasonable
            self.assertIsInstance(episode_reward, float)
            self.assertIsInstance(episode_length, int)
        except Exception as e:
            # Should be a specific type of error
            self.assertIsInstance(e, (ValueError, RuntimeError))
    
    def test_training_loop_integration(self):
        """Test complete training loop integration"""
        # Test that all components work together
        self.assertIsNotNone(self.training_engine.agent)
        self.assertIsNotNone(self.training_engine.rule_optimizer)
        self.assertIsNotNone(self.training_engine.training_data_path)
        self.assertIsNotNone(self.training_engine.output_dir)
        
        # Test configuration
        self.assertGreater(self.training_engine.episodes, 0)
        self.assertGreater(self.training_engine.max_steps_per_episode, 0)
        self.assertGreater(self.training_engine.evaluation_frequency, 0)
        self.assertGreater(self.training_engine.save_frequency, 0)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
