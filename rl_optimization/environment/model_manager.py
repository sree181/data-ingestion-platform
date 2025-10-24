"""
Model Manager
Manage multiple classification models with health checks, failover, and cost tracking
"""

import time
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a model"""
    name: str
    model_type: str
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    cost_per_request: float = 0.0
    health_check_interval: int = 60
    circuit_breaker_threshold: int = 5

@dataclass
class ModelHealth:
    """Model health status"""
    model_name: str
    is_healthy: bool
    last_check: datetime
    response_time_ms: float
    error_count: int
    success_count: int
    error_rate: float
    average_latency_ms: float

class BaseModel(ABC):
    """Base class for all classification models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.health_status = ModelHealth(
            model_name=config.name,
            is_healthy=True,
            last_check=datetime.utcnow(),
            response_time_ms=0.0,
            error_count=0,
            success_count=0,
            error_rate=0.0,
            average_latency_ms=0.0
        )
        self.lock = threading.RLock()
    
    @abstractmethod
    def predict(self, request) -> Dict[str, Any]:
        """Make a prediction on the given request"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the model is healthy"""
        pass
    
    def get_cost_estimate(self) -> float:
        """Get cost estimate for a prediction"""
        return self.config.cost_per_request
    
    def update_health_status(self, success: bool, response_time_ms: float):
        """Update health status based on prediction result"""
        with self.lock:
            self.health_status.last_check = datetime.utcnow()
            
            if success:
                self.health_status.success_count += 1
            else:
                self.health_status.error_count += 1
            
            # Update response time
            self.health_status.response_time_ms = response_time_ms
            
            # Calculate error rate
            total_requests = self.health_status.success_count + self.health_status.error_count
            if total_requests > 0:
                self.health_status.error_rate = self.health_status.error_count / total_requests
                self.health_status.is_healthy = self.health_status.error_rate < 0.1  # 10% error threshold
    
    def get_health_status(self) -> ModelHealth:
        """Get current health status"""
        with self.lock:
            return self.health_status

class RuleBasedModel(BaseModel):
    """Rule-based classification model"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load classification rules"""
        return {
            'icsr_keywords': [
                'adverse event', 'side effect', 'toxicity', 'overdose',
                'allergic reaction', 'contraindication', 'drug interaction'
            ],
            'safety_keywords': [
                'safety', 'tolerability', 'efficacy', 'clinical trial',
                'pharmacokinetics', 'pharmacodynamics'
            ],
            'mesh_terms': {
                'icsr': ['Adverse Drug Reaction Reporting Systems', 'Drug-Related Side Effects'],
                'safety': ['Drug Safety', 'Clinical Trials', 'Pharmacovigilance']
            },
            'publication_types': {
                'icsr': ['Case Reports', 'Case Studies'],
                'safety': ['Clinical Trial', 'Meta-Analysis', 'Systematic Review']
            }
        }
    
    def predict(self, request) -> Dict[str, Any]:
        """Make rule-based prediction"""
        start_time = time.time()
        
        try:
            # Extract features
            title = request.title.lower()
            abstract = request.abstract.lower()
            mesh_terms = [term.lower() for term in request.mesh_terms]
            pub_types = [pt.lower() for pt in request.publication_types]
            
            # Apply rules
            icsr_score = self._calculate_icsr_score(title, abstract, mesh_terms, pub_types)
            safety_score = self._calculate_safety_score(title, abstract, mesh_terms, pub_types)
            
            # Determine classification
            if icsr_score > 0.7:
                classification = "ICSR"
                confidence = min(icsr_score, 0.95)
            elif safety_score > 0.6:
                classification = "Safety_Information"
                confidence = min(safety_score, 0.9)
            else:
                classification = "Non-ICSR"
                confidence = 0.5
            
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(True, response_time)
            
            return {
                'classification': classification,
                'confidence': confidence,
                'reasoning': f"Rule-based classification with score {icsr_score:.2f}",
                'model_name': self.config.name,
                'processing_time_ms': int(response_time),
                'cost_estimate': self.get_cost_estimate()
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(False, response_time)
            raise e
    
    def _calculate_icsr_score(self, title: str, abstract: str, mesh_terms: List[str], pub_types: List[str]) -> float:
        """Calculate ICSR score based on rules"""
        score = 0.0
        
        # Check for ICSR keywords
        text = f"{title} {abstract}"
        icsr_keywords = self.rules['icsr_keywords']
        keyword_matches = sum(1 for keyword in icsr_keywords if keyword in text)
        score += min(keyword_matches * 0.2, 0.6)
        
        # Check MeSH terms
        icsr_mesh = self.rules['mesh_terms']['icsr']
        mesh_matches = sum(1 for mesh in icsr_mesh if any(term in mesh.lower() for term in mesh_terms))
        score += min(mesh_matches * 0.3, 0.6)
        
        # Check publication types
        icsr_pub_types = self.rules['publication_types']['icsr']
        pub_matches = sum(1 for pub_type in icsr_pub_types if any(pt in pub_type for pt in pub_types))
        score += min(pub_matches * 0.4, 0.8)
        
        return min(score, 1.0)
    
    def _calculate_safety_score(self, title: str, abstract: str, mesh_terms: List[str], pub_types: List[str]) -> float:
        """Calculate safety information score"""
        score = 0.0
        
        # Check for safety keywords
        text = f"{title} {abstract}"
        safety_keywords = self.rules['safety_keywords']
        keyword_matches = sum(1 for keyword in safety_keywords if keyword in text)
        score += min(keyword_matches * 0.15, 0.4)
        
        # Check MeSH terms
        safety_mesh = self.rules['mesh_terms']['safety']
        mesh_matches = sum(1 for mesh in safety_mesh if any(term in mesh.lower() for term in mesh_terms))
        score += min(mesh_matches * 0.25, 0.5)
        
        return min(score, 1.0)
    
    def health_check(self) -> bool:
        """Check if rule-based model is healthy"""
        return True  # Rule-based model is always healthy

class BERTModel(BaseModel):
    """BERT-based classification model"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load BERT model and tokenizer"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            model_name = "facebook/bart-large-mnli"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            
            logger.info(f"BERT model loaded: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            self.model = None
            self.tokenizer = None
    
    def predict(self, request) -> Dict[str, Any]:
        """Make BERT prediction"""
        start_time = time.time()
        
        try:
            if not self.model or not self.tokenizer:
                raise RuntimeError("BERT model not loaded")
            
            # Prepare input
            text = f"{request.title}. {request.abstract}"
            labels = ["ICSR", "Safety_Information", "Non-ICSR"]
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
            
            # Get best prediction
            best_idx = torch.argmax(probabilities, dim=-1).item()
            classification = labels[best_idx]
            confidence = probabilities[0][best_idx].item()
            
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(True, response_time)
            
            return {
                'classification': classification,
                'confidence': confidence,
                'reasoning': f"BERT classification with confidence {confidence:.3f}",
                'model_name': self.config.name,
                'processing_time_ms': int(response_time),
                'cost_estimate': self.get_cost_estimate()
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(False, response_time)
            raise e
    
    def health_check(self) -> bool:
        """Check if BERT model is healthy"""
        return self.model is not None and self.tokenizer is not None

class LLMModel(BaseModel):
    """Large Language Model for classification"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.endpoint = config.endpoint
        self._setup_client()
    
    def _setup_client(self):
        """Setup LLM client"""
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to setup LLM client: {e}")
            self.client = None
    
    def predict(self, request) -> Dict[str, Any]:
        """Make LLM prediction"""
        start_time = time.time()
        
        try:
            if not self.client:
                raise RuntimeError("LLM client not initialized")
            
            # Prepare prompt
            prompt = self._create_classification_prompt(request)
            
            # Make API call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical literature classification expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse response
            result = self._parse_llm_response(response.choices[0].message.content)
            
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(True, response_time)
            
            return {
                'classification': result['classification'],
                'confidence': result['confidence'],
                'reasoning': result['reasoning'],
                'model_name': self.config.name,
                'processing_time_ms': int(response_time),
                'cost_estimate': self.get_cost_estimate()
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.update_health_status(False, response_time)
            raise e
    
    def _create_classification_prompt(self, request) -> str:
        """Create classification prompt for LLM"""
        return f"""
        Classify this medical document as ICSR, Safety_Information, or Non-ICSR:
        
        Title: {request.title}
        Abstract: {request.abstract}
        MeSH Terms: {', '.join(request.mesh_terms)}
        Publication Types: {', '.join(request.publication_types)}
        Domain: {request.domain}
        
        Provide your classification in JSON format:
        {{
            "classification": "ICSR|Safety_Information|Non-ICSR",
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation"
        }}
        """
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            import json
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return {
                'classification': 'Non-ICSR',
                'confidence': 0.5,
                'reasoning': 'Failed to parse LLM response'
            }
    
    def health_check(self) -> bool:
        """Check if LLM is healthy"""
        if not self.client:
            return False
        
        try:
            # Simple health check
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response is not None
        except Exception:
            return False

class ModelManager:
    """
    Manage multiple classification models
    - Model loading and initialization
    - Health checks and monitoring
    - Automatic failover
    - Cost tracking per model
    - Latency monitoring
    """
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.health_check_thread = None
        self.health_check_interval = 60  # seconds
        self.running = False
        
        logger.info("ModelManager initialized")
    
    def register_model(self, config: ModelConfig) -> bool:
        """Register a new model"""
        try:
            # Create model instance based on type
            if config.model_type == "rule_based":
                model = RuleBasedModel(config)
            elif config.model_type == "bert":
                model = BERTModel(config)
            elif config.model_type == "llm":
                model = LLMModel(config)
            else:
                raise ValueError(f"Unknown model type: {config.model_type}")
            
            # Register model
            self.models[config.name] = model
            self.model_configs[config.name] = config
            
            logger.info(f"Model registered: {config.name} ({config.model_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model {config.name}: {e}")
            return False
    
    def get_model(self, name: str) -> Optional[BaseModel]:
        """Get model by name"""
        return self.models.get(name)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def get_healthy_models(self) -> List[str]:
        """Get list of healthy model names"""
        healthy_models = []
        for name, model in self.models.items():
            if model.health_check():
                healthy_models.append(name)
        return healthy_models
    
    def get_model_health(self, name: str) -> Optional[ModelHealth]:
        """Get health status for a specific model"""
        model = self.models.get(name)
        if model:
            return model.get_health_status()
        return None
    
    def get_all_health_status(self) -> Dict[str, ModelHealth]:
        """Get health status for all models"""
        health_status = {}
        for name, model in self.models.items():
            health_status[name] = model.get_health_status()
        return health_status
    
    def start_health_monitoring(self):
        """Start health monitoring thread"""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        
        self.running = True
        self.health_check_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True
        )
        self.health_check_thread.start()
        
        logger.info("Health monitoring started")
    
    def stop_health_monitoring(self):
        """Stop health monitoring thread"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        
        logger.info("Health monitoring stopped")
    
    def _health_monitoring_loop(self):
        """Health monitoring loop"""
        while self.running:
            try:
                for name, model in self.models.items():
                    try:
                        # Perform health check
                        is_healthy = model.health_check()
                        
                        # Log health status
                        if not is_healthy:
                            logger.warning(f"Model {name} is unhealthy")
                        
                    except Exception as e:
                        logger.error(f"Health check failed for {name}: {e}")
                
                # Wait for next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(5)  # Short delay before retry
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary for all models"""
        costs = {}
        for name, model in self.models.items():
            costs[name] = model.get_cost_estimate()
        return costs
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all models"""
        summary = {}
        for name, model in self.models.items():
            health = model.get_health_status()
            summary[name] = {
                'is_healthy': health.is_healthy,
                'error_rate': health.error_rate,
                'average_latency_ms': health.average_latency_ms,
                'success_count': health.success_count,
                'error_count': health.error_count,
                'last_check': health.last_check.isoformat()
            }
        return summary
    
    def shutdown(self):
        """Shutdown model manager"""
        self.stop_health_monitoring()
        self.models.clear()
        self.model_configs.clear()
        
        logger.info("ModelManager shutdown complete")
