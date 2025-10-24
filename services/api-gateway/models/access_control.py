"""
Access Control Models

This module defines Pydantic models for IP whitelist and domain restrictions,
including geographic access control and email domain validation.
"""

from pydantic import BaseModel, Field, validator, IPvAnyAddress
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import ipaddress
import re


class AccessControlType(str, Enum):
    """Types of access control"""
    IP_WHITELIST = "ip_whitelist"
    IP_BLACKLIST = "ip_blacklist"
    DOMAIN_RESTRICTION = "domain_restriction"
    GEOGRAPHIC_RESTRICTION = "geographic_restriction"
    TIME_BASED_RESTRICTION = "time_based_restriction"


class IPRangeType(str, Enum):
    """Types of IP ranges"""
    SINGLE_IP = "single_ip"
    CIDR_BLOCK = "cidr_block"
    IP_RANGE = "ip_range"
    WILDCARD = "wildcard"


class DomainType(str, Enum):
    """Types of domain restrictions"""
    EMAIL_DOMAIN = "email_domain"
    ALLOWED_DOMAINS = "allowed_domains"
    BLOCKED_DOMAINS = "blocked_domains"
    WILDCARD_DOMAIN = "wildcard_domain"


class GeographicRegion(str, Enum):
    """Geographic regions for access control"""
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    EUROPE = "europe"
    ASIA = "asia"
    AFRICA = "africa"
    OCEANIA = "oceania"
    MIDDLE_EAST = "middle_east"
    CUSTOM = "custom"


class TimeRestrictionType(str, Enum):
    """Types of time-based restrictions"""
    BUSINESS_HOURS = "business_hours"
    CUSTOM_HOURS = "custom_hours"
    WEEKDAYS_ONLY = "weekdays_only"
    WEEKENDS_ONLY = "weekends_only"
    MAINTENANCE_WINDOW = "maintenance_window"


class IPRange(BaseModel):
    """IP range definition"""
    id: str = Field(..., description="Unique identifier for the IP range")
    name: str = Field(..., description="Human-readable name for the IP range")
    description: Optional[str] = Field(None, description="Description of the IP range")
    ip_address: str = Field(..., description="IP address or CIDR block")
    range_type: IPRangeType = Field(..., description="Type of IP range")
    is_active: bool = Field(default=True, description="Whether the range is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the range")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        try:
            # Try to parse as IP address or CIDR
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            # Try to parse as IP range (e.g., "192.168.1.1-192.168.1.100")
            if '-' in v:
                start_ip, end_ip = v.split('-', 1)
                try:
                    ipaddress.ip_address(start_ip.strip())
                    ipaddress.ip_address(end_ip.strip())
                    return v
                except ValueError:
                    raise ValueError(f"Invalid IP range format: {v}")
            else:
                raise ValueError(f"Invalid IP address format: {v}")
    
    @validator('range_type')
    def validate_range_type(cls, v, values):
        """Validate range type matches IP address format"""
        if 'ip_address' not in values:
            return v
        
        ip_addr = values['ip_address']
        
        if v == IPRangeType.SINGLE_IP:
            try:
                ipaddress.ip_address(ip_addr)
            except ValueError:
                raise ValueError("Single IP must be a valid IP address")
        elif v == IPRangeType.CIDR_BLOCK:
            try:
                ipaddress.ip_network(ip_addr, strict=False)
            except ValueError:
                raise ValueError("CIDR block must be a valid network address")
        elif v == IPRangeType.IP_RANGE:
            if '-' not in ip_addr:
                raise ValueError("IP range must contain a dash (e.g., 192.168.1.1-192.168.1.100)")
        elif v == IPRangeType.WILDCARD:
            if not any(char in ip_addr for char in ['*', '?']):
                raise ValueError("Wildcard must contain * or ? characters")
        
        return v


class DomainRestriction(BaseModel):
    """Domain restriction definition"""
    id: str = Field(..., description="Unique identifier for the domain restriction")
    name: str = Field(..., description="Human-readable name for the domain restriction")
    description: Optional[str] = Field(None, description="Description of the domain restriction")
    domain: str = Field(..., description="Domain pattern to match")
    domain_type: DomainType = Field(..., description="Type of domain restriction")
    is_active: bool = Field(default=True, description="Whether the restriction is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the restriction")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    
    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format"""
        if not v:
            raise ValueError("Domain cannot be empty")
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        wildcard_pattern = r'^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if '*' in v or '?' in v:
            if not re.match(wildcard_pattern, v):
                raise ValueError(f"Invalid wildcard domain format: {v}")
        else:
            if not re.match(domain_pattern, v):
                raise ValueError(f"Invalid domain format: {v}")
        
        return v.lower()


class GeographicRestriction(BaseModel):
    """Geographic restriction definition"""
    id: str = Field(..., description="Unique identifier for the geographic restriction")
    name: str = Field(..., description="Human-readable name for the geographic restriction")
    description: Optional[str] = Field(None, description="Description of the geographic restriction")
    regions: List[GeographicRegion] = Field(..., description="Allowed or blocked regions")
    countries: List[str] = Field(default=[], description="Specific countries (ISO 3166-1 alpha-2 codes)")
    is_allowlist: bool = Field(default=True, description="True for allowlist, False for blocklist")
    is_active: bool = Field(default=True, description="Whether the restriction is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the restriction")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    
    @validator('countries')
    def validate_countries(cls, v):
        """Validate country codes"""
        if not v:
            return v
        
        # Basic ISO 3166-1 alpha-2 validation
        country_pattern = r'^[A-Z]{2}$'
        for country in v:
            if not re.match(country_pattern, country):
                raise ValueError(f"Invalid country code: {country}. Must be ISO 3166-1 alpha-2 format (e.g., US, CA, GB)")
        
        return [country.upper() for country in v]


class TimeRestriction(BaseModel):
    """Time-based restriction definition"""
    id: str = Field(..., description="Unique identifier for the time restriction")
    name: str = Field(..., description="Human-readable name for the time restriction")
    description: Optional[str] = Field(None, description="Description of the time restriction")
    restriction_type: TimeRestrictionType = Field(..., description="Type of time restriction")
    timezone: str = Field(default="UTC", description="Timezone for the restriction")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM format)")
    days_of_week: List[int] = Field(default=[], description="Days of week (0=Monday, 6=Sunday)")
    is_active: bool = Field(default=True, description="Whether the restriction is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the restriction")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    
    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        """Validate time format"""
        if v is None:
            return v
        
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError(f"Invalid time format: {v}. Must be HH:MM format (e.g., 09:00, 17:30)")
        
        return v
    
    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        """Validate days of week"""
        if not v:
            return v
        
        for day in v:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError(f"Invalid day of week: {day}. Must be 0-6 (0=Monday, 6=Sunday)")
        
        return sorted(list(set(v)))


class AccessControlRule(BaseModel):
    """Access control rule definition"""
    id: str = Field(..., description="Unique identifier for the rule")
    name: str = Field(..., description="Human-readable name for the rule")
    description: Optional[str] = Field(None, description="Description of the rule")
    rule_type: AccessControlType = Field(..., description="Type of access control rule")
    priority: int = Field(default=100, description="Rule priority (lower = higher priority)")
    is_active: bool = Field(default=True, description="Whether the rule is active")
    action: str = Field(..., description="Action to take: allow, deny, challenge")
    conditions: Dict[str, Any] = Field(default={}, description="Rule conditions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the rule")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action"""
        allowed_actions = ['allow', 'deny', 'challenge', 'redirect']
        if v not in allowed_actions:
            raise ValueError(f"Invalid action: {v}. Must be one of: {allowed_actions}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority"""
        if v < 1 or v > 1000:
            raise ValueError("Priority must be between 1 and 1000")
        return v


class AccessControlPolicy(BaseModel):
    """Access control policy for a project space"""
    space_id: str = Field(..., description="Project space ID")
    policy_name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    is_active: bool = Field(default=True, description="Whether the policy is active")
    
    # IP restrictions
    ip_whitelist: List[IPRange] = Field(default=[], description="Allowed IP ranges")
    ip_blacklist: List[IPRange] = Field(default=[], description="Blocked IP ranges")
    
    # Domain restrictions
    allowed_domains: List[DomainRestriction] = Field(default=[], description="Allowed email domains")
    blocked_domains: List[DomainRestriction] = Field(default=[], description="Blocked email domains")
    
    # Geographic restrictions
    geographic_restrictions: List[GeographicRestriction] = Field(default=[], description="Geographic restrictions")
    
    # Time restrictions
    time_restrictions: List[TimeRestriction] = Field(default=[], description="Time-based restrictions")
    
    # General rules
    rules: List[AccessControlRule] = Field(default=[], description="General access control rules")
    
    # Settings
    default_action: str = Field(default="allow", description="Default action for unmatched requests")
    enable_logging: bool = Field(default=True, description="Enable access logging")
    enable_notifications: bool = Field(default=True, description="Enable violation notifications")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the policy")
    last_modified_by: str = Field(..., description="User who last modified the policy")


class AccessLogEntry(BaseModel):
    """Access log entry"""
    id: str = Field(..., description="Unique identifier for the log entry")
    space_id: str = Field(..., description="Project space ID")
    user_id: Optional[str] = Field(None, description="User ID")
    ip_address: str = Field(..., description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    action: str = Field(..., description="Action taken: allowed, denied, challenged")
    rule_id: Optional[str] = Field(None, description="Rule that triggered the action")
    reason: Optional[str] = Field(None, description="Reason for the action")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class AccessControlRequest(BaseModel):
    """Request to configure access control"""
    space_id: str = Field(..., description="Project space ID")
    policy_name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    
    # IP restrictions
    ip_whitelist: Optional[List[IPRange]] = Field(None, description="IP whitelist")
    ip_blacklist: Optional[List[IPRange]] = Field(None, description="IP blacklist")
    
    # Domain restrictions
    allowed_domains: Optional[List[DomainRestriction]] = Field(None, description="Allowed domains")
    blocked_domains: Optional[List[DomainRestriction]] = Field(None, description="Blocked domains")
    
    # Geographic restrictions
    geographic_restrictions: Optional[List[GeographicRestriction]] = Field(None, description="Geographic restrictions")
    
    # Time restrictions
    time_restrictions: Optional[List[TimeRestriction]] = Field(None, description="Time restrictions")
    
    # Settings
    default_action: str = Field(default="allow", description="Default action")
    enable_logging: bool = Field(default=True, description="Enable logging")
    enable_notifications: bool = Field(default=True, description="Enable notifications")


class AccessControlUpdateRequest(BaseModel):
    """Request to update access control policy"""
    policy_name: Optional[str] = Field(None, description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    
    # IP restrictions
    ip_whitelist: Optional[List[IPRange]] = Field(None, description="IP whitelist")
    ip_blacklist: Optional[List[IPRange]] = Field(None, description="IP blacklist")
    
    # Domain restrictions
    allowed_domains: Optional[List[DomainRestriction]] = Field(None, description="Allowed domains")
    blocked_domains: Optional[List[DomainRestriction]] = Field(None, description="Blocked domains")
    
    # Geographic restrictions
    geographic_restrictions: Optional[List[GeographicRestriction]] = Field(None, description="Geographic restrictions")
    
    # Time restrictions
    time_restrictions: Optional[List[TimeRestriction]] = Field(None, description="Time restrictions")
    
    # Settings
    default_action: Optional[str] = Field(None, description="Default action")
    enable_logging: Optional[bool] = Field(None, description="Enable logging")
    enable_notifications: Optional[bool] = Field(None, description="Enable notifications")


class AccessControlTestRequest(BaseModel):
    """Request to test access control rules"""
    space_id: str = Field(..., description="Project space ID")
    ip_address: str = Field(..., description="IP address to test")
    email_domain: Optional[str] = Field(None, description="Email domain to test")
    user_agent: Optional[str] = Field(None, description="User agent to test")
    timestamp: Optional[datetime] = Field(None, description="Timestamp to test (defaults to now)")


class AccessControlTestResult(BaseModel):
    """Result of access control test"""
    space_id: str = Field(..., description="Project space ID")
    test_ip: str = Field(..., description="Tested IP address")
    test_email_domain: Optional[str] = Field(None, description="Tested email domain")
    action: str = Field(..., description="Action that would be taken")
    matched_rules: List[AccessControlRule] = Field(default=[], description="Rules that matched")
    reason: str = Field(..., description="Reason for the action")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
