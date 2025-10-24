"""
Real Classification Environment
Production environment using actual models with cost and latency tracking
"""

import asyncio
import time
import logging
import requests
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty
import structlog

from .model_manager import ModelManager
from .ensemble_strategy import EnsembleStrategy
from ..utils.error_handling import ErrorHandler, RetryConfig, CircuitBreakerConfig

logger = structlog.get_logger(__name__)

@dataclass
class ClassificationRequest:
    """Request for document classification"""
    document_id: str
    title: str
    abstract: str
    mesh_terms: List[str]
    publication_types: List[str]
    domain: str = "general_medicine"
    complexity_score: float = 0.5

@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_id: str
    classification: str
    confidence: float
    reasoning: str
    models_used: List[str]
    decision_path: str
    processing_time_ms: int
    cost_estimate: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    accuracy: float
    latency_ms: float
    cost_per_prediction: float
    throughput_per_second: float
    error_rate: float
    last_updated: datetime

class RealClassificationEnvironment:
    """
    Production environment using actual models
    - Load and manage rule-based classifier
    - Load and manage BERT model
    - Load and manage LLM (OpenAI/Anthropic)
    - Ensemble predictions based on action
    - Track actual costs and latencies
    - Implement circuit breakers for failures
    """
    
    def __init__(
        self,
        model_manager: ModelManager,
        ensemble_strategy: EnsembleStrategy,
        error_handler: Optional[ErrorHandler] = None,
        max_concurrent_requests: int = 10,
        timeout_seconds: int = 30
    ):
        """
        Initialize real classification environment
        
        Args:
            model_manager: Model management system
            ensemble_strategy: Ensemble prediction strategy
            error_handler: Error handling system
            max_concurrent_requests: Maximum concurrent requests
            timeout_seconds: Request timeout in seconds
        """
        self.model_manager = model_manager
        self.ensemble_strategy = ensemble_strategy
        self.error_handler = error_handler or ErrorHandler()
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_seconds = timeout_seconds
        
        # Request queue and thread pool
        self.request_queue = Queue(maxsize=max_concurrent_requests * 2)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_concurrent_requests)
        self.active_requests = {}
        self.request_lock = threading.RLock()
        
        # Performance tracking
        self.performance_metrics = {}
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency_ms': 0.0,
            'total_cost': 0.0
        }
        
        # Circuit breakers for each model
        self.circuit_breakers = {}
        self._initialize_circuit_breakers()
        
        logger.info("RealClassificationEnvironment initialized", 
                   max_concurrent_requests=max_concurrent_requests,
                   timeout_seconds=timeout_seconds)
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each model"""
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0
        )
        
        for model_name in self.model_manager.get_available_models():
            self.circuit_breakers[model_name] = self.error_handler.circuit_breaker
    
    async def classify_document(
        self, 
        request: ClassificationRequest,
        action: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classify a document using real models
        
        Args:
            request: Classification request
            action: RL action for model selection and parameters
            
        Returns:
            Classification result with actual metrics
        """
        start_time = time.time()
        request_id = f"{request.document_id}_{int(start_time * 1000)}"
        
        try:
            # Track request
            with self.request_lock:
                self.active_requests[request_id] = {
                    'start_time': start_time,
                    'request': request,
                    'action': action
                }
                self.request_stats['total_requests'] += 1
            
            # Determine models to use based on action
            models_to_use = self._determine_models_to_use(action)
            
            # Get model predictions
            predictions = await self._get_model_predictions(request, models_to_use)
            
            # Apply ensemble strategy
            ensemble_result = self.ensemble_strategy.combine_predictions(
                predictions, 
                action or {}
            )
            
            # Calculate actual metrics
            processing_time_ms = int((time.time() - start_time) * 1000)
            cost_estimate = self._calculate_cost(predictions)
            
            # Create result
            result = ClassificationResult(
                document_id=request.document_id,
                classification=ensemble_result['classification'],
                confidence=ensemble_result['confidence'],
                reasoning=ensemble_result['reasoning'],
                models_used=ensemble_result['models_used'],
                decision_path=ensemble_result['decision_path'],
                processing_time_ms=processing_time_ms,
                cost_estimate=cost_estimate,
                timestamp=datetime.utcnow(),
                metadata={
                    'request_id': request_id,
                    'action': action,
                    'individual_predictions': predictions
                }
            )
            
            # Update performance metrics
            self._update_performance_metrics(result, predictions)
            
            # Track successful request
            with self.request_lock:
                self.request_stats['successful_requests'] += 1
                self.request_stats['total_latency_ms'] += processing_time_ms
                self.request_stats['total_cost'] += cost_estimate
            
            logger.info("Document classified successfully",
                       document_id=request.document_id,
                       classification=result.classification,
                       confidence=result.confidence,
                       processing_time_ms=processing_time_ms,
                       cost_estimate=cost_estimate)
            
            return result
            
        except Exception as e:
            # Handle error
            error_context = self.error_handler.handle_error(
                e, "RealClassificationEnvironment", "classify_document",
                context_data={
                    'request_id': request_id,
                    'document_id': request.document_id,
                    'action': action
                }
            )
            
            # Track failed request
            with self.request_lock:
                self.request_stats['failed_requests'] += 1
            
            logger.error("Document classification failed",
                        document_id=request.document_id,
                        error=str(e),
                        error_id=error_context.error_id)
            
            # Return fallback result
            return self._create_fallback_result(request, str(e))
            
        finally:
            # Clean up request tracking
            with self.request_lock:
                if request_id in self.active_requests:
                    del self.active_requests[request_id]
    
    def _determine_models_to_use(self, action: Optional[Dict[str, Any]]) -> List[str]:
        """Determine which models to use based on RL action"""
        if not action:
            # Default to all available models
            return self.model_manager.get_available_models()
        
        # Extract model selection from action
        model_selection = action.get('model_selection', [])
        if not model_selection:
            return self.model_manager.get_available_models()
        
        # Filter to available models
        available_models = self.model_manager.get_available_models()
        return [model for model in model_selection if model in available_models]
    
    async def _get_model_predictions(
        self, 
        request: ClassificationRequest, 
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """Get predictions from multiple models"""
        predictions = []
        
        # Create tasks for parallel execution
        tasks = []
        for model_name in models:
            task = self._get_single_model_prediction(request, model_name)
            tasks.append(task)
        
        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Model {models[i]} failed: {result}")
                continue
            
            if result:
                predictions.append(result)
        
        return predictions
    
    async def _get_single_model_prediction(
        self, 
        request: ClassificationRequest, 
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get prediction from a single model"""
        try:
            # Check circuit breaker
            if model_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[model_name]
                if circuit_breaker.get_state().value == "open":
                    logger.warning(f"Circuit breaker open for {model_name}")
                    return None
            
            # Get model instance
            model = self.model_manager.get_model(model_name)
            if not model:
                logger.warning(f"Model {model_name} not available")
                return None
            
            # Make prediction with timeout
            start_time = time.time()
            
            # Use circuit breaker for model call
            if model_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[model_name]
                prediction = circuit_breaker.call(
                    lambda: model.predict(request)
                )
            else:
                prediction = model.predict(request)
            
            processing_time = time.time() - start_time
            
            # Add timing and cost information
            prediction.update({
                'model_name': model_name,
                'processing_time_ms': int(processing_time * 1000),
                'cost_estimate': model.get_cost_estimate(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return prediction
            
        except Exception as e:
            logger.error(f"Model {model_name} prediction failed: {e}")
            return None
    
    def _calculate_cost(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate total cost of predictions"""
        total_cost = 0.0
        
        for prediction in predictions:
            cost = prediction.get('cost_estimate', 0.0)
            if isinstance(cost, (int, float)):
                total_cost += cost
        
        return total_cost
    
    def _update_performance_metrics(
        self, 
        result: ClassificationResult, 
        predictions: List[Dict[str, Any]]
    ):
        """Update performance metrics for models"""
        for prediction in predictions:
            model_name = prediction.get('model_name')
            if not model_name:
                continue
            
            # Update model performance
            if model_name not in self.performance_metrics:
                self.performance_metrics[model_name] = ModelPerformance(
                    model_name=model_name,
                    accuracy=0.0,
                    latency_ms=0.0,
                    cost_per_prediction=0.0,
                    throughput_per_second=0.0,
                    error_rate=0.0,
                    last_updated=datetime.utcnow()
                )
            
            # Update metrics (simplified - in production, use proper statistical tracking)
            perf = self.performance_metrics[model_name]
            perf.latency_ms = prediction.get('processing_time_ms', 0)
            perf.cost_per_prediction = prediction.get('cost_estimate', 0.0)
            perf.last_updated = datetime.utcnow()
    
    def _create_fallback_result(
        self, 
        request: ClassificationRequest, 
        error_message: str
    ) -> ClassificationResult:
        """Create fallback result when classification fails"""
        return ClassificationResult(
            document_id=request.document_id,
            classification="Unknown",
            confidence=0.0,
            reasoning=f"Classification failed: {error_message}",
            models_used=[],
            decision_path="fallback",
            processing_time_ms=0,
            cost_estimate=0.0,
            timestamp=datetime.utcnow(),
            metadata={'error': error_message, 'fallback': True}
        )
    
    def get_performance_metrics(self) -> Dict[str, ModelPerformance]:
        """Get performance metrics for all models"""
        return self.performance_metrics.copy()
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        with self.request_lock:
            stats = self.request_stats.copy()
            
            # Calculate derived metrics
            if stats['total_requests'] > 0:
                stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
                stats['average_latency_ms'] = stats['total_latency_ms'] / stats['total_requests']
                stats['average_cost'] = stats['total_cost'] / stats['total_requests']
            else:
                stats['success_rate'] = 0.0
                stats['average_latency_ms'] = 0.0
                stats['average_cost'] = 0.0
            
            return stats
    
    def get_active_requests(self) -> Dict[str, Any]:
        """Get information about active requests"""
        with self.request_lock:
            active_info = {}
            current_time = time.time()
            
            for request_id, info in self.active_requests.items():
                active_info[request_id] = {
                    'document_id': info['request'].document_id,
                    'elapsed_time_ms': int((current_time - info['start_time']) * 1000),
                    'action': info['action']
                }
            
            return active_info
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            'environment': 'healthy',
            'models': {},
            'circuit_breakers': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check model health
        for model_name in self.model_manager.get_available_models():
            try:
                model = self.model_manager.get_model(model_name)
                if model and model.health_check():
                    health_status['models'][model_name] = 'healthy'
                else:
                    health_status['models'][model_name] = 'unhealthy'
            except Exception as e:
                health_status['models'][model_name] = f'error: {str(e)}'
        
        # Check circuit breaker status
        for model_name, circuit_breaker in self.circuit_breakers.items():
            health_status['circuit_breakers'][model_name] = circuit_breaker.get_state().value
        
        # Overall health
        unhealthy_models = [
            model for model, status in health_status['models'].items()
            if status != 'healthy'
        ]
        
        if unhealthy_models:
            health_status['environment'] = 'degraded'
            health_status['unhealthy_models'] = unhealthy_models
        
        return health_status
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        for circuit_breaker in self.circuit_breakers.values():
            circuit_breaker.reset()
        
        logger.info("All circuit breakers reset")
    
    def shutdown(self):
        """Shutdown the environment"""
        # Cancel active requests
        with self.request_lock:
            self.active_requests.clear()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("RealClassificationEnvironment shutdown complete")
