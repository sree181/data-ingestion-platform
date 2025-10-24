# 🔒 Security Features Testing Guide

This guide provides comprehensive instructions for testing all security features from the frontend perspective.

## 📋 Overview

The security testing suite includes:
- **Authentication & Authorization** - JWT tokens, user authentication, space permissions
- **Security Monitoring** - Health checks, alerts, dashboard
- **Compliance Framework** - GDPR, HIPAA, SOX compliance validation
- **Access Control** - IP whitelisting, domain restrictions, time-based access
- **Audit Logging** - Event logging, querying, statistics
- **Data Classification** - Automatic classification, policies, levels
- **MFA & Advanced Security** - Multi-factor authentication, encryption
- **Project Spaces Security** - Space configuration, permissions, security features

## 🚀 Quick Start

### Option 1: Interactive Web Interface (Recommended)

1. **Open the testing interface:**
   ```bash
   open test_security_features_frontend.html
   ```
   Or navigate to `http://localhost:3000/test_security_features_frontend.html` in your browser.

2. **Follow the guided testing:**
   - Click on each section to expand it
   - Click "Test" buttons to run individual tests
   - View results in real-time
   - Green indicators show successful tests

### Option 2: Command Line Testing

#### Python Script (Comprehensive)
```bash
# Test all security features
python test_security_endpoints.py

# Test specific features
python test_security_endpoints.py --test auth
python test_security_endpoints.py --test monitoring
python test_security_endpoints.py --test compliance
python test_security_endpoints.py --test access
python test_security_endpoints.py --test audit
python test_security_endpoints.py --test classification
python test_security_endpoints.py --test mfa
python test_security_endpoints.py --test spaces
python test_security_endpoints.py --test rate

# Use different API URL
python test_security_endpoints.py --url http://localhost:8000/api/v1
```

#### Shell Script (Quick Tests)
```bash
# Test all security features
./test_security_curl.sh

# Test specific features
./test_security_curl.sh auth
./test_security_curl.sh monitoring
./test_security_curl.sh compliance
./test_security_curl.sh access
./test_security_curl.sh audit
./test_security_curl.sh classification
./test_security_curl.sh mfa
./test_security_curl.sh spaces
./test_security_curl.sh rate
```

### Option 3: Manual curl Testing

```bash
# Test authentication
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "password123", "organization": "Default Organization"}'

# Test security health
curl http://localhost:3000/api/v1/security/health

# Test compliance frameworks
curl http://localhost:3000/api/v1/security/compliance/frameworks

# Test security alerts
curl http://localhost:3000/api/v1/security/alerts
```

## 🧪 Detailed Testing Procedures

### 1. Authentication & Authorization Testing

**Purpose:** Verify JWT token generation, user authentication, and space permissions.

**Tests:**
- ✅ JWT Token Generation
- ✅ User Authentication
- ✅ Space Permissions

**Expected Results:**
- Login returns valid JWT token
- Token validation succeeds
- Space permissions are properly enforced

### 2. Security Monitoring Testing

**Purpose:** Verify security system health, alerting, and monitoring capabilities.

**Tests:**
- ✅ Security Health Check
- ✅ Security Alerts
- ✅ Security Dashboard

**Expected Results:**
- Health check returns "healthy" status
- Alerts are properly formatted
- Dashboard data is accessible

### 3. Compliance Framework Testing

**Purpose:** Verify compliance framework management and validation.

**Tests:**
- ✅ Get Compliance Frameworks
- ✅ Compliance Validation
- ✅ Compliance Reports

**Expected Results:**
- Frameworks list includes GDPR, HIPAA, SOX, etc.
- Validation returns compliance status
- Reports are generated successfully

### 4. Access Control Testing

**Purpose:** Verify IP whitelisting, domain restrictions, and time-based access control.

**Tests:**
- ✅ IP Whitelist Policy
- ✅ Domain Restrictions
- ✅ Time Restrictions

**Expected Results:**
- IP policies are created successfully
- Domain restrictions are enforced
- Time-based access is configured

### 5. Audit Logging Testing

**Purpose:** Verify audit event logging, querying, and statistics.

**Tests:**
- ✅ Audit Event Logging
- ✅ Audit Event Querying
- ✅ Audit Statistics

**Expected Results:**
- Events are logged successfully
- Queries return filtered results
- Statistics are calculated correctly

### 6. Data Classification Testing

**Purpose:** Verify automatic data classification and policy management.

**Tests:**
- ✅ Classification Levels
- ✅ Auto Classification
- ✅ Classification Policies

**Expected Results:**
- Classification levels are defined
- Documents are automatically classified
- Policies are properly managed

### 7. MFA & Advanced Security Testing

**Purpose:** Verify multi-factor authentication and encryption services.

**Tests:**
- ✅ MFA Setup
- ✅ Encryption Test

**Expected Results:**
- MFA setup completes successfully
- Encryption/decryption works correctly

### 8. Project Spaces Security Testing

**Purpose:** Verify project space security configuration and permissions.

**Tests:**
- ✅ Space Configuration
- ✅ Space Permissions

**Expected Results:**
- Spaces are created with security settings
- Permissions are properly managed

### 9. Rate Limiting Testing

**Purpose:** Verify rate limiting functionality.

**Tests:**
- ✅ Rate Limiting

**Expected Results:**
- Rapid requests are rate limited appropriately

## 🔧 Troubleshooting

### Common Issues

1. **502 Bad Gateway Errors**
   - Ensure API Gateway service is running: `docker ps | grep api-gateway`
   - Check API Gateway logs: `docker logs api-gateway`

2. **Authentication Failures**
   - Verify login credentials are correct
   - Check if JWT service is properly configured

3. **Permission Denied Errors**
   - Ensure user has proper permissions for the space
   - Check space permission configuration

4. **Connection Refused**
   - Verify services are running: `docker-compose ps`
   - Check if ports are accessible: `curl http://localhost:3000/api/v1/health`

### Debug Commands

```bash
# Check service status
docker-compose ps

# View API Gateway logs
docker logs api-gateway --tail 50

# Test basic connectivity
curl -v http://localhost:3000/api/v1/health

# Check frontend connectivity
curl -v http://localhost:3000

# Test backend directly
curl -v http://localhost:8000/api/v1/health
```

## 📊 Test Results Interpretation

### Success Indicators
- ✅ Green checkmarks in web interface
- HTTP 200 status codes
- Valid JSON responses
- Proper authentication tokens

### Failure Indicators
- ❌ Red X marks in web interface
- HTTP 4xx/5xx status codes
- Error messages in responses
- Authentication failures

### Performance Metrics
- Response times < 2 seconds
- Rate limiting working correctly
- No memory leaks or resource issues

## 🔄 Continuous Testing

### Automated Testing
Set up automated testing in your CI/CD pipeline:

```bash
# Add to your CI pipeline
python test_security_endpoints.py --url $API_URL
```

### Monitoring
- Set up alerts for failed security tests
- Monitor response times and error rates
- Track authentication success rates

## 📝 Test Data

### Test Users
- **Admin User:** `admin@test.com` / `password123`
- **Test User:** `test@example.com` / `testpass123`

### Test Spaces
- **Test Space ID:** `test-space`
- **Test Document ID:** `test-doc-123`

### Test Data Samples
- **Personal Data:** "John Doe's SSN: 123-45-6789 and email: john@example.com"
- **Health Data:** "Patient diagnosis: diabetes, treatment: insulin"
- **Financial Data:** "Account balance: $10,000, transaction: $500"

## 🎯 Best Practices

1. **Test Authentication First:** Always test authentication before other features
2. **Use Real Data:** Test with realistic data samples
3. **Verify Permissions:** Test both authorized and unauthorized access
4. **Check Error Handling:** Verify proper error responses
5. **Monitor Performance:** Track response times and resource usage
6. **Document Results:** Keep records of test results and issues

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review service logs
3. Verify configuration settings
4. Test individual components
5. Contact the development team with detailed error information

---

**Happy Testing! 🚀**
