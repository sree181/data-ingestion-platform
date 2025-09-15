"""
Vector Embedding Service for Document Processing
Generates embeddings using OpenAI's text-embedding models
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import structlog
import openai
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)

class VectorEmbedder:
    """Generate vector embeddings for document content using OpenAI"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 1536):
        """
        Initialize the vector embedder
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use
            dimensions: Number of dimensions for the embedding
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions
        logger.info("Vector embedder initialized", model=model, dimensions=dimensions)
    
    async def embed_text(self, text: str, max_chars: int = 8000) -> List[float]:
        """
        Generate embedding for text content
        
        Args:
            text: Text to embed
            max_chars: Maximum characters to process
            
        Returns:
            List of embedding dimensions
        """
        try:
            # Truncate text if too long
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.info("Text truncated for embedding", 
                           original_length=len(text), 
                           truncated_length=max_chars)
            
            # Generate embedding
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            logger.info("Embedding generated successfully", 
                       text_length=len(text),
                       embedding_dimensions=len(embedding),
                       model=self.model)
            
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text_length=len(text))
            # Return zero vector as fallback
            return [0.0] * self.dimensions
    
    async def embed_batch(self, texts: List[str], max_chars: int = 8000) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            max_chars: Maximum characters per text
            
        Returns:
            List of embedding vectors
        """
        try:
            # Truncate texts if needed
            processed_texts = [text[:max_chars] if len(text) > max_chars else text for text in texts]
            
            # Generate embeddings in batch
            response = await self.client.embeddings.create(
                model=self.model,
                input=processed_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            
            logger.info("Batch embeddings generated successfully", 
                       batch_size=len(texts),
                       embedding_dimensions=len(embeddings[0]) if embeddings else 0)
            
            return embeddings
            
        except Exception as e:
            logger.error("Failed to generate batch embeddings", error=str(e), batch_size=len(texts))
            # Return zero vectors as fallback
            return [[0.0] * self.dimensions for _ in texts]
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        return await self.embed_text(query, max_chars=1000)
    
    def get_embedding_dimensions(self) -> int:
        """Get the number of dimensions for embeddings"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get the embedding model name"""
        return self.model
