"""
Source Configuration Service
============================

Manages external data source configuration, API keys, health monitoring,
and synchronization settings.

Author: Document Intelligence Platform Team
Date: October 2025
"""

import asyncio
import httpx
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
from cryptography.fernet import Fernet
import os

logger = structlog.get_logger()


class SourceConfigurationService:
    """
    Service for managing data source configurations
    
    Features:
    - CRUD operations for source configs
    - API key encryption/decryption
    - Health monitoring
    - Rate limit tracking
    - Sync scheduling
    """
    
    # Source definitions with metadata
    SOURCES = {
        "clinicaltrials": {
            "id": "clinicaltrials",
            "name": "ClinicalTrials.gov",
            "display_name": "ClinicalTrials.gov",
            "description": "US National Library of Medicine clinical trials database",
            "category": "Clinical Trials",
            "api_base_url": "https://clinicaltrials.gov/api/v2",
            "api_key_required": False,
            "rate_limit_per_second": 1,
            "rate_limit_per_minute": 60,
            "features": ["Real-time data", "Global coverage", "Detailed trial info"],
            "endpoints": {
                "search": "/studies",
                "details": "/studies/{nct_id}"
            },
            "health_check_url": "https://clinicaltrials.gov/api/v2/version",
            "documentation_url": "https://clinicaltrials.gov/data-api/api",
            "icon": "clinical_trials",
            "color": "#1976d2"
        },
        "fda_openfda": {
            "id": "fda_openfda",
            "name": "FDA OpenFDA",
            "display_name": "FDA OpenFDA",
            "description": "US Food and Drug Administration open data",
            "category": "Regulatory",
            "api_base_url": "https://api.fda.gov",
            "api_key_required": False,
            "rate_limit_per_second": 1,
            "rate_limit_per_minute": 40,
            "rate_limit_per_day": 1000,
            "features": ["Adverse events", "Drug labels", "Safety data"],
            "endpoints": {
                "drug_events": "/drug/event.json",
                "drug_labels": "/drug/label.json",
                "device_events": "/device/event.json"
            },
            "health_check_url": "https://api.fda.gov/drug/event.json?limit=1",
            "documentation_url": "https://open.fda.gov/apis/",
            "icon": "shield",
            "color": "#d32f2f"
        },
        "chembl": {
            "id": "chembl",
            "name": "ChEMBL",
            "display_name": "ChEMBL",
            "description": "EMBL-EBI chemical database of bioactive molecules",
            "category": "Chemical Database",
            "api_base_url": "https://www.ebi.ac.uk/chembl/api/data",
            "api_key_required": True,
            "rate_limit_per_second": 2,
            "rate_limit_per_minute": 120,
            "features": ["2.3M+ compounds", "19M+ bioactivity data", "Drug targets"],
            "endpoints": {
                "molecule": "/molecule",
                "target": "/target",
                "assay": "/assay"
            },
            "health_check_url": "https://www.ebi.ac.uk/chembl/api/data/status",
            "documentation_url": "https://chembl.gitbook.io/chembl-interface-documentation/",
            "icon": "science",
            "color": "#00897b"
        },
        "semantic_scholar": {
            "id": "semantic_scholar",
            "name": "Semantic Scholar",
            "display_name": "Semantic Scholar",
            "description": "AI-powered research tool for scientific literature",
            "category": "Research Papers",
            "api_base_url": "https://api.semanticscholar.org/graph/v1",
            "api_key_required": False,
            "rate_limit_per_second": 5,
            "rate_limit_per_minute": 300,
            "features": ["200M+ papers", "Citation analysis", "AI recommendations"],
            "endpoints": {
                "paper": "/paper",
                "author": "/author",
                "search": "/paper/search"
            },
            "health_check_url": "https://api.semanticscholar.org/graph/v1/paper/649def34f8be52c8b66281af98ae884c09aef38b",
            "documentation_url": "https://api.semanticscholar.org/",
            "icon": "school",
            "color": "#5e35b1"
        },
        "europe_pmc": {
            "id": "europe_pmc",
            "name": "Europe PMC",
            "display_name": "Europe PMC",
            "description": "European PubMed Central - European research papers",
            "category": "Research Papers",
            "api_base_url": "https://www.ebi.ac.uk/europepmc/webservices/rest",
            "api_key_required": False,
            "rate_limit_per_second": 3,
            "rate_limit_per_minute": 180,
            "features": ["40M+ publications", "Full-text access", "Citations"],
            "endpoints": {
                "search": "/search",
                "article": "/article/{source}/{id}"
            },
            "health_check_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=malaria&format=json&pageSize=1",
            "documentation_url": "https://europepmc.org/RestfulWebService",
            "icon": "article",
            "color": "#f57c00"
        }
    }
    
    def __init__(self):
        """Initialize the source configuration service"""
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
        if isinstance(self.encryption_key, str):
            self.encryption_key = self.encryption_key.encode()
        self.cipher = Fernet(self.encryption_key)
        
        # In-memory storage (in production, use database)
        self.configurations = {}
        self.health_status = {}
        self.last_sync = {}
        
        # Initialize default configurations
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default configurations for all sources"""
        for source_id, source_info in self.SOURCES.items():
            self.configurations[source_id] = {
                "id": source_id,
                "enabled": True,
                "api_key": None,
                "api_key_encrypted": None,
                "rate_limit_per_second": source_info.get("rate_limit_per_second", 1),
                "rate_limit_per_minute": source_info.get("rate_limit_per_minute", 60),
                "rate_limit_per_day": source_info.get("rate_limit_per_day", 10000),
                "last_sync_at": None,
                "sync_frequency_hours": 24,
                "auto_sync_enabled": False,
                "custom_config": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.health_status[source_id] = {
                "status": "unknown",
                "last_check": None,
                "response_time_ms": 0,
                "error_message": None
            }
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key"""
        if not api_key:
            return None
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        if not encrypted_key:
            return None
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    async def get_all_sources(self, include_disabled: bool = True) -> List[Dict[str, Any]]:
        """
        Get all data sources with their configuration and status
        
        Args:
            include_disabled: Whether to include disabled sources
            
        Returns:
            List of source configurations
        """
        sources = []
        
        for source_id, source_info in self.SOURCES.items():
            config = self.configurations.get(source_id, {})
            health = self.health_status.get(source_id, {})
            
            if not include_disabled and not config.get("enabled", False):
                continue
            
            # Calculate documents count (mock for now)
            documents_count = self._get_documents_count(source_id)
            
            source_data = {
                **source_info,
                "enabled": config.get("enabled", True),
                "api_key_configured": bool(config.get("api_key_encrypted")),
                "health_status": health.get("status", "unknown"),
                "last_check": health.get("last_check"),
                "response_time_ms": health.get("response_time_ms", 0),
                "error_message": health.get("error_message"),
                "last_sync_at": config.get("last_sync_at"),
                "documents_count": documents_count,
                "rate_limit": self._format_rate_limit(config),
                "auto_sync_enabled": config.get("auto_sync_enabled", False),
                "sync_frequency_hours": config.get("sync_frequency_hours", 24)
            }
            
            sources.append(source_data)
        
        return sources
    
    def _get_documents_count(self, source_id: str) -> int:
        """Get document count for a source (mock implementation)"""
        # In production, query Elasticsearch
        counts = {
            "clinicaltrials": 456789,
            "fda_openfda": 1234567,
            "chembl": 0,  # Requires API key
            "semantic_scholar": 2345678,
            "europe_pmc": 3456789
        }
        return counts.get(source_id, 0)
    
    def _format_rate_limit(self, config: Dict) -> str:
        """Format rate limit for display"""
        per_sec = config.get("rate_limit_per_second", 1)
        return f"{per_sec} req/sec"
    
    async def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific source by ID"""
        if source_id not in self.SOURCES:
            return None
        
        sources = await self.get_all_sources()
        return next((s for s in sources if s["id"] == source_id), None)
    
    async def update_source_config(
        self, 
        source_id: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update source configuration
        
        Args:
            source_id: Source identifier
            config: Configuration data
            
        Returns:
            Updated configuration
        """
        if source_id not in self.SOURCES:
            raise ValueError(f"Source {source_id} not found")
        
        current_config = self.configurations[source_id]
        
        # Handle API key encryption
        if "api_key" in config and config["api_key"]:
            encrypted_key = self.encrypt_api_key(config["api_key"])
            current_config["api_key_encrypted"] = encrypted_key
            current_config["api_key"] = config["api_key"]  # Store temporarily
        
        # Update other fields
        updateable_fields = [
            "enabled", "rate_limit_per_second", "rate_limit_per_minute",
            "rate_limit_per_day", "sync_frequency_hours", "auto_sync_enabled",
            "custom_config"
        ]
        
        for field in updateable_fields:
            if field in config:
                current_config[field] = config[field]
        
        current_config["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Updated configuration for source: {source_id}")
        
        return await self.get_source_by_id(source_id)
    
    async def toggle_source(self, source_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a source"""
        if source_id not in self.SOURCES:
            raise ValueError(f"Source {source_id} not found")
        
        self.configurations[source_id]["enabled"] = enabled
        self.configurations[source_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Source {source_id} {'enabled' if enabled else 'disabled'}")
        
        return await self.get_source_by_id(source_id)
    
    async def check_source_health(self, source_id: str) -> Dict[str, Any]:
        """
        Check health of a specific source
        
        Args:
            source_id: Source identifier
            
        Returns:
            Health status
        """
        if source_id not in self.SOURCES:
            raise ValueError(f"Source {source_id} not found")
        
        source_info = self.SOURCES[source_id]
        health_check_url = source_info.get("health_check_url")
        
        if not health_check_url:
            return {
                "status": "unknown",
                "message": "No health check URL configured",
                "last_check": datetime.now().isoformat()
            }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(health_check_url)
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    status = "healthy"
                    message = "Service is operational"
                else:
                    status = "unhealthy"
                    message = f"HTTP {response.status_code}"
                
                self.health_status[source_id] = {
                    "status": status,
                    "last_check": datetime.now().isoformat(),
                    "response_time_ms": response_time_ms,
                    "error_message": None if status == "healthy" else message
                }
                
                logger.info(f"Health check for {source_id}: {status} ({response_time_ms}ms)")
                
                return self.health_status[source_id]
                
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            
            self.health_status[source_id] = {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "response_time_ms": response_time_ms,
                "error_message": str(e)
            }
            
            logger.error(f"Health check failed for {source_id}: {str(e)}")
            
            return self.health_status[source_id]
    
    async def check_all_health(self) -> Dict[str, Any]:
        """Check health of all sources"""
        tasks = [
            self.check_source_health(source_id)
            for source_id in self.SOURCES.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_summary = {}
        for source_id, result in zip(self.SOURCES.keys(), results):
            if isinstance(result, Exception):
                health_summary[source_id] = {
                    "status": "error",
                    "error_message": str(result)
                }
            else:
                health_summary[source_id] = result
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sources": health_summary,
            "summary": {
                "total": len(self.SOURCES),
                "healthy": sum(1 for h in health_summary.values() if h.get("status") == "healthy"),
                "unhealthy": sum(1 for h in health_summary.values() if h.get("status") == "unhealthy"),
                "unknown": sum(1 for h in health_summary.values() if h.get("status") == "unknown")
            }
        }
    
    async def refresh_source(self, source_id: str) -> Dict[str, Any]:
        """Refresh/sync a source"""
        if source_id not in self.SOURCES:
            raise ValueError(f"Source {source_id} not found")
        
        # Check health first
        health = await self.check_source_health(source_id)
        
        if health["status"] == "healthy":
            self.configurations[source_id]["last_sync_at"] = datetime.now().isoformat()
            self.last_sync[source_id] = datetime.now()
            
            logger.info(f"Source {source_id} refreshed successfully")
            
            return {
                "success": True,
                "message": f"Source {source_id} refreshed successfully",
                "last_sync_at": self.configurations[source_id]["last_sync_at"]
            }
        else:
            return {
                "success": False,
                "message": f"Source {source_id} is unhealthy: {health.get('error_message', 'Unknown error')}"
            }
    
    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get overall statistics for all sources"""
        sources = await self.get_all_sources()
        
        total_documents = sum(s.get("documents_count", 0) for s in sources)
        enabled_count = sum(1 for s in sources if s.get("enabled", False))
        
        health_summary = await self.check_all_health()
        
        return {
            "total_sources": len(sources),
            "enabled_sources": enabled_count,
            "disabled_sources": len(sources) - enabled_count,
            "total_documents": total_documents,
            "health_summary": health_summary["summary"],
            "last_updated": datetime.now().isoformat()
        }
