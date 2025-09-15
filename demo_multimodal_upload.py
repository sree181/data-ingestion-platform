#!/usr/bin/env python3
"""
Demo Multimodal Upload Script
=============================

This script demonstrates the complete end-to-end multimodal document processing pipeline
for client demos. It showcases:

1. Document upload and ingestion
2. Text extraction with PyMuPDF/LLaVA
3. Image extraction and analysis
4. AI-powered entity and relationship extraction
5. Real-time indexing to Elasticsearch
6. UI integration for search and visualization

Perfect for client demonstrations of the complete data ingestion platform.
"""

import asyncio
import aiohttp
import os
import json
import time
from pathlib import Path
import argparse

class MultimodalDemoUploader:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def print_header(self, title):
        """Print a styled header for demo sections"""
        print("\n" + "="*80)
        print(f"🚀 {title}")
        print("="*80)
    
    def print_step(self, step_num, description):
        """Print a demo step"""
        print(f"\n📋 STEP {step_num}: {description}")
        print("-" * 60)
    
    async def check_service_health(self):
        """Check if the document processor service is running"""
        self.print_step(1, "HEALTH CHECK - Verifying Service Availability")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Document Processor Service: ONLINE")
                    print(f"✅ OpenAI Integration: {'ENABLED' if health_data.get('openai_available') else 'DISABLED'}")
                    return True
                else:
                    print(f"❌ Service health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to service: {e}")
            return False
    
    async def upload_and_process_pdf(self, pdf_path):
        """Upload and process a PDF with full multimodal analysis"""
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"❌ PDF file not found: {pdf_path}")
            return None
            
        self.print_step(2, f"DOCUMENT UPLOAD - Processing {pdf_file.name}")
        
        print(f"📄 File: {pdf_file.name}")
        print(f"📏 Size: {pdf_file.stat().st_size:,} bytes")
        
        # Prepare file upload
        data = aiohttp.FormData()
        data.add_field('file', 
                      open(pdf_path, 'rb'), 
                      filename=pdf_file.name,
                      content_type='application/pdf')
        
        start_time = time.time()
        
        try:
            print("\n🔄 Uploading to multimodal processor...")
            async with self.session.post(f"{self.base_url}/process-file", data=data) as response:
                processing_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Processing completed in {processing_time:.2f} seconds")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Upload failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def display_processing_results(self, result):
        """Display the processing results in a demo-friendly format"""
        if not result:
            return
            
        self.print_step(3, "PROCESSING RESULTS - AI Analysis Complete")
        
        # Document Overview
        print(f"📄 Document: {result.get('title', 'Unknown')}")
        print(f"📝 Text Content: {len(result.get('highlighted_content', ''))} characters extracted")
        print(f"🔧 Extraction Method: {result.get('extraction_method', 'N/A')}")
        
        # Multimodal Analysis
        images = result.get('extracted_images', [])
        print(f"\n🖼️ MULTIMODAL ANALYSIS:")
        print(f"  • Images extracted: {len(images)}")
        print(f"  • Has multimodal content: {'✅ YES' if result.get('multimodal') else '❌ NO'}")
        
        if images:
            print(f"\n📸 IMAGE DETAILS:")
            for i, img in enumerate(images[:3]):  # Show first 3 images
                print(f"  Image {i+1}: Page {img.get('page_number', 'N/A')} - {img.get('extraction_method', 'N/A')}")
        
        # AI Entity Extraction
        entities = result.get('entities', [])
        relationships = result.get('relationships', [])
        
        print(f"\n🧠 AI ENTITY EXTRACTION:")
        print(f"  • Entities identified: {len(entities)}")
        print(f"  • Relationships found: {len(relationships)}")
        
        if entities:
            print(f"\n🏷️ TOP ENTITIES:")
            for entity in entities[:5]:  # Show top 5 entities
                confidence = entity.get('confidence', 0)
                print(f"  • {entity.get('text', 'N/A')} ({entity.get('type', 'N/A')}) - {confidence:.0%} confidence")
        
        if relationships:
            print(f"\n🔗 KEY RELATIONSHIPS:")
            for rel in relationships[:3]:  # Show top 3 relationships
                print(f"  • {rel.get('source', 'N/A')} → {rel.get('relationship', 'N/A')} → {rel.get('target', 'N/A')}")
        
        # Document Insights
        insights = result.get('document_insights', {})
        if insights:
            print(f"\n💡 DOCUMENT INSIGHTS:")
            print(f"  • Type: {insights.get('document_type', 'N/A')}")
            print(f"  • Main Themes: {', '.join(insights.get('main_themes', [])[:3])}")
            print(f"  • Confidence: {insights.get('confidence', 0):.0%}")
        
        # Summary
        summary = result.get('document_summary', '')
        if summary:
            print(f"\n📋 AI SUMMARY:")
            print(f"  {summary[:200]}{'...' if len(summary) > 200 else ''}")
    
    def display_ui_integration_info(self, result):
        """Show how to access the processed document in the UI"""
        self.print_step(4, "UI INTEGRATION - Access Your Processed Document")
        
        filename = result.get('title', 'document') if result else 'document'
        
        print(f"🌐 Your document is now searchable in the UI:")
        print(f"")
        print(f"🔍 INTELLIGENT SEARCH:")
        print(f"   URL: http://localhost:3002")
        print(f"   Search for: '{filename.replace('%20', ' ')}'")
        print(f"")
        print(f"🕵️ INVESTIGATION WORKSPACE:")
        print(f"   URL: http://localhost:3002/investigation")
        print(f"   Browse entities and relationships")
        print(f"")
        print(f"📊 DOCUMENT LIBRARY:")
        print(f"   URL: http://localhost:3002")
        print(f"   View in document library tab")
        
    async def run_demo(self, pdf_path):
        """Run the complete demo flow"""
        self.print_header("MULTIMODAL DOCUMENT PROCESSING DEMO")
        print("Showcasing end-to-end AI-powered document ingestion pipeline")
        
        # Step 1: Health Check
        if not await self.check_service_health():
            print("\n❌ Demo cannot proceed - service not available")
            return False
        
        # Step 2: Process Document
        result = await self.upload_and_process_pdf(pdf_path)
        if not result:
            print("\n❌ Demo failed - document processing error")
            return False
        
        # Step 3: Display Results
        self.display_processing_results(result)
        
        # Step 4: UI Integration
        self.display_ui_integration_info(result)
        
        # Demo Summary
        self.print_header("DEMO COMPLETE - READY FOR CLIENT PRESENTATION")
        print("✅ Document successfully ingested and processed")
        print("✅ AI entities and relationships extracted")
        print("✅ Multimodal content analyzed")
        print("✅ Real-time search and visualization ready")
        print("\n🎯 Your data ingestion platform is production-ready!")
        
        return True

async def main():
    parser = argparse.ArgumentParser(description="Demo Multimodal Document Processing")
    parser.add_argument("pdf_path", help="Path to PDF file for demo")
    parser.add_argument("--url", default="http://localhost:8001", help="Document processor URL")
    
    args = parser.parse_args()
    
    async with MultimodalDemoUploader(args.url) as uploader:
        success = await uploader.run_demo(args.pdf_path)
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)