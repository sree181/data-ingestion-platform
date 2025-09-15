#!/usr/bin/env python3
"""
Database manager for the Document Chat Service
Handles conversation storage and retrieval
"""

import asyncpg
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from models import ConversationHistory, ConversationMessage, ChatRequest, ChatResponse

logger = structlog.get_logger()

class DatabaseManager:
    """Manages database connections and operations for chat service"""
    
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@postgres:5432/data_ingestion"
        )
    
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            # Create tables if they don't exist
            await self.create_tables()
            
            logger.info("✅ Database manager initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize database manager", error=str(e))
            raise
    
    async def create_tables(self):
        """Create necessary tables for chat service"""
        async with self.pool.acquire() as conn:
            # Conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    title TEXT,
                    document_scope JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id VARCHAR(255) PRIMARY KEY,
                    conversation_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    citations JSONB,
                    metadata JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
                ON conversations(user_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
                ON conversations(updated_at DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON conversation_messages(conversation_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON conversation_messages(timestamp)
            """)
    
    async def save_conversation(
        self, 
        request: ChatRequest, 
        response: ChatResponse
    ) -> bool:
        """Save or update a conversation with new message exchange"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if conversation exists
                    conversation_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM conversations WHERE conversation_id = $1)",
                        response.conversation_id
                    )
                    
                    if not conversation_exists:
                        # Create new conversation
                        await conn.execute("""
                            INSERT INTO conversations (
                                conversation_id, user_id, title, document_scope, created_at, updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """, 
                            response.conversation_id,
                            request.user_id,
                            request.query[:100] + "..." if len(request.query) > 100 else request.query,
                            json.dumps(request.document_ids) if request.document_ids else None,
                            response.timestamp,
                            response.timestamp
                        )
                    else:
                        # Update existing conversation
                        await conn.execute("""
                            UPDATE conversations 
                            SET updated_at = $1 
                            WHERE conversation_id = $2
                        """, response.timestamp, response.conversation_id)
                    
                    # Save user message
                    user_message_id = f"user_{response.conversation_id}_{int(response.timestamp.timestamp())}"
                    await conn.execute("""
                        INSERT INTO conversation_messages (
                            message_id, conversation_id, role, content, citations, metadata, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        user_message_id,
                        response.conversation_id,
                        "user",
                        request.query,
                        json.dumps([]),
                        json.dumps({"document_ids": request.document_ids}),
                        response.timestamp
                    )
                    
                    # Save assistant response
                    assistant_message_id = f"assistant_{response.conversation_id}_{int(response.timestamp.timestamp())}"
                    await conn.execute("""
                        INSERT INTO conversation_messages (
                            message_id, conversation_id, role, content, citations, metadata, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        assistant_message_id,
                        response.conversation_id,
                        "assistant",
                        response.response,
                        json.dumps([citation.dict() for citation in response.citations]),
                        json.dumps(response.metadata),
                        response.timestamp
                    )
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to save conversation", error=str(e))
            return False
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve full conversation history"""
        try:
            async with self.pool.acquire() as conn:
                # Get conversation info
                conv_row = await conn.fetchrow("""
                    SELECT conversation_id, user_id, title, document_scope, created_at, updated_at
                    FROM conversations 
                    WHERE conversation_id = $1
                """, conversation_id)
                
                if not conv_row:
                    return None
                
                # Get messages
                message_rows = await conn.fetch("""
                    SELECT message_id, role, content, citations, metadata, timestamp
                    FROM conversation_messages 
                    WHERE conversation_id = $1 
                    ORDER BY timestamp ASC
                """, conversation_id)
                
                # Build conversation history
                messages = []
                for row in message_rows:
                    messages.append(ConversationMessage(
                        message_id=row['message_id'],
                        role=row['role'],
                        content=row['content'],
                        timestamp=row['timestamp'],
                        citations=json.loads(row['citations']) if row['citations'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    ))
                
                return ConversationHistory(
                    conversation_id=conv_row['conversation_id'],
                    user_id=conv_row['user_id'],
                    title=conv_row['title'],
                    messages=messages,
                    created_at=conv_row['created_at'],
                    updated_at=conv_row['updated_at'],
                    document_scope=json.loads(conv_row['document_scope']) if conv_row['document_scope'] else None
                )
        
        except Exception as e:
            logger.error("❌ Failed to get conversation history", error=str(e))
            return None
    
    async def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations for a user"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT conversation_id, title, created_at, updated_at,
                           (SELECT COUNT(*) FROM conversation_messages 
                            WHERE conversation_id = conversations.conversation_id) as message_count
                    FROM conversations 
                    WHERE user_id = $1 
                    ORDER BY updated_at DESC 
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                return [
                    {
                        "conversation_id": row['conversation_id'],
                        "title": row['title'],
                        "message_count": row['message_count'],
                        "created_at": row['created_at'].isoformat(),
                        "updated_at": row['updated_at'].isoformat()
                    }
                    for row in rows
                ]
        
        except Exception as e:
            logger.error("❌ Failed to list conversations", error=str(e))
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM conversations WHERE conversation_id = $1",
                    conversation_id
                )
                return "DELETE 1" in result
        
        except Exception as e:
            logger.error("❌ Failed to delete conversation", error=str(e))
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("📊 Database connection pool closed")