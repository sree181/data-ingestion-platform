"""
Multi-Source Orchestrator
=========================

Orchestrates ingestion from multiple data sources in parallel.
This is the main entry point for multi-source data operations.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from ..base.abstract_data_source import AbstractDataSource, StandardDocument, SourceType, DocumentType
from .data_source_registry import get_registry, DataSourceRegistry

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Result of a multi-source search"""
    query: str
    total_documents: int
    sources_searched: List[str]
    documents: List[StandardDocument]
    source_breakdown: Dict[str, int]  # {source_name: count}
    search_time_ms: int
    errors: List[Dict[str, str]]  # {source: error_message}
    facets: Dict[str, Any]  # Aggregated facets across sources

@dataclass
class IngestionJob:
    """Represents a multi-source ingestion job"""
    job_id: str
    project_space_id: str
    query: str
    sources: List[str]
    filters: Dict[str, Any]
    status: str  # pending, running, completed, failed
    total_documents: int
    processed_documents: int
    failed_documents: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    errors: List[Dict[str, str]]

class MultiSourceOrchestrator:
    """
    Orchestrates ingestion from multiple data sources
    
    This class provides:
    - Parallel search across multiple sources
    - Unified result aggregation
    - Error handling and recovery
    - Progress tracking
    - Result deduplication
    """
    
    def __init__(self, registry: Optional[DataSourceRegistry] = None):
        self.registry = registry or get_registry()
        self.ai_processor = None  # Will be injected
        self.storage = None  # Will be injected
        self._setup_logging()
        self._active_jobs: Dict[str, IngestionJob] = {}
    
    def _setup_logging(self):
        """Setup logging for the orchestrator"""
        self.logger = logging.getLogger("multi_source_orchestrator")
    
    async def search_all_sources(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        deduplicate: bool = True
    ) -> SearchResult:
        """
        Search across multiple sources in parallel
        
        Args:
            query: Search query string
            sources: List of source names to search (None = all enabled)
            max_results_per_source: Max results per source
            filters: Source-specific filters
            date_from: Start date filter
            date_to: End date filter
            deduplicate: Whether to deduplicate results
            
        Returns:
            SearchResult with aggregated documents and metadata
        """
        start_time = datetime.now()
        
        # Get sources to search
        if sources is None:
            source_connectors = self.registry.get_healthy_sources()
        else:
            source_connectors = []
            for source_name in sources:
                connector = self.registry.get_source(source_name)
                if connector:
                    source_connectors.append(connector)
        
        if not source_connectors:
            return SearchResult(
                query=query,
                total_documents=0,
                sources_searched=[],
                documents=[],
                source_breakdown={},
                search_time_ms=0,
                errors=[{"error": "No healthy sources available"}],
                facets={}
            )
        
        self.logger.info(f"Searching {len(source_connectors)} sources for query: {query}")
        
        # Create search tasks
        tasks = []
        for connector in source_connectors:
            task = self._search_single_source(
                connector, query, max_results_per_source, filters, date_from, date_to
            )
            tasks.append((connector.source_name, task))
        
        # Execute searches in parallel
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Process results
        all_documents = []
        source_breakdown = {}
        errors = []
        facets = {}
        
        for i, (source_name, result) in enumerate(zip([name for name, _ in tasks], results)):
            if isinstance(result, Exception):
                error_msg = f"Error searching {source_name}: {str(result)}"
                self.logger.error(error_msg)
                errors.append({"source": source_name, "error": str(result)})
                source_breakdown[source_name] = 0
            else:
                documents = result
                all_documents.extend(documents)
                source_breakdown[source_name] = len(documents)
                self.logger.info(f"{source_name}: {len(documents)} documents")
        
        # Deduplicate if requested
        if deduplicate:
            all_documents = self._deduplicate_documents(all_documents)
        
        # Generate facets
        facets = self._generate_facets(all_documents)
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResult(
            query=query,
            total_documents=len(all_documents),
            sources_searched=list(source_breakdown.keys()),
            documents=all_documents,
            source_breakdown=source_breakdown,
            search_time_ms=int(search_time),
            errors=errors,
            facets=facets
        )
    
    async def _search_single_source(
        self,
        connector: AbstractDataSource,
        query: str,
        max_results: int,
        filters: Optional[Dict],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[StandardDocument]:
        """Search a single source with error handling"""
        try:
            return await connector.search(
                query=query,
                max_results=max_results,
                filters=filters,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            self.logger.error(f"Error searching {connector.source_name}: {e}")
            raise
    
    def _deduplicate_documents(self, documents: List[StandardDocument]) -> List[StandardDocument]:
        """
        Remove duplicate documents based on source_id and source
        
        Priority order for keeping documents:
        1. PubMed (highest quality)
        2. ClinicalTrials.gov
        3. FDA
        4. Others (alphabetical)
        """
        source_priority = {
            "pubmed": 1,
            "clinicaltrials": 2,
            "fda": 3,
            "chembl": 4,
            "pubchem": 5,
            "europepmc": 6,
            "semanticscholar": 7
        }
        
        # Group by source_id
        grouped = {}
        for doc in documents:
            key = f"{doc.source}:{doc.source_id}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(doc)
        
        # Keep highest priority document from each group
        deduplicated = []
        for docs in grouped.values():
            if len(docs) == 1:
                deduplicated.append(docs[0])
            else:
                # Sort by priority and keep the first one
                docs.sort(key=lambda d: source_priority.get(d.source, 999))
                deduplicated.append(docs[0])
        
        self.logger.info(f"Deduplicated {len(documents)} -> {len(deduplicated)} documents")
        return deduplicated
    
    def _generate_facets(self, documents: List[StandardDocument]) -> Dict[str, Any]:
        """Generate facets for faceted navigation"""
        facets = {
            "sources": {},
            "document_types": {},
            "years": {},
            "top_entities": {},
            "top_authors": {}
        }
        
        for doc in documents:
            # Source breakdown
            facets["sources"][doc.source] = facets["sources"].get(doc.source, 0) + 1
            
            # Document type breakdown
            doc_type = doc.document_type.value
            facets["document_types"][doc_type] = facets["document_types"].get(doc_type, 0) + 1
            
            # Year breakdown
            if doc.publication_date:
                year = doc.publication_date.year
                facets["years"][str(year)] = facets["years"].get(str(year), 0) + 1
            
            # Top entities
            for entity_type, entities in doc.entities.items():
                for entity in entities:
                    key = f"{entity_type}:{entity.normalized_value}"
                    facets["top_entities"][key] = facets["top_entities"].get(key, 0) + 1
            
            # Top authors
            for author in doc.authors:
                facets["top_authors"][author.name] = facets["top_authors"].get(author.name, 0) + 1
        
        # Sort and limit facets
        for facet_name in ["top_entities", "top_authors"]:
            facets[facet_name] = dict(
                sorted(facets[facet_name].items(), key=lambda x: x[1], reverse=True)[:20]
            )
        
        return facets
    
    async def ingest_from_sources(
        self,
        project_space_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Complete ingestion workflow from multiple sources
        
        Args:
            project_space_id: Target project space
            query: Search query
            sources: Sources to ingest from
            max_results_per_source: Max results per source
            filters: Source-specific filters
            options: Additional options (AI model, etc.)
            
        Returns:
            Job ID for tracking progress
        """
        job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_space_id[:8]}"
        
        # Create ingestion job
        job = IngestionJob(
            job_id=job_id,
            project_space_id=project_space_id,
            query=query,
            sources=sources or [],
            filters=filters or {},
            status="pending",
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            started_at=None,
            completed_at=None,
            errors=[]
        )
        
        self._active_jobs[job_id] = job
        
        # Start ingestion asynchronously
        asyncio.create_task(self._run_ingestion_job(job, max_results_per_source, options))
        
        return job_id
    
    async def _run_ingestion_job(
        self, 
        job: IngestionJob, 
        max_results_per_source: int,
        options: Optional[Dict[str, Any]]
    ):
        """Run the actual ingestion job"""
        try:
            job.status = "running"
            job.started_at = datetime.now()
            
            # Search all sources
            search_result = await self.search_all_sources(
                query=job.query,
                sources=job.sources,
                max_results_per_source=max_results_per_source,
                filters=job.filters
            )
            
            job.total_documents = search_result.total_documents
            job.errors.extend(search_result.errors)
            
            # Process each document
            for doc in search_result.documents:
                try:
                    # Set project space
                    doc.project_space_id = job.project_space_id
                    
                    # AI enrichment if available
                    if self.ai_processor:
                        await self._enrich_document(doc, options)
                    
                    # Store document
                    if self.storage:
                        await self._store_document(doc)
                    
                    job.processed_documents += 1
                    
                except Exception as e:
                    job.failed_documents += 1
                    job.errors.append({
                        "document_id": doc.id,
                        "error": str(e)
                    })
                    self.logger.error(f"Failed to process document {doc.id}: {e}")
            
            job.status = "completed"
            job.completed_at = datetime.now()
            
            self.logger.info(
                f"Completed ingestion job {job.job_id}: "
                f"{job.processed_documents}/{job.total_documents} documents processed"
            )
            
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now()
            job.errors.append({"job_error": str(e)})
            self.logger.error(f"Ingestion job {job.job_id} failed: {e}")
    
    async def _enrich_document(self, doc: StandardDocument, options: Optional[Dict[str, Any]]):
        """Apply AI processing to extract entities, relationships, etc."""
        if not self.ai_processor:
            return
        
        try:
            # Extract entities
            text = f"{doc.title} {doc.abstract or ''} {doc.content or ''}"
            model_name = options.get("model", "phi3:mini") if options else "phi3:mini"
            
            entities = await self.ai_processor.extract_entities(text, model_name)
            doc.entities = entities
            
            # Extract relationships
            relationships = await self.ai_processor.extract_relationships(text, entities)
            doc.relationships = relationships
            
            # Generate summary if not present
            if not doc.summary and len(text) > 500:
                doc.summary = await self.ai_processor.summarize(text, model_name)
            
            # Extract key concepts
            key_concepts = await self.ai_processor.extract_key_concepts(text, model_name)
            doc.key_concepts = key_concepts
            
            # Calculate quality score
            doc.quality_score = self._calculate_quality_score(doc)
            
            doc.processing_status = "completed"
            
        except Exception as e:
            self.logger.error(f"Failed to enrich document {doc.id}: {e}")
            doc.processing_errors.append(str(e))
            doc.processing_status = "failed"
    
    async def _store_document(self, doc: StandardDocument):
        """Store document in all relevant databases"""
        if not self.storage:
            return
        
        try:
            # Store in PostgreSQL (metadata)
            await self.storage.store_document_metadata(doc)
            
            # Index in Elasticsearch (search)
            await self.storage.index_document(doc)
            
            # Add to Neo4j (knowledge graph)
            await self.storage.create_document_node(doc)
            await self.storage.create_entity_links(doc)
            
            # Store content in MinIO if available
            if doc.content:
                await self.storage.store_document_content(doc.id, doc.content)
                
        except Exception as e:
            self.logger.error(f"Failed to store document {doc.id}: {e}")
            raise
    
    def _calculate_quality_score(self, doc: StandardDocument) -> float:
        """Calculate a quality score for the document"""
        score = 0.0
        
        # Basic content quality
        if doc.title:
            score += 10
        if doc.abstract:
            score += 20
        if doc.content:
            score += 30
        if doc.doi:
            score += 10
        if doc.authors:
            score += 10
        if doc.publication_date:
            score += 10
        
        # Source quality
        source_scores = {
            "pubmed": 20,
            "clinicaltrials": 15,
            "fda": 15,
            "chembl": 10,
            "pubchem": 10,
            "europepmc": 10,
            "semanticscholar": 8
        }
        score += source_scores.get(doc.source, 5)
        
        # Entity richness
        total_entities = sum(len(entities) for entities in doc.entities.values())
        score += min(total_entities * 0.5, 10)
        
        return min(score, 100.0)
    
    def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        """Get the status of an ingestion job"""
        return self._active_jobs.get(job_id)
    
    def list_active_jobs(self) -> List[IngestionJob]:
        """List all active ingestion jobs"""
        return list(self._active_jobs.values())
    
    def cleanup_completed_jobs(self, older_than_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff = datetime.now().timestamp() - (older_than_hours * 3600)
        
        to_remove = []
        for job_id, job in self._active_jobs.items():
            if (job.status in ["completed", "failed"] and 
                job.completed_at and 
                job.completed_at.timestamp() < cutoff):
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self._active_jobs[job_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old jobs")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get statistics about the orchestrator"""
        active_jobs = len(self._active_jobs)
        completed_jobs = sum(1 for job in self._active_jobs.values() if job.status == "completed")
        failed_jobs = sum(1 for job in self._active_jobs.values() if job.status == "failed")
        running_jobs = sum(1 for job in self._active_jobs.values() if job.status == "running")
        
        return {
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": running_jobs,
            "total_sources": len(self.registry.get_all_sources()),
            "healthy_sources": len(self.registry.get_healthy_sources())
        }
