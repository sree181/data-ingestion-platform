#!/usr/bin/env python3
"""
Comprehensive Security Features Testing Script
Tests all security endpoints and features from the frontend perspective
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:3000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Make HTTP request and return response data"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_data = response.json() if response.content else {}
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == expected_status,
                "data": response_data,
                "error": None
            }
            
            if not result["success"]:
                result["error"] = response_data.get("detail", f"HTTP {response.status_code}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "success": False,
                "data": {},
                "error": str(e)
            }
    
    def test_authentication(self) -> bool:
        """Test authentication and JWT token generation"""
        self.log("Testing Authentication & JWT Token Generation")
        
        # Test login
        login_data = {
            "email": "admin@test.com",
            "password": "password123",
            "organization": "Default Organization"
        }
        
        result = self.make_request("/auth/login", "POST", login_data)
        
        if result["success"]:
            self.auth_token = result["data"].get("access_token")
            self.log(f"✅ Login successful, token received: {self.auth_token[:20]}...")
            
            # Test token validation
            me_result = self.make_request("/auth/me")
            if me_result["success"]:
                self.log("✅ Token validation successful")
                return True
            else:
                self.log(f"❌ Token validation failed: {me_result['error']}", "ERROR")
                return False
        else:
            self.log(f"❌ Login failed: {result['error']}", "ERROR")
            return False
    
    def test_security_monitoring(self) -> bool:
        """Test security monitoring endpoints"""
        self.log("Testing Security Monitoring")
        
        tests = [
            ("/security/health", "Security Health Check"),
            ("/security/alerts", "Security Alerts"),
            ("/security/dashboard", "Security Dashboard")
        ]
        
        all_passed = True
        
        for endpoint, description in tests:
            result = self.make_request(endpoint)
            if result["success"]:
                self.log(f"✅ {description}: OK")
            else:
                self.log(f"❌ {description}: {result['error']}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def test_compliance_framework(self) -> bool:
        """Test compliance framework endpoints"""
        self.log("Testing Compliance Framework")
        
        if not self.auth_token:
            self.log("❌ Authentication required for compliance tests", "ERROR")
            return False
        
        tests = [
            ("/security/compliance/frameworks", "Get Compliance Frameworks"),
        ]
        
        all_passed = True
        
        for endpoint, description in tests:
            result = self.make_request(endpoint)
            if result["success"]:
                self.log(f"✅ {description}: OK")
            else:
                self.log(f"❌ {description}: {result['error']}", "ERROR")
                all_passed = False
        
        # Test compliance validation
        validation_data = {
            "space_id": "test-space",
            "framework": "gdpr",
            "data_types": ["personal_data"]
        }
        
        result = self.make_request("/compliance/validate", "POST", validation_data)
        if result["success"]:
            self.log("✅ Compliance Validation: OK")
        else:
            self.log(f"❌ Compliance Validation: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_access_control(self) -> bool:
        """Test access control endpoints"""
        self.log("Testing Access Control")
        
        if not self.auth_token:
            self.log("❌ Authentication required for access control tests", "ERROR")
            return False
        
        all_passed = True
        
        # Test IP Whitelist
        ip_data = {
            "space_id": "test-space",
            "policy_type": "ip_whitelist",
            "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"]
        }
        
        result = self.make_request("/access-control/policies", "POST", ip_data)
        if result["success"]:
            self.log("✅ IP Whitelist Policy: OK")
        else:
            self.log(f"❌ IP Whitelist Policy: {result['error']}", "ERROR")
            all_passed = False
        
        # Test Domain Restrictions
        domain_data = {
            "space_id": "test-space",
            "policy_type": "domain_restriction",
            "allowed_domains": ["company.com", "partner.com"]
        }
        
        result = self.make_request("/access-control/policies", "POST", domain_data)
        if result["success"]:
            self.log("✅ Domain Restrictions: OK")
        else:
            self.log(f"❌ Domain Restrictions: {result['error']}", "ERROR")
            all_passed = False
        
        # Test Time Restrictions
        time_data = {
            "space_id": "test-space",
            "policy_type": "time_restriction",
            "allowed_hours": {"start": "09:00", "end": "17:00"},
            "allowed_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
        
        result = self.make_request("/access-control/policies", "POST", time_data)
        if result["success"]:
            self.log("✅ Time Restrictions: OK")
        else:
            self.log(f"❌ Time Restrictions: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_audit_logging(self) -> bool:
        """Test audit logging endpoints"""
        self.log("Testing Audit Logging")
        
        if not self.auth_token:
            self.log("❌ Authentication required for audit logging tests", "ERROR")
            return False
        
        all_passed = True
        
        # Test audit event logging
        audit_data = {
            "event_type": "user_login",
            "category": "authentication",
            "severity": "info",
            "user_id": "test-user",
            "event_description": "User logged in successfully",
            "event_data": {"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0..."}
        }
        
        result = self.make_request("/audit/log", "POST", audit_data)
        if result["success"]:
            self.log("✅ Audit Event Logging: OK")
        else:
            self.log(f"❌ Audit Event Logging: {result['error']}", "ERROR")
            all_passed = False
        
        # Test audit event querying
        result = self.make_request("/audit/events?limit=10&category=authentication")
        if result["success"]:
            self.log("✅ Audit Event Querying: OK")
        else:
            self.log(f"❌ Audit Event Querying: {result['error']}", "ERROR")
            all_passed = False
        
        # Test audit statistics
        result = self.make_request("/audit/statistics")
        if result["success"]:
            self.log("✅ Audit Statistics: OK")
        else:
            self.log(f"❌ Audit Statistics: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_data_classification(self) -> bool:
        """Test data classification endpoints"""
        self.log("Testing Data Classification")
        
        all_passed = True
        
        # Test classification levels
        result = self.make_request("/data-classification/levels")
        if result["success"]:
            self.log("✅ Classification Levels: OK")
        else:
            self.log(f"❌ Classification Levels: {result['error']}", "ERROR")
            all_passed = False
        
        if not self.auth_token:
            self.log("⚠️ Authentication required for advanced classification tests", "WARNING")
            return all_passed
        
        # Test auto classification
        classification_data = {
            "document_id": "test-doc-123",
            "content": "This document contains personal information like John Doe's SSN: 123-45-6789 and email: john@example.com"
        }
        
        result = self.make_request("/data-classification/documents/auto", "POST", classification_data)
        if result["success"]:
            self.log("✅ Auto Classification: OK")
        else:
            self.log(f"❌ Auto Classification: {result['error']}", "ERROR")
            all_passed = False
        
        # Test classification policies
        result = self.make_request("/data-classification/policies")
        if result["success"]:
            self.log("✅ Classification Policies: OK")
        else:
            self.log(f"❌ Classification Policies: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_mfa_security(self) -> bool:
        """Test MFA and advanced security features"""
        self.log("Testing MFA & Advanced Security")
        
        if not self.auth_token:
            self.log("❌ Authentication required for MFA tests", "ERROR")
            return False
        
        all_passed = True
        
        # Test MFA setup
        mfa_data = {
            "user_id": "test-user"
        }
        
        result = self.make_request("/auth/mfa/setup", "POST", mfa_data)
        if result["success"]:
            self.log("✅ MFA Setup: OK")
        else:
            self.log(f"❌ MFA Setup: {result['error']}", "ERROR")
            all_passed = False
        
        # Test encryption
        encryption_data = {
            "data": "This is sensitive data that needs encryption"
        }
        
        result = self.make_request("/security/encryption/test", "POST", encryption_data)
        if result["success"]:
            self.log("✅ Encryption Test: OK")
        else:
            self.log(f"❌ Encryption Test: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_project_spaces_security(self) -> bool:
        """Test project spaces security features"""
        self.log("Testing Project Spaces Security")
        
        if not self.auth_token:
            self.log("❌ Authentication required for project spaces tests", "ERROR")
            return False
        
        all_passed = True
        
        # Test space configuration
        space_data = {
            "name": "Test Security Space",
            "description": "A test space for security features",
            "security_classification": "confidential",
            "requires_mfa": True,
            "encryption_enabled": True,
            "compliance_frameworks": ["gdpr", "hipaa"]
        }
        
        result = self.make_request("/project-spaces", "POST", space_data)
        if result["success"]:
            self.log("✅ Space Configuration: OK")
        else:
            self.log(f"❌ Space Configuration: {result['error']}", "ERROR")
            all_passed = False
        
        # Test space permissions
        permission_data = {
            "user_id": "test-user-2",
            "permission": "read"
        }
        
        result = self.make_request("/project-spaces/test-space/members", "POST", permission_data)
        if result["success"]:
            self.log("✅ Space Permissions: OK")
        else:
            self.log(f"❌ Space Permissions: {result['error']}", "ERROR")
            all_passed = False
        
        return all_passed
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        self.log("Testing Rate Limiting")
        
        # Make multiple rapid requests to test rate limiting
        requests_made = 0
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(10):
            result = self.make_request("/security/health")
            requests_made += 1
            
            if result["success"]:
                successful_requests += 1
            elif result["status_code"] == 429:  # Too Many Requests
                rate_limited_requests += 1
            
            time.sleep(0.1)  # Small delay between requests
        
        self.log(f"Rate Limiting Test Results:")
        self.log(f"  Total requests: {requests_made}")
        self.log(f"  Successful: {successful_requests}")
        self.log(f"  Rate limited: {rate_limited_requests}")
        
        return True  # Rate limiting test is informational
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all security tests and return results"""
        self.log("🚀 Starting Comprehensive Security Features Testing")
        self.log("=" * 60)
        
        results = {}
        
        # Test authentication first (required for most other tests)
        results["authentication"] = self.test_authentication()
        self.log("")
        
        # Test all security features
        results["security_monitoring"] = self.test_security_monitoring()
        self.log("")
        
        results["compliance_framework"] = self.test_compliance_framework()
        self.log("")
        
        results["access_control"] = self.test_access_control()
        self.log("")
        
        results["audit_logging"] = self.test_audit_logging()
        self.log("")
        
        results["data_classification"] = self.test_data_classification()
        self.log("")
        
        results["mfa_security"] = self.test_mfa_security()
        self.log("")
        
        results["project_spaces_security"] = self.test_project_spaces_security()
        self.log("")
        
        results["rate_limiting"] = self.test_rate_limiting()
        self.log("")
        
        # Print summary
        self.log("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log("")
        self.log(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 All security features are working correctly!", "SUCCESS")
        else:
            self.log(f"⚠️ {total_tests - passed_tests} tests failed. Please check the logs above.", "WARNING")
        
        return results

def main():
    """Main function to run security tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test all security features from frontend")
    parser.add_argument("--url", default="http://localhost:3000/api/v1", 
                       help="Base URL for API (default: http://localhost:3000/api/v1)")
    parser.add_argument("--test", choices=[
        "auth", "monitoring", "compliance", "access", "audit", 
        "classification", "mfa", "spaces", "rate", "all"
    ], default="all", help="Specific test to run (default: all)")
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url)
    
    if args.test == "all":
        results = tester.run_all_tests()
        sys.exit(0 if all(results.values()) else 1)
    else:
        # Run specific test
        test_methods = {
            "auth": tester.test_authentication,
            "monitoring": tester.test_security_monitoring,
            "compliance": tester.test_compliance_framework,
            "access": tester.test_access_control,
            "audit": tester.test_audit_logging,
            "classification": tester.test_data_classification,
            "mfa": tester.test_mfa_security,
            "spaces": tester.test_project_spaces_security,
            "rate": tester.test_rate_limiting
        }
        
        if args.test in test_methods:
            result = test_methods[args.test]()
            sys.exit(0 if result else 1)
        else:
            print(f"Unknown test: {args.test}")
            sys.exit(1)

if __name__ == "__main__":
    main()
