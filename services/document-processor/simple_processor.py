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
from processors.multi_model_entity_extractor import MultiModelEntityExtractor
from models.ai_models import model_registry, model_factory
from processors.llamaparse_processor import LlamaParseProcessor
from processors.legal_clause_extractor import LegalClauseExtractor
from processors.vector_embedder import VectorEmbedder

# Request models
class TextProcessRequest(BaseModel):
    text: str
    title: str = "Untitled Document"
    model_name: str = "gpt-4"  # Default to GPT-4

class PubMedArticleRequest(BaseModel):
    title: str
    content: str
    metadata: dict
    medical_entities: list = []
    space_id: str

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
multi_model_extractor = None
llamaparse_processor = None
legal_clause_extractor = None
vector_embedder = None
elasticsearch_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global openai_entity_extractor, multi_model_extractor, llamaparse_processor, legal_clause_extractor, vector_embedder, elasticsearch_client
    
    logger.info("🚀 Starting Document Processor initialization...")
    
    try:
        # Get API keys from environment
        openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info("Environment variables loaded", openai_api_key_available=bool(openai_api_key))
        
        # Initialize multi-model entity extractor with phi3:mini (local, no API key needed)
        multi_model_extractor = MultiModelEntityExtractor(
            model_name="phi3:mini",  # Use local phi3:mini model
            api_key=openai_api_key,  # Optional, only needed for OpenAI models
            base_url="http://ollama:11434"  # Ollama service URL in Docker network
        )
        await multi_model_extractor.initialize()
        logger.info("Multi-model entity extractor initialized successfully", model="phi3:mini")
        
        # Also initialize OpenAI extractor if API key available
        if openai_api_key:
            logger.info("OpenAI API key available, can also use OpenAI models")

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
    # Clean null values from processed_data
    entities = processed_data.get("entities")
    if entities is None:
        entities = []
    relationships = processed_data.get("relationships")
    if relationships is None:
        relationships = []
    key_concepts = processed_data.get("key_concepts")
    if key_concepts is None:
        key_concepts = []
    document_summary = processed_data.get("document_summary")
    if document_summary is None:
        document_summary = ""
    document_insights = processed_data.get("document_insights")
    if document_insights is None:
        document_insights = {}
    
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
        "openai_entities": entities,
        "openai_relationships": relationships,
        "openai_key_concepts": key_concepts,
        "openai_summary": document_summary,
        "document_insights": document_insights,
        "legal_clauses": processed_data.get("legal_clauses", []),
        "clause_contexts": processed_data.get("clause_contexts", []),
        "clause_count": processed_data.get("clause_count", 0),
        "legal_extraction_method": processed_data.get("legal_extraction_method", ""),
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
    
    # Add content_vector only if it exists and has valid dimensions
    content_vector = processed_data.get("content_vector", [])
    if content_vector and len(content_vector) > 0:
        es_document["content_vector"] = content_vector
    
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

@app.get("/api/v1/models/available")
async def get_available_models():
    """Get list of available AI models"""
    try:
        models = model_registry.list_models()
        model_list = []
        
        for model in models:
            model_info = {
                "name": model.name,
                "provider": model.provider.value,
                "capabilities": [cap.value for cap in model.capabilities],
                "max_tokens": model.max_tokens,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "description": model.description,
                "is_local": model.is_local,
                "requires_api_key": model.requires_api_key
            }
            model_list.append(model_info)
        
        logger.info("Available models retrieved", count=len(model_list))
        return {"models": model_list}
        
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve available models")

@app.post("/api/v1/models/test/{model_name}")
async def test_model(model_name: str, request: dict):
    """Test if a model is available and working"""
    try:
        # Get model info from registry
        model_info = model_registry.get_model(model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")
        
        # Create model instance using factory
        api_key = os.getenv("OPENAI_API_KEY") if model_info.provider.value == "openai" else None
        base_url = "http://ollama:11434" if model_info.provider.value == "ollama" else None
        
        model_instance = await model_factory.create_model(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        )
        
        if not model_instance:
            raise HTTPException(status_code=503, detail=f"Failed to initialize model '{model_name}'.")
        
        # Test with a simple prompt
        test_prompt = "Hello, this is a test. Please respond with 'Model is working'."
        try:
            response = await model_instance.generate_text(test_prompt, max_tokens=50)
            
            logger.info("Model test successful", model=model_name, response=response[:100])
            return {
                "success": True,
                "message": "Model is working correctly",
                "test_response": response[:200],
                "model_info": {
                    "name": model_instance.model_info.name,
                    "provider": model_instance.model_info.provider.value,
                    "is_local": model_instance.model_info.is_local
                }
            }
        except Exception as test_error:
            logger.error("Model test failed", model=model_name, error=str(test_error))
            return {
                "success": False,
                "message": f"Model test failed: {str(test_error)}",
                "model_info": {
                    "name": model_instance.model_info.name,
                    "provider": model_instance.model_info.provider.value,
                    "is_local": model_instance.model_info.is_local
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Model test error", model=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")

@app.post("/process-text")
async def process_text(request: TextProcessRequest):
    """Process text and extract entities using selected model"""
    try:
        # Determine base_url for Ollama models (Phi3, Llama)
        base_url = None
        if any(keyword in request.model_name.lower() for keyword in ["phi3", "llama"]):
            base_url = "http://ollama:11434"
        
        # Initialize multi-model extractor
        multi_model_extractor = MultiModelEntityExtractor(
            model_name=request.model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=base_url
        )
        
        if not await multi_model_extractor.initialize():
            raise HTTPException(status_code=503, detail=f"Failed to initialize model: {request.model_name}")
        
        logger.info("Processing text", title=request.title, text_length=len(request.text), model=request.model_name)
        
        # Extract entities and relationships
        results = await multi_model_extractor.extract_entities_and_relationships(
            request.text, request.title
        )
        
        # Get document insights
        insights = await multi_model_extractor.extract_document_insights(
            request.text, request.title
        )
        
        # Generate highlighted content
        highlighted_content = multi_model_extractor.highlight_entities_in_text(
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
            "processing_status": "completed",
            "model_metadata": {
                "model_name": request.model_name,
                "provider": multi_model_extractor.model.model_info.provider.value if multi_model_extractor.model else "unknown",
                "is_local": multi_model_extractor.model.model_info.is_local if multi_model_extractor.model else False
            }
        }
        
    except Exception as e:
        logger.error("Text processing failed", error=str(e), title=request.title)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-file")
async def process_file(
    file: UploadFile = File(...),
    space_id: str = Form(None),
    model: str = Form("phi3:mini")  # Accept model parameter, default to phi3:mini
):
    """Process uploaded file and extract entities"""
    try:
        logger.info("Received file processing request", filename=file.filename, space_id=space_id, model=model)
        
        if not multi_model_extractor and not openai_entity_extractor:
            raise HTTPException(status_code=503, detail="No AI model available for entity extraction")
        
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
        
        # Process the text with the selected model
        text_request = TextProcessRequest(
            text=text_content, 
            title=file.filename or "Uploaded File",
            model_name=model  # Use the model parameter from the form
        )
        text_result = await process_text(text_request)
        
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
                # Don't set content_vector if it fails - let the indexing function handle it
        
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

@app.post("/process-external-document")
async def process_external_document(request: dict):
    """Process external document from multi-source ingestion"""
    try:
        logger.info("Processing external document", 
                   title=request.get("title"), 
                   source=request.get("source"),
                   document_type=request.get("document_type"))
        
        # Process text with AI analysis
        text_result = await process_text(TextProcessRequest(
            text=request.get("content", ""),
            title=request.get("title", ""),
            model_name=request.get("model_name", "phi3:mini")
        ))
        
        # Add source-specific metadata
        text_result["source"] = request.get("source")
        text_result["source_id"] = request.get("source_id")
        text_result["document_type"] = request.get("document_type")
        text_result["external_source"] = True
        text_result["extraction_method"] = "multi_source_external"
        
        # Add additional metadata from request
        text_result["url"] = request.get("url")
        text_result["doi"] = request.get("doi")
        text_result["pmid"] = request.get("pmid")
        text_result["pmcid"] = request.get("pmcid")
        text_result["publication_date"] = request.get("publication_date")
        text_result["authors"] = request.get("authors", [])
        text_result["keywords"] = request.get("keywords", [])
        
        # NOTE: We do NOT index here - the ingestion service will index with all metadata
        # This allows the ingestion service to combine AI results with full document metadata
        
        logger.info("External document processed successfully with AI analysis", 
                   title=request.get("title"),
                   entities_count=len(text_result.get("entities", [])),
                   relationships_count=len(text_result.get("relationships", [])))
        
        return text_result
        
    except Exception as e:
        logger.error("External document processing failed", 
                    error=str(e), 
                    title=request.get("title"))
        raise HTTPException(status_code=500, detail=f"External document processing failed: {str(e)}")

@app.post("/process-pubmed-article")
async def process_pubmed_article(request: PubMedArticleRequest):
    """Process PubMed article with medical concept extraction"""
    try:
        logger.info("Processing PubMed article", title=request.title, pmid=request.metadata.get("pmid"))
        
        # Process text with OpenAI entity extraction
        text_result = await process_text(TextProcessRequest(
            text=request.content,
            title=request.title
        ))
        
        # Add medical entities to the result
        if request.medical_entities:
            text_result["medical_entities"] = request.medical_entities
            text_result["medical_concept_count"] = len(request.medical_entities)
            
            # Categorize medical concepts by type
            concept_types = {}
            for entity in request.medical_entities:
                concept_type = entity.get("type", "UNKNOWN")
                if concept_type not in concept_types:
                    concept_types[concept_type] = []
                concept_types[concept_type].append(entity)
            
            text_result["medical_concept_types"] = concept_types
        
        # Add PubMed metadata
        text_result["pubmed_metadata"] = request.metadata
        text_result["source"] = "pubmed"
        text_result["document_type"] = "research_article"
        
        # Generate vector embedding if available
        if vector_embedder:
            try:
                logger.info("Generating vector embedding for PubMed article", title=request.title)
                content_vector = await vector_embedder.embed_text(request.content)
                text_result["content_vector"] = content_vector
                logger.info("Vector embedding generated successfully", 
                           title=request.title,
                           embedding_dimensions=len(content_vector))
            except Exception as e:
                logger.error("Vector embedding generation failed", error=str(e), title=request.title)
                # Don't set content_vector if it fails - let the indexing function handle it
        
        # Index the document into Elasticsearch
        if elasticsearch_client:
            try:
                await index_document_to_elasticsearch(
                    request.title, 
                    request.content, 
                    text_result, 
                    [],  # No images for PubMed articles
                    request.space_id
                )
                logger.info("PubMed article indexed to Elasticsearch successfully", 
                           title=request.title, 
                           space_id=request.space_id)
            except Exception as e:
                logger.error("Failed to index PubMed article to Elasticsearch", 
                           error=str(e), 
                           title=request.title, 
                           space_id=request.space_id)
        
        return text_result
        
    except Exception as e:
        logger.error("PubMed article processing failed", error=str(e), title=request.title)
        raise HTTPException(status_code=500, detail=f"PubMed article processing failed: {str(e)}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "simple_processor:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )