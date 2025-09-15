"""
Image Storage Manager for handling multimodal document images
Manages storage in MinIO and metadata in Elasticsearch
"""

import asyncio
import hashlib
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

logger = structlog.get_logger(__name__)


class ImageStorageManager:
    """Manages storage and retrieval of extracted document images"""
    
    def __init__(self, minio_client: Minio, bucket_name: str = "documents"):
        self.minio_client = minio_client
        self.bucket_name = bucket_name
        self.images_folder = "images"
        
        # Ensure bucket and folder structure exists
        if MINIO_AVAILABLE:
            self._ensure_bucket_structure()
    
    def _ensure_bucket_structure(self):
        """Ensure MinIO bucket and folder structure exists"""
        try:
            # Check if bucket exists
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket", bucket=self.bucket_name)
            
            # Create images folder structure (this happens automatically with first upload)
            logger.info("MinIO image storage initialized", bucket=self.bucket_name)
            
        except Exception as e:
            logger.error("Failed to initialize MinIO image storage", error=str(e))
    
    async def store_document_images(
        self, 
        document_id: str, 
        images: List[Dict[str, Any]], 
        document_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Store extracted images from a document"""
        
        if not images:
            return []
        
        logger.info("Storing document images", 
                   document_id=document_id, 
                   image_count=len(images))
        
        stored_images = []
        
        for i, image_data in enumerate(images):
            try:
                # Generate unique image ID
                image_id = f"{document_id}_img_{i+1}_{uuid.uuid4().hex[:8]}"
                
                # Extract image binary data
                img_bytes = self._extract_image_bytes(image_data)
                if not img_bytes:
                    logger.warning("No image data found", image_index=i)
                    continue
                
                # Generate image hash for deduplication
                image_hash = hashlib.sha256(img_bytes).hexdigest()
                
                # Create image metadata
                image_metadata = {
                    "image_id": image_id,
                    "document_id": document_id,
                    "image_hash": image_hash,
                    "page_number": image_data.get("page_number", i + 1),
                    "extraction_method": image_data.get("extraction_method", "unknown"),
                    "document_section": image_data.get("document_section", f"page_{i+1}"),
                    "file_size": len(img_bytes),
                    "stored_at": datetime.utcnow().isoformat(),
                    "content_type": "image/jpeg",  # Default, could be detected
                }
                
                # Add document metadata if provided
                if document_metadata:
                    image_metadata["document_metadata"] = {
                        "title": document_metadata.get("title", ""),
                        "file_type": document_metadata.get("file_type", ""),
                        "upload_date": document_metadata.get("upload_date", "")
                    }
                
                # Store image in MinIO
                object_path = f"{self.images_folder}/{document_id}/{image_id}.jpg"
                
                try:
                    # Upload to MinIO
                    from io import BytesIO
                    image_stream = BytesIO(img_bytes)
                    
                    self.minio_client.put_object(
                        bucket_name=self.bucket_name,
                        object_name=object_path,
                        data=image_stream,
                        length=len(img_bytes),
                        content_type="image/jpeg",
                        metadata={"document_id": document_id, "image_id": image_id}
                    )
                    
                    # Update metadata with storage info
                    image_metadata.update({
                        "storage_path": object_path,
                        "storage_url": f"minio://{self.bucket_name}/{object_path}",
                        "storage_status": "stored",
                        "storage_backend": "minio"
                    })
                    
                    stored_images.append(image_metadata)
                    
                    logger.info("Image stored successfully", 
                               image_id=image_id,
                               storage_path=object_path,
                               file_size=len(img_bytes))
                
                except Exception as storage_error:
                    logger.error("Failed to store image in MinIO", 
                               image_id=image_id,
                               error=str(storage_error))
                    
                    # Still add to metadata but mark as failed
                    image_metadata.update({
                        "storage_status": "failed",
                        "storage_error": str(storage_error)
                    })
                    stored_images.append(image_metadata)
                
            except Exception as e:
                logger.error("Failed to process image", 
                           image_index=i,
                           error=str(e))
                continue
        
        logger.info("Document image storage completed",
                   document_id=document_id,
                   stored_count=len(stored_images))
        
        return stored_images
    
    def _extract_image_bytes(self, image_data: Dict[str, Any]) -> Optional[bytes]:
        """Extract binary image data from various formats"""
        
        try:
            # Try different possible keys for image data
            if "image_data" in image_data and isinstance(image_data["image_data"], bytes):
                return image_data["image_data"]
            
            # Base64 encoded data
            if "image_data" in image_data and isinstance(image_data["image_data"], str):
                import base64
                return base64.b64decode(image_data["image_data"])
            
            # Image info with data
            if "image_info" in image_data:
                img_info = image_data["image_info"]
                if isinstance(img_info, dict):
                    if "data" in img_info and isinstance(img_info["data"], bytes):
                        return img_info["data"]
                    if "base64" in img_info:
                        import base64
                        return base64.b64decode(img_info["base64"])
            
            # Direct bytes
            if "data" in image_data and isinstance(image_data["data"], bytes):
                return image_data["data"]
            
            logger.warning("No valid image data found in image_data", keys=list(image_data.keys()))
            return None
            
        except Exception as e:
            logger.error("Failed to extract image bytes", error=str(e))
            return None
    
    async def get_document_images(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all images for a document"""
        
        try:
            folder_prefix = f"{self.images_folder}/{document_id}/"
            
            # List objects in the document's image folder
            objects = self.minio_client.list_objects(
                bucket_name=self.bucket_name,
                prefix=folder_prefix
            )
            
            images = []
            for obj in objects:
                try:
                    # Get object metadata
                    stat = self.minio_client.stat_object(
                        bucket_name=self.bucket_name,
                        object_name=obj.object_name
                    )
                    
                    image_info = {
                        "image_id": obj.object_name.split('/')[-1].split('.')[0],
                        "storage_path": obj.object_name,
                        "storage_url": f"minio://{self.bucket_name}/{obj.object_name}",
                        "file_size": stat.size,
                        "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                        "content_type": stat.content_type,
                        "metadata": stat.metadata
                    }
                    
                    images.append(image_info)
                    
                except Exception as e:
                    logger.error("Failed to get image info", 
                               object_name=obj.object_name,
                               error=str(e))
            
            logger.info("Retrieved document images", 
                       document_id=document_id,
                       image_count=len(images))
            
            return images
            
        except Exception as e:
            logger.error("Failed to get document images", 
                        document_id=document_id,
                        error=str(e))
            return []
    
    async def get_image_data(self, document_id: str, image_id: str) -> Optional[bytes]:
        """Retrieve binary data for a specific image"""
        
        try:
            object_path = f"{self.images_folder}/{document_id}/{image_id}.jpg"
            
            # Get object from MinIO
            response = self.minio_client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            
            image_data = response.read()
            response.close()
            
            logger.info("Retrieved image data", 
                       document_id=document_id,
                       image_id=image_id,
                       data_size=len(image_data))
            
            return image_data
            
        except Exception as e:
            logger.error("Failed to retrieve image data", 
                        document_id=document_id,
                        image_id=image_id,
                        error=str(e))
            return None
    
    async def delete_document_images(self, document_id: str) -> bool:
        """Delete all images for a document"""
        
        try:
            folder_prefix = f"{self.images_folder}/{document_id}/"
            
            # List and delete all objects in the folder
            objects = self.minio_client.list_objects(
                bucket_name=self.bucket_name,
                prefix=folder_prefix
            )
            
            deleted_count = 0
            for obj in objects:
                try:
                    self.minio_client.remove_object(
                        bucket_name=self.bucket_name,
                        object_name=obj.object_name
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.error("Failed to delete image", 
                               object_name=obj.object_name,
                               error=str(e))
            
            logger.info("Deleted document images", 
                       document_id=document_id,
                       deleted_count=deleted_count)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error("Failed to delete document images", 
                        document_id=document_id,
                        error=str(e))
            return False
    
    def generate_image_url(self, document_id: str, image_id: str, expires_in_hours: int = 24) -> Optional[str]:
        """Generate a presigned URL for image access"""
        
        try:
            from datetime import timedelta
            
            object_path = f"{self.images_folder}/{document_id}/{image_id}.jpg"
            
            # Generate presigned URL
            url = self.minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                expires=timedelta(hours=expires_in_hours)
            )
            
            return url
            
        except Exception as e:
            logger.error("Failed to generate image URL", 
                        document_id=document_id,
                        image_id=image_id,
                        error=str(e))
            return None