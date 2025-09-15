"""
LlamaParse processor for intelligent document parsing
"""

import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

try:
    from llama_parse import LlamaParse
    LLAMAPARSE_AVAILABLE = True
except ImportError:
    LLAMAPARSE_AVAILABLE = False
    structlog.get_logger(__name__).warning("LlamaParse not available, falling back to basic extraction")

logger = structlog.get_logger(__name__)


class LlamaParseProcessor:
    """Intelligent document parsing using LlamaParse"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.parser = None
        
        if LLAMAPARSE_AVAILABLE and api_key:
            try:
                self.parser = LlamaParse(
                    api_key=api_key,
                    result_type="markdown",  # markdown or text
                    verbose=True,
                    language="en",
                    # Enable image extraction for multimodal processing
                    image_extraction=True,
                    split_by_page=True,
                    parsing_instruction="""
                    Extract all text content while preserving structure and meaning.
                    Pay special attention to:
                    - Legal citations and references
                    - Names of people and organizations
                    - Dates and locations
                    - Tables and structured data
                    - Headers and section titles
                    - Charts, diagrams, and visual elements
                    - Signatures and stamps
                    
                    For images: Extract and describe all visual content including:
                    - Charts and graphs
                    - Diagrams and flowcharts
                    - Signatures and seals
                    - Medical images or X-rays
                    - Legal stamps and watermarks
                    
                    Maintain original formatting where possible.
                    """
                )
                logger.info("LlamaParse initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize LlamaParse", error=str(e))
                self.parser = None
        else:
            logger.warning("LlamaParse not available or no API key provided")
    
    async def parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Parse PDF using LlamaParse with intelligent extraction including images"""
        
        if not self.parser:
            raise Exception("LlamaParse not available or not properly initialized")
        
        try:
            logger.info("Starting LlamaParse multimodal processing", file_path=str(file_path))
            
            # Parse document with image extraction
            documents = await asyncio.to_thread(
                self.parser.load_data, str(file_path)
            )
            
            if not documents:
                raise Exception("No content extracted from document")
            
            # Combine all document text and extract images
            full_text = ""
            extracted_images = []
            metadata = {
                "pages_extracted": len(documents),
                "parsing_method": "llamaparse_multimodal",
                "extraction_quality": "high",
                "has_images": False,
                "image_count": 0
            }
            
            for i, doc in enumerate(documents):
                if hasattr(doc, 'text'):
                    full_text += doc.text
                    if i < len(documents) - 1:
                        full_text += "\n\n---PAGE BREAK---\n\n"
                
                # Extract images if available
                if hasattr(doc, 'metadata') and doc.metadata:
                    page_metadata = doc.metadata
                    
                    # Check for images in metadata
                    if 'images' in page_metadata:
                        for img_data in page_metadata['images']:
                            extracted_images.append({
                                "page_number": i + 1,
                                "image_data": img_data,
                                "extraction_method": "llamaparse",
                                "document_section": f"page_{i+1}"
                            })
                    
                    # Update metadata
                    metadata.update(page_metadata)
                
                # Also check for base64 encoded images in text
                if hasattr(doc, 'extra_info') and doc.extra_info:
                    if 'images' in doc.extra_info:
                        for img_info in doc.extra_info['images']:
                            extracted_images.append({
                                "page_number": i + 1,
                                "image_info": img_info,
                                "extraction_method": "llamaparse_extra",
                                "document_section": f"page_{i+1}"
                            })
            
            # Update metadata with image information
            if extracted_images:
                metadata["has_images"] = True
                metadata["image_count"] = len(extracted_images)
                logger.info("Extracted images from document", 
                          count=len(extracted_images), 
                          file_path=str(file_path))
            
            # Post-process the text
            processed_text = self._post_process_text(full_text)
            
            # Extract structure information
            structure_info = self._extract_structure(processed_text)
            metadata.update(structure_info)
            
            result = {
                "text": processed_text,
                "images": extracted_images,  # New: Include extracted images
                "metadata": metadata,
                "extraction_method": "llamaparse_multimodal",
                "success": True
            }
            
            logger.info("LlamaParse multimodal processing completed", 
                       text_length=len(processed_text),
                       pages=metadata["pages_extracted"])
            
            return result
            
        except Exception as e:
            logger.error("LlamaParse processing failed", error=str(e), file_path=str(file_path))
            
            # Return error info for fallback processing
            return {
                "text": "",
                "metadata": {
                    "extraction_method": "llamaparse",
                    "error": str(e),
                    "success": False
                },
                "extraction_method": "llamaparse",
                "success": False
            }
    
    def _post_process_text(self, text: str) -> str:
        """Post-process extracted text for better quality"""
        
        if not text:
            return ""
        
        # Basic cleanup
        processed = text.strip()
        
        # Remove excessive whitespace
        import re
        processed = re.sub(r'\n\s*\n\s*\n', '\n\n', processed)
        processed = re.sub(r' +', ' ', processed)
        
        # Fix common extraction issues
        processed = processed.replace('�', '')  # Remove replacement characters
        processed = processed.replace('\x00', '')  # Remove null characters
        
        # Normalize line endings
        processed = processed.replace('\r\n', '\n').replace('\r', '\n')
        
        return processed
    
    def _extract_structure(self, text: str) -> Dict[str, Any]:
        """Extract structural information from the text"""
        
        structure = {
            "estimated_pages": 0,
            "has_tables": False,
            "has_headers": False,
            "section_count": 0,
            "paragraph_count": 0,
            "estimated_reading_time": 0
        }
        
        if not text:
            return structure
        
        # Estimate pages (assuming ~500 words per page)
        word_count = len(text.split())
        structure["estimated_pages"] = max(1, word_count // 500)
        
        # Estimate reading time (250 words per minute)
        structure["estimated_reading_time"] = max(1, word_count // 250)
        
        # Count paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        structure["paragraph_count"] = len(paragraphs)
        
        # Check for tables (look for table indicators)
        table_indicators = ['|', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
        structure["has_tables"] = any(indicator in text for indicator in table_indicators)
        
        # Check for headers (look for numbered sections, caps, etc.)
        import re
        header_patterns = [
            r'^\d+\.\s+[A-Z][A-Za-z\s]+$',  # "1. HEADER"
            r'^[A-Z\s]+$',  # "ALL CAPS HEADER"
            r'^\s*#{1,6}\s+',  # Markdown headers
        ]
        
        lines = text.split('\n')
        header_count = 0
        section_count = 0
        
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 100:  # Reasonable header length
                for pattern in header_patterns:
                    if re.match(pattern, line, re.MULTILINE):
                        header_count += 1
                        if pattern.startswith(r'^\d+'):  # Numbered sections
                            section_count += 1
                        break
        
        structure["has_headers"] = header_count > 0
        structure["section_count"] = section_count
        
        return structure
    
    async def parse_with_custom_instruction(
        self, 
        file_path: Path, 
        custom_instruction: str
    ) -> Dict[str, Any]:
        """Parse document with custom parsing instructions"""
        
        if not self.parser:
            raise Exception("LlamaParse not available")
        
        # Create a new parser instance with custom instruction
        custom_parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            verbose=True,
            language="en",
            parsing_instruction=custom_instruction
        )
        
        try:
            logger.info("Starting custom LlamaParse processing", 
                       file_path=str(file_path),
                       instruction=custom_instruction[:100] + "...")
            
            documents = await asyncio.to_thread(
                custom_parser.load_data, str(file_path)
            )
            
            if not documents:
                raise Exception("No content extracted from document")
            
            # Process results
            full_text = ""
            for doc in documents:
                if hasattr(doc, 'text'):
                    full_text += doc.text + "\n\n"
            
            return {
                "text": self._post_process_text(full_text),
                "metadata": {
                    "parsing_method": "llamaparse_custom",
                    "custom_instruction": custom_instruction,
                    "pages_extracted": len(documents),
                    "extraction_quality": "high"
                },
                "extraction_method": "llamaparse_custom",
                "success": True
            }
            
        except Exception as e:
            logger.error("Custom LlamaParse processing failed", error=str(e))
            return {
                "text": "",
                "metadata": {"error": str(e), "success": False},
                "extraction_method": "llamaparse_custom",
                "success": False
            }
    
    def is_available(self) -> bool:
        """Check if LlamaParse is available and properly configured"""
        return self.parser is not None
    
    async def get_parsing_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a parsing job (if supported by LlamaParse)"""
        # This would be used for async parsing jobs
        # Implementation depends on LlamaParse API capabilities
        return {"status": "not_implemented"}
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return [
            "pdf",
            "docx", 
            "doc",
            "pptx",
            "ppt",
            "xlsx",
            "xls",
            "txt",
            "rtf"
        ]
    
    async def batch_parse(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """Parse multiple documents in batch"""
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.parse_pdf(file_path)
                results.append({
                    "file_path": str(file_path),
                    "result": result,
                    "success": result.get("success", False)
                })
            except Exception as e:
                results.append({
                    "file_path": str(file_path),
                    "result": {"error": str(e), "success": False},
                    "success": False
                })
        
        return results