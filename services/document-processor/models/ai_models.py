"""
AI Model Abstraction Layer
Supports multiple AI providers: OpenAI, Ollama (Phi3), and future models
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import asyncio
import httpx
import json
import structlog

logger = structlog.get_logger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"

class ModelCapability(Enum):
    TEXT_GENERATION = "text_generation"
    ENTITY_EXTRACTION = "entity_extraction"
    EMBEDDINGS = "embeddings"
    CHAT = "chat"
    SUMMARIZATION = "summarization"

class ModelInfo:
    """Information about a specific model"""
    def __init__(
        self,
        name: str,
        provider: ModelProvider,
        capabilities: List[ModelCapability],
        max_tokens: int,
        cost_per_1k_tokens: float = 0.0,
        description: str = "",
        is_local: bool = False,
        requires_api_key: bool = True
    ):
        self.name = name
        self.provider = provider
        self.capabilities = capabilities
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.description = description
        self.is_local = is_local
        self.requires_api_key = requires_api_key

class AIModel(ABC):
    """Abstract base class for AI models"""
    
    def __init__(self, model_info: ModelInfo, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_info = model_info
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the model client"""
        pass
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using the model"""
        pass
    
    @abstractmethod
    async def extract_entities(
        self, 
        text: str, 
        document_title: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Extract entities and relationships from text"""
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self, 
        text: str, 
        **kwargs
    ) -> List[float]:
        """Generate embeddings for text"""
        pass
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate chat completion"""
        pass

class OpenAIModel(AIModel):
    """OpenAI model implementation"""
    
    def __init__(self, model_info: ModelInfo, api_key: str):
        super().__init__(model_info, api_key)
        self.client = None
    
    async def initialize(self) -> bool:
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
            
            # Test the connection
            await self.client.models.list()
            logger.info("OpenAI model initialized successfully", model=self.model_info.name)
            return True
        except Exception as e:
            logger.error("Failed to initialize OpenAI model", error=str(e))
            return False
    
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model_info.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI text generation failed", error=str(e))
            raise
    
    async def extract_entities(
        self, 
        text: str, 
        document_title: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        try:
            system_prompt = """You are an expert information extraction system. Extract entities and relationships from documents with high precision.
            
            Return a JSON response with the following structure:
            {
                "entities": [{"name": "entity_name", "type": "entity_type", "confidence": 0.9}],
                "relationships": [{"subject": "entity1", "predicate": "relationship", "object": "entity2", "confidence": 0.8}],
                "key_concepts": [
                    {"concept": "concept1", "importance": 0.9, "related_entities": "entity1, entity2"},
                    {"concept": "concept2", "importance": 0.8, "related_entities": "entity3, entity4"}
                ],
                "document_summary": "Brief summary of the document"
            }"""
            
            user_prompt = f"Document Title: {document_title}\n\nContent: {text[:8000]}"  # Truncate for token limits
            
            response = await self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return {
                    "entities": [],
                    "relationships": [],
                    "key_concepts": [],
                    "document_summary": response[:500]
                }
                
        except Exception as e:
            logger.error("OpenAI entity extraction failed", error=str(e))
            return {"entities": [], "relationships": [], "key_concepts": [], "document_summary": ""}
    
    async def generate_embeddings(self, text: str, **kwargs) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("OpenAI embeddings generation failed", error=str(e))
            raise
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_info.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI chat completion failed", error=str(e))
            raise

class OllamaModel(AIModel):
    """Ollama model implementation (supports Phi3 and other local models)"""
    
    def __init__(self, model_info: ModelInfo, base_url: str = "http://localhost:11434"):
        super().__init__(model_info, base_url=base_url)
        self.client = None
    
    async def initialize(self) -> bool:
        try:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
            
            # Test the connection
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                if self.model_info.name in model_names:
                    logger.info("Ollama model initialized successfully", model=self.model_info.name)
                    return True
                else:
                    logger.warning("Model not found in Ollama", model=self.model_info.name, available_models=model_names)
                    return False
            else:
                logger.error("Failed to connect to Ollama", status_code=response.status_code)
                return False
        except Exception as e:
            logger.error("Failed to initialize Ollama model", error=str(e))
            return False
    
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model_info.name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        **kwargs
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error("Ollama text generation failed", error=str(e))
            raise
    
    async def extract_entities(
        self, 
        text: str, 
        document_title: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        try:
            system_prompt = """You are an expert information extraction system. Extract entities and relationships from documents with high precision.
            
            Return a JSON response with the following structure:
            {
                "entities": [{"name": "entity_name", "type": "entity_type", "confidence": 0.9}],
                "relationships": [{"subject": "entity1", "predicate": "relationship", "object": "entity2", "confidence": 0.8}],
                "key_concepts": [
                    {"concept": "concept1", "importance": 0.9, "related_entities": "entity1, entity2"},
                    {"concept": "concept2", "importance": 0.8, "related_entities": "entity3, entity4"}
                ],
                "document_summary": "Brief summary of the document"
            }"""
            
            user_prompt = f"Document Title: {document_title}\n\nContent: {text[:4000]}"  # Smaller limit for local models
            
            response = await self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return {
                    "entities": [],
                    "relationships": [],
                    "key_concepts": [],
                    "document_summary": response[:500]
                }
                
        except Exception as e:
            logger.error("Ollama entity extraction failed", error=str(e))
            return {"entities": [], "relationships": [], "key_concepts": [], "document_summary": ""}
    
    async def generate_embeddings(self, text: str, **kwargs) -> List[float]:
        try:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": self.model_info.name,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])
            else:
                raise Exception(f"Ollama embeddings API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error("Ollama embeddings generation failed", error=str(e))
            # Fallback to a simple hash-based embedding for local models
            import hashlib
            import struct
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to float array
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    value = struct.unpack('>f', chunk)[0]
                    embedding.append(value)
            return embedding[:384]  # Standard embedding size
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        try:
            # Convert messages to prompt format for Ollama
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"Human: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            full_prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
            
            response = await self.generate_text(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response
        except Exception as e:
            logger.error("Ollama chat completion failed", error=str(e))
            raise

class ModelRegistry:
    """Registry for managing available AI models"""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self._register_default_models()
    
    def _register_default_models(self):
        """Register default models"""
        
        # OpenAI Models
        self.register_model(ModelInfo(
            name="gpt-4",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=8192,
            cost_per_1k_tokens=0.03,
            description="Most capable OpenAI model for complex tasks",
            requires_api_key=True
        ))
        
        self.register_model(ModelInfo(
            name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=4096,
            cost_per_1k_tokens=0.002,
            description="Fast and efficient OpenAI model",
            requires_api_key=True
        ))
        
        # Ollama Models
        self.register_model(ModelInfo(
            name="phi3:medium",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=2048,
            cost_per_1k_tokens=0.0,
            description="Microsoft Phi-3 Medium model via Ollama (local)",
            is_local=True,
            requires_api_key=False
        ))
        
        self.register_model(ModelInfo(
            name="phi3:mini",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=2048,
            cost_per_1k_tokens=0.0,
            description="Microsoft Phi-3 Mini model via Ollama (local, lightweight)",
            is_local=True,
            requires_api_key=False
        ))
        
        self.register_model(ModelInfo(
            name="llama3.1:8b",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=4096,
            cost_per_1k_tokens=0.0,
            description="Meta Llama 3.1 8B model via Ollama (local, fast)",
            is_local=True,
            requires_api_key=False
        ))
        
        self.register_model(ModelInfo(
            name="llama3.1:70b",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=4096,
            cost_per_1k_tokens=0.0,
            description="Meta Llama 3.1 70B model via Ollama (local, high quality, requires 48GB RAM)",
            is_local=True,
            requires_api_key=False
        ))
        
        self.register_model(ModelInfo(
            name="llama2:7b",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=2048,
            cost_per_1k_tokens=0.0,
            description="Meta Llama 2 7B model via Ollama (local, lightweight)",
            is_local=True,
            requires_api_key=False
        ))
        
        self.register_model(ModelInfo(
            name="llama2:13b",
            provider=ModelProvider.OLLAMA,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ENTITY_EXTRACTION, ModelCapability.CHAT, ModelCapability.SUMMARIZATION],
            max_tokens=2048,
            cost_per_1k_tokens=0.0,
            description="Meta Llama 2 13B model via Ollama (local, balanced)",
            is_local=True,
            requires_api_key=False
        ))
    
    def register_model(self, model_info: ModelInfo):
        """Register a new model"""
        self.models[model_info.name] = model_info
        logger.info("Model registered", model=model_info.name, provider=model_info.provider.value)
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Get model information by name"""
        return self.models.get(name)
    
    def list_models(self, capability: Optional[ModelCapability] = None) -> List[ModelInfo]:
        """List all models, optionally filtered by capability"""
        if capability:
            return [model for model in self.models.values() if capability in model.capabilities]
        return list(self.models.values())
    
    def get_models_by_provider(self, provider: ModelProvider) -> List[ModelInfo]:
        """Get all models from a specific provider"""
        return [model for model in self.models.values() if model.provider == provider]

class ModelFactory:
    """Factory for creating AI model instances"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    async def create_model(
        self, 
        model_name: str, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Optional[AIModel]:
        """Create an AI model instance"""
        
        model_info = self.registry.get_model(model_name)
        if not model_info:
            logger.error("Model not found", model=model_name)
            return None
        
        try:
            if model_info.provider == ModelProvider.OPENAI:
                if not api_key:
                    logger.error("API key required for OpenAI model", model=model_name)
                    return None
                model = OpenAIModel(model_info, api_key)
            elif model_info.provider == ModelProvider.OLLAMA:
                ollama_url = base_url or "http://localhost:11434"
                model = OllamaModel(model_info, ollama_url)
            else:
                logger.error("Unsupported model provider", provider=model_info.provider.value)
                return None
            
            # Initialize the model
            if await model.initialize():
                logger.info("Model created successfully", model=model_name, provider=model_info.provider.value)
                return model
            else:
                logger.error("Failed to initialize model", model=model_name)
                return None
                
        except Exception as e:
            logger.error("Failed to create model", model=model_name, error=str(e))
            return None

# Global instances
model_registry = ModelRegistry()
model_factory = ModelFactory(model_registry)
