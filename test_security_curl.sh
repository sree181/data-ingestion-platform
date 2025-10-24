#!/bin/bash

# Security Features Testing Script using curl
# Tests all security endpoints from the frontend perspective

set -e

# Configuration
API_BASE="http://localhost:3000/api/v1"
AUTH_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local expected_status=${5:-200}
    
    log_info "Testing: $description"
    
    local curl_cmd="curl -s -w '%{http_code}' -X $method"
    
    if [ -n "$AUTH_TOKEN" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $AUTH_TOKEN'"
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$API_BASE$endpoint'"
    
    local response=$(eval $curl_cmd)
    local status_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        log_success "$description: OK (HTTP $status_code)"
        if [ -n "$body" ] && [ "$body" != "null" ]; then
            echo "$body" | jq . 2>/dev/null || echo "$body"
        fi
        return 0
    else
        log_error "$description: FAILED (HTTP $status_code)"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 1
    fi
}

# Authentication test
test_authentication() {
    log_info "=== Testing Authentication ==="
    
    local login_data='{
        "email": "admin@test.com",
        "password": "password123",
        "organization": "Default Organization"
    }'
    
    if test_endpoint "POST" "/auth/login" "User Login" "$login_data"; then
        # Extract token from response
        local response=$(curl -s -X POST -H 'Content-Type: application/json' -d "$login_data" "$API_BASE/auth/login")
        AUTH_TOKEN=$(echo "$response" | jq -r '.access_token // empty')
        
        if [ -n "$AUTH_TOKEN" ] && [ "$AUTH_TOKEN" != "null" ]; then
            log_success "Authentication token obtained: ${AUTH_TOKEN:0:20}..."
            
            # Test token validation
            test_endpoint "GET" "/auth/me" "Token Validation"
            return 0
        else
            log_error "Failed to extract authentication token"
            return 1
        fi
    else
        log_error "Authentication failed"
        return 1
    fi
}

# Security monitoring tests
test_security_monitoring() {
    log_info "=== Testing Security Monitoring ==="
    
    test_endpoint "GET" "/security/health" "Security Health Check"
    test_endpoint "GET" "/security/alerts" "Security Alerts"
    test_endpoint "GET" "/security/dashboard" "Security Dashboard"
}

# Compliance framework tests
test_compliance_framework() {
    log_info "=== Testing Compliance Framework ==="
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for compliance tests"
        return 1
    fi
    
    test_endpoint "GET" "/security/compliance/frameworks" "Get Compliance Frameworks"
    
    local validation_data='{
        "space_id": "test-space",
        "framework": "gdpr",
        "data_types": ["personal_data"]
    }'
    
    test_endpoint "POST" "/compliance/validate" "Compliance Validation" "$validation_data"
}

# Access control tests
test_access_control() {
    log_info "=== Testing Access Control ==="
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for access control tests"
        return 1
    fi
    
    # Test IP Whitelist
    local ip_data='{
        "space_id": "test-space",
        "policy_type": "ip_whitelist",
        "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"]
    }'
    
    test_endpoint "POST" "/access-control/policies" "IP Whitelist Policy" "$ip_data"
    
    # Test Domain Restrictions
    local domain_data='{
        "space_id": "test-space",
        "policy_type": "domain_restriction",
        "allowed_domains": ["company.com", "partner.com"]
    }'
    
    test_endpoint "POST" "/access-control/policies" "Domain Restrictions" "$domain_data"
    
    # Test Time Restrictions
    local time_data='{
        "space_id": "test-space",
        "policy_type": "time_restriction",
        "allowed_hours": {"start": "09:00", "end": "17:00"},
        "allowed_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    }'
    
    test_endpoint "POST" "/access-control/policies" "Time Restrictions" "$time_data"
}

# Audit logging tests
test_audit_logging() {
    log_info "=== Testing Audit Logging ==="
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for audit logging tests"
        return 1
    fi
    
    # Test audit event logging
    local audit_data='{
        "event_type": "user_login",
        "category": "authentication",
        "severity": "info",
        "user_id": "test-user",
        "event_description": "User logged in successfully",
        "event_data": {"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0..."}
    }'
    
    test_endpoint "POST" "/audit/log" "Audit Event Logging" "$audit_data"
    test_endpoint "GET" "/audit/events?limit=10&category=authentication" "Audit Event Querying"
    test_endpoint "GET" "/audit/statistics" "Audit Statistics"
}

# Data classification tests
test_data_classification() {
    log_info "=== Testing Data Classification ==="
    
    test_endpoint "GET" "/data-classification/levels" "Classification Levels"
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for advanced classification tests"
        return 0
    fi
    
    # Test auto classification
    local classification_data='{
        "document_id": "test-doc-123",
        "content": "This document contains personal information like John Doe'\''s SSN: 123-45-6789 and email: john@example.com"
    }'
    
    test_endpoint "POST" "/data-classification/documents/auto" "Auto Classification" "$classification_data"
    test_endpoint "GET" "/data-classification/policies" "Classification Policies"
}

# MFA and advanced security tests
test_mfa_security() {
    log_info "=== Testing MFA & Advanced Security ==="
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for MFA tests"
        return 1
    fi
    
    # Test MFA setup
    local mfa_data='{
        "user_id": "test-user"
    }'
    
    test_endpoint "POST" "/auth/mfa/setup" "MFA Setup" "$mfa_data"
    
    # Test encryption
    local encryption_data='{
        "data": "This is sensitive data that needs encryption"
    }'
    
    test_endpoint "POST" "/security/encryption/test" "Encryption Test" "$encryption_data"
}

# Project spaces security tests
test_project_spaces_security() {
    log_info "=== Testing Project Spaces Security ==="
    
    if [ -z "$AUTH_TOKEN" ]; then
        log_warning "Authentication required for project spaces tests"
        return 1
    fi
    
    # Test space configuration
    local space_data='{
        "name": "Test Security Space",
        "description": "A test space for security features",
        "security_classification": "confidential",
        "requires_mfa": true,
        "encryption_enabled": true,
        "compliance_frameworks": ["gdpr", "hipaa"]
    }'
    
    test_endpoint "POST" "/project-spaces" "Space Configuration" "$space_data"
    
    # Test space permissions
    local permission_data='{
        "user_id": "test-user-2",
        "permission": "read"
    }'
    
    test_endpoint "POST" "/project-spaces/test-space/members" "Space Permissions" "$permission_data"
}

# Rate limiting test
test_rate_limiting() {
    log_info "=== Testing Rate Limiting ==="
    
    log_info "Making 10 rapid requests to test rate limiting..."
    
    local success_count=0
    local rate_limited_count=0
    
    for i in {1..10}; do
        local response=$(curl -s -w '%{http_code}' "$API_BASE/security/health")
        local status_code="${response: -3}"
        
        if [ "$status_code" = "200" ]; then
            ((success_count++))
        elif [ "$status_code" = "429" ]; then
            ((rate_limited_count++))
        fi
        
        sleep 0.1
    done
    
    log_info "Rate Limiting Test Results:"
    log_info "  Total requests: 10"
    log_info "  Successful: $success_count"
    log_info "  Rate limited: $rate_limited_count"
}

# Main function
main() {
    log_info "🚀 Starting Security Features Testing"
    log_info "API Base URL: $API_BASE"
    echo "============================================================"
    
    local test_type=${1:-"all"}
    local total_tests=0
    local passed_tests=0
    
    case $test_type in
        "auth")
            test_authentication && ((passed_tests++))
            ((total_tests++))
            ;;
        "monitoring")
            test_security_monitoring && ((passed_tests++))
            ((total_tests++))
            ;;
        "compliance")
            test_compliance_framework && ((passed_tests++))
            ((total_tests++))
            ;;
        "access")
            test_access_control && ((passed_tests++))
            ((total_tests++))
            ;;
        "audit")
            test_audit_logging && ((passed_tests++))
            ((total_tests++))
            ;;
        "classification")
            test_data_classification && ((passed_tests++))
            ((total_tests++))
            ;;
        "mfa")
            test_mfa_security && ((passed_tests++))
            ((total_tests++))
            ;;
        "spaces")
            test_project_spaces_security && ((passed_tests++))
            ((total_tests++))
            ;;
        "rate")
            test_rate_limiting && ((passed_tests++))
            ((total_tests++))
            ;;
        "all"|*)
            test_authentication && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_security_monitoring && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_compliance_framework && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_access_control && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_audit_logging && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_data_classification && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_mfa_security && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_project_spaces_security && ((passed_tests++))
            ((total_tests++))
            echo ""
            
            test_rate_limiting && ((passed_tests++))
            ((total_tests++))
            ;;
    esac
    
    echo "============================================================"
    log_info "📊 TEST SUMMARY"
    echo "============================================================"
    log_info "Overall Result: $passed_tests/$total_tests tests passed"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_success "🎉 All security features are working correctly!"
        exit 0
    else
        log_warning "⚠️ $((total_tests - passed_tests)) tests failed. Please check the logs above."
        exit 1
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    log_error "jq is required but not installed. Please install jq to run this script."
    exit 1
fi

# Run main function with arguments
main "$@"
