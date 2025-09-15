"""
Palantir-style Investigation Endpoints - Inline Implementation
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
import httpx
from pydantic import BaseModel, Field

# Pydantic Models for Investigation Features
class InvestigationCreate(BaseModel):
    title: str = Field(..., description="Investigation title")
    description: str = Field(..., description="Investigation description")
    created_by: str = Field(default="user1", description="User ID who created the investigation")
    tags: List[str] = Field(default=[], description="Investigation tags")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")

# Simple Investigation Functions
async def create_simple_investigation(title: str, description: str, created_by: str = "user1") -> Dict[str, Any]:
    """Create a simple investigation case"""
    case_id = str(uuid.uuid4())
    
    investigation_data = {
        "case_id": case_id,
        "title": title,
        "description": description,
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "tags": ["investigation"],
        "priority": "medium",
        "statistics": {
            "total_entities": 0,
            "total_relationships": 0,
            "total_documents": 0
        }
    }
    
    # Store in Elasticsearch
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"http://elasticsearch:9200/investigations/_doc/{case_id}",
                json=investigation_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return {"case_id": case_id, "status": "created", "data": investigation_data}
            else:
                return {"error": f"Failed to create investigation: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to create investigation: {str(e)}"}

async def list_simple_investigations() -> Dict[str, Any]:
    """List investigations"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://elasticsearch:9200/investigations/_search",
                json={"query": {"match_all": {}}, "sort": [{"created_at": {"order": "desc"}}], "size": 100},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                investigations = [
                    {**hit["_source"], "id": hit["_id"]} 
                    for hit in data.get("hits", {}).get("hits", [])
                ]
                return {"investigations": investigations, "total": len(investigations)}
            else:
                return {"investigations": [], "total": 0, "error": f"Search failed: {response.status_code}"}
        except Exception as e:
            return {"investigations": [], "total": 0, "error": f"Search failed: {str(e)}"}

async def explore_entity_simple(entity_id: str, depth: int = 2, confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """Simple entity exploration"""
    try:
        # Find documents containing the entity
        query = {
            "query": {
                "nested": {
                    "path": "openai_entities",
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"openai_entities.text.keyword": entity_id}},
                                {"range": {"openai_entities.confidence": {"gte": confidence_threshold}}}
                            ]
                        }
                    }
                }
            },
            "size": 50
        }
        
        connected_entities = []
        center_entity = None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data.get("hits", {}).get("hits", []):
                    doc = hit["_source"]
                    
                    # Find the center entity details
                    for entity in doc.get("openai_entities", []):
                        if entity["text"] == entity_id and not center_entity:
                            center_entity = {
                                "id": entity_id,
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "size": 10,
                                "color": "#ff6b35"
                            }
                    
                    # Get connected entities from same documents
                    for entity in doc.get("openai_entities", []):
                        if (entity["text"] != entity_id and 
                            entity["confidence"] >= confidence_threshold):
                            
                            connected_entities.append({
                                "id": entity["text"],
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "size": 6,
                                "color": get_entity_color_simple(entity["type"]),
                                "source_document": doc.get("title", "Unknown")
                            })
        
        # Remove duplicates
        unique_entities = {}
        for entity in connected_entities:
            if entity["id"] not in unique_entities:
                unique_entities[entity["id"]] = entity
            else:
                if entity["confidence"] > unique_entities[entity["id"]]["confidence"]:
                    unique_entities[entity["id"]] = entity
        
        connected_list = list(unique_entities.values())[:20]  # Limit to 20
        
        # Create network data
        nodes = []
        links = []
        
        if center_entity:
            nodes.append(center_entity)
            
            for entity in connected_list:
                nodes.append(entity)
                links.append({
                    "source": center_entity["id"],
                    "target": entity["id"],
                    "relationship": "CO_OCCURS",
                    "weight": entity["confidence"]
                })
        
        return {
            "center_entity": center_entity,
            "connected_entities": connected_list,
            "network_data": {"nodes": nodes, "links": links},
            "statistics": {
                "total_connections": len(connected_list),
                "unique_entity_types": len(set(e["type"] for e in connected_list)),
                "average_confidence": sum(e["confidence"] for e in connected_list) / len(connected_list) if connected_list else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Entity exploration failed: {str(e)}", "center_entity": None, "connected_entities": []}

def get_entity_color_simple(entity_type: str) -> str:
    """Get color for entity type"""
    colors = {
        "ORGANIZATION": "#2196F3",
        "PERSON": "#9C27B0", 
        "EVENT": "#F44336",
        "DATE": "#795548",
        "CONCEPT": "#607D8B",
        "REGULATION": "#FF5722"
    }
    return colors.get(entity_type, "#9E9E9E")

async def get_investigation_timeline(case_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get timeline for investigation"""
    try:
        # Simple timeline based on document timestamps
        query = {
            "query": {
                "range": {
                    "metadata.upload_date": {
                        "gte": start_date,
                        "lte": end_date
                    }
                }
            },
            "sort": [{"metadata.upload_date": {"order": "asc"}}],
            "size": 100
        }
        
        timeline_events = []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data.get("hits", {}).get("hits", []):
                    doc = hit["_source"]
                    timeline_events.append({
                        "id": hit["_id"],
                        "timestamp": doc["metadata"]["upload_date"],
                        "title": f"Document Processed: {doc['title'][:50]}...",
                        "description": doc.get("ai_summary", "")[:200] + "...",
                        "type": "document_processed",
                        "entities": doc.get("openai_entities", [])[:3],  # Top 3 entities
                        "confidence": 0.9
                    })
        
        return {
            "timeline_events": timeline_events,
            "statistics": {
                "total_events": len(timeline_events),
                "date_range": {"start": start_date, "end": end_date}
            }
        }
        
    except Exception as e:
        return {"error": f"Timeline generation failed: {str(e)}", "timeline_events": []}

async def advanced_search_simple(
    query: str = "",
    entity_types: Optional[str] = None,
    confidence_threshold: float = 0.5,
    size: int = 20,
    from_: int = 0
) -> Dict[str, Any]:
    """Advanced search with filters"""
    try:
        must_clauses = []
        
        if query and query.strip():
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content", "ai_summary"],
                    "fuzziness": "AUTO"
                }
            })
        
        if entity_types:
            types = [t.strip() for t in entity_types.split(",")]
            must_clauses.append({
                "nested": {
                    "path": "openai_entities",
                    "query": {
                        "bool": {
                            "must": [
                                {"terms": {"openai_entities.type": types}},
                                {"range": {"openai_entities.confidence": {"gte": confidence_threshold}}}
                            ]
                        }
                    }
                }
            })
        
        es_query = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}]
                }
            },
            "highlight": {
                "fields": {
                    "content": {},
                    "title": {},
                    "ai_summary": {}
                }
            },
            "size": size,
            "from": from_,
            "sort": [{"_score": {"order": "desc"}}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://elasticsearch:9200/documents/_search",
                json=es_query,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "query": query,
                    "filters": {
                        "entity_types": entity_types,
                        "confidence_threshold": confidence_threshold
                    },
                    "total": data.get("hits", {}).get("total", {}).get("value", 0),
                    "results": data.get("hits", {}).get("hits", []),
                    "took": data.get("took", 0)
                }
            else:
                return {"error": f"Search failed: {response.status_code}"}
                
    except Exception as e:
        return {"error": f"Advanced search failed: {str(e)}"}