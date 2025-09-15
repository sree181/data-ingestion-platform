"""
Configuration settings for the document processor service
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/data_platform")
    
    # MinIO settings
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "documents")
    
    # Elasticsearch settings
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    
    # Kafka settings
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    # Neo4j Aura settings
    neo4j_uri: str = os.getenv("NEO4J_URI", "neo4j+s://a857a30a.databases.neo4j.io")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "tWgpQzsTzGupIo5DGmos_AecmkgJYhSnL4gW_Z2012E")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # LlamaParse settings
    llamaparse_api_key: Optional[str] = os.getenv("LLAMAPARSE_API_KEY")
    use_llamaparse: bool = os.getenv("USE_LLAMAPARSE", "true").lower() == "true"
    
    # OpenAI settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Service settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))
    workers: int = int(os.getenv("WORKERS", "1"))
    
    # Processing settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "100000000"))  # 100MB
    supported_formats: list = ["pdf", "docx", "doc", "txt", "rtf"]
    
    # Vector embedding settings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()