-- Data Platform Database Initialization

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create document processing status table
CREATE TABLE IF NOT EXISTS document_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    progress FLOAT DEFAULT 0,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB NOT NULL,
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_document_status_user_id ON document_status(user_id);
CREATE INDEX IF NOT EXISTS idx_document_status_status ON document_status(status);
CREATE INDEX IF NOT EXISTS idx_document_status_created_at ON document_status(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON processing_jobs(job_type);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role, permissions) 
VALUES (
    'admin', 
    'admin@dataplatform.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewA8pQgKzOxcG3Dq', 
    'admin', 
    '["read", "write", "admin"]'
) ON CONFLICT (username) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for auto-updating timestamps
DROP TRIGGER IF EXISTS update_document_status_updated_at ON document_status;
CREATE TRIGGER update_document_status_updated_at 
    BEFORE UPDATE ON document_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initialize Enhanced Security System
-- This will add security tables, RBAC, encryption, compliance, and monitoring features
DO $security_init$
BEGIN
    -- Check if security migration should run
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'organizations') THEN
        RAISE NOTICE 'Initializing Enhanced Security System...';
        
        -- Organizations table
        CREATE TABLE organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255) UNIQUE NOT NULL,
            subscription_tier VARCHAR(50) DEFAULT 'enterprise',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT INTO organizations (name, domain) VALUES ('Default Organization', 'localhost');

        -- Enhanced Users table
        CREATE TABLE enhanced_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            mfa_enabled BOOLEAN DEFAULT FALSE,
            security_clearance VARCHAR(20) DEFAULT 'internal',
            organization_id INTEGER REFERENCES organizations(id) DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT INTO enhanced_users (email, username, full_name, password_hash, security_clearance, mfa_enabled) 
        VALUES ('admin@localhost', 'admin', 'System Administrator', 
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3/4BjL0jSi',
                'top_secret', true);

        -- Enhanced Projects table
        CREATE TABLE enhanced_projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            project_code VARCHAR(20) UNIQUE NOT NULL,
            security_classification VARCHAR(20) DEFAULT 'internal',
            encryption_enabled BOOLEAN DEFAULT TRUE,
            organization_id INTEGER REFERENCES organizations(id) DEFAULT 1,
            created_by INTEGER REFERENCES enhanced_users(id) DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Security tables
        CREATE TABLE audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES enhanced_users(id),
            action VARCHAR(50) NOT NULL,
            details JSONB DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE security_alerts (
            id SERIAL PRIMARY KEY,
            alert_id VARCHAR(64) UNIQUE NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            threat_level VARCHAR(20) NOT NULL,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(20) DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        RAISE NOTICE 'Enhanced Security System initialized successfully';
    END IF;
END $security_init$;
