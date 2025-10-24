#!/usr/bin/env python3
"""
Show a complete training dataset example
"""

import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.feature_extractor import DocumentFeatureExtractor, ClassificationOutcomeTracker
from data_collection.data_validator import DataValidator

# Configuration
CLASSIFICATION_URL = "http://localhost:8012/api/v1/classify/ensemble"

def show_training_example():
    """Show a complete training dataset example"""
    
    # Initialize components
    feature_extractor = DocumentFeatureExtractor()
    outcome_tracker = ClassificationOutcomeTracker()
    validator = DataValidator()
    
    # Example document
    document_data = {
        "title": "Case Report: Severe Hepatotoxicity Induced by Acetaminophen Overdose",
        "abstract": "A 45-year-old male patient presented to the emergency department with severe jaundice, elevated liver enzymes (ALT 2500 U/L, AST 1800 U/L), and signs of acute liver failure following an intentional acetaminophen overdose of 15g taken 24 hours prior. The patient had no known liver disease. Physical examination revealed icteric sclera, hepatomegaly, and mild ascites. Laboratory findings showed elevated bilirubin (8.5 mg/dL), prolonged prothrombin time (INR 2.8), and thrombocytopenia. The patient was diagnosed with acetaminophen-induced acute liver injury and treated with N-acetylcysteine. Despite aggressive supportive care, the patient developed hepatic encephalopathy and required liver transplantation. This case highlights the severe hepatotoxicity that can occur with acetaminophen overdose and the importance of early recognition and treatment.",
        "mesh_terms": [
            "Case Reports",
            "Drug-Induced Liver Injury", 
            "Acetaminophen",
            "Acute Liver Failure",
            "Chemical and Drug Induced Liver Injury",
            "Hepatotoxicity",
            "Liver Transplantation"
        ],
        "publication_types": ["Case Reports"]
    }
    
    print("📄 EXAMPLE TRAINING DATASET ENTRY")
    print("=" * 80)
    print(f"Title: {document_data['title']}")
    print(f"Abstract: {document_data['abstract'][:200]}...")
    print(f"MeSH Terms: {document_data['mesh_terms']}")
    print(f"Publication Types: {document_data['publication_types']}")
    print()
    
    # Classify document
    payload = {
        "document": {
            "id": "example_doc_001",
            "title": document_data["title"],
            "abstract": document_data["abstract"],
            "mesh_terms": document_data["mesh_terms"],
            "publication_types": document_data["publication_types"]
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
            
            print("🔍 CLASSIFICATION RESULT:")
            print(f"Classification: {classification_result['classification']}")
            print(f"Confidence: {classification_result['classification_confidence']:.2f}")
            print(f"Models Used: {classification_result['models_used']}")
            print(f"Processing Time: {classification_result['processing_time_ms']}ms")
            print(f"Cost: ${classification_result['cost_estimate']:.4f}")
            print()
            
            # Extract features
            features = feature_extractor.extract_features(document_data)
            print("🧬 EXTRACTED FEATURES:")
            print(f"Domain: {features.domain}")
            print(f"Word Count: {features.word_count}")
            print(f"Sentence Count: {features.sentence_count}")
            print(f"Technical Terms: {features.technical_term_count}")
            print(f"Medical Terms: {features.medical_term_count}")
            print(f"Patient Mentions: {features.patient_mentions}")
            print(f"Drug Mentions: {features.drug_mentions}")
            print(f"Adverse Event Mentions: {features.adverse_event_mentions}")
            print(f"Temporal Mentions: {features.temporal_mentions}")
            print(f"ICSR MeSH Count: {features.icsr_mesh_count}")
            print(f"Non-ICSR MeSH Count: {features.non_icsr_mesh_count}")
            print(f"Rejected Signals: {features.rejected_signals}")
            print(f"Complexity Score: {features.complexity_score:.3f}")
            print(f"Confidence Indicators: {features.confidence_indicators}")
            print()
            
            # Track outcome
            outcome = outcome_tracker.track_outcome(classification_result, None)
            print("📊 CLASSIFICATION OUTCOME:")
            print(f"Predicted Classification: {outcome.predicted_classification}")
            print(f"True Classification: {outcome.true_classification}")
            print(f"Confidence: {outcome.confidence:.2f}")
            print(f"Reasoning: {outcome.reasoning}")
            print(f"Models Used: {outcome.models_used}")
            print(f"Decision Path: {outcome.decision_path}")
            print(f"Processing Time: {outcome.processing_time_ms}ms")
            print(f"Cost Estimate: ${outcome.cost_estimate:.4f}")
            print(f"Is Correct: {outcome.is_correct}")
            print(f"Confidence Penalty: {outcome.confidence_penalty:.3f}")
            print(f"Cost Efficiency: {outcome.cost_efficiency:.3f}")
            print()
            
            # Create complete training data
            training_data = {
                'features': features,
                'outcome': outcome,
                'collected_at': datetime.utcnow(),
                'data_id': f"{features.title[:50]}_{datetime.utcnow().timestamp()}"
            }
            
            # Validate
            validation_result = validator.validate_training_data(training_data)
            print("✅ VALIDATION RESULT:")
            print(f"Is Valid: {validation_result.is_valid}")
            print(f"Quality Score: {validation_result.quality_score:.2f}")
            print(f"Validation Messages: {validation_result.messages}")
            print()
            
            # Show complete JSON structure
            print("📋 COMPLETE TRAINING DATA STRUCTURE:")
            print("=" * 80)
            
            # Convert to serializable format
            serializable_data = {
                'features': {
                    'title': features.title,
                    'abstract': features.abstract,
                    'mesh_terms': features.mesh_terms,
                    'publication_types': features.publication_types,
                    'word_count': features.word_count,
                    'sentence_count': features.sentence_count,
                    'technical_term_count': features.technical_term_count,
                    'medical_term_count': features.medical_term_count,
                    'patient_mentions': features.patient_mentions,
                    'drug_mentions': features.drug_mentions,
                    'adverse_event_mentions': features.adverse_event_mentions,
                    'temporal_mentions': features.temporal_mentions,
                    'icsr_mesh_count': features.icsr_mesh_count,
                    'non_icsr_mesh_count': features.non_icsr_mesh_count,
                    'rejected_signals': features.rejected_signals,
                    'domain': features.domain,
                    'complexity_score': features.complexity_score,
                    'confidence_indicators': features.confidence_indicators,
                    'extracted_at': features.extracted_at.isoformat()
                },
                'outcome': {
                    'true_classification': outcome.true_classification,
                    'predicted_classification': outcome.predicted_classification,
                    'confidence': outcome.confidence,
                    'reasoning': outcome.reasoning,
                    'models_used': outcome.models_used,
                    'decision_path': outcome.decision_path,
                    'processing_time_ms': outcome.processing_time_ms,
                    'cost_estimate': outcome.cost_estimate,
                    'is_correct': outcome.is_correct,
                    'confidence_penalty': outcome.confidence_penalty,
                    'cost_efficiency': outcome.cost_efficiency,
                    'classified_at': outcome.classified_at.isoformat()
                },
                'collected_at': training_data['collected_at'].isoformat(),
                'data_id': training_data['data_id']
            }
            
            print(json.dumps(serializable_data, indent=2))
            
        else:
            print(f"❌ Classification failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_training_example()
