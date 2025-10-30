#!/usr/bin/env python3
"""
Test Real Documents with RL-Enhanced Intelligence
Process real medical documents using the RL-enhanced classification system
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class RealDocumentProcessor:
    """Process real documents with RL-enhanced intelligence"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def test_real_document_classification(self):
        """Test with real medical document"""
        print("🧪 Testing Real Document Classification with RL Intelligence")
        print("=" * 60)
        
        # Real medical document from our collected data
        real_document = {
            "title": "Severe adverse drug reaction in cardiac patients following medication administration",
            "abstract": "Case study of life-threatening adverse events in patients with cardiovascular disease after receiving new medication. Patient experienced severe cardiac arrhythmia and required immediate intervention. The adverse reaction was temporally associated with medication administration and resolved upon discontinuation.",
            "mesh_terms": ["Cardiovascular Diseases", "Adverse Drug Reaction", "Drug Toxicity", "Cardiac Arrhythmia", "Drug-Related Side Effects and Adverse Reactions"],
            "publication_types": ["Case Reports"],
            "journal": "Journal of Clinical Pharmacology"
        }
        
        print(f"📄 Document: {real_document['title']}")
        print(f"📝 Abstract: {real_document['abstract'][:100]}...")
        print(f"🏷️  MeSH Terms: {real_document['mesh_terms']}")
        print(f"📚 Publication Type: {real_document['publication_types']}")
        print()
        
        # Test with RL-enhanced classification
        request_data = {
            "document": real_document,
            "document_id": f"real_doc_{int(time.time())}",
            "enable_rl_optimization": True,
            "cost_budget": 0.01,
            "performance_targets": {
                "accuracy": 0.9,
                "cost_efficiency": 0.8
            }
        }
        
        try:
            print("🤖 Sending to RL-Enhanced Classification System...")
            response = requests.post(
                f"{self.base_url}/api/v1/rl/classify",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ RL Classification Successful!")
                print("=" * 40)
                print(f"🎯 Classification: {result['classification']}")
                print(f"📊 Confidence: {result['confidence']:.3f}")
                print(f"🧠 Reasoning: {result['reasoning']}")
                print(f"🔧 Models Used: {result['models_used']}")
                print(f"🛤️  RL Decision Path: {result['rl_decision_path']}")
                print(f"⏱️  Processing Time: {result['processing_time']:.3f}s")
                print(f"💰 Cost Estimate: ${result['cost_estimate']:.4f}")
                print(f"🤖 RL Optimization: {result['rl_optimization_applied']}")
                
                # Performance metrics
                if 'performance_metrics' in result:
                    metrics = result['performance_metrics']
                    print("\n📈 Performance Metrics:")
                    print(f"   • Accuracy: {metrics.get('accuracy', 0):.3f}")
                    print(f"   • Cost Efficiency: {metrics.get('cost_efficiency', 0):.3f}")
                    print(f"   • Processing Speed: {metrics.get('processing_speed', 0):.3f}")
                    print(f"   • Domain Specialization: {metrics.get('domain_specialization', 0):.3f}")
                
                return result
            else:
                print(f"❌ Classification failed: {response.status_code}")
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_batch_real_documents(self):
        """Test with multiple real documents"""
        print("\n🧪 Testing Batch Real Document Classification")
        print("=" * 50)
        
        # Multiple real medical documents
        real_documents = [
            {
                "title": "Adverse drug reaction in oncology patients receiving chemotherapy",
                "abstract": "Study of adverse events in cancer patients receiving chemotherapy treatment. Multiple cases of severe toxicity reported.",
                "mesh_terms": ["Neoplasms", "Antineoplastic Agents", "Adverse Drug Reaction", "Drug Toxicity"],
                "publication_types": ["Case Reports"]
            },
            {
                "title": "Systematic review of drug safety in cardiovascular medicine",
                "abstract": "Comprehensive review of drug safety profiles in cardiovascular medicine across multiple clinical trials.",
                "mesh_terms": ["Cardiovascular Diseases", "Drug Safety", "Systematic Review", "Pharmacovigilance"],
                "publication_types": ["Review"]
            },
            {
                "title": "Clinical trial of new antihypertensive medication",
                "abstract": "Randomized controlled trial of new medication for hypertension treatment in elderly patients.",
                "mesh_terms": ["Hypertension", "Clinical Trial", "Randomized Controlled Trial", "Antihypertensive Agents"],
                "publication_types": ["Clinical Trial"]
            }
        ]
        
        request_data = {
            "documents": real_documents,
            "enable_rl_optimization": True,
            "cost_budget": 0.05,
            "performance_targets": {
                "accuracy": 0.85,
                "cost_efficiency": 0.7
            }
        }
        
        try:
            print("🤖 Sending batch to RL-Enhanced Classification System...")
            response = requests.post(
                f"{self.base_url}/api/v1/rl/classify/batch",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Batch RL Classification Successful!")
                print("=" * 40)
                print(f"📊 Total Documents: {result['total_documents']}")
                print(f"✅ Successful: {result['successful_classifications']}")
                print(f"❌ Failed: {result['failed_classifications']}")
                print(f"💰 Total Cost: ${result['total_cost']:.4f}")
                print(f"⏱️  Average Processing Time: {result['average_processing_time']:.3f}s")
                
                # Show individual results
                print("\n📋 Individual Classifications:")
                for i, classification in enumerate(result['classifications']):
                    print(f"   {i+1}. {classification['classification']} (confidence: {classification['confidence']:.3f})")
                
                return result
            else:
                print(f"❌ Batch classification failed: {response.status_code}")
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def test_rl_metrics(self):
        """Test RL metrics and monitoring"""
        print("\n🧪 Testing RL Metrics and Monitoring")
        print("=" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rl/metrics",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ RL Metrics Retrieved!")
                
                if 'performance_summary' in result:
                    summary = result['performance_summary']
                    if 'current_metrics' in summary:
                        metrics = summary['current_metrics']
                        print(f"📊 Current Performance:")
                        print(f"   • Accuracy: {metrics.get('accuracy', 0):.3f}")
                        print(f"   • Cost Efficiency: {metrics.get('cost_efficiency', 0):.3f}")
                        print(f"   • Processing Speed: {metrics.get('processing_speed', 0):.3f}")
                        print(f"   • Domain Specialization: {metrics.get('domain_specialization', 0):.3f}")
                
                return result
            else:
                print(f"❌ Metrics failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def run_complete_test(self):
        """Run complete real document processing test"""
        print("🚀 Real Document Processing with RL-Enhanced Intelligence")
        print("=" * 70)
        
        # Test single document
        single_result = self.test_real_document_classification()
        
        # Test batch documents
        batch_result = self.test_batch_real_documents()
        
        # Test metrics
        metrics_result = self.test_rl_metrics()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 30)
        print(f"✅ Single Document: {'Success' if single_result else 'Failed'}")
        print(f"✅ Batch Processing: {'Success' if batch_result else 'Failed'}")
        print(f"✅ Metrics Monitoring: {'Success' if metrics_result else 'Failed'}")
        
        if single_result and batch_result and metrics_result:
            print("\n🎉 All tests passed! RL-enhanced intelligence is working!")
            return True
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
            return False

def main():
    """Main test function"""
    processor = RealDocumentProcessor()
    
    # Check if service is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service not running! Please start the service first.")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to service! Please start the service first.")
        return
    
    # Run tests
    success = processor.run_complete_test()
    
    if success:
        print("\n🎯 RL-Enhanced Intelligence is successfully processing real documents!")
    else:
        print("\n⚠️  Some issues detected. Check the service logs.")

if __name__ == "__main__":
    main()
