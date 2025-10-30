"""
Unified Multi-Source Ingestion Service
Extends the existing PubMed system to support all external data sources
Uses Elasticsearch directly (like PubMed) instead of PostgreSQL
"""

import asyncio
import httpx
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from enum import Enum
from graph_db.integration_service import Neo4jIntegrationService

# Import existing data connectors
from data_connectors.sources.clinicaltrials_connector import ClinicalTrialsConnector
from data_connectors.sources.fda_connector import FDAConnector
from data_connectors.sources.semantic_scholar_connector import SemanticScholarConnector
from data_connectors.sources.europepmc_connector import EuropePMCConnector
from data_connectors.sources.chembl_connector import ChEMBLConnector

logger = structlog.get_logger(__name__)

class DocumentType(Enum):
    CLINICAL_TRIAL = "clinical_trial"
    DRUG_LABEL = "drug_label"
    ADVERSE_EVENT = "adverse_event"
    RESEARCH_PAPER = "research_paper"
    CHEMICAL_COMPOUND = "chemical_compound"
    PUBMED_ARTICLE = "pubmed_article"

@dataclass
class UnifiedDocument:
    """Unified document format for all external sources"""
    id: str
    title: str
    content: str
    source: str
    source_id: str
    document_type: DocumentType
    abstract: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    publication_date: Optional[datetime] = None
    authors: List[Dict[str, str]] = None
    keywords: List[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class IngestionJob:
    """Unified ingestion job for all sources"""
    job_id: str
    space_id: str
    query: str
    sources: List[str]
    status: str  # pending, processing, completed, failed
    total_documents: int = 0
    processed_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.errors is None:
            self.errors = []

class UnifiedIngestionService:
    """Unified service for ingesting data from all external sources"""
    
    def __init__(self):
        self.connectors = {
            'clinicaltrials': ClinicalTrialsConnector(),
            'fda': FDAConnector(),
            'semanticscholar': SemanticScholarConnector(),
            'europepmc': EuropePMCConnector(),
            'chembl': ChEMBLConnector()
        }
        self.jobs: Dict[str, IngestionJob] = {}
        self.elasticsearch_client = None
        self.neo4j_service = None
        self._init_elasticsearch()
        self._init_neo4j()
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client"""
        try:
            import httpx
            self.elasticsearch_client = httpx.AsyncClient(
                base_url="http://elasticsearch:9200",
                timeout=30.0
            )
            logger.info("Elasticsearch client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
    
    def _init_neo4j(self):
        """Initialize Neo4j integration service"""
        try:
            self.neo4j_service = Neo4jIntegrationService()
            logger.info("Neo4j integration service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
    
    async def start_ingestion(self, query: str, sources: List[str], 
                            max_results_per_source: int, space_id: str,
                            processing_options: Dict[str, Any]) -> str:
        """Start a new multi-source ingestion job"""
        try:
            job_id = str(uuid.uuid4())
            job = IngestionJob(
                job_id=job_id,
                space_id=space_id,
                query=query,
                sources=sources,
                status="pending"
            )
            
            self.jobs[job_id] = job
            
            # Start background processing
            asyncio.create_task(self._process_ingestion_job(job_id, processing_options))
            
            logger.info(f"Started ingestion job {job_id} for sources: {sources}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start ingestion job: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an ingestion job"""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": (job.processed_documents / job.total_documents * 100) if job.total_documents > 0 else 0,
            "total_documents": job.total_documents,
            "processed_documents": job.processed_documents,
            "successful_documents": job.successful_documents,
            "failed_documents": job.failed_documents,
            "errors": job.errors,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    
    async def _process_ingestion_job(self, job_id: str, processing_options: Dict[str, Any]):
        """Background task to process multi-source ingestion"""
        try:
            job = self.jobs[job_id]
            job.status = "processing"
            job.started_at = datetime.now()
            
            logger.info(f"Processing ingestion job {job_id} for query: {job.query}")
            
            all_documents = []
            
            # Fetch documents from each source
            for source_id in job.sources:
                if source_id not in self.connectors:
                    logger.warning(f"Unknown source: {source_id}")
                    continue
                
                try:
                    logger.info(f"Fetching documents from {source_id}")
                    connector = self.connectors[source_id]
                    
                    # Search for documents
                    documents = await connector.search(
                        query=job.query,
                        max_results=job.total_documents // len(job.sources) if job.total_documents > 0 else 10
                    )
                    
                    # Convert to unified format
                    for doc in documents:
                        unified_doc = self._convert_to_unified_document(doc, source_id)
                        all_documents.append(unified_doc)
                    
                    logger.info(f"Fetched {len(documents)} documents from {source_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch from {source_id}: {e}")
                    job.errors.append({
                        "source": source_id,
                        "error": str(e)
                    })
            
            job.total_documents = len(all_documents)
            logger.info(f"Total documents to process: {job.total_documents}")
            
            # Process each document
            for doc in all_documents:
                try:
                    await self._process_document(doc, job.space_id, processing_options)
                    job.successful_documents += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process document {doc.id}: {e}")
                    job.failed_documents += 1
                    job.errors.append({
                        "document_id": doc.id,
                        "error": str(e)
                    })
                
                job.processed_documents += 1
            
            job.status = "completed"
            job.completed_at = datetime.now()
            
            logger.info(f"Ingestion job {job_id} completed: {job.successful_documents} successful, {job.failed_documents} failed")
            
        except Exception as e:
            logger.error(f"Ingestion job {job_id} failed: {e}")
            job = self.jobs[job_id]
            job.status = "failed"
            job.completed_at = datetime.now()
            job.errors.append({
                "job_error": str(e)
            })
    
    def _convert_to_unified_document(self, doc, source_id: str) -> UnifiedDocument:
        """Convert source-specific document to unified format"""
        # Map source to document type
        type_mapping = {
            'clinicaltrials': DocumentType.CLINICAL_TRIAL,
            'fda': DocumentType.DRUG_LABEL,
            'semanticscholar': DocumentType.RESEARCH_PAPER,
            'europepmc': DocumentType.RESEARCH_PAPER,
            'chembl': DocumentType.CHEMICAL_COMPOUND
        }
        
        # Convert authors to serializable format
        authors = []
        if doc.authors:
            for author in doc.authors:
                if hasattr(author, 'name') and hasattr(author, 'affiliation'):
                    authors.append({
                        "name": author.name,
                        "affiliation": author.affiliation
                    })
                elif isinstance(author, dict):
                    authors.append(author)
                else:
                    # Fallback for string authors
                    authors.append({
                        "name": str(author),
                        "affiliation": ""
                    })
        
        return UnifiedDocument(
            id=doc.id,
            title=doc.title,
            content=doc.content or doc.abstract or "",
            abstract=doc.abstract,
            source=source_id,
            source_id=doc.source_id,
            document_type=type_mapping.get(source_id, DocumentType.RESEARCH_PAPER),
            url=doc.url,
            doi=doc.doi,
            pmid=doc.pmid,
            pmcid=doc.pmcid,
            publication_date=doc.publication_date,
            authors=authors,
            keywords=doc.key_concepts or doc.tags or [],
            metadata=doc.metadata or {}
        )
    
    async def _process_document(self, doc: UnifiedDocument, space_id: str, processing_options: Dict[str, Any]):
        """Process a single document and store in Elasticsearch"""
        try:
            logger.info(f"Processing document {doc.id} with options: {processing_options}")
            
            # If AI analysis is enabled, process through document processor first
            if processing_options.get("enable_ai_analysis", True):  # Default to True
                logger.info(f"Sending document {doc.id} to document processor for AI analysis")
                ai_result = await self._send_to_document_processor(doc, space_id, processing_options)
                
                if ai_result:
                    # Document processor has already indexed the document with AI results
                    logger.info(f"Document {doc.id} processed and indexed with AI analysis")
                    
                    # If ICSR Classification is enabled, classify the document
                    logger.info(f"🔍 DEBUG: enable_icsr_classification = {processing_options.get('enable_icsr_classification', False)}")
                    logger.info(f"🔍 DEBUG: processing_options = {processing_options}")
                    if processing_options.get("enable_icsr_classification", False):
                        logger.info(f"🎯 Running ICSR classification for document {doc.id}")
                        await self._classify_document_icsr(doc, space_id, ai_result, processing_options)
                    else:
                        logger.warning(f"⚠️ ICSR classification SKIPPED for {doc.id} - enable_icsr_classification is False")
                    
                    return
                else:
                    logger.warning(f"AI processing failed for document {doc.id}, indexing without AI analysis")
            else:
                logger.info(f"AI analysis disabled for document {doc.id}, indexing without AI analysis")
            
            # Fallback: Index document without AI analysis
            await self._index_document_basic(doc, space_id)
            
        except Exception as e:
            logger.error(f"Failed to process document {doc.id}: {e}")
            raise
    
    async def _index_document_with_ai(self, doc: UnifiedDocument, space_id: str, ai_results: Dict[str, Any]):
        """Index document in Elasticsearch WITH AI processing results"""
        try:
            # Clean null values from AI results
            entities = ai_results.get("entities")
            if entities is None:
                entities = []
            relationships = ai_results.get("relationships")
            if relationships is None:
                relationships = []
            key_concepts = ai_results.get("key_concepts")
            if key_concepts is None:
                key_concepts = []
            
            # DEBUG: Log the cleaned values
            logger.info(f"Cleaned AI results for {doc.id}: entities={type(entities)}, relationships={type(relationships)}, key_concepts={type(key_concepts)}")
            logger.info(f"Key concepts value: {key_concepts}")
            logger.info(f"Key concepts is None: {key_concepts is None}")
            logger.info(f"Key concepts == None: {key_concepts == None}")
            document_summary = ai_results.get("document_summary")
            if document_summary is None:
                document_summary = ""
            document_insights = ai_results.get("document_insights")
            if document_insights is None:
                document_insights = {}
            highlighted_content = ai_results.get("highlighted_content")
            if highlighted_content is None:
                highlighted_content = ""
            model_metadata = ai_results.get("model_metadata")
            if model_metadata is None:
                model_metadata = {}
            
            # DEBUG: Log before Elasticsearch indexing
            logger.info(f"About to index document {doc.id} with key_concepts: {key_concepts} (type: {type(key_concepts)})")
            
            # Create Elasticsearch document with AI results
            es_document = {
                "title": doc.title,
                "content": doc.content,
                "abstract": doc.abstract or "",
                "summary": doc.summary or "",
                "source": doc.source,
                "source_id": doc.source_id,
                "document_type": doc.document_type.value,
                "url": doc.url,
                "doi": doc.doi,
                "pmid": doc.pmid,
                "pmcid": doc.pmcid,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "authors": doc.authors,
                "keywords": doc.keywords,
                "metadata": doc.metadata,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "space_id": space_id,
                "external_source": True,
                # AI Processing Results
                "ai_processed": True,
                "extraction_method": "multi_source_ai_enhanced",
                "openai_entities": entities,
                "openai_relationships": relationships,
                "openai_key_concepts": key_concepts,
                "openai_summary": document_summary,
                "document_insights": document_insights,
                "highlighted_content": highlighted_content,
                "model_metadata": model_metadata,
                "multimodal": False,
                "has_images": False
            }
            
            # Index in Elasticsearch
            if self.elasticsearch_client:
                response = await self.elasticsearch_client.post(
                    f"/documents/_doc/{doc.id}",
                    json=es_document
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Document {doc.id} indexed with AI analysis: "
                               f"{len(ai_results.get('entities', []))} entities, "
                               f"{len(ai_results.get('relationships', []))} relationships")
                    
                    # Also sync to Neo4j knowledge graph
                    if self.neo4j_service:
                        try:
                            doc_metadata = {
                                "title": doc.title,
                                "source": doc.source,
                                "document_type": doc.document_type.value,
                                "url": doc.url,
                                "doi": doc.doi,
                                "pmid": doc.pmid,
                                "pmcid": doc.pmcid,
                                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                                "authors": doc.authors,
                                "space_id": space_id,
                                "external_source": True,
                                "ai_processed": True
                            }
                            
                            await self.neo4j_service.process_document_to_neo4j(
                                doc.id, ai_results, doc_metadata
                            )
                            logger.info(f"Document {doc.id} synced to Neo4j knowledge graph")
                        except Exception as e:
                            logger.warning(f"Failed to sync document {doc.id} to Neo4j: {e}")
                else:
                    raise Exception(f"Elasticsearch indexing failed: {response.status_code} - {response.text}")
            else:
                logger.warning("Elasticsearch client not available, skipping indexing")
                
        except Exception as e:
            logger.error(f"Failed to index document {doc.id} with AI results: {e}")
            raise
    
    async def _index_document_basic(self, doc: UnifiedDocument, space_id: str):
        """Index document in Elasticsearch without AI processing"""
        try:
            # Create Elasticsearch document
            es_document = {
                "title": doc.title,
                "content": doc.content,
                "abstract": doc.abstract or "",
                "summary": doc.summary or "",
                "source": doc.source,
                "source_id": doc.source_id,
                "document_type": doc.document_type.value,
                "url": doc.url,
                "doi": doc.doi,
                "pmid": doc.pmid,
                "pmcid": doc.pmcid,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "authors": doc.authors,
                "keywords": doc.keywords,
                "metadata": doc.metadata,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "space_id": space_id,
                "ai_processed": False,
                "multimodal": False,
                "has_images": False,
                "extraction_method": "multi_source_api",
                "external_source": True
            }
            
            # Index in Elasticsearch
            if self.elasticsearch_client:
                response = await self.elasticsearch_client.post(
                    f"/documents/_doc/{doc.id}",
                    json=es_document
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Document {doc.id} indexed successfully in Elasticsearch")
                else:
                    raise Exception(f"Elasticsearch indexing failed: {response.status_code} - {response.text}")
            else:
                logger.warning("Elasticsearch client not available, skipping indexing")
                
        except Exception as e:
            logger.error(f"Failed to index document {doc.id}: {e}")
            raise
    
    async def _send_to_document_processor(self, doc: UnifiedDocument, space_id: str, processing_options: Dict[str, Any]) -> bool:
        """Send document to document processor for AI analysis and return results"""
        try:
            # Prepare data for document processor
            processor_data = {
                "title": doc.title,
                "content": doc.content,
                "source": doc.source,
                "source_id": doc.source_id,
                "document_type": doc.document_type.value,
                "space_id": space_id,
                "model_name": processing_options.get("model_name", "phi3:mini"),
                "enable_entity_extraction": processing_options.get("enable_entity_extraction", True),
                "enable_relationship_extraction": processing_options.get("enable_relationship_extraction", True),
                # Pass additional document metadata
                "url": doc.url,
                "doi": doc.doi,
                "pmid": doc.pmid,
                "pmcid": doc.pmcid,
                "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
                "authors": doc.authors,
                "keywords": doc.keywords
            }
            
            # Send to document processor
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://document-processor:8001/process-external-document",
                    json=processor_data,
                    timeout=300.0
                )
                
                if response.status_code == 200:
                    ai_results = response.json()
                    
                    # DEBUG: Log what we received
                    logger.info(f"AI Results for {doc.id}: entities={type(ai_results.get('entities'))}, "
                               f"relationships={type(ai_results.get('relationships'))}, "
                               f"key_concepts={type(ai_results.get('key_concepts'))}, "
                               f"key_concepts_value={ai_results.get('key_concepts')}")
                    
                    logger.info(f"Document {doc.id} processed with AI: "
                               f"{len(ai_results.get('entities', []) or [])} entities, "
                               f"{len(ai_results.get('relationships', []) or [])} relationships")
                    
                    # Index document with AI results
                    await self._index_document_with_ai(doc, space_id, ai_results)
                    return True
                else:
                    logger.warning(f"Document processor returned {response.status_code} for document {doc.id}: {response.text}")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to send document {doc.id} to document processor: {e}")
            return False
    
    async def list_jobs(self, project_space_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all ingestion jobs, optionally filtered by project space"""
        try:
            if project_space_id:
                # Filter jobs by project space
                filtered_jobs = {
                    job_id: job for job_id, job in self.jobs.items() 
                    if job.space_id == project_space_id
                }
                return [self._job_to_dict(job) for job in filtered_jobs.values()]
            else:
                # Return all jobs
                return [self._job_to_dict(job) for job in self.jobs.values()]
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise

    def _job_to_dict(self, job: IngestionJob) -> Dict[str, Any]:
        """Convert IngestionJob to dictionary"""
        # Calculate progress percentage
        progress = 0.0
        if job.total_documents > 0:
            progress = (job.processed_documents / job.total_documents) * 100.0
        
        return {
            "job_id": job.job_id,
            "query": job.query,
            "sources": job.sources,
            "space_id": job.space_id,
            "status": job.status,
            "progress": progress,
            "total_documents": job.total_documents,
            "processed_documents": job.processed_documents,
            "successful_documents": job.successful_documents,
            "failed_documents": job.failed_documents,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "errors": job.errors
        }
    
    async def _classify_document_icsr(self, doc: UnifiedDocument, space_id: str, ai_results: Dict[str, Any], processing_options: Dict = None):
        """Classify document using PV Classification Service"""
        if processing_options is None:
            processing_options = {}
        try:
            import httpx
            
            # Prepare document content for classification
            content = ""
            if doc.abstract:
                content += f"Abstract: {doc.abstract}\n\n"
            if doc.content:
                content += f"Content: {doc.content}\n\n"
            if doc.summary:
                content += f"Summary: {doc.summary}\n\n"
            
            # If no content available, use title
            if not content.strip():
                content = doc.title or "No content available"
            
            # Prepare classification request in the correct format
            classification_request = {
                "document": {
                    "id": doc.id,
                    "title": doc.title or "",
                    "abstract": content  # Use the prepared content as abstract
                },
                "force_ensemble": processing_options.get('force_ensemble', False)
            }
            
            # Add LLM model selection if specified
            model_name = processing_options.get('model_name', '')
            if model_name:
                # Map UI model names to LLM provider/model format
                if 'gpt' in model_name.lower() or 'openai' in model_name.lower():
                    classification_request['llm'] = {
                        "provider": "openai",
                        "model": model_name
                    }
                elif 'llama' in model_name.lower():
                    classification_request['llm'] = {
                        "provider": "ollama",
                        "model": "llama3.1:8b"
                    }
                elif 'phi' in model_name.lower():
                    classification_request['llm'] = {
                        "provider": "ollama",
                        "model": "phi3:mini"
                    }
            
            # Debug logging
            logger.info(f"🔍 DEBUG (unified): Sending classification for {doc.id}, force_ensemble={classification_request['force_ensemble']}, model={model_name}, llm={classification_request.get('llm', 'default')}")
            
            # Call PV Classification Service using ensemble endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://pv-classification-service:8002/api/v1/classify/ensemble",
                    json=classification_request,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    # Extract the nested classification object for logging
                    classification_result = response_data.get("classification", {})
                    logger.info(f"✅ ICSR classification completed for {doc.id}: {classification_result.get('classification')} ({classification_result.get('confidence', 0):.2%})")
                    
                    # Update Elasticsearch with FULL classification results (including ensemble_metadata)
                    await self._update_document_classification(doc.id, response_data, space_id)
                    
                else:
                    logger.warning(f"ICSR classification failed for {doc.id}: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Failed to classify document {doc.id} for ICSR: {e}")
            # Don't raise - classification failure shouldn't stop ingestion
    
    async def _update_document_classification(self, doc_id: str, classification_result: Dict[str, Any], space_id: str):
        """Update document in Elasticsearch with classification results"""
        try:
            import httpx
            
            # Extract classification and ensemble metadata from response
            cls_block = classification_result.get("classification", {})
            meta = classification_result.get("ensemble_metadata", {})
            
            classification_label = cls_block.get("classification", "")
            classification_conf = cls_block.get("confidence", 0.0)
            classification_reason = cls_block.get("reasoning", "")
            classification_entities = cls_block.get("key_entities", [])
            
            models_used = meta.get("models_used", [])
            proc_time = meta.get("processing_time_ms", 0)
            cost = meta.get("cost_estimate", 0.0)
            decision_path = meta.get("decision_path", "")
            individual_results = meta.get("individual_results", {})
            
            update_payload = {
                "doc": {
                    "classification": classification_label,
                    "classification_confidence": classification_conf,
                    "classification_entities": classification_entities,
                    "classification_reasoning": classification_reason,
                    "classified_at": datetime.utcnow().isoformat(),
                    "classification_model": classification_result.get("model", "pv-ensemble"),
                    "ensemble_models_used": models_used,
                    "decision_path": decision_path,
                    "processing_time_ms": proc_time,
                    "classification_cost": cost,
                    "individual_results": individual_results,
                    "processing_status": "classified",
                    "ai_processed": True,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Update document in Elasticsearch
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://elasticsearch:9200/documents/_update/{doc_id}",
                    json=update_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Updated document {doc_id} with classification: {classification_result.get('classification')} ({classification_result.get('confidence', 0):.2%})")
                else:
                    logger.warning(f"❌ Failed to update document {doc_id} with classification: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} with classification: {e}")

# Global service instance
unified_ingestion_service = UnifiedIngestionService()
