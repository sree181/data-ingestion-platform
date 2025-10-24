"""
Hierarchical Configuration Management System
Environment-specific configs with validation and secret injection
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import hashlib
from pydantic import BaseModel, Field, validator
import hvac  # HashiCorp Vault client
import boto3  # AWS Secrets Manager
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Training configuration"""
    episodes: int = 1000
    max_steps_per_episode: int = 100
    evaluation_frequency: int = 50
    save_frequency: int = 100
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon: float = 0.1
    epsilon_min: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 32
    memory_size: int = 10000
    target_update_frequency: int = 100

@dataclass
class AgentConfig:
    """RL Agent configuration"""
    state_dim: int = 20
    action_dim: int = 10
    hidden_dim: int = 128
    network_layers: int = 3
    activation: str = "relu"
    dropout: float = 0.1
    weight_decay: float = 1e-5

@dataclass
class ModelConfig:
    """Model configuration"""
    model_name: str = "MultiObjectiveRLAgent"
    checkpoint_dir: str = "checkpoints"
    model_registry_url: str = "http://localhost:5000"
    model_version: str = "latest"
    auto_save: bool = True
    save_best_only: bool = True

@dataclass
class InfrastructureConfig:
    """Infrastructure configuration"""
    num_workers: int = 4
    prefetch_factor: int = 2
    pin_memory: bool = True
    distributed: bool = False
    gpu_enabled: bool = True
    mixed_precision: bool = True
    gradient_checkpointing: bool = False

@dataclass
class DataConfig:
    """Data configuration"""
    data_path: str = "data/training"
    cache_size: int = 10000
    batch_size: int = 32
    shuffle: bool = True
    validation_split: float = 0.2
    augmentation: bool = False
    compression: str = "gzip"

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    metrics_port: int = 8000
    log_level: str = "INFO"
    log_format: str = "json"
    enable_tracing: bool = True
    trace_endpoint: str = "http://localhost:14268/api/traces"

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: Optional[str] = None
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_secrets_manager: bool = False
    enable_audit_logging: bool = True
    data_encryption: bool = True

class ConfigSchema(BaseModel):
    """Configuration schema with validation"""
    training: TrainingConfig
    agent: AgentConfig
    model: ModelConfig
    infrastructure: InfrastructureConfig
    data: DataConfig
    monitoring: MonitoringConfig
    security: SecurityConfig
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('training')
    def validate_training_config(cls, v):
        if v.episodes <= 0:
            raise ValueError("Episodes must be positive")
        if v.learning_rate <= 0 or v.learning_rate >= 1:
            raise ValueError("Learning rate must be between 0 and 1")
        if v.gamma < 0 or v.gamma > 1:
            raise ValueError("Gamma must be between 0 and 1")
        return v
    
    @validator('agent')
    def validate_agent_config(cls, v):
        if v.state_dim <= 0:
            raise ValueError("State dimension must be positive")
        if v.action_dim <= 0:
            raise ValueError("Action dimension must be positive")
        if v.hidden_dim <= 0:
            raise ValueError("Hidden dimension must be positive")
        return v
    
    @validator('data')
    def validate_data_config(cls, v):
        if v.validation_split < 0 or v.validation_split >= 1:
            raise ValueError("Validation split must be between 0 and 1")
        if v.cache_size <= 0:
            raise ValueError("Cache size must be positive")
        return v

class SecretsManager:
    """Secure secrets management with multiple backends"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.vault_client = None
        self.aws_client = None
        self.encryption_key = None
        
        # Initialize backends
        self._initialize_vault()
        self._initialize_aws()
        self._initialize_encryption()
    
    def _initialize_vault(self):
        """Initialize HashiCorp Vault client"""
        if self.config.vault_url and self.config.vault_token:
            try:
                self.vault_client = hvac.Client(
                    url=self.config.vault_url,
                    token=self.config.vault_token
                )
                # Test connection
                self.vault_client.is_authenticated()
                logger.info("Vault client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vault client: {e}")
                self.vault_client = None
    
    def _initialize_aws(self):
        """Initialize AWS Secrets Manager client"""
        if self.config.aws_secrets_manager:
            try:
                self.aws_client = boto3.client(
                    'secretsmanager',
                    region_name=self.config.aws_region
                )
                logger.info("AWS Secrets Manager client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS client: {e}")
                self.aws_client = None
    
    def _initialize_encryption(self):
        """Initialize encryption key"""
        if self.config.encryption_key:
            self.encryption_key = self.config.encryption_key.encode()
        else:
            # Generate a new key (not recommended for production)
            self.encryption_key = Fernet.generate_key()
            logger.warning("Generated new encryption key - not recommended for production")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from configured backend"""
        # Try Vault first
        if self.vault_client:
            try:
                secret = self.vault_client.secrets.kv.v2.read_secret_version(path=key)
                return secret['data']['data']['value']
            except Exception as e:
                logger.debug(f"Failed to get secret from Vault: {e}")
        
        # Try AWS Secrets Manager
        if self.aws_client:
            try:
                response = self.aws_client.get_secret_value(SecretId=key)
                return response['SecretString']
            except Exception as e:
                logger.debug(f"Failed to get secret from AWS: {e}")
        
        # Try environment variable
        env_value = os.getenv(key)
        if env_value:
            return env_value
        
        # Return default
        return default
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in configured backend"""
        # Try Vault first
        if self.vault_client:
            try:
                self.vault_client.secrets.kv.v2.create_or_update_secret(
                    path=key,
                    secret={'value': value}
                )
                return True
            except Exception as e:
                logger.error(f"Failed to set secret in Vault: {e}")
        
        # Try AWS Secrets Manager
        if self.aws_client:
            try:
                self.aws_client.update_secret(
                    SecretId=key,
                    SecretString=value
                )
                return True
            except Exception as e:
                logger.error(f"Failed to set secret in AWS: {e}")
        
        # Fallback to environment variable
        os.environ[key] = value
        return True
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a value using the configured encryption key"""
        if not self.encryption_key:
            return value
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_value = fernet.encrypt(value.encode())
            return encrypted_value.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return value
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value using the configured encryption key"""
        if not self.encryption_key:
            return encrypted_value
        
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_value = fernet.decrypt(encrypted_value.encode())
            return decrypted_value.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value

class ConfigManager:
    """
    Hierarchical configuration management
    - Load from YAML/JSON files
    - Environment variable override
    - Schema validation (Pydantic)
    - Secret injection from vault
    - Hot reload for dynamic configs
    """
    
    def __init__(
        self,
        config_dir: str = "config",
        environment: str = "development",
        secrets_manager: Optional[SecretsManager] = None
    ):
        self.config_dir = Path(config_dir)
        self.environment = environment
        self.secrets_manager = secrets_manager
        self.config_cache = {}
        self.config_hash = None
        self.last_modified = None
        
        # Load configuration
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> ConfigSchema:
        """Load configuration from files and environment"""
        # Load base configuration
        base_config = self._load_config_file("base.yaml")
        
        # Load environment-specific configuration
        env_config = self._load_config_file(f"{self.environment}.yaml")
        
        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)
        
        # Apply environment variable overrides
        merged_config = self._apply_env_overrides(merged_config)
        
        # Inject secrets
        if self.secrets_manager:
            merged_config = self._inject_secrets(merged_config)
        
        # Validate configuration
        try:
            return ConfigSchema(**merged_config)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif filename.endswith('.json'):
                    return json.load(f) or {}
                else:
                    logger.warning(f"Unsupported configuration file format: {filename}")
                    return {}
        except Exception as e:
            logger.error(f"Failed to load configuration file {config_path}: {e}")
            return {}
    
    def _merge_configs(self, base_config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and environment configurations"""
        merged = base_config.copy()
        
        for key, value in env_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Define environment variable mappings
        env_mappings = {
            'TRAINING_EPISODES': ['training', 'episodes'],
            'TRAINING_LEARNING_RATE': ['training', 'learning_rate'],
            'TRAINING_BATCH_SIZE': ['training', 'batch_size'],
            'AGENT_STATE_DIM': ['agent', 'state_dim'],
            'AGENT_ACTION_DIM': ['agent', 'action_dim'],
            'AGENT_HIDDEN_DIM': ['agent', 'hidden_dim'],
            'DATA_PATH': ['data', 'data_path'],
            'DATA_CACHE_SIZE': ['data', 'cache_size'],
            'INFRASTRUCTURE_NUM_WORKERS': ['infrastructure', 'num_workers'],
            'INFRASTRUCTURE_GPU_ENABLED': ['infrastructure', 'gpu_enabled'],
            'MONITORING_LOG_LEVEL': ['monitoring', 'log_level'],
            'SECURITY_VAULT_URL': ['security', 'vault_url'],
            'SECURITY_VAULT_TOKEN': ['security', 'vault_token'],
            'SECURITY_AWS_REGION': ['security', 'aws_region'],
            'SECURITY_AWS_SECRETS_MANAGER': ['security', 'aws_secrets_manager']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert string value to appropriate type
                converted_value = self._convert_env_value(env_value)
                
                # Set value in nested config
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = converted_value
        
        return config
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # String value
        return value
    
    def _inject_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Inject secrets from secrets manager"""
        # Define secret mappings
        secret_mappings = {
            'encryption_key': ['security', 'encryption_key'],
            'vault_token': ['security', 'vault_token'],
            'model_registry_token': ['model', 'registry_token'],
            'monitoring_api_key': ['monitoring', 'api_key']
        }
        
        for secret_key, config_path in secret_mappings.items():
            secret_value = self.secrets_manager.get_secret(secret_key)
            if secret_value:
                # Set value in nested config
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = secret_value
        
        return config
    
    def get_config(self) -> ConfigSchema:
        """Get current configuration"""
        return self.config
    
    def get_training_config(self) -> TrainingConfig:
        """Get training configuration"""
        return self.config.training
    
    def get_agent_config(self) -> AgentConfig:
        """Get agent configuration"""
        return self.config.agent
    
    def get_model_config(self) -> ModelConfig:
        """Get model configuration"""
        return self.config.model
    
    def get_infrastructure_config(self) -> InfrastructureConfig:
        """Get infrastructure configuration"""
        return self.config.infrastructure
    
    def get_data_config(self) -> DataConfig:
        """Get data configuration"""
        return self.config.data
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self.config.monitoring
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security
    
    def reload_config(self) -> bool:
        """Reload configuration from files"""
        try:
            # Check if configuration files have changed
            if self._config_files_changed():
                self.config = self._load_configuration()
                logger.info("Configuration reloaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def _config_files_changed(self) -> bool:
        """Check if configuration files have changed"""
        config_files = [
            self.config_dir / "base.yaml",
            self.config_dir / f"{self.environment}.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                current_mtime = config_file.stat().st_mtime
                if self.last_modified is None or current_mtime > self.last_modified:
                    self.last_modified = current_mtime
                    return True
        
        return False
    
    def save_config(self, config: ConfigSchema, filename: Optional[str] = None) -> bool:
        """Save configuration to file"""
        try:
            if filename is None:
                filename = f"{self.environment}_saved.yaml"
            
            config_path = self.config_dir / filename
            
            # Convert to dictionary
            config_dict = config.dict()
            
            # Save to YAML file
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def validate_config(self, config: ConfigSchema) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        try:
            # Validate using Pydantic
            ConfigSchema(**config.dict())
        except Exception as e:
            errors.append(str(e))
        
        # Additional custom validations
        if config.training.episodes <= 0:
            errors.append("Training episodes must be positive")
        
        if config.agent.state_dim <= 0:
            errors.append("Agent state dimension must be positive")
        
        if config.data.validation_split < 0 or config.data.validation_split >= 1:
            errors.append("Data validation split must be between 0 and 1")
        
        return errors
    
    def get_config_hash(self) -> str:
        """Get hash of current configuration for change detection"""
        config_str = json.dumps(self.config.dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def export_config(self, format: str = "yaml") -> str:
        """Export configuration as string"""
        config_dict = self.config.dict()
        
        if format.lower() == "yaml":
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        elif format.lower() == "json":
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Factory function for easy configuration loading
def load_config(
    config_dir: str = "config",
    environment: Optional[str] = None,
    secrets_manager: Optional[SecretsManager] = None
) -> ConfigManager:
    """
    Load configuration with default settings
    
    Args:
        config_dir: Directory containing configuration files
        environment: Environment name (defaults to ENV environment variable)
        secrets_manager: Optional secrets manager for secret injection
        
    Returns:
        Configured ConfigManager instance
    """
    if environment is None:
        environment = os.getenv("ENV", "development")
    
    return ConfigManager(
        config_dir=config_dir,
        environment=environment,
        secrets_manager=secrets_manager
    )
