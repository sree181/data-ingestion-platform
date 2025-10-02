#!/usr/bin/env python3
"""
Ingest 10 COVID documents as a test batch
"""

import os
import requests
from pathlib import Path
import time
import json

def get_pdf_files(directory: str, limit: int = 10):
    """Get first 10 PDF files from the directory"""
    pdf_files = list(Path(directory).glob("*.pdf"))[:limit]
    print(f"Selected {len(pdf_files)} PDF files from {directory}")
    return pdf_files

def upload_document(file_path: Path, api_url: str = "http://localhost:8000/api/v1/upload"):
    """Upload a single document"""
    try:
        with open(file_path, 'rb') as file:
            files = {'files': (file_path.name, file, 'application/pdf')}
            data = {'category': 'COVID Research'}
            
            print(f"Uploading: {file_path.name}")
            start_time = time.time()
            
            response = requests.post(api_url, files=files, data=data, timeout=300)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Success: {file_path.name} ({elapsed:.1f}s)")
                return True
            else:
                print(f"❌ Failed: {file_path.name} - HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading {file_path.name}: {str(e)}")
        return False

def get_document_count():
    """Get current document count"""
    try:
        response = requests.get("http://localhost:9200/documents/_search?size=0")
        if response.status_code == 200:
            return response.json()["hits"]["total"]["value"]
    except:
        pass
    return None

def main():
    print("🔬 COVID Document Ingestion - 10 Documents Test")
    print("=" * 50)
    
    # Check initial count
    initial_count = get_document_count()
    if initial_count is None:
        print("❌ Error: Could not connect to Elasticsearch")
        return
    
    print(f"📊 Current document count: {initial_count}")
    
    # Get PDF files
    pdf_files = get_pdf_files("Searchable", 10)
    
    if not pdf_files:
        print("❌ No PDF files found in Searchable/ directory")
        return
    
    print(f"\n📁 Files to upload:")
    for i, file_path in enumerate(pdf_files, 1):
        print(f"  {i}. {file_path.name}")
    
    print(f"\n🚀 Starting upload of {len(pdf_files)} documents...")
    print("-" * 50)
    
    # Upload documents
    successful = 0
    start_time = time.time()
    
    for i, file_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] ", end="")
        if upload_document(file_path):
            successful += 1
        
        # Small delay between uploads
        if i < len(pdf_files):
            time.sleep(2)
    
    # Final summary
    total_time = time.time() - start_time
    final_count = get_document_count()
    
    print("\n" + "=" * 50)
    print("📋 UPLOAD SUMMARY")
    print("=" * 50)
    print(f"📁 Files processed: {len(pdf_files)}")
    print(f"✅ Successful uploads: {successful}")
    print(f"❌ Failed uploads: {len(pdf_files) - successful}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"📊 Documents before: {initial_count}")
    print(f"📊 Documents after: {final_count}")
    print(f"📈 Documents added: {final_count - initial_count if final_count else 'Unknown'}")
    print("=" * 50)

if __name__ == "__main__":
    main()


