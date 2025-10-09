"""
Configuration management for the API Gateway
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "Data Ingestion Platform API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Security
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Enhanced Security Settings
    master_encryption_key: str = os.getenv("MASTER_ENCRYPTION_KEY", "enterprise-master-key-change-in-production")
    mfa_issuer_name: str = os.getenv("MFA_ISSUER_NAME", "Nuve Enterprise Platform")
    
    # Email/SMTP Configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "security@company.com")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "smtp_password")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Session Management
    session_timeout_minutes: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "480"))
    max_concurrent_sessions: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))
    
    # Account Security
    failed_login_lockout_minutes: int = int(os.getenv("FAILED_LOGIN_LOCKOUT_MINUTES", "30"))
    max_failed_login_attempts: int = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
    
    # CORS and Hosts
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://frontend:80"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "api-gateway"]
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/dataplatform")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Elasticsearch
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    elasticsearch_index_prefix: str = "dataplatform"
    
    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    minio_secure: bool = False
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # File Processing
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/html",
        "application/json",
        "text/csv"
    ]
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False