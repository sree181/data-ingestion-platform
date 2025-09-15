"""
Official LLaVA Multimodal Processor
===================================

This processor implements the official LLaVA repository approach for multimodal processing
using the methods you suggested:

- llava.model.builder.load_pretrained_model
- llava.mm_utils.get_model_name_from_path  
- llava.eval.run_llava.eval_model

This provides direct access to the official LLaVA implementation for optimal performance
and compatibility with the latest model versions.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import torch
import fitz  # PyMuPDF
import base64
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logger = logging.getLogger(__name__)

class OfficialLLaVAProcessor:
    """
    Multimodal processor using the official LLaVA repository implementation
    """
    
    def __init__(self):
        """Initialize the official LLaVA processor"""
        self.tokenizer = None
        self.model = None
        self.image_processor = None
        self.context_len = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        
        logger.info(f"Official LLaVA Processor initializing on {self.device}")
        self._initialize_llava()
    
    def _initialize_llava(self):
        """Initialize LLaVA using the official repository methods"""
        try:
            # Import official LLaVA modules
            from llava.model.builder import load_pretrained_model
            from llava.mm_utils import get_model_name_from_path
            
            # Use the model path you suggested
            model_path = "liuhaotian/llava-v1.5-7b"
            
            logger.info(f"Loading official LLaVA model: {model_path}")
            
            # Load the pretrained model using official LLaVA method
            self.tokenizer, self.model, self.image_processor, self.context_len = load_pretrained_model(
                model_path=model_path,
                model_base=None,
                model_name=get_model_name_from_path(model_path)
            )
            
            self.initialized = True
            logger.info(f"Official LLaVA model loaded successfully on {self.device}")
            logger.info(f"Context length: {self.context_len}")
            
        except ImportError as e:
            logger.error(f"Official LLaVA not installed: {e}")
            logger.warning("Install with: pip install git+https://github.com/haotian-liu/LLaVA.git")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize official LLaVA model: {e}")
            self.initialized = False
    
    def analyze_image_with_llava(self, image_path: str, prompt: str = None) -> str:
        """
        Analyze an image using official LLaVA eval_model function
        
        Args:
            image_path: Path to image file  
            prompt: Optional specific prompt for analysis
            
        Returns:
            str: LLaVA's analysis of the image
        """
        if not self.initialized:
            return "Official LLaVA model not available for image analysis"
        
        try:
            from llava.eval.run_llava import eval_model
            from llava.mm_utils import get_model_name_from_path
            
            # Default comprehensive analysis prompt
            if not prompt:
                prompt = """Analyze this image in detail. Describe:
1. Main objects, people, or subjects visible
2. Setting, background, and environment
3. Colors, lighting, and visual style  
4. Any text, numbers, charts, diagrams, or technical content
5. Relationships between elements
6. Scientific or technical information if present
7. Overall purpose and context of the image

Provide a comprehensive analysis useful for document understanding and entity extraction."""
            
            model_path = "liuhaotian/llava-v1.5-7b"
            
            # Create args object as suggested in your example
            args = type('Args', (), {
                "model_path": model_path,
                "model_base": None,
                "model_name": get_model_name_from_path(model_path),
                "query": prompt,
                "conv_mode": None,
                "image_file": image_path,
                "sep": ",",
                "temperature": 0.1,  # Low temperature for consistent analysis
                "top_p": None,
                "num_beams": 1,
                "max_new_tokens": 512
            })()
            
            logger.info(f"Analyzing image with official LLaVA: {image_path}")
            
            # Use the official eval_model function
            analysis_result = eval_model(args)
            
            logger.info(f"Official LLaVA analysis completed, length: {len(str(analysis_result))}")
            return str(analysis_result)
            
        except Exception as e:
            logger.error(f"Official LLaVA image analysis failed: {e}")
            return f"Error during official LLaVA analysis: {str(e)}"
    
    async def analyze_image_async(self, image_path: str, prompt: str = None) -> str:
        """
        Asynchronous wrapper for image analysis
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor, 
                self.analyze_image_with_llava, 
                image_path, 
                prompt
            )
        return result
    
    def extract_images_from_pdf(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract images from PDF using PyMuPDF and analyze with official LLaVA
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            List of dictionaries containing image information and LLaVA analysis
        """
        extracted_images = []
        
        try:
            # Open PDF from bytes
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                
                # Get image list from page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_doc, xref)
                        
                        # Convert to PIL Image
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("ppm")
                            pil_image = Image.open(io.BytesIO(img_data))
                        else:  # CMYK: convert to RGB first
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("ppm")
                            pil_image = Image.open(io.BytesIO(img_data))
                            pix1 = None
                        
                        # Save image to temporary file for LLaVA analysis
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                            pil_image.save(tmp_file.name, 'PNG')
                            image_path = tmp_file.name
                        
                        # Analyze image with official LLaVA
                        llava_analysis = self.analyze_image_with_llava(image_path)
                        
                        # Store image information
                        extracted_images.append({
                            "image_path": image_path,
                            "image_filename": f"page_{page_num + 1}_img_{img_index + 1}.png",
                            "page_number": page_num + 1,
                            "image_index": img_index,
                            "extraction_method": "official_llava",
                            "image_type": "extracted",
                            "llava_analysis": llava_analysis,
                            "width": pix.width,
                            "height": pix.height,
                            "size_bytes": len(img_data)
                        })
                        
                        logger.info(f"Extracted and analyzed image {img_index + 1} from page {page_num + 1}")
                        
                        # Clean up temp file
                        try:
                            os.unlink(image_path)
                        except:
                            pass
                        
                        pix = None  # Release memory
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract/analyze image {img_index} from page {page_num}: {e}")
                        continue
            
            pdf_doc.close()
            logger.info(f"Successfully extracted and analyzed {len(extracted_images)} images from PDF")
            
        except Exception as e:
            logger.error(f"PDF image extraction failed: {e}")
        
        return extracted_images
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            str: Extracted text content
        """
        try:
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            text_content = ""
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    text_content += f"=== PAGE {page_num + 1} ===\n\n"
                    text_content += page_text
                    text_content += f"\n\n---END PAGE {page_num + 1}---\n\n"
            
            pdf_doc.close()
            logger.info(f"Extracted text from PDF: {len(text_content)} characters")
            
            return text_content
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def process_pdf_multimodal(self, pdf_content: bytes, filename: str = "") -> Dict[str, Any]:
        """
        Process PDF with both text and image extraction using official LLaVA analysis
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Dict containing text content and official LLaVA analyzed images
        """
        logger.info(f"Starting official LLaVA multimodal PDF processing for {filename}")
        
        # Extract text
        text_content = self.extract_text_from_pdf(pdf_content)
        
        # Extract and analyze images with official LLaVA
        extracted_images = self.extract_images_from_pdf(pdf_content)
        
        # Combine image analyses into the text content for richer context
        if extracted_images:
            text_content += "\n\n=== OFFICIAL LLAVA IMAGE ANALYSIS SECTION ===\n\n"
            for i, img_info in enumerate(extracted_images):
                text_content += f"Image {i + 1} (Page {img_info['page_number']}) - Official LLaVA Analysis:\n"
                text_content += img_info['llava_analysis'] + "\n\n"
        
        result = {
            "text_content": text_content,
            "extracted_images": extracted_images,
            "has_images": len(extracted_images) > 0,
            "image_count": len(extracted_images),
            "extraction_method": "official_llava_multimodal",
            "text_length": len(text_content),
            "processing_status": "completed",
            "llava_version": "official_v1.5-7b"
        }
        
        logger.info(f"Official LLaVA multimodal processing completed for {filename}: "
                   f"{len(text_content)} chars, {len(extracted_images)} images")
        
        return result


def get_official_llava_processor() -> Optional[OfficialLLaVAProcessor]:
    """
    Factory function to get official LLaVA processor instance
    
    Returns:
        OfficialLLaVAProcessor instance or None if initialization fails
    """
    try:
        return OfficialLLaVAProcessor()
    except Exception as e:
        logger.error(f"Failed to create official LLaVA processor: {e}")
        return None