"""
Database Manager for Entity Enrichment Service
Handles PostgreSQL operations for entity enrichment data
"""

import asyncpg
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:password@localhost:5432/data_ingestion"
        )
        self.pool = None

    async def init_pool(self):
        """Initialize connection pool"""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                await self._create_tables()
                logger.info("Database pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {str(e)}")
                raise

    async def _create_tables(self):
        """Create necessary tables for entity enrichment"""
        create_tables_sql = """
        -- Entity enrichment results table
        CREATE TABLE IF NOT EXISTS entity_enrichments (
            id SERIAL PRIMARY KEY,
            entity_id VARCHAR(255) UNIQUE NOT NULL,
            entity_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            scraped_data JSONB,
            consolidated_data JSONB,
            sources TEXT[],
            confidence_score FLOAT DEFAULT 0.0,
            conflicts JSONB,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Entity enrichment status tracking
        CREATE TABLE IF NOT EXISTS entity_enrichment_status (
            id SERIAL PRIMARY KEY,
            entity_id VARCHAR(255) UNIQUE NOT NULL,
            entity_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL, -- pending, scraping, completed, failed
            sources_scraped INTEGER DEFAULT 0,
            enrichment_score FLOAT DEFAULT 0.0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_entity_enrichments_entity_id ON entity_enrichments(entity_id);
        CREATE INDEX IF NOT EXISTS idx_entity_enrichments_entity_type ON entity_enrichments(entity_type);
        CREATE INDEX IF NOT EXISTS idx_entity_enrichments_status ON entity_enrichments(status);
        CREATE INDEX IF NOT EXISTS idx_entity_enrichment_status_entity_id ON entity_enrichment_status(entity_id);
        CREATE INDEX IF NOT EXISTS idx_entity_enrichment_status_status ON entity_enrichment_status(status);
        """
        
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_tables_sql)
            logger.info("Database tables created/verified successfully")

    async def store_entity_enrichment(self, entity_id: str, enrichment_data: Dict[str, Any]) -> bool:
        """Store entity enrichment results"""
        try:
            if not self.pool:
                await self.init_pool()

            query = """
            INSERT INTO entity_enrichments 
            (entity_id, entity_name, entity_type, scraped_data, consolidated_data, 
             sources, confidence_score, conflicts, status, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (entity_id) 
            DO UPDATE SET
                scraped_data = EXCLUDED.scraped_data,
                consolidated_data = EXCLUDED.consolidated_data,
                sources = EXCLUDED.sources,
                confidence_score = EXCLUDED.confidence_score,
                conflicts = EXCLUDED.conflicts,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    entity_id,
                    enrichment_data.get("entity_name", ""),
                    enrichment_data.get("entity_type", ""),
                    json.dumps(enrichment_data.get("scraped_data", {})),
                    json.dumps(enrichment_data.get("consolidated_data", {})),
                    enrichment_data.get("sources", []),
                    enrichment_data.get("confidence_score", 0.0),
                    json.dumps(enrichment_data.get("conflicts", [])),
                    "completed",
                    datetime.now()
                )
            
            logger.info(f"Stored enrichment data for entity: {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing entity enrichment for {entity_id}: {str(e)}")
            return False

    async def get_entity_enrichment(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity enrichment data"""
        try:
            if not self.pool:
                await self.init_pool()

            query = """
            SELECT entity_id, entity_name, entity_type, scraped_data, consolidated_data,
                   sources, confidence_score, conflicts, status, created_at, updated_at
            FROM entity_enrichments 
            WHERE entity_id = $1
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, entity_id)
                
                if row:
                    return {
                        "entity_id": row["entity_id"],
                        "entity_name": row["entity_name"],
                        "entity_type": row["entity_type"],
                        "scraped_data": json.loads(row["scraped_data"]) if row["scraped_data"] else {},
                        "consolidated_data": json.loads(row["consolidated_data"]) if row["consolidated_data"] else {},
                        "sources": list(row["sources"]) if row["sources"] else [],
                        "confidence_score": row["confidence_score"],
                        "conflicts": json.loads(row["conflicts"]) if row["conflicts"] else [],
                        "status": row["status"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting entity enrichment for {entity_id}: {str(e)}")
            return None

    async def update_enrichment_status(
        self, 
        entity_id: str, 
        status: str, 
        entity_name: str = "", 
        entity_type: str = "",
        sources_scraped: int = 0,
        enrichment_score: float = 0.0,
        error_message: str = ""
    ) -> bool:
        """Update entity enrichment status"""
        try:
            if not self.pool:
                await self.init_pool()

            query = """
            INSERT INTO entity_enrichment_status 
            (entity_id, entity_name, entity_type, status, sources_scraped, 
             enrichment_score, error_message, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (entity_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                sources_scraped = EXCLUDED.sources_scraped,
                enrichment_score = EXCLUDED.enrichment_score,
                error_message = EXCLUDED.error_message,
                updated_at = EXCLUDED.updated_at
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    entity_id,
                    entity_name,
                    entity_type,
                    status,
                    sources_scraped,
                    enrichment_score,
                    error_message,
                    datetime.now()
                )
            
            logger.info(f"Updated enrichment status for {entity_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating enrichment status for {entity_id}: {str(e)}")
            return False

    async def get_enrichment_status(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity enrichment status"""
        try:
            if not self.pool:
                await self.init_pool()

            query = """
            SELECT entity_id, entity_name, entity_type, status, sources_scraped,
                   enrichment_score, error_message, created_at, updated_at
            FROM entity_enrichment_status 
            WHERE entity_id = $1
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, entity_id)
                
                if row:
                    return {
                        "entity_id": row["entity_id"],
                        "entity_name": row["entity_name"],
                        "entity_type": row["entity_type"],
                        "status": row["status"],
                        "sources_scraped": row["sources_scraped"],
                        "enrichment_score": row["enrichment_score"],
                        "error_message": row["error_message"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting enrichment status for {entity_id}: {str(e)}")
            return None

    async def get_all_enrichment_statuses(self) -> List[Dict[str, Any]]:
        """Get all entity enrichment statuses"""
        try:
            if not self.pool:
                await self.init_pool()

            query = """
            SELECT entity_id, entity_name, entity_type, status, sources_scraped,
                   enrichment_score, error_message, created_at, updated_at
            FROM entity_enrichment_status 
            ORDER BY updated_at DESC
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
                
                return [
                    {
                        "entity_id": row["entity_id"],
                        "entity_name": row["entity_name"],
                        "entity_type": row["entity_type"],
                        "status": row["status"],
                        "sources_scraped": row["sources_scraped"],
                        "enrichment_score": row["enrichment_score"],
                        "error_message": row["error_message"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat()
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting all enrichment statuses: {str(e)}")
            return []

    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")