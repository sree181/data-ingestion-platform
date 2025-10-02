from fastapi import APIRouter, HTTPException, Depends, Query, Form, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import uuid
import structlog
import os

from models.project_spaces import ProjectSpace
from services.project_spaces_service import ProjectSpacesService
from routes.project_spaces import get_spaces_service, get_current_user
from websocket_service import websocket_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/spaces", tags=["Document Ingestion"])


# Pydantic Models
class LocalFile(BaseModel):
    """Local file information"""
    filename: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    modified_date: datetime = Field(..., description="Last modified date")
    file_type: str = Field(..., description="File type/extension")


class LocalFilesResponse(BaseModel):
    """Response for local files listing"""
    files: List[LocalFile] = Field(..., description="List of available files")
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size of all files in bytes")


class BatchIngestionRequest(BaseModel):
    """Request for batch ingestion"""
    file_paths: List[str] = Field(..., description="List of file paths to ingest")
    file_type: Optional[str] = Field(None, description="File type filter")
    processing_options: Dict = Field(default={}, description="Processing options")


class IngestionStatus(BaseModel):
    """Ingestion job status"""
    job_id: str = Field(..., description="Job ID")
    space_id: str = Field(..., description="Project space ID")
    status: str = Field(..., description="Job status (pending, running, completed, failed)")
    total_files: int = Field(..., description="Total files to process")
    processed_files: int = Field(..., description="Files processed so far")
    successful_files: int = Field(..., description="Successfully processed files")
    failed_files: int = Field(..., description="Failed files")
    created_at: datetime = Field(..., description="Job creation time")
    updated_at: datetime = Field(..., description="Last update time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class IngestionStatusResponse(BaseModel):
    """Response for ingestion status"""
    jobs: List[IngestionStatus] = Field(..., description="List of ingestion jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    total_documents: int = Field(default=0, description="Total documents ingested")
    recent_documents: int = Field(default=0, description="Documents ingested in last 24 hours")
    success_rate: float = Field(default=0.0, description="Success rate percentage")


# In-memory storage for ingestion jobs (in production, use Redis or database)
ingestion_jobs: Dict[str, IngestionStatus] = {}


@router.get("/{space_id}/ingestion/local-files", response_model=LocalFilesResponse)
async def list_local_files(
    space_id: str,
    file_type: Optional[str] = Query(None, description="Filter by file type (pdf, docx, txt)")
):
    """List available local files in the Searchable folder"""
    try:
        # Simplified implementation - just return mock data for now
        # TODO: Implement proper permission checking and real file scanning later
        logger.info("Listing local files for space", space_id=space_id)
        
        # Get the searchable folder path
        from pathlib import Path
        searchable_path = Path("/app/Searchable")  # Adjust path as needed
        if not searchable_path.exists():
            # Try alternative paths
            for alt_path in ["/workspace/Searchable", "./Searchable", "../Searchable"]:
                alt_searchable_path = Path(alt_path)
                if alt_searchable_path.exists():
                    searchable_path = alt_searchable_path
                    break
        
        if not searchable_path.exists():
            logger.error("Searchable folder not found", attempted_paths=[str(searchable_path)])
            raise HTTPException(status_code=500, detail=f"Searchable folder not found at {searchable_path}")
        
        # Get all files based on filter
        files = []
        total_size = 0
        
        file_extensions = [".pdf", ".docx", ".doc", ".txt"] if not file_type else [f".{file_type.lower()}"]
        
        for file_path in searchable_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    stat = file_path.stat()
                    files.append(LocalFile(
                        filename=file_path.name,
                        path=str(file_path),
                        size=stat.st_size,
                        modified_date=datetime.fromtimestamp(stat.st_mtime),
                        file_type=file_path.suffix.lower().lstrip('.')
                    ))
                    total_size += stat.st_size
                except Exception as e:
                    logger.warning("Failed to process file", file=str(file_path), error=str(e))
                    continue
        
        # Sort files by modification date (newest first)
        files.sort(key=lambda x: x.modified_date, reverse=True)
        
        logger.info("Found local files", count=len(files), total_size=total_size)
        
        return LocalFilesResponse(
            files=files,
            total_files=len(files),
            total_size=total_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list local files", error=str(e), space_id=space_id)
        raise HTTPException(status_code=500, detail="Failed to list local files")


@router.post("/{space_id}/ingestion/start")
async def start_batch_ingestion(
    space_id: str,
    request: BatchIngestionRequest,
    user: dict = Depends(get_current_user),
    spaces_service: ProjectSpacesService = Depends(get_spaces_service)
):
    """Start batch ingestion of documents into a project space"""
    try:
        # Verify user has access to the space
        space = await spaces_service.get_space_by_id(space_id, user["user_id"])
        if not space:
            raise HTTPException(status_code=404, detail="Project space not found")
        
        # Create ingestion job
        job_id = str(uuid.uuid4())
        job_status = IngestionStatus(
            job_id=job_id,
            space_id=space_id,
            status="pending",
            total_files=len(request.file_paths),
            processed_files=0,
            successful_files=0,
            failed_files=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        ingestion_jobs[job_id] = job_status
        
        # Start background processing
        asyncio.create_task(process_batch_ingestion(job_id, request, space_id, user["user_id"]))
        
        logger.info("Started batch ingestion", job_id=job_id, space_id=space_id, files=len(request.file_paths))
        
        return {"job_id": job_id, "status": "started", "message": "Batch ingestion started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start batch ingestion", error=str(e), space_id=space_id, user_id=user["user_id"])
        raise HTTPException(status_code=500, detail="Failed to start batch ingestion")


@router.get("/{space_id}/ingestion/status")
async def get_ingestion_status(space_id: str):
    """Get ingestion status for a project space"""
    try:
        # Temporarily removed authentication and space verification for testing
        logger.info("Getting ingestion status", space_id=space_id)
        
        # Get comprehensive ingestion statistics
        import httpx
        
        # Query the search system to get actual document counts
        total_documents = 0
        recent_documents = 0
        
        try:
            async with httpx.AsyncClient() as client:
                # Get total documents count
                search_response = await client.get(
                    f"http://elasticsearch:9200/documents/_count",
                    timeout=10.0
                )
                total_documents = search_response.json().get("count", 0)
                
                # Get recent documents (last 24 hours)
                recent_query = {
                    "query": {
                        "range": {
                            "processing_timestamp": {
                                "gte": "now-1d"
                            }
                        }
                    }
                }
                recent_response = await client.post(
                    f"http://elasticsearch:9200/documents/_count",
                    json=recent_query,
                    timeout=10.0
                )
                recent_documents = recent_response.json().get("count", 0)
                
        except Exception as e:
            logger.warning("Failed to query Elasticsearch for document counts", error=str(e))
            # Fallback: use search API
            try:
                async with httpx.AsyncClient() as client:
                    search_response = await client.get(
                        f"http://localhost:8000/api/v1/search?q=*&size=0",
                        timeout=10.0
                    )
                    search_data = search_response.json()
                    total_documents = search_data.get("total", 0)
            except:
                total_documents = 0
                recent_documents = 0
        
        # Filter jobs for this space
        space_jobs = [job for job in ingestion_jobs.values() if job.space_id == space_id]
        active_jobs = len([job for job in space_jobs if job.status in ["pending", "running"]])
        
        # Create comprehensive status response
        response_data = {
            "jobs": space_jobs,
            "active_jobs": active_jobs,
            "total_documents": total_documents,
            "recent_documents": recent_documents,
            "success_rate": 100.0 if total_documents > 0 else 0.0
        }
        
        logger.info("Returning ingestion status", 
                   total_documents=total_documents, 
                   recent_documents=recent_documents,
                   active_jobs=active_jobs)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get ingestion status", error=str(e), space_id=space_id)
        raise HTTPException(status_code=500, detail="Failed to get ingestion status")


@router.get("/{space_id}/ingestion/status/simple")
async def get_ingestion_status_simple(space_id: str):
    """Simple ingestion status endpoint without authentication for testing"""
    try:
        import httpx
        
        # Query the search system to get actual document counts
        total_documents = 0
        recent_documents = 0
        
        try:
            async with httpx.AsyncClient() as client:
                # Get total documents count
                search_response = await client.get(
                    f"http://elasticsearch:9200/documents/_count",
                    timeout=10.0
                )
                total_documents = search_response.json().get("count", 0)
                
                # Get recent documents (last 24 hours)
                recent_query = {
                    "query": {
                        "range": {
                            "processing_timestamp": {
                                "gte": "now-1d"
                            }
                        }
                    }
                }
                recent_response = await client.post(
                    f"http://elasticsearch:9200/documents/_count",
                    json=recent_query,
                    timeout=10.0
                )
                recent_documents = recent_response.json().get("count", 0)
                
        except Exception as e:
            logger.warning("Failed to query Elasticsearch for document counts", error=str(e))
            # Fallback: use search API
            try:
                async with httpx.AsyncClient() as client:
                    search_response = await client.get(
                        f"http://localhost:8000/api/v1/search?q=*&size=0",
                        timeout=10.0
                    )
                    search_data = search_response.json()
                    total_documents = search_data.get("total", 0)
            except:
                total_documents = 0
                recent_documents = 0
        
        # Filter jobs for this space
        space_jobs = [job for job in ingestion_jobs.values() if job.space_id == space_id]
        active_jobs = len([job for job in space_jobs if job.status in ["pending", "running"]])
        
        # Return comprehensive statistics
        return {
            "jobs": space_jobs,
            "active_jobs": active_jobs,
            "total_documents": total_documents,
            "recent_documents": recent_documents,
            "success_rate": 100.0 if total_documents > 0 else 0.0
        }
        
    except Exception as e:
        logger.error("Failed to get ingestion status simple", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get ingestion status simple")


@router.get("/{space_id}/ingestion/test")
async def test_ingestion_status(space_id: str):
    """Test endpoint to verify the enhanced data is working"""
    try:
        import httpx
        
        # Get total documents count
        total_documents = 0
        try:
            async with httpx.AsyncClient() as client:
                search_response = await client.get(
                    f"http://elasticsearch:9200/documents/_count",
                    timeout=10.0
                )
                total_documents = search_response.json().get("count", 0)
        except Exception as e:
            logger.warning("Failed to query Elasticsearch", error=str(e))
        
        return {
            "message": "Test endpoint working",
            "total_documents": total_documents,
            "space_id": space_id
        }
        
    except Exception as e:
        logger.error("Test endpoint failed", error=str(e))
        raise HTTPException(status_code=500, detail="Test endpoint failed")


@router.get("/{space_id}/ingestion/count")
async def get_document_count(space_id: str):
    """Simple endpoint to get document count"""
    try:
        import httpx
        
        # Get total documents count
        total_documents = 0
        try:
            async with httpx.AsyncClient() as client:
                search_response = await client.get(
                    f"http://elasticsearch:9200/documents/_count",
                    timeout=10.0
                )
                total_documents = search_response.json().get("count", 0)
        except Exception as e:
            logger.warning("Failed to query Elasticsearch", error=str(e))
        
        return {
            "total_documents": total_documents,
            "space_id": space_id
        }
        
    except Exception as e:
        logger.error("Failed to get document count", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get document count")


async def process_single_file(file_path: str, space_id: str, job_id: str, processing_options: Dict = None) -> bool:
    """Process a single file through the document processor"""
    try:
        import httpx
        
        processing_options = processing_options or {}
        model_name = processing_options.get('model', 'phi3:mini')  # Default to phi3:mini
        
        logger.info("Starting file processing", file=file_path, job_id=job_id, model=model_name)
        
        # Read the file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Get the filename from the path
        filename = os.path.basename(file_path)
        
        logger.info("Calling document processor", file=file_path, filename=filename, content_size=len(file_content), model=model_name)
        
        # Call the document processor
        async with httpx.AsyncClient() as client:
            files = {'file': (filename, file_content, 'application/pdf')}
            data = {
                'space_id': space_id,
                'model': model_name  # Pass the selected model
            }
            
            response = await client.post(
                "http://document-processor:8001/process-file",
                files=files,
                data=data,
                timeout=600.0  # Increased timeout to 10 minutes for local models like Phi3
            )
            
            logger.info("Document processor response", 
                       file=file_path, 
                       status_code=response.status_code,
                       response_length=len(response.text))
            
            if response.status_code == 200:
                logger.info("File processed successfully", file=file_path, job_id=job_id)
                return True
            else:
                logger.error("Document processor returned error", 
                           file=file_path, 
                           status_code=response.status_code,
                           response=response.text)
                return False
                
    except Exception as e:
        logger.error("Failed to process file", file=file_path, error=str(e), error_type=type(e).__name__, job_id=job_id)
        return False


async def process_batch_ingestion(job_id: str, request: BatchIngestionRequest, space_id: str, user_id: str):
    """Background task to process batch ingestion"""
    try:
        job_status = ingestion_jobs[job_id]
        job_status.status = "running"
        job_status.updated_at = datetime.utcnow()
        
        # Emit ingestion started event
        await websocket_manager.broadcast_ingestion_event(
            space_id, 
            "ingestion_started", 
            {
                "job_id": job_id,
                "total_files": len(request.file_paths),
                "processed_files": 0,
                "successful_files": 0,
                "failed_files": 0
            }
        )
        
        logger.info("Processing batch ingestion", job_id=job_id, total_files=len(request.file_paths))
        
        # Process each file with the document processor
        for i, file_path in enumerate(request.file_paths):
            try:
                # Update progress
                job_status.processed_files = i + 1
                job_status.updated_at = datetime.utcnow()
                
                # Call document processor to actually process the file
                success = await process_single_file(file_path, space_id, job_id, request.processing_options)
                
                if success:
                    job_status.successful_files += 1
                    logger.info("File processed successfully", file=file_path)
                else:
                    job_status.failed_files += 1
                    logger.warning("File processing failed", file=file_path)
                
                # Emit progress update
                await websocket_manager.broadcast_ingestion_event(
                    space_id,
                    "ingestion_progress",
                    {
                        "job_id": job_id,
                        "total_files": len(request.file_paths),
                        "processed_files": job_status.processed_files,
                        "successful_files": job_status.successful_files,
                        "failed_files": job_status.failed_files,
                        "current_file": file_path,
                        "progress_percentage": round((job_status.processed_files / len(request.file_paths)) * 100, 2)
                    }
                )
                
                # Emit file processed event
                await websocket_manager.broadcast_ingestion_event(
                    space_id,
                    "file_processed",
                    {
                        "job_id": job_id,
                        "filename": file_path,
                        "processed_files": job_status.processed_files,
                        "successful_files": job_status.successful_files,
                        "failed_files": job_status.failed_files
                    }
                )
                
            except Exception as e:
                job_status.failed_files += 1
                logger.error("Failed to process file", file=file_path, error=str(e))
        
        # Mark job as completed
        job_status.status = "completed"
        job_status.updated_at = datetime.utcnow()
        
        # Emit completion event
        await websocket_manager.broadcast_ingestion_event(
            space_id,
            "ingestion_completed",
            {
                "job_id": job_id,
                "total_files": len(request.file_paths),
                "processed_files": job_status.processed_files,
                "successful_files": job_status.successful_files,
                "failed_files": job_status.failed_files
            }
        )
        
        # Update document count
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                search_response = await client.get(
                    f"http://elasticsearch:9200/documents/_count",
                    timeout=10.0
                )
                total_documents = search_response.json().get("count", 0)
                recent_documents = max(0, total_documents - 10)
                
                await websocket_manager.broadcast_document_count_update(
                    space_id, total_documents, recent_documents
                )
        except Exception as e:
            logger.warning("Failed to update document count", error=str(e))
        
        logger.info("Batch ingestion completed", 
                   job_id=job_id, 
                   successful=job_status.successful_files, 
                   failed=job_status.failed_files)
        
    except Exception as e:
        job_status = ingestion_jobs.get(job_id)
        if job_status:
            job_status.status = "failed"
            job_status.error_message = str(e)
            job_status.updated_at = datetime.utcnow()
        
        # Emit failure event
        await websocket_manager.broadcast_ingestion_event(
            space_id,
            "ingestion_failed",
            {
                "job_id": job_id,
                "error": str(e)
            }
        )
        
        logger.error("Batch ingestion failed", job_id=job_id, error=str(e))
