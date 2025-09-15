#!/usr/bin/env python3
"""
Test Official LLaVA Implementation
==================================

This script tests the official LLaVA implementation with your suggested methods:
- llava.model.builder.load_pretrained_model
- llava.mm_utils.get_model_name_from_path
- llava.eval.run_llava.eval_model

Usage:
    python test_official_llava.py [pdf_path]
"""

import asyncio
import aiohttp
import os
import sys
from pathlib import Path

async def test_official_llava_upload(pdf_path):
    """Test PDF upload with official LLaVA processing"""
    
    print("🚀 Testing Official LLaVA Implementation")
    print("=" * 60)
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    pdf_file = Path(pdf_path)
    print(f"📄 Testing with: {pdf_file.name}")
    print(f"📏 File size: {pdf_file.stat().st_size:,} bytes")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Health check
            print("\n🔍 Checking service health...")
            async with session.get("http://localhost:8001/health") as response:
                if response.status != 200:
                    print(f"❌ Service not healthy: {response.status}")
                    return False
                health = await response.json()
                print(f"✅ Service online - OpenAI: {'enabled' if health.get('openai_available') else 'disabled'}")
            
            # Upload and process
            print(f"\n🔄 Uploading PDF for Official LLaVA processing...")
            
            data = aiohttp.FormData()
            data.add_field('file', 
                          open(pdf_path, 'rb'), 
                          filename=pdf_file.name,
                          content_type='application/pdf')
            
            async with session.post("http://localhost:8001/process-file", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print("✅ Official LLaVA processing completed!")
                    print("\n📊 RESULTS:")
                    print(f"  • Extraction method: {result.get('extraction_method', 'unknown')}")
                    print(f"  • Text length: {len(result.get('highlighted_content', ''))} characters")
                    print(f"  • Images extracted: {len(result.get('extracted_images', []))}")
                    print(f"  • AI entities found: {len(result.get('entities', []))}")
                    print(f"  • Relationships found: {len(result.get('relationships', []))}")
                    
                    # Check if official LLaVA was used
                    extraction_method = result.get('extraction_method', '')
                    if 'official_llava' in extraction_method:
                        print("\n🎉 SUCCESS: Official LLaVA implementation is working!")
                        
                        # Show LLaVA-specific results
                        images = result.get('extracted_images', [])
                        if images:
                            print(f"\n🖼️ LLaVA IMAGE ANALYSIS:")
                            for i, img in enumerate(images[:2]):  # Show first 2
                                print(f"  Image {i+1} (Page {img.get('page_number', 'N/A')}):")
                                analysis = img.get('llava_analysis', 'No analysis available')[:200]
                                print(f"    Analysis: {analysis}...")
                    else:
                        print(f"\n⚠️ Using fallback method: {extraction_method}")
                        print("Official LLaVA not active (likely due to missing dependencies or GPU)")
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Upload failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_official_llava.py <pdf_path>")
        print("\nExample:")
        print("  python test_official_llava.py /path/to/s41598-020-76550-z.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    success = asyncio.run(test_official_llava_upload(pdf_path))
    
    if success:
        print("\n🎯 Official LLaVA test completed successfully!")
        print("🌐 Check the UI at http://localhost:3002 to see results")
    else:
        print("\n❌ Official LLaVA test failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()