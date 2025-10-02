"""
Multi-Model Entity Extractor
Supports OpenAI, Ollama (Phi3), and other AI models for entity extraction
"""

import os
import json
import structlog
from typing import Dict, Any, Optional, List
from models.ai_models import AIModel, ModelProvider, model_registry, model_factory

logger = structlog.get_logger(__name__)

class MultiModelEntityExtractor:
    """Entity extractor that can use multiple AI models"""
    
    def __init__(self, model_name: str = "phi3:mini", api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.model: Optional[AIModel] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the selected model"""
        try:
            self.model = await model_factory.create_model(
                model_name=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            if self.model:
                self._initialized = True
                logger.info("Multi-model entity extractor initialized", model=self.model_name)
                return True
            else:
                logger.error("Failed to initialize model", model=self.model_name)
                return False
                
        except Exception as e:
            logger.error("Failed to initialize multi-model entity extractor", error=str(e))
            return False
    
    async def extract_entities_and_relationships(
        self, 
        text: str, 
        document_title: str = ""
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships using the selected model
        
        Args:
            text: Document text content
            document_title: Title of the document for context
            
        Returns:
            Dict containing entities, relationships, and metadata
        """
        if not self._initialized or not self.model:
            logger.error("Model not initialized")
            return {"entities": [], "relationships": [], "key_concepts": [], "document_summary": ""}
        
        try:
            logger.info("Starting multi-model entity extraction", 
                       model=self.model_name,
                       text_length=len(text), 
                       title=document_title)
            
            # Use the model's entity extraction method
            result = await self.model.extract_entities(text, document_title)
            
            # Add metadata
            result["extraction_metadata"] = {
                "model": self.model_name,
                "provider": self.model.model_info.provider.value,
                "text_length": len(text),
                "document_title": document_title,
                "is_local": self.model.model_info.is_local
            }
            
            logger.info("Multi-model entity extraction completed",
                       model=self.model_name,
                       entities_count=len(result.get("entities", [])),
                       relationships_count=len(result.get("relationships", [])))
            
            return result
            
        except Exception as e:
            logger.error("Multi-model entity extraction failed", 
                        model=self.model_name, 
                        error=str(e))
            return {"entities": [], "relationships": [], "key_concepts": [], "document_summary": ""}
    
    async def extract_document_insights(self, text: str, document_title: str = "") -> Dict[str, Any]:
        """
        Extract document insights using the selected model
        
        Args:
            text: Document text content
            document_title: Title of the document for context
            
        Returns:
            Dict containing document insights
        """
        if not self._initialized or not self.model:
            logger.error("Model not initialized")
            return {}
        
        try:
            system_prompt = """You are an expert document analyst. Analyze the document and provide insights about:
            1. Main topics and themes
            2. Key findings or conclusions
            3. Important data points or statistics
            4. Potential risks or concerns
            5. Recommendations or next steps
            
            Return a JSON response with these insights."""
            
            user_prompt = f"Document Title: {document_title}\n\nContent: {text[:6000]}"
            
            response = await self.model.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                insights = json.loads(response)
                return insights
            except json.JSONDecodeError:
                return {
                    "analysis": response,
                    "model": self.model_name,
                    "provider": self.model.model_info.provider.value
                }
                
        except Exception as e:
            logger.error("Document insights extraction failed", 
                        model=self.model_name, 
                        error=str(e))
            return {}
    
    def highlight_entities_in_text(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Highlight entities in text (simple implementation)
        
        Args:
            text: Original text
            entities: List of extracted entities
            
        Returns:
            Text with highlighted entities
        """
        try:
            highlighted_text = text
            
            # Sort entities by length (longest first) to avoid partial replacements
            sorted_entities = sorted(entities, key=lambda x: len(x.get("name", "")), reverse=True)
            
            for entity in sorted_entities:
                entity_name = entity.get("name", "")
                entity_type = entity.get("type", "ENTITY")
                
                if entity_name and len(entity_name) > 2:  # Avoid very short matches
                    # Create highlighted version
                    highlighted_entity = f"<mark data-entity-type='{entity_type}'>{entity_name}</mark>"
                    
                    # Replace in text (case-insensitive)
                    import re
                    pattern = re.escape(entity_name)
                    highlighted_text = re.sub(
                        pattern, 
                        highlighted_entity, 
                        highlighted_text, 
                        flags=re.IGNORECASE
                    )
            
            return highlighted_text
            
        except Exception as e:
            logger.error("Entity highlighting failed", error=str(e))
            return text
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current model"""
        if self.model:
            return {
                "name": self.model.model_info.name,
                "provider": self.model.model_info.provider.value,
                "capabilities": [cap.value for cap in self.model.model_info.capabilities],
                "max_tokens": self.model.model_info.max_tokens,
                "is_local": self.model.model_info.is_local,
                "description": self.model.model_info.description
            }
        return None
    
    async def switch_model(self, new_model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> bool:
        """
        Switch to a different model
        
        Args:
            new_model_name: Name of the new model
            api_key: API key for the new model (if needed)
            base_url: Base URL for the new model (if needed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Switching model", from_model=self.model_name, to_model=new_model_name)
            
            # Create new model instance
            new_model = await model_factory.create_model(
                model_name=new_model_name,
                api_key=api_key or self.api_key,
                base_url=base_url or self.base_url
            )
            
            if new_model:
                self.model = new_model
                self.model_name = new_model_name
                self.api_key = api_key or self.api_key
                self.base_url = base_url or self.base_url
                self._initialized = True
                
                logger.info("Model switched successfully", new_model=new_model_name)
                return True
            else:
                logger.error("Failed to create new model", model=new_model_name)
                return False
                
        except Exception as e:
            logger.error("Failed to switch model", error=str(e))
            return False
