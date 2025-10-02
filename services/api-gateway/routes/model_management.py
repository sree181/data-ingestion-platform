"""
Model Management API Endpoints
Handles AI model selection, testing, and configuration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import structlog
import asyncio
import httpx
import os

from auth.enhanced_auth import get_current_user
# from services.model_service import ModelService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["model-management"])

class ModelTestRequest(BaseModel):
    space_id: str
    model_name: str

class ModelConfigurationRequest(BaseModel):
    space_id: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class ModelConfigurationResponse(BaseModel):
    success: bool
    message: str
    model_info: Optional[Dict[str, Any]] = None

@router.get("/available")
async def get_available_models():
    """Get list of available AI models"""
    try:
        # Make a request to the document processor service
        async with httpx.AsyncClient() as client:
            response = await client.get("http://document-processor:8001/api/v1/models/available")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get models from document processor")
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve available models")

@router.post("/test/{model_name}")
async def test_model(model_name: str, request: ModelTestRequest):
    """Test if a model is available and working"""
    try:
        # Make a request to the document processor service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://document-processor:8001/api/v1/models/test/{model_name}",
                json=request.dict()
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to test model")
    except Exception as e:
        logger.error("Model test error", model=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")

@router.post("/configure")
async def configure_model_for_space(
    request: ModelConfigurationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Configure a model for a specific project space"""
    try:
        from services.document_processor.models import model_factory
        
        # Verify user has access to the space
        # This would typically check project space permissions
        # For now, we'll assume the user has access
        
        # Get model info
        model_info = model_factory.registry.get_model(request.model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Test the model configuration
        model = await model_factory.create_model(
            model_name=request.model_name,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        if not model:
            raise HTTPException(status_code=400, detail="Failed to initialize model with provided configuration")
        
        # Store model configuration for the space
        # This would typically be stored in the database
        # For now, we'll return success
        
        logger.info("Model configured for space", 
                   model=request.model_name, 
                   space_id=request.space_id,
                   user_id=current_user.get("user_id"))
        
        return ModelConfigurationResponse(
            success=True,
            message=f"Model {request.model_name} configured successfully for space {request.space_id}",
            model_info={
                "name": model.model_info.name,
                "provider": model.model_info.provider.value,
                "capabilities": [cap.value for cap in model.model_info.capabilities],
                "max_tokens": model.model_info.max_tokens,
                "is_local": model.model_info.is_local
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Model configuration failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Model configuration failed: {str(e)}")

@router.get("/space/{space_id}/current")
async def get_current_model_for_space(
    space_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the currently configured model for a project space"""
    try:
        # This would typically fetch from the database
        # For now, return a default configuration
        
        # Check if space exists and user has access
        # This would be a database query
        
        # Return default model configuration
        default_model = {
            "name": "gpt-4",
            "provider": "openai",
            "capabilities": ["text_generation", "entity_extraction", "chat", "summarization"],
            "max_tokens": 8192,
            "is_local": False,
            "configured_at": "2024-01-01T00:00:00Z"
        }
        
        logger.info("Current model retrieved for space", space_id=space_id)
        return {"current_model": default_model}
        
    except Exception as e:
        logger.error("Failed to get current model", space_id=space_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve current model")

@router.get("/ollama/status")
async def get_ollama_status():
    """Check Ollama service status and available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ollama:11434/api/tags", timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                return {
                    "status": "running",
                    "available_models": [
                        {
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", "")
                        }
                        for model in models
                    ]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama API returned status {response.status_code}",
                    "available_models": []
                }
                
    except Exception as e:
        logger.error("Ollama status check failed", error=str(e))
        return {
            "status": "offline",
            "message": f"Ollama service unavailable: {str(e)}",
            "available_models": []
        }

@router.post("/ollama/pull")
async def pull_ollama_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Pull/download a model to Ollama"""
    try:
        # Start the pull process in the background
        background_tasks.add_task(pull_model_task, model_name)
        
        logger.info("Model pull initiated", model=model_name, user_id=current_user.get("user_id"))
        return {
            "success": True,
            "message": f"Pulling model {model_name}. This may take several minutes.",
            "model_name": model_name
        }
        
    except Exception as e:
        logger.error("Failed to initiate model pull", model=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")

async def pull_model_task(model_name: str):
    """Background task to pull a model from Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://ollama:11434/api/pull",
                json={"name": model_name},
                timeout=300.0  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                logger.info("Model pulled successfully", model=model_name)
            else:
                logger.error("Model pull failed", model=model_name, status_code=response.status_code)
                
    except Exception as e:
        logger.error("Model pull task failed", model=model_name, error=str(e))
