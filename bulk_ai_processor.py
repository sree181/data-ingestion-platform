#!/usr/bin/env python3
"""
Bulk AI Processing Script
Processes all documents in Elasticsearch through the AI pipeline for enhanced feature depth.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_ai_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BulkAIProcessor:
    def __init__(self):
        self.elasticsearch_url = "http://localhost:9200"
        self.document_processor_url = "http://localhost:8001"
        self.batch_size = 5  # Process 5 documents at a time to avoid overwhelming OpenAI
        self.delay_between_batches = 2  # 2 seconds between batches
        
        self.stats = {
            "total_documents": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "errors": []
        }
    
    async def get_unprocessed_documents(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Get all documents that haven't been multimodal processed yet"""
        try:
            # Query for documents without multimodal processing
            query = {
                "query": {
                    "bool": {
                        "must_not": [
                            {"exists": {"field": "multimodal"}}
                        ]
                    }
                },
                "size": 1000,  # Get all unprocessed documents
                "_source": ["title", "content", "metadata"]
            }
            
            async with session.post(
                f"{self.elasticsearch_url}/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get("hits", {}).get("hits", [])
                    
                    documents = []
                    for hit in hits:
                        doc = {
                            "id": hit["_id"],
                            "title": hit["_source"].get("title", ""),
                            "content": hit["_source"].get("content", ""),
                            "metadata": hit["_source"].get("metadata", {})
                        }
                        documents.append(doc)
                    
                    logger.info(f"Found {len(documents)} documents without multimodal processing")
                    return documents
                else:
                    logger.error(f"Failed to fetch unprocessed documents: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching unprocessed documents: {e}")
            return []
    
    async def process_document_ai(self, session: aiohttp.ClientSession, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document through the AI pipeline"""
        try:
            # Prepare the document for AI processing
            payload = {
                "text": document["content"],
                "title": document["title"]
            }
            
            logger.info(f"Processing document: {document['id']} - {document['title'][:50]}...")
            
            async with session.post(
                f"{self.document_processor_url}/process-text",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout for AI processing
            ) as response:
                if response.status == 200:
                    ai_data = await response.json()
                    logger.info(f"Successfully processed document {document['id']}")
                    return {
                        "id": document["id"],
                        "ai_data": ai_data,
                        "success": True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to process document {document['id']}: {response.status} - {error_text}")
                    return {
                        "id": document["id"],
                        "error": f"HTTP {response.status}: {error_text}",
                        "success": False
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout processing document {document['id']}")
            return {
                "id": document["id"],
                "error": "Processing timeout",
                "success": False
            }
        except Exception as e:
            logger.error(f"Error processing document {document['id']}: {e}")
            return {
                "id": document["id"],
                "error": str(e),
                "success": False
            }
    
    async def update_elasticsearch_document(self, session: aiohttp.ClientSession, doc_id: str, ai_data: Dict[str, Any]) -> bool:
        """Update Elasticsearch document with AI-enhanced data"""
        try:
            # Prepare the update payload
            update_doc = {
                "doc": {
                    "ai_processed": True,
                    "openai_entities": ai_data.get("entities", []),
                    "relationships": ai_data.get("relationships", []),
                    "key_concepts": ai_data.get("key_concepts", []),
                    "ai_summary": ai_data.get("document_summary", ""),
                    "highlighted_content": ai_data.get("highlighted_content", ""),
                    "document_insights": ai_data.get("document_insights", {}),
                    "ai_processing_date": datetime.utcnow().isoformat()
                }
            }
            
            async with session.post(
                f"{self.elasticsearch_url}/documents/_update/{doc_id}",
                json=update_doc,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Updated Elasticsearch document {doc_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update Elasticsearch document {doc_id}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating Elasticsearch document {doc_id}: {e}")
            return False
    
    async def process_batch(self, session: aiohttp.ClientSession, batch: List[Dict[str, Any]]) -> None:
        """Process a batch of documents"""
        logger.info(f"Processing batch of {len(batch)} documents...")
        
        # Process documents in parallel within the batch
        tasks = [self.process_document_ai(session, doc) for doc in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update Elasticsearch with results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception in batch processing: {result}")
                self.stats["failed"] += 1
                self.stats["errors"].append(str(result))
            elif result["success"]:
                # Update Elasticsearch
                if await self.update_elasticsearch_document(session, result["id"], result["ai_data"]):
                    self.stats["processed"] += 1
                else:
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Failed to update ES for {result['id']}")
            else:
                self.stats["failed"] += 1
                self.stats["errors"].append(f"Failed to process {result['id']}: {result.get('error', 'Unknown error')}")
    
    async def run_bulk_processing(self) -> None:
        """Main function to run bulk AI processing"""
        self.stats["start_time"] = datetime.utcnow()
        logger.info("Starting bulk AI processing...")
        
        async with aiohttp.ClientSession() as session:
            # Get all unprocessed documents
            documents = await self.get_unprocessed_documents(session)
            self.stats["total_documents"] = len(documents)
            
            if not documents:
                logger.info("No documents without multimodal processing found!")
                return
            
            logger.info(f"Processing {len(documents)} documents in batches of {self.batch_size}")
            
            # Process documents in batches
            for i in range(0, len(documents), self.batch_size):
                batch = documents[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"Starting batch {batch_num}/{total_batches}")
                
                await self.process_batch(session, batch)
                
                # Progress report
                elapsed = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
                processed = self.stats["processed"] + self.stats["failed"]
                remaining = self.stats["total_documents"] - processed
                
                if processed > 0:
                    avg_time_per_doc = elapsed / processed
                    eta_seconds = avg_time_per_doc * remaining
                    eta_minutes = eta_seconds / 60
                    
                    logger.info(f"Progress: {processed}/{self.stats['total_documents']} documents "
                              f"({processed/self.stats['total_documents']*100:.1f}%) - "
                              f"ETA: {eta_minutes:.1f} minutes")
                
                # Wait between batches to avoid overwhelming the API
                if i + self.batch_size < len(documents):
                    logger.info(f"Waiting {self.delay_between_batches} seconds before next batch...")
                    await asyncio.sleep(self.delay_between_batches)
        
        # Final report
        self.print_final_report()
    
    def print_final_report(self) -> None:
        """Print final processing report"""
        elapsed = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        logger.info("="*60)
        logger.info("BULK AI PROCESSING COMPLETE!")
        logger.info("="*60)
        logger.info(f"Total documents: {self.stats['total_documents']}")
        logger.info(f"Successfully processed: {self.stats['processed']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Processing time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        
        if self.stats["processed"] > 0:
            logger.info(f"Average time per document: {elapsed/self.stats['processed']:.1f} seconds")
        
        if self.stats["errors"]:
            logger.info(f"\nErrors encountered ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                logger.info(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                logger.info(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        # Save detailed report to file
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": self.stats,
            "processing_time_seconds": elapsed
        }
        
        with open("bulk_ai_processing_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("\nDetailed report saved to 'bulk_ai_processing_report.json'")

async def main():
    """Main entry point"""
    processor = BulkAIProcessor()
    await processor.run_bulk_processing()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")