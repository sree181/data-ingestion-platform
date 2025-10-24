#!/usr/bin/env python3
"""
Test script for RL Data Collection
Demonstrates the data collection pipeline
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.data_collector import RLDataCollectionOrchestrator
from data_collection.feature_extractor import DocumentFeatureExtractor, ClassificationOutcomeTracker
from data_collection.data_validator import DataValidator


def test_feature_extraction():
    """Test the feature extraction component"""
    print("🧪 Testing Feature Extraction...")
    
    # Create feature extractor
    extractor = DocumentFeatureExtractor()
    
    # Sample document data
    sample_document = {
        'title': 'Case report of severe hepatotoxicity in patient taking acetaminophen',
        'abstract': 'A 45-year-old male patient developed severe liver injury after taking acetaminophen for 3 days. The patient presented with jaundice and elevated liver enzymes. The adverse event was temporally related to drug administration.',
        'mesh_terms': ['Case Reports', 'Drug-Induced Liver Injury', 'Acetaminophen', 'Hepatotoxicity'],
        'publication_types': ['Case Report']
    }
    
    # Extract features
    features = extractor.extract_features(sample_document)
    
    print(f"✅ Features extracted successfully!")
    print(f"   Domain: {features.domain}")
    print(f"   Word count: {features.word_count}")
    print(f"   Medical terms: {features.medical_term_count}")
    print(f"   Patient mentions: {features.patient_mentions}")
    print(f"   Drug mentions: {features.drug_mentions}")
    print(f"   Adverse event mentions: {features.adverse_event_mentions}")
    print(f"   ICSR MeSH count: {features.icsr_mesh_count}")
    print(f"   Complexity score: {features.complexity_score:.2f}")
    print(f"   Overall confidence: {features.confidence_indicators['overall_confidence']:.2f}")
    
    return features


def test_outcome_tracking():
    """Test the outcome tracking component"""
    print("\n🧪 Testing Outcome Tracking...")
    
    # Create outcome tracker
    tracker = ClassificationOutcomeTracker()
    
    # Sample classification result
    sample_result = {
        'ensemble_result': 'ICSR',
        'confidence': 0.92,
        'reasoning': 'High confidence: Case Report publication type with ICSR MeSH terms and clear patient-drug-event narrative',
        'models_used': ['rule_based'],
        'decision_path': 'rule_based_only',
        'processing_time_ms': 15,
        'cost_estimate': 0.0
    }
    
    # Track outcome
    outcome = tracker.track_outcome(sample_result, 'ICSR')  # Ground truth
    
    print(f"✅ Outcome tracked successfully!")
    print(f"   Predicted: {outcome.predicted_classification}")
    print(f"   True: {outcome.true_classification}")
    print(f"   Correct: {outcome.is_correct}")
    print(f"   Confidence: {outcome.confidence:.2f}")
    print(f"   Processing time: {outcome.processing_time_ms}ms")
    print(f"   Cost efficiency: {outcome.cost_efficiency:.2f}")
    
    return outcome


def test_data_validation():
    """Test the data validation component"""
    print("\n🧪 Testing Data Validation...")
    
    # Create validator
    validator = DataValidator()
    
    # Sample training data
    sample_training_data = {
        'features': {
            'title': 'Case report of hepatotoxicity',
            'abstract': 'Patient developed liver injury after medication',
            'mesh_terms': ['Case Reports', 'Drug-Induced Liver Injury'],
            'publication_types': ['Case Report'],
            'word_count': 15,
            'sentence_count': 2,
            'technical_term_count': 0,
            'medical_term_count': 5,
            'patient_mentions': 1,
            'drug_mentions': 1,
            'adverse_event_mentions': 1,
            'temporal_mentions': 1,
            'icsr_mesh_count': 2,
            'non_icsr_mesh_count': 0,
            'rejected_signals': 0,
            'domain': 'hepatology',
            'complexity_score': 0.3,
            'confidence_indicators': {
                'icsr_evidence_strength': 0.8,
                'icsr_mesh_ratio': 1.0,
                'temporal_evidence': 0.6,
                'overall_confidence': 0.8
            }
        },
        'outcome': {
            'true_classification': 'ICSR',
            'predicted_classification': 'ICSR',
            'confidence': 0.92,
            'reasoning': 'High confidence rule-based classification',
            'models_used': ['rule_based'],
            'decision_path': 'rule_based_only',
            'processing_time_ms': 15,
            'cost_estimate': 0.0,
            'is_correct': True,
            'confidence_penalty': 0.92,
            'cost_efficiency': 1.0
        },
        'data_id': 'test_001'
    }
    
    # Validate data
    result = validator.validate_training_data(sample_training_data)
    
    print(f"✅ Data validation completed!")
    print(f"   Valid: {result.is_valid}")
    print(f"   Quality score: {result.quality_score:.2f}")
    print(f"   Issues: {len(result.issues)}")
    print(f"   Warnings: {len(result.warnings)}")
    
    if result.issues:
        print("   Issues found:")
        for issue in result.issues:
            print(f"     - {issue}")
    
    if result.warnings:
        print("   Warnings:")
        for warning in result.warnings:
            print(f"     - {warning}")
    
    return result


async def test_full_pipeline():
    """Test the complete data collection pipeline"""
    print("\n🧪 Testing Full Data Collection Pipeline...")
    
    # Create orchestrator
    orchestrator = RLDataCollectionOrchestrator(output_dir="rl_optimization/test_data")
    
    # Test simulation
    print("   Running simulation...")
    report = await orchestrator.collect_from_classification_service(
        "http://localhost:8012",
        max_documents=20,
        batch_size=5
    )
    
    print(f"✅ Pipeline test completed!")
    print(f"   Total collected: {report['collection_summary']['total_collected']}")
    print(f"   Valid entries: {report['collection_summary']['valid_entries']}")
    print(f"   Valid rate: {report['collection_summary']['valid_rate']:.2%}")
    print(f"   Average quality score: {report['collection_summary']['avg_quality_score']:.2f}")
    
    # Show domain distribution
    print("   Domain distribution:")
    for domain, count in report['domain_distribution'].items():
        print(f"     {domain}: {count}")
    
    # Show classification distribution
    print("   Classification distribution:")
    for classification, count in report['classification_distribution'].items():
        print(f"     {classification}: {count}")
    
    # Show recommendations
    if report['recommendations']:
        print("   Recommendations:")
        for rec in report['recommendations']:
            print(f"     - {rec}")
    
    return report


async def test_elasticsearch_simulation():
    """Test Elasticsearch data collection simulation"""
    print("\n🧪 Testing Elasticsearch Data Collection...")
    
    # Create orchestrator
    orchestrator = RLDataCollectionOrchestrator(output_dir="rl_optimization/test_data")
    
    # Test Elasticsearch simulation
    print("   Running Elasticsearch simulation...")
    report = await orchestrator.collect_from_elasticsearch(
        "http://localhost:9200",
        "documents",
        max_documents=15
    )
    
    print(f"✅ Elasticsearch test completed!")
    print(f"   Total collected: {report['collection_summary']['total_collected']}")
    print(f"   Valid entries: {report['collection_summary']['valid_entries']}")
    print(f"   Valid rate: {report['collection_summary']['valid_rate']:.2%}")
    
    return report


async def test_file_collection():
    """Test file-based data collection"""
    print("\n🧪 Testing File Data Collection...")
    
    # Create sample data file
    sample_data = [
        {
            'title': 'File Document 1',
            'abstract': 'This is a test document from file collection.',
            'mesh_terms': ['Case Reports'],
            'publication_types': ['Case Report'],
            'classification': 'ICSR',
            'classification_confidence': 0.85,
            'reasoning': 'File-based classification',
            'models_used': ['rule_based'],
            'decision_path': 'rule_based_only',
            'processing_time_ms': 10,
            'cost_estimate': 0.0,
            'true_classification': 'ICSR'
        },
        {
            'title': 'File Document 2',
            'abstract': 'Another test document for file collection.',
            'mesh_terms': ['Review'],
            'publication_types': ['Review'],
            'classification': 'Non-ICSR',
            'classification_confidence': 0.78,
            'reasoning': 'File-based classification',
            'models_used': ['rule_based'],
            'decision_path': 'rule_based_only',
            'processing_time_ms': 12,
            'cost_estimate': 0.0,
            'true_classification': 'Non-ICSR'
        }
    ]
    
    # Save sample data to file
    test_file = "rl_optimization/test_data/sample_classification_data.json"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"   Sample data saved to: {test_file}")
    
    # Test file collection
    orchestrator = RLDataCollectionOrchestrator(output_dir="rl_optimization/test_data")
    
    # Run the test
    report = await orchestrator.collect_from_file(test_file)
    
    print(f"✅ File collection test completed!")
    print(f"   Total collected: {report['collection_summary']['total_collected']}")
    print(f"   Valid entries: {report['collection_summary']['valid_entries']}")
    print(f"   Valid rate: {report['collection_summary']['valid_rate']:.2%}")
    
    return report


async def main():
    """Run all tests"""
    print("🚀 Starting RL Data Collection Tests\n")
    
    try:
        # Test individual components
        features = test_feature_extraction()
        outcome = test_outcome_tracking()
        validation = test_data_validation()
        
        # Test full pipeline
        pipeline_report = await test_full_pipeline()
        
        # Test Elasticsearch simulation
        es_report = await test_elasticsearch_simulation()
        
        # Test file collection
        file_report = await test_file_collection()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"   Feature extraction: ✅")
        print(f"   Outcome tracking: ✅")
        print(f"   Data validation: ✅")
        print(f"   Full pipeline: ✅")
        print(f"   Elasticsearch simulation: ✅")
        print(f"   File collection: ✅")
        
        print("\n📁 Output files saved to: rl_optimization/test_data/")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
