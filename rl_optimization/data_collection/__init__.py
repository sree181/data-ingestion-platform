"""
RL Data Collection Module

This module provides comprehensive data collection capabilities for training
Reinforcement Learning models on the PV classification system.

Components:
- feature_extractor: Extracts document features and classification outcomes
- data_validator: Validates data quality and consistency
- data_collector: Main orchestrator for data collection from various sources

Usage:
    from rl_optimization.data_collection import RLDataCollectionOrchestrator
    
    orchestrator = RLDataCollectionOrchestrator()
    report = await orchestrator.collect_from_classification_service(
        "http://localhost:8012", max_documents=1000
    )
"""

from .feature_extractor import (
    DocumentFeatureExtractor,
    ClassificationOutcomeTracker,
    RLDataCollector,
    DocumentFeatures,
    ClassificationOutcome
)

from .data_validator import (
    DataValidator,
    ValidationResult
)

from .data_collector import (
    RLDataCollectionOrchestrator
)

__all__ = [
    'DocumentFeatureExtractor',
    'ClassificationOutcomeTracker', 
    'RLDataCollector',
    'DocumentFeatures',
    'ClassificationOutcome',
    'DataValidator',
    'ValidationResult',
    'RLDataCollectionOrchestrator'
]

__version__ = "1.0.0"
__author__ = "RL Optimization Team"
