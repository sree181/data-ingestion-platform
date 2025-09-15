"""
Kafka service for message queuing
"""

import asyncio
import json
from typing import Dict, Any, Optional
import structlog
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = structlog.get_logger(__name__)


class KafkaService:
    """Service for interacting with Apache Kafka"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[KafkaProducer] = None
        self.consumers: Dict[str, KafkaConsumer] = {}
    
    async def connect(self):
        """Initialize Kafka connection"""
        try:
            # Create producer
            self.producer = KafkaProducer(
                bootstrap_servers=[self.bootstrap_servers],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',
                retries=3,
                retry_backoff_ms=100
            )
            
            logger.info("Connected to Kafka", servers=self.bootstrap_servers)
            
        except Exception as e:
            logger.error("Failed to connect to Kafka", error=str(e))
            raise
    
    async def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        logger.info("Kafka connections closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Kafka health"""
        try:
            # Simple health check by getting cluster metadata
            if self.producer:
                metadata = self.producer.list_topics(timeout=5)
                return {
                    "status": "healthy",
                    "topics": len(metadata)
                }
            else:
                return {"status": "not_connected"}
                
        except Exception as e:
            logger.error("Kafka health check failed", error=str(e))
            raise
    
    async def send_message(
        self, 
        topic: str, 
        message: Dict[str, Any], 
        key: Optional[str] = None
    ) -> bool:
        """Send a message to Kafka topic"""
        
        if not self.producer:
            raise Exception("Kafka producer not initialized")
        
        try:
            future = self.producer.send(
                topic, 
                value=message, 
                key=key
            )
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            
            logger.debug("Message sent to Kafka", 
                        topic=topic,
                        partition=record_metadata.partition,
                        offset=record_metadata.offset)
            
            return True
            
        except KafkaError as e:
            logger.error("Failed to send Kafka message", topic=topic, error=str(e))
            return False
        except Exception as e:
            logger.error("Kafka send error", topic=topic, error=str(e))
            return False
    
    async def create_consumer(
        self, 
        topics: list, 
        group_id: str,
        auto_offset_reset: str = 'latest'
    ) -> str:
        """Create a Kafka consumer"""
        
        consumer_id = f"{group_id}_{len(self.consumers)}"
        
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=[self.bootstrap_servers],
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            
            self.consumers[consumer_id] = consumer
            
            logger.info("Kafka consumer created", 
                       consumer_id=consumer_id,
                       topics=topics,
                       group_id=group_id)
            
            return consumer_id
            
        except Exception as e:
            logger.error("Failed to create Kafka consumer", error=str(e))
            raise
    
    async def consume_messages(
        self, 
        consumer_id: str, 
        timeout_ms: int = 1000
    ) -> list:
        """Consume messages from Kafka"""
        
        if consumer_id not in self.consumers:
            raise Exception(f"Consumer {consumer_id} not found")
        
        consumer = self.consumers[consumer_id]
        
        try:
            # Poll for messages
            message_batch = consumer.poll(timeout_ms=timeout_ms)
            
            messages = []
            for topic_partition, msgs in message_batch.items():
                for message in msgs:
                    messages.append({
                        "topic": topic_partition.topic,
                        "partition": topic_partition.partition,
                        "offset": message.offset,
                        "key": message.key,
                        "value": message.value,
                        "timestamp": message.timestamp
                    })
            
            return messages
            
        except Exception as e:
            logger.error("Failed to consume Kafka messages", error=str(e))
            return []
    
    async def close_consumer(self, consumer_id: str):
        """Close a specific consumer"""
        if consumer_id in self.consumers:
            self.consumers[consumer_id].close()
            del self.consumers[consumer_id]
            logger.info("Kafka consumer closed", consumer_id=consumer_id)
    
    async def list_topics(self) -> list:
        """List available Kafka topics"""
        if not self.producer:
            raise Exception("Kafka producer not initialized")
        
        try:
            metadata = self.producer.list_topics(timeout=5)
            return list(metadata.topics.keys())
            
        except Exception as e:
            logger.error("Failed to list Kafka topics", error=str(e))
            return []
    
    async def create_topic(
        self, 
        topic_name: str, 
        num_partitions: int = 1, 
        replication_factor: int = 1
    ) -> bool:
        """Create a new Kafka topic"""
        try:
            # Note: This is a simplified version
            # In production, you'd use kafka-python-ng or AdminClient
            logger.info("Topic creation requested", 
                       topic=topic_name,
                       partitions=num_partitions,
                       replication=replication_factor)
            
            # For now, just log the request
            # Actual implementation would use KafkaAdminClient
            return True
            
        except Exception as e:
            logger.error("Failed to create Kafka topic", topic=topic_name, error=str(e))
            return False