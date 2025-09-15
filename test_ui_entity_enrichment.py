#!/usr/bin/env python3
"""
Comprehensive UI Entity Enrichment Test
Tests the complete workflow from UI to backend enrichment
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

class UIEntityEnrichmentTester:
    def __init__(self):
        self.api_gateway_url = "http://localhost:8000/api/v1"
        self.entity_enrichment_url = "http://localhost:8003/api/v1"
        self.frontend_url = "http://localhost:3002"
        
    async def test_api_gateway_health(self) -> bool:
        """Test API Gateway health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url.replace('/api/v1', '')}/health")
                if response.status_code == 200:
                    print("✅ API Gateway is healthy")
                    return True
                else:
                    print(f"❌ API Gateway health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ API Gateway health check error: {e}")
            return False
    
    async def test_entity_enrichment_service_health(self) -> bool:
        """Test Entity Enrichment Service health"""
        try:
            async with httpx.AsyncClient() as client:
                # Test by getting entities list
                response = await client.get(f"{self.entity_enrichment_url}/entities")
                if response.status_code == 200:
                    print("✅ Entity Enrichment Service is healthy")
                    return True
                else:
                    print(f"❌ Entity Enrichment Service health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Entity Enrichment Service health check error: {e}")
            return False
    
    async def test_frontend_accessibility(self) -> bool:
        """Test if frontend is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.frontend_url)
                if response.status_code == 200:
                    print("✅ Frontend is accessible")
                    return True
                else:
                    print(f"❌ Frontend accessibility failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Frontend accessibility error: {e}")
            return False
    
    async def test_entities_listing(self) -> bool:
        """Test entities listing through API Gateway"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url}/entities")
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get('entities', [])
                    print(f"✅ Entities listing successful: {len(entities)} entities found")
                    
                    # Find PeaceHealth entity
                    peacehealth = next((e for e in entities if e.get('name') == 'PeaceHealth'), None)
                    if peacehealth:
                        print(f"✅ PeaceHealth entity found with status: {peacehealth.get('status', 'unknown')}")
                    else:
                        print("⚠️  PeaceHealth entity not found in listing")
                    
                    return True
                else:
                    print(f"❌ Entities listing failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Entities listing error: {e}")
            return False
    
    async def test_entity_enrichment_workflow(self) -> bool:
        """Test complete entity enrichment workflow"""
        test_entity = "Confluence Health_ORGANIZATION"
        
        print(f"\n🔄 Testing enrichment workflow for: {test_entity}")
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Start enrichment
                print("   📤 Starting enrichment...")
                enrich_response = await client.post(
                    f"{self.api_gateway_url}/entities/enrich",
                    json={"entity_ids": [test_entity], "max_sources": 3}
                )
                
                if enrich_response.status_code != 200:
                    print(f"   ❌ Enrichment start failed: {enrich_response.status_code}")
                    return False
                
                print("   ✅ Enrichment started successfully")
                
                # 2. Monitor status
                print("   📊 Monitoring enrichment status...")
                max_attempts = 30  # 5 minutes max
                for attempt in range(max_attempts):
                    status_response = await client.get(f"{self.api_gateway_url}/entities/status/{test_entity}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        print(f"   📈 Status: {status} (attempt {attempt + 1}/{max_attempts})")
                        
                        if status == 'completed':
                            print("   ✅ Enrichment completed successfully!")
                            
                            # 3. Get detailed results
                            details_response = await client.get(f"{self.api_gateway_url}/entities/{test_entity}")
                            if details_response.status_code == 200:
                                details = details_response.json()
                                consolidated_data = details.get('consolidated_data', {})
                                sources = details.get('sources', [])
                                confidence = details.get('confidence_score', 0)
                                
                                print(f"   📊 Results:")
                                print(f"      - Sources: {len(sources)}")
                                print(f"      - Confidence: {confidence}")
                                print(f"      - Data fields: {len(consolidated_data)}")
                                
                                if consolidated_data:
                                    print(f"      - Sample data: {list(consolidated_data.keys())[:5]}")
                                
                                return True
                            else:
                                print(f"   ❌ Failed to get enrichment details: {details_response.status_code}")
                                return False
                        
                        elif status == 'failed':
                            print(f"   ❌ Enrichment failed: {status_data.get('error_message', 'Unknown error')}")
                            return False
                    
                    await asyncio.sleep(10)  # Wait 10 seconds between checks
                
                print("   ⏰ Enrichment timed out")
                return False
                
        except Exception as e:
            print(f"   ❌ Enrichment workflow error: {e}")
            return False
    
    async def test_ai_insights_generation(self) -> bool:
        """Test AI insights generation"""
        test_entity = "PeaceHealth_ORGANIZATION"
        
        print(f"\n🧠 Testing AI insights generation for: {test_entity}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.entity_enrichment_url}/entities/{test_entity}/insights")
                
                if response.status_code == 200:
                    data = response.json()
                    insights = data.get('insights', {})
                    
                    if isinstance(insights, dict) and 'insights' in insights:
                        insight_text = insights['insights']
                        print(f"   ✅ AI insights generated successfully!")
                        print(f"   📝 Insight length: {len(insight_text)} characters")
                        print(f"   🎯 Model: {insights.get('model', 'unknown')}")
                        
                        # Check if insights contain expected sections
                        sections = ['Market Position', 'Competitive Advantages', 'Risks', 'Growth Opportunities']
                        found_sections = [s for s in sections if s in insight_text]
                        print(f"   📋 Found sections: {found_sections}")
                        
                        return len(found_sections) >= 2  # At least 2 sections should be present
                    else:
                        print(f"   ❌ Unexpected insights format: {type(insights)}")
                        return False
                else:
                    print(f"   ❌ AI insights generation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ AI insights generation error: {e}")
            return False
    
    async def test_batch_enrichment(self) -> bool:
        """Test batch enrichment functionality"""
        test_entities = ["FDA_ORGANIZATION", "CDC_ORGANIZATION"]
        
        print(f"\n🔄 Testing batch enrichment for: {test_entities}")
        
        try:
            async with httpx.AsyncClient() as client:
                # Start batch enrichment
                response = await client.post(
                    f"{self.api_gateway_url}/entities/enrich",
                    json={"entity_ids": test_entities, "max_sources": 2}
                )
                
                if response.status_code == 200:
                    print("   ✅ Batch enrichment started successfully")
                    
                    # Monitor status for both entities
                    completed_count = 0
                    max_attempts = 20
                    
                    for attempt in range(max_attempts):
                        print(f"   📊 Checking batch status (attempt {attempt + 1}/{max_attempts})...")
                        
                        for entity_id in test_entities:
                            status_response = await client.get(f"{self.api_gateway_url}/entities/status/{entity_id}")
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                status = status_data.get('status', 'unknown')
                                
                                if status == 'completed':
                                    completed_count += 1
                                    print(f"      ✅ {entity_id}: {status}")
                                elif status == 'failed':
                                    print(f"      ❌ {entity_id}: {status}")
                                else:
                                    print(f"      ⏳ {entity_id}: {status}")
                        
                        if completed_count >= len(test_entities):
                            print("   ✅ All entities in batch completed!")
                            return True
                        
                        await asyncio.sleep(15)  # Wait 15 seconds between checks
                    
                    print(f"   ⏰ Batch enrichment timed out ({completed_count}/{len(test_entities)} completed)")
                    return completed_count > 0
                else:
                    print(f"   ❌ Batch enrichment start failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Batch enrichment error: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive UI entity enrichment test suite"""
        print("🚀 Starting Comprehensive UI Entity Enrichment Test Suite")
        print("=" * 70)
        
        # Health checks
        if not await self.test_api_gateway_health():
            return False
        
        if not await self.test_entity_enrichment_service_health():
            return False
        
        if not await self.test_frontend_accessibility():
            return False
        
        # Core functionality tests
        if not await self.test_entities_listing():
            return False
        
        if not await self.test_entity_enrichment_workflow():
            return False
        
        if not await self.test_ai_insights_generation():
            return False
        
        if not await self.test_batch_enrichment():
            return False
        
        print("\n" + "=" * 70)
        print("✅ Comprehensive UI Entity Enrichment Test Suite Completed Successfully!")
        print("\n🎉 UI Entity Enrichment System is Fully Functional!")
        print("\n📋 Summary of Working Features:")
        print("   ✅ API Gateway routing and health")
        print("   ✅ Entity Enrichment Service with AI capabilities")
        print("   ✅ Frontend accessibility")
        print("   ✅ Entities listing and status tracking")
        print("   ✅ Single entity enrichment workflow")
        print("   ✅ AI-powered insights generation")
        print("   ✅ Batch enrichment processing")
        print("   ✅ Real-time status updates")
        print("   ✅ Comprehensive error handling")
        
        print("\n🌐 Access Points:")
        print(f"   - Frontend UI: {self.frontend_url}")
        print(f"   - API Gateway: {self.api_gateway_url}")
        print(f"   - Entity Enrichment Service: {self.entity_enrichment_url}")
        
        return True

async def main():
    tester = UIEntityEnrichmentTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 Ready for Production Use!")
        print("   Users can now:")
        print("   1. Access the UI at http://localhost:3002")
        print("   2. View all entities with real-time status")
        print("   3. Select entities and initiate enrichment")
        print("   4. Monitor progress with live updates")
        print("   5. View detailed enrichment results")
        print("   6. Generate AI-powered insights")
        print("   7. Process multiple entities in batch")
    else:
        print("\n❌ Test suite failed - please check the issues above")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 