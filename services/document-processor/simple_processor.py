"""
Simplified Document Processor for Testing OpenAI Integration
"""
import asyncio
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog
from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch

# Import our OpenAI entity extractor and LlamaParse
from processors.openai_entity_extractor import OpenAIEntityExtractor
from processors.llamaparse_processor import LlamaParseProcessor
from processors.legal_clause_extractor import LegalClauseExtractor
from processors.vector_embedder import VectorEmbedder

# Request models
class TextProcessRequest(BaseModel):
    text: str
    title: str = "Untitled Document"

# Setup logging
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Document Processor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
openai_entity_extractor = None
llamaparse_processor = None
legal_clause_extractor = None
vector_embedder = None
elasticsearch_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global openai_entity_extractor, llamaparse_processor, legal_clause_extractor, vector_embedder, elasticsearch_client
    
    logger.info("🚀 Starting Document Processor initialization...")
    
    try:
        # Get API keys from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info("Environment variables loaded", openai_api_key_available=bool(openai_api_key))
        
        # Initialize OpenAI entity extractor
        if openai_api_key:
            openai_entity_extractor = OpenAIEntityExtractor(
                api_key=openai_api_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4")
            )
            logger.info("OpenAI entity extractor initialized successfully")
        else:
            logger.warning("OpenAI API key not found, entity extraction will be disabled")

        # Initialize LlamaParse processor for multimodal processing
        llamaparse_api_key = os.getenv("LLAMAPARSE_API_KEY")
        if llamaparse_api_key:
            llamaparse_processor = LlamaParseProcessor(api_key=llamaparse_api_key)
            logger.info("LlamaParse processor initialized successfully")
        else:
            logger.warning("LLAMAPARSE_API_KEY not found, will use basic PDF extraction")

        # Initialize Legal Clause Extractor
        logger.info("Initializing Legal Clause Extractor...")
        if openai_api_key:
            try:
                legal_clause_extractor = LegalClauseExtractor(
                    api_key=openai_api_key,
                    model=os.getenv("OPENAI_MODEL", "gpt-4")
                )
                logger.info("✅ Legal clause extractor initialized successfully")
            except Exception as e:
                logger.error("❌ Failed to initialize legal clause extractor", error=str(e))
                legal_clause_extractor = None
        else:
            logger.warning("OpenAI API key not found, legal clause extraction will be disabled")

        # Initialize Vector Embedder
        logger.info("Initializing Vector Embedder...")
        if openai_api_key:
            try:
                vector_embedder = VectorEmbedder(
                    api_key=openai_api_key,
                    model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                    dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
                )
                logger.info("✅ Vector embedder initialized successfully")
            except Exception as e:
                logger.error("❌ Failed to initialize vector embedder", error=str(e))
                vector_embedder = None
        else:
            logger.warning("OpenAI API key not found, vector embedding will be disabled")

        # Initialize Elasticsearch client
        elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        elasticsearch_client = AsyncElasticsearch([elasticsearch_url])
        logger.info("Elasticsearch client initialized", url=elasticsearch_url)
            
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))

async def index_document_to_elasticsearch(filename: str, content: str, processed_data: dict, images: list, space_id: str = None):
    """Index processed document into Elasticsearch"""
    if not elasticsearch_client:
        return
    
    # Create document ID
    doc_id = f"upload_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    # Debug: Log content information
    logger.info("Indexing document to Elasticsearch",
               filename=filename,
               content_type=type(content).__name__,
               content_length=len(content),
               content_is_str=isinstance(content, str),
               content_preview=content[:100] if isinstance(content, str) else f"Binary data: {len(content)} bytes")
    
    # Create Elasticsearch document
    es_document = {
        "title": filename,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "file_type": "pdf" if filename.lower().endswith('.pdf') else "text",
        "ai_processed": True,
        "multimodal": processed_data.get("multimodal", False),
        "has_images": processed_data.get("has_images", False),
        "image_count": processed_data.get("image_count", 0),
        "extraction_method": processed_data.get("extraction_method", "basic"),
        "openai_entities": processed_data.get("entities", []),
        "openai_relationships": processed_data.get("relationships", []),
        "openai_key_concepts": processed_data.get("key_concepts", []),
        "openai_summary": processed_data.get("document_summary", ""),
        "document_insights": processed_data.get("document_insights", {}),
        "legal_clauses": processed_data.get("legal_clauses", []),
        "clause_contexts": processed_data.get("clause_contexts", []),
        "clause_count": processed_data.get("clause_count", 0),
        "legal_extraction_method": processed_data.get("legal_extraction_method", ""),
        "content_vector": processed_data.get("content_vector", []),
        "space_id": space_id,
        "metadata": {
            "processing_timestamp": datetime.now().isoformat(),
            "processing_method": processed_data.get("extraction_method", "basic"),
            "text_length": len(content),
            "has_images": len(images) > 0,
            "image_count": len(images),
            "space_id": space_id
        }
    }
    
    # Add image information if available
    if images:
        es_document["extracted_images"] = images
        es_document["image_metadata"] = [{"path": img.get("image_path", ""), "type": img.get("image_type", "unknown")} for img in images]
    
    try:
        # Index document
        await elasticsearch_client.index(
            index="documents",
            id=doc_id,
            body=es_document
        )
        logger.info("Document indexed successfully", doc_id=doc_id, filename=filename)
        
    except Exception as e:
        logger.error("Elasticsearch indexing failed", error=str(e), filename=filename)
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_available": openai_entity_extractor is not None,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/process-text")
async def process_text(request: TextProcessRequest):
    """Process text and extract entities using OpenAI"""
    try:
        if not openai_entity_extractor:
            raise HTTPException(status_code=503, detail="OpenAI entity extractor not available")
        
        logger.info("Processing text", title=request.title, text_length=len(request.text))
        
        # Extract entities and relationships
        results = await openai_entity_extractor.extract_entities_and_relationships(
            request.text, request.title
        )
        
        # Get document insights
        insights = await openai_entity_extractor.extract_document_insights(
            request.text, request.title
        )
        
        # Generate highlighted content
        highlighted_content = openai_entity_extractor.highlight_entities_in_text(
            request.text, results.get("entities", [])
        )
        
        # Add legal clause highlighting if available
        if legal_clause_extractor:
            try:
                legal_clauses_result = await legal_clause_extractor.extract_legal_clauses(
                    request.text, request.title
                )
                # Add legal clause highlighting to the content
                highlighted_content = legal_clause_extractor.highlight_clauses_in_text(
                    highlighted_content, legal_clauses_result.get("legal_clauses", [])
                )
            except Exception as e:
                logger.error("Legal clause highlighting failed", error=str(e))
        
        return {
            "title": request.title,
            "entities": results.get("entities", []),
            "relationships": results.get("relationships", []),
            "key_concepts": results.get("key_concepts", []),
            "document_summary": results.get("document_summary", ""),
            "highlighted_content": highlighted_content,
            "document_insights": insights,
            "processing_status": "completed"
        }
        
    except Exception as e:
        logger.error("Text processing failed", error=str(e), title=request.title)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-file")
async def process_file(
    file: UploadFile = File(...),
    space_id: str = Form(None)
):
    """Process uploaded file and extract entities"""
    try:
        if not openai_entity_extractor:
            raise HTTPException(status_code=503, detail="OpenAI entity extractor not available")
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        extracted_images = []
        
        if file.filename and file.filename.lower().endswith('.pdf'):
            # Use Official LLaVA + Whisper multimodal approach for PDF processing
            try:
                logger.info("Processing PDF with Official LLaVA multimodal extraction", filename=file.filename)
                
                # Try official LLaVA first, fallback to PyMuPDF if needed
                try:
                    from processors.official_llava_processor import get_official_llava_processor
                    
                    # Get official LLaVA processor instance
                    official_llava_processor = get_official_llava_processor()
                    
                    if official_llava_processor and official_llava_processor.initialized:
                        # Process PDF with official LLaVA multimodal analysis
                        result = official_llava_processor.process_pdf_multimodal(content, file.filename)
                        
                        text_content = result["text_content"]
                        extracted_images = result["extracted_images"]
                        
                        logger.info("Official LLaVA multimodal processing completed",
                                   filename=file.filename,
                                   text_length=len(text_content),
                                   images_count=len(extracted_images))
                    else:
                        raise Exception("Official LLaVA not available")
                        
                except Exception as llava_error:
                    logger.warning(f"Official LLaVA processing failed: {llava_error}")
                    logger.info("Falling back to PyMuPDF extraction")
                    
                    # Fallback to basic PyMuPDF extraction if LLaVA fails
                    try:
                        import fitz
                        pdf_doc = fitz.open(stream=content, filetype="pdf")
                        text_content = ""
                        for page_num, page in enumerate(pdf_doc):
                            page_text = page.get_text()
                            if page_text.strip():
                                text_content += f"=== PAGE {page_num + 1} ===\n\n"
                                text_content += page_text
                                text_content += f"\n\n---END PAGE {page_num + 1}---\n\n"
                        pdf_doc.close()
                        
                        logger.info("PyMuPDF fallback extraction completed",
                                   filename=file.filename,
                                   text_length=len(text_content))
                        
                        # If no meaningful text was extracted, provide a helpful message
                        if not text_content.strip():
                            text_content = f"PDF document '{file.filename}' processed. No extractable text content found."
                            
                    except Exception as fallback_error:
                        logger.error("Fallback extraction failed", 
                                   error=str(fallback_error), filename=file.filename)
                        text_content = f"Failed to extract content from PDF: {str(fallback_error)}"
                    
                    logger.info("LLaVA multimodal processing completed",
                               filename=file.filename,
                               text_length=len(text_content),
                               images_count=len(extracted_images))
                
                else:
                    logger.warning("LLaVA processor not available, falling back to PyMuPDF", filename=file.filename)
                    
                    # Fallback to basic PyMuPDF extraction
                    try:
                        import fitz
                        pdf_doc = fitz.open(stream=content, filetype="pdf")
                        text_content = ""
                        for page_num, page in enumerate(pdf_doc):
                            page_text = page.get_text()
                            if page_text.strip():
                                text_content += f"=== PAGE {page_num + 1} ===\n\n"
                                text_content += page_text
                                text_content += f"\n\n---END PAGE {page_num + 1}---\n\n"
                        pdf_doc.close()
                        
                        logger.info("PyMuPDF fallback extraction completed",
                                   filename=file.filename,
                                   text_length=len(text_content))
                        
                        # If no meaningful text was extracted, provide a helpful message
                        if not text_content.strip():
                            text_content = f"PDF document '{file.filename}' processed. No extractable text content found."
                            
                    except Exception as fallback_error:
                        logger.error("Fallback extraction failed", 
                                   error=str(fallback_error), filename=file.filename)
                        text_content = f"Failed to extract content from PDF: {str(fallback_error)}"
                        
            except Exception as e:
                logger.error("PDF processing failed", error=str(e), filename=file.filename)
                text_content = f"Failed to extract content from PDF: {str(e)}"
        else:
            # Handle text files
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be a text file or PDF")
        
        # Process the text with OpenAI
        request = TextProcessRequest(text=text_content, title=file.filename or "Uploaded File")
        text_result = await process_text(request)
        
        # Extract legal clauses if available
        legal_clauses_result = None
        if legal_clause_extractor:
            try:
                logger.info("Starting legal clause extraction", filename=file.filename)
                legal_clauses_result = await legal_clause_extractor.extract_legal_clauses(
                    text_content, file.filename or "Uploaded File"
                )
                logger.info("Legal clause extraction completed", 
                           filename=file.filename,
                           clause_count=legal_clauses_result.get("clause_count", 0))
            except Exception as e:
                logger.error("Legal clause extraction failed", error=str(e), filename=file.filename)
                legal_clauses_result = {
                    "legal_clauses": [],
                    "clause_contexts": [],
                    "clause_count": 0,
                    "error": str(e)
                }
        
        # Add multimodal information to the response
        text_result["extracted_images"] = extracted_images
        text_result["multimodal"] = len(extracted_images) > 0
        text_result["has_images"] = len(extracted_images) > 0
        text_result["image_count"] = len(extracted_images)
        text_result["extraction_method"] = "official_llava_multimodal" if len(extracted_images) > 0 else "official_llava_text_only"
        
        # Add legal clauses to the response
        if legal_clauses_result:
            text_result["legal_clauses"] = legal_clauses_result.get("legal_clauses", [])
            text_result["clause_contexts"] = legal_clauses_result.get("clause_contexts", [])
            text_result["clause_count"] = legal_clauses_result.get("clause_count", 0)
            text_result["legal_extraction_method"] = "legal_clause_extractor"

        # Generate vector embedding if available
        if vector_embedder:
            try:
                logger.info("Generating vector embedding", filename=file.filename)
                content_vector = await vector_embedder.embed_text(text_content)
                text_result["content_vector"] = content_vector
                logger.info("Vector embedding generated successfully", 
                           filename=file.filename,
                           embedding_dimensions=len(content_vector))
            except Exception as e:
                logger.error("Vector embedding generation failed", error=str(e), filename=file.filename)
                text_result["content_vector"] = []
        
        # Index the document into Elasticsearch
        if elasticsearch_client:
            try:
                await index_document_to_elasticsearch(file.filename, text_content, text_result, extracted_images, space_id)
                logger.info("Document indexed to Elasticsearch successfully", filename=file.filename, space_id=space_id)
            except Exception as e:
                logger.error("Failed to index document to Elasticsearch", error=str(e), filename=file.filename, space_id=space_id)
        
        return text_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File processing failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "simple_processor:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )