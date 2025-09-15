-- Enhanced Security Database Schema
-- Creates tables for RBAC, encryption, compliance, and monitoring

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'enterprise',
    security_settings JSONB DEFAULT '{}',
    compliance_requirements JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Security Fields
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(32),
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Profile
    department VARCHAR(100),
    job_title VARCHAR(100),
    phone VARCHAR(20),
    security_clearance VARCHAR(20) DEFAULT 'internal',
    
    -- Organizational
    organization_id INTEGER REFERENCES organizations(id) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_code VARCHAR(20) UNIQUE NOT NULL,
    
    -- Security Settings
    security_classification VARCHAR(20) DEFAULT 'internal',
    encryption_enabled BOOLEAN DEFAULT TRUE,
    data_retention_days INTEGER DEFAULT 2555,
    requires_mfa BOOLEAN DEFAULT FALSE,
    ip_whitelist JSONB DEFAULT '[]',
    allowed_domains JSONB DEFAULT '[]',
    
    -- Compliance
    compliance_frameworks JSONB DEFAULT '[]',
    data_location_restrictions JSONB DEFAULT '[]',
    
    -- Organizational
    organization_id INTEGER REFERENCES organizations(id) NOT NULL,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    archived_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Members table
CREATE TABLE IF NOT EXISTS project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    role VARCHAR(20) NOT NULL,
    
    -- Access Control
    permissions JSONB DEFAULT '[]',
    access_restrictions JSONB DEFAULT '{}',
    
    -- Delegation
    delegated_by INTEGER REFERENCES users(id),
    delegation_expires_at TIMESTAMP,
    
    -- Audit
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    invited_by INTEGER REFERENCES users(id) NOT NULL,
    joined_at TIMESTAMP,
    last_access TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(project_id, user_id)
);

-- Enhanced Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    
    -- Security
    security_classification VARCHAR(20) DEFAULT 'internal',
    encryption_key_id VARCHAR(255),
    checksum VARCHAR(64) NOT NULL,
    
    -- Access Control
    requires_approval BOOLEAN DEFAULT FALSE,
    download_restrictions JSONB DEFAULT '{}',
    
    -- Organizational
    project_id INTEGER REFERENCES projects(id) NOT NULL,
    uploaded_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    
    -- Event Details
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Event Data
    details JSONB DEFAULT '{}',
    risk_score INTEGER DEFAULT 0,
    
    -- Timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Session Details
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    terminated_by VARCHAR(50)
);

-- Encryption Keys table
CREATE TABLE IF NOT EXISTS encryption_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(64) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    key_type VARCHAR(20) NOT NULL,
    
    -- Encrypted key material
    encrypted_key BYTEA NOT NULL,
    key_derivation_salt BYTEA NOT NULL,
    
    -- Key metadata
    algorithm VARCHAR(20) DEFAULT 'AES-256',
    key_version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Rotation and lifecycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    rotated_at TIMESTAMP,
    rotation_frequency_days INTEGER DEFAULT 90,
    
    -- Audit
    created_by INTEGER REFERENCES users(id) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP
);

-- Encryption Audit Logs table
CREATE TABLE IF NOT EXISTS encryption_audit_logs (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(64) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    
    -- Context
    user_id INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    
    -- Audit details
    ip_address VARCHAR(45),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance Reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(64) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    framework VARCHAR(20) NOT NULL,
    
    -- Report metadata
    report_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Compliance scores
    overall_score FLOAT NOT NULL,
    control_scores JSONB NOT NULL,
    risk_assessment JSONB NOT NULL,
    
    -- Report content
    executive_summary TEXT NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    evidence JSONB NOT NULL,
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'draft',
    generated_by INTEGER REFERENCES users(id) NOT NULL,
    approved_by INTEGER REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP
);

-- Compliance Control Implementations table
CREATE TABLE IF NOT EXISTS compliance_control_implementations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) NOT NULL,
    control_id VARCHAR(50) NOT NULL,
    framework VARCHAR(20) NOT NULL,
    
    -- Implementation status
    status VARCHAR(20) NOT NULL,
    implementation_date TIMESTAMP,
    last_tested TIMESTAMP,
    next_test_due TIMESTAMP,
    
    -- Assessment results
    current_score FLOAT DEFAULT 0.0,
    evidence_collected JSONB DEFAULT '[]',
    gaps_identified JSONB DEFAULT '[]',
    remediation_plan JSONB DEFAULT '[]',
    
    -- Responsible parties
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    reviewer_id INTEGER REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security Alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    threat_level VARCHAR(20) NOT NULL,
    
    -- Alert content
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    events JSONB NOT NULL,
    affected_resources JSONB NOT NULL,
    recommended_actions JSONB NOT NULL,
    
    -- Context
    project_id INTEGER REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    source_ip VARCHAR(45),
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'open',
    assigned_to INTEGER REFERENCES users(id),
    escalated BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMP,
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Metadata
    correlation_id VARCHAR(64),
    false_positive BOOLEAN DEFAULT FALSE,
    suppressed BOOLEAN DEFAULT FALSE
);

-- Threat Intelligence table
CREATE TABLE IF NOT EXISTS threat_intelligence (
    id SERIAL PRIMARY KEY,
    indicator_type VARCHAR(20) NOT NULL,
    indicator_value VARCHAR(255) NOT NULL,
    threat_type VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    
    -- Threat details
    description TEXT,
    tags JSONB DEFAULT '[]',
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    
    -- Source information
    source VARCHAR(100) NOT NULL,
    source_reliability VARCHAR(20) DEFAULT 'unknown',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_project_timestamp ON audit_logs(project_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_timestamp ON audit_logs(action, timestamp);
CREATE INDEX IF NOT EXISTS idx_project_members_project_user ON project_members(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_encryption_keys_project ON encryption_keys(project_id);
CREATE INDEX IF NOT EXISTS idx_encryption_keys_type_active ON encryption_keys(key_type, is_active);
CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(status);
CREATE INDEX IF NOT EXISTS idx_security_alerts_threat_level ON security_alerts(threat_level);
CREATE INDEX IF NOT EXISTS idx_security_alerts_project ON security_alerts(project_id);

-- Insert default organization
INSERT INTO organizations (name, domain, subscription_tier) 
VALUES ('Default Organization', 'localhost', 'enterprise')
ON CONFLICT (domain) DO NOTHING;

-- Insert default admin user
INSERT INTO users (
    email, username, full_name, password_hash, 
    organization_id, security_clearance, mfa_enabled
) 
SELECT 
    'admin@localhost', 'admin', 'System Administrator', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3/4BjL0jSi', -- password: admin123
    o.id, 'top_secret', true
FROM organizations o WHERE o.domain = 'localhost'
ON CONFLICT (email) DO NOTHING;

-- Insert sample threat intelligence
INSERT INTO threat_intelligence (
    indicator_type, indicator_value, threat_type, confidence_score,
    description, first_seen, last_seen, source
) VALUES 
('ip', '192.168.100.100', 'malware_c2', 95.0, 'Known malware command and control server', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'internal_analysis'),
('ip', '10.0.0.100', 'brute_force', 80.0, 'IP associated with brute force attacks', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'honeypot_data')
ON CONFLICT DO NOTHING;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_control_implementations_updated_at BEFORE UPDATE ON compliance_control_implementations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threat_intelligence_updated_at BEFORE UPDATE ON threat_intelligence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
