# 🔐 Security & Access Control Features

**Last Updated**: October 5, 2025  
**Status**: ✅ Active & Operational

---

## 📋 Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Access Control (RBAC)](#access-control-rbac)
3. [Security Monitoring](#security-monitoring)
4. [Rate Limiting](#rate-limiting)
5. [Business Logic Validation](#business-logic-validation)
6. [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)
7. [Encryption & Data Protection](#encryption--data-protection)
8. [Audit Logging](#audit-logging)
9. [API Endpoints Protection](#api-endpoints-protection)
10. [Configuration & Environment](#configuration--environment)

---

## 🔑 Authentication & Authorization

### JWT-Based Authentication

**Location**: `services/api-gateway/auth/jwt_auth.py`, `jwt_service.py`, `jwt_handler.py`

**Features**:
- **JWT Token Generation**: HS256 algorithm with configurable expiration
- **Token Validation**: Signature verification and expiration checks
- **Session Management**: 8-hour session timeout (configurable)
- **Refresh Tokens**: Secure token refresh mechanism
- **Account Lockout**: 5 failed attempts → 30-minute lockout

**Implementation**:
```python
class JWTAuthService:
    - authenticate_user(email, password, ip_address, user_agent, mfa_token)
    - generate_token(user_id, email, role)
    - validate_token(token)
    - refresh_token(refresh_token)
```

**Protected Routes**:
- All routes use `Depends(get_current_user)` or `Depends(require_mfa_verification)`
- 228+ protected endpoints across 15 route files

---

## 👥 Access Control (RBAC)

### 10-Tier Hierarchical Role System

**Location**: `services/api-gateway/models/security_models.py`

**Roles** (Highest → Lowest):
1. **SUPER_ADMIN** - Platform-wide access
2. **ORG_ADMIN** - Organization-wide access
3. **PROJECT_OWNER** - Full project control
4. **PROJECT_ADMIN** - Project administration
5. **PROJECT_MANAGER** - Project management
6. **SENIOR_ANALYST** - Advanced analysis + limited admin
7. **ANALYST** - Standard analysis access
8. **REVIEWER** - Read + comment access
9. **VIEWER** - Read-only access
10. **GUEST** - Limited temporary access

### 15+ Permission Types

**Document Permissions**:
- `CREATE_DOCUMENT`
- `READ_DOCUMENT`
- `UPDATE_DOCUMENT`
- `DELETE_DOCUMENT`
- `DOWNLOAD_DOCUMENT`

**Project Permissions**:
- `CREATE_PROJECT`
- `READ_PROJECT`
- `UPDATE_PROJECT`
- `DELETE_PROJECT`
- `ARCHIVE_PROJECT`

**User Management**:
- `INVITE_USER`
- `REMOVE_USER`
- `MANAGE_ROLES`
- `VIEW_AUDIT_LOGS`

**Advanced Features**:
- `EXPORT_DATA`
- `BULK_OPERATIONS`
- `API_ACCESS`
- `SYSTEM_SETTINGS`

### Security Classifications

**5 Data Security Levels**:
1. **PUBLIC** - No restrictions
2. **INTERNAL** - Internal use only
3. **CONFIDENTIAL** - Restricted access
4. **SECRET** - High-level clearance required
5. **TOP_SECRET** - Maximum security

---

## 🛡️ Security Monitoring

### Real-Time Threat Detection

**Location**: `services/api-gateway/security/security_monitor.py`

**Features**:
- **Event Tracking**: Last 10,000 security events stored in-memory
- **User Activity Monitoring**: Per-user activity tracking (last 1,000 events)
- **IP Activity Monitoring**: Per-IP activity tracking (last 1,000 events)
- **Automated Alerting**: Multi-level threat response

### Threat Levels

```python
class ThreatLevel(Enum):
    LOW = "low"           # Informational
    MEDIUM = "medium"     # Warning
    HIGH = "high"         # Urgent action required
    CRITICAL = "critical" # Immediate response
```

### Security Event Types

- **AUTH_FAILURE** - Failed authentication attempts
- **RATE_LIMIT_EXCEEDED** - Rate limit violations
- **SUSPICIOUS_ACTIVITY** - Anomalous behavior detected
- **PRIVILEGE_ESCALATION** - Unauthorized role changes
- **DATA_BREACH_ATTEMPT** - Data exfiltration attempts
- **MFA_BYPASS_ATTEMPT** - MFA circumvention attempts
- **BULK_OPERATION** - Large-scale operations
- **UNUSUAL_TIME_ACCESS** - Off-hours access
- **GEOGRAPHIC_ANOMALY** - Unusual location access

### Automated Alert Rules

| Rule Name | Threshold | Window | Threat Level | Action |
|-----------|-----------|--------|--------------|--------|
| **Multiple Auth Failures** | 5 attempts | 15 min | HIGH | Block IP |
| **Rapid Requests** | 100 requests | 5 min | MEDIUM | Rate limit |
| **Privilege Escalation** | 1 attempt | 60 min | CRITICAL | Disable user + Block IP |
| **Bulk Operations** | 3 operations | 60 min | MEDIUM | Alert |
| **Unusual Time Access** | 1 access | 60 min | LOW | Log |
| **MFA Bypass Attempts** | 3 attempts | 30 min | HIGH | Block IP |

### Automated Response Actions

**High/Critical Threats**:
- ✅ IP blocking (automatic)
- ✅ Security alert generation
- ✅ Audit log entry

**Critical Threats Only**:
- ✅ User account suspension
- ✅ Session termination
- ✅ Admin notification

---

## ⏱️ Rate Limiting

### Sliding Window Algorithm

**Location**: `services/api-gateway/security/rate_limiter.py`

**Features**:
- **In-Memory Storage**: Fast, lightweight (production: use Redis)
- **Sliding Window**: Accurate rate calculation
- **Automatic Blocking**: Progressive penalties
- **Suspicious IP Tracking**: 24-hour monitoring

### Rate Limit Configurations

#### Authentication Endpoints
```python
"auth": {
    "login": {"limit": 5, "window": 300},      # 5 attempts per 5 min
    "mfa": {"limit": 10, "window": 300},       # 10 attempts per 5 min
    "refresh": {"limit": 20, "window": 3600}   # 20 refreshes per hour
}
```

#### Sensitive Operations
```python
"sensitive": {
    "delete_space": {"limit": 20, "window": 3600},      # 20 deletions per hour
    "bulk_delete": {"limit": 5, "window": 3600},        # 5 bulk deletes per hour
    "security_config": {"limit": 10, "window": 3600}    # 10 config changes per hour
}
```

#### General API
```python
"general": {
    "api": {"limit": 100, "window": 3600},      # 100 requests per hour
    "upload": {"limit": 20, "window": 3600},    # 20 uploads per hour
    "search": {"limit": 200, "window": 3600}    # 200 searches per hour
}
```

### Block Duration Penalties

| Request Type | Block Duration | Max Duration |
|--------------|----------------|--------------|
| **Sensitive** | 10x window | Up to 1 hour |
| **Auth** | 5x window | Up to 30 min |
| **General** | 2x window | Up to 15 min |

---

## ⚖️ Business Logic Validation

### Deletion Request Validation

**Location**: `services/api-gateway/security/business_logic_validator.py`

**Features**:
- **Business Hours Check**: 9 AM - 5 PM UTC (configurable)
- **Membership Duration**: 24-hour minimum (bypassable by admin)
- **Daily Deletion Limit**: 5 deletions per user per day
- **Space Dependencies**: Checks for active documents/members
- **Cooling Period**: 30-minute cooldown after failed attempts

### Validation Checks

#### 1. Business Hours Validation
```python
business_hours = {
    "start": 9,   # 9 AM
    "end": 17,    # 5 PM
    "timezone": "UTC"
}
```
**Admin Override**: ✅ Yes

#### 2. Minimum Membership Duration
```python
minimum_membership_duration = timedelta(hours=24)
```
**Admin Override**: ✅ Yes (as of latest fix)

#### 3. Daily Deletion Limit
```python
maximum_daily_deletions = 5
```
**Admin Override**: ❌ No

#### 4. Space Dependencies
- Checks for active documents
- Checks for active members
- Validates no blocking dependencies

**Admin Override**: ❌ No

#### 5. User Role Validation
- Verifies user has sufficient permissions
- Checks role hierarchy

**Admin Override**: ❌ No

### Admin Override Logic

```python
is_admin = user_role in ['admin', 'owner']
admin_override = is_admin and auth_level in ['admin', 'owner']
```

**Bypasses**:
- ✅ Business hours restriction
- ✅ Membership duration requirement
- ❌ Daily deletion limit (still enforced)
- ❌ Space dependencies (still enforced)

---

## 🔐 Multi-Factor Authentication (MFA)

### TOTP-Based MFA

**Location**: `services/api-gateway/auth/mfa_service.py`

**Features**:
- **TOTP Protocol**: Time-based One-Time Password (RFC 6238)
- **QR Code Generation**: Easy setup with authenticator apps
- **Backup Codes**: 10 one-time recovery codes
- **Flexible Window**: 1-window tolerance (±30 seconds)

### MFA Setup Flow

```
1. User initiates MFA setup
   ↓
2. System generates TOTP secret
   ↓
3. QR code generated (base64 PNG)
   ↓
4. User scans with authenticator app
   ↓
5. User enters verification code
   ↓
6. System validates and enables MFA
   ↓
7. Backup codes provided
```

### MFA Service Methods

```python
class MFAService:
    - generate_secret() → str
    - generate_qr_code(user_id, email, secret) → base64_image
    - verify_totp(secret, token) → bool
    - generate_backup_codes() → List[str]
    - verify_backup_code(code, stored_codes) → bool
    - setup_mfa(user_id, email) → Dict
    - authenticate_with_mfa(secret, token, backup_codes) → Dict
```

### MFA Configuration

```python
issuer_name = "Data Ingestion Platform"
totp_digits = 6
totp_interval = 30  # seconds
backup_codes_count = 10
```

---

## 🔒 Encryption & Data Protection

### AES-256 Encryption at Rest

**Location**: `services/api-gateway/security/encryption_service.py`

**Features**:
- **Algorithm**: AES-256-CBC
- **Key Management**: Automated key rotation
- **Key Hierarchy**: Master key → Project keys
- **Integrity Protection**: HMAC-SHA256 checksums

### Encryption Workflow

```
Master Key (Password-derived)
├── Project Keys (AES-256)
│   ├── Document Encryption Keys
│   └── Metadata Encryption Keys
└── User Keys (AES-256)
    └── Sensitive User Data Keys
```

### Data Classification & Encryption

| Classification | Encryption Required | Key Rotation | Access Control |
|----------------|---------------------|--------------|----------------|
| **PUBLIC** | ❌ No | N/A | Open |
| **INTERNAL** | ✅ Yes | 90 days | Role-based |
| **CONFIDENTIAL** | ✅ Yes | 30 days | Restricted |
| **SECRET** | ✅ Yes | 7 days | High clearance |
| **TOP_SECRET** | ✅ Yes | Daily | Maximum security |

---

## 📝 Audit Logging

### Comprehensive Activity Tracking

**Location**: `services/api-gateway/models/security_models.py` (AuditLog model)

**Logged Events**:
- **Authentication**: Login, logout, MFA events
- **Authorization**: Permission checks, role changes
- **Data Access**: Document reads, downloads, exports
- **Data Modification**: Creates, updates, deletes
- **Security Events**: Failed logins, rate limits, alerts
- **Administrative Actions**: User management, config changes

### Audit Log Schema

```python
class AuditLog(Base):
    id: int
    user_id: int
    project_id: int
    action: AuditAction
    resource_type: str
    resource_id: str
    details: JSON
    ip_address: str
    user_agent: str
    timestamp: datetime
    risk_score: int
```

### Audit Actions

```python
class AuditAction(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    MFA_SETUP = "mfa_setup"
    MFA_FAILED = "mfa_failed"
    PERMISSION_DENIED = "permission_denied"
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_ACCESSED = "document_accessed"
    DOCUMENT_DELETED = "document_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_DELETED = "project_deleted"
    USER_INVITED = "user_invited"
    ROLE_CHANGED = "role_changed"
    SECURITY_ALERT = "security_alert"
```

---

## 🔗 API Endpoints Protection

### Protected Route Categories

**Total Protected Endpoints**: 228+ across 15 route files

#### 1. Project Spaces (`project_spaces.py`)
- **MFA Required**: ✅ Delete operations
- **Auth Required**: ✅ All CRUD operations
- **Rate Limited**: ✅ Sensitive operations

#### 2. Document Ingestion (`document_ingestion.py`)
- **Auth Required**: ✅ All operations
- **Rate Limited**: ✅ Upload operations

#### 3. Knowledge Hub (`knowledge_hub.py`)
- **Auth Required**: ✅ All operations
- **Rate Limited**: ✅ Search operations

#### 4. Investigation Board (`investigation.py`)
- **Auth Required**: ✅ All operations
- **Rate Limited**: ❌ No

#### 5. Workflow Builder (`workflow.py`)
- **Auth Required**: ✅ All operations
- **Rate Limited**: ❌ No

#### 6. Source Configuration (`source_config.py`)
- **Auth Required**: ⚠️ Partial (some public endpoints)
- **Rate Limited**: ✅ Config changes

#### 7. Security Endpoints (`security_endpoints.py`)
- **Auth Required**: ⚠️ Login/MFA setup public
- **Rate Limited**: ✅ All auth operations

### Authentication Dependency Injection

```python
# Standard authentication
async def protected_endpoint(
    user: dict = Depends(get_current_user)
):
    # Endpoint logic

# MFA-required authentication
async def sensitive_endpoint(
    user: dict = Depends(require_mfa_verification)
):
    # Endpoint logic
```

---

## ⚙️ Configuration & Environment

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY="your-secure-jwt-secret-key"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_HOURS=8

# MFA Configuration
MFA_ISSUER_NAME="Data Ingestion Platform"
MFA_TOTP_DIGITS=6
MFA_TOTP_INTERVAL=30

# Encryption Configuration
MASTER_ENCRYPTION_KEY="your-master-encryption-password"
ENCRYPTION_ALGORITHM="AES-256-CBC"

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND="memory"  # or "redis"
REDIS_URL="redis://localhost:6379"

# Security Monitoring
SECURITY_MONITORING_ENABLED=true
ALERT_WEBHOOK_URL="https://your-webhook-endpoint"
SMTP_SERVER="your-smtp-server"
SMTP_PORT=587

# Business Logic
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=17
BUSINESS_HOURS_TIMEZONE="UTC"
MIN_MEMBERSHIP_DURATION_HOURS=24
MAX_DAILY_DELETIONS=5
```

### Database Configuration

**PostgreSQL Schema**: `sql/enhanced_security_schema.sql`

**Tables**:
- `users` - User accounts and profiles
- `organizations` - Organization management
- `projects` - Project spaces
- `project_members` - Project membership and roles
- `documents` - Document metadata
- `audit_logs` - Comprehensive audit trail
- `user_sessions` - Active session tracking
- `security_alerts` - Security alert history
- `compliance_assessments` - Compliance tracking
- `encryption_keys` - Key management

---

## 📊 Security Dashboard Metrics

### Real-Time Monitoring

**Available via**: `/api/v1/security/dashboard`

**Metrics**:
- **Overall Security Score**: 0-100 composite score
- **Active Threats**: Real-time threat count
- **Recent Events**: Last 50 security events (24h)
- **Active Alerts**: Unresolved security alerts
- **Threat Level Distribution**: Event breakdown by severity
- **Top Suspicious IPs**: Most flagged IP addresses
- **MFA Adoption Rate**: Percentage of users with MFA enabled
- **Encryption Health**: Key rotation status
- **Compliance Score**: Multi-framework compliance percentage

### Security Health API

```python
GET /api/v1/security/health
Response:
{
  "status": "healthy",
  "monitoring_enabled": true,
  "active_alerts": 2,
  "total_events_24h": 1247,
  "threat_level_distribution": {
    "low": 1100,
    "medium": 120,
    "high": 25,
    "critical": 2
  }
}
```

---

## 🚨 Security Alerts API

### Get Active Alerts

```python
GET /api/v1/security/alerts
Response:
{
  "success": true,
  "alerts": [
    {
      "alert_id": "alert_multiple_auth_failures_1728123456",
      "rule_name": "multiple_auth_failures",
      "threat_level": "high",
      "description": "Multiple authentication failures from same IP",
      "timestamp": "2025-10-05T12:34:56Z",
      "actions_taken": ["ip_blocked", "alert_logged"]
    }
  ]
}
```

### Resolve Alert

```python
POST /api/v1/security/alerts/{alert_id}/resolve
Response:
{
  "success": true,
  "message": "Alert resolved successfully"
}
```

---

## 🎯 Best Practices & Recommendations

### For Administrators

1. **Enable MFA**: Require MFA for all admin and owner accounts
2. **Monitor Alerts**: Review security alerts daily
3. **Audit Logs**: Regular audit log reviews (weekly)
4. **Key Rotation**: Follow encryption key rotation schedules
5. **Rate Limits**: Adjust rate limits based on usage patterns
6. **Business Hours**: Configure business hours for your timezone

### For Developers

1. **Use Dependencies**: Always use `Depends(get_current_user)` for protected routes
2. **Rate Limiting**: Apply rate limiting to all sensitive operations
3. **Audit Logging**: Log all security-relevant actions
4. **Error Handling**: Don't leak sensitive information in error messages
5. **Input Validation**: Validate and sanitize all user inputs
6. **HTTPS Only**: Always use HTTPS in production

### For Users

1. **Enable MFA**: Set up multi-factor authentication
2. **Strong Passwords**: Use complex, unique passwords
3. **Backup Codes**: Store MFA backup codes securely
4. **Session Management**: Log out when done
5. **Suspicious Activity**: Report unusual activity immediately

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Account temporarily locked"
**Cause**: 5+ failed login attempts  
**Solution**: Wait 30 minutes or contact admin for manual unlock

#### 2. "Rate limit exceeded"
**Cause**: Too many requests in short time  
**Solution**: Wait for the retry-after period (check `Retry-After` header)

#### 3. "Business logic validation failed: Minimum membership duration not met"
**Cause**: Trying to delete project within 24 hours of creation  
**Solution**: Wait 24 hours OR use admin override (owner/admin role)

#### 4. "MFA token required"
**Cause**: MFA enabled but token not provided  
**Solution**: Provide 6-digit TOTP code from authenticator app

#### 5. "Request outside business hours"
**Cause**: Attempting sensitive operation outside configured hours  
**Solution**: Wait for business hours OR use admin override

---

## 📚 Related Documentation

- **Enterprise Security Framework**: `docs/archive/ENTERPRISE_SECURITY_README.md`
- **Database Schema**: `sql/enhanced_security_schema.sql`
- **Project Spaces Schema**: `sql/project_spaces.sql`
- **Design Enhancements**: `DESIGN_ENHANCEMENTS.md`

---

## 🔄 Recent Updates

### October 5, 2025
- ✅ Fixed UUID serialization in delete endpoint
- ✅ Added admin override for membership duration check
- ✅ Updated rate limits for development (increased limits)
- ✅ Improved business logic validation logging

### Previous Updates
- ✅ Implemented Gothic Noir color palette
- ✅ Enhanced Project Spaces UI/UX
- ✅ Added Workflow Builder with persistence
- ✅ Implemented AI Investigation Report Generator
- ✅ Added Entity-Centric Chat with RAG
- ✅ Implemented Knowledge Hub with Neo4j integration

---

## 📞 Support & Contact

For security-related questions or to report vulnerabilities:
- **Email**: security@yourcompany.com
- **Slack**: #security-team
- **Emergency**: security-oncall@yourcompany.com

---

**Document Version**: 1.0  
**Last Reviewed**: October 5, 2025  
**Next Review**: November 5, 2025
