"""
PubMed Integration Service
Handles PubMed/NCBI data ingestion and medical concept extraction
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import uuid
import xml.etree.ElementTree as ET
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PubMed Integration Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PubMed E-utilities API configuration
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
ESEARCH_URL = f"{PUBMED_BASE_URL}esearch.fcgi"
EFETCH_URL = f"{PUBMED_BASE_URL}efetch.fcgi"
ELINK_URL = f"{PUBMED_BASE_URL}elink.fcgi"

# Pydantic models
class PubMedSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for PubMed")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    date_range: Optional[str] = Field(None, description="Date range filter (e.g., '2020:2024')")
    article_types: Optional[List[str]] = Field(None, description="Article types to filter")
    space_id: str = Field(..., description="Project space ID for ingestion")

class PubMedArticle(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str] = None
    authors: List[str] = []
    journal: str
    publication_date: str
    mesh_terms: List[str] = []
    keywords: List[str] = []
    doi: Optional[str] = None
    pmc_id: Optional[str] = None
    article_types: List[str] = []

class MedicalConcept(BaseModel):
    concept_id: str
    name: str
    concept_type: str  # DISEASE, DRUG, GENE, SYMPTOM, TREATMENT, etc.
    confidence: float
    mesh_id: Optional[str] = None
    synonyms: List[str] = []
    related_concepts: List[str] = []

class PubMedIngestionJob(BaseModel):
    job_id: str
    space_id: str
    query: str
    status: str  # pending, processing, completed, failed
    total_articles: int
    processed_articles: int
    successful_articles: int
    failed_articles: int
    created_at: datetime
    updated_at: datetime
    medical_concepts: List[MedicalConcept] = []

# In-memory storage for jobs (in production, use Redis or database)
ingestion_jobs: Dict[str, PubMedIngestionJob] = {}

class PubMedService:
    """Service for interacting with PubMed API"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def search_articles(self, query: str, max_results: int = 100, 
                            date_range: Optional[str] = None, 
                            article_types: Optional[List[str]] = None) -> List[str]:
        """Search PubMed for articles and return PMIDs"""
        try:
            # Build search parameters
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": min(max_results, 10000),  # PubMed limit
                "retmode": "json",
                "sort": "relevance"
            }
            
            # Add date range filter
            if date_range:
                params["term"] = f"{query} AND {date_range}[dp]"
            
            # Add article type filters
            if article_types:
                type_filter = " OR ".join([f'"{at}"[pt]' for at in article_types])
                params["term"] = f"{params['term']} AND ({type_filter})"
            
            logger.info(f"Searching PubMed with query: {params['term']}")
            
            response = await self.session.get(ESEARCH_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            logger.info(f"Found {len(pmids)} articles for query: {query}")
            return pmids
            
        except Exception as e:
            logger.error(f"PubMed search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PubMed search failed: {str(e)}")
    
    async def fetch_article_details(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch detailed article information from PubMed"""
        try:
            if not pmids:
                return []
            
            # PubMed API has a limit of 200 PMIDs per request
            articles = []
            batch_size = 200
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                
                params = {
                    "db": "pubmed",
                    "id": ",".join(batch_pmids),
                    "retmode": "xml",
                    "rettype": "abstract"
                }
                
                response = await self.session.get(EFETCH_URL, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.text)
                batch_articles = self._parse_pubmed_xml(root)
                articles.extend(batch_articles)
                
                # Rate limiting - PubMed allows 3 requests per second
                await asyncio.sleep(0.4)
            
            logger.info(f"Fetched details for {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch article details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch article details: {str(e)}")
    
    def _parse_pubmed_xml(self, root: ET.Element) -> List[PubMedArticle]:
        """Parse PubMed XML response into article objects"""
        articles = []
        
        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract PMID
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "unknown"
                
                # Extract title
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title"
                
                # Extract abstract
                abstract_elem = article.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else None
                
                # Extract authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find("LastName")
                    first_name = author.find("ForeName")
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name = f"{first_name.text} {name}"
                        authors.append(name)
                
                # Extract journal
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                
                # Extract publication date
                pub_date = article.find(".//PubDate")
                publication_date = self._extract_publication_date(pub_date)
                
                # Extract MeSH terms
                mesh_terms = []
                for mesh in article.findall(".//MeshHeading/DescriptorName"):
                    if mesh.text:
                        mesh_terms.append(mesh.text)
                
                # Extract keywords
                keywords = []
                for kw in article.findall(".//Keyword"):
                    if kw.text:
                        keywords.append(kw.text)
                
                # Extract DOI
                doi = None
                for article_id in article.findall(".//ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break
                
                # Extract PMC ID
                pmc_id = None
                for article_id in article.findall(".//ArticleId"):
                    if article_id.get("IdType") == "pmc":
                        pmc_id = article_id.text
                        break
                
                # Extract article types
                article_types = []
                for pub_type in article.findall(".//PublicationType"):
                    if pub_type.text:
                        article_types.append(pub_type.text)
                
                article_obj = PubMedArticle(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    journal=journal,
                    publication_date=publication_date,
                    mesh_terms=mesh_terms,
                    keywords=keywords,
                    doi=doi,
                    pmc_id=pmc_id,
                    article_types=article_types
                )
                
                articles.append(article_obj)
                
            except Exception as e:
                logger.warning(f"Failed to parse article: {str(e)}")
                continue
        
        return articles
    
    def _extract_publication_date(self, pub_date_elem) -> str:
        """Extract publication date from PubMed XML"""
        if pub_date_elem is None:
            return datetime.now().strftime("%Y-%m-%d")
        
        year_elem = pub_date_elem.find("Year")
        month_elem = pub_date_elem.find("Month")
        day_elem = pub_date_elem.find("Day")
        
        year = year_elem.text if year_elem is not None else "2024"
        month = month_elem.text if month_elem is not None else "01"
        day = day_elem.text if day_elem is not None else "01"
        
        # Handle month names
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
        
        if month in month_map:
            month = month_map[month]
        
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

class MedicalConceptExtractor:
    """Extract medical concepts from PubMed articles"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def extract_concepts(self, article: PubMedArticle) -> List[MedicalConcept]:
        """Extract medical concepts from article using OpenAI"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not found, using basic extraction")
                return self._basic_concept_extraction(article)
            
            # Prepare text for analysis
            text_parts = [article.title]
            if article.abstract:
                text_parts.append(article.abstract)
            
            text = " ".join(text_parts)
            
            # Call OpenAI for concept extraction
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": """Extract medical concepts from the given text. Return a JSON array of concepts with the following structure:
                                {
                                    "concept_id": "unique_id",
                                    "name": "concept_name",
                                    "concept_type": "DISEASE|DRUG|GENE|SYMPTOM|TREATMENT|PROCEDURE|ANATOMY",
                                    "confidence": 0.0-1.0,
                                    "mesh_id": "MeSH ID if available",
                                    "synonyms": ["synonym1", "synonym2"],
                                    "related_concepts": ["related1", "related2"]
                                }
                                
                                Focus on medical entities, diseases, drugs, genes, symptoms, treatments, and procedures."""
                            },
                            {
                                "role": "user",
                                "content": f"Extract medical concepts from this text:\n\n{text}"
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Parse JSON response
                    concepts_data = json.loads(content)
                    concepts = []
                    
                    for concept_data in concepts_data:
                        concept = MedicalConcept(
                            concept_id=concept_data.get("concept_id", str(uuid.uuid4())),
                            name=concept_data.get("name", ""),
                            concept_type=concept_data.get("concept_type", "UNKNOWN"),
                            confidence=concept_data.get("confidence", 0.5),
                            mesh_id=concept_data.get("mesh_id"),
                            synonyms=concept_data.get("synonyms", []),
                            related_concepts=concept_data.get("related_concepts", [])
                        )
                        concepts.append(concept)
                    
                    return concepts
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return self._basic_concept_extraction(article)
                    
        except Exception as e:
            logger.error(f"Concept extraction failed: {str(e)}")
            return self._basic_concept_extraction(article)
    
    def _basic_concept_extraction(self, article: PubMedArticle) -> List[MedicalConcept]:
        """Basic concept extraction using MeSH terms and keywords"""
        concepts = []
        
        # Extract from MeSH terms
        for mesh_term in article.mesh_terms:
            concept = MedicalConcept(
                concept_id=str(uuid.uuid4()),
                name=mesh_term,
                concept_type="DISEASE",  # Default type
                confidence=0.8,
                synonyms=[]
            )
            concepts.append(concept)
        
        # Extract from keywords
        for keyword in article.keywords:
            concept = MedicalConcept(
                concept_id=str(uuid.uuid4()),
                name=keyword,
                concept_type="UNKNOWN",
                confidence=0.6,
                synonyms=[]
            )
            concepts.append(concept)
        
        return concepts

# Initialize services
pubmed_service = PubMedService()
concept_extractor = MedicalConceptExtractor()

# API Endpoints
@app.post("/api/v1/pubmed/search")
async def search_pubmed(request: PubMedSearchRequest):
    """Search PubMed and start ingestion process"""
    try:
        # Create ingestion job
        job_id = str(uuid.uuid4())
        job = PubMedIngestionJob(
            job_id=job_id,
            space_id=request.space_id,
            query=request.query,
            status="pending",
            total_articles=0,
            processed_articles=0,
            successful_articles=0,
            failed_articles=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        ingestion_jobs[job_id] = job
        
        # Start background processing
        asyncio.create_task(process_pubmed_ingestion(job_id, request))
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "PubMed search and ingestion started"
        }
        
    except Exception as e:
        logger.error(f"PubMed search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PubMed search failed: {str(e)}")

@app.get("/api/v1/pubmed/jobs/{job_id}")
async def get_ingestion_status(job_id: str):
    """Get status of PubMed ingestion job"""
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ingestion_jobs[job_id]

@app.get("/api/v1/pubmed/jobs")
async def list_ingestion_jobs(space_id: Optional[str] = None):
    """List all ingestion jobs, optionally filtered by space_id"""
    jobs = list(ingestion_jobs.values())
    
    if space_id:
        jobs = [job for job in jobs if job.space_id == space_id]
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }

async def process_pubmed_ingestion(job_id: str, request: PubMedSearchRequest):
    """Background task to process PubMed ingestion"""
    try:
        job = ingestion_jobs[job_id]
        job.status = "processing"
        job.updated_at = datetime.utcnow()
        
        # Search PubMed
        pmids = await pubmed_service.search_articles(
            query=request.query,
            max_results=request.max_results,
            date_range=request.date_range,
            article_types=request.article_types
        )
        
        job.total_articles = len(pmids)
        job.updated_at = datetime.utcnow()
        
        if not pmids:
            job.status = "completed"
            job.updated_at = datetime.utcnow()
            return
        
        # Fetch article details
        articles = await pubmed_service.fetch_article_details(pmids)
        
        # Process each article
        for article in articles:
            try:
                # Extract medical concepts
                concepts = await concept_extractor.extract_concepts(article)
                job.medical_concepts.extend(concepts)
                
                # Send to document processor
                await send_to_document_processor(article, concepts, request.space_id)
                
                job.successful_articles += 1
                
            except Exception as e:
                logger.error(f"Failed to process article {article.pmid}: {str(e)}")
                job.failed_articles += 1
            
            job.processed_articles += 1
            job.updated_at = datetime.utcnow()
        
        job.status = "completed"
        job.updated_at = datetime.utcnow()
        
        logger.info(f"PubMed ingestion completed: {job.successful_articles} successful, {job.failed_articles} failed")
        
    except Exception as e:
        logger.error(f"PubMed ingestion failed: {str(e)}")
        job = ingestion_jobs[job_id]
        job.status = "failed"
        job.updated_at = datetime.utcnow()

async def send_to_document_processor(article: PubMedArticle, concepts: List[MedicalConcept], space_id: str):
    """Send processed article to document processor"""
    try:
        # Prepare document content
        content_parts = [f"Title: {article.title}"]
        
        if article.abstract:
            content_parts.append(f"Abstract: {article.abstract}")
        
        content_parts.append(f"Journal: {article.journal}")
        content_parts.append(f"Authors: {', '.join(article.authors)}")
        content_parts.append(f"Publication Date: {article.publication_date}")
        
        if article.doi:
            content_parts.append(f"DOI: {article.doi}")
        
        content = "\n\n".join(content_parts)
        
        # Prepare medical concepts for processing
        medical_entities = []
        for concept in concepts:
            medical_entities.append({
                "text": concept.name,
                "type": concept.concept_type,
                "confidence": concept.confidence,
                "mesh_id": concept.mesh_id,
                "synonyms": concept.synonyms,
                "related_concepts": concept.related_concepts
            })
        
        # Send to document processor
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://document-processor:8001/process-pubmed-article",
                json={
                    "title": f"PubMed: {article.title}",
                    "content": content,
                    "metadata": {
                        "pmid": article.pmid,
                        "journal": article.journal,
                        "authors": article.authors,
                        "publication_date": article.publication_date,
                        "doi": article.doi,
                        "pmc_id": article.pmc_id,
                        "article_types": article.article_types,
                        "mesh_terms": article.mesh_terms,
                        "keywords": article.keywords,
                        "source": "pubmed"
                    },
                    "medical_entities": medical_entities,
                    "space_id": space_id
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Document processor error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to send to document processor: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pubmed-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
