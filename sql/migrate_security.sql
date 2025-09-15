-- Security Migration Script
-- Adds enhanced security tables to existing database

-- Check if security tables already exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'organizations') THEN
        -- Organizations table
        CREATE TABLE organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255) UNIQUE NOT NULL,
            subscription_tier VARCHAR(50) DEFAULT 'enterprise',
            security_settings JSONB DEFAULT '{}',
            compliance_requirements JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Insert default organization
        INSERT INTO organizations (name, domain, subscription_tier) 
        VALUES ('Default Organization', 'localhost', 'enterprise');
    END IF;

    -- Enhanced Users table (extend existing or create)
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'enhanced_users') THEN
        CREATE TABLE enhanced_users (
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
            organization_id INTEGER REFERENCES organizations(id) DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Insert default admin user
        INSERT INTO enhanced_users (
            email, username, full_name, password_hash, 
            organization_id, security_clearance, mfa_enabled
        ) VALUES (
            'admin@localhost', 'admin', 'System Administrator', 
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3/4BjL0jSi', -- password: admin123
            1, 'top_secret', true
        );
    END IF;

    -- Enhanced Projects table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'enhanced_projects') THEN
        CREATE TABLE enhanced_projects (
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
            organization_id INTEGER REFERENCES organizations(id) DEFAULT 1,
            created_by INTEGER REFERENCES enhanced_users(id) DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            archived_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    END IF;

    -- Project Members table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_members') THEN
        CREATE TABLE project_members (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES enhanced_projects(id) NOT NULL,
            user_id INTEGER REFERENCES enhanced_users(id) NOT NULL,
            role VARCHAR(20) NOT NULL,
            
            -- Access Control
            permissions JSONB DEFAULT '[]',
            access_restrictions JSONB DEFAULT '{}',
            
            -- Delegation
            delegated_by INTEGER REFERENCES enhanced_users(id),
            delegation_expires_at TIMESTAMP,
            
            -- Audit
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            invited_by INTEGER REFERENCES enhanced_users(id) NOT NULL,
            joined_at TIMESTAMP,
            last_access TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            
            UNIQUE(project_id, user_id)
        );
    END IF;

    -- Audit Logs table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        CREATE TABLE audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES enhanced_users(id),
            project_id INTEGER REFERENCES enhanced_projects(id),
            
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
    END IF;

    -- User Sessions table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_sessions') THEN
        CREATE TABLE user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES enhanced_users(id) NOT NULL,
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
    END IF;

    -- Encryption Keys table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'encryption_keys') THEN
        CREATE TABLE encryption_keys (
            id SERIAL PRIMARY KEY,
            key_id VARCHAR(64) UNIQUE NOT NULL,
            project_id INTEGER REFERENCES enhanced_projects(id),
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
            created_by INTEGER REFERENCES enhanced_users(id) NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP
        );
    END IF;

    -- Security Alerts table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'security_alerts') THEN
        CREATE TABLE security_alerts (
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
            project_id INTEGER REFERENCES enhanced_projects(id),
            user_id INTEGER REFERENCES enhanced_users(id),
            source_ip VARCHAR(45),
            
            -- Status and workflow
            status VARCHAR(20) DEFAULT 'open',
            assigned_to INTEGER REFERENCES enhanced_users(id),
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
    END IF;

    -- Compliance Reports table
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'compliance_reports') THEN
        CREATE TABLE compliance_reports (
            id SERIAL PRIMARY KEY,
            report_id VARCHAR(64) UNIQUE NOT NULL,
            project_id INTEGER REFERENCES enhanced_projects(id),
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
            generated_by INTEGER REFERENCES enhanced_users(id) NOT NULL,
            approved_by INTEGER REFERENCES enhanced_users(id),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP
        );
    END IF;

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

    RAISE NOTICE 'Enhanced security tables created successfully';

END $$;
