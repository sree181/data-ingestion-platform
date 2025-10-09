"""
Unified Search API Routes
========================

API endpoints for unified search across all data sources.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import time

from services.unified_search_service import UnifiedSearchService
from auth.jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/unified-search", tags=["unified-search"])

# Initialize unified search service
unified_search_service = UnifiedSearchService()

@router.get("/")
async def unified_search_get(
    q: str = Query(..., description="Search query"),
    sources: Optional[str] = Query(None, description="Comma-separated list of source IDs"),
    document_types: Optional[str] = Query(None, description="Comma-separated list of document types"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    page: int = Query(0, ge=0, description="Page number (0-based)"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    sort_by: str = Query("relevance", description="Sort field (relevance, date, quality)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform unified search across all enabled data sources (GET endpoint)
    
    Args:
        q: Search query
        sources: Comma-separated list of source IDs to search
        document_types: Comma-separated list of document types to filter
        date_from: Start date filter (YYYY-MM-DD)
        date_to: End date filter (YYYY-MM-DD)
        page: Page number (0-based)
        size: Page size
        sort_by: Sort field (relevance, date, quality)
        sort_order: Sort order (asc, desc)
    
    Returns:
        Unified search results with documents from all sources
    """
    try:
        # Convert query parameters to search request format
        search_request = {
            "q": q,
            "sources": sources.split(",") if sources else None,
            "document_types": document_types.split(",") if document_types else None,
            "date_from": date_from,
            "date_to": date_to,
            "page": page,
            "size": size,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Call the unified search service
        results = await unified_search_service.search_all_sources(
            query=search_request["q"],
            sources=search_request["sources"],
            document_types=search_request["document_types"],
            date_from=datetime.fromisoformat(search_request["date_from"]) if search_request["date_from"] else None,
            date_to=datetime.fromisoformat(search_request["date_to"]) if search_request["date_to"] else None,
            max_results_per_source=search_request["size"],
            sort_by=search_request["sort_by"],
            sort_order=search_request["sort_order"]
        )
        
        # Convert SearchResult to dictionary format
        results_by_source = {}
        for doc in results.documents:
            source = doc.source
            if source not in results_by_source:
                results_by_source[source] = []
            results_by_source[source].append({
                "id": doc.id,
                "title": doc.title,
                "abstract": doc.abstract,
                "source": doc.source,
                "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "authors": [{"name": author.name, "affiliation": author.affiliation} for author in doc.authors],
                "url": doc.url,
                "doi": doc.doi
            })
        
        return {
            "query": q,
            "total_results": results.total_documents,
            "results_by_source": results_by_source,
            "all_results": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "abstract": doc.abstract,
                    "source": doc.source,
                    "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                    "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                    "authors": [{"name": author.name, "affiliation": author.affiliation} for author in doc.authors],
                    "url": doc.url,
                    "doi": doc.doi
                } for doc in results.documents
            ],
            "search_metadata": {
                "sources_searched": results.sources_searched,
                "source_breakdown": results.source_breakdown,
                "search_time_ms": results.search_time_ms,
                "errors": results.errors
            },
            "pagination": {
                "page": page,
                "size": size,
                "total_pages": (results.total_documents + size - 1) // size
            }
        }
        
    except Exception as e:
        logger.error(f"Unified search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/")
async def unified_search(
    search_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Perform unified search across all enabled data sources
    
    Args:
        search_request: Search parameters including:
            - q: Search query
            - sources: List of source IDs to search
            - document_types: List of document types to filter
            - date_from: Start date filter
            - date_to: End date filter
            - page: Page number (0-based)
            - size: Page size
            - sort_by: Sort field (relevance, date, quality)
            - sort_order: Sort order (asc, desc)
    
    Returns:
        Unified search results with documents from all sources
    """
    try:
        start_time = time.time()
        
        # Extract search parameters
        query = search_request.get("q", "").strip()
        if not query or len(query) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Search query must be at least 2 characters long"
            )
        
        sources = search_request.get("sources", [])
        document_types = search_request.get("document_types", [])
        date_from = search_request.get("date_from")
        date_to = search_request.get("date_to")
        page = search_request.get("page", 0)
        size = search_request.get("size", 25)
        sort_by = search_request.get("sort_by", "relevance")
        sort_order = search_request.get("sort_order", "desc")
        
        # Validate parameters
        if page < 0:
            raise HTTPException(status_code=400, detail="Page must be non-negative")
        if size < 1 or size > 100:
            raise HTTPException(status_code=400, detail="Size must be between 1 and 100")
        if sort_by not in ["relevance", "date", "quality"]:
            raise HTTPException(status_code=400, detail="Invalid sort_by parameter")
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Invalid sort_order parameter")
        
        # Parse dates if provided
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")
        
        logger.info(
            f"Unified search request",
            user_id=current_user.get("user_id"),
            query=query,
            sources=sources,
            document_types=document_types,
            page=page,
            size=size
        )
        
        # Perform unified search
        search_result = await unified_search_service.search_all_sources(
            query=query,
            sources=sources,
            document_types=document_types,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            max_results_per_source=size * 2,  # Get more results for better sorting
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Apply pagination
        start_idx = page * size
        end_idx = start_idx + size
        paginated_results = search_result.documents[start_idx:end_idx]
        
        # Calculate search time
        search_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = {
            "query": query,
            "total": search_result.total_documents,
            "page": page,
            "size": size,
            "total_pages": (search_result.total_documents + size - 1) // size,
            "results": paginated_results,
            "sources_searched": search_result.sources_searched,
            "source_breakdown": search_result.source_breakdown,
            "search_time_ms": search_time_ms,
            "errors": search_result.errors,
            "facets": search_result.facets,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        logger.info(
            f"Unified search completed",
            user_id=current_user.get("user_id"),
            total_results=search_result.total_documents,
            search_time_ms=search_time_ms,
            sources_searched=len(search_result.sources_searched)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/sources")
async def get_available_sources(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of available data sources and their status
    
    Returns:
        List of data sources with their configuration and status
    """
    try:
        sources = await unified_search_service.get_available_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting available sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

@router.get("/health")
async def get_search_health(
    current_user: dict = Depends(get_current_user)
):
    """
    Get health status of all data sources
    
    Returns:
        Health status of all sources
    """
    try:
        health_status = await unified_search_service.get_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error getting search health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.post("/sources/{source_id}/test")
async def test_source_connection(
    source_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Test connection to a specific data source
    
    Args:
        source_id: ID of the source to test
    
    Returns:
        Test result with connection status
    """
    try:
        result = await unified_search_service.test_source_connection(source_id)
        return result
    except Exception as e:
        logger.error(f"Error testing source {source_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to test source: {str(e)}")

@router.get("/facets")
async def get_search_facets(
    query: str = Query("", description="Search query to generate facets for"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get search facets for a given query
    
    Args:
        query: Search query to generate facets for
    
    Returns:
        Available facets for the query
    """
    try:
        if not query or len(query) < 2:
            return {"facets": {}}
        
        facets = await unified_search_service.get_search_facets(query)
        return {"facets": facets}
    except Exception as e:
        logger.error(f"Error getting search facets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get facets: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query("", description="Partial search query"),
    limit: int = Query(10, description="Maximum number of suggestions"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get search suggestions based on partial query
    
    Args:
        q: Partial search query
        limit: Maximum number of suggestions
    
    Returns:
        List of search suggestions
    """
    try:
        if not q or len(q) < 2:
            return {"suggestions": []}
        
        suggestions = await unified_search_service.get_search_suggestions(q, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")