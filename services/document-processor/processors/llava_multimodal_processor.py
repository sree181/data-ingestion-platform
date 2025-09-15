"""
LLaVA + Whisper Multimodal Processor
=====================================

This processor implements the LLaVA (Large Language and Vision Assistant) + Whisper approach
for multimodal document processing, avoiding complex dependencies while providing robust
image and text analysis capabilities.

Architecture:
- LLaVA: For image understanding and visual question answering
- Whisper: For audio transcription (future audio support)
- PyMuPDF: For PDF text and image extraction
- Integration with existing OpenAI entity extraction
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import torch
from transformers import BitsAndBytesConfig, pipeline
import fitz  # PyMuPDF
import base64
import io

# Set up logging
logger = logging.getLogger(__name__)

class LLaVAMultimodalProcessor:
    """
    Multimodal processor using LLaVA for image understanding and PyMuPDF for PDF processing
    """
    
    def __init__(self):
        """Initialize the LLaVA multimodal processor"""
        self.llava_pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        
        logger.info(f"LLaVA Multimodal Processor initializing on {self.device}")
        self._initialize_llava()
    
    def _initialize_llava(self):
        """Initialize the LLaVA model pipeline with quantization"""
        try:
            if self.device == "cuda" and torch.cuda.is_available():
                # GPU configuration with quantization
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
                model_kwargs = {"quantization_config": quant_config}
                device = 0
                logger.info("Initializing LLaVA with GPU and quantization")
            else:
                # CPU configuration - no quantization needed
                model_kwargs = {"torch_dtype": torch.float32}
                device = -1
                logger.info("Initializing LLaVA in CPU mode for demo compatibility")
            
            # Use LLaVA 1.5 7B model (good balance of performance and size)
            model_id = "llava-hf/llava-1.5-7b-hf"
            
            logger.info(f"Loading LLaVA model: {model_id}")
            
            # Initialize the image-to-text pipeline
            self.llava_pipeline = pipeline(
                "image-to-text",
                model=model_id,
                model_kwargs=model_kwargs,
                device=device
            )
            
            self.initialized = True
            logger.info(f"LLaVA model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLaVA model: {e}")
            logger.warning("LLaVA will not be available for image analysis - using enhanced PyMuPDF fallback")
            self.initialized = False
    
    def analyze_image_with_llava(self, image: Image.Image, prompt: str = None) -> str:
        """
        Analyze an image using LLaVA model
        
        Args:
            image: PIL Image object
            prompt: Optional specific prompt for analysis
            
        Returns:
            str: LLaVA's analysis of the image
        """
        if not self.initialized:
            return "LLaVA model not available for image analysis"
        
        try:
            # Default comprehensive analysis prompt
            if not prompt:
                prompt_instructions = """
                Act as an expert in imagery descriptive analysis. Using as much detail as possible from the image, 
                describe what you see. Include:
                1. Main objects, people, or subjects in the image
                2. Setting, background, and environment
                3. Colors, lighting, and visual style
                4. Any text, numbers, charts, or diagrams visible
                5. Relationships between elements
                6. Scientific or technical content if present
                
                Provide a comprehensive analysis that would be useful for document understanding and entity extraction.
                """
            else:
                prompt_instructions = prompt
            
            # Format prompt for LLaVA
            full_prompt = "USER: <image>\n" + prompt_instructions + "\nASSISTANT:"
            
            # Generate analysis
            outputs = self.llava_pipeline(
                image, 
                prompt=full_prompt, 
                generate_kwargs={"max_new_tokens": 300, "do_sample": True, "temperature": 0.7}
            )
            
            # Extract the response
            if outputs and len(outputs) > 0 and "generated_text" in outputs[0]:
                generated_text = outputs[0]["generated_text"]
                
                # Extract text after "ASSISTANT:"
                if "ASSISTANT:" in generated_text:
                    analysis = generated_text.split("ASSISTANT:")[-1].strip()
                else:
                    analysis = generated_text.strip()
                
                logger.info(f"LLaVA analysis completed, length: {len(analysis)}")
                return analysis
            else:
                return "No analysis generated by LLaVA"
                
        except Exception as e:
            logger.error(f"LLaVA image analysis failed: {e}")
            return f"Error during image analysis: {str(e)}"
    
    def extract_images_from_pdf(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract images from PDF using PyMuPDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            List of dictionaries containing image information
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
                        
                        # Save image to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                            pil_image.save(tmp_file.name, 'PNG')
                            image_path = tmp_file.name
                        
                        # Analyze image with LLaVA
                        llava_analysis = self.analyze_image_with_llava(pil_image)
                        
                        # Store image information
                        extracted_images.append({
                            "image_path": image_path,
                            "image_filename": f"page_{page_num + 1}_img_{img_index + 1}.png",
                            "page_number": page_num + 1,
                            "image_index": img_index,
                            "extraction_method": "pymupdf_llava",
                            "image_type": "extracted",
                            "llava_analysis": llava_analysis,
                            "width": pix.width,
                            "height": pix.height,
                            "size_bytes": len(img_data)
                        })
                        
                        logger.info(f"Extracted and analyzed image {img_index + 1} from page {page_num + 1}")
                        
                        pix = None  # Release memory
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                        continue
            
            pdf_doc.close()
            logger.info(f"Successfully extracted {len(extracted_images)} images from PDF")
            
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
        Process PDF with both text and image extraction using LLaVA analysis
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Dict containing text content and analyzed images
        """
        logger.info(f"Starting multimodal PDF processing for {filename}")
        
        # Extract text
        text_content = self.extract_text_from_pdf(pdf_content)
        
        # Extract and analyze images
        extracted_images = self.extract_images_from_pdf(pdf_content)
        
        # Combine image analyses into the text content for richer context
        if extracted_images:
            text_content += "\n\n=== IMAGE ANALYSIS SECTION ===\n\n"
            for i, img_info in enumerate(extracted_images):
                text_content += f"Image {i + 1} (Page {img_info['page_number']}):\n"
                text_content += img_info['llava_analysis'] + "\n\n"
        
        result = {
            "text_content": text_content,
            "extracted_images": extracted_images,
            "has_images": len(extracted_images) > 0,
            "image_count": len(extracted_images),
            "extraction_method": "llava_multimodal",
            "text_length": len(text_content),
            "processing_status": "completed"
        }
        
        logger.info(f"Multimodal processing completed for {filename}: "
                   f"{len(text_content)} chars, {len(extracted_images)} images")
        
        return result


def get_llava_processor() -> Optional[LLaVAMultimodalProcessor]:
    """
    Factory function to get LLaVA processor instance
    
    Returns:
        LLaVAMultimodalProcessor instance or None if initialization fails
    """
    try:
        return LLaVAMultimodalProcessor()
    except Exception as e:
        logger.error(f"Failed to create LLaVA processor: {e}")
        return None