#!/usr/bin/env python3
"""
Pydantic models for the Document Chat Service
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str = Field(..., description="User's question or chat message")
    document_ids: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of specific document IDs to search. If None, searches all documents"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID to continue existing conversation"
    )
    user_id: str = Field(default="user1", description="User identifier")
    max_documents: int = Field(default=5, description="Maximum number of documents to use for context")
    include_citations: bool = Field(default=True, description="Whether to include source citations")
    
class DocumentCitation(BaseModel):
    """Citation information for source documents"""
    document_id: str = Field(..., description="Document identifier")
    document_title: str = Field(..., description="Document title")
    excerpt: str = Field(..., description="Relevant excerpt from the document")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    page_number: Optional[int] = Field(default=None, description="Page number if available")
    url: Optional[str] = Field(default=None, description="Document URL if available")


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: List[DocumentCitation] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationHistory(BaseModel):
    """Full conversation history"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(default=None, description="Conversation title")
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    document_scope: Optional[List[str]] = Field(
        default=None,
        description="Document IDs that were in scope for this conversation"
    )

class DocumentSearchResult(BaseModel):
    """Result from document search"""
    document_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    content_excerpt: str = Field(..., description="Relevant content excerpt")
    score: float = Field(..., description="Search relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI-generated response to the user's query")
    conversation_id: str = Field(..., description="Conversation identifier")
    citations: List[DocumentCitation] = Field(
        default_factory=list,
        description="Source documents used to generate the response"
    )
    documents: List[DocumentSearchResult] = Field(
        default_factory=list,
        description="Documents retrieved for the query"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds")
    
class ChatContext(BaseModel):
    """Internal model for chat context management"""
    query: str
    document_ids: Optional[List[str]]
    conversation_history: List[ConversationMessage]
    retrieved_documents: List[DocumentSearchResult]
    user_id: str