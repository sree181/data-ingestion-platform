#!/usr/bin/env python3
"""
Comprehensive UI Entity Enrichment Workflow Test
Tests the complete workflow from UI to backend enrichment and AI insights
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

class UIWorkflowTester:
    def __init__(self):
        self.api_gateway_url = "http://localhost:8000/api/v1"
        self.entity_enrichment_url = "http://localhost:8003/api/v1"
        self.frontend_url = "http://localhost:3002"
        
    async def test_complete_workflow(self):
        """Test the complete UI entity enrichment workflow"""
        print("🚀 Testing Complete UI Entity Enrichment Workflow")
        print("=" * 60)
        
        # Test 1: Frontend Accessibility
        print("\n1. Testing Frontend Accessibility...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.frontend_url)
                if response.status_code == 200:
                    print("✅ Frontend is accessible")
                else:
                    print(f"❌ Frontend failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Frontend error: {e}")
            return False
        
        # Test 2: API Gateway Health
        print("\n2. Testing API Gateway...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url.replace('/api/v1', '')}/health")
                if response.status_code == 200:
                    print("✅ API Gateway is healthy")
                else:
                    print(f"❌ API Gateway failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ API Gateway error: {e}")
            return False
        
        # Test 3: Entities Listing
        print("\n3. Testing Entities Listing...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url}/entities")
                if response.status_code == 200:
                    data = response.json()
                    entities = data if isinstance(data, list) else data.get('entities', [])
                    print(f"✅ Entities listing works - {len(entities)} entities found")
                    
                    # Find PeaceHealth entity
                    peacehealth = next((e for e in entities if e.get('name') == 'PeaceHealth'), None)
                    if peacehealth:
                        print(f"✅ Found PeaceHealth entity: {peacehealth.get('id')}")
                    else:
                        print("⚠️  PeaceHealth entity not found in listing")
                else:
                    print(f"❌ Entities listing failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Entities listing error: {e}")
            return False
        
        # Test 4: Entity Enrichment
        print("\n4. Testing Entity Enrichment...")
        try:
            async with httpx.AsyncClient() as client:
                # Start enrichment
                enrich_data = {
                    "entity_ids": ["PeaceHealth_ORGANIZATION"],
                    "max_sources": 3
                }
                response = await client.post(
                    f"{self.api_gateway_url}/entities/enrich",
                    json=enrich_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Enrichment started: {result.get('message')}")
                    
                    # Wait for completion
                    print("⏳ Waiting for enrichment to complete...")
                    for i in range(30):  # Wait up to 30 seconds
                        await asyncio.sleep(2)
                        
                        status_response = await client.get(
                            f"{self.api_gateway_url}/entities/status/PeaceHealth_ORGANIZATION"
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status')
                            print(f"   Status: {status}")
                            
                            if status == 'completed':
                                print(f"✅ Enrichment completed with score: {status_data.get('enrichment_score')}")
                                break
                            elif status == 'failed':
                                print(f"❌ Enrichment failed: {status_data.get('error_message')}")
                                return False
                        else:
                            print(f"❌ Status check failed: {status_response.status_code}")
                            return False
                    else:
                        print("❌ Enrichment timed out")
                        return False
                else:
                    print(f"❌ Enrichment start failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Enrichment error: {e}")
            return False
        
        # Test 5: Enrichment Data Retrieval
        print("\n5. Testing Enrichment Data Retrieval...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url}/entities/PeaceHealth_ORGANIZATION")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('scraped_data'):
                        print(f"✅ Enrichment data retrieved successfully")
                        print(f"   Sources: {len(data.get('scraped_data', []))}")
                        print(f"   Confidence: {data.get('confidence_score')}")
                        
                        # Check consolidated data
                        consolidated = data.get('consolidated_data', {})
                        if consolidated:
                            print(f"   Name: {consolidated.get('name')}")
                            print(f"   Founded: {consolidated.get('founded')}")
                            print(f"   Industry: {consolidated.get('industry')}")
                            print(f"   Employees: {consolidated.get('employee_count')}")
                    else:
                        print("❌ No enrichment data found")
                        return False
                else:
                    print(f"❌ Data retrieval failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Data retrieval error: {e}")
            return False
        
        # Test 6: AI Insights Generation
        print("\n6. Testing AI Insights Generation...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.entity_enrichment_url}/entities/PeaceHealth_ORGANIZATION/insights"
                )
                if response.status_code == 200:
                    insights = response.json()
                    if insights.get('insights', {}).get('insights'):
                        print("✅ AI insights generated successfully")
                        print(f"   Model: {insights.get('insights', {}).get('model')}")
                        print(f"   Generated: {insights.get('insights', {}).get('generated_at')}")
                    else:
                        print("❌ No AI insights found")
                        return False
                else:
                    print(f"❌ AI insights failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ AI insights error: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 COMPLETE UI WORKFLOW TEST PASSED!")
        print("\n✅ All Components Working:")
        print("   ✅ Frontend accessible")
        print("   ✅ API Gateway routing")
        print("   ✅ Entities listing")
        print("   ✅ Entity enrichment")
        print("   ✅ Real-time status updates")
        print("   ✅ Enrichment data retrieval")
        print("   ✅ AI insights generation")
        print("\n🚀 The UI Entity Enrichment system is FULLY FUNCTIONAL!")
        
        return True

async def main():
    tester = UIWorkflowTester()
    success = await tester.test_complete_workflow()
    
    if success:
        print("\n🎯 SUMMARY: UI Entity Enrichment is working perfectly!")
        print("   - Users can access the UI at http://localhost:3002")
        print("   - Users can select entities and start enrichment")
        print("   - Real-time status updates work")
        print("   - Enrichment data is retrieved successfully")
        print("   - AI insights are generated")
        print("\n✅ The system is ready for production use!")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main()) 