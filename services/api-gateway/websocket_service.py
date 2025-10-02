"""
WebSocket service for real-time ingestion updates
"""
import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Store active connections by project_id
        self.project_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections for general broadcasts
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, project_id: str = None):
        """Accept a WebSocket connection"""
        await websocket.accept()
        
        # Add to all connections
        self.all_connections.add(websocket)
        
        # Add to project-specific connections if project_id provided
        if project_id:
            if project_id not in self.project_connections:
                self.project_connections[project_id] = set()
            self.project_connections[project_id].add(websocket)
            logger.info(f"WebSocket connected for project {project_id}")
        else:
            logger.info("WebSocket connected (general)")
    
    def disconnect(self, websocket: WebSocket, project_id: str = None):
        """Remove a WebSocket connection"""
        # Remove from all connections
        self.all_connections.discard(websocket)
        
        # Remove from project-specific connections
        if project_id and project_id in self.project_connections:
            self.project_connections[project_id].discard(websocket)
            # Clean up empty project sets
            if not self.project_connections[project_id]:
                del self.project_connections[project_id]
        
        logger.info(f"WebSocket disconnected for project {project_id or 'general'}")
    
    async def send_to_project(self, project_id: str, message: Dict[str, Any]):
        """Send message to all connections for a specific project"""
        if project_id in self.project_connections:
            message["timestamp"] = datetime.utcnow().isoformat()
            message_str = json.dumps(message)
            
            # Send to all project connections
            disconnected = set()
            for websocket in self.project_connections[project_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected:
                self.disconnect(websocket, project_id)
            
            logger.info(f"Sent message to {len(self.project_connections[project_id])} connections for project {project_id}")
    
    async def send_to_all(self, message: Dict[str, Any]):
        """Send message to all connections"""
        message["timestamp"] = datetime.utcnow().isoformat()
        message_str = json.dumps(message)
        
        # Send to all connections
        disconnected = set()
        for websocket in self.all_connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
        
        logger.info(f"Sent message to {len(self.all_connections)} total connections")
    
    async def broadcast_ingestion_event(self, project_id: str, event_type: str, payload: Dict[str, Any]):
        """Broadcast an ingestion event to project subscribers"""
        message = {
            "type": "ingestion_event",
            "project_id": project_id,
            "event_type": event_type,
            "payload": payload
        }
        await self.send_to_project(project_id, message)
    
    async def broadcast_document_count_update(self, project_id: str, total_documents: int, recent_documents: int = 0):
        """Broadcast document count update"""
        message = {
            "type": "document_count_update",
            "project_id": project_id,
            "total_documents": total_documents,
            "recent_documents": recent_documents
        }
        await self.send_to_project(project_id, message)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

