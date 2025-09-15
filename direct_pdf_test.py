#!/usr/bin/env python3
"""
Direct PDF test to process your s41598-020-76550-z.pdf
This will extract text from the PDF and show you what the system would process
"""

import asyncio
import json
from pathlib import Path
import sys

# Simple PDF text extraction
def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        pdf_doc = fitz.open(pdf_path)
        text_content = ""
        
        print(f"📄 Processing PDF: {Path(pdf_path).name}")
        print(f"📏 Pages: {pdf_doc.page_count}")
        
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            page_text = page.get_text()
            text_content += page_text
            text_content += f"\n\n---PAGE {page_num + 1} END---\n\n"
        
        pdf_doc.close()
        return text_content
        
    except ImportError:
        print("❌ PyMuPDF not available. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "PyMuPDF"], check=True)
        return extract_pdf_text(pdf_path)
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None

async def simulate_ai_processing(text_content, title):
    """Simulate what OpenAI would extract from this text"""
    
    # Basic entity detection (simple keyword-based simulation)
    entities = []
    
    # Look for common patterns
    import re
    
    # Find potential scientific terms
    scientific_terms = re.findall(r'\b[A-Z][a-z]+\s+[a-z]+\b', text_content)
    for term in set(scientific_terms[:20]):  # Limit to 20
        if len(term) > 6 and term not in ['Figure', 'Table', 'Method']:
            entities.append({
                "text": term,
                "type": "SCIENTIFIC_TERM",
                "confidence": 0.8
            })
    
    # Find numbers that might be measurements
    measurements = re.findall(r'\d+\.?\d*\s*(?:mg|ml|cm|mm|kg|g|%)', text_content)
    for measure in set(measurements[:10]):
        entities.append({
            "text": measure,
            "type": "MEASUREMENT", 
            "confidence": 0.9
        })
    
    # Find years
    years = re.findall(r'\b(19|20)\d{2}\b', text_content)
    for year in set(years[:5]):
        entities.append({
            "text": year,
            "type": "DATE",
            "confidence": 0.9
        })
    
    # Create a summary (first few sentences)
    sentences = text_content.split('. ')[:3]
    summary = '. '.join(sentences) + '.' if sentences else "Summary not available"
    
    return {
        "title": title,
        "entities": entities,
        "summary": summary,
        "text_length": len(text_content),
        "processed": True
    }

async def main():
    """Process the uploaded PDF"""
    
    pdf_path = "~/Downloads/s41598-020-76550-z.pdf"
    pdf_path = Path(pdf_path).expanduser()
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("💡 Make sure the PDF is in your Downloads folder")
        return
    
    print("🚀 DIRECT PDF PROCESSING TEST")
    print("=" * 50)
    
    # Extract text
    text_content = extract_pdf_text(str(pdf_path))
    if not text_content:
        return
    
    print(f"✅ Text extracted: {len(text_content):,} characters")
    
    # Simulate AI processing 
    result = await simulate_ai_processing(text_content, pdf_path.stem)
    
    print("\n📊 PROCESSING RESULTS")
    print("=" * 30)
    print(f"Title: {result['title']}")
    print(f"Text Length: {result['text_length']:,} characters")
    print(f"Entities Found: {len(result['entities'])}")
    print(f"Summary: {result['summary'][:200]}...")
    
    print(f"\n🏷️ SAMPLE ENTITIES:")
    for i, entity in enumerate(result['entities'][:10]):
        print(f"  {i+1}. {entity['text']} ({entity['type']}) - {entity['confidence']:.1%}")
    
    # Show sample text
    print(f"\n📝 SAMPLE TEXT (first 500 chars):")
    print("-" * 30)
    print(text_content[:500] + "...")
    
    print(f"\n✅ PDF PROCESSING COMPLETE!")
    print(f"🎯 This demonstrates what your system would extract from the PDF")
    print(f"🔄 In the full system, this would be:")
    print(f"   1. Indexed in Elasticsearch")
    print(f"   2. Entities stored in Neo4j") 
    print(f"   3. Searchable in the Investigation workspace")
    print(f"   4. Images would be extracted and analyzed with OpenAI Vision")

if __name__ == "__main__":
    asyncio.run(main())