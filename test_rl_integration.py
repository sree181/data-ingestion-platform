#!/usr/bin/env python3
"""
RL Integration Test Script
Tests the complete RL-enhanced classification pipeline
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add project paths
sys.path.append('/Users/sreehasgopinathan/Documents/Auburn/Project/Data_Ingestion')

class RLIntegrationTester:
    """Test RL-enhanced classification integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def test_rl_classification(self) -> Dict[str, Any]:
        """Test single document RL classification"""
        print("🧪 Testing RL Classification...")
        
        test_document = {
            "title": "Severe adverse drug reaction in cardiac patients following medication administration",
            "abstract": "Case study of life-threatening adverse events in patients with cardiovascular disease after receiving new medication. Patient experienced severe cardiac arrhythmia and required immediate intervention.",
            "mesh_terms": ["Cardiovascular Diseases", "Adverse Drug Reaction", "Drug Toxicity", "Cardiac Arrhythmia"],
            "publication_types": ["Case Reports"],
            "journal": "Journal of Clinical Pharmacology"
        }
        
        request_data = {
            "document": test_document,
            "document_id": f"test_rl_{int(time.time())}",
            "enable_rl_optimization": True,
            "cost_budget": 0.01,
            "performance_targets": {
                "accuracy": 0.9,
                "cost_efficiency": 0.8
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/rl/classify",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Classification successful")
                print(f"   Classification: {result['classification']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   Models used: {result['models_used']}")
                print(f"   RL decision path: {result['rl_decision_path']}")
                print(f"   Processing time: {result['processing_time']:.3f}s")
                print(f"   RL optimization: {result['rl_optimization_applied']}")
                
                return {
                    "test": "rl_classification",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Classification failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_classification",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Classification error: {str(e)}")
            return {
                "test": "rl_classification",
                "status": "error",
                "error": str(e)
            }
    
    def test_rl_batch_classification(self) -> Dict[str, Any]:
        """Test batch RL classification"""
        print("\n🧪 Testing RL Batch Classification...")
        
        test_documents = [
            {
                "title": "Adverse drug reaction in oncology patients",
                "abstract": "Study of adverse events in cancer patients receiving chemotherapy",
                "mesh_terms": ["Neoplasms", "Antineoplastic Agents", "Adverse Drug Reaction"],
                "publication_types": ["Case Reports"]
            },
            {
                "title": "Systematic review of drug safety",
                "abstract": "Comprehensive review of drug safety profiles across multiple studies",
                "mesh_terms": ["Drug Safety", "Systematic Review", "Pharmacovigilance"],
                "publication_types": ["Review"]
            },
            {
                "title": "Clinical trial of new medication",
                "abstract": "Randomized controlled trial of new medication for hypertension",
                "mesh_terms": ["Hypertension", "Clinical Trial", "Randomized Controlled Trial"],
                "publication_types": ["Clinical Trial"]
            }
        ]
        
        request_data = {
            "documents": test_documents,
            "enable_rl_optimization": True,
            "cost_budget": 0.05,
            "performance_targets": {
                "accuracy": 0.85,
                "cost_efficiency": 0.7
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/rl/classify/batch",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Batch Classification successful")
                print(f"   Total documents: {result['total_documents']}")
                print(f"   Successful: {result['successful_classifications']}")
                print(f"   Failed: {result['failed_classifications']}")
                print(f"   Total cost: ${result['total_cost']:.4f}")
                print(f"   Average processing time: {result['average_processing_time']:.3f}s")
                
                return {
                    "test": "rl_batch_classification",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Batch Classification failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_batch_classification",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Batch Classification error: {str(e)}")
            return {
                "test": "rl_batch_classification",
                "status": "error",
                "error": str(e)
            }
    
    def test_rl_metrics(self) -> Dict[str, Any]:
        """Test RL metrics endpoint"""
        print("\n🧪 Testing RL Metrics...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rl/metrics",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Metrics retrieved successfully")
                
                # Check if we have performance data
                if 'performance_summary' in result:
                    summary = result['performance_summary']
                    if 'current_metrics' in summary:
                        metrics = summary['current_metrics']
                        print(f"   Current accuracy: {metrics.get('accuracy', 0):.3f}")
                        print(f"   Current cost efficiency: {metrics.get('cost_efficiency', 0):.3f}")
                        print(f"   Current processing speed: {metrics.get('processing_speed', 0):.3f}")
                        print(f"   Current domain specialization: {metrics.get('domain_specialization', 0):.3f}")
                
                return {
                    "test": "rl_metrics",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Metrics failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_metrics",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Metrics error: {str(e)}")
            return {
                "test": "rl_metrics",
                "status": "error",
                "error": str(e)
            }
    
    def test_rl_health(self) -> Dict[str, Any]:
        """Test RL health check"""
        print("\n🧪 Testing RL Health Check...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rl/health",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Health check successful")
                print(f"   Status: {result.get('status', 'unknown')}")
                print(f"   RL controller available: {result.get('rl_controller_available', False)}")
                print(f"   Monitoring active: {result.get('monitoring_active', False)}")
                
                return {
                    "test": "rl_health",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Health check failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_health",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Health check error: {str(e)}")
            return {
                "test": "rl_health",
                "status": "error",
                "error": str(e)
            }
    
    def test_rl_alerts(self) -> Dict[str, Any]:
        """Test RL alerts endpoint"""
        print("\n🧪 Testing RL Alerts...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rl/alerts",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Alerts retrieved successfully")
                print(f"   Total alerts: {result.get('total_alerts', 0)}")
                print(f"   Alerts by type: {result.get('alerts_by_type', {})}")
                
                return {
                    "test": "rl_alerts",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Alerts failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_alerts",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Alerts error: {str(e)}")
            return {
                "test": "rl_alerts",
                "status": "error",
                "error": str(e)
            }
    
    def test_performance_report(self) -> Dict[str, Any]:
        """Test RL performance report generation"""
        print("\n🧪 Testing RL Performance Report...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rl/performance-report",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RL Performance report generated successfully")
                print(f"   Generated at: {result.get('generated_at', 'unknown')}")
                print(f"   Visualizations: {len(result.get('visualizations', []))}")
                print(f"   Recommendations: {len(result.get('recommendations', []))}")
                
                return {
                    "test": "rl_performance_report",
                    "status": "success",
                    "result": result
                }
            else:
                print(f"❌ RL Performance report failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {
                    "test": "rl_performance_report",
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            print(f"❌ RL Performance report error: {str(e)}")
            return {
                "test": "rl_performance_report",
                "status": "error",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all RL integration tests"""
        print("🚀 Starting RL Integration Tests")
        print("=" * 50)
        
        # Test sequence
        tests = [
            self.test_rl_health,
            self.test_rl_classification,
            self.test_rl_batch_classification,
            self.test_rl_metrics,
            self.test_rl_alerts,
            self.test_performance_report
        ]
        
        results = []
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
                self.test_results.append(result)
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
                results.append({
                    "test": test_func.__name__,
                    "status": "crashed",
                    "error": str(e)
                })
                self.test_results.append({
                    "test": test_func.__name__,
                    "status": "crashed",
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 RL Integration Test Summary")
        print("=" * 50)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['status'] == 'success')
        failed_tests = sum(1 for r in results if r['status'] == 'failed')
        error_tests = sum(1 for r in results if r['status'] in ['error', 'crashed'])
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"rl_integration_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_summary': {
                    'total_tests': total_tests,
                    'successful': successful_tests,
                    'failed': failed_tests,
                    'errors': error_tests,
                    'success_rate': successful_tests/total_tests*100
                },
                'test_results': results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful': successful_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': successful_tests/total_tests*100
            },
            'results': results
        }

def main():
    """Main test function"""
    print("🤖 RL-Enhanced Classification Integration Test")
    print("=" * 60)
    
    # Check if service is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ PV Classification Service is not running!")
            print("   Please start the service first:")
            print("   cd services/pv-classification-service")
            print("   python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to PV Classification Service!")
        print("   Please start the service first:")
        print("   cd services/pv-classification-service")
        print("   python main.py")
        return
    
    # Run tests
    tester = RLIntegrationTester()
    results = tester.run_all_tests()
    
    # Final status
    if results['summary']['success_rate'] >= 80:
        print("\n🎉 RL Integration Tests PASSED!")
        print("   The RL-enhanced classification system is working correctly.")
    else:
        print("\n⚠️  RL Integration Tests PARTIALLY PASSED")
        print("   Some tests failed. Check the results for details.")
    
    return results

if __name__ == "__main__":
    main()
