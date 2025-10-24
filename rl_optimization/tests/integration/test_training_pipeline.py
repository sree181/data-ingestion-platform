"""
Integration Tests for Complete Training Pipeline
End-to-end testing of the RL training system
"""

import unittest
import torch
import numpy as np
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from rl_training.training_engine import RLTrainingEngine
from rl_training.rl_agent import MultiObjectiveRLAgent
from data.dataset import PubMedStreamingDataset, TrainingSample, DocumentFeatures, ClassificationOutcome
from data.data_loader import RLDataLoader, BatchConfig
from data.validators import DataValidator

class TestTrainingPipeline(unittest.TestCase):
    """Test complete training pipeline integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.training_data_path = os.path.join(self.temp_dir, "training_data")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        # Create test data
        self._create_comprehensive_test_data()
        
        # Initialize components
        self.dataset = PubMedStreamingDataset(
            data_path=self.training_data_path,
            cache_size=100,
            num_workers=2
        )
        
        self.batch_config = BatchConfig(
            batch_size=8,
            dynamic_batching=True
        )
        
        self.data_loader = RLDataLoader(
            dataset=self.dataset,
            batch_config=self.batch_config,
            num_workers=2
        )
        
        self.training_engine = RLTrainingEngine(
            training_data_path=self.training_data_path,
            output_dir=self.output_dir,
            episodes=5,
            max_steps_per_episode=3,
            evaluation_frequency=2,
            save_frequency=2
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_comprehensive_test_data(self):
        """Create comprehensive test training data"""
        os.makedirs(self.training_data_path, exist_ok=True)
        
        # Create multiple test files with different characteristics
        domains = ['hepatology', 'cardiology', 'neurology', 'general_medicine']
        classifications = ['ICSR', 'Non-ICSR', 'Safety_Information', 'Rejected']
        
        for file_idx in range(5):
            samples = []
            for sample_idx in range(20):
                domain = domains[sample_idx % len(domains)]
                classification = classifications[sample_idx % len(classifications)]
                
                sample_data = {
                    "features": {
                        "document_id": f"test_{file_idx}_{sample_idx}",
                        "title": f"Test {domain} Document {sample_idx}",
                        "abstract": f"This is a test abstract for {domain} document {sample_idx}. It contains medical terminology and patient information.",
                        "mesh_terms": [f"{domain}_term_{i}" for i in range(3)],
                        "publication_types": ["Journal Article", "Case Report"],
                        "word_count": 100 + sample_idx * 10,
                        "sentence_count": 5 + sample_idx,
                        "technical_term_count": 10 + sample_idx,
                        "medical_term_count": 15 + sample_idx,
                        "patient_mentions": 5 + sample_idx,
                        "drug_mentions": 3 + sample_idx,
                        "adverse_event_mentions": 2 + sample_idx,
                        "temporal_mentions": 1 + sample_idx,
                        "icsr_mesh_count": 2 + sample_idx,
                        "non_icsr_mesh_count": 1 + sample_idx,
                        "rejected_signals": 0,
                        "domain": domain,
                        "complexity_score": 0.5 + (sample_idx % 5) * 0.1,
                        "confidence_indicators": {
                            "overall_confidence": 0.7 + (sample_idx % 3) * 0.1,
                            "icsr_evidence_strength": 0.6 + (sample_idx % 4) * 0.1
                        },
                        "extracted_at": "2024-01-01T00:00:00Z"
                    },
                    "outcome": {
                        "true_classification": classification,
                        "predicted_classification": classification,
                        "confidence": 0.8 + (sample_idx % 2) * 0.1,
                        "reasoning": f"High confidence classification for {domain}",
                        "models_used": ["rule_based", "bert"] if sample_idx % 2 == 0 else ["rule_based"],
                        "decision_path": "rule_based_bert" if sample_idx % 2 == 0 else "rule_based_only",
                        "processing_time_ms": 100 + sample_idx * 10,
                        "cost_estimate": 0.01 + sample_idx * 0.001,
                        "is_correct": sample_idx % 3 != 0,  # Some incorrect predictions
                        "confidence_penalty": 0.9 - (sample_idx % 3) * 0.1,
                        "cost_efficiency": 0.8 - (sample_idx % 4) * 0.05,
                        "classified_at": "2024-01-01T00:00:00Z"
                    },
                    "metadata": {
                        "collected_at": "2024-01-01T00:00:00Z",
                        "data_id": f"test_{file_idx}_{sample_idx}"
                    }
                }
                samples.append(sample_data)
            
            # Save to file
            file_path = os.path.join(self.training_data_path, f"test_data_{file_idx}.json")
            with open(file_path, 'w') as f:
                json.dump(samples, f)
    
    def test_data_loading_pipeline(self):
        """Test complete data loading pipeline"""
        # Test dataset loading
        self.assertIsNotNone(self.dataset)
        
        # Test data loader
        self.assertIsNotNone(self.data_loader)
        
        # Test data loading
        batch_count = 0
        for batch in self.data_loader:
            self.assertIsInstance(batch, dict)
            self.assertIn('features', batch)
            self.assertIn('outcomes', batch)
            self.assertIn('batch_size', batch)
            
            # Check batch structure
            self.assertIsInstance(batch['features'], torch.Tensor)
            self.assertIsInstance(batch['outcomes'], torch.Tensor)
            self.assertIsInstance(batch['batch_size'], int)
            
            batch_count += 1
            if batch_count >= 3:  # Limit to avoid long test
                break
        
        self.assertGreater(batch_count, 0)
    
    def test_training_engine_integration(self):
        """Test training engine integration"""
        # Test training engine initialization
        self.assertIsNotNone(self.training_engine)
        self.assertIsNotNone(self.training_engine.agent)
        self.assertIsNotNone(self.training_engine.rule_optimizer)
        
        # Test data loading
        training_data = self.training_engine._load_training_data()
        self.assertIsInstance(training_data, list)
        self.assertGreater(len(training_data), 0)
    
    def test_agent_training_integration(self):
        """Test agent training integration"""
        # Load training data
        training_data = self.training_engine._load_training_data()
        
        # Test episode execution
        episode_reward, episode_length = self.training_engine._run_episode(training_data[:10])
        
        self.assertIsInstance(episode_reward, float)
        self.assertIsInstance(episode_length, int)
        self.assertGreaterEqual(episode_length, 0)
        
        # Test agent memory
        self.assertGreater(len(self.training_engine.agent.memory), 0)
    
    def test_rule_optimization_integration(self):
        """Test rule optimization integration"""
        # Test rule optimizer
        rule_optimizer = self.training_engine.rule_optimizer
        self.assertIsNotNone(rule_optimizer)
        
        # Test rule configuration generation
        config = rule_optimizer.generate_config()
        self.assertIsInstance(config, dict)
        self.assertIn('confidence_thresholds', config)
        self.assertIn('model_weights', config)
        self.assertIn('cascade_thresholds', config)
        self.assertIn('domain_specific_rules', config)
        
        # Test rule mutation
        mutated_config = rule_optimizer.mutate_config(config)
        self.assertIsInstance(mutated_config, dict)
        self.assertNotEqual(config, mutated_config)
    
    def test_evaluation_integration(self):
        """Test evaluation integration"""
        # Load training data
        training_data = self.training_engine._load_training_data()
        
        # Test evaluation
        eval_metrics = self.training_engine._evaluate_model(training_data[:5])
        
        self.assertIsInstance(eval_metrics, dict)
        required_metrics = [
            'accuracy', 'cost_efficiency', 'processing_speed', 
            'stability', 'domain_specialization'
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, eval_metrics)
            self.assertIsInstance(eval_metrics[metric], float)
            self.assertGreaterEqual(eval_metrics[metric], 0.0)
            self.assertLessEqual(eval_metrics[metric], 1.0)
    
    def test_checkpoint_integration(self):
        """Test checkpoint integration"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test checkpoint saving
        checkpoint_path = os.path.join(self.output_dir, "integration_test_checkpoint.pth")
        self.training_engine._save_checkpoint(checkpoint_path)
        
        # Verify checkpoint was created
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Test checkpoint loading
        new_engine = RLTrainingEngine(
            training_data_path=self.training_data_path,
            output_dir=self.output_dir,
            episodes=2,
            max_steps_per_episode=2,
            evaluation_frequency=1,
            save_frequency=1
        )
        
        # Load checkpoint
        new_engine._load_checkpoint(checkpoint_path)
        
        # Verify loading was successful
        self.assertIsNotNone(new_engine.agent)
        self.assertIsNotNone(new_engine.rule_optimizer)
    
    def test_distributed_training_simulation(self):
        """Test distributed training simulation"""
        # Simulate multiple training engines (workers)
        workers = []
        for i in range(3):
            worker = RLTrainingEngine(
                training_data_path=self.training_data_path,
                output_dir=os.path.join(self.output_dir, f"worker_{i}"),
                episodes=2,
                max_steps_per_episode=2,
                evaluation_frequency=1,
                save_frequency=1
            )
            workers.append(worker)
        
        # Test that all workers can run independently
        for i, worker in enumerate(workers):
            training_data = worker._load_training_data()
            episode_reward, episode_length = worker._run_episode(training_data[:5])
            
            self.assertIsInstance(episode_reward, float)
            self.assertIsInstance(episode_length, int)
    
    def test_memory_management_integration(self):
        """Test memory management integration"""
        # Test memory usage tracking
        initial_memory = self.training_engine._get_memory_usage()
        self.assertIsInstance(initial_memory, float)
        self.assertGreaterEqual(initial_memory, 0.0)
        
        # Run some training to increase memory usage
        training_data = self.training_engine._load_training_data()
        self.training_engine._run_episode(training_data[:10])
        
        # Test memory cleanup
        self.training_engine._cleanup_memory()
        
        # Should not raise exceptions
        self.assertTrue(True)
    
    def test_error_handling_integration(self):
        """Test error handling integration"""
        # Test with corrupted data
        corrupted_data = [
            {
                'features': {
                    'document_id': 'corrupted_001',
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
                    'domain': 'invalid_domain',
                    'complexity_score': 1.5,  # Invalid score > 1.0
                    'confidence_indicators': {},
                    'extracted_at': 'invalid_date'
                },
                'outcome': {
                    'true_classification': 'Invalid',
                    'predicted_classification': 'Invalid',
                    'confidence': 1.5,  # Invalid confidence > 1.0
                    'reasoning': '',
                    'models_used': [],
                    'decision_path': '',
                    'processing_time_ms': -1,
                    'cost_estimate': -0.1,
                    'is_correct': True,
                    'confidence_penalty': 0.0,
                    'cost_efficiency': 0.0,
                    'classified_at': 'invalid_date'
                }
            }
        ]
        
        # Should handle corrupted data gracefully
        try:
            episode_reward, episode_length = self.training_engine._run_episode(corrupted_data)
            # If no exception, check that values are reasonable
            self.assertIsInstance(episode_reward, float)
            self.assertIsInstance(episode_length, int)
        except Exception as e:
            # Should be a specific type of error
            self.assertIsInstance(e, (ValueError, RuntimeError, KeyError))
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        # Test performance metrics calculation
        metrics = self.training_engine._calculate_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        required_metrics = [
            'episode_reward_mean', 'episode_reward_std',
            'episode_length_mean', 'episode_length_std'
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], float)
    
    def test_data_validation_integration(self):
        """Test data validation integration"""
        # Create data validator
        validator = DataValidator()
        
        # Load training data
        training_data = self.training_engine._load_training_data()
        
        # Convert to TrainingSample objects for validation
        samples = []
        for data in training_data[:5]:  # Test with first 5 samples
            try:
                features = DocumentFeatures(**data['features'])
                outcome = ClassificationOutcome(**data['outcome'])
                sample = TrainingSample(
                    features=features,
                    outcome=outcome,
                    metadata=data.get('metadata', {})
                )
                samples.append(sample)
            except Exception as e:
                # Skip invalid samples
                continue
        
        # Test validation
        if samples:
            report = validator.validate_dataset(samples)
            self.assertIsNotNone(report)
            self.assertIsInstance(report.validation_result.is_valid, bool)
    
    def test_complete_training_cycle(self):
        """Test complete training cycle"""
        # Test that all components work together in a complete cycle
        start_time = time.time()
        
        # Load training data
        training_data = self.training_engine._load_training_data()
        self.assertGreater(len(training_data), 0)
        
        # Run training episodes
        for episode in range(2):
            episode_reward, episode_length = self.training_engine._run_episode(training_data[:10])
            self.assertIsInstance(episode_reward, float)
            self.assertIsInstance(episode_length, int)
        
        # Test evaluation
        eval_metrics = self.training_engine._evaluate_model(training_data[:5])
        self.assertIsInstance(eval_metrics, dict)
        
        # Test checkpoint saving
        os.makedirs(self.output_dir, exist_ok=True)
        checkpoint_path = os.path.join(self.output_dir, "complete_cycle_checkpoint.pth")
        self.training_engine._save_checkpoint(checkpoint_path)
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Test performance metrics
        performance_metrics = self.training_engine._calculate_performance_metrics()
        self.assertIsInstance(performance_metrics, dict)
        
        # Test that training completed within reasonable time
        training_time = time.time() - start_time
        self.assertLess(training_time, 60.0)  # Should complete within 60 seconds
    
    def test_multi_domain_training(self):
        """Test training with multiple domains"""
        # Test that training works with different medical domains
        domains = ['hepatology', 'cardiology', 'neurology', 'general_medicine']
        
        for domain in domains:
            # Filter data by domain
            domain_data = []
            training_data = self.training_engine._load_training_data()
            
            for data in training_data:
                if data['features']['domain'] == domain:
                    domain_data.append(data)
            
            if domain_data:
                # Test episode execution with domain-specific data
                episode_reward, episode_length = self.training_engine._run_episode(domain_data[:5])
                self.assertIsInstance(episode_reward, float)
                self.assertIsInstance(episode_length, int)
    
    def test_concurrent_data_loading(self):
        """Test concurrent data loading"""
        # Test that data loading works with multiple workers
        import threading
        import queue
        
        results = queue.Queue()
        
        def load_data_worker(worker_id):
            try:
                training_data = self.training_engine._load_training_data()
                results.put((worker_id, len(training_data), None))
            except Exception as e:
                results.put((worker_id, 0, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=load_data_worker, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            worker_id, data_length, error = results.get()
            if error:
                self.fail(f"Worker {worker_id} failed: {error}")
            self.assertGreater(data_length, 0)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
