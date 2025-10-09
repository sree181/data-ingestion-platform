"""
Data Source Registry
====================

Central registry for managing all available data source connectors.
This provides a single point of access to all external data sources
and handles their lifecycle management.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from ..base.abstract_data_source import AbstractDataSource, SourceType, DocumentType

logger = logging.getLogger(__name__)

@dataclass
class SourceInfo:
    """Information about a registered data source"""
    name: str
    display_name: str
    source_type: SourceType
    connector_class: Type[AbstractDataSource]
    is_enabled: bool = True
    config: Dict[str, Any] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    error_count: int = 0
    last_error: Optional[str] = None

class DataSourceRegistry:
    """
    Registry for managing all available data source connectors
    
    This class provides:
    - Registration and discovery of data sources
    - Health monitoring and status tracking
    - Configuration management
    - Source filtering and querying
    """
    
    def __init__(self):
        self._sources: Dict[str, SourceInfo] = {}
        self._connectors: Dict[str, AbstractDataSource] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the registry"""
        self.logger = logging.getLogger("data_source_registry")
    
    def register(
        self, 
        connector_class: Type[AbstractDataSource], 
        config: Dict[str, Any] = None,
        enabled: bool = True
    ) -> bool:
        """
        Register a new data source connector
        
        Args:
            connector_class: Class that implements AbstractDataSource
            config: Configuration for this source
            enabled: Whether this source is enabled by default
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Create a temporary instance to get source info
            temp_instance = connector_class(api_key=config.get("api_key") if config else None)
            
            source_info = SourceInfo(
                name=temp_instance.source_name,
                display_name=temp_instance.display_name,
                source_type=temp_instance.source_type,
                connector_class=connector_class,
                is_enabled=enabled,
                config=config or {}
            )
            
            self._sources[source_info.name] = source_info
            self.logger.info(f"Registered data source: {source_info.display_name} ({source_info.name})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register data source {connector_class.__name__}: {e}")
            return False
    
    def unregister(self, source_name: str) -> bool:
        """
        Unregister a data source
        
        Args:
            source_name: Name of the source to unregister
            
        Returns:
            True if unregistered successfully, False otherwise
        """
        if source_name in self._sources:
            del self._sources[source_name]
            if source_name in self._connectors:
                del self._connectors[source_name]
            self.logger.info(f"Unregistered data source: {source_name}")
            return True
        return False
    
    def get_source(self, name: str) -> Optional[AbstractDataSource]:
        """
        Get a specific source connector by name
        
        Args:
            name: Name of the source
            
        Returns:
            Data source connector instance or None if not found
        """
        if name not in self._sources:
            return None
        
        # Return cached instance if available
        if name in self._connectors:
            return self._connectors[name]
        
        # Create new instance
        source_info = self._sources[name]
        try:
            connector = source_info.connector_class(
                api_key=source_info.config.get("api_key"),
                config=source_info.config
            )
            self._connectors[name] = connector
            return connector
        except Exception as e:
            self.logger.error(f"Failed to create connector for {name}: {e}")
            return None
    
    def get_all_sources(self) -> List[AbstractDataSource]:
        """
        Get all registered and enabled source connectors
        
        Returns:
            List of all enabled data source connectors
        """
        connectors = []
        for name, source_info in self._sources.items():
            if source_info.is_enabled:
                connector = self.get_source(name)
                if connector:
                    connectors.append(connector)
        return connectors
    
    def get_sources_by_type(self, source_type: SourceType) -> List[AbstractDataSource]:
        """
        Get sources filtered by type
        
        Args:
            source_type: Type of sources to return
            
        Returns:
            List of connectors matching the type
        """
        connectors = []
        for name, source_info in self._sources.items():
            if source_info.is_enabled and source_info.source_type == source_type:
                connector = self.get_source(name)
                if connector:
                    connectors.append(connector)
        return connectors
    
    def get_sources_by_document_type(self, document_type: DocumentType) -> List[AbstractDataSource]:
        """
        Get sources that support a specific document type
        
        Args:
            document_type: Document type to filter by
            
        Returns:
            List of connectors that support this document type
        """
        connectors = []
        for name, source_info in self._sources.items():
            if source_info.is_enabled:
                connector = self.get_source(name)
                if connector and document_type in connector.supported_document_types:
                    connectors.append(connector)
        return connectors
    
    def get_source_info(self, name: str) -> Optional[SourceInfo]:
        """Get information about a specific source"""
        return self._sources.get(name)
    
    def get_all_source_info(self) -> List[SourceInfo]:
        """Get information about all registered sources"""
        return list(self._sources.values())
    
    def enable_source(self, name: str) -> bool:
        """Enable a data source"""
        if name in self._sources:
            self._sources[name].is_enabled = True
            self.logger.info(f"Enabled data source: {name}")
            return True
        return False
    
    def disable_source(self, name: str) -> bool:
        """Disable a data source"""
        if name in self._sources:
            self._sources[name].is_enabled = False
            self.logger.info(f"Disabled data source: {name}")
            return True
        return False
    
    def update_config(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration for a source
        
        Args:
            name: Name of the source
            config: New configuration
            
        Returns:
            True if updated successfully, False otherwise
        """
        if name in self._sources:
            self._sources[name].config.update(config)
            # Clear cached connector to force recreation with new config
            if name in self._connectors:
                del self._connectors[name]
            self.logger.info(f"Updated config for data source: {name}")
            return True
        return False
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all enabled sources
        
        Returns:
            Dictionary mapping source names to health status
        """
        health_results = {}
        
        for name, source_info in self._sources.items():
            if source_info.is_enabled:
                try:
                    connector = self.get_source(name)
                    if connector:
                        health_status = await connector.health_check()
                        health_results[name] = health_status
                        
                        # Update source info
                        source_info.last_health_check = datetime.now()
                        source_info.health_status = health_status.get("status", "unknown")
                        
                        if health_status.get("status") == "unhealthy":
                            source_info.error_count += 1
                            source_info.last_error = health_status.get("error")
                        else:
                            source_info.error_count = 0
                            source_info.last_error = None
                    else:
                        health_results[name] = {
                            "status": "error",
                            "error": "Failed to create connector"
                        }
                        source_info.health_status = "error"
                        source_info.error_count += 1
                        
                except Exception as e:
                    health_results[name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    source_info.health_status = "error"
                    source_info.error_count += 1
                    source_info.last_error = str(e)
                    self.logger.error(f"Health check failed for {name}: {e}")
        
        return health_results
    
    def get_healthy_sources(self) -> List[AbstractDataSource]:
        """Get all healthy and enabled sources"""
        healthy_sources = []
        for name, source_info in self._sources.items():
            if (source_info.is_enabled and 
                source_info.health_status == "healthy" and
                source_info.error_count < 3):  # Allow some failures
                connector = self.get_source(name)
                if connector:
                    healthy_sources.append(connector)
        return healthy_sources
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered sources"""
        total_sources = len(self._sources)
        enabled_sources = sum(1 for info in self._sources.values() if info.is_enabled)
        healthy_sources = sum(1 for info in self._sources.values() 
                            if info.is_enabled and info.health_status == "healthy")
        
        source_types = {}
        for info in self._sources.values():
            source_type = info.source_type.value
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "healthy_sources": healthy_sources,
            "unhealthy_sources": enabled_sources - healthy_sources,
            "source_types": source_types,
            "last_health_check": max(
                (info.last_health_check for info in self._sources.values() 
                 if info.last_health_check), 
                default=None
            )
        }
    
    def list_available_sources(self) -> List[Dict[str, Any]]:
        """Get a list of all available sources with their info"""
        sources = []
        for name, source_info in self._sources.items():
            connector = self.get_source(name)
            if connector:
                sources.append(connector.get_source_info())
            else:
                sources.append({
                    "name": source_info.name,
                    "display_name": source_info.display_name,
                    "type": source_info.source_type.value,
                    "is_enabled": source_info.is_enabled,
                    "health_status": source_info.health_status,
                    "error": "Failed to create connector"
                })
        return sources

# Global registry instance
_registry_instance: Optional[DataSourceRegistry] = None

def get_registry() -> DataSourceRegistry:
    """Get the global data source registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = DataSourceRegistry()
    return _registry_instance

def register_source(
    connector_class: Type[AbstractDataSource], 
    config: Dict[str, Any] = None,
    enabled: bool = True
) -> bool:
    """Register a source with the global registry"""
    return get_registry().register(connector_class, config, enabled)
