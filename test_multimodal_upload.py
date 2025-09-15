#!/usr/bin/env python3
"""
Test script for uploading and processing a PDF with multimodal capabilities
This will demonstrate image extraction and AI analysis of your uploaded PDF
"""

import asyncio
import aiohttp
import json
import base64
from pathlib import Path
import sys

class MultimodalUploadTest:
    def __init__(self):
        self.document_processor_url = "http://localhost:8001"
        self.api_gateway_url = "http://localhost:8000"
        
    async def test_pdf_upload(self, pdf_path: str):
        """Test uploading and processing a PDF with multimodal capabilities"""
        
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"❌ Error: File not found: {pdf_path}")
            return False
            
        print(f"📄 Processing PDF: {pdf_file.name}")
        print(f"📏 File size: {pdf_file.stat().st_size:,} bytes")
        
        try:            
            async with aiohttp.ClientSession() as session:
                print("🔄 Uploading to multimodal processor...")
                
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', 
                             open(pdf_file, 'rb'), 
                             filename=pdf_file.name, 
                             content_type='application/pdf')
                
                # Test with the /process-file endpoint
                async with session.post(
                    f"{self.document_processor_url}/process-file",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ PDF processed successfully!")
                        
                        # Display results
                        await self.display_results(result)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Processing failed: {response.status}")
                        print(f"Error: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            return False
    
    async def display_results(self, result):
        """Display the processing results"""
        
        print("\n" + "="*60)
        print("📊 MULTIMODAL PROCESSING RESULTS")
        print("="*60)
        
        # Basic info
        print(f"📄 Title: {result.get('title', 'N/A')}")
        print(f"📝 Content length: {len(result.get('content', ''))} characters")
        
        # AI entities
        entities = result.get('openai_entities', [])
        print(f"🧠 AI Entities found: {len(entities)}")
        for entity in entities[:5]:  # Show first 5
            print(f"  • {entity.get('text', 'N/A')} ({entity.get('type', 'Unknown')})")
        
        # Image processing
        images = result.get('images', [])
        image_metadata = result.get('image_metadata', [])
        image_entities = result.get('image_entities', [])
        
        print(f"\n🖼️ MULTIMODAL FEATURES:")
        print(f"  • Images extracted: {len(images)}")
        print(f"  • Image metadata: {len(image_metadata)}")
        print(f"  • Image entities: {len(image_entities)}")
        
        if image_metadata:
            print(f"\n📷 IMAGE ANALYSIS:")
            for i, img_meta in enumerate(image_metadata[:3]):  # Show first 3
                print(f"  Image {i+1}:")
                print(f"    • Type: {img_meta.get('image_type', 'Unknown')}")
                print(f"    • Analysis: {img_meta.get('analysis', 'N/A')[:100]}...")
                print(f"    • Key elements: {len(img_meta.get('key_elements', []))}")
        
        if image_entities:
            print(f"\n🏷️ ENTITIES IN IMAGES:")
            for entity in image_entities[:5]:  # Show first 5
                print(f"  • {entity.get('text', 'N/A')} ({entity.get('type', 'Unknown')})")
        
        # Document insights
        insights = result.get('document_insights', {})
        if insights:
            print(f"\n💡 DOCUMENT INSIGHTS:")
            print(f"  • Type: {insights.get('document_type', 'N/A')}")
            print(f"  • Main themes: {', '.join(insights.get('main_themes', [])[:3])}")
            print(f"  • Confidence: {insights.get('confidence_score', 0):.2f}")
        
        # Summary
        summary = result.get('document_summary', '')
        if summary:
            print(f"\n📋 AI SUMMARY:")
            print(f"  {summary[:200]}...")
        
        print(f"\n🎯 STATUS: {'✅ SUCCESS' if result.get('success', False) else '❌ FAILED'}")
        
        # Instructions for viewing in UI
        print(f"\n🌐 VIEW IN UI:")
        print(f"  • Investigation: http://localhost:3002/investigation")
        print(f"  • Search for: {result.get('title', 'N/A')}")

async def main():
    """Main function"""
    
    if len(sys.argv) != 2:
        print("Usage: python test_multimodal_upload.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_multimodal_upload.py ./s41598-020-76550-z.pdf")
        print("  python test_multimodal_upload.py ~/Downloads/s41598-020-76550-z.pdf")
        return
    
    pdf_path = sys.argv[1]
    tester = MultimodalUploadTest()
    
    print("🚀 Starting Multimodal PDF Upload Test")
    print("="*50)
    
    success = await tester.test_pdf_upload(pdf_path)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("   Check the Investigation workspace to see your processed document with images!")
    else:
        print("\n❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())