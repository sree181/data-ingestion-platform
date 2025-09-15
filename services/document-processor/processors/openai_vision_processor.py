"""
OpenAI Vision API processor for multimodal image analysis
"""

import asyncio
import base64
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    structlog.get_logger(__name__).warning("OpenAI not available")

logger = structlog.get_logger(__name__)


class OpenAIVisionProcessor:
    """Process images using OpenAI Vision API for entity extraction and analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-vision-preview"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and api_key:
            try:
                self.client = openai.AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI Vision processor initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize OpenAI Vision", error=str(e))
                self.client = None
        else:
            logger.warning("OpenAI Vision not available or no API key provided")
    
    async def analyze_image(self, image_data: bytes, image_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API"""
        
        if not self.client:
            raise Exception("OpenAI Vision not available or not properly initialized")
        
        try:
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(image_context)
            
            logger.info("Starting OpenAI Vision analysis", 
                       image_size=len(image_data),
                       context=image_context)
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Extract structured data from analysis
            structured_analysis = await self._extract_structured_data(analysis_text)
            
            result = {
                "analysis": analysis_text,
                "entities": structured_analysis.get("entities", []),
                "image_type": structured_analysis.get("image_type", "unknown"),
                "key_elements": structured_analysis.get("key_elements", []),
                "text_content": structured_analysis.get("text_content", ""),
                "confidence": structured_analysis.get("confidence", 0.8),
                "processing_method": "openai_vision",
                "success": True
            }
            
            logger.info("OpenAI Vision analysis completed",
                       entities_found=len(result["entities"]),
                       image_type=result["image_type"])
            
            return result
            
        except Exception as e:
            logger.error("OpenAI Vision analysis failed", error=str(e))
            return {
                "analysis": "",
                "entities": [],
                "image_type": "unknown",
                "key_elements": [],
                "text_content": "",
                "confidence": 0.0,
                "processing_method": "openai_vision",
                "success": False,
                "error": str(e)
            }
    
    def _create_analysis_prompt(self, context: Dict[str, Any] = None) -> str:
        """Create analysis prompt for image processing"""
        
        base_prompt = """
        Analyze this image from a document and extract the following information:

        1. **Image Type**: Classify the image (chart, diagram, signature, seal, photo, table, etc.)
        
        2. **Entities**: Extract any entities visible in the image:
           - PERSON: Names of people (signatures, titles, etc.)
           - ORGANIZATION: Company names, institutions
           - LOCATION: Places, addresses
           - DATE: Dates visible in the image
           - DOCUMENT_TYPE: Type of document or form
           - MEDICAL: Medical terms, procedures, conditions
           - LEGAL: Legal terms, case numbers, citations
           
        3. **Text Content**: Any readable text in the image
        
        4. **Key Visual Elements**: Describe important visual elements like:
           - Charts/graphs and their data
           - Diagrams and their components
           - Signatures and stamps
           - Logos and symbols
           - Medical images (X-rays, scans, etc.)
           
        5. **Relationships**: How this image relates to the document content
        
        Format your response as structured JSON:
        {
            "image_type": "chart|diagram|signature|seal|photo|table|medical|legal|other",
            "entities": [
                {
                    "text": "entity name",
                    "type": "PERSON|ORGANIZATION|LOCATION|DATE|MEDICAL|LEGAL|OTHER",
                    "confidence": 0.9,
                    "position": "description of where found"
                }
            ],
            "text_content": "all readable text in the image",
            "key_elements": ["element1", "element2", "element3"],
            "confidence": 0.8,
            "description": "detailed description of the image"
        }
        """
        
        if context:
            if context.get("page_number"):
                base_prompt += f"\n\nContext: This image is from page {context['page_number']} of the document."
            if context.get("document_section"):
                base_prompt += f" Section: {context['document_section']}"
        
        return base_prompt
    
    async def _extract_structured_data(self, analysis_text: str) -> Dict[str, Any]:
        """Extract structured data from analysis text"""
        
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                structured_data = json.loads(json_str)
                return structured_data
            else:
                # Fallback: parse text manually
                return self._parse_analysis_manually(analysis_text)
                
        except Exception as e:
            logger.warning("Failed to extract structured data", error=str(e))
            return self._parse_analysis_manually(analysis_text)
    
    def _parse_analysis_manually(self, analysis_text: str) -> Dict[str, Any]:
        """Manually parse analysis text when JSON extraction fails"""
        
        return {
            "image_type": "unknown",
            "entities": [],
            "text_content": analysis_text[:200],  # First 200 chars as text content
            "key_elements": [],
            "confidence": 0.5,
            "description": analysis_text
        }
    
    async def analyze_multiple_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple images concurrently"""
        
        if not images:
            return []
        
        logger.info("Starting batch image analysis", count=len(images))
        
        # Analyze images concurrently (but limit concurrency to avoid rate limits)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def analyze_single(image_info):
            async with semaphore:
                try:
                    image_data = image_info.get("image_data") or image_info.get("data")
                    context = {
                        "page_number": image_info.get("page_number"),
                        "document_section": image_info.get("document_section")
                    }
                    result = await self.analyze_image(image_data, context)
                    result["source_info"] = image_info
                    return result
                except Exception as e:
                    logger.error("Failed to analyze single image", error=str(e))
                    return {
                        "analysis": "",
                        "entities": [],
                        "image_type": "unknown",
                        "success": False,
                        "error": str(e),
                        "source_info": image_info
                    }
        
        # Process all images
        results = await asyncio.gather(
            *[analyze_single(img) for img in images],
            return_exceptions=True
        )
        
        # Filter out exceptions and failed analyses
        successful_results = [
            r for r in results 
            if isinstance(r, dict) and not isinstance(r, Exception)
        ]
        
        logger.info("Batch image analysis completed",
                   total=len(images),
                   successful=len(successful_results))
        
        return successful_results