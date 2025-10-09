"""
Base Data Source Classes
========================

Core abstractions and interfaces for data source connectors.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from .abstract_data_source import (
    AbstractDataSource, StandardDocument, SourceType, DocumentType,
    Author, Entity, Relationship,
    DataSourceError, AuthenticationError, RateLimitError, 
    DocumentNotFoundError, ConfigurationError, NetworkError
)

__all__ = [
    "AbstractDataSource",
    "StandardDocument", 
    "SourceType",
    "DocumentType",
    "Author",
    "Entity",
    "Relationship",
    "DataSourceError",
    "AuthenticationError",
    "RateLimitError",
    "DocumentNotFoundError",
    "ConfigurationError",
    "NetworkError"
]
