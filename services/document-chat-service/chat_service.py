#!/usr/bin/env python3
"""
Document Chat Service - Core chat processing logic
Handles document retrieval, OpenAI integration, and response generation
"""

import os
import asyncio
import json
import time
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import structlog
from functools import lru_cache

import openai
from elasticsearch import AsyncElasticsearch
import tiktoken

from models import (
    ChatRequest, ChatResponse, DocumentCitation, DocumentSearchResult,
    ChatContext, ConversationHistory, ConversationMessage
)
from database import DatabaseManager

logger = structlog.get_logger()

class DocumentChatService:
    """Professional-grade document chat service with AI-powered responses"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.es_client = None
        self.openai_client = None
        self.encoding = None
        
        # Configuration
        self.max_context_tokens = 8000  # Max tokens for GPT-4 input context (8,192 is the limit)
        self.max_response_tokens = 2000
        self.es_index = "documents"
        
        # Performance optimizations
        self.query_cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        
        # Professional features
        self.confidence_threshold = 0.7
        self.min_document_score = 0.1
        
    async def initialize(self):
        """Initialize external service connections"""
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)
            
            # Initialize Elasticsearch client
            es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
            es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
            
            self.es_client = AsyncElasticsearch(
                [f"http://{es_host}:{es_port}"],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connections
            await self._test_connections()
            
            # Initialize tokenizer
            self.encoding = tiktoken.encoding_for_model("gpt-4")
            
            logger.info("✅ Document chat service initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize document chat service", error=str(e))
            raise
    
    async def _test_connections(self):
        """Test external service connections"""
        # Test Elasticsearch
        try:
            await self.es_client.info()
            logger.info("✅ Elasticsearch connection successful")
        except Exception as e:
            logger.error("❌ Elasticsearch connection failed", error=str(e))
            raise
        
        # Test OpenAI
        try:
            await self.openai_client.models.list()
            logger.info("✅ OpenAI connection successful")
        except Exception as e:
            logger.error("❌ OpenAI connection failed", error=str(e))
            raise
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and generate AI response"""
        start_time = time.time()
        
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Get conversation history if continuing
            conversation_history = []
            if request.conversation_id:
                history = await self.db_manager.get_conversation_history(request.conversation_id)
                if history:
                    conversation_history = history.messages[-10:]  # Last 10 messages for context
            
            # Search for relevant documents with intelligent strategy selection
            logger.info(f"🔍 Starting document search for query: {request.query[:100]}")
            retrieved_docs = await self.search_documents(
                request.query, 
                request.max_documents,
                request.document_ids,
                conversation_history,
                search_type="auto"
            )
            logger.info(f"📄 Found {len(retrieved_docs)} documents for query")
            
            # Build chat context
            context = ChatContext(
                query=request.query,
                document_ids=request.document_ids,
                conversation_history=conversation_history,
                retrieved_documents=retrieved_docs,
                user_id=request.user_id
            )
            
            logger.info(f"📋 Built chat context with {len(retrieved_docs)} documents")
            for i, doc in enumerate(retrieved_docs):
                logger.info(f"  Document {i+1}: {doc.title} (content_length: {len(doc.content_excerpt)})")
            
            # Generate AI response
            ai_response, citations = await self._generate_ai_response(context)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Build response
            response = ChatResponse(
                response=ai_response,
                conversation_id=conversation_id,
                citations=citations if request.include_citations else [],
                documents=retrieved_docs,
                metadata={
                    "document_count": len(retrieved_docs),
                    "model": "gpt-4",
                    "has_conversation_history": len(conversation_history) > 0,
                    "query_length": len(request.query)
                },
                processing_time_ms=processing_time
            )
            
            return response
            
        except Exception as e:
            logger.error("❌ Failed to process chat request", error=str(e))
            raise
    
    async def search_documents(
        self, 
        query: str, 
        limit: int = 10,
        document_ids: Optional[List[str]] = None,
        conversation_history: Optional[List] = None,
        search_type: str = "hybrid"
    ) -> List[DocumentSearchResult]:
        """Advanced document search with multiple algorithms and caching"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, limit, document_ids, search_type)
            if cache_key in self.query_cache:
                cached_result, timestamp = self.query_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    logger.info("🎯 Cache hit for search query", query=query[:50])
                    return cached_result
                else:
                    # Remove expired cache entry
                    del self.query_cache[cache_key]
            
            # Extract context from conversation history
            context_info = self._extract_conversation_context(conversation_history)
            
            # Auto-select search strategy based on query analysis
            if search_type == "auto":
                search_type = self._analyze_query_and_select_strategy(query, context_info)
                logger.info(f"Selected search strategy: {search_type} for query: {query[:100]}")
            
            logger.info(f"Using search type: {search_type} for query: {query[:100]}")
            
            # Choose search strategy based on query characteristics
            if search_type == "hybrid":
                es_query = self._build_hybrid_search_query(query, context_info)
            elif search_type == "semantic":
                es_query = self._build_semantic_search_query(query, context_info)
            elif search_type == "vector":
                # Generate query embedding for vector search
                try:
                    query_vector = await self._generate_query_embedding(query)
                    es_query = self._build_vector_search_query(query_vector, context_info)
                except Exception as e:
                    logger.warning("Vector search failed, falling back to semantic", error=str(e))
                    es_query = self._build_semantic_search_query(query, context_info)
            elif search_type == "exact":
                es_query = self._build_exact_search_query(query, context_info)
            else:
                es_query = self._build_hybrid_search_query(query, context_info)
            
            # Filter by specific documents if provided
            if document_ids:
                es_query["bool"]["filter"] = {
                    "ids": {
                        "values": document_ids
                    }
                }
            
            # Execute search
            response = await self.es_client.search(
                index=self.es_index,
                query=es_query,
                size=limit,
                _source=[
                    "title", "content", "openai_summary", 
                    "created_at", "metadata"
                ],
                highlight={
                    "fields": {
                        "content": {"fragment_size": 200, "number_of_fragments": 2},
                        "openai_summary": {"fragment_size": 150, "number_of_fragments": 1}
                    }
                }
            )
            
            # Process results
            logger.info(f"Elasticsearch returned {response['hits']['total']['value']} total hits, processing {len(response['hits']['hits'])} hits")
            # Process search results with quality filtering
            results = []
            for hit in response["hits"]["hits"]:
                # Filter by minimum score threshold
                if hit["_score"] < self.min_document_score:
                    continue
                
                doc = hit["_source"]
                highlights = hit.get("highlight", {})
                
                # Get best excerpt from highlights or content
                excerpt = ""
                
                # For specific document queries, prefer full content over highlights
                if search_type == "exact" or (document_ids and len(document_ids) == 1):
                    # Use full content for specific document queries
                    logger.info(f"Using full content for exact search, search_type={search_type}, content_length={len(doc.get('content', ''))}")
                    if doc.get("content"):
                        excerpt = doc["content"]
                    elif doc.get("openai_summary"):
                        excerpt = doc["openai_summary"]
                    else:
                        excerpt = "No content available"
                else:
                    # Use highlights for general searches
                    if "content" in highlights:
                        excerpt = " ... ".join(highlights["content"])
                    elif "openai_summary" in highlights:
                        excerpt = highlights["openai_summary"][0]
                    elif doc.get("openai_summary"):
                        excerpt = doc["openai_summary"][:300] + "..."
                    else:
                        excerpt = doc.get("content", "")[:300] + "..."
                
                # Calculate confidence score
                confidence = min(hit["_score"] / 10.0, 1.0)
                
                results.append(DocumentSearchResult(
                    document_id=hit["_id"],
                    title=doc.get("title", "Untitled"),
                    content_excerpt=excerpt,
                    score=hit["_score"],
                    metadata={
                        "created_at": doc.get("created_at"),
                        "has_summary": bool(doc.get("openai_summary")),
                        "entity_count": 0,  # Simplified since entities are not available
                        "confidence": confidence,
                        "search_type": search_type
                    }
                ))
            
            # Cache the results
            self._cache_search_result(cache_key, results)
            
            logger.info(
                "🔍 Document search completed",
                query=query[:50] + "..." if len(query) > 50 else query,
                results_count=len(results),
                document_filter_count=len(document_ids) if document_ids else 0
            )
            
            return results
            
        except Exception as e:
            logger.error("❌ Document search failed", error=str(e))
            return []
    
    async def _generate_ai_response(
        self, 
        context: ChatContext
    ) -> tuple[str, List[DocumentCitation]]:
        """Generate AI response using OpenAI with document context"""
        try:
            # Prepare context for OpenAI
            system_prompt = self._build_system_prompt()
            user_message = self._build_user_message(context)
            
            # Check token limits
            total_tokens = len(self.encoding.encode(system_prompt + user_message))
            if total_tokens > self.max_context_tokens:
                # Truncate document content if necessary
                user_message = self._truncate_context(user_message, context)
            
            # Prepare conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in context.conversation_history[-5:]:  # Last 5 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=self.max_response_tokens,
                temperature=0.3,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Build citations
            citations = self._build_citations(context.retrieved_documents)
            
            logger.info(
                "🤖 AI response generated",
                response_length=len(ai_response),
                citations_count=len(citations),
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            
            return ai_response, citations
            
        except Exception as e:
            logger.error("❌ AI response generation failed", error=str(e))
            return "I apologize, but I encountered an error while processing your request. Please try again.", []
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for OpenAI"""
        return """You are a professional-grade document intelligence assistant specializing in legal, business, and technical document analysis. You provide enterprise-level document search, analysis, and insights.

CORE CAPABILITIES:
- Advanced document search and retrieval with context awareness
- Legal document analysis including clause extraction, risk assessment, and compliance review
- Business document insights including contract analysis, financial terms, and key provisions
- Technical document interpretation with precise terminology and specifications
- Multi-document comparison and cross-reference analysis
- Intelligent conversation context management and reference resolution

PROFESSIONAL STANDARDS:
- Provide accurate, comprehensive, and actionable insights
- Maintain strict confidentiality and professional discretion
- Use precise legal and business terminology appropriately
- Distinguish between factual information and professional advice
- Provide structured, well-organized responses with clear sections
- Include relevant citations and source references
- Maintain conversation context and resolve ambiguous references

LEGAL DOCUMENT EXPERTISE:
- Contract analysis: terms, obligations, rights, liabilities, termination clauses
- Compliance review: regulatory requirements, standards, and obligations
- Risk assessment: potential issues, liabilities, and mitigation strategies
- Clause categorization: payment terms, intellectual property, confidentiality, force majeure
- Cross-reference analysis: related documents, amendments, and dependencies

RESPONSE STRUCTURE:
1. Executive Summary: Brief overview of key findings
2. Detailed Analysis: Comprehensive examination of relevant sections
3. Key Provisions: Important clauses, terms, and conditions
4. Risk Factors: Potential issues or concerns identified
5. Recommendations: Actionable insights and next steps
6. Sources: Complete citation of referenced documents

CONVERSATION INTELLIGENCE:
- Maintain full conversation context and history
- Resolve ambiguous references like "this document", "the agreement", "it"
- Track document mentions and user preferences across exchanges
- Provide contextual follow-up suggestions
- Remember user's specific areas of interest and focus

QUALITY ASSURANCE:
- Verify all information against source documents
- Flag any uncertainties or limitations in available information
- Provide confidence levels for analysis and recommendations
- Suggest additional documents or information when relevant
- Maintain professional tone and appropriate formality level

IMPORTANT: When you receive document content with page markers (=== PAGE X === and ---END PAGE X---), this indicates the COMPLETE document has been provided, not fragments. The page markers are formatting artifacts from the document processing pipeline. You have access to the full document content and should analyze it comprehensively.
"""
    
    def _build_user_message(self, context: ChatContext) -> str:
        """Build user message with document context"""
        message_parts = []
        
        # Add conversation context if available
        if context.conversation_history:
            message_parts.append("**CONVERSATION CONTEXT:**")
            message_parts.append("Previous messages in this conversation:")
            for msg in context.conversation_history[-3:]:  # Last 3 messages for context
                message_parts.append(f"- {msg.role}: {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            message_parts.append("")
        
        # Add document context
        if context.retrieved_documents:
            message_parts.append("**DOCUMENT CONTEXT:**")
            message_parts.append("The following documents have been retrieved and are available for analysis. The content includes page markers (=== PAGE X ===) which are formatting artifacts - the complete document content is provided.")
            for i, doc in enumerate(context.retrieved_documents[:5], 1):
                message_parts.append(f"\n**Document {i}: {doc.title}**")
                message_parts.append(f"Content Length: {len(doc.content_excerpt)} characters")
                message_parts.append(f"Content: {doc.content_excerpt}")
                if doc.metadata.get("created_at"):
                    message_parts.append(f"Date: {doc.metadata['created_at']}")
                message_parts.append("")
        
        # Add user query
        message_parts.append("**USER QUESTION:**")
        message_parts.append(context.query)
        
        return "\n".join(message_parts)
    
    def _truncate_context(self, message: str, context: ChatContext) -> str:
        """Truncate context to fit token limits"""
        # Improved truncation for large documents
        max_chars = self.max_context_tokens * 3  # Rough estimate: 1 token ≈ 3 characters
        if len(message) > max_chars:
            # Keep the user query and truncate document content intelligently
            query_part = f"\n**USER QUESTION:**\n{context.query}"
            available_chars = max_chars - len(query_part) - 500  # Buffer for system prompt
            
            doc_part = "**DOCUMENT CONTEXT (TRUNCATED FOR TOKEN LIMITS):**\n"
            doc_part += "The following documents have been retrieved. Content is truncated due to token limits but represents the complete document.\n"
            
            for doc in context.retrieved_documents[:2]:  # Limit to 2 documents for large content
                # Calculate how much content we can include
                doc_header = f"**{doc.title}**\nContent Length: {len(doc.content_excerpt)} characters\n"
                remaining_chars = available_chars - len(doc_part) - len(doc_header) - 100
                
                if remaining_chars > 1000:  # Only include if we have substantial space
                    # Include beginning, middle, and end of document
                    content = doc.content_excerpt
                    if len(content) > remaining_chars:
                        # Smart truncation: beginning + middle + end
                        start_chars = remaining_chars // 3
                        end_chars = remaining_chars // 3
                        middle_chars = remaining_chars - start_chars - end_chars
                        
                        truncated_content = (
                            content[:start_chars] + 
                            f"\n\n[... TRUNCATED MIDDLE SECTION ...]\n\n" +
                            content[-(end_chars):]
                        )
                    else:
                        truncated_content = content
                    
                    doc_text = f"{doc_header}Content: {truncated_content}\n\n"
                    doc_part += doc_text
                else:
                    break
            
            return doc_part + query_part
        
        return message
    
    def _build_citations(self, documents: List[DocumentSearchResult]) -> List[DocumentCitation]:
        """Build citation objects from search results"""
        citations = []
        for doc in documents[:3]:  # Top 3 documents for citations
            citations.append(DocumentCitation(
                document_id=doc.document_id,
                document_title=doc.title,
                excerpt=doc.content_excerpt[:200] + "..." if len(doc.content_excerpt) > 200 else doc.content_excerpt,
                relevance_score=min(doc.score / 10.0, 1.0),  # Normalize score
                url=f"/documents/{doc.document_id}"  # Placeholder URL
            ))
        
        return citations
    
    def _extract_conversation_context(self, conversation_history: Optional[List]) -> Dict[str, Any]:
        """Extract relevant context from conversation history"""
        context_info = {
            "recent_documents": [],
            "discussed_topics": [],
            "user_preferences": {},
            "document_mentions": []
        }
        
        if not conversation_history:
            return context_info
        
        for msg in conversation_history[-10:]:  # Last 10 messages
            # Extract document mentions from citations
            if hasattr(msg, 'citations') and msg.citations:
                for citation in msg.citations:
                    if hasattr(citation, 'document_title'):
                        context_info["recent_documents"].append(citation.document_title)
                        context_info["document_mentions"].append(citation.document_title)
            
            # Extract topics from user messages
            if hasattr(msg, 'role') and msg.role == 'user':
                content = getattr(msg, 'content', '')
                # Simple topic extraction (could be enhanced with NLP)
                if 'clause' in content.lower():
                    context_info["discussed_topics"].append("legal_clauses")
                if 'agreement' in content.lower():
                    context_info["discussed_topics"].append("agreements")
                if 'finding' in content.lower():
                    context_info["discussed_topics"].append("key_findings")
        
        # Remove duplicates and keep recent
        context_info["recent_documents"] = list(dict.fromkeys(context_info["recent_documents"]))[-5:]
        context_info["document_mentions"] = list(dict.fromkeys(context_info["document_mentions"]))[-10:]
        
        return context_info
    
    def _generate_cache_key(self, query: str, limit: int, document_ids: Optional[List[str]], search_type: str) -> str:
        """Generate cache key for search query"""
        key_data = {
            "query": query.lower().strip(),
            "limit": limit,
            "document_ids": sorted(document_ids) if document_ids else None,
            "search_type": search_type
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _cache_search_result(self, cache_key: str, result: List[DocumentSearchResult]):
        """Cache search result with size management"""
        # Remove oldest entries if cache is full
        if len(self.query_cache) >= self.max_cache_size:
            oldest_key = min(self.query_cache.keys(), key=lambda k: self.query_cache[k][1])
            del self.query_cache[oldest_key]
        
        self.query_cache[cache_key] = (result, time.time())
    
    def _analyze_query_and_select_strategy(self, query: str, context_info: Dict[str, Any]) -> str:
        """Analyze query characteristics and select optimal search strategy"""
        query_lower = query.lower()
        
        # Check for exact document name patterns - more flexible patterns
        document_patterns = [
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+_[0-9]+_[0-9A-Z-]+_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+_[0-9]+_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}.*\.pdf'
        ]
        
        import re
        for pattern in document_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.info(f"Document pattern matched, using exact search for query: {query[:100]}")
                return "exact"
        
        # Check for specific document queries (asking about a particular document)
        specific_doc_phrases = [
            'about', 'regarding', 'concerning', 'findings about', 'analysis of',
            'key findings', 'summary of', 'details about', 'information about'
        ]
        if any(phrase in query_lower for phrase in specific_doc_phrases):
            # Check if there's a document name in the query
            if any(re.search(pattern, query, re.IGNORECASE) for pattern in document_patterns):
                return "exact"
        
        # Check for specific legal terms that benefit from exact search
        exact_terms = ['clause', 'section', 'article', 'paragraph', 'subsection']
        if any(term in query_lower for term in exact_terms):
            return "exact"
        
        # Check for context references
        context_refs = ['this document', 'the document', 'it', 'that agreement', 'this agreement']
        if any(ref in query_lower for ref in context_refs):
            return "hybrid"  # Use hybrid to leverage context
        
        # Check for conceptual questions
        conceptual_terms = ['what are', 'explain', 'describe', 'summarize', 'key findings', 'main points']
        if any(term in query_lower for term in conceptual_terms):
            return "semantic"
        
        # Check for meaning-based queries that benefit from vector search
        meaning_terms = ['similar', 'related', 'like', 'similar to', 'find documents about', 'documents discussing']
        if any(term in query_lower for term in meaning_terms):
            return "vector"
        
        # Check for specific information requests
        specific_terms = ['when', 'where', 'who', 'how much', 'how many', 'date', 'amount', 'number']
        if any(term in query_lower for term in specific_terms):
            return "exact"
        
        # Default to hybrid for general queries
        return "hybrid"
    
    def _build_hybrid_search_query(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build hybrid search query combining multiple search strategies"""
        should_clauses = [
            # High-precision exact matches
            {
                "match_phrase": {
                    "title": {
                        "query": query,
                        "boost": 4.0
                    }
                }
            },
            # Content search with different analyzers
            {
                "multi_match": {
                    "query": query,
                    "fields": ["content^1.5", "openai_summary^2.0", "title^3.0"],
                    "type": "best_fields",
                    "boost": 2.0
                }
            },
            # Fuzzy search for typos
            {
                "match": {
                    "title": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 1.5
                    }
                }
            },
            # Wildcard search for partial matches
            {
                "wildcard": {
                    "title": {
                        "value": f"*{query.lower()}*",
                        "boost": 1.2
                    }
                }
            }
        ]
        
        # Add vector search if embeddings are available
        # Note: This will be added dynamically when query embedding is generated
        
        # Add context-based boosting
        if context_info["recent_documents"]:
            for doc_title in context_info["recent_documents"]:
                should_clauses.append({
                    "match_phrase": {
                        "title": {
                            "query": doc_title,
                            "boost": 3.0
                        }
                    }
                })
        
        # Add topic-based boosting
        if "legal_clauses" in context_info["discussed_topics"]:
            should_clauses.append({
                "exists": {
                    "field": "legal_clauses",
                    "boost": 1.5
                }
            })
        
        return {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1
            }
        }
    
    def _build_semantic_search_query(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build semantic search query focusing on meaning and context"""
        return {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["content^1.0", "openai_summary^1.5", "title^2.0"],
                            "type": "most_fields",
                            "boost": 2.0
                        }
                    },
                    {
                        "match": {
                            "content": {
                                "query": query,
                                "boost": 1.0
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    
    def _extract_document_name_from_query(self, query: str) -> Optional[str]:
        """Extract document name from query using regex patterns"""
        import re
        
        # Document name patterns
        document_patterns = [
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+_[0-9]+_[0-9A-Z-]+_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+_[0-9]+_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}_[0-9A-Z-]+.*\.pdf',
            r'[A-Za-z]+[A-Za-z0-9]*_[0-9]{8}.*\.pdf'
        ]
        
        for pattern in document_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group()
        
        return None

    def _build_exact_search_query(self, query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build exact search query for precise matches"""
        # Extract document name from query if it contains a document pattern
        document_name = self._extract_document_name_from_query(query)
        
        if document_name:
            # Search for the specific document
            logger.info(f"Extracted document name for exact search: {document_name}")
            return {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "title": {
                                    "query": document_name,
                                    "boost": 3.0
                                }
                            }
                        }
                    ]
                }
            }
        else:
            # Fallback to searching the full query
            return {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "title": {
                                    "query": query,
                                    "boost": 3.0
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "content": {
                                    "query": query,
                                    "boost": 2.0
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
    
    async def save_conversation(self, request: ChatRequest, response: ChatResponse):
        """Save conversation to database"""
        try:
            await self.db_manager.save_conversation(request, response)
        except Exception as e:
            logger.error("❌ Failed to save conversation", error=str(e))
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation history"""
        return await self.db_manager.get_conversation_history(conversation_id)
    
    def _build_vector_search_query(self, query_vector: List[float], context_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build vector similarity search query using document embeddings"""
        return {
            "bool": {
                "should": [
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                "params": {"query_vector": query_vector}
                            },
                            "boost": 3.0
                        }
                    }
                ],
                "filter": [
                    {
                        "exists": {
                            "field": "content_vector"
                        }
                    }
                ]
            }
        }
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Failed to generate query embedding", error=str(e))
            raise
    
    async def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations"""
        return await self.db_manager.list_conversations(user_id, limit, offset)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        return await self.db_manager.delete_conversation(conversation_id)
        return await self.db_manager.delete_conversation(conversation_id)