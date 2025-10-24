"""
Data Protection Manager
Advanced data protection and privacy features for RL training
"""

import os
import hashlib
import secrets
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import structlog
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from pathlib import Path
import threading

logger = structlog.get_logger(__name__)

@dataclass
class DataProtectionConfig:
    """Configuration for data protection"""
    enable_data_anonymization: bool = True
    enable_data_masking: bool = True
    enable_differential_privacy: bool = True
    enable_data_retention: bool = True
    enable_data_classification: bool = True
    retention_period_days: int = 365
    anonymization_level: str = "high"  # low, medium, high
    masking_character: str = "*"
    differential_privacy_epsilon: float = 1.0
    data_classification_levels: List[str] = None

class DataAnonymizer:
    """Data anonymization utilities"""
    
    def __init__(self, level: str = "high"):
        self.level = level
        self.anonymization_mapping = {}
        self.anonymization_history = []
    
    def anonymize_text(self, text: str, field_type: str = "general") -> str:
        """Anonymize text data"""
        try:
            if self.level == "low":
                return self._low_level_anonymization(text, field_type)
            elif self.level == "medium":
                return self._medium_level_anonymization(text, field_type)
            else:  # high
                return self._high_level_anonymization(text, field_type)
                
        except Exception as e:
            logger.error(f"Text anonymization failed: {e}")
            return text
    
    def _low_level_anonymization(self, text: str, field_type: str) -> str:
        """Low level anonymization - minimal changes"""
        if field_type == "email":
            # Replace domain
            if "@" in text:
                local, domain = text.split("@", 1)
                return f"{local[:2]}***@{domain}"
        elif field_type == "phone":
            # Replace last 4 digits
            if len(text) >= 4:
                return text[:-4] + "****"
        elif field_type == "name":
            # Replace with first letter + asterisks
            if len(text) > 1:
                return text[0] + "*" * (len(text) - 1)
        
        return text
    
    def _medium_level_anonymization(self, text: str, field_type: str) -> str:
        """Medium level anonymization - moderate changes"""
        if field_type == "email":
            # Replace with generic format
            return "user@example.com"
        elif field_type == "phone":
            # Replace with generic format
            return "***-***-****"
        elif field_type == "name":
            # Replace with generic name
            return "Anonymous User"
        elif field_type == "id":
            # Replace with hash
            return hashlib.sha256(text.encode()).hexdigest()[:8]
        
        return "***"
    
    def _high_level_anonymization(self, text: str, field_type: str) -> str:
        """High level anonymization - maximum privacy"""
        # Always return generic placeholder
        return "***"
    
    def anonymize_structured_data(self, data: dict) -> dict:
        """Anonymize structured data"""
        try:
            anonymized_data = {}
            
            for key, value in data.items():
                if isinstance(value, str):
                    # Determine field type based on key name
                    field_type = self._determine_field_type(key)
                    anonymized_data[key] = self.anonymize_text(value, field_type)
                elif isinstance(value, dict):
                    anonymized_data[key] = self.anonymize_structured_data(value)
                elif isinstance(value, list):
                    anonymized_data[key] = [
                        self.anonymize_structured_data(item) if isinstance(item, dict)
                        else self.anonymize_text(str(item), "general")
                        for item in value
                    ]
                else:
                    anonymized_data[key] = value
            
            # Record anonymization
            self.anonymization_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "original_keys": list(data.keys()),
                "anonymized_keys": list(anonymized_data.keys()),
                "level": self.level
            })
            
            return anonymized_data
            
        except Exception as e:
            logger.error(f"Structured data anonymization failed: {e}")
            return data
    
    def _determine_field_type(self, key: str) -> str:
        """Determine field type based on key name"""
        key_lower = key.lower()
        
        if any(x in key_lower for x in ["email", "mail"]):
            return "email"
        elif any(x in key_lower for x in ["phone", "tel", "mobile"]):
            return "phone"
        elif any(x in key_lower for x in ["name", "firstname", "lastname"]):
            return "name"
        elif any(x in key_lower for x in ["id", "identifier", "uuid"]):
            return "id"
        elif any(x in key_lower for x in ["address", "street", "city"]):
            return "address"
        else:
            return "general"

class DataMasker:
    """Data masking utilities"""
    
    def __init__(self, mask_character: str = "*"):
        self.mask_character = mask_character
        self.masking_history = []
    
    def mask_sensitive_data(self, data: str, mask_ratio: float = 0.5) -> str:
        """Mask sensitive data with specified ratio"""
        try:
            if not data or len(data) < 2:
                return data
            
            # Calculate number of characters to mask
            mask_count = int(len(data) * mask_ratio)
            mask_count = max(1, min(mask_count, len(data) - 1))  # Keep at least 1 character
            
            # Create masked version
            masked_data = data[:1] + self.mask_character * mask_count + data[1 + mask_count:]
            
            # Record masking
            self.masking_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "original_length": len(data),
                "masked_length": len(masked_data),
                "mask_ratio": mask_ratio
            })
            
            return masked_data
            
        except Exception as e:
            logger.error(f"Data masking failed: {e}")
            return data
    
    def mask_structured_data(self, data: dict, sensitive_fields: List[str] = None) -> dict:
        """Mask sensitive fields in structured data"""
        try:
            if sensitive_fields is None:
                sensitive_fields = ["password", "token", "secret", "key", "ssn", "credit_card"]
            
            masked_data = {}
            
            for key, value in data.items():
                if isinstance(value, str) and any(field in key.lower() for field in sensitive_fields):
                    masked_data[key] = self.mask_sensitive_data(value)
                elif isinstance(value, dict):
                    masked_data[key] = self.mask_structured_data(value, sensitive_fields)
                elif isinstance(value, list):
                    masked_data[key] = [
                        self.mask_structured_data(item, sensitive_fields) if isinstance(item, dict)
                        else self.mask_sensitive_data(str(item)) if isinstance(item, str) and any(field in key.lower() for field in sensitive_fields)
                        else item
                        for item in value
                    ]
                else:
                    masked_data[key] = value
            
            return masked_data
            
        except Exception as e:
            logger.error(f"Structured data masking failed: {e}")
            return data

class DifferentialPrivacyManager:
    """Differential privacy implementation"""
    
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon
        self.privacy_budget = epsilon
        self.privacy_history = []
    
    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplace noise for differential privacy"""
        try:
            # Calculate noise scale
            scale = sensitivity / self.epsilon
            
            # Generate Laplace noise
            noise = np.random.laplace(0, scale)
            
            # Add noise to value
            noisy_value = value + noise
            
            # Record privacy usage
            self.privacy_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "original_value": value,
                "noisy_value": noisy_value,
                "noise": noise,
                "sensitivity": sensitivity,
                "epsilon": self.epsilon
            })
            
            return noisy_value
            
        except Exception as e:
            logger.error(f"Laplace noise addition failed: {e}")
            return value
    
    def add_gaussian_noise(self, value: float, sensitivity: float = 1.0, delta: float = 1e-5) -> float:
        """Add Gaussian noise for differential privacy"""
        try:
            # Calculate noise scale
            scale = (2 * np.log(1.25 / delta) * sensitivity**2) / (self.epsilon**2)
            scale = np.sqrt(scale)
            
            # Generate Gaussian noise
            noise = np.random.normal(0, scale)
            
            # Add noise to value
            noisy_value = value + noise
            
            # Record privacy usage
            self.privacy_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "original_value": value,
                "noisy_value": noisy_value,
                "noise": noise,
                "sensitivity": sensitivity,
                "epsilon": self.epsilon,
                "delta": delta
            })
            
            return noisy_value
            
        except Exception as e:
            logger.error(f"Gaussian noise addition failed: {e}")
            return value
    
    def apply_differential_privacy_to_dataset(self, dataset: List[dict], 
                                            numeric_fields: List[str] = None) -> List[dict]:
        """Apply differential privacy to entire dataset"""
        try:
            if numeric_fields is None:
                numeric_fields = ["age", "salary", "score", "count", "value"]
            
            private_dataset = []
            
            for record in dataset:
                private_record = record.copy()
                
                for field in numeric_fields:
                    if field in private_record and isinstance(private_record[field], (int, float)):
                        private_record[field] = self.add_laplace_noise(
                            float(private_record[field]),
                            sensitivity=1.0
                        )
                
                private_dataset.append(private_record)
            
            return private_dataset
            
        except Exception as e:
            logger.error(f"Dataset differential privacy failed: {e}")
            return dataset

class DataRetentionManager:
    """Data retention and lifecycle management"""
    
    def __init__(self, retention_period_days: int = 365):
        self.retention_period_days = retention_period_days
        self.retention_policies = {}
        self.retention_history = []
    
    def set_retention_policy(self, data_type: str, retention_days: int):
        """Set retention policy for data type"""
        self.retention_policies[data_type] = {
            "retention_days": retention_days,
            "created_at": datetime.utcnow()
        }
        logger.info(f"Retention policy set for {data_type}: {retention_days} days")
    
    def check_data_expiry(self, data: dict, data_type: str = "general") -> bool:
        """Check if data has expired based on retention policy"""
        try:
            # Get retention policy
            policy = self.retention_policies.get(data_type, {
                "retention_days": self.retention_period_days
            })
            
            # Get data creation time
            created_at = data.get("created_at", data.get("timestamp"))
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif not isinstance(created_at, datetime):
                created_at = datetime.utcnow()
            
            # Check if expired
            expiry_date = created_at + timedelta(days=policy["retention_days"])
            is_expired = datetime.utcnow() > expiry_date
            
            # Record check
            self.retention_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "data_type": data_type,
                "created_at": created_at.isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "is_expired": is_expired,
                "retention_days": policy["retention_days"]
            })
            
            return is_expired
            
        except Exception as e:
            logger.error(f"Data expiry check failed: {e}")
            return False
    
    def cleanup_expired_data(self, data_list: List[dict], data_type: str = "general") -> List[dict]:
        """Remove expired data from list"""
        try:
            active_data = []
            expired_count = 0
            
            for data in data_list:
                if self.check_data_expiry(data, data_type):
                    expired_count += 1
                else:
                    active_data.append(data)
            
            logger.info(f"Data cleanup completed: {expired_count} expired records removed")
            return active_data
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return data_list

class DataClassifier:
    """Data classification and sensitivity labeling"""
    
    def __init__(self, classification_levels: List[str] = None):
        self.classification_levels = classification_levels or [
            "public", "internal", "confidential", "restricted"
        ]
        self.classification_rules = {}
        self.classification_history = []
        
        # Initialize default classification rules
        self._initialize_classification_rules()
    
    def _initialize_classification_rules(self):
        """Initialize default classification rules"""
        self.classification_rules = {
            "public": {
                "keywords": ["public", "general", "open"],
                "sensitivity_score": 1
            },
            "internal": {
                "keywords": ["internal", "company", "team"],
                "sensitivity_score": 2
            },
            "confidential": {
                "keywords": ["confidential", "private", "sensitive"],
                "sensitivity_score": 3
            },
            "restricted": {
                "keywords": ["restricted", "secret", "classified", "top_secret"],
                "sensitivity_score": 4
            }
        }
    
    def classify_data(self, data: dict, context: str = "") -> str:
        """Classify data based on content and context"""
        try:
            # Extract text content for analysis
            text_content = self._extract_text_content(data)
            text_content += " " + context
            
            # Calculate sensitivity score
            sensitivity_score = self._calculate_sensitivity_score(text_content)
            
            # Determine classification level
            classification = self._determine_classification_level(sensitivity_score)
            
            # Record classification
            self.classification_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "sensitivity_score": sensitivity_score,
                "classification": classification,
                "context": context
            })
            
            return classification
            
        except Exception as e:
            logger.error(f"Data classification failed: {e}")
            return "internal"  # Default classification
    
    def _extract_text_content(self, data: dict) -> str:
        """Extract text content from data for analysis"""
        text_parts = []
        
        for key, value in data.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, dict):
                text_parts.append(self._extract_text_content(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        text_parts.append(self._extract_text_content(item))
        
        return " ".join(text_parts)
    
    def _calculate_sensitivity_score(self, text: str) -> int:
        """Calculate sensitivity score based on text content"""
        text_lower = text.lower()
        score = 1  # Start with public level
        
        for level, rules in self.classification_rules.items():
            for keyword in rules["keywords"]:
                if keyword in text_lower:
                    score = max(score, rules["sensitivity_score"])
        
        # Check for sensitive patterns
        sensitive_patterns = [
            "password", "secret", "key", "token", "ssn", "credit_card",
            "medical", "health", "patient", "diagnosis", "treatment"
        ]
        
        for pattern in sensitive_patterns:
            if pattern in text_lower:
                score = max(score, 3)  # At least confidential
        
        return score
    
    def _determine_classification_level(self, score: int) -> str:
        """Determine classification level based on score"""
        if score >= 4:
            return "restricted"
        elif score >= 3:
            return "confidential"
        elif score >= 2:
            return "internal"
        else:
            return "public"

class DataProtectionManager:
    """
    Main data protection management system
    - Data anonymization
    - Data masking
    - Differential privacy
    - Data retention
    - Data classification
    """
    
    def __init__(self, config: DataProtectionConfig):
        """
        Initialize data protection manager
        
        Args:
            config: Data protection configuration
        """
        self.config = config
        self.anonymizer = None
        self.masker = None
        self.privacy_manager = None
        self.retention_manager = None
        self.classifier = None
        
        # Initialize components
        self._initialize_components()
        
        logger.info("DataProtectionManager initialized", 
                   anonymization=config.enable_data_anonymization,
                   masking=config.enable_data_masking,
                   differential_privacy=config.enable_differential_privacy,
                   retention=config.enable_data_retention,
                   classification=config.enable_data_classification)
    
    def _initialize_components(self):
        """Initialize data protection components"""
        try:
            # Initialize anonymizer
            if self.config.enable_data_anonymization:
                self.anonymizer = DataAnonymizer(self.config.anonymization_level)
                logger.info("Data anonymizer initialized")
            
            # Initialize masker
            if self.config.enable_data_masking:
                self.masker = DataMasker(self.config.masking_character)
                logger.info("Data masker initialized")
            
            # Initialize privacy manager
            if self.config.enable_differential_privacy:
                self.privacy_manager = DifferentialPrivacyManager(
                    self.config.differential_privacy_epsilon
                )
                logger.info("Differential privacy manager initialized")
            
            # Initialize retention manager
            if self.config.enable_data_retention:
                self.retention_manager = DataRetentionManager(
                    self.config.retention_period_days
                )
                logger.info("Data retention manager initialized")
            
            # Initialize classifier
            if self.config.enable_data_classification:
                self.classifier = DataClassifier(self.config.data_classification_levels)
                logger.info("Data classifier initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize data protection components: {e}")
            raise
    
    def protect_data(self, data: dict, protection_level: str = "medium") -> dict:
        """Apply data protection based on level"""
        try:
            protected_data = data.copy()
            
            # Classify data first
            if self.classifier:
                classification = self.classifier.classify_data(protected_data)
                protected_data["_classification"] = classification
                protected_data["_protection_level"] = protection_level
            
            # Apply anonymization
            if self.anonymizer and protection_level in ["medium", "high"]:
                protected_data = self.anonymizer.anonymize_structured_data(protected_data)
            
            # Apply masking
            if self.masker and protection_level in ["low", "medium", "high"]:
                protected_data = self.masker.mask_structured_data(protected_data)
            
            # Apply differential privacy to numeric fields
            if self.privacy_manager and protection_level == "high":
                numeric_fields = ["age", "salary", "score", "count", "value", "reward", "loss"]
                for field in numeric_fields:
                    if field in protected_data and isinstance(protected_data[field], (int, float)):
                        protected_data[field] = self.privacy_manager.add_laplace_noise(
                            float(protected_data[field])
                        )
            
            return protected_data
            
        except Exception as e:
            logger.error(f"Data protection failed: {e}")
            return data
    
    def cleanup_expired_data(self, data_list: List[dict], data_type: str = "general") -> List[dict]:
        """Cleanup expired data based on retention policies"""
        if not self.retention_manager:
            return data_list
        
        return self.retention_manager.cleanup_expired_data(data_list, data_type)
    
    def get_protection_summary(self) -> Dict[str, Any]:
        """Get data protection summary"""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "anonymization_enabled": self.config.enable_data_anonymization,
                "masking_enabled": self.config.enable_data_masking,
                "differential_privacy_enabled": self.config.enable_differential_privacy,
                "retention_enabled": self.config.enable_data_retention,
                "classification_enabled": self.config.enable_data_classification,
                "anonymization_level": self.config.anonymization_level,
                "retention_period_days": self.config.retention_period_days,
                "differential_privacy_epsilon": self.config.differential_privacy_epsilon
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get protection summary: {e}")
            return {}

# Factory function for easy data protection manager setup
def create_data_protection_manager(
    enable_anonymization: bool = True,
    enable_masking: bool = True,
    enable_differential_privacy: bool = True,
    enable_retention: bool = True,
    enable_classification: bool = True,
    **kwargs
) -> DataProtectionManager:
    """
    Create data protection manager with default configuration
    
    Args:
        enable_anonymization: Enable data anonymization
        enable_masking: Enable data masking
        enable_differential_privacy: Enable differential privacy
        enable_retention: Enable data retention
        enable_classification: Enable data classification
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured DataProtectionManager
    """
    config = DataProtectionConfig(
        enable_data_anonymization=enable_anonymization,
        enable_data_masking=enable_masking,
        enable_differential_privacy=enable_differential_privacy,
        enable_data_retention=enable_retention,
        enable_data_classification=enable_classification,
        **kwargs
    )
    
    return DataProtectionManager(config)
