"""
PV Classification Integration Service
Coordinates PubMed ingestion, classification, and storage
"""

import httpx
import structlog
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

logger = structlog.get_logger()


class PVClassificationIntegrationService:
    """
    Integration service for PV classification workflow
    Coordinates: PubMed fetch → Elasticsearch → Classification → Neo4j
    """
    
    def __init__(self):
        self.pv_classification_url = "http://pv-classification-service:8012"
        self.elasticsearch_url = "http://elasticsearch:9200"
        self.neo4j_url = "bolt://neo4j:7687"
        
    async def ingest_and_classify(
        self,
        domain: str,
        max_articles: int,
        project_id: str = "icsr",
        user_id: str = None
    ) -> Dict:
        """
        Complete workflow: Fetch → Store → Classify → Extract Entities
        """
        logger.info(
            "Starting PV classification workflow",
            domain=domain,
            max_articles=max_articles,
            project_id=project_id
        )
        
        # Step 1: Fetch articles from PubMed
        articles = await self._fetch_pubmed_articles(domain, max_articles)
        logger.info("Fetched articles from PubMed", count=len(articles))
        
        if not articles:
            return {
                "articles_ingested": 0,
                "articles_classified": 0,
                "classifications": {}
            }
        
        # Step 2: Store articles in Elasticsearch
        stored_count = await self._store_in_elasticsearch(articles, project_id)
        logger.info("Stored articles in Elasticsearch", count=stored_count)
        
        # Step 3: Classify articles
        classifications = await self._classify_articles(articles)
        logger.info("Classified articles", count=len(classifications))
        
        # Step 4: Update Elasticsearch with classifications
        await self._update_classifications(articles, classifications)
        logger.info("Updated classifications in Elasticsearch")
        
        # Step 5: Extract entities to Neo4j
        await self._extract_entities_to_neo4j(articles, classifications, project_id)
        logger.info("Extracted entities to Neo4j")
        
        # Calculate statistics
        classification_counts = {}
        for classification in classifications:
            label = classification["classification"]["classification"]
            classification_counts[label] = classification_counts.get(label, 0) + 1
        
        return {
            "articles_ingested": stored_count,
            "articles_classified": len(classifications),
            "classifications": classification_counts
        }
    
    async def _fetch_pubmed_articles(self, domain: str, max_articles: int) -> List[Dict]:
        """
        Fetch articles from PubMed using targeted ingestion
        """
        try:
            from services.pubmed_ingestor import PubMedTargetedIngestor
            
            ingestor = PubMedTargetedIngestor()
            articles = await ingestor.fetch_articles(domain=domain, max_results=max_articles)
            
            return articles
            
        except Exception as e:
            logger.error("Failed to fetch PubMed articles", error=str(e), exc_info=True)
            return []
    
    async def _store_in_elasticsearch(self, articles: List[Dict], project_id: str) -> int:
        """
        Store articles in Elasticsearch with proper schema transformation
        """
        try:
            from elasticsearch import AsyncElasticsearch
            
            es_client = AsyncElasticsearch([self.elasticsearch_url])
            
            stored = 0
            for article in articles:
                # Transform PubMed article to match existing document schema
                document = {
                    # Core fields
                    "document_id": article.get("id", ""),
                    "filename": f"{article.get('pmid', 'unknown')}.txt",
                    "file_type": "pubmed_article",
                    "file_size": len(article.get("abstract", "") + article.get("title", "")),
                    "upload_date": article.get("ingested_at", datetime.utcnow().isoformat()),
                    
                    # Content fields
                    "title": article.get("title", ""),
                    "content": article.get("abstract", ""),
                    "abstract": article.get("abstract", ""),
                    
                    # Metadata - handle null values gracefully
                    "metadata": {
                        "pmid": article.get("pmid"),
                        "doi": article.get("doi") if article.get("doi") else None,
                        "journal": article.get("journal") if article.get("journal") else None,
                        "publication_date": article.get("publication_date"),
                        "url": article.get("url"),
                        "source": "pubmed",
                        "domain": article.get("domain"),
                        # Store authors as array of strings (not objects)
                        "authors": article.get("authors", []) if article.get("authors") else [],
                        # Store MeSH terms as array of strings
                        "mesh_terms": article.get("mesh_terms", []) if article.get("mesh_terms") else [],
                        # Store publication types as array of strings
                        "publication_types": article.get("publication_types", []) if article.get("publication_types") else [],
                        # Store keywords as array of strings
                        "keywords": article.get("keywords", []) if article.get("keywords") else []
                    },
                    
                    # Project and user info
                    "project_id": project_id,
                    "user_id": "system",
                    
                    # Classification fields (to be updated later)
                    "classification": None,
                    "classification_confidence": None,
                    "classification_reasoning": None,
                    "classification_entities": [],
                    "regulatory_elements": {},
                    "classified_at": None,
                    
                    # Processing status
                    "processing_status": "classified",
                    "extraction_method": "pubmed_api",
                    
                    # Timestamps
                    "created_at": article.get("ingested_at", datetime.utcnow().isoformat()),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Index document
                try:
                    await es_client.index(
                        index="documents",
                        id=article["id"],
                        document=document
                    )
                    stored += 1
                    logger.info("Stored article in Elasticsearch", article_id=article["id"], pmid=article.get("pmid"))
                except Exception as e:
                    logger.warning("Failed to store article", article_id=article["id"], error=str(e))
            
            await es_client.close()
            return stored
            
        except Exception as e:
            logger.error("Failed to store articles in Elasticsearch", error=str(e), exc_info=True)
            return 0
    
    async def _classify_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Classify articles using PV classification service
        """
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                # Prepare documents for classification
                documents = [
                    {
                        "id": article["id"],
                        "title": article["title"],
                        "abstract": article.get("abstract", ""),
                        "mesh_terms": article.get("mesh_terms", []),
                        "publication_types": article.get("publication_types", [])
                    }
                    for article in articles
                ]
                
                # Call batch classification endpoint
                # Use ensemble batch endpoint for 75% cost savings and 2.2x speed improvement
                response = await client.post(
                    f"{self.pv_classification_url}/api/v1/classify/ensemble/batch",
                    json={"documents": documents},
                    timeout=180.0
                )
                
                if response.status_code != 200:
                    logger.error("Classification service error", status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get("results", [])
                
        except Exception as e:
            logger.error("Failed to classify articles", error=str(e))
            return []
    
    async def _update_classifications(self, articles: List[Dict], classifications: List[Dict]):
        """
        Update Elasticsearch documents with classification results
        """
        try:
            from elasticsearch import AsyncElasticsearch
            
            es_client = AsyncElasticsearch([self.elasticsearch_url])
            
            # Create mapping of document_id to classification
            classification_map = {
                c["document_id"]: c["classification"]
                for c in classifications
            }
            
            # Update each document
            for article in articles:
                if article["id"] in classification_map:
                    classification = classification_map[article["id"]]
                    
                    update_doc = {
                        "classification": classification["classification"],
                        "classification_confidence": classification["confidence"],
                        "classification_reasoning": classification["reasoning"],
                        "classification_entities": [
                            {
                                "entity": e["entity"],
                                "type": e["type"],
                                "confidence": e["confidence"],
                                "relevance": e["relevance"]
                            }
                            for e in classification.get("key_entities", [])
                        ],
                        "regulatory_elements": classification.get("regulatory_elements", {}),
                        "classified_at": datetime.utcnow().isoformat()
                    }
                    
                    try:
                        await es_client.update(
                            index="documents",
                            id=article["id"],
                            doc=update_doc
                        )
                    except Exception as e:
                        logger.warning("Failed to update classification", article_id=article["id"], error=str(e))
            
            await es_client.close()
            
        except Exception as e:
            logger.error("Failed to update classifications", error=str(e))
    
    async def _extract_entities_to_neo4j(
        self,
        articles: List[Dict],
        classifications: List[Dict],
        project_id: str
    ):
        """
        Extract entities and relationships to Neo4j
        """
        try:
            from services.neo4j_service import Neo4jService
            
            neo4j_service = Neo4jService(
                uri=self.neo4j_url,
                user="neo4j",
                password="neo4jpassword"
            )
            
            # Create mapping
            classification_map = {
                c["document_id"]: c["classification"]
                for c in classifications
            }
            
            for article in articles:
                if article["id"] not in classification_map:
                    continue
                
                classification = classification_map[article["id"]]
                
                # Create document node
                await neo4j_service.execute_query(
                    """
                    MERGE (d:Document {id: $doc_id})
                    SET d.title = $title,
                        d.pmid = $pmid,
                        d.source = $source,
                        d.project_id = $project_id,
                        d.classification = $classification,
                        d.confidence = $confidence,
                        d.classified_at = $classified_at
                    """,
                    {
                        "doc_id": article["id"],
                        "title": article["title"],
                        "pmid": article.get("pmid", ""),
                        "source": "pubmed",
                        "project_id": project_id,
                        "classification": classification["classification"],
                        "confidence": classification["confidence"],
                        "classified_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Create entity nodes and relationships
                for entity in classification.get("key_entities", []):
                    await neo4j_service.execute_query(
                        """
                        MERGE (e:Entity {name: $entity_name, type: $entity_type})
                        SET e.updated_at = $updated_at
                        
                        WITH e
                        MATCH (d:Document {id: $doc_id})
                        MERGE (d)-[r:HAS_ENTITY]->(e)
                        SET r.confidence = $confidence,
                            r.relevance = $relevance,
                            r.classification_context = true
                        """,
                        {
                            "entity_name": entity["entity"],
                            "entity_type": entity["type"],
                            "updated_at": datetime.utcnow().isoformat(),
                            "doc_id": article["id"],
                            "confidence": entity["confidence"],
                            "relevance": entity["relevance"]
                        }
                    )
            
            logger.info("Entities extracted to Neo4j successfully")
            
        except Exception as e:
            logger.error("Failed to extract entities to Neo4j", error=str(e))

