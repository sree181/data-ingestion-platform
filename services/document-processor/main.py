"""
Document Processing Service with LlamaParse Integration
Handles document ingestion, parsing, entity extraction, and indexing
"""

import asyncio
import json
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import structlog
from kafka import KafkaConsumer, KafkaProducer
from minio import Minio
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase

# Inline config for now to avoid import issues
import os
from typing import Optional

class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/data_platform")
        
        # MinIO settings
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "documents")
        
        # Elasticsearch settings
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        
        # Kafka settings
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        
        # Neo4j settings
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
        
        # LlamaParse settings
        self.llamaparse_api_key = os.getenv("LLAMAPARSE_API_KEY")
        self.use_llamaparse = os.getenv("USE_LLAMAPARSE", "true").lower() == "true"
        
        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Service settings
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8001"))
        self.minio_secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Processing settings
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "100000000"))  # 100MB
        self.supported_formats = ["pdf", "docx", "doc", "txt", "rtf"]

# Imports - only import what we need
from processors.llamaparse_processor import LlamaParseProcessor
# from processors.text_extractor import TextExtractor
# from processors.entity_extractor import EntityExtractor
# from processors.vector_embedder import VectorEmbedder
from processors.openai_entity_extractor import OpenAIEntityExtractor
from processors.openai_vision_processor import OpenAIVisionProcessor
from storage.image_storage_manager import ImageStorageManager
# from database import DatabaseManager
# from utils.logging_config import setup_logging

# Simple logging setup
import logging
logging.basicConfig(level=logging.INFO)

# Setup logging
logger = structlog.get_logger(__name__)

# Global configuration
settings = Settings()

# Service clients
elasticsearch_client: Optional[AsyncElasticsearch] = None
neo4j_driver = None
minio_client: Optional[Minio] = None
database_manager: Optional[DatabaseManager] = None

# Processors
llamaparse_processor = None  # Will be initialized if available
text_extractor = None
entity_extractor = None  
vector_embedder = None
openai_entity_extractor: Optional[OpenAIEntityExtractor] = None
openai_vision_processor: Optional[OpenAIVisionProcessor] = None
image_storage_manager: Optional[ImageStorageManager] = None


class DocumentProcessor:
    """Main document processing orchestrator"""
    
    def __init__(self):
        self.kafka_consumer = None
        self.kafka_producer = None
        self.processing_stats = {
            "documents_processed": 0,
            "documents_failed": 0,
            "total_processing_time": 0,
            "start_time": datetime.utcnow()
        }
    
    async def initialize(self):
        """Initialize all services and processors"""
        global elasticsearch_client, neo4j_driver, minio_client, database_manager
        global llamaparse_processor, text_extractor, entity_extractor, vector_embedder
        global openai_entity_extractor, openai_vision_processor, image_storage_manager
        
        logger.info("Initializing Document Processing Service")
        
        try:
            # Initialize storage clients
            elasticsearch_client = AsyncElasticsearch([settings.elasticsearch_url])
            await elasticsearch_client.ping()
            
            neo4j_driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            await neo4j_driver.verify_connectivity()
            
            minio_client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            
            database_manager = DatabaseManager(settings.database_url)
            await database_manager.connect()
            
            # Initialize Kafka
            self.kafka_consumer = KafkaConsumer(
                'document_processing',
                bootstrap_servers=[settings.kafka_bootstrap_servers],
                auto_offset_reset='latest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id='document_processor'
            )
            
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=[settings.kafka_bootstrap_servers],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            # Initialize processors
            if settings.llamaparse_api_key:
                llamaparse_processor = LlamaParseProcessor(settings.llamaparse_api_key)
                logger.info("LlamaParse processor initialized")
            else:
                logger.warning("LlamaParse API key not provided")
            
            # Other processors will be initialized when needed
            # text_extractor = TextExtractor()
            # entity_extractor = EntityExtractor()
            # vector_embedder = VectorEmbedder()
            
            # Initialize OpenAI processors if API key is available
            if settings.openai_api_key:
                # Text entity extractor
                openai_entity_extractor = OpenAIEntityExtractor(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model
                )
                logger.info("OpenAI entity extractor initialized")
                
                # Vision processor for multimodal analysis
                openai_vision_processor = OpenAIVisionProcessor(
                    api_key=settings.openai_api_key,
                    model="gpt-4-vision-preview"
                )
                logger.info("OpenAI Vision processor initialized")
            else:
                logger.warning("OpenAI API key not provided, multimodal processing will be limited")
            
            # Initialize image storage manager
            if minio_client:
                image_storage_manager = ImageStorageManager(
                    minio_client=minio_client,
                    bucket_name=settings.minio_bucket
                )
                logger.info("Image storage manager initialized")
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize services", error=str(e))
            raise
    
    async def start_processing(self):
        """Start the document processing loop"""
        logger.info("Starting document processing loop")
        
        try:
            while True:
                # Poll for new messages
                message_batch = self.kafka_consumer.poll(timeout_ms=1000)
                
                if message_batch:
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            await self.process_document_message(message.value)
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except KeyboardInterrupt:
            logger.info("Shutting down document processor")
        except Exception as e:
            logger.error("Error in processing loop", error=str(e))
            raise
    
    async def process_document_message(self, message: Dict[str, Any]):
        """Process a single document processing message"""
        document_id = None
        start_time = datetime.utcnow()
        
        try:
            file_info = message["file_info"]
            user_id = message["user_id"]
            document_id = file_info["file_id"]
            
            logger.info("Processing document", document_id=document_id, filename=file_info["filename"])
            
            # Update status to processing
            await self.update_document_status(
                document_id, 
                "processing", 
                "Document processing started", 
                0
            )
            
            # Download file from MinIO
            file_path = await self.download_file(file_info)
            
            # Process the document through the pipeline
            processed_data = await self.process_document_pipeline(file_path, file_info, user_id)
            
            # Index in Elasticsearch
            await self.index_document(document_id, processed_data)
            
            # Create knowledge graph entities
            if processed_data.get("entities"):
                await self.create_knowledge_graph(document_id, processed_data)
            
            # Update status to completed
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_document_status(
                document_id, 
                "completed", 
                "Document processing completed successfully", 
                100,
                {"processing_time_seconds": processing_time}
            )
            
            # Update statistics
            self.processing_stats["documents_processed"] += 1
            self.processing_stats["total_processing_time"] += processing_time
            
            # Send completion notification
            self.kafka_producer.send('document_completed', {
                "document_id": document_id,
                "user_id": user_id,
                "processing_time": processing_time,
                "entities_extracted": len(processed_data.get("entities", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info("Document processing completed", 
                       document_id=document_id,
                       processing_time=processing_time)
            
        except Exception as e:
            # Update status to failed
            if document_id:
                await self.update_document_status(
                    document_id, 
                    "failed", 
                    f"Document processing failed: {str(e)}", 
                    0,
                    {"error": str(e)}
                )
            
            self.processing_stats["documents_failed"] += 1
            
            logger.error("Document processing failed", 
                        document_id=document_id, 
                        error=str(e))
    
    async def download_file(self, file_info: Dict[str, Any]) -> Path:
        """Download file from MinIO to local storage"""
        bucket = file_info["bucket"]
        object_name = file_info["object_name"]
        
        # Create local file path
        local_filename = f"/tmp/{uuid.uuid4()}_{file_info['filename']}"
        local_path = Path(local_filename)
        
        try:
            # Download from MinIO
            minio_client.fget_object(bucket, object_name, str(local_path))
            
            logger.debug("File downloaded", 
                        object_name=object_name, 
                        local_path=str(local_path))
            
            return local_path
            
        except Exception as e:
            logger.error("Failed to download file", error=str(e))
            raise
    
    async def process_document_pipeline(
        self, 
        file_path: Path, 
        file_info: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Run the document through the complete processing pipeline"""
        
        file_type = file_info.get("content_type", "").lower()
        filename = file_info["filename"]
        
        processed_data = {
            "title": Path(filename).stem,
            "content": "",
            "metadata": {
                "filename": filename,
                "file_type": file_type,
                "file_size": file_info.get("size", 0),
                "upload_date": file_info.get("uploaded_at"),
                "user_id": user_id,
                "processing_method": "unknown"
            },
            "entities": [],
            "content_vector": None,
            "tags": [],
            "categories": []
        }
        
        try:
            # Step 1: Extract text based on file type
            if "pdf" in file_type:
                if settings.use_llamaparse and settings.llamaparse_api_key:
                    # Use LlamaParse for intelligent PDF parsing
                    text_content = await llamaparse_processor.parse_pdf(file_path)
                    processed_data["metadata"]["processing_method"] = "llamaparse"
                else:
                    # Fallback to traditional PDF extraction
                    text_content = await text_extractor.extract_from_pdf(file_path)
                    processed_data["metadata"]["processing_method"] = "pymupdf"
            
            elif "word" in file_type or "document" in file_type:
                text_content = await text_extractor.extract_from_docx(file_path)
                processed_data["metadata"]["processing_method"] = "python-docx"
            
            elif "text" in file_type or "plain" in file_type:
                text_content = await text_extractor.extract_from_text(file_path)
                processed_data["metadata"]["processing_method"] = "direct"
            
            elif "html" in file_type:
                text_content = await text_extractor.extract_from_html(file_path)
                processed_data["metadata"]["processing_method"] = "beautifulsoup"
            
            else:
                # Try OCR for images or unknown formats
                text_content = await text_extractor.extract_with_ocr(file_path)
                processed_data["metadata"]["processing_method"] = "ocr"
            
            processed_data["content"] = text_content["text"]
            processed_data["metadata"].update(text_content.get("metadata", {}))
            
            # Step 1.5: Process extracted images (multimodal enhancement)
            extracted_images = text_content.get("images", [])
            image_entities = []
            image_metadata = []
            
            if extracted_images and openai_vision_processor and image_storage_manager:
                try:
                    logger.info("Processing extracted images", 
                               count=len(extracted_images), 
                               document=filename)
                    
                    # Store images in MinIO
                    stored_images = await image_storage_manager.store_document_images(
                        document_id=str(uuid.uuid4()),  # Will be updated with real document ID later
                        images=extracted_images,
                        document_metadata=processed_data["metadata"]
                    )
                    
                    # Analyze images with OpenAI Vision
                    if stored_images:
                        vision_results = await openai_vision_processor.analyze_multiple_images(extracted_images)
                        
                        # Aggregate image analysis results
                        for result in vision_results:
                            if result.get("success"):
                                image_entities.extend(result.get("entities", []))
                                image_metadata.append({
                                    "image_type": result.get("image_type"),
                                    "analysis": result.get("analysis"),
                                    "key_elements": result.get("key_elements", []),
                                    "text_content": result.get("text_content", ""),
                                    "confidence": result.get("confidence", 0.0)
                                })
                        
                        # Add multimodal metadata
                        processed_data["metadata"]["has_images"] = True
                        processed_data["metadata"]["image_count"] = len(extracted_images)
                        processed_data["metadata"]["processing_method"] += "_multimodal"
                        processed_data["image_metadata"] = image_metadata
                        processed_data["image_entities"] = image_entities
                        processed_data["stored_images"] = stored_images
                        
                        logger.info("Multimodal processing completed", 
                                   image_entities_found=len(image_entities),
                                   images_stored=len(stored_images))
                
                except Exception as img_error:
                    logger.error("Failed to process images", error=str(img_error))
                    processed_data["metadata"]["image_processing_error"] = str(img_error)
            
            # Step 2: Extract entities from text
            if processed_data["content"]:
                # Use OpenAI for enhanced entity extraction if available
                if openai_entity_extractor:
                    logger.info("Using OpenAI for entity extraction")
                    openai_results = await openai_entity_extractor.extract_entities_and_relationships(
                        processed_data["content"], 
                        document_title=filename
                    )
                    
                    # Store OpenAI results
                    processed_data["openai_entities"] = openai_results.get("entities", [])
                    processed_data["relationships"] = openai_results.get("relationships", [])
                    processed_data["key_concepts"] = openai_results.get("key_concepts", [])
                    processed_data["document_summary"] = openai_results.get("document_summary", "")
                    processed_data["highlighted_content"] = openai_entity_extractor.highlight_entities_in_text(
                        processed_data["content"], openai_results.get("entities", [])
                    )
                    
                    # Get document insights
                    insights = await openai_entity_extractor.extract_document_insights(
                        processed_data["content"], filename
                    )
                    processed_data["document_insights"] = insights
                    
                    logger.info("OpenAI entity extraction completed",
                               entities_count=len(openai_results.get("entities", [])),
                               relationships_count=len(openai_results.get("relationships", [])))
                
                # Fallback to traditional entity extraction
                entities = await entity_extractor.extract_entities(processed_data["content"])
                processed_data["entities"] = entities
                
                # Auto-categorize based on entities and OpenAI insights
                categories = self.categorize_document(entities, processed_data.get("document_insights", {}))
                processed_data["categories"] = categories
            
            # Step 3: Generate content embeddings
            content_vector = await vector_embedder.embed_text(
                processed_data["content"][:8000]  # Limit to first 8k chars
            )
            processed_data["content_vector"] = content_vector
            
            # Step 4: Extract key phrases as tags
            if processed_data["content"]:
                tags = await entity_extractor.extract_key_phrases(processed_data["content"])
                processed_data["tags"] = tags[:20]  # Limit to top 20 tags
            
            logger.info("Document pipeline completed", 
                       filename=filename,
                       entities_count=len(processed_data["entities"]),
                       content_length=len(processed_data["content"]))
            
            return processed_data
            
        except Exception as e:
            logger.error("Document pipeline failed", filename=filename, error=str(e))
            raise
        
        finally:
            # Clean up temporary file
            if file_path.exists():
                file_path.unlink()
    
    def categorize_document(self, entities: List[Dict[str, Any]], insights: Dict[str, Any] = None) -> List[str]:
        """Auto-categorize document based on extracted entities"""
        categories = set()
        
        # Entity type based categorization
        entity_types = [entity["type"] for entity in entities]
        
        if "PERSON" in entity_types:
            categories.add("people")
        if any(t in entity_types for t in ["ORG", "ORGANIZATION"]):
            categories.add("organizations")
        if any(t in entity_types for t in ["GPE", "LOCATION"]):
            categories.add("locations")
        if "DATE" in entity_types:
            categories.add("temporal")
        if "MONEY" in entity_types:
            categories.add("financial")
        if any(t in entity_types for t in ["LAW", "LEGAL"]):
            categories.add("legal")
        
        # Content-based categorization
        entity_names = [entity["name"].lower() for entity in entities]
        
        legal_keywords = ["court", "case", "law", "legal", "ruling", "judgment", "statute"]
        if any(keyword in " ".join(entity_names) for keyword in legal_keywords):
            categories.add("legal")
        
        medical_keywords = ["health", "medical", "patient", "doctor", "hospital", "treatment"]
        if any(keyword in " ".join(entity_names) for keyword in medical_keywords):
            categories.add("medical")
        
        government_keywords = ["government", "policy", "regulation", "department", "agency"]
        if any(keyword in " ".join(entity_names) for keyword in government_keywords):
            categories.add("government")
        
        # Add insights-based categorization if available
        if insights:
            document_type = insights.get("document_type", "")
            main_themes = insights.get("main_themes", [])
            
            # Map document types to categories
            if document_type == "research_paper":
                categories.add("research")
            elif document_type == "regulatory_document":
                categories.add("regulatory")
            elif document_type == "clinical_trial":
                categories.add("clinical")
            elif document_type == "patent":
                categories.add("intellectual_property")
            
            # Add theme-based categories
            for theme in main_themes:
                theme_lower = theme.lower()
                if "covid" in theme_lower or "pandemic" in theme_lower:
                    categories.add("covid-19")
                if "vaccine" in theme_lower:
                    categories.add("vaccines")
                if "fda" in theme_lower or "regulatory" in theme_lower:
                    categories.add("regulatory")
                if "treatment" in theme_lower or "therapy" in theme_lower:
                    categories.add("treatment")
        
        return list(categories)
    
    async def index_document(self, document_id: str, processed_data: Dict[str, Any]):
        """Index the processed document in Elasticsearch"""
        try:
            # Prepare document for indexing
            es_document = {
                "title": processed_data["title"],
                "content": processed_data["content"],
                "metadata": processed_data["metadata"],
                "extracted_entities": processed_data["entities"],
                "tags": processed_data["tags"],
                "categories": processed_data["categories"],
                "processing_status": "completed",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Add OpenAI enhanced fields if available
            if processed_data.get("openai_entities"):
                es_document["openai_entities"] = processed_data["openai_entities"]
            if processed_data.get("relationships"):
                es_document["relationships"] = processed_data["relationships"]
            if processed_data.get("key_concepts"):
                es_document["key_concepts"] = processed_data["key_concepts"]
            if processed_data.get("document_summary"):
                es_document["ai_summary"] = processed_data["document_summary"]
            if processed_data.get("highlighted_content"):
                es_document["highlighted_content"] = processed_data["highlighted_content"]
            if processed_data.get("document_insights"):
                es_document["document_insights"] = processed_data["document_insights"]
            
            # Add multimodal fields if available
            if processed_data.get("image_metadata"):
                es_document["image_metadata"] = processed_data["image_metadata"]
            if processed_data.get("image_entities"):
                es_document["image_entities"] = processed_data["image_entities"]
            if processed_data.get("stored_images"):
                es_document["stored_images"] = processed_data["stored_images"]
            
            # Add multimodal processing flag
            es_document["ai_processed"] = True
            es_document["has_images"] = processed_data["metadata"].get("has_images", False)
            es_document["multimodal"] = processed_data["metadata"].get("has_images", False)
            
            # Add vector field if available
            if processed_data.get("content_vector"):
                es_document["content_vector"] = processed_data["content_vector"]
            
            # Index in Elasticsearch
            await elasticsearch_client.index(
                index="dataplatform_documents",
                id=document_id,
                body=es_document
            )
            
            logger.info("Document indexed in Elasticsearch", document_id=document_id)
            
        except Exception as e:
            logger.error("Failed to index document", document_id=document_id, error=str(e))
            raise
    
    async def create_knowledge_graph(self, document_id: str, processed_data: Dict[str, Any]):
        """Create knowledge graph nodes and relationships"""
        try:
            async with neo4j_driver.session() as session:
                # Create document node
                await session.run("""
                    MERGE (d:Document {id: $document_id})
                    SET d.title = $title,
                        d.created_at = datetime(),
                        d.updated_at = datetime(),
                        d.filename = $filename,
                        d.file_type = $file_type,
                        d.user_id = $user_id
                """, {
                    "document_id": document_id,
                    "title": processed_data["title"],
                    "filename": processed_data["metadata"]["filename"],
                    "file_type": processed_data["metadata"]["file_type"],
                    "user_id": processed_data["metadata"]["user_id"]
                })
                
                # Create entity nodes and relationships
                for entity in processed_data["entities"]:
                    entity_id = f"{entity['type']}_{entity['name'].replace(' ', '_').lower()}"
                    
                    # Determine entity label
                    label_mapping = {
                        "PERSON": "Person",
                        "ORG": "Organization",
                        "ORGANIZATION": "Organization",
                        "GPE": "Location",
                        "LOCATION": "Location",
                        "DATE": "Date",
                        "MONEY": "Money",
                        "LAW": "Legal",
                        "LEGAL": "Legal"
                    }
                    
                    label = label_mapping.get(entity["type"], "Entity")
                    
                    # Create entity node
                    await session.run(f"""
                        MERGE (e:{label} {{id: $entity_id}})
                        SET e.name = $name,
                            e.type = $entity_type,
                            e.confidence = $confidence,
                            e.created_at = datetime(),
                            e.updated_at = datetime()
                    """, {
                        "entity_id": entity_id,
                        "name": entity["name"],
                        "entity_type": entity["type"],
                        "confidence": entity.get("confidence", 1.0)
                    })
                    
                    # Create relationship between document and entity
                    await session.run("""
                        MATCH (d:Document {id: $document_id}), (e {id: $entity_id})
                        MERGE (d)-[r:MENTIONS]->(e)
                        SET r.frequency = coalesce(r.frequency, 0) + 1,
                            r.updated_at = datetime()
                    """, {
                        "document_id": document_id,
                        "entity_id": entity_id
                    })
                
                logger.info("Knowledge graph created", 
                           document_id=document_id,
                           entities_count=len(processed_data["entities"]))
                
        except Exception as e:
            logger.error("Failed to create knowledge graph", document_id=document_id, error=str(e))
            raise
    
    async def update_document_status(
        self, 
        document_id: str, 
        status: str, 
        message: str, 
        progress: float,
        metadata: Dict[str, Any] = None
    ):
        """Update document processing status in database"""
        try:
            await database_manager.update_document_status(
                document_id=document_id,
                status=status,
                message=message,
                progress=progress,
                metadata=metadata or {}
            )
            
        except Exception as e:
            logger.error("Failed to update document status", document_id=document_id, error=str(e))
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if elasticsearch_client:
            await elasticsearch_client.close()
        if neo4j_driver:
            await neo4j_driver.close()
        if database_manager:
            await database_manager.close()
        
        logger.info("Document processor cleanup completed")


async def main():
    """Main entry point for the document processor"""
    processor = DocumentProcessor()
    
    try:
        await processor.initialize()
        await processor.start_processing()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Fatal error in document processor", error=str(e))
        raise
    finally:
        await processor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())