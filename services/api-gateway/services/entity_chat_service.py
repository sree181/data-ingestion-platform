"""
Entity-Centric Chat Service - RAG-based Q&A about entities
"""
import os
import structlog
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from services.knowledge_hub_service import KnowledgeHubService

logger = structlog.get_logger(__name__)


class EntityChatService:
    """Service for RAG-based chat about entities using their source documents"""
    
    def __init__(self, knowledge_hub_service: KnowledgeHubService):
        self.knowledge_hub_service = knowledge_hub_service
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        self.max_context_docs = 5
        self.max_tokens = 2000
        
    async def chat_with_entity(
        self,
        entity_name: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        space_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with an entity using RAG pipeline
        
        Args:
            entity_name: Name of the entity to chat about
            message: User's question/message
            conversation_history: Previous conversation messages
            space_id: Optional filter by space
            
        Returns:
            Dict with response, sources, and metadata
        """
        try:
            logger.info(f"Entity chat request", entity=entity_name, message=message)
            
            # Step 1: Get entity details
            entity_details = await self.knowledge_hub_service.get_entity_details(entity_name)
            if not entity_details:
                return {
                    "success": False,
                    "error": f"Entity '{entity_name}' not found"
                }
            
            # Step 2: Retrieve source documents
            sources_response = await self.knowledge_hub_service.get_entity_source_documents(
                entity_name=entity_name,
                space_id=space_id,
                limit=self.max_context_docs
            )
            
            if not sources_response.get("success") or not sources_response.get("documents"):
                return {
                    "success": True,
                    "response": "I don't have enough source documents to answer questions about this entity.",
                    "sources": [],
                    "entity_name": entity_name
                }
            
            documents = sources_response["documents"]
            
            # Step 3: Build context from documents
            context = self._build_context(entity_name, entity_details, documents)
            
            # Step 4: Build prompt with conversation history
            prompt = self._build_prompt(
                entity_name=entity_name,
                entity_type=entity_details.get("type", "Entity"),
                context=context,
                question=message,
                conversation_history=conversation_history or []
            )
            
            # Step 5: Call LLM
            llm_response = await self._call_llm(prompt)
            
            if not llm_response:
                return {
                    "success": False,
                    "error": "Failed to get response from LLM"
                }
            
            # Step 6: Format response with sources
            return {
                "success": True,
                "response": llm_response,
                "sources": self._format_sources(documents),
                "entity_name": entity_name,
                "entity_type": entity_details.get("type", "Entity")
            }
            
        except Exception as e:
            logger.error(f"Entity chat failed: {e}", entity=entity_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_context(
        self,
        entity_name: str,
        entity_details: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> str:
        """Build context string from source documents"""
        context_parts = []
        
        # Add entity overview
        context_parts.append(f"Entity: {entity_name}")
        context_parts.append(f"Type: {entity_details.get('type', 'Unknown')}")
        if entity_details.get('description'):
            context_parts.append(f"Description: {entity_details['description']}")
        context_parts.append("")
        
        # Add source documents
        context_parts.append("Source Documents:")
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"\n[{i}] {doc.get('title', 'Untitled')} (Source: {doc.get('source_type', 'unknown')})")
            
            # Add snippets or summary
            if doc.get('snippets'):
                # Clean HTML marks from snippets
                snippets = doc['snippets']
                clean_snippets = [s.replace('<mark>', '').replace('</mark>', '') for s in snippets]
                context_parts.append("   " + " ... ".join(clean_snippets[:2]))
            elif doc.get('summary'):
                context_parts.append(f"   {doc['summary']}")
        
        return "\n".join(context_parts)
    
    def _build_prompt(
        self,
        entity_name: str,
        entity_type: str,
        context: str,
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build complete prompt for LLM"""
        
        system_prompt = """You are an AI assistant helping domain experts (attorneys, physicians, clinical scientists) analyze entities in a knowledge graph.

Your role:
- Answer questions based ONLY on the provided document context
- Always cite your sources using [1], [2] notation referring to the numbered documents
- Be concise but thorough
- If information is not in the context, say "I don't have enough information in the available documents"
- Focus on factual information, not speculation
"""
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nPrevious Conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 exchanges for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role.capitalize()}: {content}\n"
        
        # Combine all parts
        full_prompt = f"""{system_prompt}

{context}
{conversation_context}

Current Question: {question}

Please provide a clear, concise answer with citations to the source documents [1], [2], etc.

Answer:"""
        
        return full_prompt
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call OpenAI GPT with prompt"""
        try:
            logger.info(f"Calling OpenAI with model {self.model}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant helping domain experts analyze entities in a knowledge graph. Always cite your sources using [1], [2] notation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=500,  # Max response length
                timeout=60.0
            )
            
            llm_response = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received, length: {len(llm_response)}")
            return llm_response
                    
        except Exception as e:
            logger.error(f"OpenAI call error: {type(e).__name__}: {str(e)}")
            return None
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        formatted = []
        for i, doc in enumerate(documents, 1):
            formatted.append({
                "citation_number": i,
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title", "Untitled"),
                "source_type": doc.get("source_type", "unknown"),
                "is_external": doc.get("is_external", False),
                "snippet": doc.get("snippets", [""])[0] if doc.get("snippets") else doc.get("summary", "")[:200],
                "confidence": doc.get("entity_confidence", 0.5),
                "relevance_score": doc.get("score", 0)
            })
        return formatted

