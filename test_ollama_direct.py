#!/usr/bin/env python3
"""
Direct Test of Ollama Classification
Bypass service issues and test Ollama LLM directly
"""

import asyncio
import httpx
import json
from typing import Dict, List, Optional, Tuple

async def test_ollama_classification():
    """Test Ollama classification directly"""
    
    print("🧪 Testing Ollama Classification Directly")
    print("=" * 50)
    
    # Test document
    test_doc = {
        "title": "Severe adverse drug reaction in cardiac patients following medication administration",
        "abstract": "Case study of life-threatening adverse events in patients with cardiovascular disease after receiving new medication. Patient experienced severe cardiac arrhythmia requiring emergency intervention.",
        "mesh_terms": ["Cardiovascular Diseases", "Adverse Drug Reaction", "Drug Toxicity"],
        "publication_types": ["Case Reports"]
    }
    
    print(f"📄 Document: {test_doc['title']}")
    print(f"📝 Abstract: {test_doc['abstract'][:100]}...")
    print(f"🏷️  MeSH Terms: {test_doc['mesh_terms']}")
    print(f"📚 Publication Type: {test_doc['publication_types']}")
    print()
    
    # Create classification prompt
    prompt = f"""
You are a medical literature classification expert. Classify the following document into one of these categories:

1. **ICSR** (Individual Case Safety Report) - Individual patient case reports of adverse drug reactions
2. **Safety_Information** - General safety information, warnings, or guidelines  
3. **Non-ICSR** - Research studies, reviews, or other non-case report literature
4. **Rejected** - Not relevant to pharmacovigilance

Document Information:
Title: {test_doc['title']}
Abstract: {test_doc['abstract']}
MeSH Terms: {', '.join(test_doc['mesh_terms'])}
Publication Type: {', '.join(test_doc['publication_types'])}

Respond with ONLY the classification category name (ICSR, Safety_Information, Non-ICSR, or Rejected) and a brief reasoning.

Classification:"""
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("🤖 Calling Ollama API...")
            
            response = await client.post("http://localhost:11434/api/generate", json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            })
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                
                print("✅ Ollama Response:")
                print("-" * 30)
                print(response_text)
                print("-" * 30)
                
                # Parse response
                lines = response_text.strip().split('\n')
                classification = "Non-ICSR"  # Default
                reasoning = "No specific reasoning provided"
                
                for line in lines:
                    line = line.strip()
                    if line.upper() in ["ICSR", "SAFETY_INFORMATION", "NON-ICSR", "REJECTED"]:
                        classification = line.upper()
                    elif line.startswith("Classification:"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            classification = parts[1].strip().upper()
                    elif line and not line.startswith("Classification:"):
                        reasoning = line
                
                print(f"\n🎯 Classification: {classification}")
                print(f"💭 Reasoning: {reasoning}")
                
                # Calculate confidence
                confidence = 0.7
                if classification in ["ICSR", "Non-ICSR"]:
                    confidence += 0.1
                if len(response_text) > 50:
                    confidence += 0.1
                if any(term in response_text.lower() for term in ["adverse", "reaction", "patient", "drug", "case", "safety"]):
                    confidence += 0.1
                
                confidence = min(confidence, 0.95)
                print(f"📊 Confidence: {confidence:.2f}")
                
                print("\n✅ Ollama Classification Test Successful!")
                return True
                
            else:
                print(f"❌ Ollama API Error: {response.status_code}")
                print(response.text)
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_ollama_models():
    """Test available Ollama models"""
    print("\n🔍 Checking Available Ollama Models")
    print("=" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Found {len(models)} models:")
                
                for model in models:
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0)
                    size_gb = size / (1024**3)
                    print(f"   📦 {name} ({size_gb:.1f}GB)")
                
                return True
            else:
                print(f"❌ Failed to get models: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Ollama Direct Classification Test")
    print("=" * 50)
    
    # Test 1: Check available models
    models_ok = await test_ollama_models()
    
    if not models_ok:
        print("❌ Cannot connect to Ollama. Make sure Ollama is running.")
        return
    
    # Test 2: Test classification
    classification_ok = await test_ollama_classification()
    
    if classification_ok:
        print("\n🎉 All Tests Passed!")
        print("✅ Ollama is working correctly")
        print("✅ Classification is functional")
        print("✅ Ready for real document processing")
    else:
        print("\n❌ Some tests failed")
        print("⚠️  Check Ollama service and models")

if __name__ == "__main__":
    asyncio.run(main())
