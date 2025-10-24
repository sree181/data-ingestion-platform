#!/usr/bin/env python3
"""
IP Framework Testing Script
Tests all novel algorithms and IP components
"""

import sys
import os
from pathlib import Path
import structlog
import json
import numpy as np
from datetime import datetime

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import IP components
from ip_enhanced_rl_agent import IPEnhancedRLAgent, IPEnhancedConfig
from adaptive_reward_shaping import AdaptiveMultiObjectiveRewardShaping, PerformanceTargets, AdaptationConfig
from hierarchical_rule_evolution import HierarchicalRuleEvolution, RuleLevel, EvolutionConfig
from confidence_aware_multi_objective import ConfidenceAwareMultiObjective, OptimizationConfig
from ip_validation_framework import IPValidationFramework, ValidationConfig

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

def test_adaptive_reward_shaping():
    """Test Adaptive Multi-Objective Reward Shaping"""
    print("\n🧪 Testing Adaptive Multi-Objective Reward Shaping...")
    
    try:
        # Initialize AMORS
        amors = AdaptiveMultiObjectiveRewardShaping()
        
        # Test weight adaptation
        performance_feedback = {
            'accuracy': 0.85,
            'cost_efficiency': 0.78,
            'processing_speed': 0.82,
            'stability': 0.88,
            'domain_specialization': 0.75
        }
        
        adapted_weights = amors.adapt_weights(performance_feedback)
        print(f"   ✅ Adapted weights: {adapted_weights}")
        
        # Test context-aware weights
        context = {
            'domain': 'hepatology',
            'complexity_score': 0.7,
            'urgency': 'high'
        }
        
        context_weights = amors.get_recommended_weights(context)
        print(f"   ✅ Context-aware weights: {context_weights}")
        
        # Test statistics
        stats = amors.get_adaptation_statistics()
        print(f"   ✅ Adaptation statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_hierarchical_rule_evolution():
    """Test Hierarchical Rule Evolution"""
    print("\n🧪 Testing Hierarchical Rule Evolution...")
    
    try:
        # Initialize HRE
        hre = HierarchicalRuleEvolution()
        
        # Test rule evolution at different levels
        performance_feedback = {
            'accuracy': 0.82,
            'cost_efficiency': 0.75,
            'processing_speed': 0.80,
            'stability': 0.85,
            'domain_specialization': 0.78
        }
        
        # Test global rule evolution
        global_rules = hre.evolve_rules(RuleLevel.GLOBAL, performance_feedback)
        print(f"   ✅ Global rules evolved: {len(global_rules)} rules")
        
        # Test domain rule evolution
        domain_rules = hre.evolve_rules(RuleLevel.DOMAIN, performance_feedback, domain='hepatology')
        print(f"   ✅ Domain rules evolved: {len(domain_rules)} rules")
        
        # Test subdomain rule evolution
        subdomain_rules = hre.evolve_rules(RuleLevel.SUBDOMAIN, performance_feedback, 
                                          domain='hepatology', subdomain='liver_toxicity')
        print(f"   ✅ Subdomain rules evolved: {len(subdomain_rules)} rules")
        
        # Test rule synchronization
        cross_domain_results = {
            'hepatology': domain_rules,
            'cardiology': {'confidence_threshold': 0.8, 'model_weight': 0.6},
            'neurology': {'confidence_threshold': 0.75, 'model_weight': 0.7}
        }
        
        synchronized_rules = hre.synchronize_rules(cross_domain_results)
        print(f"   ✅ Rules synchronized across {len(synchronized_rules)} domains")
        
        # Test statistics
        stats = hre.get_evolution_statistics()
        print(f"   ✅ Evolution statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_confidence_aware_multi_objective():
    """Test Confidence-Aware Multi-Objective Optimization"""
    print("\n🧪 Testing Confidence-Aware Multi-Objective Optimization...")
    
    try:
        # Initialize CAMO
        camo = ConfidenceAwareMultiObjective()
        
        # Test optimization with different confidence levels
        state = {
            'confidence_thresholds': {'rule_based': 0.8, 'bert': 0.7, 'llm': 0.6},
            'model_weights': {'rule_based': 0.4, 'bert': 0.3, 'llm': 0.3},
            'epsilon': 0.1
        }
        
        # High confidence optimization
        high_conf_config = camo.optimize_with_confidence(state, confidence=0.9)
        print(f"   ✅ High confidence optimization: {len(high_conf_config)} parameters")
        
        # Medium confidence optimization
        medium_conf_config = camo.optimize_with_confidence(state, confidence=0.6)
        print(f"   ✅ Medium confidence optimization: {len(medium_conf_config)} parameters")
        
        # Low confidence optimization
        low_conf_config = camo.optimize_with_confidence(state, confidence=0.3)
        print(f"   ✅ Low confidence optimization: {len(low_conf_config)} parameters")
        
        # Test with context
        context = {
            'domain': 'cardiology',
            'complexity_score': 0.8,
            'urgency': 'high'
        }
        
        context_config = camo.optimize_with_confidence(state, confidence=0.7, context=context)
        print(f"   ✅ Context-aware optimization: {len(context_config)} parameters")
        
        # Test statistics
        stats = camo.get_optimization_statistics()
        print(f"   ✅ Optimization statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_ip_enhanced_agent():
    """Test IP-Enhanced RL Agent"""
    print("\n🧪 Testing IP-Enhanced RL Agent...")
    
    try:
        # Initialize IP-enhanced agent
        ip_agent = IPEnhancedRLAgent()
        
        # Test state
        state = {
            'confidence_thresholds': {'rule_based': 0.8, 'bert': 0.7, 'llm': 0.6},
            'model_weights': {'rule_based': 0.4, 'bert': 0.3, 'llm': 0.3},
            'epsilon': 0.1,
            'learning_rate': 0.001
        }
        
        # Test performance feedback
        performance_feedback = {
            'accuracy': 0.85,
            'cost_efficiency': 0.78,
            'processing_speed': 0.82,
            'stability': 0.88,
            'domain_specialization': 0.75
        }
        
        # Test context
        context = {
            'domain': 'hepatology',
            'complexity_score': 0.7,
            'urgency': 'normal'
        }
        
        # Test IP optimization
        ip_optimized_config = ip_agent.optimize_with_ip_algorithms(
            state=state,
            performance_feedback=performance_feedback,
            confidence=0.8,
            context=context
        )
        
        print(f"   ✅ IP optimization completed: {len(ip_optimized_config)} parameters")
        
        # Test IP statistics
        ip_stats = ip_agent.get_ip_statistics()
        print(f"   ✅ IP statistics: {ip_stats}")
        
        # Test patent application data
        patent_data = ip_agent.get_patent_application_data()
        print(f"   ✅ Patent data: {len(patent_data)} components")
        
        # Test patent summary
        patent_summary = ip_agent.generate_patent_summary()
        print(f"   ✅ Patent summary generated: {len(patent_summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_ip_validation_framework():
    """Test IP Validation Framework"""
    print("\n🧪 Testing IP Validation Framework...")
    
    try:
        # Initialize validation framework
        validation_framework = IPValidationFramework()
        
        # Test quick validation
        quick_results = validation_framework.run_quick_validation()
        print(f"   ✅ Quick validation: {quick_results}")
        
        # Test comprehensive validation (simplified)
        print("   🔄 Running comprehensive validation...")
        
        # Performance validation
        performance_results = validation_framework._validate_performance()
        print(f"   ✅ Performance validation: {performance_results}")
        
        # Novelty validation
        novelty_results = validation_framework._validate_novelty()
        print(f"   ✅ Novelty validation: {novelty_results}")
        
        # Patent validation
        patent_results = validation_framework._validate_patent_potential()
        print(f"   ✅ Patent validation: {patent_results}")
        
        # Commercial validation
        commercial_results = validation_framework._validate_commercial_viability()
        print(f"   ✅ Commercial validation: {commercial_results}")
        
        # Integration validation
        integration_results = validation_framework._validate_integration()
        print(f"   ✅ Integration validation: {integration_results}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_integration():
    """Test integration of all components"""
    print("\n🧪 Testing IP Framework Integration...")
    
    try:
        # Initialize all components
        ip_agent = IPEnhancedRLAgent()
        validation_framework = IPValidationFramework()
        
        # Test integrated workflow
        state = {
            'confidence_thresholds': {'rule_based': 0.8, 'bert': 0.7, 'llm': 0.6},
            'model_weights': {'rule_based': 0.4, 'bert': 0.3, 'llm': 0.3},
            'epsilon': 0.1
        }
        
        performance_feedback = {
            'accuracy': 0.85,
            'cost_efficiency': 0.78,
            'processing_speed': 0.82,
            'stability': 0.88,
            'domain_specialization': 0.75
        }
        
        context = {
            'domain': 'hepatology',
            'complexity_score': 0.7,
            'urgency': 'normal'
        }
        
        # Step 1: IP optimization
        ip_optimized_config = ip_agent.optimize_with_ip_algorithms(
            state=state,
            performance_feedback=performance_feedback,
            confidence=0.8,
            context=context
        )
        
        print(f"   ✅ IP optimization: {len(ip_optimized_config)} parameters")
        
        # Step 2: Validation
        quick_validation = validation_framework.run_quick_validation()
        print(f"   ✅ Quick validation: {quick_validation['ip_readiness']}")
        
        # Step 3: Patent data generation
        patent_data = ip_agent.get_patent_application_data()
        print(f"   ✅ Patent data: {len(patent_data)} components")
        
        # Step 4: Patent summary
        patent_summary = ip_agent.generate_patent_summary()
        print(f"   ✅ Patent summary: {len(patent_summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main testing function"""
    print("🚀 IP Framework Testing Suite")
    print("=" * 50)
    
    test_results = {}
    
    # Test individual components
    test_results['adaptive_reward_shaping'] = test_adaptive_reward_shaping()
    test_results['hierarchical_rule_evolution'] = test_hierarchical_rule_evolution()
    test_results['confidence_aware_multi_objective'] = test_confidence_aware_multi_objective()
    test_results['ip_enhanced_agent'] = test_ip_enhanced_agent()
    test_results['ip_validation_framework'] = test_ip_validation_framework()
    test_results['integration'] = test_integration()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All IP framework tests passed!")
        print("🚀 Ready for patent application!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed")
        print("🔧 Please fix issues before proceeding")
    
    return test_results

if __name__ == "__main__":
    main()
