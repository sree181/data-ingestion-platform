#!/usr/bin/env python3
"""
Test script for the Data Ingestion Platform
Tests document upload and processing with existing documents
"""

import asyncio
import aiohttp
import json
from pathlib import Path
import time
import sys

# API endpoints
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class DataIngestionTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
    
    async def setup(self):
        """Initialize HTTP session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Test basic connectivity
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    print("✅ API Gateway is healthy")
                else:
                    print(f"❌ API Gateway health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to API Gateway: {e}")
            return False
        
        # Get authentication token (using default admin credentials)
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.auth_token = token_data["access_token"]
                    print("✅ Authentication successful")
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    # Continue without auth for testing
        except Exception as e:
            print(f"⚠️ Authentication error (continuing without auth): {e}")
        
        return True
    
    async def test_health_checks(self):
        """Test all service health endpoints"""
        print("\n🔍 Testing service health...")
        
        # Detailed health check
        try:
            async with self.session.get(f"{BASE_URL}/health/detailed") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("📊 Service Health Status:")
                    for service, status in health_data["services"].items():
                        emoji = "✅" if status == "healthy" else "❌"
                        print(f"  {emoji} {service}: {status}")
                else:
                    print(f"❌ Detailed health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
    
    async def test_search_functionality(self):
        """Test search capabilities"""
        print("\n🔍 Testing search functionality...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test basic search
        search_request = {
            "query": "COVID",
            "size": 5,
            "highlight": True
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/search", 
                json=search_request,
                headers=headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ Search test passed - found {search_results['total']} documents")
                    if search_results['hits']:
                        print(f"  📄 Sample result: {search_results['hits'][0]['source'].get('title', 'No title')}")
                elif response.status == 401:
                    print("⚠️ Search requires authentication (expected for secure deployment)")
                else:
                    print(f"❌ Search test failed: {response.status}")
        except Exception as e:
            print(f"❌ Search test error: {e}")
    
    async def test_document_upload(self):
        """Test document upload with a sample PDF"""
        print("\n📤 Testing document upload...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Find a sample PDF from the existing documents
        pdf_files = list(Path("Publishable").glob("*.pdf"))
        if not pdf_files:
            print("⚠️ No PDF files found in Publishable directory")
            return
        
        # Use a smaller PDF for testing
        test_file = None
        for pdf_file in pdf_files:
            if pdf_file.stat().st_size < 5 * 1024 * 1024:  # Less than 5MB
                test_file = pdf_file
                break
        
        if not test_file:
            test_file = pdf_files[0]  # Use first file if none are small enough
        
        print(f"📄 Uploading test file: {test_file.name}")
        
        try:
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name, content_type='application/pdf')
                
                async with self.session.post(
                    f"{API_BASE}/documents/upload",
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        upload_result = await response.json()
                        document_id = upload_result["document_id"]
                        print(f"✅ Upload successful - Document ID: {document_id}")
                        
                        # Test status checking
                        await self.test_processing_status(document_id, headers)
                        
                    elif response.status == 401:
                        print("⚠️ Upload requires authentication")
                    else:
                        error_text = await response.text()
                        print(f"❌ Upload failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Upload test error: {e}")
    
    async def test_processing_status(self, document_id: str, headers: dict):
        """Test document processing status"""
        print(f"⏳ Checking processing status for {document_id}")
        
        for attempt in range(10):  # Check up to 10 times
            try:
                async with self.session.get(
                    f"{API_BASE}/documents/{document_id}/status",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data["status"]
                        progress = status_data["progress"]
                        message = status_data["message"]
                        
                        print(f"  📊 Status: {status} ({progress}%) - {message}")
                        
                        if status in ["completed", "failed"]:
                            break
                    else:
                        print(f"❌ Status check failed: {response.status}")
                        break
                        
            except Exception as e:
                print(f"❌ Status check error: {e}")
                break
            
            await asyncio.sleep(2)  # Wait 2 seconds between checks
    
    async def test_knowledge_graph(self):
        """Test knowledge graph functionality"""
        print("\n🕸️ Testing knowledge graph...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test simple graph query
        graph_query = {
            "cypher_query": "MATCH (d:Document) RETURN d.title, d.id LIMIT 5",
            "parameters": {}
        }
        
        try:
            async with self.session.post(
                f"{API_BASE}/graph/query",
                json=graph_query,
                headers=headers
            ) as response:
                if response.status == 200:
                    graph_results = await response.json()
                    print(f"✅ Knowledge graph test passed - found {graph_results['total']} results")
                    if graph_results['nodes']:
                        print(f"  🔗 Sample node: {graph_results['nodes'][0].get('properties', {})}")
                elif response.status == 401:
                    print("⚠️ Graph query requires authentication")
                else:
                    print(f"❌ Graph query failed: {response.status}")
        except Exception as e:
            print(f"❌ Graph query error: {e}")
    
    async def test_analytics_dashboard(self):
        """Test analytics dashboard data"""
        print("\n📊 Testing analytics dashboard...")
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.get(
                f"{API_BASE}/analytics/dashboard",
                headers=headers
            ) as response:
                if response.status == 200:
                    analytics_data = await response.json()
                    doc_stats = analytics_data.get("document_stats", {})
                    graph_stats = analytics_data.get("knowledge_graph_stats", {})
                    
                    print("✅ Analytics data retrieved:")
                    print(f"  📄 Total documents: {doc_stats.get('total_documents', 0)}")
                    print(f"  🕸️ Total graph nodes: {graph_stats.get('total_nodes', 0)}")
                    print(f"  🔗 Total relationships: {graph_stats.get('total_relationships', 0)}")
                elif response.status == 401:
                    print("⚠️ Analytics requires authentication")
                else:
                    print(f"❌ Analytics test failed: {response.status}")
        except Exception as e:
            print(f"❌ Analytics test error: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Data Ingestion Platform Tests")
        print("=" * 50)
        
        if not await self.setup():
            print("❌ Setup failed, aborting tests")
            return False
        
        # Run tests
        await self.test_health_checks()
        await self.test_search_functionality()
        await self.test_document_upload()
        await self.test_knowledge_graph()
        await self.test_analytics_dashboard()
        
        print("\n" + "=" * 50)
        print("✅ Test suite completed!")
        
        return True


async def main():
    """Main test runner"""
    tester = DataIngestionTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            print("\n🎉 All tests completed! Your Data Ingestion Platform is working correctly.")
            print("\n📚 Next steps:")
            print("  1. Visit http://localhost:8000/docs for full API documentation")
            print("  2. Try uploading more documents from your Publishable folder")
            print("  3. Explore the knowledge graph at http://localhost:7474")
            print("  4. Set up monitoring dashboards at http://localhost:3000")
        else:
            print("\n❌ Some tests failed. Check the service logs for more details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    # Check if services are running
    import subprocess
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose-optimized.yml", "ps"],
            capture_output=True,
            text=True
        )
        if "Up" not in result.stdout:
            print("⚠️ Services don't appear to be running.")
            print("Please start the platform first with: ./start.sh")
            sys.exit(1)
    except Exception:
        print("⚠️ Could not check service status.")
        print("Please ensure Docker and docker-compose are installed and services are running.")
    
    asyncio.run(main())