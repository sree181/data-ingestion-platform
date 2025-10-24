"""
Access Control Service

This service handles IP whitelist, domain restrictions, and geographic access control
for project spaces.
"""

import json
import uuid
import ipaddress
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.access_control import (
    AccessControlPolicy, IPRange, DomainRestriction, GeographicRestriction,
    TimeRestriction, AccessControlRule, AccessLogEntry, AccessControlTestResult,
    AccessControlType, IPRangeType, DomainType, GeographicRegion, TimeRestrictionType
)
from models.project_spaces import SpacePermission

logger = structlog.get_logger(__name__)


class AccessControlService:
    """Service for managing access control policies"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_access_control_policy(
        self,
        space_id: str,
        policy_name: str,
        description: Optional[str] = None,
        ip_whitelist: Optional[List[IPRange]] = None,
        ip_blacklist: Optional[List[IPRange]] = None,
        allowed_domains: Optional[List[DomainRestriction]] = None,
        blocked_domains: Optional[List[DomainRestriction]] = None,
        geographic_restrictions: Optional[List[GeographicRestriction]] = None,
        time_restrictions: Optional[List[TimeRestriction]] = None,
        default_action: str = "allow",
        enable_logging: bool = True,
        enable_notifications: bool = True,
        created_by: str = "system"
    ) -> AccessControlPolicy:
        """Create a new access control policy for a project space"""
        
        logger.info("Creating access control policy", space_id=space_id, policy_name=policy_name)
        
        try:
            # Create the policy
            policy = AccessControlPolicy(
                space_id=space_id,
                policy_name=policy_name,
                description=description,
                ip_whitelist=ip_whitelist or [],
                ip_blacklist=ip_blacklist or [],
                allowed_domains=allowed_domains or [],
                blocked_domains=blocked_domains or [],
                geographic_restrictions=geographic_restrictions or [],
                time_restrictions=time_restrictions or [],
                default_action=default_action,
                enable_logging=enable_logging,
                enable_notifications=enable_notifications,
                created_by=created_by,
                last_modified_by=created_by
            )
            
            # Store in database
            await self._store_access_control_policy(policy)
            
            logger.info("Access control policy created successfully", space_id=space_id, policy_id=policy.space_id)
            return policy
            
        except Exception as e:
            logger.error("Failed to create access control policy", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def get_access_control_policy(self, space_id: str) -> Optional[AccessControlPolicy]:
        """Get access control policy for a project space"""
        
        logger.info("Getting access control policy", space_id=space_id)
        
        try:
            query = text("""
                SELECT access_control_policy 
                FROM project_spaces 
                WHERE id = :space_id
            """)
            
            result = await self.db_session.execute(query, {"space_id": space_id})
            row = result.fetchone()
            
            if not row or not row[0]:
                return None
            
            policy_data = json.loads(row[0])
            return AccessControlPolicy(**policy_data)
            
        except Exception as e:
            logger.error("Failed to get access control policy", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def update_access_control_policy(
        self,
        space_id: str,
        policy_name: Optional[str] = None,
        description: Optional[str] = None,
        ip_whitelist: Optional[List[IPRange]] = None,
        ip_blacklist: Optional[List[IPRange]] = None,
        allowed_domains: Optional[List[DomainRestriction]] = None,
        blocked_domains: Optional[List[DomainRestriction]] = None,
        geographic_restrictions: Optional[List[GeographicRestriction]] = None,
        time_restrictions: Optional[List[TimeRestriction]] = None,
        default_action: Optional[str] = None,
        enable_logging: Optional[bool] = None,
        enable_notifications: Optional[bool] = None,
        modified_by: str = "system"
    ) -> AccessControlPolicy:
        """Update access control policy for a project space"""
        
        logger.info("Updating access control policy", space_id=space_id)
        
        try:
            # Get existing policy
            existing_policy = await self.get_access_control_policy(space_id)
            if not existing_policy:
                raise ValueError("Access control policy not found")
            
            # Update fields if provided
            if policy_name is not None:
                existing_policy.policy_name = policy_name
            if description is not None:
                existing_policy.description = description
            if ip_whitelist is not None:
                existing_policy.ip_whitelist = ip_whitelist
            if ip_blacklist is not None:
                existing_policy.ip_blacklist = ip_blacklist
            if allowed_domains is not None:
                existing_policy.allowed_domains = allowed_domains
            if blocked_domains is not None:
                existing_policy.blocked_domains = blocked_domains
            if geographic_restrictions is not None:
                existing_policy.geographic_restrictions = geographic_restrictions
            if time_restrictions is not None:
                existing_policy.time_restrictions = time_restrictions
            if default_action is not None:
                existing_policy.default_action = default_action
            if enable_logging is not None:
                existing_policy.enable_logging = enable_logging
            if enable_notifications is not None:
                existing_policy.enable_notifications = enable_notifications
            
            existing_policy.last_modified_by = modified_by
            existing_policy.updated_at = datetime.utcnow()
            
            # Store updated policy
            await self._store_access_control_policy(existing_policy)
            
            logger.info("Access control policy updated successfully", space_id=space_id)
            return existing_policy
            
        except Exception as e:
            logger.error("Failed to update access control policy", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def test_access_control(
        self,
        space_id: str,
        ip_address: str,
        email_domain: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> AccessControlTestResult:
        """Test access control rules for a given IP address and domain"""
        
        logger.info("Testing access control", space_id=space_id, ip_address=ip_address, email_domain=email_domain)
        
        try:
            # Get access control policy
            policy = await self.get_access_control_policy(space_id)
            if not policy:
                return AccessControlTestResult(
                    space_id=space_id,
                    test_ip=ip_address,
                    test_email_domain=email_domain,
                    action=policy.default_action if policy else "allow",
                    reason="No access control policy found",
                    metadata={"policy_exists": False}
                )
            
            # Test IP restrictions
            ip_action, ip_rules = await self._test_ip_restrictions(ip_address, policy)
            
            # Test domain restrictions
            domain_action, domain_rules = await self._test_domain_restrictions(email_domain, policy)
            
            # Test geographic restrictions
            geo_action, geo_rules = await self._test_geographic_restrictions(ip_address, policy)
            
            # Test time restrictions
            time_action, time_rules = await self._test_time_restrictions(timestamp or datetime.utcnow(), policy)
            
            # Determine final action based on priority
            all_rules = ip_rules + domain_rules + geo_rules + time_rules
            final_action = self._determine_final_action(ip_action, domain_action, geo_action, time_action, policy)
            
            # Generate reason
            reason = self._generate_reason(final_action, all_rules, policy)
            
            result = AccessControlTestResult(
                space_id=space_id,
                test_ip=ip_address,
                test_email_domain=email_domain,
                action=final_action,
                matched_rules=all_rules,
                reason=reason,
                metadata={
                    "ip_action": ip_action,
                    "domain_action": domain_action,
                    "geo_action": geo_action,
                    "time_action": time_action,
                    "policy_name": policy.policy_name
                }
            )
            
            logger.info("Access control test completed", space_id=space_id, action=final_action)
            return result
            
        except Exception as e:
            logger.error("Failed to test access control", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def log_access_attempt(
        self,
        space_id: str,
        ip_address: str,
        action: str,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        rule_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an access attempt"""
        
        try:
            log_entry = AccessLogEntry(
                id=str(uuid.uuid4()),
                space_id=space_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                rule_id=rule_id,
                reason=reason,
                metadata=metadata or {}
            )
            
            await self._store_access_log(log_entry)
            
        except Exception as e:
            logger.error("Failed to log access attempt", space_id=space_id, error=str(e), exc_info=True)
    
    async def get_access_logs(
        self,
        space_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None
    ) -> List[AccessLogEntry]:
        """Get access logs for a project space"""
        
        logger.info("Getting access logs", space_id=space_id, limit=limit)
        
        try:
            query = text("""
                SELECT log_data 
                FROM access_logs 
                WHERE space_id = :space_id
                AND (:start_date IS NULL OR timestamp >= :start_date)
                AND (:end_date IS NULL OR timestamp <= :end_date)
                AND (:action IS NULL OR action = :action)
                ORDER BY timestamp DESC 
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.db_session.execute(query, {
                "space_id": space_id,
                "start_date": start_date,
                "end_date": end_date,
                "action": action,
                "limit": limit,
                "offset": offset
            })
            rows = result.fetchall()
            
            logs = []
            for row in rows:
                log_data = json.loads(row[0])
                logs.append(AccessLogEntry(**log_data))
            
            logger.info("Retrieved access logs", space_id=space_id, count=len(logs))
            return logs
            
        except Exception as e:
            logger.error("Failed to get access logs", space_id=space_id, error=str(e), exc_info=True)
            raise
    
    async def _store_access_control_policy(self, policy: AccessControlPolicy) -> None:
        """Store access control policy in database"""
        
        policy_json = json.dumps(policy.dict(), default=str)
        
        query = text("""
            UPDATE project_spaces 
            SET access_control_policy = :policy_json,
                updated_at = :updated_at
            WHERE id = :space_id
        """)
        
        await self.db_session.execute(query, {
            "space_id": policy.space_id,
            "policy_json": policy_json,
            "updated_at": policy.updated_at
        })
        await self.db_session.commit()
    
    async def _store_access_log(self, log_entry: AccessLogEntry) -> None:
        """Store access log entry in database"""
        
        log_json = json.dumps(log_entry.dict(), default=str)
        
        query = text("""
            INSERT INTO access_logs (log_id, space_id, log_data, timestamp)
            VALUES (:log_id, :space_id, :log_data, :timestamp)
        """)
        
        await self.db_session.execute(query, {
            "log_id": log_entry.id,
            "space_id": log_entry.space_id,
            "log_data": log_json,
            "timestamp": log_entry.timestamp
        })
        await self.db_session.commit()
    
    async def _test_ip_restrictions(self, ip_address: str, policy: AccessControlPolicy) -> Tuple[str, List[AccessControlRule]]:
        """Test IP address against IP restrictions"""
        
        try:
            test_ip = ipaddress.ip_address(ip_address)
        except ValueError:
            return "deny", []
        
        matched_rules = []
        
        # Check blacklist first (higher priority)
        for ip_range in policy.ip_blacklist:
            if not ip_range.is_active:
                continue
            
            if self._ip_matches_range(test_ip, ip_range):
                rule = AccessControlRule(
                    id=ip_range.id,
                    name=ip_range.name,
                    rule_type=AccessControlType.IP_BLACKLIST,
                    action="deny",
                    conditions={"ip_range": ip_range.ip_address}
                )
                matched_rules.append(rule)
                return "deny", matched_rules
        
        # Check whitelist
        for ip_range in policy.ip_whitelist:
            if not ip_range.is_active:
                continue
            
            if self._ip_matches_range(test_ip, ip_range):
                rule = AccessControlRule(
                    id=ip_range.id,
                    name=ip_range.name,
                    rule_type=AccessControlType.IP_WHITELIST,
                    action="allow",
                    conditions={"ip_range": ip_range.ip_address}
                )
                matched_rules.append(rule)
                return "allow", matched_rules
        
        return "neutral", matched_rules
    
    async def _test_domain_restrictions(self, email_domain: Optional[str], policy: AccessControlPolicy) -> Tuple[str, List[AccessControlRule]]:
        """Test email domain against domain restrictions"""
        
        if not email_domain:
            return "neutral", []
        
        matched_rules = []
        
        # Check blocked domains first
        for domain_restriction in policy.blocked_domains:
            if not domain_restriction.is_active:
                continue
            
            if self._domain_matches_restriction(email_domain, domain_restriction):
                rule = AccessControlRule(
                    id=domain_restriction.id,
                    name=domain_restriction.name,
                    rule_type=AccessControlType.DOMAIN_RESTRICTION,
                    action="deny",
                    conditions={"domain": domain_restriction.domain}
                )
                matched_rules.append(rule)
                return "deny", matched_rules
        
        # Check allowed domains
        for domain_restriction in policy.allowed_domains:
            if not domain_restriction.is_active:
                continue
            
            if self._domain_matches_restriction(email_domain, domain_restriction):
                rule = AccessControlRule(
                    id=domain_restriction.id,
                    name=domain_restriction.name,
                    rule_type=AccessControlType.DOMAIN_RESTRICTION,
                    action="allow",
                    conditions={"domain": domain_restriction.domain}
                )
                matched_rules.append(rule)
                return "allow", matched_rules
        
        return "neutral", matched_rules
    
    async def _test_geographic_restrictions(self, ip_address: str, policy: AccessControlPolicy) -> Tuple[str, List[AccessControlRule]]:
        """Test IP address against geographic restrictions"""
        
        # This is a simplified implementation
        # In production, you would use a GeoIP service like MaxMind
        matched_rules = []
        
        for geo_restriction in policy.geographic_restrictions:
            if not geo_restriction.is_active:
                continue
            
            # Simplified geographic check (in production, use GeoIP service)
            if self._ip_matches_geographic_region(ip_address, geo_restriction):
                action = "allow" if geo_restriction.is_allowlist else "deny"
                rule = AccessControlRule(
                    id=geo_restriction.id,
                    name=geo_restriction.name,
                    rule_type=AccessControlType.GEOGRAPHIC_RESTRICTION,
                    action=action,
                    conditions={"regions": [r.value for r in geo_restriction.regions]}
                )
                matched_rules.append(rule)
                return action, matched_rules
        
        return "neutral", matched_rules
    
    async def _test_time_restrictions(self, timestamp: datetime, policy: AccessControlPolicy) -> Tuple[str, List[AccessControlRule]]:
        """Test timestamp against time restrictions"""
        
        matched_rules = []
        
        for time_restriction in policy.time_restrictions:
            if not time_restriction.is_active:
                continue
            
            if self._timestamp_matches_restriction(timestamp, time_restriction):
                rule = AccessControlRule(
                    id=time_restriction.id,
                    name=time_restriction.name,
                    rule_type=AccessControlType.TIME_BASED_RESTRICTION,
                    action="deny",
                    conditions={"restriction_type": time_restriction.restriction_type.value}
                )
                matched_rules.append(rule)
                return "deny", matched_rules
        
        return "neutral", matched_rules
    
    def _ip_matches_range(self, ip_address: ipaddress.IPv4Address | ipaddress.IPv6Address, ip_range: IPRange) -> bool:
        """Check if IP address matches IP range"""
        
        try:
            if ip_range.range_type == IPRangeType.SINGLE_IP:
                return str(ip_address) == ip_range.ip_address
            elif ip_range.range_type == IPRangeType.CIDR_BLOCK:
                network = ipaddress.ip_network(ip_range.ip_address, strict=False)
                return ip_address in network
            elif ip_range.range_type == IPRangeType.IP_RANGE:
                start_ip, end_ip = ip_range.ip_address.split('-', 1)
                start_ip = ipaddress.ip_address(start_ip.strip())
                end_ip = ipaddress.ip_address(end_ip.strip())
                return start_ip <= ip_address <= end_ip
            elif ip_range.range_type == IPRangeType.WILDCARD:
                # Convert wildcard pattern to regex
                pattern = ip_range.ip_address.replace('*', '.*').replace('?', '.')
                return bool(re.match(pattern, str(ip_address)))
        except Exception:
            return False
        
        return False
    
    def _domain_matches_restriction(self, domain: str, restriction: DomainRestriction) -> bool:
        """Check if domain matches domain restriction"""
        
        try:
            if restriction.domain_type == DomainType.WILDCARD_DOMAIN:
                pattern = restriction.domain.replace('*', '.*')
                return bool(re.match(pattern, domain.lower()))
            else:
                return domain.lower() == restriction.domain.lower()
        except Exception:
            return False
    
    def _ip_matches_geographic_region(self, ip_address: str, restriction: GeographicRestriction) -> bool:
        """Check if IP address matches geographic region"""
        
        # This is a simplified implementation
        # In production, use a GeoIP service like MaxMind
        # For now, return False to indicate no geographic restrictions
        return False
    
    def _timestamp_matches_restriction(self, timestamp: datetime, restriction: TimeRestriction) -> bool:
        """Check if timestamp matches time restriction"""
        
        try:
            if restriction.restriction_type == TimeRestrictionType.BUSINESS_HOURS:
                # 9 AM to 5 PM, Monday to Friday
                return (timestamp.weekday() < 5 and 
                        timestamp.hour >= 9 and 
                        timestamp.hour < 17)
            elif restriction.restriction_type == TimeRestrictionType.CUSTOM_HOURS:
                if not restriction.start_time or not restriction.end_time:
                    return False
                
                start_hour, start_min = map(int, restriction.start_time.split(':'))
                end_hour, end_min = map(int, restriction.end_time.split(':'))
                
                current_time = timestamp.hour * 60 + timestamp.minute
                start_time = start_hour * 60 + start_min
                end_time = end_hour * 60 + end_min
                
                return start_time <= current_time <= end_time
            elif restriction.restriction_type == TimeRestrictionType.WEEKDAYS_ONLY:
                return timestamp.weekday() < 5
            elif restriction.restriction_type == TimeRestrictionType.WEEKENDS_ONLY:
                return timestamp.weekday() >= 5
            elif restriction.restriction_type == TimeRestrictionType.MAINTENANCE_WINDOW:
                # Check if current time is within maintenance window
                if not restriction.start_time or not restriction.end_time:
                    return False
                
                start_hour, start_min = map(int, restriction.start_time.split(':'))
                end_hour, end_min = map(int, restriction.end_time.split(':'))
                
                current_time = timestamp.hour * 60 + timestamp.minute
                start_time = start_hour * 60 + start_min
                end_time = end_hour * 60 + end_min
                
                return start_time <= current_time <= end_time
        except Exception:
            return False
        
        return False
    
    def _determine_final_action(self, ip_action: str, domain_action: str, geo_action: str, time_action: str, policy: AccessControlPolicy) -> str:
        """Determine final action based on all test results"""
        
        # Priority order: deny > allow > neutral
        actions = [ip_action, domain_action, geo_action, time_action]
        
        if "deny" in actions:
            return "deny"
        elif "allow" in actions:
            return "allow"
        else:
            return policy.default_action
    
    def _generate_reason(self, action: str, rules: List[AccessControlRule], policy: AccessControlPolicy) -> str:
        """Generate human-readable reason for the action"""
        
        if not rules:
            return f"No matching rules found, using default action: {policy.default_action}"
        
        rule_names = [rule.name for rule in rules]
        return f"Action '{action}' based on rules: {', '.join(rule_names)}"
