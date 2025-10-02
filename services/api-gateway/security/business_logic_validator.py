"""
Business Logic Validation Service
Enforces business rules and validation for security-sensitive operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class ValidationResult:
    """Result of business logic validation"""
    
    def __init__(self, valid: bool, reason: str = "", details: Dict = None):
        self.valid = valid
        self.reason = reason
        self.details = details or {}
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "details": self.details
        }

class BusinessLogicValidator:
    """Validates business logic for security-sensitive operations"""
    
    def __init__(self):
        self.business_hours = {
            "start": 9,  # 9 AM
            "end": 17,   # 5 PM
            "timezone": "UTC"
        }
        self.minimum_membership_duration = timedelta(hours=24)
        self.maximum_daily_deletions = 5
        self.cooling_period_after_failure = timedelta(minutes=30)
    
    async def validate_deletion_request(self, user_id: str, space_id: str, 
                                      auth_level: str, user_role: str,
                                      space_details: Dict, 
                                      admin_override: bool = False) -> ValidationResult:
        """Validate business logic for space deletion request
        
        Args:
            admin_override: If True, allows admins to bypass business hours and other restrictions
        """
        try:
            # Check 1: Business hours validation (can be bypassed by admin)
            if not admin_override:
                business_hours_result = self._validate_business_hours()
                if not business_hours_result.valid:
                    return business_hours_result
            else:
                logger.info("Admin override enabled - bypassing business hours restriction", 
                           user_id=user_id, user_role=user_role)
            
            # Check 2: Minimum membership duration
            membership_duration_result = await self._validate_membership_duration(
                user_id, space_id, space_details
            )
            if not membership_duration_result.valid:
                return membership_duration_result
            
            # Check 3: Daily deletion limit
            daily_limit_result = await self._validate_daily_deletion_limit(user_id)
            if not daily_limit_result.valid:
                return daily_limit_result
            
            # Check 4: Space dependency validation
            dependency_result = await self._validate_space_dependencies(space_id)
            if not dependency_result.valid:
                return dependency_result
            
            # Check 5: User role validation
            role_result = self._validate_user_role(user_role, auth_level)
            if not role_result.valid:
                return role_result
            
            # Check 6: Space security classification
            security_result = self._validate_security_classification(
                space_details, user_role, auth_level
            )
            if not security_result.valid:
                return security_result
            
            # Check 7: Recent failure validation
            failure_result = await self._validate_recent_failures(user_id)
            if not failure_result.valid:
                return failure_result
            
            logger.info("Business logic validation passed", 
                       user_id=user_id, space_id=space_id, auth_level=auth_level)
            
            return ValidationResult(True, "All business logic validations passed")
            
        except Exception as e:
            logger.error("Business logic validation failed", 
                        error=str(e), user_id=user_id, space_id=space_id)
            return ValidationResult(False, f"Validation error: {str(e)}")
    
    def _validate_business_hours(self) -> ValidationResult:
        """Validate if request is within business hours"""
        now = datetime.utcnow()
        current_hour = now.hour
        
        if self.business_hours["start"] <= current_hour < self.business_hours["end"]:
            return ValidationResult(True, "Request within business hours")
        
        return ValidationResult(
            False, 
            f"Request outside business hours (current: {current_hour}:00, allowed: {self.business_hours['start']}:00-{self.business_hours['end']}:00)",
            {"current_hour": current_hour, "business_hours": self.business_hours}
        )
    
    async def _validate_membership_duration(self, user_id: str, space_id: str, 
                                          space_details: Dict) -> ValidationResult:
        """Validate minimum membership duration"""
        try:
            # This would typically query the database for membership start date
            # For now, we'll simulate the check
            membership_start = space_details.get("membership_start", datetime.utcnow())
            
            if isinstance(membership_start, str):
                membership_start = datetime.fromisoformat(membership_start.replace('Z', '+00:00'))
            
            membership_duration = datetime.utcnow() - membership_start
            
            if membership_duration >= self.minimum_membership_duration:
                return ValidationResult(True, "Minimum membership duration satisfied")
            
            return ValidationResult(
                False,
                f"Minimum membership duration not met (required: {self.minimum_membership_duration}, actual: {membership_duration})",
                {
                    "required_duration": str(self.minimum_membership_duration),
                    "actual_duration": str(membership_duration),
                    "membership_start": membership_start.isoformat()
                }
            )
            
        except Exception as e:
            logger.error("Membership duration validation failed", error=str(e))
            return ValidationResult(False, f"Membership duration validation error: {str(e)}")
    
    async def _validate_daily_deletion_limit(self, user_id: str) -> ValidationResult:
        """Validate daily deletion limit per user"""
        try:
            # This would typically query the database for today's deletions
            # For now, we'll simulate the check
            today_deletions = 0  # Would be: await get_user_deletions_today(user_id)
            
            if today_deletions < self.maximum_daily_deletions:
                return ValidationResult(True, "Daily deletion limit not exceeded")
            
            return ValidationResult(
                False,
                f"Daily deletion limit exceeded (limit: {self.maximum_daily_deletions}, current: {today_deletions})",
                {
                    "limit": self.maximum_daily_deletions,
                    "current": today_deletions,
                    "reset_time": (datetime.utcnow() + timedelta(days=1)).isoformat()
                }
            )
            
        except Exception as e:
            logger.error("Daily deletion limit validation failed", error=str(e))
            return ValidationResult(False, f"Daily deletion limit validation error: {str(e)}")
    
    async def _validate_space_dependencies(self, space_id: str) -> ValidationResult:
        """Validate that space has no blocking dependencies"""
        try:
            # Check for active documents
            active_documents = 0  # Would be: await count_active_documents(space_id)
            
            # Check for active members
            active_members = 1  # Would be: await count_active_members(space_id)
            
            # Check for pending operations
            pending_operations = 0  # Would be: await count_pending_operations(space_id)
            
            if active_documents > 0:
                return ValidationResult(
                    False,
                    f"Space has {active_documents} active documents that must be removed first",
                    {"active_documents": active_documents}
                )
            
            if active_members > 1:  # More than just the owner
                return ValidationResult(
                    False,
                    f"Space has {active_members} members. All members must be removed first",
                    {"active_members": active_members}
                )
            
            if pending_operations > 0:
                return ValidationResult(
                    False,
                    f"Space has {pending_operations} pending operations that must complete first",
                    {"pending_operations": pending_operations}
                )
            
            return ValidationResult(True, "No blocking dependencies found")
            
        except Exception as e:
            logger.error("Space dependency validation failed", error=str(e))
            return ValidationResult(False, f"Space dependency validation error: {str(e)}")
    
    def _validate_user_role(self, user_role: str, auth_level: str) -> ValidationResult:
        """Validate user role against required authentication level"""
        role_hierarchy = {
            "owner": 4,
            "admin": 3,
            "member": 2,
            "viewer": 1
        }
        
        required_levels = {
            "owner": ["owner"],
            "admin": ["owner", "admin"],
            "member": ["owner", "admin", "member"],
            "viewer": ["owner", "admin", "member", "viewer"]
        }
        
        if auth_level not in required_levels:
            return ValidationResult(False, f"Invalid authentication level: {auth_level}")
        
        if user_role not in required_levels[auth_level]:
            return ValidationResult(
                False,
                f"User role '{user_role}' insufficient for '{auth_level}' level deletion",
                {
                    "user_role": user_role,
                    "required_roles": required_levels[auth_level],
                    "role_hierarchy": role_hierarchy
                }
            )
        
        return ValidationResult(True, "User role validation passed")
    
    def _validate_security_classification(self, space_details: Dict, user_role: str, 
                                        auth_level: str) -> ValidationResult:
        """Validate security classification requirements"""
        security_classification = space_details.get("security_classification", "internal")
        
        # Higher security classifications require higher roles
        classification_requirements = {
            "public": ["owner", "admin", "member", "viewer"],
            "internal": ["owner", "admin", "member", "viewer"],
            "confidential": ["owner", "admin"],
            "restricted": ["owner"],
            "top_secret": ["owner"]
        }
        
        required_roles = classification_requirements.get(security_classification, ["owner"])
        
        if user_role not in required_roles:
            return ValidationResult(
                False,
                f"Security classification '{security_classification}' requires roles: {required_roles}",
                {
                    "security_classification": security_classification,
                    "user_role": user_role,
                    "required_roles": required_roles
                }
            )
        
        return ValidationResult(True, "Security classification validation passed")
    
    async def _validate_recent_failures(self, user_id: str) -> ValidationResult:
        """Validate that user hasn't had recent failures"""
        try:
            # This would typically query the database for recent failures
            # For now, we'll simulate the check
            last_failure_time = None  # Would be: await get_last_failure_time(user_id)
            
            if last_failure_time:
                if isinstance(last_failure_time, str):
                    last_failure_time = datetime.fromisoformat(last_failure_time.replace('Z', '+00:00'))
                
                time_since_failure = datetime.utcnow() - last_failure_time
                
                if time_since_failure < self.cooling_period_after_failure:
                    return ValidationResult(
                        False,
                        f"Cooling period active after recent failure (remaining: {self.cooling_period_after_failure - time_since_failure})",
                        {
                            "last_failure": last_failure_time.isoformat(),
                            "cooling_period": str(self.cooling_period_after_failure),
                            "time_since_failure": str(time_since_failure)
                        }
                    )
            
            return ValidationResult(True, "No recent failures detected")
            
        except Exception as e:
            logger.error("Recent failure validation failed", error=str(e))
            return ValidationResult(False, f"Recent failure validation error: {str(e)}")
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation rules and limits"""
        return {
            "business_hours": self.business_hours,
            "minimum_membership_duration": str(self.minimum_membership_duration),
            "maximum_daily_deletions": self.maximum_daily_deletions,
            "cooling_period_after_failure": str(self.cooling_period_after_failure),
            "role_hierarchy": {
                "owner": 4,
                "admin": 3,
                "member": 2,
                "viewer": 1
            },
            "security_classification_requirements": {
                "public": ["owner", "admin", "member", "viewer"],
                "internal": ["owner", "admin", "member", "viewer"],
                "confidential": ["owner", "admin"],
                "restricted": ["owner"],
                "top_secret": ["owner"]
            }
        }

# Global business logic validator instance
business_validator = BusinessLogicValidator()
