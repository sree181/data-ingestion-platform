#!/usr/bin/env python3
"""
Document Chat Service - Intelligent chatbot for document interaction
Provides chat capabilities with document-aware context and citations
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import asyncio
import json
from datetime import datetime, timezone
import uuid
import structlog
from contextlib import asynccontextmanager

# Import our services
from chat_service import DocumentChatService
from models import ChatRequest, ChatResponse, ConversationHistory
from database import DatabaseManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
chat_service = None
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global chat_service, db_manager
    
    logger.info("🚀 Starting Document Chat Service...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("✅ Database manager initialized")
        
        # Initialize chat service
        chat_service = DocumentChatService(db_manager)
        await chat_service.initialize()
        logger.info("✅ Document chat service initialized")
        
        yield
        
    except Exception as e:
        logger.error("❌ Failed to start services", error=str(e))
        raise
    finally:
        # Cleanup
        if db_manager:
            await db_manager.close()
        logger.info("🔄 Document Chat Service stopped")

# Create FastAPI app
app = FastAPI(
    title="Document Chat Service",
    description="Intelligent chatbot for document interaction with AI-powered responses",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "document-chat-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# Chat endpoints
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    background_tasks: BackgroundTasks
) -> ChatResponse:
    """
    Chat with documents using AI-powered responses
    
    Args:
        request: Chat request with query, document IDs, and conversation context
        
    Returns:
        AI-generated response with citations and metadata
    """
    try:
        logger.info(
            "💬 Processing chat request",
            query=request.query[:100] + "..." if len(request.query) > 100 else request.query,
            document_count=len(request.document_ids) if request.document_ids else 0,
            conversation_id=request.conversation_id
        )
        
        # Process chat request
        response = await chat_service.process_chat(request)
        
        # Save conversation in background
        background_tasks.add_task(
            chat_service.save_conversation,
            request,
            response
        )
        
        logger.info(
            "✅ Chat response generated",
            conversation_id=response.conversation_id,
            response_length=len(response.response),
            citation_count=len(response.citations)
        )
        
        return response
        
    except Exception as e:
        logger.error("❌ Chat processing failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(conversation_id: str) -> ConversationHistory:
    """Get conversation history by ID"""
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get conversation history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversations")
async def list_conversations(
    user_id: str = "user1",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List recent conversations for a user"""
    try:
        conversations = await chat_service.list_conversations(user_id, limit, offset)
        return {
            "conversations": conversations,
            "total": len(conversations),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error("❌ Failed to list conversations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        success = await chat_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to delete conversation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents/search")
async def search_documents(
    query: str,
    limit: int = 10,
    document_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Search documents for chat context"""
    try:
        results = await chat_service.search_documents(query, limit, document_ids)
        return {
            "documents": results,
            "total": len(results),
            "query": query
        }
    except Exception as e:
        logger.error("❌ Document search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )