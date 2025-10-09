"""
ICSR Review API Routes
Handles ICSR extraction, review, validation, and XML generation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import structlog
from datetime import datetime
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/icsr", tags=["ICSR Review"])

# Configuration
PV_CLASSIFICATION_SERVICE = "http://pv-classification-service:8012"
ELASTICSEARCH_HOST = "http://elasticsearch:9200"


class ICSRExtractionRequest(BaseModel):
    """Request to extract ICSR data from a document"""
    document_id: str


class ICSRReviewUpdate(BaseModel):
    """Update ICSR data after reviewer changes"""
    document_id: str
    icsr_data: Dict[str, Any]
    reviewer_notes: Optional[str] = None
    status: str  # "pending", "approved", "rejected"


class ICSRApprovalRequest(BaseModel):
    """Approve ICSR and generate XML"""
    document_id: str
    reviewer_name: str
    reviewer_comments: Optional[str] = None


@router.post("/extract/{document_id}")
async def extract_icsr_data(document_id: str):
    """
    Extract ICSR data from a classified ICSR document
    
    This triggers the full ICSR extraction pipeline:
    1. Fetch document from Elasticsearch
    2. Send to PV Classification Service for ICSR extraction
    3. Generate AI narrative
    4. Store extracted data back to Elasticsearch
    """
    try:
        logger.info("ICSR extraction requested", document_id=document_id)
        
        # Step 1: Fetch document from Elasticsearch
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            doc_response = await es_client.get(index="documents", id=document_id)
            document = doc_response["_source"]
        finally:
            await es_client.close()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify it's classified as ICSR
        if document.get("classification") != "ICSR":
            raise HTTPException(
                status_code=400,
                detail=f"Document is not classified as ICSR (current: {document.get('classification')})"
            )
        
        # Check if already extracted
        if document.get("icsr_data"):
            logger.info("ICSR data already exists", document_id=document_id)
            return {
                "success": True,
                "message": "ICSR data already extracted",
                "document_id": document_id,
                "icsr_data": document["icsr_data"],
                "narrative": document.get("icsr_narrative"),
                "extraction_date": document.get("icsr_extraction_date"),
                "already_extracted": True
            }
        
        # Step 2: Send to PV Classification Service for extraction
        async with httpx.AsyncClient(timeout=180.0) as client:
            extraction_payload = {
                "document_id": document_id,
                "title": document.get("title", ""),
                "abstract": document.get("abstract", document.get("content", "")[:2000]),
                "full_text": document.get("content", ""),
                "pmid": document.get("pmid", ""),
                "doi": document.get("doi", "")
            }
            
            response = await client.post(
                f"{PV_CLASSIFICATION_SERVICE}/api/v1/extract/icsr",
                json=extraction_payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ICSR extraction failed: {response.text}"
                )
            
            extraction_result = response.json()
        
        # Step 3: Store extracted data in Elasticsearch
        # Store icsr_data as JSON string to avoid field limit issues
        import json as json_lib
        
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            await es_client.update(
                index="documents",
                id=document_id,
                body={
                    "doc": {
                        "icsr_data_json": json_lib.dumps(extraction_result.get("icsr_data")),
                        "icsr_narrative": extraction_result.get("narrative"),
                        "icsr_xml": extraction_result.get("xml"),
                        "icsr_extraction_date": extraction_result.get("extraction_date"),
                        "icsr_status": "pending_review",
                        "ai_processed": True
                    }
                }
            )
        finally:
            await es_client.close()
        
        logger.info("ICSR extraction completed", document_id=document_id)
        
        return {
            "success": True,
            "message": "ICSR data extracted successfully",
            "document_id": document_id,
            "icsr_data": extraction_result.get("icsr_data"),
            "narrative": extraction_result.get("narrative"),
            "xml_preview": extraction_result.get("xml")[:500] + "..." if extraction_result.get("xml") else None,
            "extraction_date": extraction_result.get("extraction_date"),
            "already_extracted": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ICSR extraction failed", document_id=document_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"ICSR extraction failed: {str(e)}")


@router.get("/{document_id}")
async def get_icsr_data(document_id: str):
    """
    Get ICSR data for a document
    """
    try:
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            doc_response = await es_client.get(index="documents", id=document_id)
            document = doc_response["_source"]
        finally:
            await es_client.close()
        
        if not document.get("icsr_data"):
            raise HTTPException(status_code=404, detail="No ICSR data found for this document")
        
        return {
            "success": True,
            "document_id": document_id,
            "title": document.get("title"),
            "classification": document.get("classification"),
            "icsr_data": document["icsr_data"],
            "narrative": document.get("icsr_narrative"),
            "extraction_date": document.get("icsr_extraction_date"),
            "status": document.get("icsr_status", "pending_review"),
            "reviewer_notes": document.get("icsr_reviewer_notes"),
            "approved_by": document.get("icsr_approved_by"),
            "approved_at": document.get("icsr_approved_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get ICSR data", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}")
async def update_icsr_data(document_id: str, update: ICSRReviewUpdate):
    """
    Update ICSR data after reviewer modifications
    """
    try:
        logger.info("Updating ICSR data", document_id=document_id, status=update.status)
        
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            await es_client.update(
                index="documents",
                id=document_id,
                body={
                    "doc": {
                        "icsr_data": update.icsr_data,
                        "icsr_status": update.status,
                        "icsr_reviewer_notes": update.reviewer_notes,
                        "icsr_last_modified": datetime.utcnow().isoformat()
                    }
                }
            )
        finally:
            await es_client.close()
        
        return {
            "success": True,
            "message": "ICSR data updated successfully",
            "document_id": document_id,
            "status": update.status
        }
        
    except Exception as e:
        logger.error("Failed to update ICSR data", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_icsr(approval: ICSRApprovalRequest):
    """
    Approve ICSR and generate final XML
    """
    try:
        logger.info("Approving ICSR", document_id=approval.document_id, reviewer=approval.reviewer_name)
        
        # Fetch document
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            doc_response = await es_client.get(index="documents", id=approval.document_id)
            document = doc_response["_source"]
        finally:
            await es_client.close()
        
        if not document.get("icsr_data"):
            raise HTTPException(status_code=404, detail="No ICSR data found")
        
        # Re-generate XML with latest data (in case reviewer modified it)
        async with httpx.AsyncClient(timeout=60.0) as client:
            # We could add a separate XML-only endpoint, or just extract the XML we already have
            icsr_xml = document.get("icsr_xml")
            
            if not icsr_xml:
                raise HTTPException(status_code=500, detail="XML not available")
        
        # Update status to approved
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            await es_client.update(
                index="documents",
                id=approval.document_id,
                body={
                    "doc": {
                        "icsr_status": "approved",
                        "icsr_approved_by": approval.reviewer_name,
                        "icsr_approved_at": datetime.utcnow().isoformat(),
                        "icsr_approval_comments": approval.reviewer_comments
                    }
                }
            )
        finally:
            await es_client.close()
        
        logger.info("ICSR approved", document_id=approval.document_id)
        
        return {
            "success": True,
            "message": "ICSR approved successfully",
            "document_id": approval.document_id,
            "xml": icsr_xml,
            "approved_by": approval.reviewer_name,
            "approved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to approve ICSR", document_id=approval.document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/xml")
async def download_icsr_xml(document_id: str):
    """
    Download ICH E2B R3 XML for approved ICSR
    """
    try:
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            doc_response = await es_client.get(index="documents", id=document_id)
            document = doc_response["_source"]
        finally:
            await es_client.close()
        
        if not document.get("icsr_xml"):
            raise HTTPException(status_code=404, detail="No XML available for this document")
        
        # Return XML content
        from fastapi.responses import Response
        
        return Response(
            content=document["icsr_xml"],
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=icsr_{document_id}.xml"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download XML", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/pending")
async def list_pending_icsrs():
    """
    List all ICSRs pending review
    """
    try:
        es_client = AsyncElasticsearch([ELASTICSEARCH_HOST])
        
        try:
            response = await es_client.search(
                index="documents",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"classification": "ICSR"}},
                                {"exists": {"field": "icsr_data"}},
                                {"term": {"icsr_status": "pending_review"}}
                            ]
                        }
                    },
                    "size": 100,
                    "_source": ["title", "pmid", "icsr_extraction_date", "classification_confidence"]
                }
            )
        finally:
            await es_client.close()
        
        documents = [
            {
                "document_id": hit["_id"],
                "title": hit["_source"].get("title"),
                "pmid": hit["_source"].get("pmid"),
                "extraction_date": hit["_source"].get("icsr_extraction_date"),
                "confidence": hit["_source"].get("classification_confidence")
            }
            for hit in response["hits"]["hits"]
        ]
        
        return {
            "success": True,
            "total": len(documents),
            "documents": documents
        }
        
    except Exception as e:
        logger.error("Failed to list pending ICSRs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

