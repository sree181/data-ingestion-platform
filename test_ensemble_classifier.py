#!/usr/bin/env python3
"""
Test script for ensemble PV classifier
Demonstrates speed and accuracy improvements
"""

import requests
import json
import time
from typing import List, Dict

# Configuration
PV_SERVICE_URL = "http://localhost:8012"

# Test documents
TEST_DOCUMENTS = [
    {
        "id": "test_1",
        "title": "Ceftazidime-induced liver injury in a 45-year-old male patient",
        "abstract": "We report a case of a 45-year-old male who developed acute liver injury after receiving ceftazidime 2g IV twice daily for pneumonia. Patient presented with jaundice and elevated transaminases (ALT 850 U/L, AST 720 U/L) on day 7 of treatment. Ceftazidime was discontinued and liver function normalized within 2 weeks.",
        "mesh_terms": ["Case Reports", "Drug-Related Side Effects and Adverse Reactions", "Ceftazidime", "Liver Injury"],
        "publication_types": ["Case Reports"]
    },
    {
        "id": "test_2",
        "title": "Systematic review and meta-analysis of statin efficacy in cardiovascular disease prevention",
        "abstract": "We conducted a systematic review of 45 randomized controlled trials involving 120,000 patients to assess statin efficacy. Results show a 25% relative risk reduction in major cardiovascular events. Heterogeneity was low (I² = 12%).",
        "mesh_terms": ["Meta-Analysis", "Randomized Controlled Trial", "Cardiovascular Diseases", "Statins"],
        "publication_types": ["Meta-Analysis", "Systematic Review"]
    },
    {
        "id": "test_3",
        "title": "Molecular docking studies of novel EGFR inhibitors",
        "abstract": "We performed in silico molecular docking analysis of 50 novel compounds against EGFR kinase domain. Compound 23 showed highest binding affinity (-9.2 kcal/mol) with favorable ADME properties predicted by computational methods.",
        "mesh_terms": ["Molecular Docking Simulation", "In Vitro Techniques", "Protein Kinase Inhibitors"],
        "publication_types": ["Research Article"]
    },
    {
        "id": "test_4",
        "title": "Warfarin-associated hemorrhage: a case report",
        "abstract": "A 72-year-old female with atrial fibrillation on warfarin 5mg daily presented with severe epistaxis and INR of 8.5. Warfarin was held and vitamin K administered. Bleeding resolved within 24 hours. Patient had recently started amiodarone which likely caused the drug interaction.",
        "mesh_terms": ["Case Reports", "Warfarin", "Hemorrhage", "Drug Interactions"],
        "publication_types": ["Case Reports"]
    }
]


def test_llm_only(doc: Dict) -> Dict:
    """Test LLM-only classification (original endpoint)"""
    start = time.time()
    
    response = requests.post(
        f"{PV_SERVICE_URL}/api/v1/classify",
        json={"document": doc},
        timeout=30
    )
    
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    if response.status_code == 200:
        result = response.json()
        return {
            "success": True,
            "classification": result['classification']['classification'],
            "confidence": result['classification']['confidence'],
            "time_ms": elapsed,
            "cost_estimate": 0.005  # Approximate LLM cost
        }
    else:
        return {
            "success": False,
            "error": response.text,
            "time_ms": elapsed
        }


def test_ensemble(doc: Dict) -> Dict:
    """Test ensemble classification (new endpoint)"""
    start = time.time()
    
    response = requests.post(
        f"{PV_SERVICE_URL}/api/v1/classify/ensemble",
        json={"document": doc},
        timeout=30
    )
    
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    if response.status_code == 200:
        result = response.json()
        return {
            "success": True,
            "classification": result['classification']['classification'],
            "confidence": result['classification']['confidence'],
            "time_ms": elapsed,
            "models_used": result.get('ensemble_metadata', {}).get('models_used', []),
            "decision_path": result.get('ensemble_metadata', {}).get('decision_path', 'unknown'),
            "cost_estimate": result.get('ensemble_metadata', {}).get('cost_estimate', 0.0),
            "individual_results": result.get('ensemble_metadata', {}).get('individual_results', {})
        }
    else:
        return {
            "success": False,
            "error": response.text,
            "time_ms": elapsed
        }


def print_comparison(doc_id: str, title: str, llm_result: Dict, ensemble_result: Dict):
    """Print comparison between LLM and ensemble"""
    print(f"\n{'='*80}")
    print(f"📄 Document: {title[:60]}...")
    print(f"{'='*80}")
    
    # LLM Results
    print(f"\n🤖 LLM-Only Classification:")
    if llm_result['success']:
        print(f"   Classification: {llm_result['classification']}")
        print(f"   Confidence: {llm_result['confidence']:.2%}")
        print(f"   Time: {llm_result['time_ms']:.0f}ms")
        print(f"   Cost: ${llm_result['cost_estimate']:.4f}")
    else:
        print(f"   ❌ Error: {llm_result.get('error', 'Unknown')}")
    
    # Ensemble Results
    print(f"\n🎯 Ensemble Classification:")
    if ensemble_result['success']:
        print(f"   Classification: {ensemble_result['classification']}")
        print(f"   Confidence: {ensemble_result['confidence']:.2%}")
        print(f"   Time: {ensemble_result['time_ms']:.0f}ms")
        print(f"   Cost: ${ensemble_result['cost_estimate']:.4f}")
        print(f"   Models Used: {', '.join(ensemble_result['models_used'])}")
        print(f"   Decision Path: {ensemble_result['decision_path']}")
        
        # Individual model results
        print(f"\n   📊 Individual Model Results:")
        for model, result in ensemble_result.get('individual_results', {}).items():
            print(f"      {model:15s}: {result['classification']:20s} (conf: {result['confidence']:.2%})")
    else:
        print(f"   ❌ Error: {ensemble_result.get('error', 'Unknown')}")
    
    # Comparison
    if llm_result['success'] and ensemble_result['success']:
        speedup = llm_result['time_ms'] / ensemble_result['time_ms']
        cost_savings = (llm_result['cost_estimate'] - ensemble_result['cost_estimate']) / llm_result['cost_estimate'] * 100
        
        print(f"\n📈 Improvements:")
        print(f"   Speed: {speedup:.1f}x faster")
        print(f"   Cost: {cost_savings:.1f}% savings")
        
        if llm_result['classification'] == ensemble_result['classification']:
            print(f"   Agreement: ✅ Both models agree")
        else:
            print(f"   Agreement: ⚠️  Models disagree (LLM: {llm_result['classification']}, Ensemble: {ensemble_result['classification']})")


def main():
    """Run ensemble classifier tests"""
    print("\n" + "="*80)
    print("🏗️  ENSEMBLE PV CLASSIFIER TEST")
    print("="*80)
    print("\nTesting ensemble classifier vs LLM-only approach...")
    print(f"Service URL: {PV_SERVICE_URL}")
    
    # Check service health
    try:
        health = requests.get(f"{PV_SERVICE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ Service is healthy")
        else:
            print("❌ Service health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return
    
    # Test each document
    total_llm_time = 0
    total_ensemble_time = 0
    total_llm_cost = 0
    total_ensemble_cost = 0
    
    for doc in TEST_DOCUMENTS:
        # Test LLM-only
        llm_result = test_llm_only(doc)
        
        # Test ensemble
        ensemble_result = test_ensemble(doc)
        
        # Print comparison
        print_comparison(doc['id'], doc['title'], llm_result, ensemble_result)
        
        # Aggregate stats
        if llm_result['success']:
            total_llm_time += llm_result['time_ms']
            total_llm_cost += llm_result['cost_estimate']
        
        if ensemble_result['success']:
            total_ensemble_time += ensemble_result['time_ms']
            total_ensemble_cost += ensemble_result['cost_estimate']
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"📊 OVERALL SUMMARY ({len(TEST_DOCUMENTS)} documents)")
    print(f"{'='*80}")
    
    if total_llm_time > 0 and total_ensemble_time > 0:
        avg_speedup = total_llm_time / total_ensemble_time
        cost_savings = (total_llm_cost - total_ensemble_cost) / total_llm_cost * 100
        
        print(f"\n⏱️  Total Time:")
        print(f"   LLM-Only:  {total_llm_time:.0f}ms")
        print(f"   Ensemble:  {total_ensemble_time:.0f}ms")
        print(f"   Speedup:   {avg_speedup:.1f}x faster")
        
        print(f"\n💰 Total Cost:")
        print(f"   LLM-Only:  ${total_llm_cost:.4f}")
        print(f"   Ensemble:  ${total_ensemble_cost:.4f}")
        print(f"   Savings:   {cost_savings:.1f}%")
        
        print(f"\n🎯 Projected Savings (1000 documents):")
        print(f"   Time saved:  {(total_llm_time - total_ensemble_time) * 1000 / len(TEST_DOCUMENTS) / 1000:.1f} seconds")
        print(f"   Cost saved:  ${(total_llm_cost - total_ensemble_cost) * 1000 / len(TEST_DOCUMENTS):.2f}")
    
    print(f"\n{'='*80}")
    print("✅ Test complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

