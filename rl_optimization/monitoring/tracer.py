"""
Distributed Tracer for RL Training
OpenTelemetry integration with performance profiling
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import structlog
import threading
from contextlib import contextmanager
import uuid
import json
import os

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger-thrift")

logger = structlog.get_logger(__name__)

@dataclass
class TraceConfig:
    """Configuration for distributed tracing"""
    service_name: str = "rl-training"
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    sampling_rate: float = 1.0
    max_attributes: int = 32
    max_events: int = 128
    max_links: int = 128
    enable_auto_instrumentation: bool = True

class DistributedTracer:
    """
    Distributed tracing for debugging
    - OpenTelemetry integration
    - Trace episode execution
    - Track data flow across services
    - Performance profiling
    """
    
    def __init__(self, config: TraceConfig):
        """
        Initialize distributed tracer
        
        Args:
            config: Tracing configuration
        """
        self.config = config
        self.tracer = None
        self.trace_contexts = {}
        self.active_traces = {}
        
        if OPENTELEMETRY_AVAILABLE:
            self._setup_opentelemetry()
        else:
            self._setup_mock_tracer()
        
        logger.info("DistributedTracer initialized", service_name=config.service_name)
    
    def _setup_opentelemetry(self):
        """Setup OpenTelemetry tracing"""
        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": "1.0.0"
            })
            
            # Create tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            
            # Create Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=14268,
            )
            
            # Create span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info("OpenTelemetry tracing configured")
            
        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            self._setup_mock_tracer()
    
    def _setup_mock_tracer(self):
        """Setup mock tracer when OpenTelemetry is not available"""
        self.tracer = MockTracer()
        logger.info("Mock tracer configured")
    
    def start_trace(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace
        
        Args:
            name: Trace name
            attributes: Trace attributes
            
        Returns:
            Trace ID
        """
        try:
            trace_id = str(uuid.uuid4())
            
            if self.tracer:
                span = self.tracer.start_span(name)
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Store trace context
                self.trace_contexts[trace_id] = {
                    'span': span,
                    'name': name,
                    'start_time': time.time(),
                    'attributes': attributes or {}
                }
            
            self.active_traces[trace_id] = {
                'name': name,
                'start_time': time.time(),
                'attributes': attributes or {}
            }
            
            logger.debug(f"Started trace {trace_id}: {name}")
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to start trace: {e}")
            return str(uuid.uuid4())
    
    def end_trace(self, trace_id: str, status: str = "OK", attributes: Optional[Dict[str, Any]] = None):
        """
        End a trace
        
        Args:
            trace_id: Trace ID
            status: Trace status
            attributes: Additional attributes
        """
        try:
            if trace_id in self.trace_contexts:
                context = self.trace_contexts[trace_id]
                span = context['span']
                
                # Add final attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Set status
                if status == "OK":
                    span.set_status(Status(StatusCode.OK))
                else:
                    span.set_status(Status(StatusCode.ERROR, status))
                
                # End span
                span.end()
                
                # Remove from active traces
                del self.trace_contexts[trace_id]
            
            if trace_id in self.active_traces:
                trace_info = self.active_traces[trace_id]
                duration = time.time() - trace_info['start_time']
                
                logger.debug(f"Ended trace {trace_id}: {trace_info['name']} ({duration:.3f}s)")
                
                # Remove from active traces
                del self.active_traces[trace_id]
            
        except Exception as e:
            logger.error(f"Failed to end trace {trace_id}: {e}")
    
    def add_event(self, trace_id: str, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add event to trace
        
        Args:
            trace_id: Trace ID
            name: Event name
            attributes: Event attributes
        """
        try:
            if trace_id in self.trace_contexts:
                context = self.trace_contexts[trace_id]
                span = context['span']
                span.add_event(name, attributes or {})
            
            logger.debug(f"Added event to trace {trace_id}: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add event to trace {trace_id}: {e}")
    
    def add_attributes(self, trace_id: str, attributes: Dict[str, Any]):
        """
        Add attributes to trace
        
        Args:
            trace_id: Trace ID
            attributes: Attributes to add
        """
        try:
            if trace_id in self.trace_contexts:
                context = self.trace_contexts[trace_id]
                span = context['span']
                
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                
                # Update stored attributes
                context['attributes'].update(attributes)
            
            if trace_id in self.active_traces:
                self.active_traces[trace_id]['attributes'].update(attributes)
            
        except Exception as e:
            logger.error(f"Failed to add attributes to trace {trace_id}: {e}")
    
    def create_child_span(self, parent_trace_id: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Create child span
        
        Args:
            parent_trace_id: Parent trace ID
            name: Child span name
            attributes: Child span attributes
            
        Returns:
            Child span ID
        """
        try:
            child_span_id = str(uuid.uuid4())
            
            if parent_trace_id in self.trace_contexts:
                parent_context = self.trace_contexts[parent_trace_id]
                parent_span = parent_context['span']
                
                # Create child span
                child_span = self.tracer.start_span(name, parent=parent_span)
                if attributes:
                    for key, value in attributes.items():
                        child_span.set_attribute(key, value)
                
                # Store child span context
                self.trace_contexts[child_span_id] = {
                    'span': child_span,
                    'name': name,
                    'start_time': time.time(),
                    'attributes': attributes or {},
                    'parent_trace_id': parent_trace_id
                }
            
            logger.debug(f"Created child span {child_span_id} for parent {parent_trace_id}")
            return child_span_id
            
        except Exception as e:
            logger.error(f"Failed to create child span: {e}")
            return str(uuid.uuid4())
    
    @contextmanager
    def trace_context(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing"""
        trace_id = self.start_trace(name, attributes)
        try:
            yield trace_id
        finally:
            self.end_trace(trace_id)
    
    def get_active_traces(self) -> Dict[str, Any]:
        """Get information about active traces"""
        active_info = {}
        current_time = time.time()
        
        for trace_id, trace_info in self.active_traces.items():
            active_info[trace_id] = {
                'name': trace_info['name'],
                'duration': current_time - trace_info['start_time'],
                'attributes': trace_info['attributes']
            }
        
        return active_info
    
    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get trace statistics"""
        return {
            'active_traces': len(self.active_traces),
            'total_contexts': len(self.trace_contexts),
            'service_name': self.config.service_name,
            'sampling_rate': self.config.sampling_rate
        }
    
    def export_traces_to_file(self, filepath: str):
        """Export traces to file"""
        try:
            traces_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'config': self.config.__dict__,
                'active_traces': self.get_active_traces(),
                'statistics': self.get_trace_statistics()
            }
            
            with open(filepath, 'w') as f:
                json.dump(traces_data, f, indent=2, default=str)
            
            logger.info(f"Traces exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export traces: {e}")

class MockTracer:
    """Mock tracer when OpenTelemetry is not available"""
    
    def start_span(self, name: str, parent=None):
        return MockSpan(name)
    
    def get_current_span(self):
        return MockSpan("mock")

class MockSpan:
    """Mock span when OpenTelemetry is not available"""
    
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        self.events = []
        self.status = None
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict[str, Any]):
        self.events.append({'name': name, 'attributes': attributes})
    
    def set_status(self, status):
        self.status = status
    
    def end(self):
        pass

# Decorator for automatic tracing
def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for automatic function tracing"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            trace_name = name or f"{func.__module__}.{func.__name__}"
            
            # Get tracer from global context (simplified)
            tracer = DistributedTracer(TraceConfig())
            
            with tracer.trace_context(trace_name, attributes):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Factory function for easy tracing setup
def create_tracer(
    service_name: str = "rl-training",
    jaeger_endpoint: str = "http://localhost:14268/api/traces",
    sampling_rate: float = 1.0,
    **kwargs
) -> DistributedTracer:
    """
    Create distributed tracer with default configuration
    
    Args:
        service_name: Service name for tracing
        jaeger_endpoint: Jaeger endpoint
        sampling_rate: Sampling rate for traces
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured DistributedTracer
    """
    config = TraceConfig(
        service_name=service_name,
        jaeger_endpoint=jaeger_endpoint,
        sampling_rate=sampling_rate,
        **kwargs
    )
    
    return DistributedTracer(config)
