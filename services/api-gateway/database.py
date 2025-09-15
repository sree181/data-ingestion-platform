"""
Database connection and management
"""

import asyncio
from typing import Optional, Dict, Any
import structlog
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Import security models to ensure they're registered
from models.security_models import Base as SecurityBase

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.sync_engine = None
        self.session_factory = None
        self.sync_session_factory = None
        self.pool = None
    
    async def connect(self):
        """Initialize database connection"""
        try:
            # Create asyncpg connection pool for raw queries
            self.pool = await asyncpg.create_pool(
                self.database_url
            )
            
            # Create SQLAlchemy async engine
            self.engine = create_async_engine(
                self.database_url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                pool_pre_ping=True
            )
            
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create synchronous engine for security services
            self.sync_engine = create_engine(
                self.database_url,
                pool_pre_ping=True
            )
            
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                expire_on_commit=False
            )
            
            # Create security tables (temporarily disabled)
            # SecurityBase.metadata.create_all(self.sync_engine)
            
            logger.info("Database connected successfully")
            
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        if self.engine:
            await self.engine.dispose()
        if self.sync_engine:
            self.sync_engine.dispose()
        logger.info("Database connections closed")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def get_document_status(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT document_id, status, progress, message, metadata, 
                           created_at, updated_at, filename
                    FROM document_status 
                    WHERE document_id = $1 AND user_id = $2
                    """,
                    document_id, user_id
                )
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error("Failed to get document status", error=str(e))
            raise
    
    async def update_document_status(
        self,
        document_id: str,
        status: str,
        message: str,
        progress: float,
        metadata: Dict[str, Any] = None
    ):
        """Update document processing status"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO document_status (document_id, user_id, filename, status, progress, message, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (document_id) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        progress = EXCLUDED.progress,
                        message = EXCLUDED.message,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    document_id, "system", "unknown", status, progress, message, metadata or {}
                )
                
        except Exception as e:
            logger.error("Failed to update document status", error=str(e))
            raise
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Get job counts by status
                stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_jobs,
                        COUNT(*) FILTER (WHERE status = 'processing') as processing_jobs,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) FILTER (WHERE status = 'completed') as avg_processing_time
                    FROM document_status
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    """
                )
                
                return {
                    "pending_jobs": stats["pending_jobs"] or 0,
                    "processing_jobs": stats["processing_jobs"] or 0,
                    "completed_jobs": stats["completed_jobs"] or 0,
                    "failed_jobs": stats["failed_jobs"] or 0,
                    "average_processing_time": float(stats["avg_processing_time"] or 0)
                }
                
        except Exception as e:
            logger.error("Failed to get processing stats", error=str(e))
            return {
                "pending_jobs": 0,
                "processing_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "average_processing_time": 0.0
            }
    
    def get_session(self):
        """Get synchronous database session for security services"""
        return self.sync_session_factory()

# Dependency for FastAPI
def get_db():
    """FastAPI dependency for database session"""
    # This will be set by the main application
    from main import db_manager
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()