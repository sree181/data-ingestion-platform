"""
Literature Search Service
Handles literature search from multiple sources (PubMed, Embase, Cochrane)
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
import structlog
from pymed import PubMed
from datetime import datetime, timedelta
import json

from models.literature_models import (
    LiteratureSearchRequest,
    LiteratureArticle,
    LiteratureSource
)

logger = structlog.get_logger()

class LiteratureSearchService:
    def __init__(self):
        self.pubmed = PubMed(tool="LiteratureAutomation", email="admin@example.com")
        self.embase_api_key = None  # Will be configured via environment
        self.cochrane_api_key = None  # Will be configured via environment
        
    async def search_literature(
        self, 
        query: str, 
        sources: List[LiteratureSource], 
        max_results: int = 100,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[LiteratureArticle]:
        """
        Search literature from multiple sources
        """
        logger.info("Starting literature search", query=query, sources=sources, max_results=max_results)
        
        all_results = []
        
        # Search each source
        for source in sources:
            try:
                if source == LiteratureSource.PUBMED:
                    results = await self._search_pubmed(query, max_results, date_range)
                elif source == LiteratureSource.EMBASE:
                    results = await self._search_embase(query, max_results, date_range)
                elif source == LiteratureSource.COHRANE:
                    results = await self._search_cochrane(query, max_results, date_range)
                else:
                    logger.warning("Unknown literature source", source=source)
                    continue
                
                all_results.extend(results)
                logger.info("Source search completed", source=source, results_count=len(results))
                
            except Exception as e:
                logger.error("Source search failed", source=source, error=str(e))
                continue
        
        # Remove duplicates and limit results
        unique_results = self._deduplicate_results(all_results)
        final_results = unique_results[:max_results]
        
        logger.info("Literature search completed", total_results=len(final_results))
        return final_results
    
    async def _search_pubmed(self, query: str, max_results: int, date_range: Optional[Dict[str, str]]) -> List[LiteratureArticle]:
        """Search PubMed database"""
        try:
            # Build PubMed query
            pubmed_query = query
            if date_range:
                from_date = date_range.get('from_date', '')
                to_date = date_range.get('to_date', '')
                if from_date and to_date:
                    pubmed_query += f" AND {from_date}[PDAT]:{to_date}[PDAT]"
            
            # Search PubMed
            results = self.pubmed.query(pubmed_query, max_results=max_results)
            
            articles = []
            for article in results:
                try:
                    # Extract article data
                    article_data = {
                        'id': f"pubmed_{article.pubmed_id}",
                        'title': article.title or '',
                        'abstract': article.abstract or '',
                        'authors': [f"{author.get('firstname', '')} {author.get('lastname', '')}".strip() 
                                  for author in article.authors] if article.authors else [],
                        'journal': article.journal,
                        'publication_date': self._parse_pubmed_date(article.publication_date),
                        'doi': article.doi,
                        'pmid': str(article.pubmed_id),
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/",
                        'source': LiteratureSource.PUBMED,
                        'keywords': article.keywords if hasattr(article, 'keywords') else [],
                        'mesh_terms': article.mesh_terms if hasattr(article, 'mesh_terms') else [],
                        'content': f"{article.title or ''}\n\n{article.abstract or ''}"
                    }
                    
                    articles.append(LiteratureArticle(**article_data))
                    
                except Exception as e:
                    logger.warning("Failed to process PubMed article", error=str(e))
                    continue
            
            return articles
            
        except Exception as e:
            logger.error("PubMed search failed", error=str(e))
            return []
    
    async def _search_embase(self, query: str, max_results: int, date_range: Optional[Dict[str, str]]) -> List[LiteratureArticle]:
        """Search Embase database (placeholder - requires API key)"""
        try:
            # TODO: Implement Embase API integration
            logger.info("Embase search not implemented yet", query=query)
            return []
            
        except Exception as e:
            logger.error("Embase search failed", error=str(e))
            return []
    
    async def _search_cochrane(self, query: str, max_results: int, date_range: Optional[Dict[str, str]]) -> List[LiteratureArticle]:
        """Search Cochrane Library (placeholder - requires API key)"""
        try:
            # TODO: Implement Cochrane API integration
            logger.info("Cochrane search not implemented yet", query=query)
            return []
            
        except Exception as e:
            logger.error("Cochrane search failed", error=str(e))
            return []
    
    def _parse_pubmed_date(self, pubmed_date: Any) -> Optional[datetime]:
        """Parse PubMed date format"""
        try:
            if isinstance(pubmed_date, datetime):
                return pubmed_date
            elif isinstance(pubmed_date, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        return datetime.strptime(pubmed_date, fmt)
                    except ValueError:
                        continue
            return None
        except Exception:
            return None
    
    def _deduplicate_results(self, results: List[LiteratureArticle]) -> List[LiteratureArticle]:
        """Remove duplicate articles based on title and DOI"""
        seen = set()
        unique_results = []
        
        for article in results:
            # Create a unique key based on title and DOI
            key = (article.title.lower().strip(), article.doi or '')
            if key not in seen:
                seen.add(key)
                unique_results.append(article)
        
        return unique_results
