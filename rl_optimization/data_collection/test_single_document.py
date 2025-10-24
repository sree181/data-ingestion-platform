#!/usr/bin/env python3
"""
Test single document classification to verify API format
"""

import requests
import json

# Configuration
CLASSIFICATION_URL = "http://localhost:8012/api/v1/classify/ensemble"

def test_single_document():
    """Test classification of a single document"""
    
    # Test document
    test_doc = {
        "document": {
            "id": "test_doc_001",
            "title": "Case Report: Severe Hepatotoxicity Induced by Acetaminophen",
            "abstract": "A 45-year-old male developed severe liver injury after taking an overdose of acetaminophen. Patient presented with jaundice and elevated liver enzymes. Drug was discontinued.",
            "mesh_terms": ["Case Reports", "Drug-Induced Liver Injury", "Acetaminophen"],
            "publication_types": ["Case Reports"]
        }
    }
    
    print("🧪 Testing single document classification...")
    print(f"Title: {test_doc['document']['title']}")
    print(f"Abstract: {test_doc['document']['abstract'][:100]}...")
    
    try:
        response = requests.post(
            CLASSIFICATION_URL,
            json=test_doc,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Classification successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Extract key information
            classification_data = result.get('classification', {})
            ensemble_metadata = result.get('ensemble_metadata', {})
            
            print(f"\n📊 Results:")
            print(f"Classification: {classification_data.get('classification', 'Unknown')}")
            print(f"Confidence: {classification_data.get('confidence', 0.0):.2f}")
            print(f"Models used: {ensemble_metadata.get('models_used', [])}")
            print(f"Processing time: {ensemble_metadata.get('processing_time_ms', 0)}ms")
            
        else:
            print(f"❌ Classification failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_document()
