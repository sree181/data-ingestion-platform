#!/usr/bin/env python3
"""
Test Force Ensemble Mode
Tests classification with force_ensemble=True to ensure all 3 models run
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test documents
TEST_DOCUMENTS = [
    {
        "title": "Severe allergic rash in a 45-year-old patient after penicillin",
        "abstract": "A 45-year-old male developed widespread urticaria 2 hours after receiving penicillin for pneumonia. The rash resolved upon discontinuation of the antibiotic.",
        "mesh_terms": ["Drug Hypersensitivity", "Urticaria"],
        "publication_types": ["Case Reports"],
        "expected_class": "ICSR"
    },
    {
        "title": "Safety and tolerability of Drug X in Phase III trial",
        "abstract": "450 patients received Drug X. Adverse events included headache (12%), nausea (8%). This study provides safety data from a large clinical trial population.",
        "mesh_terms": ["Clinical Trials, Phase III", "Drug Safety"],
        "publication_types": ["Clinical Trial"],
        "expected_class": "Safety_Information"
    },
    {
        "title": "Mechanisms of drug-induced liver injury: a review",
        "abstract": "This review discusses molecular pathways involved in hepatotoxicity, including mechanisms of cellular damage and repair processes.",
        "mesh_terms": ["Hepatotoxicity", "Review Literature"],
        "publication_types": ["Review"],
        "expected_class": "Non-ICSR"
    }
]

async def test_force_ensemble():
    """Test classification with force_ensemble enabled"""
    
    print("="*80)
    print("FORCE ENSEMBLE MODE TEST")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, doc in enumerate(TEST_DOCUMENTS, 1):
            print(f"\n{'='*80}")
            print(f"TEST CASE {idx}: {doc['title'][:60]}...")
            print(f"{'='*80}")
            print(f"Expected Classification: {doc['expected_class']}")
            
            # Test with force_ensemble=True
            print("\n🔥 Testing with force_ensemble=True...")
            
            request_data = {
                "document": {
                    "id": f"test-doc-{idx}",
                    "title": doc["title"],
                    "abstract": doc["abstract"],
                    "mesh_terms": doc["mesh_terms"],
                    "publication_types": doc["publication_types"]
                },
                "force_ensemble": True  # Force all 3 models to run
            }
            
            try:
                response = await client.post(
                    "http://localhost:8012/api/v1/classify/ensemble",
                    json=request_data
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract results
                classification = result.get("classification", {}).get("classification")
                confidence = result.get("classification", {}).get("confidence")
                ensemble_meta = result.get("ensemble_metadata", {})
                models_used = ensemble_meta.get("models_used", [])
                decision_path = ensemble_meta.get("decision_path", "")
                individual_results = ensemble_meta.get("individual_results", {})
                processing_time_ms = ensemble_meta.get("processing_time_ms", 0)
                cost = ensemble_meta.get("cost_estimate", 0.0)
                
                # Verify all 3 models ran
                print(f"\n📊 RESULTS:")
                print(f"   Final Classification: {classification} ({confidence:.2f} confidence)")
                print(f"   Models Used: {models_used}")
                print(f"   Decision Path: {decision_path}")
                print(f"   Processing Time: {processing_time_ms}ms")
                print(f"   Cost: ${cost:.4f}")
                
                # Check if all 3 models ran
                expected_models = ['rule_based', 'bert', 'llm']
                all_models_ran = all(model in models_used for model in expected_models)
                
                if all_models_ran:
                    print(f"\n   ✅ SUCCESS: All 3 models ran (Rule, BERT, LLM)")
                else:
                    print(f"\n   ❌ FAIL: Not all models ran. Expected {expected_models}, got {models_used}")
                
                # Display per-model results
                if individual_results:
                    print(f"\n   📋 PER-MODEL RESULTS:")
                    for model_name in ['rule_based', 'bert', 'llm']:
                        model_result = individual_results.get(model_name)
                        if model_result:
                            model_class = model_result.get('classification')
                            model_conf = model_result.get('confidence', 0.0)
                            model_reason = (model_result.get('reasoning', 'N/A')[:80] + '...') if len(model_result.get('reasoning', '')) > 80 else model_result.get('reasoning', 'N/A')
                            print(f"      • {model_name.upper()}: {model_class} ({model_conf:.2f}) - {model_reason}")
                        else:
                            print(f"      • {model_name.upper()}: MISSING")
                    
                    # Verify individual_results has all 3 models
                    if len(individual_results) >= 3:
                        print(f"\n   ✅ SUCCESS: individual_results contains all model breakdowns")
                    else:
                        print(f"\n   ❌ FAIL: individual_results incomplete. Expected 3 models, got {len(individual_results)}")
                else:
                    print(f"\n   ❌ FAIL: individual_results is empty")
                
                # Check classification accuracy
                if classification == doc["expected_class"]:
                    print(f"\n   ✅ Classification matches expected class: {doc['expected_class']}")
                else:
                    print(f"\n   ⚠️  Classification mismatch: Expected {doc['expected_class']}, got {classification}")
                
            except httpx.HTTPStatusError as e:
                print(f"\n   ❌ HTTP ERROR: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"\n   ❌ ERROR: {str(e)}")
        
        # Summary
        print(f"\n\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print("Force ensemble mode ensures that all 3 models (Rule-based, BERT, LLM)")
        print("run for every document, providing full transparency and allowing")
        print("users to see how each model voted before the final ensemble decision.")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_force_ensemble())

