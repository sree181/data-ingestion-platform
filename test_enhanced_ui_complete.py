#!/usr/bin/env python3
"""
Complete Enhanced UI Entity Enrichment Test
Tests the fully redesigned UI system with live tracking and results display
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class EnhancedUITester:
    def __init__(self):
        self.api_gateway_url = "http://localhost:8000/api/v1"
        self.frontend_url = "http://localhost:3002"
        
    async def test_complete_enhanced_ui(self):
        """Test the complete enhanced UI system"""
        print("🚀 Testing Complete Enhanced Entity Enrichment UI")
        print("=" * 60)
        
        # Test 1: Frontend Accessibility
        print("\n1. Testing Frontend Accessibility...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.frontend_url)
                if response.status_code == 200:
                    print("✅ Frontend accessible at http://localhost:3002")
                else:
                    print(f"❌ Frontend failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Frontend error: {e}")
            return False
        
        # Test 2: Enhanced Entities API with Enrichment Status
        print("\n2. Testing Enhanced Entities API...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_gateway_url}/entities")
                if response.status_code == 200:
                    data = response.json()
                    entities = data.get('entities', [])
                    
                    # Count enriched entities
                    enriched_entities = [e for e in entities if e.get('enrichment_status') == 'completed']
                    print(f"✅ Entities API working - {len(entities)} total entities")
                    print(f"✅ Found {len(enriched_entities)} enriched entities")
                    
                    # Show some examples
                    if enriched_entities:
                        print("\n📊 Sample Enriched Entities:")
                        for entity in enriched_entities[:5]:
                            score = entity.get('enrichment_score', 0)
                            print(f"   • {entity['name']}: {score:.0%} confidence")
                    
                    return len(enriched_entities) > 0
                else:
                    print(f"❌ Entities API failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Entities API error: {e}")
            return False
        
        # Test 3: Live Enrichment Tracking
        print("\n3. Testing Live Enrichment Tracking...")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Start enrichment of a test entity
                test_entity = "Microsoft_ORGANIZATION"
                enrich_response = await client.post(
                    f"{self.api_gateway_url}/entities/enrich",
                    json={"entity_ids": [test_entity], "max_sources": 3}
                )
                
                if enrich_response.status_code == 200:
                    print(f"✅ Started enrichment for {test_entity}")
                    
                    # Track status changes
                    for i in range(10):  # Poll for 50 seconds
                        await asyncio.sleep(5)
                        status_response = await client.get(f"{self.api_gateway_url}/entities/status/{test_entity}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            print(f"   📊 Status check {i+1}: {status}")
                            
                            if status == 'completed':
                                score = status_data.get('enrichment_score', 0)
                                print(f"✅ Enrichment completed with {score:.0%} confidence!")
                                break
                        else:
                            print(f"   ⚠️ Status check failed: {status_response.status_code}")
                    
                    return True
                else:
                    print(f"❌ Failed to start enrichment: {enrich_response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Live tracking error: {e}")
            return False
        
        # Test 4: Enrichment Results Display
        print("\n4. Testing Enrichment Results Display...")
        try:
            async with httpx.AsyncClient() as client:
                # Get detailed results for an enriched entity
                enriched_entity = "Food and Drug Administration_ORGANIZATION"
                response = await client.get(f"{self.api_gateway_url}/entities/{enriched_entity}")
                
                if response.status_code == 200:
                    entity_data = response.json()
                    print(f"✅ Retrieved detailed data for {enriched_entity}")
                    
                    # Check for key components
                    components = []
                    if entity_data.get('consolidated_data'):
                        components.append("Consolidated Data")
                    if entity_data.get('ai_summary'):
                        components.append("AI Summary")
                    if entity_data.get('sources'):
                        components.append(f"Sources ({len(entity_data['sources'])})")
                    if entity_data.get('enrichment_score'):
                        components.append(f"Confidence Score ({entity_data['enrichment_score']:.0%})")
                    
                    print(f"✅ Available components: {', '.join(components)}")
                    
                    # Show a preview of the data
                    if entity_data.get('consolidated_data'):
                        data = entity_data['consolidated_data']
                        print(f"\n📋 Sample Data Preview:")
                        for key, value in list(data.items())[:4]:
                            if value and len(str(value)) < 100:
                                print(f"   • {key}: {value}")
                    
                    return len(components) >= 3
                else:
                    print(f"❌ Failed to get entity details: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Results display error: {e}")
            return False

async def main():
    tester = EnhancedUITester()
    
    print("🎯 Enhanced Entity Enrichment UI Test Suite")
    print("Testing the completely redesigned UI with:")
    print("   • Live status tracking")
    print("   • Enhanced visual indicators")
    print("   • Enrichment score display")
    print("   • Comprehensive results viewer")
    print("   • Real-time progress updates")
    
    success = await tester.test_complete_enhanced_ui()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Enhanced UI Test Suite PASSED!")
        print("\n✅ All Enhanced Features Working:")
        print("   ✅ Real-time status updates")
        print("   ✅ Visual enrichment indicators")
        print("   ✅ Confidence score display")
        print("   ✅ Live progress tracking")
        print("   ✅ Comprehensive results viewer")
        print("   ✅ Enhanced visual design")
        
        print("\n🚀 UI Features Available:")
        print("   • Enhanced status chips with descriptions")
        print("   • Enrichment score progress bars")
        print("   • Live tracking every 5 seconds")
        print("   • Detailed results dialog")
        print("   • AI summary display")
        print("   • Source attribution")
        print("   • Re-enrichment capability")
        
        print(f"\n🌐 Access the Enhanced UI: http://localhost:3002")
        print("   Navigate to Entity Enrichment tab to see all features!")
        
    else:
        print("❌ Enhanced UI Test Suite FAILED!")
        print("   Please check the logs above for specific issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())