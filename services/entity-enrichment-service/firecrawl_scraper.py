"""
Firecrawl Entity Scraper
Handles intelligent web scraping for different entity types
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from firecrawl import FirecrawlApp
from pydantic import BaseModel
import json
import re
from urllib.parse import quote_plus
import openai
import os

logger = logging.getLogger(__name__)

# Pydantic schemas for structured extraction
class OrganizationSchema(BaseModel):
    name: str
    description: str
    industry: str
    headquarters: str
    founded: str
    website: str
    employee_count: str
    revenue: str
    key_people: List[str]

class PersonSchema(BaseModel):
    name: str
    title: str
    company: str
    location: str
    bio: str
    experience: List[str]
    education: List[str]
    skills: List[str]

class LocationSchema(BaseModel):
    name: str
    type: str
    population: str
    area: str
    country: str
    notable_features: List[str]
    description: str

class FirecrawlEntityScraper:
    def __init__(self, api_key: str):
        self.firecrawl = FirecrawlApp(api_key=api_key)
        
        # Initialize OpenAI client for AI summarization
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not found. AI summarization will be disabled.")
        
        # Entity-specific search strategies
        self.entity_sources = {
            "PERSON": [
                "linkedin.com/in/",
                "linkedin.com/pub/",
                "wikipedia.org/wiki/",
                "crunchbase.com/person/"
            ],
            "ORGANIZATION": [
                "linkedin.com/company/",
                "crunchbase.com/organization/",
                "wikipedia.org/wiki/",
                "about.{entity}.com",
                "{entity}.com/about"
            ],
            "LOCATION": [
                "wikipedia.org/wiki/",
                "britannica.com/place/"
            ]
        }
        
        # Extraction schemas for different entity types
        self.extraction_schemas = {
            "PERSON": {
                "name": "string",
                "title": "string", 
                "company": "string",
                "location": "string",
                "bio": "string",
                "experience": "array",
                "education": "array",
                "skills": "array"
            },
            "ORGANIZATION": {
                "name": "string",
                "description": "string",
                "industry": "string",
                "headquarters": "string",
                "founded": "string",
                "size": "string",
                "website": "string",
                "leadership": "array"
            },
            "LOCATION": {
                "name": "string",
                "type": "string",
                "population": "string",
                "area": "string",
                "description": "string",
                "notable_features": "array"
            }
        }

    async def scrape_entity_with_strategies(self, entity_name: str, entity_type: str, max_sources: int = 3) -> Dict[str, Any]:
        """
        Scrape web information for an entity using multiple search strategies with fallbacks
        """
        logger.info(f"Starting enhanced scrape for {entity_name} (Type: {entity_type})")
        
        try:
            # Get search strategies
            search_strategies = self._generate_search_strategies(entity_name, entity_type, max_sources)
            
            scraped_data = {}
            sources_used = []
            conflicts = []
            search_attempts = 0
            successful_strategies = []
            
            # Try each strategy until we get enough data or exhaust strategies
            for strategy in search_strategies:
                if len(sources_used) >= max_sources:
                    break
                    
                search_attempts += 1
                logger.info(f"Attempt {search_attempts}: Using '{strategy['name']}' strategy")
                logger.info(f"Query: {strategy['query']}")
                
                try:
                    # Use Firecrawl search instead of direct URL scraping
                    search_result = await self._search_with_firecrawl(
                        strategy['query'], 
                        strategy['limit']
                    )
                    
                    if search_result and search_result.get("success"):
                        strategy_data = await self._process_search_results(
                            search_result.get("data", []), 
                            entity_name, 
                            entity_type
                        )
                        
                        if strategy_data:
                            scraped_data[strategy["name"]] = strategy_data
                            sources_used.extend([item.get("url", "") for item in search_result.get("data", [])])
                            successful_strategies.append(strategy["name"])
                            
                            # Detect conflicts with previous data
                            conflicts.extend(self._detect_conflicts(scraped_data, strategy["name"]))
                            
                            logger.info(f"Strategy '{strategy['name']}' successful - found data")
                        else:
                            logger.info(f"Strategy '{strategy['name']}' returned no useful data")
                    else:
                        logger.info(f"Strategy '{strategy['name']}' failed to return results")
                        
                except Exception as e:
                    logger.warning(f"Strategy '{strategy['name']}' failed: {str(e)}")
                    continue
            
            # Calculate confidence score based on strategies used and data quality
            confidence_score = self._calculate_enhanced_confidence_score(
                scraped_data, successful_strategies, search_attempts
            )
            
            # Consolidate data from all successful strategies
            consolidated_data = self._consolidate_strategy_data(scraped_data, entity_type)
            
            return {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "scraped_data": scraped_data,
                "consolidated_data": consolidated_data,
                "sources": list(set(sources_used)),  # Remove duplicates
                "confidence_score": confidence_score,
                "conflicts": conflicts,
                "search_attempts": search_attempts,
                "successful_strategies": successful_strategies,
                "scrape_timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced scraping for {entity_name}: {str(e)}")
            return {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "error": str(e),
                "confidence_score": 0.0,
                "sources": [],
                "conflicts": [],
                "search_attempts": 0,
                "successful_strategies": []
            }

    # Keep the original method for backward compatibility
    async def scrape_entity(self, entity_name: str, entity_type: str, max_sources: int = 3) -> Dict[str, Any]:
        """Main entry point for entity scraping - now using structured extraction"""
        return await self.scrape_entity_structured(entity_name, entity_type, max_sources)

    def _generate_search_strategies(self, entity_name: str, entity_type: str, max_sources: int) -> List[Dict[str, str]]:
        """Generate intelligent search strategies for the entity with fallbacks"""
        clean_name = self._clean_entity_name(entity_name)
        
        if entity_type == "ORGANIZATION":
            return [
                {
                    "name": "direct_company",
                    "query": f'"{clean_name}" company about headquarters',
                    "limit": 3
                },
                {
                    "name": "linkedin_focused",
                    "query": f'site:linkedin.com/company "{clean_name}"',
                    "limit": 2
                },
                {
                    "name": "crunchbase_focused", 
                    "query": f'site:crunchbase.com "{clean_name}" organization',
                    "limit": 2
                },
                {
                    "name": "general_info",
                    "query": f'"{clean_name}" company information founded industry',
                    "limit": 3
                }
            ]
        elif entity_type == "PERSON":
            return [
                {
                    "name": "linkedin_profile",
                    "query": f'site:linkedin.com/in "{clean_name}"',
                    "limit": 2
                },
                {
                    "name": "professional_bio",
                    "query": f'"{clean_name}" biography professional experience',
                    "limit": 3
                },
                {
                    "name": "general_person",
                    "query": f'"{clean_name}" profile background',
                    "limit": 2
                }
            ]
        elif entity_type == "LOCATION":
            return [
                {
                    "name": "wikipedia_location",
                    "query": f'site:wikipedia.org "{clean_name}" location',
                    "limit": 2
                },
                {
                    "name": "general_location",
                    "query": f'"{clean_name}" information facts geography',
                    "limit": 3
                }
            ]
        else:
            return [
                {
                    "name": "general_search",
                    "query": f'"{clean_name}" information about',
                    "limit": 3
                }
            ]

    async def _scrape_url(self, url: str, entity_type: str) -> Dict[str, Any]:
        """Scrape a single URL using Firecrawl"""
        try:
            # Get extraction schema for entity type
            schema = self.extraction_schemas.get(entity_type, {})
            
            # Configure scraping parameters
            scrape_params = {
                'formats': ['markdown', 'html'],
                'onlyMainContent': True,
                'includeTags': ['title', 'meta', 'h1', 'h2', 'h3', 'p', 'span', 'div'],
                'excludeTags': ['script', 'style', 'nav', 'footer', 'header', 'aside']
            }
            
            if schema:
                scrape_params['extract'] = {
                    'schema': schema,
                    'systemPrompt': f'Extract information about {entity_type.lower()} entities from this content.'
                }
            
            # Perform scrape
            result = self.firecrawl.scrape(url, **scrape_params)
            
            if result.get('success'):
                return {
                    "success": True,
                    "data": {
                        "content": result.get('data', {}).get('markdown', ''),
                        "extracted": result.get('data', {}).get('extract', {}),
                        "metadata": result.get('data', {}).get('metadata', {})
                    }
                }
            else:
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            logger.error(f"Firecrawl scraping failed for {url}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _clean_entity_name(self, entity_name: str) -> str:
        """Clean entity name for URL construction"""
        # Remove special characters and normalize
        clean_name = re.sub(r'[^\w\s-]', '', entity_name)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        return clean_name

    def _extract_source_name(self, url: str) -> str:
        """Extract source name from URL"""
        if "linkedin.com" in url:
            return "linkedin"
        elif "wikipedia.org" in url:
            return "wikipedia"
        elif "crunchbase.com" in url:
            return "crunchbase"
        elif "google.com" in url:
            return "google_search"
        else:
            return "other"

    def _detect_conflicts(self, scraped_data: Dict[str, Any], new_source: str) -> List[Dict[str, Any]]:
        """Detect conflicts between different sources"""
        conflicts = []
        
        if len(scraped_data) < 2:
            return conflicts
        
        # Simple conflict detection - comparing company names, titles, etc.
        new_data = scraped_data.get(new_source, {}).get("extracted", {})
        
        for source, data in scraped_data.items():
            if source == new_source:
                continue
                
            existing_data = data.get("extracted", {})
            
            # Check for conflicting company names
            if (new_data.get("company") and existing_data.get("company") and 
                new_data["company"].lower() != existing_data["company"].lower()):
                conflicts.append({
                    "field": "company",
                    "source1": source,
                    "value1": existing_data["company"],
                    "source2": new_source,
                    "value2": new_data["company"]
                })
            
            # Check for conflicting titles
            if (new_data.get("title") and existing_data.get("title") and 
                new_data["title"].lower() != existing_data["title"].lower()):
                conflicts.append({
                    "field": "title",
                    "source1": source,
                    "value1": existing_data["title"],
                    "source2": new_source,
                    "value2": new_data["title"]
                })
        
        return conflicts

    def _calculate_confidence_score(self, scraped_data: Dict[str, Any], sources: List[str]) -> float:
        """Calculate confidence score based on data quality and source count"""
        if not scraped_data:
            return 0.0
        
        # Base score from number of sources
        source_score = min(len(sources) / 3.0, 1.0) * 0.4
        
        # Data completeness score
        total_fields = 0
        filled_fields = 0
        
        for source_data in scraped_data.values():
            extracted = source_data.get("extracted", {})
            for value in extracted.values():
                total_fields += 1
                if value and str(value).strip():
                    filled_fields += 1
        
        completeness_score = (filled_fields / max(total_fields, 1)) * 0.4 if total_fields > 0 else 0.0
        
        # Source quality bonus
        quality_bonus = 0.0
        for source in sources:
            if "linkedin.com" in source:
                quality_bonus += 0.1
            elif "wikipedia.org" in source:
                quality_bonus += 0.08
            elif "crunchbase.com" in source:
                quality_bonus += 0.07
        
        quality_bonus = min(quality_bonus, 0.2)
        
        return min(source_score + completeness_score + quality_bonus, 1.0)

    def _consolidate_data(self, scraped_data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Consolidate data from multiple sources"""
        consolidated = {}
        
        # Simple consolidation - prefer LinkedIn for professional info, Wikipedia for general info
        source_priority = ["linkedin", "wikipedia", "crunchbase", "google_search", "other"]
        
        for source in source_priority:
            if source in scraped_data:
                source_data = scraped_data[source].get("extracted", {})
                for field, value in source_data.items():
                    if field not in consolidated and value and str(value).strip():
                        consolidated[field] = value
        
        return consolidated

    async def _search_with_firecrawl(self, query: str, limit: int) -> Dict[str, Any]:
        """Use Firecrawl search API to find relevant URLs"""
        try:
            logger.info(f"Firecrawl search for query: {query}")
            
            # Use Firecrawl search API
            search_result = self.firecrawl.search(
                query=query,
                limit=limit,
                timeout=30000
            )
            
            results = []
            # Check both web and news results
            search_data = []
            if hasattr(search_result, 'web') and search_result.web:
                search_data.extend(search_result.web)
            if hasattr(search_result, 'news') and search_result.news:
                search_data.extend(search_result.news)
            
            for item in search_data:
                if hasattr(item, 'url') and hasattr(item, 'title'):
                    results.append({
                        "url": item.url,
                        "title": item.title,
                        "description": getattr(item, 'description', ''),
                        "snippet": getattr(item, 'snippet', '')
                    })
                    logger.info(f"Found search result: {item.url}")
            
            return {
                "success": len(results) > 0,
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Firecrawl search failed for query '{query}': {str(e)}")
            return {"success": False, "error": str(e)}

    async def _process_search_results(self, search_results: List[Dict], entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Process search results and extract relevant entity information"""
        if not search_results:
            return None
            
        # Combine all content from search results
        combined_content = ""
        sources = []
        
        for result in search_results:
            if result.get("markdown"):
                combined_content += f"\n\n--- Source: {result.get('url', 'Unknown')} ---\n"
                combined_content += result.get("markdown", "")[:2000]  # Limit content length
                sources.append(result.get("url", ""))
        
        if not combined_content.strip():
            return None
            
        # Use a simplified extraction for now - in production you'd use OpenAI here
        extracted_data = self._extract_basic_info(combined_content, entity_name, entity_type)
        
        return {
            "extracted_info": extracted_data,
            "sources": sources,
            "content_length": len(combined_content),
            "num_sources": len(search_results)
        }

    def _extract_basic_info(self, content: str, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Basic information extraction - in production this would use OpenAI"""
        content_lower = content.lower()
        entity_lower = entity_name.lower()
        
        # Basic extraction logic
        extracted = {
            "name": entity_name,
            "type": entity_type,
            "mentioned": entity_lower in content_lower,
            "content_snippet": content[:500] if content else ""
        }
        
        if entity_type == "ORGANIZATION":
            # Look for common organization keywords
            if any(word in content_lower for word in ["company", "corporation", "inc", "ltd", "founded"]):
                extracted["is_company"] = True
            if "founded" in content_lower:
                extracted["has_founding_info"] = True
            if any(word in content_lower for word in ["headquarters", "based in", "located"]):
                extracted["has_location_info"] = True
                
        elif entity_type == "PERSON":
            if any(word in content_lower for word in ["profile", "biography", "experience", "works at"]):
                extracted["has_professional_info"] = True
                
        elif entity_type == "LOCATION":
            if any(word in content_lower for word in ["population", "area", "geography", "located"]):
                extracted["has_geographic_info"] = True
        
        return extracted

    def _calculate_enhanced_confidence_score(self, scraped_data: Dict[str, Any], successful_strategies: List[str], search_attempts: int) -> float:
        """Calculate confidence score based on strategy success and data quality"""
        if not scraped_data:
            return 0.0
        
        # Base score from successful strategies
        strategy_score = min(len(successful_strategies) / 3.0, 1.0) * 0.4
        
        # Data quality score
        quality_score = 0.0
        total_items = 0
        quality_items = 0
        
        for strategy_name, strategy_data in scraped_data.items():
            if strategy_data and strategy_data.get("extracted_info"):
                extracted = strategy_data["extracted_info"]
                for key, value in extracted.items():
                    total_items += 1
                    if value and str(value).strip() and value != "Unknown":
                        quality_items += 1
        
        if total_items > 0:
            quality_score = (quality_items / total_items) * 0.4
        
        # Strategy diversity bonus
        diversity_bonus = 0.0
        if "linkedin_focused" in successful_strategies:
            diversity_bonus += 0.05
        if "crunchbase_focused" in successful_strategies:
            diversity_bonus += 0.05
        if "direct_company" in successful_strategies:
            diversity_bonus += 0.05
        
        # Penalty for too many attempts
        attempt_penalty = min(search_attempts / 10.0, 0.1)
        
        return min(strategy_score + quality_score + diversity_bonus - attempt_penalty, 1.0)

    def _consolidate_strategy_data(self, scraped_data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Consolidate data from multiple search strategies"""
        consolidated = {
            "name": "",
            "type": entity_type,
            "sources_used": [],
            "data_quality": "basic"
        }
        
        # Strategy priority for consolidation
        strategy_priority = [
            "linkedin_focused", 
            "crunchbase_focused", 
            "direct_company", 
            "professional_bio",
            "wikipedia_location",
            "general_info",
            "general_person",
            "general_location",
            "general_search"
        ]
        
        # Consolidate based on priority
        for strategy in strategy_priority:
            if strategy in scraped_data:
                strategy_data = scraped_data[strategy]
                if strategy_data and strategy_data.get("extracted_info"):
                    extracted = strategy_data["extracted_info"]
                    
                    # Fill in missing fields with higher priority data
                    for field, value in extracted.items():
                        if field not in consolidated and value and str(value).strip():
                            consolidated[field] = value
                    
                    # Add sources
                    if strategy_data.get("sources"):
                        consolidated["sources_used"].extend(strategy_data["sources"])
        
        # Remove duplicates from sources
        consolidated["sources_used"] = list(set(consolidated["sources_used"]))
        
        # Determine data quality
        if len(consolidated["sources_used"]) >= 3:
            consolidated["data_quality"] = "comprehensive"
        elif len(consolidated["sources_used"]) >= 2:
            consolidated["data_quality"] = "moderate"
        
        return consolidated

    def _generate_search_urls(self, query: str, limit: int) -> List[str]:
        """Generate search URLs for the query"""
        # Clean the query for URL encoding
        clean_query = query.replace('"', '').replace(' ', '+').replace(',', '')
        wiki_query = query.replace(' ', '_').replace(',', '').replace('"', '')
        
        urls = [
            f"https://www.google.com/search?q={clean_query}",
            f"https://en.wikipedia.org/wiki/{wiki_query}",
        ]
        
        # Add specific URLs based on entity type - use proper search URLs
        if "organization" in query.lower() or "company" in query.lower() or "llc" in query.lower():
            # Use DuckDuckGo search instead of direct company URLs
            urls.extend([
                f"https://duckduckgo.com/?q={clean_query}+company+information",
                f"https://www.bing.com/search?q={clean_query}+business+profile"
            ])
        
        return urls[:limit]

    def _is_valid_content(self, content: str, query: str) -> bool:
        """Check if content is valid and not a 404/error page"""
        if not content or len(content.strip()) < 50:
            return False
        
        # Check for common error indicators
        error_indicators = [
            "page not found",
            "404",
            "not found",
            "error occurred",
            "oops",
            "something went wrong",
            "unexpected issue",
            "try again",
            "refresh the page",
            "contact support"
        ]
        
        content_lower = content.lower()
        for indicator in error_indicators:
            if indicator in content_lower:
                return False
        
        # Check if content contains the query (entity name)
        query_words = query.lower().split()
        content_lower = content.lower()
        matching_words = sum(1 for word in query_words if word in content_lower)
        
        # At least 50% of query words should be present
        return matching_words >= len(query_words) * 0.5

    async def _extract_structured_data(self, url: str, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Extract structured data using Firecrawl's LLM extraction"""
        try:
            # Choose the right schema based on entity type
            if entity_type == "ORGANIZATION":
                schema = OrganizationSchema
            elif entity_type == "PERSON":
                schema = PersonSchema
            elif entity_type == "LOCATION":
                schema = LocationSchema
            else:
                # Generic schema for other types
                schema = OrganizationSchema  # Default fallback
            
            # Extract structured data using Firecrawl's scraping
            extraction_result = self.firecrawl.scrape(
                url,
                only_main_content=True,
                timeout=60000
            )
            
            # Handle the new API response structure
            if hasattr(extraction_result, 'content') or hasattr(extraction_result, 'markdown'):
                content = getattr(extraction_result, 'content', '') or getattr(extraction_result, 'markdown', '')
                if content:
                    return {
                        "extracted_data": {"content": content},
                        "metadata": {"url": url},
                        "source_url": url,
                        "extraction_method": "scrape_content"
                    }
            
            logger.warning(f"LLM extraction failed for {url}: {extraction_result}")
            return None
                
        except Exception as e:
            logger.error(f"Structured extraction failed for {url}: {str(e)}")
            return None

    def _generate_target_urls(self, entity_name: str, entity_type: str, max_urls: int = 3) -> List[str]:
        """Generate intelligent target URLs for entity types with enhanced coverage"""
        urls = []
        clean_name = entity_name.lower().replace(' ', '-').replace(',', '').replace('.', '').replace('&', 'and')
        wiki_name = entity_name.replace(' ', '_').replace('&', 'and')
        
        if entity_type == "ORGANIZATION":
            # Enhanced company-specific sources with better URL patterns
            urls.extend([
                f"https://www.crunchbase.com/organization/{clean_name}",
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.linkedin.com/company/{clean_name}",
                f"https://www.bloomberg.com/profile/company/{clean_name.upper()}",
                f"https://finance.yahoo.com/quote/{clean_name.upper()}",
                f"https://www.reuters.com/companies/{clean_name.upper()}",
                f"https://www.forbes.com/companies/{clean_name}/",
                f"https://www.hoovers.com/company-information/cs/company-profile.{clean_name}.html",
                f"https://www.zoominfo.com/c/{clean_name}/",
                f"https://www.glassdoor.com/Overview/{clean_name}"
            ])
        elif entity_type == "PERSON":
            # Enhanced person-specific sources
            urls.extend([
                f"https://www.linkedin.com/in/{clean_name}",
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.crunchbase.com/person/{clean_name}",
                f"https://www.bloomberg.com/profile/person/{clean_name}",
                f"https://www.forbes.com/profile/{clean_name}/",
                f"https://www.zoominfo.com/p/{clean_name}/",
                f"https://www.glassdoor.com/Reviews/{clean_name}-reviews",
                f"https://www.businessinsider.com/search?query={entity_name.replace(' ', '+')}",
                f"https://www.reuters.com/search/news?blob={entity_name.replace(' ', '+')}"
            ])
        elif entity_type == "LOCATION":
            # Enhanced location-specific sources
            urls.extend([
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.britannica.com/place/{clean_name}",
                f"https://www.worldbank.org/en/country/{clean_name}",
                f"https://www.cia.gov/the-world-factbook/countries/{clean_name}/",
                f"https://www.lonelyplanet.com/{clean_name}",
                f"https://www.tripadvisor.com/Search?q={entity_name.replace(' ', '+')}",
                f"https://www.google.com/maps/place/{entity_name.replace(' ', '+')}",
                f"https://www.weather.gov/{clean_name}",
                f"https://www.census.gov/quickfacts/{clean_name}"
            ])
        elif entity_type == "DISEASE":
            # Medical/health-specific sources
            urls.extend([
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.mayoclinic.org/diseases-conditions/{clean_name}",
                f"https://www.cdc.gov/{clean_name}/index.html",
                f"https://www.who.int/health-topics/{clean_name}",
                f"https://www.medlineplus.gov/{clean_name}.html",
                f"https://www.nhs.uk/conditions/{clean_name}/",
                f"https://www.webmd.com/search/search_results/default.aspx?query={entity_name.replace(' ', '+')}",
                f"https://www.healthline.com/health/{clean_name}"
            ])
        elif entity_type == "DRUG":
            # Pharmaceutical-specific sources
            urls.extend([
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.drugs.com/{clean_name}.html",
                f"https://www.rxlist.com/{clean_name}-drug.htm",
                f"https://www.webmd.com/drugs/2/search?type=drugs&query={entity_name.replace(' ', '+')}",
                f"https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files",
                f"https://www.ncbi.nlm.nih.gov/pubmed/?term={entity_name.replace(' ', '+')}",
                f"https://www.clinicaltrials.gov/ct2/results?term={entity_name.replace(' ', '+')}"
            ])
        elif entity_type == "TREATMENT":
            # Treatment-specific sources
            urls.extend([
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.mayoclinic.org/tests-procedures/{clean_name}",
                f"https://www.cancer.gov/about-cancer/treatment/types/{clean_name}",
                f"https://www.nhs.uk/treatments/{clean_name}/",
                f"https://www.healthline.com/health/{clean_name}",
                f"https://www.webmd.com/search/search_results/default.aspx?query={entity_name.replace(' ', '+')}",
                f"https://www.medlineplus.gov/{clean_name}.html"
            ])
        else:
            # Generic sources for other entity types
            urls.extend([
                f"https://en.wikipedia.org/wiki/{wiki_name}",
                f"https://www.google.com/search?q={entity_name.replace(' ', '+')}",
                f"https://www.britannica.com/search?query={entity_name.replace(' ', '+')}",
                f"https://www.merriam-webster.com/dictionary/{clean_name}",
                f"https://www.urbandictionary.com/define.php?term={clean_name}"
            ])
        
        # Remove duplicates and limit to max_urls
        unique_urls = list(dict.fromkeys(urls))  # Preserves order while removing duplicates
        return unique_urls[:max_urls]

    async def _extract_structured_data_batch(self, urls: List[str], entity_name: str, entity_type: str) -> List[Dict[str, Any]]:
        """Use Firecrawl's extract API for structured data extraction"""
        try:
            # Choose the right schema based on entity type
            if entity_type == "ORGANIZATION":
                schema = OrganizationSchema
            elif entity_type == "PERSON":
                schema = PersonSchema
            elif entity_type == "LOCATION":
                schema = LocationSchema
            else:
                schema = OrganizationSchema  # Default fallback

            logger.info(f"Starting Firecrawl extract for {len(urls)} URLs")
            
            # Use Firecrawl's extract API with structured schema
            extraction_result = self.firecrawl.extract(
                urls=urls,
                prompt=f"Extract detailed information about {entity_name}, focusing on {entity_type.lower()} data",
                schema=schema.model_json_schema(),
                system_prompt=f"You are an expert at extracting structured information about {entity_type.lower()} entities. Focus on factual, verifiable information.",
                enable_web_search=True,
                show_sources=True,
                timeout=60000
            )
            
            results = []
            if hasattr(extraction_result, 'data') and extraction_result.data:
                for item in extraction_result.data:
                    if hasattr(item, 'extract') and item.extract:
                        results.append({
                            "source_url": getattr(item, 'url', ''),
                            "extracted_data": item.extract,
                            "metadata": {
                                "url": getattr(item, 'url', ''),
                                "sources": getattr(item, 'sources', [])
                            },
                            "extraction_method": "firecrawl_extract_api"
                        })
                        logger.info(f"Successfully extracted structured data from: {getattr(item, 'url', 'unknown')}")
                    else:
                        logger.warning(f"No extract data from: {getattr(item, 'url', 'unknown')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch extraction failed: {str(e)}")
            return []

    def _consolidate_extraction_results(self, extraction_results: List[Dict[str, Any]], entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Consolidate structured extraction results from multiple sources"""
        consolidated = {
            "name": entity_name,
            "type": entity_type,
            "sources_count": len(extraction_results),
            "confidence": "high" if len(extraction_results) >= 2 else "medium" if len(extraction_results) == 1 else "low"
        }
        
        # Combine data from all sources
        all_extracted_data = []
        for result in extraction_results:
            extracted = result.get("extracted_data", {})
            if extracted:
                all_extracted_data.append(extracted)
        
        if all_extracted_data:
            # For organization data, prioritize first good result and supplement with others
            if entity_type == "ORGANIZATION" and all_extracted_data:
                primary_data = all_extracted_data[0]
                
                # Copy all fields from primary source
                for field, value in primary_data.items():
                    if value and str(value).strip():
                        consolidated[field] = value
                
                # Supplement with data from other sources for missing fields
                for additional_data in all_extracted_data[1:]:
                    for field, value in additional_data.items():
                        if field not in consolidated and value and str(value).strip():
                            consolidated[field] = value
        
        return consolidated

    def _calculate_confidence_from_extractions(self, extraction_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on extraction results"""
        if not extraction_results:
            return 0.0
        
        base_score = min(len(extraction_results) * 0.3, 0.8)  # 30% per source, max 80%
        
        # Bonus for data completeness
        total_fields = 0
        filled_fields = 0
        
        for result in extraction_results:
            extracted = result.get("extracted_data", {})
            for value in extracted.values():
                total_fields += 1
                if value and str(value).strip():
                    filled_fields += 1
        
        completeness_bonus = (filled_fields / total_fields) * 0.2 if total_fields > 0 else 0
        
        return min(base_score + completeness_bonus, 1.0)

    def _empty_result(self, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "scraped_data": {},
            "consolidated_data": {},
            "confidence_score": 0.0,
            "sources": [],
            "extraction_method": "failed"
        }

    async def scrape_entity_structured(self, entity_name: str, entity_type: str, max_sources: int = 3) -> Dict[str, Any]:
        """
        Enhanced scraping using Firecrawl's search and extract APIs
        """
        logger.info(f"Starting structured scrape for {entity_name} (Type: {entity_type})")
        
        try:
            # Step 1: Use Firecrawl search API to find relevant URLs
            search_query = f"{entity_name} {entity_type.lower()}"
            search_results = await self._search_with_firecrawl(search_query, max_sources)
            
            if not search_results.get("success") or not search_results.get("data"):
                logger.warning(f"No search results found for {entity_name}")
                return self._empty_result(entity_name, entity_type)
            
            # Extract URLs from search results
            search_urls = [result["url"] for result in search_results["data"]]
            logger.info(f"Found {len(search_urls)} URLs from search: {search_urls}")
            
            # Step 2: Use Firecrawl extract API for structured data extraction
            extraction_results = await self._extract_structured_data_batch(search_urls, entity_name, entity_type)
            
            if extraction_results:
                # Consolidate results from multiple sources
                consolidated_data = self._consolidate_extraction_results(extraction_results, entity_name, entity_type)
                confidence_score = self._calculate_confidence_from_extractions(extraction_results)
                
                # Generate AI summary if OpenAI is available
                ai_summary = None
                if self.openai_client:
                    ai_summary = await self._generate_ai_summary(consolidated_data, entity_name, entity_type)
                
                result = {
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "scraped_data": extraction_results,
                    "consolidated_data": consolidated_data,
                    "confidence_score": confidence_score,
                    "sources": [result.get("source_url", "") for result in extraction_results],
                    "extraction_method": "structured_firecrawl"
                }
                
                if ai_summary:
                    result["ai_summary"] = ai_summary
                
                return result
            else:
                logger.warning(f"No successful extractions for {entity_name}")
                return self._empty_result(entity_name, entity_type)
                
        except Exception as e:
            logger.error(f"Structured scraping failed for {entity_name}: {str(e)}")
            return self._empty_result(entity_name, entity_type)

    async def _generate_ai_summary(self, consolidated_data: Dict[str, Any], entity_name: str, entity_type: str) -> Optional[str]:
        """Generate AI-powered summary of enriched entity data"""
        try:
            if not self.openai_client:
                return None
            
            # Prepare the data for summarization
            summary_prompt = self._create_summary_prompt(consolidated_data, entity_name, entity_type)
            
            # Generate summary using OpenAI (v1.0.0+ API)
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst specializing in entity enrichment and summarization. Provide concise, informative summaries that highlight key insights and relationships."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            if response and response.choices:
                summary = response.choices[0].message.content.strip()
                logger.info(f"Generated AI summary for {entity_name}")
                return summary
            else:
                logger.warning(f"Failed to generate AI summary for {entity_name}")
                return None
                
        except Exception as e:
            logger.error(f"AI summarization failed for {entity_name}: {str(e)}")
            return None

    def _create_summary_prompt(self, consolidated_data: Dict[str, Any], entity_name: str, entity_type: str) -> str:
        """Create a structured prompt for AI summarization"""
        
        # Extract key information
        description = consolidated_data.get("description", "")
        industry = consolidated_data.get("industry", "")
        headquarters = consolidated_data.get("headquarters", "")
        founded = consolidated_data.get("founded", "")
        key_people = consolidated_data.get("key_people", [])
        employee_count = consolidated_data.get("employee_count", "")
        revenue = consolidated_data.get("revenue", "")
        website = consolidated_data.get("website", "")
        
        prompt = f"""
        Please provide a comprehensive yet concise summary of the following {entity_type.lower()} entity:

        Entity: {entity_name}
        Type: {entity_type}
        
        Key Information:
        - Description: {description}
        - Industry: {industry}
        - Headquarters: {headquarters}
        - Founded: {founded}
        - Key People: {', '.join(key_people) if key_people else 'Not specified'}
        - Employee Count: {employee_count}
        - Revenue: {revenue}
        - Website: {website}
        
        Please provide a 2-3 paragraph summary that:
        1. Introduces the entity and its primary purpose
        2. Highlights key business aspects, achievements, or notable characteristics
        3. Mentions any significant relationships, impact, or relevance in their field
        
        Focus on providing actionable insights and context that would be valuable for business intelligence or research purposes.
        """
        
        return prompt

    async def generate_entity_insights(self, entity_name: str, entity_type: str, consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate advanced insights and analysis for an entity"""
        try:
            if not self.openai_client:
                return {"insights": "AI insights not available - OpenAI API key not configured"}
            
            # Create insights prompt
            insights_prompt = f"""
            Analyze the following {entity_type.lower()} entity and provide strategic insights:
            
            Entity: {entity_name}
            Data: {json.dumps(consolidated_data, indent=2)}
            
            Please provide:
            1. Market Position Analysis
            2. Competitive Advantages
            3. Potential Risks or Challenges
            4. Growth Opportunities
            5. Key Relationships or Partnerships
            6. Industry Impact Assessment
            
            Format as a structured analysis with clear sections.
            """
            
            # Generate insights using OpenAI (v1.0.0+ API)
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a strategic business analyst with expertise in market research and competitive intelligence."},
                    {"role": "user", "content": insights_prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            if response and response.choices:
                insights = response.choices[0].message.content.strip()
                return {
                    "insights": insights,
                    "generated_at": "2025-08-08T15:00:00Z",
                    "model": "gpt-3.5-turbo"
                }
            else:
                return {"insights": "Failed to generate insights"}
                
        except Exception as e:
            logger.error(f"Insights generation failed for {entity_name}: {str(e)}")
            return {"insights": f"Error generating insights: {str(e)}"}