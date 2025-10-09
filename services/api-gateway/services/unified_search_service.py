"""
Unified Search Service
=====================

Service for coordinating searches across multiple data sources.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from data_connectors.orchestrator.multi_source_orchestrator import MultiSourceOrchestrator
from data_connectors.orchestrator.data_source_registry import get_registry
from data_connectors.sources.clinicaltrials_connector import ClinicalTrialsConnector
from data_connectors.sources.fda_connector import FDAConnector
from data_connectors.sources.chembl_connector import ChEMBLConnector
from data_connectors.sources.semantic_scholar_connector import SemanticScholarConnector
from data_connectors.sources.europepmc_connector import EuropePMCConnector

logger = logging.getLogger(__name__)

class UnifiedSearchService:
    """
    Service for unified search across all data sources
    """
    
    def __init__(self):
        self.orchestrator = MultiSourceOrchestrator()
        self.registry = get_registry()
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize all available data sources"""
        try:
            # Register all available sources
            source_classes = [
                ClinicalTrialsConnector,
                FDAConnector,
                ChEMBLConnector,  # Will be disabled by default (needs API key)
                SemanticScholarConnector,
                EuropePMCConnector
            ]
            
            for source_class in source_classes:
                self.registry.register(source_class)
                logger.info(f"Registered source: {source_class.__name__}")
            
            # Enable sources that don't require API keys
            enabled_sources = ['clinicaltrials', 'fda', 'semanticscholar', 'europepmc']
            for source_id in enabled_sources:
                self.registry.enable_source(source_id)
                logger.info(f"Enabled source: {source_id}")
            
        except Exception as e:
            logger.error(f"Error initializing sources: {e}", exc_info=True)
    
    async def search_all_sources(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        max_results_per_source: int = 50,
        sort_by: str = "relevance",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Search across all enabled sources
        
        Args:
            query: Search query
            sources: List of source IDs to search (None for all enabled)
            document_types: List of document types to filter
            date_from: Start date filter
            date_to: End date filter
            max_results_per_source: Maximum results per source
            sort_by: Sort field (relevance, date, quality)
            sort_order: Sort order (asc, desc)
        
        Returns:
            Unified search results
        """
        try:
            start_time = time.time()
            
            # Use all enabled sources if none specified
            if not sources:
                all_sources = self.registry.get_all_source_info()
                sources = [source.name for source in all_sources if source.is_enabled]
            
            # Filter sources to only enabled ones
            enabled_sources = []
            all_sources = self.registry.get_all_source_info()
            source_info_map = {source.name: source for source in all_sources}
            
            for source_id in sources:
                source_info = source_info_map.get(source_id)
                if source_info and source_info.is_enabled:
                    enabled_sources.append(source_id)
                else:
                    logger.warning(f"Source {source_id} is not enabled, skipping")
            
            if not enabled_sources:
                return {
                    "documents": [],
                    "total_documents": 0,
                    "sources_searched": [],
                    "source_breakdown": {},
                    "search_time_ms": 0,
                    "errors": ["No enabled sources available"],
                    "facets": {}
                }
            
            # Perform search using orchestrator
            search_result = await self.orchestrator.search_all_sources(
                query=query,
                sources=enabled_sources,
                max_results_per_source=max_results_per_source,
                filters={
                    "document_types": document_types,
                    "date_from": date_from,
                    "date_to": date_to
                }
            )
            
            # Apply document type filtering if specified
            if document_types:
                filtered_docs = []
                for doc in search_result.documents:
                    if doc.document_type.value in document_types:
                        filtered_docs.append(doc)
                search_result.documents = filtered_docs
                search_result.total_documents = len(filtered_docs)
            
            # Sort results
            search_result.documents = self._sort_documents(
                search_result.documents, 
                sort_by, 
                sort_order
            )
            
            # Generate facets
            facets = self._generate_facets(search_result.documents)
            search_result.facets = facets
            
            # Calculate search time
            search_time_ms = int((time.time() - start_time) * 1000)
            search_result.search_time_ms = search_time_ms
            
            logger.info(
                f"Unified search completed",
                query=query,
                total_documents=search_result.total_documents,
                sources_searched=len(search_result.sources_searched),
                search_time_ms=search_time_ms
            )
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error in unified search: {e}", exc_info=True)
            raise
    
    def _sort_documents(
        self, 
        documents: List[Any], 
        sort_by: str, 
        sort_order: str
    ) -> List[Any]:
        """Sort documents by specified field and order"""
        try:
            if not documents:
                return documents
            
            # Define sort key functions
            def get_sort_key(doc):
                if sort_by == "relevance":
                    return doc.quality_score or 0
                elif sort_by == "date":
                    return doc.publication_date or datetime.min
                elif sort_by == "quality":
                    return doc.quality_score or 0
                else:
                    return 0
            
            # Sort documents
            reverse = sort_order == "desc"
            sorted_docs = sorted(documents, key=get_sort_key, reverse=reverse)
            
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Error sorting documents: {e}", exc_info=True)
            return documents
    
    def _generate_facets(self, documents: List[Any]) -> Dict[str, Any]:
        """Generate facets from search results"""
        try:
            facets = {
                "sources": {},
                "document_types": {},
                "years": {},
                "top_entities": {},
                "top_authors": {}
            }
            
            for doc in documents:
                # Source facet
                source = doc.source
                facets["sources"][source] = facets["sources"].get(source, 0) + 1
                
                # Document type facet
                doc_type = doc.document_type.value
                facets["document_types"][doc_type] = facets["document_types"].get(doc_type, 0) + 1
                
                # Year facet
                if doc.publication_date:
                    year = doc.publication_date.year
                    facets["years"][str(year)] = facets["years"].get(str(year), 0) + 1
                
                # Top entities facet
                if hasattr(doc, 'entities') and doc.entities:
                    for entity_type, entities in doc.entities.items():
                        for entity in entities[:3]:  # Limit to top 3 per document
                            entity_key = f"{entity_type}:{entity.value}"
                            facets["top_entities"][entity_key] = facets["top_entities"].get(entity_key, 0) + 1
                
                # Top authors facet
                if hasattr(doc, 'authors') and doc.authors:
                    for author in doc.authors[:2]:  # Limit to top 2 per document
                        author_name = author.name
                        facets["top_authors"][author_name] = facets["top_authors"].get(author_name, 0) + 1
            
            # Sort facets by count and limit to top 10
            for facet_name in facets:
                if facet_name in ["top_entities", "top_authors"]:
                    facets[facet_name] = dict(
                        sorted(facets[facet_name].items(), key=lambda x: x[1], reverse=True)[:10]
                    )
            
            return facets
            
        except Exception as e:
            logger.error(f"Error generating facets: {e}", exc_info=True)
            return {}
    
    async def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get list of available data sources"""
        try:
            sources = []
            all_sources = self.registry.get_all_source_info()
            
            for source_info in all_sources:
                # Create a temporary instance to access properties
                temp_instance = source_info.connector_class()
                source_data = {
                    "id": source_info.name,
                    "name": source_info.display_name,
                    "description": getattr(temp_instance, 'description', ''),
                    "enabled": source_info.is_enabled,
                    "requires_api_key": getattr(temp_instance, 'requires_api_key', False),
                    "rate_limits": getattr(temp_instance, 'rate_limits', {}),
                    "supported_document_types": [dt.value for dt in temp_instance.supported_document_types],
                    "source_type": source_info.source_type.value
                }
                sources.append(source_data)
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting available sources: {e}", exc_info=True)
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all sources"""
        try:
            health_report = await self.registry.health_check_all()
            
            healthy_count = sum(1 for status in health_report.values() if status.get('status') == 'healthy')
            total_count = len(health_report)
            
            return {
                "status": "healthy" if healthy_count > 0 else "unhealthy",
                "statistics": {
                    "total_sources": total_count,
                    "healthy_sources": healthy_count,
                    "unhealthy_sources": total_count - healthy_count
                },
                "sources": health_report
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "sources": {}
            }
    
    async def test_source_connection(self, source_id: str) -> Dict[str, Any]:
        """Test connection to a specific source"""
        try:
            source = self.registry.get_source(source_id)
            if not source:
                return {
                    "status": "error",
                    "message": f"Source {source_id} not found"
                }
            
            # Run health check
            health_result = await source.health_check()
            
            return {
                "source_id": source_id,
                "status": health_result.get("status", "unknown"),
                "response_time_ms": health_result.get("response_time_ms", 0),
                "last_check": health_result.get("last_check"),
                "message": health_result.get("error", "Connection successful")
            }
            
        except Exception as e:
            logger.error(f"Error testing source {source_id}: {e}", exc_info=True)
            return {
                "source_id": source_id,
                "status": "error",
                "message": str(e)
            }
    
    async def get_search_facets(self, query: str) -> Dict[str, Any]:
        """Get search facets for a query"""
        try:
            # Perform a quick search to get facets
            search_result = await self.search_all_sources(
                query=query,
                max_results_per_source=10  # Small number for facet generation
            )
            
            return search_result.facets or {}
            
        except Exception as e:
            logger.error(f"Error getting search facets: {e}", exc_info=True)
            return {}
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            # This is a simple implementation - in production, you'd want to use
            # a proper search suggestion service or cache common queries
            suggestions = []
            
            # Common medical/research terms for suggestions
            common_terms = [
                "cancer", "diabetes", "hypertension", "depression", "asthma",
                "clinical trial", "adverse event", "drug safety", "pharmacology",
                "immunotherapy", "chemotherapy", "surgery", "diagnosis", "treatment",
                "aspirin", "insulin", "metformin", "warfarin", "statins"
            ]
            
            query_lower = query.lower()
            for term in common_terms:
                if term.startswith(query_lower) and len(suggestions) < limit:
                    suggestions.append(term)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}", exc_info=True)
            return []
