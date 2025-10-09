"""
Multi-Source Ingestion Service
=============================

This service handles ingestion of documents from external data sources
into the existing document processing pipeline.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from data_connectors.orchestrator.multi_source_orchestrator import MultiSourceOrchestrator
from data_connectors.orchestrator.data_source_registry import get_registry
from data_connectors.base.abstract_data_source import StandardDocument
from data_connectors.sources.clinicaltrials_connector import ClinicalTrialsConnector
from data_connectors.sources.fda_connector import FDAConnector
from data_connectors.sources.chembl_connector import ChEMBLConnector
from data_connectors.sources.semantic_scholar_connector import SemanticScholarConnector
from data_connectors.sources.europepmc_connector import EuropePMCConnector

logger = logging.getLogger(__name__)

class MultiSourceIngestionService:
    """
    Service for ingesting documents from external data sources
    into the existing document processing pipeline.
    """
    
    def __init__(self):
        self.registry = get_registry()
        self.orchestrator = MultiSourceOrchestrator(self.registry)
        self._initialize_sources()
        
        # Track active ingestion jobs
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_sources(self):
        """Initialize all available data sources"""
        try:
            source_classes = [
                ClinicalTrialsConnector,
                FDAConnector,
                ChEMBLConnector,
                SemanticScholarConnector,
                EuropePMCConnector
            ]
            
            for source_class in source_classes:
                self.registry.register(source_class)
                logger.info(f"Registered source: {source_class.__name__}")
            
            # Enable sources that don't require API keys by default
            enabled_sources = ['clinicaltrials', 'fda', 'semanticscholar', 'europepmc']
            for source_id in enabled_sources:
                self.registry.enable_source(source_id)
                
        except Exception as e:
            logger.error(f"Error initializing sources: {e}", exc_info=True)
    
    async def start_ingestion_job(
        self,
        project_space_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new multi-source ingestion job
        
        Args:
            project_space_id: Target project space ID
            query: Search query
            sources: List of source IDs to search (None = all enabled)
            max_results_per_source: Max results per source
            filters: Additional filters
            options: Processing options
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        # Create job record
        job_info = {
            "job_id": job_id,
            "project_space_id": project_space_id,
            "query": query,
            "sources": sources or self._get_enabled_sources(),
            "max_results_per_source": max_results_per_source,
            "filters": filters or {},
            "options": options or {},
            "status": "pending",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "errors": []
        }
        
        self.active_jobs[job_id] = job_info
        
        # Start job asynchronously
        asyncio.create_task(self._run_ingestion_job(job_id))
        
        logger.info(f"Started ingestion job {job_id} for project {project_space_id}")
        return job_id
    
    async def _run_ingestion_job(self, job_id: str):
        """Run the actual ingestion job"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Update job status
            job_info["status"] = "running"
            job_info["started_at"] = datetime.now()
            
            logger.info(f"Running ingestion job {job_id}")
            
            # Search all sources
            search_result = await self.orchestrator.search_all_sources(
                query=job_info["query"],
                sources=job_info["sources"],
                max_results_per_source=job_info["max_results_per_source"],
                filters=job_info["filters"]
            )
            
            job_info["total_documents"] = len(search_result.documents)
            job_info["errors"].extend(search_result.errors)
            
            # Process each document
            for doc in search_result.documents:
                try:
                    # Set project space
                    doc.project_space_id = job_info["project_space_id"]
                    
                    # Process through existing pipeline
                    success = await self._process_external_document(doc, job_info["project_space_id"])
                    
                    if success:
                        job_info["processed_documents"] += 1
                    else:
                        job_info["failed_documents"] += 1
                        job_info["errors"].append({
                            "document_id": doc.id,
                            "error": "Failed to process document"
                        })
                    
                except Exception as e:
                    job_info["failed_documents"] += 1
                    job_info["errors"].append({
                        "document_id": doc.id,
                        "error": str(e)
                    })
                    logger.error(f"Failed to process document {doc.id}: {e}")
            
            # Mark job as completed
            job_info["status"] = "completed"
            job_info["completed_at"] = datetime.now()
            
            logger.info(
                f"Completed ingestion job {job_id}: "
                f"{job_info['processed_documents']}/{job_info['total_documents']} documents processed"
            )
            
        except Exception as e:
            job_info["status"] = "failed"
            job_info["completed_at"] = datetime.now()
            job_info["errors"].append({
                "error": str(e)
            })
            logger.error(f"Ingestion job {job_id} failed: {e}")
    
    async def _process_external_document(
        self,
        doc: StandardDocument,
        project_space_id: str
    ) -> bool:
        """
        Process external document through existing pipeline
        
        This method integrates with the existing document processing pipeline
        to ensure external documents are processed consistently with local documents.
        """
        try:
            # TODO: Integrate with existing DocumentProcessor
            # For now, we'll simulate the processing
            
            logger.info(f"Processing external document {doc.id} from {doc.source}")
            logger.info(f"Document title: {doc.title}")
            logger.info(f"Document content length: {len(doc.content or '')}")
            
            # 1. Store document metadata in database
            logger.info(f"About to store document metadata for {doc.id}")
            await self._store_document_metadata(doc, project_space_id)
            logger.info(f"Successfully stored document metadata for {doc.id}")
            
            # 2. Index in Elasticsearch
            await self._index_document(doc)
            
            # 3. Create knowledge graph entities
            if doc.entities:
                await self._create_knowledge_graph_entities(doc)
            
            # 4. Update processing status
            doc.processing_status = "completed"
            doc.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process external document {doc.id}: {e}")
            doc.processing_status = "failed"
            doc.processing_errors.append(str(e))
            return False
    
    async def _store_document_metadata(self, doc: StandardDocument, project_space_id: str):
        """Store document metadata in database"""
        try:
            # Use the same database pool as other services
            from services.project_spaces_service import ProjectSpacesService
            import os
            
            # Get database connection
            database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/dataplatform")
            import asyncpg
            
            logger.info(f"Creating database pool with URL: {database_url}")
            
            # Create a temporary pool for this operation
            pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=5,
                command_timeout=60
            )
            
            logger.info(f"Database pool created: {pool}")
            
            try:
                async with pool.acquire() as conn:
                # Insert document metadata
                await conn.execute(
                    """
                    INSERT INTO documents (
                        id, title, content, source, source_id, project_space_id,
                        document_type, language, publication_date, created_at, updated_at,
                        processing_status, quality_score, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        source = EXCLUDED.source,
                        source_id = EXCLUDED.source_id,
                        project_space_id = EXCLUDED.project_space_id,
                        document_type = EXCLUDED.document_type,
                        language = EXCLUDED.language,
                        publication_date = EXCLUDED.publication_date,
                        updated_at = EXCLUDED.updated_at,
                        processing_status = EXCLUDED.processing_status,
                        quality_score = EXCLUDED.quality_score,
                        metadata = EXCLUDED.metadata
                    """,
                    doc.id,
                    doc.title,
                    doc.content or "",
                    doc.source,
                    doc.source_id,
                    project_space_id,
                    doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                    doc.language or "en",
                    doc.publication_date,
                    doc.created_at,
                    doc.updated_at,
                    doc.processing_status,
                    doc.quality_score or 0.0,
                    json.dumps(doc.metadata) if doc.metadata else "{}"
                )
                
                # Insert authors
                for author in doc.authors:
                    await conn.execute(
                        """
                        INSERT INTO document_authors (document_id, name, affiliation, orcid, email, position)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (document_id, name) DO NOTHING
                        """,
                        doc.id,
                        author.name,
                        author.affiliation or "",
                        author.orcid or "",
                        author.email or "",
                        author.position or ""
                    )
                
                logger.info(f"Stored metadata for document {doc.id} in database")
            finally:
                await pool.close()
                
        except Exception as e:
            logger.error(f"Failed to store document metadata for {doc.id}: {e}")
            raise
    
    async def _index_document(self, doc: StandardDocument):
        """Index document in Elasticsearch"""
        try:
            import httpx
            
            # Prepare document for Elasticsearch
            es_doc = {
                "title": doc.title,
                "content": doc.content or "",
                "abstract": doc.abstract or "",
                "summary": doc.summary or "",
                "source": doc.source,
                "source_id": doc.source_id,
                "project_space_id": doc.project_space_id,
                "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                "language": doc.language,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "processing_status": doc.processing_status,
                "quality_score": doc.quality_score,
                "url": doc.url,
                "doi": doc.doi,
                "pmid": doc.pmid,
                "pmcid": doc.pmcid,
                "authors": [
                    {
                        "name": author.name,
                        "affiliation": author.affiliation,
                        "orcid": author.orcid,
                        "email": author.email,
                        "position": author.position
                    } for author in doc.authors
                ],
                "entities": {
                    entity_type: [
                        {
                            "value": entity.value,
                            "normalized_value": entity.normalized_value,
                            "entity_type": entity.entity_type,
                            "confidence": entity.confidence,
                            "start_pos": entity.start_pos,
                            "end_pos": entity.end_pos,
                            "context": entity.context,
                            "source": entity.source
                        } for entity in entities
                    ] for entity_type, entities in doc.entities.items()
                },
                "relationships": [
                    {
                        "subject": rel.subject,
                        "predicate": rel.predicate,
                        "object": rel.object,
                        "confidence": rel.confidence,
                        "context": rel.context,
                        "source": rel.source
                    } for rel in doc.relationships
                ],
                "key_concepts": doc.key_concepts,
                "tags": doc.tags,
                "metadata": doc.metadata,
                "version": doc.version,
                "is_deleted": doc.is_deleted
            }
            
            # Index in Elasticsearch
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"http://elasticsearch:9200/documents/_doc/{doc.id}",
                    json=es_doc,
                    timeout=30
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Elasticsearch indexing failed: {response.status_code} - {response.text}")
                
                logger.info(f"Indexed document {doc.id} in Elasticsearch")
                
        except Exception as e:
            logger.error(f"Failed to index document {doc.id} in Elasticsearch: {e}")
            raise
    
    async def _create_knowledge_graph_entities(self, doc: StandardDocument):
        """Create knowledge graph entities in Neo4j"""
        try:
            import httpx
            
            # Prepare entities and relationships for Neo4j
            entities_data = []
            relationships_data = []
            
            # Process entities
            for entity_type, entities in doc.entities.items():
                for entity in entities:
                    entities_data.append({
                        "id": f"{doc.id}_{entity.value}_{entity_type}",
                        "value": entity.value,
                        "normalized_value": entity.normalized_value,
                        "entity_type": entity.entity_type,
                        "confidence": entity.confidence,
                        "context": entity.context,
                        "source": entity.source,
                        "document_id": doc.id,
                        "document_title": doc.title
                    })
            
            # Process relationships
            for rel in doc.relationships:
                relationships_data.append({
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "confidence": rel.confidence,
                    "context": rel.context,
                    "source": rel.source,
                    "document_id": doc.id
                })
            
            # Create document node in Neo4j
            async with httpx.AsyncClient() as client:
                # Create document node
                doc_node = {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                    "created_at": doc.created_at.isoformat(),
                    "project_space_id": doc.project_space_id
                }
                
                # Send to Neo4j (using HTTP API for simplicity)
                neo4j_url = "http://neo4j:7474"
                auth = ("neo4j", "password")  # Default Neo4j credentials
                
                # Create document node
                doc_response = await client.post(
                    f"{neo4j_url}/db/data/transaction/commit",
                    json={
                        "statements": [{
                            "statement": """
                                MERGE (d:Document {id: $id})
                                SET d.title = $title,
                                    d.source = $source,
                                    d.document_type = $document_type,
                                    d.created_at = $created_at,
                                    d.project_space_id = $project_space_id
                                RETURN d
                            """,
                            "parameters": doc_node
                        }]
                    },
                    auth=auth,
                    timeout=30
                )
                
                if doc_response.status_code != 200:
                    logger.warning(f"Failed to create document node in Neo4j: {doc_response.status_code}")
                    return
                
                # Create entity nodes and relationships
                for entity in entities_data:
                    entity_response = await client.post(
                        f"{neo4j_url}/db/data/transaction/commit",
                        json={
                            "statements": [{
                                "statement": """
                                    MERGE (e:Entity {id: $id})
                                    SET e.value = $value,
                                        e.normalized_value = $normalized_value,
                                        e.entity_type = $entity_type,
                                        e.confidence = $confidence,
                                        e.context = $context,
                                        e.source = $source
                                    
                                    MERGE (d:Document {id: $document_id})
                                    MERGE (d)-[:CONTAINS {confidence: $confidence}]->(e)
                                """,
                                "parameters": entity
                            }]
                        },
                        auth=auth,
                        timeout=30
                    )
                    
                    if entity_response.status_code != 200:
                        logger.warning(f"Failed to create entity node in Neo4j: {entity_response.status_code}")
                
                # Create relationship nodes
                for rel in relationships_data:
                    rel_response = await client.post(
                        f"{neo4j_url}/db/data/transaction/commit",
                        json={
                            "statements": [{
                                "statement": """
                                    MERGE (s:Entity {value: $subject})
                                    MERGE (o:Entity {value: $object})
                                    MERGE (s)-[r:RELATES_TO {predicate: $predicate, confidence: $confidence, context: $context, source: $source}]->(o)
                                    
                                    MERGE (d:Document {id: $document_id})
                                    MERGE (d)-[:CONTAINS_RELATIONSHIP]->(r)
                                """,
                                "parameters": rel
                            }]
                        },
                        auth=auth,
                        timeout=30
                    )
                    
                    if rel_response.status_code != 200:
                        logger.warning(f"Failed to create relationship in Neo4j: {rel_response.status_code}")
                
                logger.info(f"Created knowledge graph entities for document {doc.id} in Neo4j")
                
        except Exception as e:
            logger.error(f"Failed to create knowledge graph entities for document {doc.id}: {e}")
            # Don't raise exception here as Neo4j is optional
            pass
    
    def _get_enabled_sources(self) -> List[str]:
        """Get list of enabled source IDs"""
        enabled_sources = []
        all_sources = self.registry.get_all_source_info()
        
        for source_info in all_sources:
            if source_info.is_enabled:
                enabled_sources.append(source_info.name)
        
        return enabled_sources
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an ingestion job"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return None
        
        # Calculate progress percentage
        if job_info["total_documents"] > 0:
            progress = (job_info["processed_documents"] + job_info["failed_documents"]) / job_info["total_documents"] * 100
        else:
            progress = 0
        
        return {
            "job_id": job_id,
            "status": job_info["status"],
            "progress": progress,
            "total_documents": job_info["total_documents"],
            "processed_documents": job_info["processed_documents"],
            "failed_documents": job_info["failed_documents"],
            "errors": job_info["errors"],
            "created_at": job_info["created_at"].isoformat(),
            "started_at": job_info["started_at"].isoformat() if job_info["started_at"] else None,
            "completed_at": job_info["completed_at"].isoformat() if job_info["completed_at"] else None
        }
    
    async def list_jobs(self, project_space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all ingestion jobs, optionally filtered by project space"""
        jobs = []
        
        for job_info in self.active_jobs.values():
            if project_space_id and job_info["project_space_id"] != project_space_id:
                continue
            
            # Calculate progress
            if job_info["total_documents"] > 0:
                progress = (job_info["processed_documents"] + job_info["failed_documents"]) / job_info["total_documents"] * 100
            else:
                progress = 0
            
            jobs.append({
                "job_id": job_info["job_id"],
                "project_space_id": job_info["project_space_id"],
                "query": job_info["query"],
                "sources": job_info["sources"],
                "status": job_info["status"],
                "progress": progress,
                "total_documents": job_info["total_documents"],
                "processed_documents": job_info["processed_documents"],
                "failed_documents": job_info["failed_documents"],
                "created_at": job_info["created_at"].isoformat(),
                "started_at": job_info["started_at"].isoformat() if job_info["started_at"] else None,
                "completed_at": job_info["completed_at"].isoformat() if job_info["completed_at"] else None
            })
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return jobs
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running ingestion job"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return False
        
        if job_info["status"] in ["completed", "failed"]:
            return False
        
        job_info["status"] = "cancelled"
        job_info["completed_at"] = datetime.now()
        
        logger.info(f"Cancelled ingestion job {job_id}")
        return True
