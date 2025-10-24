#!/usr/bin/env python3
"""
Test fixed data collection with a few documents
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.data_collector import RLDataCollectionOrchestrator
from data_collection.feature_extractor import DocumentFeatureExtractor, ClassificationOutcomeTracker
from data_collection.data_validator import DataValidator

# Configuration
CLASSIFICATION_URL = "http://localhost:8012/api/v1/classify/ensemble"

def test_fixed_collection():
    """Test the fixed data collection with a few documents"""
    
    # Initialize components
    rl_orchestrator = RLDataCollectionOrchestrator(output_dir="rl_optimization/test_fixed_data")
    feature_extractor = DocumentFeatureExtractor()
    outcome_tracker = ClassificationOutcomeTracker()
    validator = DataValidator()
    
    # Test documents
    test_documents = [
        {
            "title": "Case Report: Severe Hepatotoxicity Induced by Acetaminophen",
            "abstract": "A 45-year-old male developed severe liver injury after taking an overdose of acetaminophen. Patient presented with jaundice and elevated liver enzymes. Drug was discontinued.",
            "mesh_terms": ["Case Reports", "Drug-Induced Liver Injury", "Acetaminophen"],
            "publication_types": ["Case Reports"]
        },
        {
            "title": "Randomized Controlled Trial: Efficacy of New Antihypertensive Drug",
            "abstract": "A multicenter, randomized, double-blind, placebo-controlled trial was conducted to evaluate the efficacy and safety of a new drug for hypertension in 500 patients.",
            "mesh_terms": ["Randomized Controlled Trial", "Hypertension", "Antihypertensive Agents"],
            "publication_types": ["Randomized Controlled Trial"]
        }
    ]
    
    print("🧪 Testing fixed data collection...")
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 Testing document {i}: {doc['title'][:50]}...")
        
        # Classify document
        payload = {
            "document": {
                "id": f"test_doc_{i}",
                "title": doc["title"],
                "abstract": doc["abstract"],
                "mesh_terms": doc["mesh_terms"],
                "publication_types": doc["publication_types"]
            }
        }
        
        try:
            response = requests.post(CLASSIFICATION_URL, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract classification data
                classification_data = result.get('classification', {})
                ensemble_metadata = result.get('ensemble_metadata', {})
                
                classification_result = {
                    'classification': classification_data.get('classification', 'Unknown'),
                    'classification_confidence': classification_data.get('confidence', 0.0),
                    'reasoning': classification_data.get('reasoning', ''),
                    'models_used': ensemble_metadata.get('models_used', []),
                    'decision_path': ensemble_metadata.get('decision_path', 'unknown'),
                    'processing_time_ms': ensemble_metadata.get('processing_time_ms', 0),
                    'cost_estimate': ensemble_metadata.get('cost_estimate', 0.0)
                }
                
                print(f"   ✅ Classification: {classification_result['classification']} ({classification_result['classification_confidence']:.2f})")
                
                # Collect training data
                training_data = rl_orchestrator.data_collector.collect_training_data(
                    doc, classification_result, None
                )
                
                # Validate
                validation_result = validator.validate_training_data(training_data)
                
                print(f"   ✅ Data collected and validated (Quality: {validation_result.quality_score:.2f})")
                print(f"   📊 Features: {training_data['features'].domain}, {training_data['features'].word_count} words")
                print(f"   📊 Outcome: {training_data['outcome'].predicted_classification}, confidence: {training_data['outcome'].confidence:.2f}")
                
            else:
                print(f"   ❌ Classification failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 Fixed data collection test complete!")

if __name__ == "__main__":
    test_fixed_collection()
