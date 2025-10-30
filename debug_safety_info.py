"""
Debug script to test Safety_Information classification
"""

import sys
from pathlib import Path

# Add service path
sys.path.append(str(Path(__file__).parent / "services" / "pv-classification-service"))

from rule_based_classifier import rule_based_classifier

# Test document from test suite (Safety_Info - Clinical Trial)
test_doc = {
    "title": "Safety and tolerability of Drug X in patients with rheumatoid arthritis: results from a Phase III clinical trial",
    "abstract": "This randomized, double-blind, placebo-controlled Phase III study evaluated the safety profile of Drug X in 450 patients with active rheumatoid arthritis. Adverse events were reported in 60% of patients in the Drug X group vs. 40% in placebo. Most common adverse events were headache and nausea. No new safety signals were identified.",
    "mesh_terms": ["Clinical Trials, Phase III", "Drug Safety", "Rheumatoid Arthritis"],
    "publication_types": ["Clinical Trial", "Randomized Controlled Trial"]
}

print("=" * 80)
print("DEBUG: Safety_Information Classification")
print("=" * 80)

print("\n📄 Test Document:")
print(f"Title: {test_doc['title'][:80]}...")
print(f"MeSH Terms: {test_doc['mesh_terms']}")
print(f"Publication Types: {test_doc['publication_types']}")

# Classify
classification, confidence, reasoning, evidence = rule_based_classifier.classify(
    test_doc['title'],
    test_doc['abstract'],
    test_doc['mesh_terms'],
    test_doc['publication_types']
)

print("\n🔍 Evidence Scores:")
for key, value in evidence.items():
    print(f"  {key}: {value}")

print("\n📊 Classification Result:")
print(f"  Classification: {classification}")
print(f"  Confidence: {confidence}")
print(f"  Reasoning: {reasoning}")

print("\n🔬 Checking Safety_Information Signals:")

# Check publication types
pub_types_set = set(test_doc['publication_types'])
safety_pub_types = rule_based_classifier.SAFETY_INFO_PUBLICATION_TYPES

print(f"\n  Input pub_types: {pub_types_set}")
print(f"  Safety pub_types: {safety_pub_types}")
print(f"  Intersection: {pub_types_set & safety_pub_types}")
print(f"  Match found: {bool(pub_types_set & safety_pub_types)}")

# Check MeSH terms
mesh_set = set(test_doc['mesh_terms'])
safety_mesh = rule_based_classifier.SAFETY_INFO_MESH_TERMS

print(f"\n  Input MeSH: {mesh_set}")
print(f"  Safety MeSH: {safety_mesh}")
print(f"  Intersection: {mesh_set & safety_mesh}")
print(f"  Match found: {bool(mesh_set & safety_mesh)}")

# Check keywords
text = f"{test_doc['title']} {test_doc['abstract']}".lower()
safety_keywords = rule_based_classifier.SAFETY_INFO_KEYWORDS

print(f"\n  Safety keywords: {safety_keywords}")
found_keywords = [kw for kw in safety_keywords if kw in text]
print(f"  Found keywords: {found_keywords}")
print(f"  Count: {len(found_keywords)}")

print("\n" + "=" * 80)
print("Expected: Safety_Information")
print(f"Actual: {classification}")
print(f"Match: {'✅ PASS' if classification == 'Safety_Information' else '❌ FAIL'}")
print("=" * 80)

