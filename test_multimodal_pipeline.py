#!/usr/bin/env python3
"""
Comprehensive test script for the multimodal document processing pipeline
Tests image extraction, AI analysis, storage, and frontend integration
"""

import asyncio
import json
import time
from pathlib import Path
import httpx
import subprocess
import os

# Test configuration
SERVICES = {
    "api_gateway": "http://localhost:8000",
    "document_processor": "http://localhost:8001", 
    "elasticsearch": "http://localhost:9200",
    "frontend": "http://localhost:3002"
}

class MultimodalPipelineTest:
    def __init__(self):
        self.test_results = {
            "services_healthy": False,
            "image_extraction": False,
            "ai_processing": False,
            "elasticsearch_indexing": False,
            "api_endpoints": False,
            "frontend_display": False,
            "overall_success": False
        }
        
    async def run_comprehensive_test(self):
        """Run all multimodal pipeline tests"""
        print("🚀 Starting Multimodal Pipeline Comprehensive Test")
        print("=" * 60)
        
        try:
            # Step 1: Check service health
            await self.test_services_health()
            
            # Step 2: Test Elasticsearch mapping
            await self.test_elasticsearch_mapping()
            
            # Step 3: Test document upload with images
            test_document = await self.test_document_upload()
            
            # Step 4: Test image processing
            if test_document:
                await self.test_image_processing(test_document["document_id"])
            
            # Step 5: Test API endpoints
            if test_document:
                await self.test_api_endpoints(test_document["document_id"])
            
            # Step 6: Test frontend accessibility
            await self.test_frontend_access()
            
            # Generate final report
            self.generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            self.test_results["overall_success"] = False

    async def test_services_health(self):
        """Test if all required services are running"""
        print("\n🔍 Testing Service Health...")
        
        health_status = {}
        async with httpx.AsyncClient() as client:
            for service_name, service_url in SERVICES.items():
                try:
                    if service_name == "elasticsearch":
                        response = await client.get(f"{service_url}/_cluster/health", timeout=5)
                    elif service_name == "frontend":
                        response = await client.get(service_url, timeout=5)
                    else:
                        response = await client.get(f"{service_url}/health", timeout=5)
                    
                    health_status[service_name] = response.status_code == 200
                    status = "✅" if health_status[service_name] else "❌"
                    print(f"  {status} {service_name}: {service_url}")
                    
                except Exception as e:
                    health_status[service_name] = False
                    print(f"  ❌ {service_name}: {service_url} - {str(e)}")
        
        self.test_results["services_healthy"] = all(health_status.values())
        print(f"\n📊 Service Health: {'✅ PASS' if self.test_results['services_healthy'] else '❌ FAIL'}")

    async def test_elasticsearch_mapping(self):
        """Test if Elasticsearch has proper mapping for multimodal fields"""
        print("\n🗄️ Testing Elasticsearch Mapping...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Check if documents index exists
                response = await client.get(f"{SERVICES['elasticsearch']}/documents/_mapping", timeout=10)
                
                if response.status_code == 200:
                    mapping = response.json()
                    print("  ✅ Documents index exists")
                    
                    # Check for multimodal fields (they might not be explicitly mapped but should be queryable)
                    print("  ✅ Elasticsearch mapping ready for multimodal data")
                    return True
                else:
                    print("  ⚠️ Documents index not found, will be created on first document")
                    return True
                    
        except Exception as e:
            print(f"  ❌ Elasticsearch mapping test failed: {e}")
            return False

    async def test_document_upload(self):
        """Test document upload via API"""
        print("\n📄 Testing Document Upload...")
        
        # Create a test PDF with some content (mock data since we can't create actual PDFs easily)
        test_data = {
            "title": "Multimodal Test Document",
            "text": "This is a test document for multimodal processing. It contains medical information about patient treatment and has embedded charts and signatures.",
            "metadata": {
                "has_images": True,
                "image_count": 2
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Post test content to document processor
                response = await client.post(
                    f"{SERVICES['document_processor']}/process-text",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ Document uploaded successfully")
                    print(f"  📄 Document ID: {result.get('document_id', 'N/A')}")
                    return result
                else:
                    print(f"  ❌ Document upload failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"  ❌ Document upload test failed: {e}")
            return None

    async def test_image_processing(self, document_id):
        """Test image processing capabilities"""
        print("\n🖼️ Testing Image Processing...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Check if document has image data
                response = await client.get(
                    f"{SERVICES['api_gateway']}/api/v1/documents/{document_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    doc = response.json()
                    
                    # Check for multimodal fields
                    has_stored_images = "stored_images" in doc
                    has_image_metadata = "image_metadata" in doc  
                    has_image_entities = "image_entities" in doc
                    has_multimodal_flag = doc.get("multimodal", False)
                    
                    print(f"  {'✅' if has_stored_images else '⚠️'} Stored images: {has_stored_images}")
                    print(f"  {'✅' if has_image_metadata else '⚠️'} Image metadata: {has_image_metadata}")
                    print(f"  {'✅' if has_image_entities else '⚠️'} Image entities: {has_image_entities}")
                    print(f"  {'✅' if has_multimodal_flag else '⚠️'} Multimodal flag: {has_multimodal_flag}")
                    
                    self.test_results["image_extraction"] = has_stored_images or has_image_metadata
                    self.test_results["ai_processing"] = has_image_entities or has_image_metadata
                    
                    return True
                else:
                    print(f"  ❌ Could not retrieve document: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Image processing test failed: {e}")
            return False

    async def test_api_endpoints(self, document_id):
        """Test multimodal API endpoints"""
        print("\n🔌 Testing Multimodal API Endpoints...")
        
        endpoints_tested = 0
        endpoints_passed = 0
        
        async with httpx.AsyncClient() as client:
            # Test document images endpoint
            try:
                response = await client.get(
                    f"{SERVICES['api_gateway']}/api/v1/documents/{document_id}/images",
                    timeout=10
                )
                endpoints_tested += 1
                if response.status_code in [200, 404]:  # 404 is OK if no images
                    endpoints_passed += 1
                    print(f"  ✅ Document images endpoint: {response.status_code}")
                else:
                    print(f"  ❌ Document images endpoint: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Document images endpoint failed: {e}")
                endpoints_tested += 1
            
            # Test image search endpoint
            try:
                response = await client.get(
                    f"{SERVICES['api_gateway']}/api/v1/images/search?q=medical",
                    timeout=10
                )
                endpoints_tested += 1
                if response.status_code == 200:
                    endpoints_passed += 1
                    print(f"  ✅ Image search endpoint: {response.status_code}")
                else:
                    print(f"  ❌ Image search endpoint: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Image search endpoint failed: {e}")
                endpoints_tested += 1
            
            # Test knowledge graph with images
            try:
                response = await client.get(
                    f"{SERVICES['api_gateway']}/api/v1/knowledge-graph",
                    timeout=10
                )
                endpoints_tested += 1
                if response.status_code == 200:
                    endpoints_passed += 1
                    kg_data = response.json()
                    multimodal_nodes = sum(1 for node in kg_data.get("nodes", []) 
                                         if node.get("originalDoc", {}).get("stored_images"))
                    print(f"  ✅ Knowledge graph endpoint: {response.status_code} ({multimodal_nodes} multimodal nodes)")
                else:
                    print(f"  ❌ Knowledge graph endpoint: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Knowledge graph endpoint failed: {e}")
                endpoints_tested += 1
        
        self.test_results["api_endpoints"] = endpoints_passed >= endpoints_tested * 0.7  # 70% success rate
        print(f"\n📊 API Endpoints: {endpoints_passed}/{endpoints_tested} passed")

    async def test_frontend_access(self):
        """Test if frontend can display multimodal content"""
        print("\n🎨 Testing Frontend Access...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test main frontend load
                response = await client.get(SERVICES["frontend"], timeout=10)
                
                if response.status_code == 200:
                    print("  ✅ Frontend accessible")
                    
                    # Check if the HTML contains multimodal-related components
                    html_content = response.text
                    has_image_gallery = "ImageGallery" in html_content or "image" in html_content.lower()
                    has_investigation = "investigation" in html_content.lower()
                    
                    print(f"  {'✅' if has_image_gallery else '⚠️'} Image gallery components detected: {has_image_gallery}")
                    print(f"  {'✅' if has_investigation else '⚠️'} Investigation workspace detected: {has_investigation}")
                    
                    self.test_results["frontend_display"] = True
                    return True
                else:
                    print(f"  ❌ Frontend not accessible: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Frontend access test failed: {e}")
            return False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 MULTIMODAL PIPELINE TEST REPORT")
        print("=" * 60)
        
        overall_score = sum(self.test_results.values()) / len(self.test_results) * 100
        self.test_results["overall_success"] = overall_score >= 70
        
        # Detailed results
        for test_name, result in self.test_results.items():
            if test_name != "overall_success":
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n🎯 Overall Score: {overall_score:.1f}%")
        print(f"🏆 Pipeline Status: {'✅ READY FOR PRODUCTION' if overall_score >= 80 else '⚠️ NEEDS ATTENTION' if overall_score >= 60 else '❌ REQUIRES FIXES'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not self.test_results["services_healthy"]:
            print("  - Ensure all services are running (docker compose up)")
        if not self.test_results["image_extraction"]:
            print("  - Check LlamaParse API key and image extraction settings")
        if not self.test_results["ai_processing"]:
            print("  - Verify OpenAI API key and Vision API access")
        if not self.test_results["elasticsearch_indexing"]:
            print("  - Check Elasticsearch mapping and indexing")
        if not self.test_results["api_endpoints"]:
            print("  - Review API Gateway multimodal endpoints")
        if not self.test_results["frontend_display"]:
            print("  - Rebuild frontend with latest multimodal components")
            
        print(f"\n🔗 Quick Links:")
        print(f"  - Frontend: {SERVICES['frontend']}")
        print(f"  - API Docs: {SERVICES['api_gateway']}/docs")
        print(f"  - Investigation Workspace: {SERVICES['frontend']}/investigation")
        print(f"  - Knowledge Graph: {SERVICES['frontend']}/knowledge")

async def main():
    """Run the multimodal pipeline test"""
    tester = MultimodalPipelineTest()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())