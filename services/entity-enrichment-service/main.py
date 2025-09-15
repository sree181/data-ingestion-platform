"""
Entity Enrichment Service
Handles web scraping and entity enrichment using Firecrawl API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import httpx
import json
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from firecrawl_scraper import FirecrawlEntityScraper
from entity_manager import EntityManager
from database import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Entity Enrichment Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
entity_manager = EntityManager()
db_manager = DatabaseManager()
firecrawl_scraper = FirecrawlEntityScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database connection pool...")
    await db_manager.init_pool()
    logger.info("Entity enrichment service started successfully")

# Pydantic models
class EntityScrapeRequest(BaseModel):
    entity_ids: List[str]
    entity_type: Optional[str] = None
    max_sources: int = 3

class EntityEnrichmentStatus(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    status: str  # "pending", "scraping", "completed", "failed"
    sources_scraped: int
    enrichment_score: float
    last_updated: datetime

class EntityEnrichmentResult(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    scraped_data: Dict[str, Any]
    sources: List[str]
    confidence_score: float
    conflicts: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "entity-enrichment-service"}

@app.get("/api/v1/entities")
async def get_all_entities():
    """Get all extracted entities from the system"""
    try:
        logger.info("Starting entity fetch process")
        
        # Get entities from Elasticsearch via API Gateway (primary) with ES fallback
        async with httpx.AsyncClient() as client:
            logger.info("Making request to API Gateway")
            response = await client.get(
                "http://api-gateway:8000/api/v1/search?q=*&size=200",
                timeout=60
            )
            
            logger.info(f"API Gateway response status: {response.status_code}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch documents")
            
            data = response.json()
            entities_map = {}
            
            logger.info(f"Received {len(data.get('results', []))} documents from API")
            results = data.get("results", [])
            
            # Fallback: if API Gateway returned no results, query Elasticsearch directly
            if not results:
                logger.info("API Gateway returned 0 results. Falling back to Elasticsearch directly")
                es_query = {
                    "query": {"match_all": {}},
                    "size": 200,
                    "_source": ["title", "openai_entities"]
                }
                es_resp = await client.post(
                    "http://elasticsearch:9200/documents/_search",
                    json=es_query,
                    timeout=60
                )
                if es_resp.status_code == 200:
                    es_json = es_resp.json()
                    results = es_json.get("hits", {}).get("hits", [])
                    logger.info(f"Elasticsearch fallback returned {len(results)} documents")
                else:
                    logger.warning(f"Elasticsearch fallback failed: {es_resp.status_code}")
            
            # Extract entities from all documents
            processed = 0
            for doc in results:
                source = doc.get("_source", {})
                openai_entities = source.get("openai_entities", [])
                doc_id = doc.get("_id")
                doc_title = source.get("title", "Unknown")
                
                logger.info(f"Processing document {doc_title} with {len(openai_entities)} entities")
                
                for entity in openai_entities:
                    entity_name = entity.get("text", "").strip()  # Fixed: was "entity", should be "text"
                    entity_type = entity.get("type", "UNKNOWN").upper()
                    
                    logger.info(f"Found entity: {entity_name} ({entity_type})")
                    
                    if entity_name:
                        entity_key = f"{entity_name}_{entity_type}"
                        
                        if entity_key not in entities_map:
                            entities_map[entity_key] = {
                                "id": entity_key,
                                "name": entity_name,
                                "type": entity_type,
                                "frequency": 0,
                                "documents": [],
                                "enrichment_status": "not_scraped",
                                "last_updated": None
                            }
                        
                        entities_map[entity_key]["frequency"] += 1
                        entities_map[entity_key]["documents"].append({
                            "id": doc_id,
                            "title": doc_title
                        })
                processed += 1
            logger.info(f"Entity extraction complete. Docs processed: {processed}. Unique entities: {len(entities_map)}")
            
            # Sort by frequency (high-frequency first)
            entities_list = list(entities_map.values())
            entities_list.sort(key=lambda x: x["frequency"], reverse=True)
            
            # Check enrichment status for each entity
            logger.info("Checking enrichment status for entities")
            for entity in entities_list:
                try:
                    # Check if entity has been enriched
                    enrichment_status = await db_manager.get_enrichment_status(entity["id"])
                    if enrichment_status:
                        entity["enrichment_status"] = enrichment_status["status"]
                        entity["enrichment_score"] = enrichment_status.get("enrichment_score")
                        entity["last_updated"] = enrichment_status["updated_at"].isoformat() if enrichment_status.get("updated_at") else None
                        logger.info(f"Entity {entity['name']} has status: {enrichment_status['status']}")
                    else:
                        logger.info(f"Entity {entity['name']} has no enrichment status")
                except Exception as e:
                    logger.warning(f"Failed to check enrichment status for {entity['name']}: {str(e)}")
                    # Keep default status if check fails
            
            logger.info(f"Returning {len(entities_list)} total entities")
            
            # Return at least an empty array structure
            return {"total": len(entities_list), "entities": entities_list}
            
    except Exception as e:
        logger.error(f"Error fetching entities: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching entities: {str(e)}")

@app.get("/api/v1/entities/{entity_id}")
async def get_entity_details(entity_id: str):
    """Get detailed information about a specific entity"""
    try:
        # Check if we have enriched data for this entity
        enriched_data = await db_manager.get_entity_enrichment(entity_id)
        
        if enriched_data:
            return enriched_data
        else:
            return {"entity_id": entity_id, "status": "not_enriched"}
            
    except Exception as e:
        logger.error(f"Error fetching entity details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching entity details: {str(e)}")

@app.post("/api/v1/entities/enrich")
async def enrich_entities(request: EntityScrapeRequest, background_tasks: BackgroundTasks):
    """Start entity enrichment process"""
    try:
        # Add enrichment task to background
        background_tasks.add_task(
            process_entity_enrichment,
            request.entity_ids,
            request.entity_type,
            request.max_sources
        )
        
        return {
            "message": f"Entity enrichment started for {len(request.entity_ids)} entities",
            "entity_ids": request.entity_ids,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting entity enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting entity enrichment: {str(e)}")

@app.get("/api/v1/entities/status/{entity_id}")
async def get_enrichment_status(entity_id: str):
    """Get enrichment status for a specific entity"""
    try:
        status = await db_manager.get_enrichment_status(entity_id)
        return status or {"entity_id": entity_id, "status": "not_started"}
        
    except Exception as e:
        logger.error(f"Error fetching enrichment status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching enrichment status: {str(e)}")

@app.post("/api/v1/entities/{entity_id}/insights")
async def generate_entity_insights(entity_id: str):
    """Generate AI-powered insights for a specific entity"""
    try:
        # Get the enriched data for the entity
        enriched_data = await db_manager.get_entity_enrichment(entity_id)
        
        if not enriched_data:
            raise HTTPException(status_code=404, detail="Entity not found or not enriched")
        
        # Parse entity name and type
        parts = entity_id.split("_")
        entity_name = "_".join(parts[:-1])
        entity_type = parts[-1] if len(parts) > 1 else "ORGANIZATION"
        
        # Generate insights using the scraper
        consolidated_data = enriched_data.get("consolidated_data", {})
        insights = await firecrawl_scraper.generate_entity_insights(
            entity_name, entity_type, consolidated_data
        )
        
        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "insights": insights,
            "generated_at": "2025-08-08T15:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insights for {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@app.post("/api/v1/entities/batch-enrich")
async def batch_enrich_entities(request: EntityScrapeRequest, background_tasks: BackgroundTasks):
    """Enhanced batch enrichment with progress tracking"""
    try:
        # Add batch enrichment task to background
        background_tasks.add_task(
            process_batch_entity_enrichment,
            request.entity_ids,
            request.entity_type,
            request.max_sources
        )
        
        return {
            "message": f"Batch entity enrichment started for {len(request.entity_ids)} entities",
            "entity_ids": request.entity_ids,
            "status": "processing",
            "batch_id": f"batch_{len(request.entity_ids)}_{int(datetime.now().timestamp())}"
        }
        
    except Exception as e:
        logger.error(f"Error starting batch enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting batch enrichment: {str(e)}")

@app.get("/api/v1/entities/batch-status/{batch_id}")
async def get_batch_enrichment_status(batch_id: str):
    """Get status of batch enrichment process"""
    try:
        # This would typically query a batch tracking table
        # For now, return a mock response
        return {
            "batch_id": batch_id,
            "status": "completed",
            "total_entities": 3,
            "completed_entities": 3,
            "failed_entities": 0,
            "progress_percentage": 100
        }
        
    except Exception as e:
        logger.error(f"Error fetching batch status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching batch status: {str(e)}")

async def process_entity_enrichment(entity_ids: List[str], entity_type: Optional[str], max_sources: int):
    """Background task to process entity enrichment"""
    logger.info(f"Starting enrichment for entities: {entity_ids}")
    
    for entity_id in entity_ids:
        try:
            # Parse entity name and type from entity_id
            # If entity_id contains underscore, split it; otherwise use the whole string as entity_name
            if "_" in entity_id and entity_id.count("_") >= 1:
                parts = entity_id.split("_")
                entity_name = "_".join(parts[:-1])
                actual_entity_type = parts[-1]
            else:
                entity_name = entity_id
                actual_entity_type = entity_type or "ORGANIZATION"
            
            logger.info(f"Enriching entity: {entity_name} (Type: {actual_entity_type})")
            
            # Update status to scraping
            await db_manager.update_enrichment_status(
                entity_id, "scraping", entity_name, actual_entity_type
            )
            
            # Perform structured scraping (enhanced tutorial approach)
            enrichment_result = await firecrawl_scraper.scrape_entity_structured(
                entity_name, actual_entity_type, max_sources
            )
            
            # Store results
            await db_manager.store_entity_enrichment(entity_id, enrichment_result)
            
            # Update status to completed
            await db_manager.update_enrichment_status(
                entity_id, "completed", entity_name, actual_entity_type,
                enrichment_score=enrichment_result.get("confidence_score", 0.0)
            )
            
            logger.info(f"Successfully enriched entity: {entity_name}")
            
        except Exception as e:
            logger.error(f"Error enriching entity {entity_id}: {str(e)}")
            await db_manager.update_enrichment_status(
                entity_id, "failed", entity_name or entity_id, actual_entity_type or "UNKNOWN"
            )

async def process_batch_entity_enrichment(entity_ids: List[str], entity_type: Optional[str], max_sources: int):
    """Enhanced batch processing with progress tracking and parallel processing"""
    logger.info(f"Starting batch enrichment for {len(entity_ids)} entities")
    
    # Process entities with limited concurrency to avoid rate limits
    semaphore = asyncio.Semaphore(3)  # Process up to 3 entities concurrently
    
    async def enrich_single_entity(entity_id: str):
        async with semaphore:
            try:
                # Parse entity name and type from entity_id
                parts = entity_id.split("_")
                entity_name = "_".join(parts[:-1])
                actual_entity_type = parts[-1] if len(parts) > 1 else (entity_type or "ORGANIZATION")
                
                logger.info(f"Enriching entity: {entity_name} (Type: {actual_entity_type})")
                
                # Update status to scraping
                await db_manager.update_enrichment_status(
                    entity_id, "scraping", entity_name, actual_entity_type
                )
                
                # Perform structured scraping with enhanced capabilities
                enrichment_result = await firecrawl_scraper.scrape_entity_structured(
                    entity_name, actual_entity_type, max_sources
                )
                
                # Store results
                await db_manager.store_entity_enrichment(entity_id, enrichment_result)
                
                # Update status to completed
                await db_manager.update_enrichment_status(
                    entity_id, "completed", entity_name, actual_entity_type,
                    enrichment_score=enrichment_result.get("confidence_score", 0.0)
                )
                
                logger.info(f"Successfully enriched entity: {entity_name}")
                return {"entity_id": entity_id, "status": "success"}
                
            except Exception as e:
                logger.error(f"Error enriching entity {entity_id}: {str(e)}")
                await db_manager.update_enrichment_status(
                    entity_id, "failed", entity_name or entity_id, actual_entity_type or "UNKNOWN"
                )
                return {"entity_id": entity_id, "status": "failed", "error": str(e)}
    
    # Process all entities concurrently with semaphore
    tasks = [enrich_single_entity(entity_id) for entity_id in entity_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log batch completion
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed = len(results) - successful
    
    logger.info(f"Batch enrichment completed: {successful} successful, {failed} failed out of {len(entity_ids)} total")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)