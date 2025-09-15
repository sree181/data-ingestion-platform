"""
MinIO service for object storage
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import structlog
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile

logger = structlog.get_logger(__name__)


class MinioService:
    """Service for interacting with MinIO object storage"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.client: Optional[Minio] = None
        
        # Default buckets
        self.buckets = {
            "documents": "documents",
            "images": "images", 
            "processed": "processed",
            "exports": "exports"
        }
    
    async def connect(self):
        """Initialize MinIO connection"""
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            
            # Create buckets if they don't exist
            await self._create_buckets()
            
            logger.info("Connected to MinIO", endpoint=self.endpoint)
            
        except Exception as e:
            logger.error("Failed to connect to MinIO", error=str(e))
            raise
    
    async def close(self):
        """Close MinIO connection"""
        # MinIO client doesn't need explicit closing
        logger.info("MinIO connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MinIO health"""
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            # Try to list buckets as a health check
            buckets = await asyncio.to_thread(self.client.list_buckets)
            return {
                "status": "healthy",
                "buckets": len(buckets)
            }
        except Exception as e:
            logger.error("MinIO health check failed", error=str(e))
            raise
    
    async def _create_buckets(self):
        """Create default buckets if they don't exist"""
        for bucket_name in self.buckets.values():
            try:
                bucket_exists = await asyncio.to_thread(
                    self.client.bucket_exists, bucket_name
                )
                
                if not bucket_exists:
                    await asyncio.to_thread(
                        self.client.make_bucket, bucket_name
                    )
                    logger.info("Created bucket", bucket=bucket_name)
                    
            except Exception as e:
                logger.error("Failed to create bucket", bucket=bucket_name, error=str(e))
    
    async def upload_file(
        self, 
        file: UploadFile, 
        bucket: str, 
        user_id: str,
        object_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to MinIO"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        # Generate unique object name if not provided
        if not object_name:
            file_extension = Path(file.filename).suffix
            object_name = f"{user_id}/{uuid.uuid4()}{file_extension}"
        
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
            # Upload to MinIO
            await asyncio.to_thread(
                self.client.put_object,
                bucket,
                object_name,
                data=file_content,
                length=file_size,
                content_type=file.content_type
            )
            
            file_info = {
                "file_id": str(uuid.uuid4()),
                "bucket": bucket,
                "object_name": object_name,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file_size,
                "uploaded_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            logger.info("File uploaded successfully", 
                       filename=file.filename,
                       bucket=bucket,
                       object_name=object_name,
                       size=file_size)
            
            return file_info
            
        except S3Error as e:
            logger.error("MinIO upload failed", error=str(e))
            raise Exception(f"File upload failed: {str(e)}")
        except Exception as e:
            logger.error("Upload failed", error=str(e))
            raise
    
    async def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            response = await asyncio.to_thread(
                self.client.get_object, bucket, object_name
            )
            
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.debug("File downloaded", bucket=bucket, object_name=object_name)
            return data
            
        except S3Error as e:
            logger.error("MinIO download failed", error=str(e))
            raise Exception(f"File download failed: {str(e)}")
        except Exception as e:
            logger.error("Download failed", error=str(e))
            raise
    
    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete a file from MinIO"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            await asyncio.to_thread(
                self.client.remove_object, bucket, object_name
            )
            
            logger.info("File deleted", bucket=bucket, object_name=object_name)
            return True
            
        except S3Error as e:
            logger.error("MinIO delete failed", error=str(e))
            return False
        except Exception as e:
            logger.error("Delete failed", error=str(e))
            return False
    
    async def list_files(
        self, 
        bucket: str, 
        prefix: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List files in a bucket"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            objects = await asyncio.to_thread(
                self.client.list_objects,
                bucket,
                prefix=prefix,
                recursive=True
            )
            
            files = []
            for obj in objects:
                if len(files) >= limit:
                    break
                    
                files.append({
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag
                })
            
            return files
            
        except Exception as e:
            logger.error("Failed to list files", error=str(e))
            raise
    
    async def get_file_url(
        self, 
        bucket: str, 
        object_name: str, 
        expires: int = 3600
    ) -> str:
        """Get a presigned URL for file access"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            url = await asyncio.to_thread(
                self.client.presigned_get_object,
                bucket,
                object_name,
                expires=expires
            )
            
            return url
            
        except Exception as e:
            logger.error("Failed to generate file URL", error=str(e))
            raise
    
    async def get_upload_url(
        self, 
        bucket: str, 
        object_name: str, 
        expires: int = 3600
    ) -> str:
        """Get a presigned URL for file upload"""
        
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        try:
            url = await asyncio.to_thread(
                self.client.presigned_put_object,
                bucket,
                object_name,
                expires=expires
            )
            
            return url
            
        except Exception as e:
            logger.error("Failed to generate upload URL", error=str(e))
            raise