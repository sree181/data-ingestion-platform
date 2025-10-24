#!/usr/bin/env python3
"""
Test RL Training Components
Quick test to verify all components work together
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from rl_agent import MultiObjectiveRLAgent, RLState, RLAction, RLReward
from training_engine import RLTrainingEngine
from rule_optimizer import RuleConfigurationGenerator

def test_rl_agent():
    """Test RL agent initialization and basic functionality"""
    print("🧪 Testing RL Agent...")
    
    # Initialize agent
    agent = MultiObjectiveRLAgent(
        state_dim=20,
        action_dim=10,
        hidden_dim=64,
        learning_rate=0.001
    )
    
    # Test state creation
    features = {
        'word_count': 100,
        'sentence_count': 10,
        'technical_term_count': 5,
        'medical_term_count': 8,
        'patient_mentions': 3,
        'drug_mentions': 4,
        'adverse_event_mentions': 2,
        'temporal_mentions': 1,
        'icsr_mesh_count': 2,
        'non_icsr_mesh_count': 1,
        'rejected_signals': 0,
        'complexity_score': 0.5,
        'domain': 'hepatology',
        'confidence_indicators': {
            'overall_confidence': 0.8,
            'icsr_evidence_strength': 0.7,
            'temporal_evidence': 0.3
        }
    }
    
    performance = {
        'accuracy': 0.8,
        'cost_efficiency': 0.7,
        'processing_speed': 0.6,
        'stability': 0.9,
        'domain_specialization': 0.8
    }
    
    state = agent.get_state(features, performance)
    print(f"   ✅ State created: {len(state.features)} features")
    
    # Test action selection
    action = agent.select_action(state)
    print(f"   ✅ Action selected: confidence={action.confidence_threshold:.2f}")
    
    # Test reward calculation
    outcome = {
        'is_correct': True,
        'confidence': 0.85,
        'processing_time_ms': 1000,
        'cost_efficiency': 0.8
    }
    
    reward = agent.calculate_reward(state, action, state, outcome)
    print(f"   ✅ Reward calculated: {reward.total_reward:.3f}")
    
    print("   🎉 RL Agent test passed!")
    return True

def test_rule_optimizer():
    """Test rule configuration generator"""
    print("\n🧪 Testing Rule Optimizer...")
    
    # Initialize generator
    generator = RuleConfigurationGenerator()
    
    # Test random config generation
    config = generator.generate_random_config()
    print(f"   ✅ Random config generated: {len(config.confidence_thresholds)} thresholds")
    
    # Test mutation
    mutated_config = generator.generate_mutated_config(config, mutation_rate=0.2)
    print(f"   ✅ Config mutated: {len(mutated_config.confidence_thresholds)} thresholds")
    
    # Test crossover
    config2 = generator.generate_random_config()
    crossover_config = generator.generate_crossover_config(config, config2)
    print(f"   ✅ Config crossover: {len(crossover_config.confidence_thresholds)} thresholds")
    
    # Test optimization
    performance_metrics = {
        'accuracy': 0.8,
        'cost_efficiency': 0.7,
        'processing_speed': 0.6
    }
    
    optimized_config = generator.optimize_config(config, performance_metrics, optimization_steps=10)
    print(f"   ✅ Config optimized: {len(optimized_config.confidence_thresholds)} thresholds")
    
    print("   🎉 Rule Optimizer test passed!")
    return True

def test_training_engine():
    """Test training engine initialization"""
    print("\n🧪 Testing Training Engine...")
    
    # Check if training data exists
    data_path = "real_pubmed_data"
    if not Path(data_path).exists():
        print(f"   ⚠️  Training data not found at {data_path}")
        print("   💡 Run data collection first to generate training data")
        return False
    
    # Initialize training engine
    try:
        engine = RLTrainingEngine(
            training_data_path=data_path,
            output_dir="rl_optimization/test_training_results",
            episodes=10,  # Small test
            max_steps_per_episode=5,
            evaluation_frequency=5,
            save_frequency=10
        )
        
        print(f"   ✅ Training engine initialized")
        print(f"   📊 Training data size: {len(engine.training_data)}")
        
        # Test a single episode
        print("   🏃 Running test episode...")
        episode_reward, episode_length = engine._run_episode(0)
        print(f"   ✅ Test episode completed: reward={episode_reward:.3f}, length={episode_length}")
        
        print("   🎉 Training Engine test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Training engine test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RL Training Component Tests")
    print("=" * 60)
    
    tests = [
        test_rl_agent,
        test_rule_optimizer,
        test_training_engine
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RL training components are ready.")
        print("\n🚀 Next steps:")
        print("   1. Run: python rl_optimization/rl_training/train_rl_agent.py")
        print("   2. Monitor training progress in rl_optimization/training_results/")
        print("   3. Analyze results and optimize hyperparameters")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
