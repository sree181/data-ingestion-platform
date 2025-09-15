"""
Elasticsearch service for document storage and search
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError

from models.api_models import SearchResponse, SearchHit, SearchFacet, DocumentStats

logger = structlog.get_logger(__name__)


class ElasticsearchService:
    """Service for interacting with Elasticsearch"""
    
    def __init__(self, elasticsearch_url: str, index_prefix: str = "dataplatform"):
        self.elasticsearch_url = elasticsearch_url
        self.index_prefix = index_prefix
        self.client: Optional[AsyncElasticsearch] = None
        
        # Index configurations
        self.indices = {
            "documents": f"{index_prefix}_documents",
            "entities": f"{index_prefix}_entities",
            "logs": f"{index_prefix}_logs"
        }
    
    async def connect(self):
        """Initialize Elasticsearch connection"""
        try:
            self.client = AsyncElasticsearch([self.elasticsearch_url])
            
            # Test connection
            await self.client.ping()
            
            # Create indices if they don't exist
            await self._create_indices()
            
            logger.info("Connected to Elasticsearch", url=self.elasticsearch_url)
            
        except Exception as e:
            logger.error("Failed to connect to Elasticsearch", error=str(e))
            raise
    
    async def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        try:
            health = await self.client.cluster.health()
            return {
                "status": health["status"],
                "number_of_nodes": health["number_of_nodes"],
                "active_primary_shards": health["active_primary_shards"]
            }
        except Exception as e:
            logger.error("Elasticsearch health check failed", error=str(e))
            raise
    
    async def _create_indices(self):
        """Create Elasticsearch indices with proper mappings"""
        
        # Documents index mapping
        documents_mapping = {
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "metadata": {
                        "properties": {
                            "filename": {"type": "keyword"},
                            "file_type": {"type": "keyword"},
                            "file_size": {"type": "long"},
                            "upload_date": {"type": "date"},
                            "user_id": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "page_count": {"type": "integer"}
                        }
                    },
                    "extracted_entities": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "keyword"},
                            "type": {"type": "keyword"},
                            "confidence": {"type": "float"},
                            "start_char": {"type": "integer"},
                            "end_char": {"type": "integer"}
                        }
                    },
                    "tags": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "processing_status": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 768  # For sentence transformers
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "custom_text_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "snowball"]
                        }
                    }
                }
            }
        }
        
        # Entities index mapping
        entities_mapping = {
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "type": {"type": "keyword"},
                    "properties": {"type": "object"},
                    "document_ids": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "frequency": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        # Create indices
        for index_name, mapping in [
            (self.indices["documents"], documents_mapping),
            (self.indices["entities"], entities_mapping)
        ]:
            try:
                exists = await self.client.indices.exists(index=index_name)
                if not exists:
                    await self.client.indices.create(index=index_name, body=mapping)
                    logger.info("Created Elasticsearch index", index=index_name)
            except Exception as e:
                logger.error("Failed to create index", index=index_name, error=str(e))
                raise
    
    async def search(
        self,
        query: str,
        filters: Optional[List[Dict]] = None,
        size: int = 20,
        offset: int = 0,
        sort: Optional[List[Dict]] = None,
        highlight: bool = True,
        index: str = None
    ) -> SearchResponse:
        """Advanced document search with filters and facets"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        index_name = index or self.indices["documents"]
        
        # Build query
        search_body = {
            "query": self._build_query(query, filters),
            "size": size,
            "from": offset,
            "track_total_hits": True
        }
        
        # Add sorting
        if sort:
            search_body["sort"] = sort
        else:
            search_body["sort"] = [{"_score": {"order": "desc"}}]
        
        # Add highlighting
        if highlight:
            search_body["highlight"] = {
                "fields": {
                    "title": {"number_of_fragments": 1},
                    "content": {"number_of_fragments": 3, "fragment_size": 150}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        
        # Add aggregations for facets
        search_body["aggs"] = {
            "file_types": {
                "terms": {"field": "metadata.file_type", "size": 10}
            },
            "categories": {
                "terms": {"field": "categories", "size": 20}
            },
            "upload_dates": {
                "date_histogram": {
                    "field": "metadata.upload_date",
                    "calendar_interval": "month"
                }
            },
            "entities": {
                "nested": {"path": "extracted_entities"},
                "aggs": {
                    "entity_types": {
                        "terms": {"field": "extracted_entities.type", "size": 10}
                    }
                }
            }
        }
        
        try:
            start_time = datetime.now()
            
            response = await self.client.search(
                index=index_name,
                body=search_body
            )
            
            took = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Process results
            hits = []
            for hit in response["hits"]["hits"]:
                search_hit = SearchHit(
                    id=hit["_id"],
                    score=hit["_score"],
                    source=hit["_source"],
                    highlight=hit.get("highlight")
                )
                hits.append(search_hit)
            
            # Process facets
            facets = []
            if "aggregations" in response:
                aggs = response["aggregations"]
                
                # File types facet
                if "file_types" in aggs:
                    facets.append(SearchFacet(
                        field="file_type",
                        buckets=aggs["file_types"]["buckets"]
                    ))
                
                # Categories facet
                if "categories" in aggs:
                    facets.append(SearchFacet(
                        field="categories",
                        buckets=aggs["categories"]["buckets"]
                    ))
                
                # Entity types facet
                if "entities" in aggs and "entity_types" in aggs["entities"]:
                    facets.append(SearchFacet(
                        field="entity_types",
                        buckets=aggs["entities"]["entity_types"]["buckets"]
                    ))
            
            return SearchResponse(
                total=response["hits"]["total"]["value"],
                hits=hits,
                facets=facets,
                took=took,
                query=query
            )
            
        except Exception as e:
            logger.error("Search failed", error=str(e), query=query)
            raise
    
    def _build_query(self, query: str, filters: Optional[List[Dict]] = None) -> Dict:
        """Build Elasticsearch query with filters"""
        
        # Base query
        if query.strip():
            base_query = {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "content^1",
                        "metadata.filename^2",
                        "extracted_entities.name^2"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            }
        else:
            base_query = {"match_all": {}}
        
        # Apply filters
        if filters:
            filter_clauses = []
            
            for filter_item in filters:
                field = filter_item["field"]
                value = filter_item["value"]
                operator = filter_item.get("operator", "equals")
                
                if operator == "equals":
                    if isinstance(value, list):
                        filter_clauses.append({"terms": {field: value}})
                    else:
                        filter_clauses.append({"term": {field: value}})
                elif operator == "contains":
                    filter_clauses.append({"wildcard": {field: f"*{value}*"}})
                elif operator == "range":
                    filter_clauses.append({"range": {field: value}})
            
            if filter_clauses:
                return {
                    "bool": {
                        "must": [base_query],
                        "filter": filter_clauses
                    }
                }
        
        return base_query
    
    async def index_document(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        index: str = None
    ) -> bool:
        """Index a document in Elasticsearch"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        index_name = index or self.indices["documents"]
        
        try:
            # Add timestamps
            document_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            await self.client.index(
                index=index_name,
                id=document_id,
                body=document_data
            )
            
            logger.info("Document indexed", document_id=document_id, index=index_name)
            return True
            
        except Exception as e:
            logger.error("Failed to index document", document_id=document_id, error=str(e))
            raise
    
    async def get_document(self, document_id: str, index: str = None) -> Optional[Dict]:
        """Get a document by ID"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        index_name = index or self.indices["documents"]
        
        try:
            response = await self.client.get(index=index_name, id=document_id)
            return response["_source"]
            
        except NotFoundError:
            return None
        except Exception as e:
            logger.error("Failed to get document", document_id=document_id, error=str(e))
            raise
    
    async def delete_document(self, document_id: str, index: str = None) -> bool:
        """Delete a document by ID"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        index_name = index or self.indices["documents"]
        
        try:
            await self.client.delete(index=index_name, id=document_id)
            logger.info("Document deleted", document_id=document_id)
            return True
            
        except NotFoundError:
            return False
        except Exception as e:
            logger.error("Failed to delete document", document_id=document_id, error=str(e))
            raise
    
    async def get_stats(self) -> DocumentStats:
        """Get document statistics"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        try:
            # Get index stats
            stats = await self.client.indices.stats(index=self.indices["documents"])
            index_stats = stats["indices"][self.indices["documents"]]
            
            total_docs = index_stats["total"]["docs"]["count"]
            total_size = index_stats["total"]["store"]["size_in_bytes"]
            
            # Get aggregations for document types
            agg_response = await self.client.search(
                index=self.indices["documents"],
                body={
                    "size": 0,
                    "aggs": {
                        "file_types": {
                            "terms": {"field": "metadata.file_type", "size": 20}
                        },
                        "recent_uploads": {
                            "filter": {
                                "range": {
                                    "metadata.upload_date": {
                                        "gte": "now-7d"
                                    }
                                }
                            }
                        }
                    }
                }
            )
            
            # Process file types
            file_types = {}
            if "file_types" in agg_response["aggregations"]:
                for bucket in agg_response["aggregations"]["file_types"]["buckets"]:
                    file_types[bucket["key"]] = bucket["doc_count"]
            
            recent_uploads = agg_response["aggregations"]["recent_uploads"]["doc_count"]
            
            return DocumentStats(
                total_documents=total_docs,
                total_size_bytes=total_size,
                documents_by_type=file_types,
                recent_uploads=recent_uploads
            )
            
        except Exception as e:
            logger.error("Failed to get document stats", error=str(e))
            raise
    
    async def suggest(self, text: str, field: str = "title", size: int = 5) -> List[str]:
        """Get search suggestions"""
        
        if not self.client:
            raise Exception("Elasticsearch client not initialized")
        
        try:
            response = await self.client.search(
                index=self.indices["documents"],
                body={
                    "suggest": {
                        "text_suggest": {
                            "prefix": text,
                            "completion": {
                                "field": f"{field}.suggest",
                                "size": size,
                                "skip_duplicates": True
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for option in response["suggest"]["text_suggest"][0]["options"]:
                suggestions.append(option["text"])
            
            return suggestions
            
        except Exception as e:
            logger.error("Failed to get suggestions", error=str(e))
            return []