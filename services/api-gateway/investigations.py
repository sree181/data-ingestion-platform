"""
Investigation Management APIs - Palantir-style investigative analytics
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
import httpx
from pydantic import BaseModel, Field

# Pydantic Models
class InvestigationCreate(BaseModel):
    title: str = Field(..., description="Investigation title")
    description: str = Field(..., description="Investigation description")
    created_by: str = Field(..., description="User ID who created the investigation")
    tags: List[str] = Field(default=[], description="Investigation tags")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")

class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None

class EntityExploreRequest(BaseModel):
    entity_id: str = Field(..., description="Entity ID to explore")
    depth: int = Field(default=2, ge=1, le=5, description="Relationship depth (1-5)")
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence score")

class TemporalAnalysisRequest(BaseModel):
    case_id: str = Field(..., description="Investigation case ID")
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")
    granularity: str = Field(default="day", description="Time granularity: hour, day, week, month")
    entity_filter: Optional[List[str]] = Field(default=None, description="Filter by specific entities")

# Investigation Management
class InvestigationManager:
    def __init__(self, elasticsearch_url: str = "http://elasticsearch:9200", neo4j_uri: str = None):
        self.es_url = elasticsearch_url
        self.neo4j_uri = neo4j_uri
    
    async def create_investigation(self, investigation: InvestigationCreate) -> Dict[str, Any]:
        """Create a new investigation case"""
        case_id = str(uuid.uuid4())
        
        investigation_data = {
            "case_id": case_id,
            "title": investigation.title,
            "description": investigation.description,
            "created_by": investigation.created_by,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
            "priority": investigation.priority,
            "tags": investigation.tags,
            "entities": [],
            "relationships": [],
            "documents": [],
            "timeline_events": [],
            "insights": [],
            "statistics": {
                "total_entities": 0,
                "total_relationships": 0,
                "total_documents": 0,
                "total_events": 0
            }
        }
        
        # Store in Elasticsearch
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/investigations/_doc/{case_id}",
                json=investigation_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(status_code=500, detail="Failed to create investigation")
        
        return {"case_id": case_id, "status": "created", "data": investigation_data}
    
    async def get_investigation(self, case_id: str) -> Dict[str, Any]:
        """Get investigation details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.es_url}/investigations/_doc/{case_id}",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Investigation not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to retrieve investigation")
            
            return response.json()["_source"]
    
    async def update_investigation(self, case_id: str, updates: InvestigationUpdate) -> Dict[str, Any]:
        """Update investigation details"""
        update_data = {
            "doc": {
                "updated_at": datetime.utcnow().isoformat(),
                **{k: v for k, v in updates.dict().items() if v is not None}
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/investigations/_update/{case_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Investigation not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to update investigation")
        
        return {"case_id": case_id, "status": "updated"}
    
    async def list_investigations(self, user_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """List investigations with optional filters"""
        query = {
            "query": {"match_all": {}},
            "sort": [{"created_at": {"order": "desc"}}],
            "size": 100
        }
        
        # Add filters
        filters = []
        if user_id:
            filters.append({"term": {"created_by": user_id}})
        if status:
            filters.append({"term": {"status": status}})
        
        if filters:
            query["query"] = {"bool": {"must": filters}}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/investigations/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to list investigations")
            
            data = response.json()
            investigations = [
                {**hit["_source"], "id": hit["_id"]} 
                for hit in data["hits"]["hits"]
            ]
            
            return {
                "investigations": investigations,
                "total": data["hits"]["total"]["value"]
            }

# Entity Exploration
class EntityExplorer:
    def __init__(self, elasticsearch_url: str = "http://elasticsearch:9200", neo4j_uri: str = None):
        self.es_url = elasticsearch_url
        self.neo4j_uri = neo4j_uri
    
    async def explore_entity(self, request: EntityExploreRequest) -> Dict[str, Any]:
        """Deep exploration of entity connections - Palantir-style"""
        
        # Get entity details from Elasticsearch
        entity_details = await self._get_entity_details(request.entity_id)
        if not entity_details:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Find connected entities using multi-hop search
        connected_entities = await self._find_connected_entities(
            request.entity_id,
            request.depth,
            request.entity_types,
            request.confidence_threshold
        )
        
        # Get relationship paths
        relationship_paths = await self._get_relationship_paths(
            request.entity_id,
            connected_entities,
            request.depth
        )
        
        # Generate AI insights
        insights = await self._generate_entity_insights(entity_details, connected_entities)
        
        # Calculate network statistics
        stats = self._calculate_network_stats(entity_details, connected_entities, relationship_paths)
        
        return {
            "center_entity": entity_details,
            "connected_entities": connected_entities,
            "relationship_paths": relationship_paths,
            "insights": insights,
            "statistics": stats,
            "exploration_depth": request.depth,
            "total_connections": len(connected_entities)
        }
    
    async def _get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed entity information"""
        # Search for entity in documents
        query = {
            "query": {
                "nested": {
                    "path": "openai_entities",
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"openai_entities.text.keyword": entity_id}},
                            ]
                        }
                    }
                }
            },
            "size": 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["hits"]["hits"]:
                    doc = data["hits"]["hits"][0]["_source"]
                    # Find the specific entity in the document
                    for entity in doc.get("openai_entities", []):
                        if entity["text"] == entity_id:
                            return {
                                "id": entity_id,
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "source_document": doc.get("title", "Unknown")
                            }
        
        return None
    
    async def _find_connected_entities(self, entity_id: str, depth: int, entity_types: Optional[List[str]], confidence_threshold: float) -> List[Dict[str, Any]]:
        """Find entities connected to the target entity"""
        # This is a simplified version - in production, you'd use Neo4j for proper graph traversal
        
        # Find documents containing the entity
        query = {
            "query": {
                "nested": {
                    "path": "openai_entities",
                    "query": {
                        "term": {"openai_entities.text.keyword": entity_id}
                    }
                }
            },
            "size": 100
        }
        
        connected_entities = []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data["hits"]["hits"]:
                    doc = hit["_source"]
                    
                    # Get all entities from documents that contain our target entity
                    for entity in doc.get("openai_entities", []):
                        if (entity["text"] != entity_id and 
                            entity["confidence"] >= confidence_threshold and
                            (not entity_types or entity["type"] in entity_types)):
                            
                            connected_entities.append({
                                "id": entity["text"],
                                "label": entity["text"],
                                "type": entity["type"],
                                "confidence": entity["confidence"],
                                "description": entity.get("description", ""),
                                "connection_strength": entity["confidence"],
                                "source_document": doc.get("title", "Unknown")
                            })
        
        # Remove duplicates and sort by confidence
        unique_entities = {}
        for entity in connected_entities:
            if entity["id"] not in unique_entities:
                unique_entities[entity["id"]] = entity
            else:
                # Keep the one with higher confidence
                if entity["confidence"] > unique_entities[entity["id"]]["confidence"]:
                    unique_entities[entity["id"]] = entity
        
        return sorted(unique_entities.values(), key=lambda x: x["confidence"], reverse=True)[:50]  # Limit to top 50
    
    async def _get_relationship_paths(self, entity_id: str, connected_entities: List[Dict], depth: int) -> List[Dict[str, Any]]:
        """Get relationship paths between entities"""
        # This would be much more sophisticated with Neo4j
        paths = []
        
        for entity in connected_entities[:20]:  # Limit for performance
            paths.append({
                "source": entity_id,
                "target": entity["id"],
                "path_length": 1,  # Simplified - would be actual path length in graph DB
                "relationship_type": "CO_OCCURS",
                "strength": entity["confidence"],
                "intermediate_entities": []
            })
        
        return paths
    
    async def _generate_entity_insights(self, entity: Dict[str, Any], connected_entities: List[Dict]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights about the entity network"""
        insights = []
        
        # Entity type distribution
        type_counts = {}
        for connected in connected_entities:
            entity_type = connected["type"]
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        if type_counts:
            insights.append({
                "type": "network_composition",
                "title": "Network Composition",
                "description": f"Connected to {len(connected_entities)} entities across {len(type_counts)} different types",
                "data": type_counts,
                "confidence": 0.9
            })
        
        # High confidence connections
        high_conf_entities = [e for e in connected_entities if e["confidence"] > 0.8]
        if high_conf_entities:
            insights.append({
                "type": "strong_connections",
                "title": "Strong Connections",
                "description": f"Has {len(high_conf_entities)} high-confidence connections",
                "data": high_conf_entities[:5],  # Top 5
                "confidence": 0.85
            })
        
        return insights
    
    def _calculate_network_stats(self, entity: Dict, connected_entities: List[Dict], paths: List[Dict]) -> Dict[str, Any]:
        """Calculate network statistics"""
        return {
            "total_connections": len(connected_entities),
            "unique_entity_types": len(set(e["type"] for e in connected_entities)),
            "average_confidence": sum(e["confidence"] for e in connected_entities) / len(connected_entities) if connected_entities else 0,
            "max_confidence": max((e["confidence"] for e in connected_entities), default=0),
            "path_count": len(paths),
            "network_density": len(connected_entities) / 100,  # Simplified calculation
        }

# Temporal Analysis
class TemporalAnalyzer:
    def __init__(self, elasticsearch_url: str = "http://elasticsearch:9200"):
        self.es_url = elasticsearch_url
    
    async def analyze_temporal_patterns(self, request: TemporalAnalysisRequest) -> Dict[str, Any]:
        """Analyze temporal patterns in investigation data"""
        
        # Get timeline events
        timeline_events = await self._get_timeline_events(
            request.case_id,
            request.start_date,
            request.end_date,
            request.entity_filter
        )
        
        # Detect patterns
        patterns = await self._detect_temporal_patterns(timeline_events, request.granularity)
        
        # Activity clustering
        clusters = await self._detect_activity_clusters(timeline_events, request.granularity)
        
        # Generate insights
        insights = await self._generate_temporal_insights(timeline_events, patterns, clusters)
        
        return {
            "timeline_events": timeline_events,
            "patterns": patterns,
            "activity_clusters": clusters,
            "insights": insights,
            "statistics": {
                "total_events": len(timeline_events),
                "date_range": {
                    "start": request.start_date.isoformat(),
                    "end": request.end_date.isoformat()
                },
                "pattern_count": len(patterns),
                "cluster_count": len(clusters)
            }
        }
    
    async def _get_timeline_events(self, case_id: str, start_date: datetime, end_date: datetime, entity_filter: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Get timeline events for the investigation"""
        # This would query actual timeline/event data
        # For now, we'll simulate based on document timestamps and entity mentions
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {
                            "metadata.upload_date": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }}
                    ]
                }
            },
            "sort": [{"metadata.upload_date": {"order": "asc"}}],
            "size": 1000
        }
        
        if entity_filter:
            # Add entity filter
            entity_queries = []
            for entity in entity_filter:
                entity_queries.append({
                    "nested": {
                        "path": "openai_entities",
                        "query": {"term": {"openai_entities.text.keyword": entity}}
                    }
                })
            
            query["query"]["bool"]["should"] = entity_queries
            query["query"]["bool"]["minimum_should_match"] = 1
        
        events = []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.es_url}/documents/_search",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for hit in data["hits"]["hits"]:
                    doc = hit["_source"]
                    events.append({
                        "id": hit["_id"],
                        "timestamp": doc["metadata"]["upload_date"],
                        "title": f"Document: {doc['title']}",
                        "description": doc.get("ai_summary", "")[:200] + "...",
                        "type": "document_processed",
                        "entities": doc.get("openai_entities", [])[:5],  # Limit entities
                        "confidence": 0.9,
                        "metadata": {
                            "document_id": hit["_id"],
                            "document_title": doc["title"]
                        }
                    })
        
        return events
    
    async def _detect_temporal_patterns(self, events: List[Dict], granularity: str) -> List[Dict[str, Any]]:
        """Detect temporal patterns in events"""
        patterns = []
        
        if not events:
            return patterns
        
        # Group events by time period
        time_groups = {}
        for event in events:
            timestamp = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
            
            if granularity == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif granularity == "day":
                key = timestamp.strftime("%Y-%m-%d")
            elif granularity == "week":
                key = timestamp.strftime("%Y-W%U")
            else:  # month
                key = timestamp.strftime("%Y-%m")
            
            if key not in time_groups:
                time_groups[key] = []
            time_groups[key].append(event)
        
        # Detect spikes (periods with unusually high activity)
        event_counts = [len(events) for events in time_groups.values()]
        if event_counts:
            avg_count = sum(event_counts) / len(event_counts)
            threshold = avg_count * 2  # Simple spike detection
            
            for time_key, time_events in time_groups.items():
                if len(time_events) > threshold:
                    patterns.append({
                        "type": "activity_spike",
                        "time_period": time_key,
                        "event_count": len(time_events),
                        "description": f"High activity period with {len(time_events)} events",
                        "confidence": min(len(time_events) / threshold, 1.0)
                    })
        
        return patterns
    
    async def _detect_activity_clusters(self, events: List[Dict], granularity: str) -> List[Dict[str, Any]]:
        """Detect clusters of related activity"""
        clusters = []
        
        # Simple clustering by entity co-occurrence
        entity_groups = {}
        
        for event in events:
            entities = [e["text"] for e in event.get("entities", [])]
            if len(entities) >= 2:
                # Create signature for this entity combination
                signature = tuple(sorted(entities))
                if signature not in entity_groups:
                    entity_groups[signature] = []
                entity_groups[signature].append(event)
        
        # Find significant clusters
        for entities, cluster_events in entity_groups.items():
            if len(cluster_events) >= 2:  # At least 2 events to form a cluster
                clusters.append({
                    "id": str(hash(entities)),
                    "entities": list(entities),
                    "event_count": len(cluster_events),
                    "time_span": {
                        "start": min(e["timestamp"] for e in cluster_events),
                        "end": max(e["timestamp"] for e in cluster_events)
                    },
                    "events": cluster_events,
                    "description": f"Cluster of {len(cluster_events)} events involving {', '.join(entities[:3])}"
                })
        
        return sorted(clusters, key=lambda x: x["event_count"], reverse=True)
    
    async def _generate_temporal_insights(self, events: List[Dict], patterns: List[Dict], clusters: List[Dict]) -> List[Dict[str, Any]]:
        """Generate insights from temporal analysis"""
        insights = []
        
        if events:
            # Time distribution insight
            insights.append({
                "type": "time_distribution",
                "title": "Activity Distribution",
                "description": f"Analysis of {len(events)} events showing temporal patterns",
                "confidence": 0.8
            })
        
        if patterns:
            # Pattern insights
            spike_patterns = [p for p in patterns if p["type"] == "activity_spike"]
            if spike_patterns:
                insights.append({
                    "type": "activity_spikes",
                    "title": "Activity Spikes Detected",
                    "description": f"Found {len(spike_patterns)} periods of unusually high activity",
                    "data": spike_patterns,
                    "confidence": 0.85
                })
        
        if clusters:
            # Clustering insights
            insights.append({
                "type": "entity_clustering",
                "title": "Entity Interaction Patterns",
                "description": f"Identified {len(clusters)} clusters of related activity",
                "data": clusters[:3],  # Top 3 clusters
                "confidence": 0.75
            })
        
        return insights

# Initialize managers
investigation_manager = InvestigationManager()
entity_explorer = EntityExplorer()
temporal_analyzer = TemporalAnalyzer()