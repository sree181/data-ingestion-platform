"""
OpenAI-powered entity extraction and relationship detection
"""
import json
import re
from typing import Dict, List, Any, Tuple, Optional
import structlog
import openai
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

class OpenAIEntityExtractor:
    """Extract entities and relationships using OpenAI GPT models"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize the OpenAI entity extractor"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info("OpenAI Entity Extractor initialized", model=model)
    
    async def extract_entities_and_relationships(self, text: str, document_title: str = "") -> Dict[str, Any]:
        """
        Extract entities and relationships from text using OpenAI
        
        Args:
            text: Document text content
            document_title: Title of the document for context
            
        Returns:
            Dict containing entities, relationships, and metadata
        """
        try:
            logger.info("Starting OpenAI entity extraction", 
                       text_length=len(text), 
                       title=document_title)
            
            # Truncate text if too long (GPT-4 has token limits)
            max_chars = 12000  # Roughly 3000 tokens
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                logger.info("Text truncated for processing", 
                           original_length=len(text), 
                           truncated_length=max_chars)
            
            # Create the prompt for entity extraction
            prompt = self._create_entity_extraction_prompt(text, document_title)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert information extraction system. Extract entities and relationships from documents with high precision."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            # Parse the response
            result = self._parse_openai_response(response.choices[0].message.content)
            
            # Add metadata
            result["extraction_metadata"] = {
                "model": self.model,
                "text_length": len(text),
                "document_title": document_title,
                "token_usage": response.usage.dict() if response.usage else None
            }
            
            logger.info("Entity extraction completed",
                       entities_count=len(result.get("entities", [])),
                       relationships_count=len(result.get("relationships", [])))
            
            return result
            
        except Exception as e:
            logger.error("OpenAI entity extraction failed", error=str(e))
            return self._get_fallback_result(text, str(e))
    
    def _create_entity_extraction_prompt(self, text: str, document_title: str) -> str:
        """Create a detailed prompt for entity extraction"""
        
        prompt = f"""
Extract entities and relationships from the following document:

DOCUMENT TITLE: {document_title}

TEXT:
{text}

Please extract information in the following JSON format:

{{
    "entities": [
        {{
            "text": "entity text as it appears in document",
            "type": "PERSON|ORGANIZATION|LOCATION|DATE|MONEY|DRUG|DISEASE|TREATMENT|REGULATION|PRODUCT|EVENT|CONCEPT",
            "description": "brief description of the entity",
            "confidence": 0.95,
            "start_char": 123,
            "end_char": 135
        }}
    ],
    "relationships": [
        {{
            "source_entity": "entity1 text",
            "target_entity": "entity2 text", 
            "relationship_type": "WORKS_FOR|LOCATED_IN|CAUSES|TREATS|REGULATES|APPROVES|DEVELOPS|STUDIES|RELATED_TO",
            "description": "description of the relationship",
            "confidence": 0.90
        }}
    ],
    "key_concepts": [
        {{
            "concept": "main concept or theme",
            "importance": 0.95,
            "related_entities": ["entity1", "entity2"]
        }}
    ],
    "document_summary": "2-3 sentence summary of the document's main points"
}}

Focus on:
1. Medical entities (drugs, diseases, treatments, organizations like FDA, CDC)
2. People (researchers, officials, patients)
3. Locations (countries, cities, facilities)
4. Dates and timeframes
5. Financial information
6. Regulatory information
7. Relationships between entities

Be precise with character positions and ensure all extracted text exactly matches the source.
"""
        return prompt
    
    def _parse_openai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI response and extract structured data"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Fallback parsing if no JSON found
                return self._fallback_parse(response_text)
                
        except json.JSONDecodeError as e:
            logger.error("Failed to parse OpenAI JSON response", error=str(e))
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails"""
        return {
            "entities": [],
            "relationships": [],
            "key_concepts": [],
            "document_summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "extraction_method": "fallback"
        }
    
    def _get_fallback_result(self, text: str, error: str) -> Dict[str, Any]:
        """Return fallback result when extraction fails"""
        return {
            "entities": [],
            "relationships": [],
            "key_concepts": [],
            "document_summary": "Entity extraction failed",
            "error": error,
            "extraction_method": "failed"
        }
    
    async def extract_document_insights(self, text: str, document_title: str = "") -> Dict[str, Any]:
        """
        Extract high-level insights and themes from document
        """
        try:
            prompt = f"""
Analyze this document and provide insights:

TITLE: {document_title}
TEXT: {text[:8000]}

Provide a JSON response with:
{{
    "main_themes": ["theme1", "theme2", "theme3"],
    "document_type": "research_paper|regulatory_document|news_article|clinical_trial|patent|other",
    "key_findings": ["finding1", "finding2"],
    "stakeholders": ["stakeholder1", "stakeholder2"],
    "timeline_events": [
        {{
            "date": "date or timeframe",
            "event": "description of event"
        }}
    ],
    "risk_factors": ["risk1", "risk2"],
    "regulatory_aspects": ["aspect1", "aspect2"],
    "sentiment": "positive|negative|neutral",
    "confidence_score": 0.85
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document analysis expert. Provide structured insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            return self._parse_openai_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error("Document insights extraction failed", error=str(e))
            return {"error": str(e)}

    def highlight_entities_in_text(self, text: str, entities: List[Dict]) -> str:
        """
        Create HTML with highlighted entities for UI display
        """
        highlighted_text = text
        
        # Sort entities by start position (reverse order to maintain positions)
        sorted_entities = sorted(entities, key=lambda x: x.get('start_char', 0), reverse=True)
        
        for entity in sorted_entities:
            start = entity.get('start_char', 0)
            end = entity.get('end_char', 0)
            entity_type = entity.get('type', 'UNKNOWN')
            entity_text = entity.get('text', '')
            
            if start < end and end <= len(highlighted_text):
                # Create highlighted span with tooltip
                highlight_html = f'''<span class="entity entity-{entity_type.lower()}" 
                                    title="{entity_type}: {entity.get('description', '')}"
                                    data-entity-type="{entity_type}"
                                    data-confidence="{entity.get('confidence', 0)}">{entity_text}</span>'''
                
                highlighted_text = (highlighted_text[:start] + 
                                  highlight_html + 
                                  highlighted_text[end:])
        
        return highlighted_text