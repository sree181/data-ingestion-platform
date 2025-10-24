"""
Model Server
Production-ready model serving and deployment system
"""

import os
import json
import time
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
import structlog
from datetime import datetime
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
import torch
import numpy as np
from pathlib import Path
import pickle
import hashlib

logger = structlog.get_logger(__name__)

@dataclass
class ModelServerConfig:
    """Configuration for model server"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    max_requests: int = 1000
    timeout: int = 30
    enable_cors: bool = True
    enable_metrics: bool = True
    enable_health_checks: bool = True
    model_path: str = "models"
    cache_size: int = 1000
    enable_batch_processing: bool = True
    batch_size: int = 32
    enable_async_processing: bool = True

class ModelCache:
    """Model caching system for fast inference"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                self.hit_count += 1
                return self.cache[key]
            else:
                self.miss_count += 1
                return None
    
    def put(self, key: str, value: Any):
        """Put item in cache"""
        with self.lock:
            # Remove oldest item if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=self.access_times.get)
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0
            
            return {
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": hit_rate
            }

class ModelManager:
    """Model loading and management system"""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.loaded_models = {}
        self.model_metadata = {}
        self.model_versions = {}
        self.lock = threading.Lock()
    
    def load_model(self, model_name: str, version: str = "latest") -> bool:
        """Load model into memory"""
        try:
            with self.lock:
                model_key = f"{model_name}_{version}"
                
                if model_key in self.loaded_models:
                    logger.info(f"Model {model_key} already loaded")
                    return True
                
                # Find model file
                model_file = self._find_model_file(model_name, version)
                if not model_file:
                    logger.error(f"Model file not found: {model_name}_{version}")
                    return False
                
                # Load model
                if model_file.suffix == ".pth":
                    model = torch.load(model_file, map_location="cpu")
                elif model_file.suffix == ".pkl":
                    with open(model_file, "rb") as f:
                        model = pickle.load(f)
                else:
                    logger.error(f"Unsupported model format: {model_file.suffix}")
                    return False
                
                # Store model
                self.loaded_models[model_key] = model
                
                # Load metadata
                metadata_file = model_file.with_suffix(".json")
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        self.model_metadata[model_key] = json.load(f)
                
                logger.info(f"Model {model_key} loaded successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load model {model_name}_{version}: {e}")
            return False
    
    def _find_model_file(self, model_name: str, version: str) -> Optional[Path]:
        """Find model file for given name and version"""
        if version == "latest":
            # Find latest version
            pattern = f"{model_name}_*.pth"
            files = list(self.model_path.glob(pattern))
            if not files:
                pattern = f"{model_name}_*.pkl"
                files = list(self.model_path.glob(pattern))
            
            if files:
                # Sort by modification time and return latest
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                return latest_file
        else:
            # Find specific version
            for ext in [".pth", ".pkl"]:
                model_file = self.model_path / f"{model_name}_{version}{ext}"
                if model_file.exists():
                    return model_file
        
        return None
    
    def get_model(self, model_name: str, version: str = "latest") -> Optional[Any]:
        """Get loaded model"""
        with self.lock:
            model_key = f"{model_name}_{version}"
            return self.loaded_models.get(model_key)
    
    def get_model_metadata(self, model_name: str, version: str = "latest") -> Dict[str, Any]:
        """Get model metadata"""
        with self.lock:
            model_key = f"{model_name}_{version}"
            return self.model_metadata.get(model_key, {})
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        with self.lock:
            models = []
            for model_key, metadata in self.model_metadata.items():
                model_name, version = model_key.rsplit("_", 1)
                models.append({
                    "name": model_name,
                    "version": version,
                    "metadata": metadata,
                    "loaded": model_key in self.loaded_models
                })
            return models
    
    def unload_model(self, model_name: str, version: str = "latest"):
        """Unload model from memory"""
        with self.lock:
            model_key = f"{model_name}_{version}"
            if model_key in self.loaded_models:
                del self.loaded_models[model_key]
                logger.info(f"Model {model_key} unloaded")

class InferenceEngine:
    """Model inference engine"""
    
    def __init__(self, model_manager: ModelManager, cache: ModelCache):
        self.model_manager = model_manager
        self.cache = cache
        self.inference_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency": 0.0,
            "latency_history": []
        }
        self.lock = threading.Lock()
    
    def predict(self, model_name: str, input_data: Any, version: str = "latest") -> Dict[str, Any]:
        """Run inference on model"""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(model_name, input_data, version)
            
            # Check cache first
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {model_name}")
                return cached_result
            
            # Get model
            model = self.model_manager.get_model(model_name, version)
            if model is None:
                raise ValueError(f"Model {model_name}_{version} not found")
            
            # Run inference
            result = self._run_inference(model, input_data)
            
            # Cache result
            self.cache.put(cache_key, result)
            
            # Update stats
            latency = time.time() - start_time
            self._update_stats(True, latency)
            
            logger.info(f"Inference completed for {model_name}", latency=latency)
            return result
            
        except Exception as e:
            latency = time.time() - start_time
            self._update_stats(False, latency)
            logger.error(f"Inference failed for {model_name}: {e}")
            raise
    
    def _generate_cache_key(self, model_name: str, input_data: Any, version: str) -> str:
        """Generate cache key for input"""
        key_data = {
            "model_name": model_name,
            "version": version,
            "input": str(input_data)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _run_inference(self, model, input_data: Any) -> Dict[str, Any]:
        """Run inference on model"""
        # This is a placeholder - actual implementation depends on model type
        if hasattr(model, "predict"):
            prediction = model.predict(input_data)
        elif hasattr(model, "forward"):
            # PyTorch model
            with torch.no_grad():
                if isinstance(input_data, dict):
                    # Handle structured input
                    input_tensor = torch.tensor(list(input_data.values()), dtype=torch.float32)
                else:
                    input_tensor = torch.tensor(input_data, dtype=torch.float32)
                
                prediction = model(input_tensor)
                prediction = prediction.cpu().numpy()
        else:
            # Generic model
            prediction = model(input_data)
        
        return {
            "prediction": prediction.tolist() if hasattr(prediction, "tolist") else prediction,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "latest"
        }
    
    def _update_stats(self, success: bool, latency: float):
        """Update inference statistics"""
        with self.lock:
            self.inference_stats["total_requests"] += 1
            if success:
                self.inference_stats["successful_requests"] += 1
            else:
                self.inference_stats["failed_requests"] += 1
            
            # Update average latency
            total_requests = self.inference_stats["total_requests"]
            current_avg = self.inference_stats["average_latency"]
            self.inference_stats["average_latency"] = (
                (current_avg * (total_requests - 1) + latency) / total_requests
            )
            
            # Keep latency history (last 1000 requests)
            self.inference_stats["latency_history"].append(latency)
            if len(self.inference_stats["latency_history"]) > 1000:
                self.inference_stats["latency_history"] = self.inference_stats["latency_history"][-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics"""
        with self.lock:
            stats = self.inference_stats.copy()
            stats["cache_stats"] = self.cache.get_stats()
            return stats

# Pydantic models for API
class PredictionRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to use")
    input_data: Any = Field(..., description="Input data for prediction")
    version: str = Field("latest", description="Model version to use")

class PredictionResponse(BaseModel):
    prediction: Any = Field(..., description="Model prediction")
    timestamp: str = Field(..., description="Prediction timestamp")
    model_version: str = Field(..., description="Model version used")
    latency_ms: float = Field(..., description="Prediction latency in milliseconds")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: float = Field(..., description="Service uptime in seconds")
    models_loaded: int = Field(..., description="Number of loaded models")

class ModelServer:
    """
    Production-ready model server
    - FastAPI-based REST API
    - Model caching and management
    - Health checks and metrics
    - Async processing support
    - Batch processing
    """
    
    def __init__(self, config: ModelServerConfig):
        """
        Initialize model server
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.app = FastAPI(
            title="RL Model Server",
            description="Production-ready model serving API",
            version="1.0.0"
        )
        
        # Initialize components
        self.model_manager = ModelManager(config.model_path)
        self.cache = ModelCache(config.cache_size)
        self.inference_engine = InferenceEngine(self.model_manager, self.cache)
        
        # Server state
        self.start_time = time.time()
        self.is_running = False
        
        # Setup API routes
        self._setup_routes()
        self._setup_middleware()
        
        logger.info("ModelServer initialized", 
                   host=config.host, port=config.port, workers=config.workers)
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS middleware
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
        
        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            uptime = time.time() - self.start_time
            models_loaded = len(self.model_manager.loaded_models)
            
            return HealthResponse(
                status="healthy",
                timestamp=datetime.utcnow().isoformat(),
                uptime=uptime,
                models_loaded=models_loaded
            )
        
        @self.app.post("/predict", response_model=PredictionResponse)
        async def predict(request: PredictionRequest):
            """Prediction endpoint"""
            try:
                start_time = time.time()
                
                # Run inference
                result = self.inference_engine.predict(
                    request.model_name,
                    request.input_data,
                    request.version
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                return PredictionResponse(
                    prediction=result["prediction"],
                    timestamp=result["timestamp"],
                    model_version=result["model_version"],
                    latency_ms=latency_ms
                )
                
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models")
        async def list_models():
            """List available models"""
            try:
                models = self.model_manager.list_models()
                return {"models": models}
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/{model_name}/load")
        async def load_model(model_name: str, version: str = "latest"):
            """Load model into memory"""
            try:
                success = self.model_manager.load_model(model_name, version)
                if success:
                    return {"message": f"Model {model_name}_{version} loaded successfully"}
                else:
                    raise HTTPException(status_code=404, detail="Model not found")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/{model_name}/unload")
        async def unload_model(model_name: str, version: str = "latest"):
            """Unload model from memory"""
            try:
                self.model_manager.unload_model(model_name, version)
                return {"message": f"Model {model_name}_{version} unloaded successfully"}
            except Exception as e:
                logger.error(f"Failed to unload model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get server statistics"""
            try:
                stats = self.inference_engine.get_stats()
                return stats
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/batch_predict")
        async def batch_predict(requests: List[PredictionRequest]):
            """Batch prediction endpoint"""
            try:
                if not self.config.enable_batch_processing:
                    raise HTTPException(status_code=400, detail="Batch processing not enabled")
                
                results = []
                for request in requests:
                    try:
                        result = self.inference_engine.predict(
                            request.model_name,
                            request.input_data,
                            request.version
                        )
                        results.append({
                            "success": True,
                            "result": result
                        })
                    except Exception as e:
                        results.append({
                            "success": False,
                            "error": str(e)
                        })
                
                return {"results": results}
                
            except Exception as e:
                logger.error(f"Batch prediction failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start(self):
        """Start the model server"""
        try:
            self.is_running = True
            logger.info("Starting model server", 
                       host=self.config.host, port=self.config.port)
            
            uvicorn.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                workers=self.config.workers,
                log_level="info"
            )
            
        except Exception as e:
            logger.error(f"Failed to start model server: {e}")
            raise
    
    def stop(self):
        """Stop the model server"""
        self.is_running = False
        logger.info("Model server stopped")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "config": self.config.__dict__,
            "is_running": self.is_running,
            "uptime": time.time() - self.start_time,
            "models_loaded": len(self.model_manager.loaded_models),
            "cache_stats": self.cache.get_stats(),
            "inference_stats": self.inference_engine.get_stats()
        }

# Factory function for easy model server setup
def create_model_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    model_path: str = "models",
    cache_size: int = 1000,
    **kwargs
) -> ModelServer:
    """
    Create model server with default configuration
    
    Args:
        host: Server host
        port: Server port
        model_path: Path to model files
        cache_size: Cache size for predictions
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured ModelServer
    """
    config = ModelServerConfig(
        host=host,
        port=port,
        model_path=model_path,
        cache_size=cache_size,
        **kwargs
    )
    
    return ModelServer(config)
