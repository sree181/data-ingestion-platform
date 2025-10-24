"""
Comprehensive Error Handling Framework
Implements retry logic, circuit breakers, graceful degradation, and detailed logging
"""

import logging
import time
import random
import threading
from typing import Dict, List, Any, Optional, Callable, Union, Type, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import traceback
import functools
import asyncio
from contextlib import contextmanager
import json
import uuid

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class RetryConfig:
    """Configuration for retry strategy"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (KeyboardInterrupt, SystemExit)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    success_threshold: int = 3

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    component: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: str
    context_data: Dict[str, Any]
    retry_count: int = 0
    circuit_state: Optional[CircuitState] = None

class RetryStrategy:
    """
    Configurable retry logic with exponential backoff and jitter
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.retry_stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'average_retry_time': 0.0
        }
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                
                # Update statistics on success
                if attempt > 0:
                    self.retry_stats['successful_retries'] += 1
                    retry_time = time.time() - start_time
                    self._update_average_retry_time(retry_time)
                
                return result
                
            except Exception as e:
                last_exception = e
                self.retry_stats['total_attempts'] += 1
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"Non-retryable exception: {e}")
                    raise e
                
                # Check if we have more attempts
                if attempt == self.config.max_attempts - 1:
                    self.retry_stats['failed_retries'] += 1
                    logger.error(f"All retry attempts failed for {func.__name__}")
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                time.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception
    
    async def async_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with retry logic
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                
                # Update statistics on success
                if attempt > 0:
                    self.retry_stats['successful_retries'] += 1
                    retry_time = time.time() - start_time
                    self._update_average_retry_time(retry_time)
                
                return result
                
            except Exception as e:
                last_exception = e
                self.retry_stats['total_attempts'] += 1
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"Non-retryable exception: {e}")
                    raise e
                
                # Check if we have more attempts
                if attempt == self.config.max_attempts - 1:
                    self.retry_stats['failed_retries'] += 1
                    logger.error(f"All retry attempts failed for {func.__name__}")
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        # Check if exception is in non-retryable list
        if isinstance(exception, self.config.non_retryable_exceptions):
            return False
        
        # Check if exception is in retryable list
        if isinstance(exception, self.config.retryable_exceptions):
            return True
        
        # Default to retryable for unknown exceptions
        return True
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return delay
    
    def _update_average_retry_time(self, retry_time: float):
        """Update average retry time"""
        current_avg = self.retry_stats['average_retry_time']
        total_retries = self.retry_stats['successful_retries']
        
        if total_retries == 1:
            self.retry_stats['average_retry_time'] = retry_time
        else:
            self.retry_stats['average_retry_time'] = (
                (current_avg * (total_retries - 1) + retry_time) / total_retries
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return self.retry_stats.copy()

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Protects against cascading failures
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.RLock()
        
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'circuit_opens': 0,
            'circuit_closes': 0
        }
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException if circuit is open
            Original exception if function fails
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenException("Circuit breaker is OPEN")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Handle success
                self._on_success()
                return result
                
            except self.config.expected_exception as e:
                # Handle failure
                self._on_failure()
                raise e
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException if circuit is open
            Original exception if function fails
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenException("Circuit breaker is OPEN")
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Handle success
                self._on_success()
                return result
                
            except self.config.expected_exception as e:
                # Handle failure
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.stats['successful_requests'] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.stats['circuit_closes'] += 1
                logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed execution"""
        self.stats['failed_requests'] += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.stats['circuit_opens'] += 1
            logger.warning("Circuit breaker transitioning to OPEN (from HALF_OPEN)")
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.stats['circuit_opens'] += 1
            logger.warning("Circuit breaker transitioning to OPEN")
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            **self.stats,
            'current_state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info("Circuit breaker manually reset")

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class ErrorRecovery:
    """
    Graceful degradation and recovery strategies
    """
    
    def __init__(self):
        self.recovery_strategies = {}
        self.fallback_handlers = {}
        self.recovery_stats = {
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'fallback_activations': 0
        }
    
    def register_recovery_strategy(
        self, 
        error_type: Type[Exception], 
        strategy: Callable,
        priority: int = 1
    ):
        """Register a recovery strategy for a specific error type"""
        if error_type not in self.recovery_strategies:
            self.recovery_strategies[error_type] = []
        
        self.recovery_strategies[error_type].append({
            'strategy': strategy,
            'priority': priority
        })
        
        # Sort by priority (higher priority first)
        self.recovery_strategies[error_type].sort(key=lambda x: x['priority'], reverse=True)
    
    def register_fallback_handler(
        self, 
        component: str, 
        handler: Callable
    ):
        """Register a fallback handler for a component"""
        self.fallback_handlers[component] = handler
    
    def recover(self, error: Exception, context: ErrorContext) -> Any:
        """
        Attempt to recover from an error
        
        Args:
            error: The exception that occurred
            context: Error context information
            
        Returns:
            Recovery result or None if no recovery possible
        """
        self.recovery_stats['total_recoveries'] += 1
        
        # Try recovery strategies
        error_type = type(error)
        if error_type in self.recovery_strategies:
            for strategy_info in self.recovery_strategies[error_type]:
                try:
                    result = strategy_info['strategy'](error, context)
                    self.recovery_stats['successful_recoveries'] += 1
                    logger.info(f"Recovery successful using strategy {strategy_info['strategy'].__name__}")
                    return result
                except Exception as recovery_error:
                    logger.warning(f"Recovery strategy failed: {recovery_error}")
                    continue
        
        # Try fallback handler
        if context.component in self.fallback_handlers:
            try:
                result = self.fallback_handlers[context.component](error, context)
                self.recovery_stats['fallback_activations'] += 1
                logger.info(f"Fallback handler activated for {context.component}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback handler failed: {fallback_error}")
        
        logger.error(f"No recovery strategy available for {error_type.__name__}")
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        return self.recovery_stats.copy()

class StructuredLogger:
    """
    Production-grade structured logging with distributed tracing
    """
    
    def __init__(self, service_name: str = "rl-training"):
        self.service_name = service_name
        self.correlation_id = None
        self.logger = logging.getLogger(service_name)
        
        # Configure structured logging
        self._setup_structured_logging()
    
    def _setup_structured_logging(self):
        """Setup structured logging configuration"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id
    
    def _create_log_entry(
        self, 
        level: str, 
        message: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': level,
            'message': message,
            'correlation_id': self.correlation_id,
            **kwargs
        }
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        log_entry = self._create_log_entry('INFO', message, **kwargs)
        self.logger.info(json.dumps(log_entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        log_entry = self._create_log_entry('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(log_entry))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        log_entry = self._create_log_entry('ERROR', message, **kwargs)
        self.logger.error(json.dumps(log_entry))
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        log_entry = self._create_log_entry('CRITICAL', message, **kwargs)
        self.logger.critical(json.dumps(log_entry))
    
    def log_error_context(self, error: Exception, context: ErrorContext):
        """Log detailed error context"""
        self.error(
            f"Error in {context.component}.{context.operation}",
            error_type=context.error_type,
            error_message=context.error_message,
            severity=context.severity.value,
            retry_count=context.retry_count,
            circuit_state=context.circuit_state.value if context.circuit_state else None,
            stack_trace=context.stack_trace,
            context_data=context.context_data
        )

class ErrorHandler:
    """
    Main error handling orchestrator
    Combines retry logic, circuit breakers, and recovery strategies
    """
    
    def __init__(
        self, 
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        self.retry_strategy = RetryStrategy(retry_config or RetryConfig())
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        self.error_recovery = ErrorRecovery()
        self.structured_logger = StructuredLogger()
        
        # Error tracking
        self.error_contexts = {}
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_component': {},
            'errors_by_severity': {}
        }
    
    def handle_error(
        self, 
        error: Exception, 
        component: str, 
        operation: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        Handle an error with full context tracking
        
        Args:
            error: The exception that occurred
            component: Component where error occurred
            operation: Operation that failed
            context_data: Additional context data
            
        Returns:
            Error context with handling information
        """
        # Create error context
        error_context = ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=self._determine_severity(error),
            component=component,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context_data=context_data or {},
            circuit_state=self.circuit_breaker.get_state()
        )
        
        # Store error context
        self.error_contexts[error_context.error_id] = error_context
        
        # Update statistics
        self._update_error_stats(error_context)
        
        # Log error context
        self.structured_logger.log_error_context(error, error_context)
        
        # Attempt recovery
        recovery_result = self.error_recovery.recover(error, error_context)
        if recovery_result is not None:
            error_context.context_data['recovery_result'] = recovery_result
        
        return error_context
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type"""
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _update_error_stats(self, context: ErrorContext):
        """Update error statistics"""
        self.error_stats['total_errors'] += 1
        
        # Update by type
        error_type = context.error_type
        self.error_stats['errors_by_type'][error_type] = \
            self.error_stats['errors_by_type'].get(error_type, 0) + 1
        
        # Update by component
        component = context.component
        self.error_stats['errors_by_component'][component] = \
            self.error_stats['errors_by_component'].get(component, 0) + 1
        
        # Update by severity
        severity = context.severity.value
        self.error_stats['errors_by_severity'][severity] = \
            self.error_stats['errors_by_severity'].get(severity, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        return {
            **self.error_stats,
            'retry_stats': self.retry_strategy.get_stats(),
            'circuit_breaker_stats': self.circuit_breaker.get_stats(),
            'recovery_stats': self.error_recovery.get_stats()
        }
    
    def get_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """Get error context by ID"""
        return self.error_contexts.get(error_id)

# Decorators for easy error handling integration

def with_error_handling(
    component: str,
    operation: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator for automatic error handling
    
    Args:
        component: Component name
        operation: Operation name
        retry_config: Retry configuration
        circuit_breaker_config: Circuit breaker configuration
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(retry_config, circuit_breaker_config)
            
            try:
                # Try with retry logic
                return error_handler.retry_strategy.retry(func, *args, **kwargs)
            except Exception as e:
                # Handle error with full context
                context = error_handler.handle_error(e, component, operation)
                raise e
        
        return wrapper
    return decorator

def with_async_error_handling(
    component: str,
    operation: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator for automatic async error handling
    
    Args:
        component: Component name
        operation: Operation name
        retry_config: Retry configuration
        circuit_breaker_config: Circuit breaker configuration
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(retry_config, circuit_breaker_config)
            
            try:
                # Try with retry logic
                return await error_handler.retry_strategy.async_retry(func, *args, **kwargs)
            except Exception as e:
                # Handle error with full context
                context = error_handler.handle_error(e, component, operation)
                raise e
        
        return wrapper
    return decorator

@contextmanager
def error_context(component: str, operation: str):
    """
    Context manager for error handling
    
    Args:
        component: Component name
        operation: Operation name
    """
    error_handler = ErrorHandler()
    try:
        yield error_handler
    except Exception as e:
        context = error_handler.handle_error(e, component, operation)
        raise e
