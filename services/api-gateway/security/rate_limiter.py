"""
Rate Limiting Service
Implements sliding window rate limiting with Redis backend
"""

import time
import json
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger(__name__)

class RateLimiter:
    """Rate limiter with sliding window algorithm"""
    
    def __init__(self):
        # In-memory storage for rate limiting (in production, use Redis)
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}
        self.suspicious_ips = {}
    
    def is_rate_limited(self, identifier: str, limit: int, window_seconds: int, 
                       request_type: str = "general") -> Tuple[bool, Dict]:
        """
        Check if request should be rate limited
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            request_type: Type of request for different limits
        
        Returns:
            (is_limited, rate_info)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        requests_queue = self.requests[identifier]
        while requests_queue and requests_queue[0] < window_start:
            requests_queue.popleft()
        
        # Check if blocked
        if identifier in self.blocked_ips:
            block_info = self.blocked_ips[identifier]
            if now < block_info["expires_at"]:
                logger.warning("Rate limit exceeded - IP blocked", 
                             identifier=identifier, 
                             block_duration=block_info["duration"])
                return True, {
                    "blocked": True,
                    "reason": "IP temporarily blocked due to excessive requests",
                    "retry_after": int(block_info["expires_at"] - now),
                    "block_duration": block_info["duration"]
                }
            else:
                # Unblock expired IPs
                del self.blocked_ips[identifier]
        
        # Check current rate
        current_requests = len(requests_queue)
        
        if current_requests >= limit:
            # Apply different penalties based on request type
            if request_type == "sensitive":
                # Block for longer for sensitive operations
                block_duration = min(3600, window_seconds * 10)  # Up to 1 hour
            elif request_type == "auth":
                # Block for medium duration for auth attempts
                block_duration = min(1800, window_seconds * 5)  # Up to 30 minutes
            else:
                # Standard block duration
                block_duration = min(900, window_seconds * 2)  # Up to 15 minutes
            
            # Block the identifier
            self.blocked_ips[identifier] = {
                "expires_at": now + block_duration,
                "duration": block_duration,
                "blocked_at": now,
                "request_type": request_type
            }
            
            # Mark as suspicious if multiple blocks
            if identifier in self.suspicious_ips:
                self.suspicious_ips[identifier]["block_count"] += 1
                self.suspicious_ips[identifier]["last_block"] = now
            else:
                self.suspicious_ips[identifier] = {
                    "block_count": 1,
                    "first_block": now,
                    "last_block": now
                }
            
            logger.warning("Rate limit exceeded", 
                         identifier=identifier, 
                         current_requests=current_requests,
                         limit=limit,
                         window_seconds=window_seconds,
                         request_type=request_type,
                         block_duration=block_duration)
            
            return True, {
                "blocked": True,
                "reason": f"Rate limit exceeded: {current_requests}/{limit} requests in {window_seconds}s",
                "retry_after": block_duration,
                "current_requests": current_requests,
                "limit": limit,
                "window_seconds": window_seconds
            }
        
        # Add current request
        requests_queue.append(now)
        
        # Calculate rate info
        rate_info = {
            "blocked": False,
            "current_requests": current_requests + 1,
            "limit": limit,
            "window_seconds": window_seconds,
            "remaining": limit - (current_requests + 1),
            "reset_time": int(now + window_seconds)
        }
        
        return False, rate_info
    
    def get_rate_limit_headers(self, rate_info: Dict) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset_time"])
        }
        
        if rate_info.get("blocked"):
            headers["X-RateLimit-Blocked"] = "true"
            headers["Retry-After"] = str(rate_info["retry_after"])
        
        return headers
    
    def get_suspicious_ips(self) -> Dict:
        """Get list of suspicious IPs for monitoring"""
        now = time.time()
        suspicious = {}
        
        for ip, info in self.suspicious_ips.items():
            if now - info["last_block"] < 86400:  # Keep for 24 hours
                suspicious[ip] = {
                    "block_count": info["block_count"],
                    "first_block": info["first_block"],
                    "last_block": info["last_block"],
                    "currently_blocked": ip in self.blocked_ips
                }
        
        return suspicious
    
    def unblock_ip(self, identifier: str) -> bool:
        """Manually unblock an IP"""
        if identifier in self.blocked_ips:
            del self.blocked_ips[identifier]
            logger.info("IP manually unblocked", identifier=identifier)
            return True
        return False

# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "auth": {
        "login": {"limit": 5, "window": 300},  # 5 attempts per 5 minutes
        "mfa": {"limit": 10, "window": 300},   # 10 MFA attempts per 5 minutes
        "refresh": {"limit": 20, "window": 3600}  # 20 refreshes per hour
    },
    "sensitive": {
        "delete_space": {"limit": 20, "window": 3600},  # 20 deletions per hour (increased for development)
        "bulk_delete": {"limit": 5, "window": 3600},    # 5 bulk deletes per hour (increased)
        "security_config": {"limit": 10, "window": 3600}  # 10 security config changes per hour (increased)
    },
    "general": {
        "api": {"limit": 100, "window": 3600},  # 100 requests per hour
        "upload": {"limit": 20, "window": 3600},  # 20 uploads per hour
        "search": {"limit": 200, "window": 3600}  # 200 searches per hour
    }
}

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_rate_limit_config(endpoint_type: str, endpoint: str) -> Dict:
    """Get rate limit configuration for an endpoint"""
    return RATE_LIMITS.get(endpoint_type, {}).get(endpoint, RATE_LIMITS["general"]["api"])

def check_rate_limit(request: Request, endpoint_type: str, endpoint: str, 
                    identifier: Optional[str] = None) -> Tuple[bool, Dict]:
    """Check rate limit for a request"""
    # Get identifier (IP address or user ID)
    if not identifier:
        identifier = request.client.host
    
    # Get rate limit config
    config = get_rate_limit_config(endpoint_type, endpoint)
    
    # Check rate limit
    is_limited, rate_info = rate_limiter.is_rate_limited(
        identifier=identifier,
        limit=config["limit"],
        window_seconds=config["window"],
        request_type=endpoint_type
    )
    
    return is_limited, rate_info
