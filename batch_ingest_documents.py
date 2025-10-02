#!/usr/bin/env python3
"""
Batch Document Ingestion Script
Safely ingests all PDF documents from Searchable/ folder without disrupting existing CUAD data
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DocumentIngestor:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.upload_url = f"{api_base_url}/api/v1/upload"
        self.search_url = f"{api_base_url}/api/v1/search"
        self.stats = {
            "total_files": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }
        
    def get_pdf_files(self, directory: str) -> List[Path]:
        """Get all PDF files from the directory"""
        pdf_files = list(Path(directory).glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        return pdf_files
    
    def check_document_exists(self, filename: str) -> bool:
        """Check if document already exists in the system"""
        try:
            # Search for document by filename
            response = requests.post(
                self.search_url,
                json={"query": filename, "size": 1},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("total", 0) > 0
        except Exception as e:
            logger.warning(f"Error checking if document exists: {e}")
        return False
    
    def upload_document(self, file_path: Path) -> dict:
        """Upload a single document"""
        try:
            # Check if document already exists
            if self.check_document_exists(file_path.name):
                logger.info(f"Document already exists, skipping: {file_path.name}")
                self.stats["skipped"] += 1
                return {"status": "skipped", "filename": file_path.name}
            
            # Upload the document
            with open(file_path, 'rb') as file:
                files = {'files': (file_path.name, file, 'application/pdf')}
                data = {'category': 'COVID Research'}
                
                logger.info(f"Uploading: {file_path.name}")
                response = requests.post(
                    self.upload_url,
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout per document
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully uploaded: {file_path.name}")
                    self.stats["successful"] += 1
                    return {"status": "success", "filename": file_path.name, "result": result}
                else:
                    logger.error(f"Failed to upload {file_path.name}: HTTP {response.status_code}")
                    self.stats["failed"] += 1
                    return {"status": "failed", "filename": file_path.name, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error uploading {file_path.name}: {str(e)}")
            self.stats["failed"] += 1
            return {"status": "failed", "filename": file_path.name, "error": str(e)}
        finally:
            self.stats["processed"] += 1
    
    def process_batch(self, files: List[Path], batch_size: int = 5, max_workers: int = 2):
        """Process files in batches with controlled concurrency"""
        self.stats["total_files"] = len(files)
        self.stats["start_time"] = time.time()
        
        logger.info(f"Starting batch processing of {len(files)} files")
        logger.info(f"Batch size: {batch_size}, Max workers: {max_workers}")
        
        results = []
        
        # Process in batches
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}")
            
            # Process batch with limited concurrency
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(self.upload_document, file_path): file_path 
                                for file_path in batch}
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
                    
                    # Progress update
                    progress = (self.stats["processed"] / self.stats["total_files"]) * 100
                    logger.info(f"Progress: {progress:.1f}% ({self.stats['processed']}/{self.stats['total_files']})")
            
            # Small delay between batches to prevent overwhelming the system
            if i + batch_size < len(files):
                logger.info("Waiting 10 seconds before next batch...")
                time.sleep(10)
        
        self.stats["end_time"] = time.time()
        return results
    
    def print_summary(self):
        """Print processing summary"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        logger.info("=" * 60)
        logger.info("BATCH INGESTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files found: {self.stats['total_files']}")
        logger.info(f"Files processed: {self.stats['processed']}")
        logger.info(f"Successfully uploaded: {self.stats['successful']}")
        logger.info(f"Failed uploads: {self.stats['failed']}")
        logger.info(f"Skipped (already exist): {self.stats['skipped']}")
        logger.info(f"Total processing time: {duration/60:.1f} minutes")
        logger.info(f"Average time per file: {duration/self.stats['processed']:.1f} seconds")
        logger.info("=" * 60)

def main():
    """Main function"""
    # Configuration
    SEARCHABLE_DIR = "Searchable"
    BATCH_SIZE = 3  # Small batches to prevent overwhelming
    MAX_WORKERS = 1  # Conservative concurrency
    
    if not os.path.exists(SEARCHABLE_DIR):
        logger.error(f"Directory {SEARCHABLE_DIR} not found!")
        sys.exit(1)
    
    # Initialize ingestor
    ingestor = DocumentIngestor()
    
    # Get all PDF files
    pdf_files = ingestor.get_pdf_files(SEARCHABLE_DIR)
    
    if not pdf_files:
        logger.warning("No PDF files found!")
        sys.exit(1)
    
    # Confirm with user
    print(f"\nFound {len(pdf_files)} PDF files to process.")
    print(f"This will be processed in batches of {BATCH_SIZE} with {MAX_WORKERS} concurrent uploads.")
    print(f"Estimated time: {(len(pdf_files) * 90) / 60:.1f} minutes")
    
    confirm = input("\nDo you want to proceed? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Process all files
    try:
        results = ingestor.process_batch(pdf_files, BATCH_SIZE, MAX_WORKERS)
        ingestor.print_summary()
        
        # Save detailed results
        with open('batch_ingestion_results.json', 'w') as f:
            json.dump({
                'stats': ingestor.stats,
                'results': results
            }, f, indent=2, default=str)
        
        logger.info("Detailed results saved to batch_ingestion_results.json")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        ingestor.print_summary()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        ingestor.print_summary()

if __name__ == "__main__":
    main()


