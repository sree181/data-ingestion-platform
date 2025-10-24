-- Enhanced Audit Logging Tables - Working with existing structure
-- This migration enhances the existing audit_logs table and adds new tables

-- First, let's create a new enhanced audit_logs table with a different name
CREATE TABLE IF NOT EXISTS enhanced_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- User and session information
    user_id VARCHAR(255),
    username VARCHAR(255),
    user_email VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Event details
    event_description TEXT NOT NULL,
    event_data JSONB,
    context JSONB,
    
    -- Resource information
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    
    -- Project space context
    space_id VARCHAR(255),
    space_name VARCHAR(255),
    
    -- Compliance and security
    compliance_framework VARCHAR(100),
    risk_score DECIMAL(3,1) CHECK (risk_score >= 0.0 AND risk_score <= 10.0),
    requires_review BOOLEAN DEFAULT FALSE,
    
    -- System information
    service_name VARCHAR(100) DEFAULT 'api-gateway',
    version VARCHAR(20) DEFAULT '1.0.0',
    environment VARCHAR(50) DEFAULT 'production',
    
    -- Metadata
    tags TEXT[],
    retention_days INTEGER,
    archived BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for enhanced_audit_logs
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_timestamp ON enhanced_audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_event_type ON enhanced_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_category ON enhanced_audit_logs(category);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_severity ON enhanced_audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_user_id ON enhanced_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_space_id ON enhanced_audit_logs(space_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_resource_type ON enhanced_audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_resource_id ON enhanced_audit_logs(resource_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_requires_review ON enhanced_audit_logs(requires_review);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_risk_score ON enhanced_audit_logs(risk_score);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_compliance_framework ON enhanced_audit_logs(compliance_framework);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_archived ON enhanced_audit_logs(archived);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_created_at ON enhanced_audit_logs(created_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_user_timestamp ON enhanced_audit_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_space_timestamp ON enhanced_audit_logs(space_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_type_timestamp ON enhanced_audit_logs(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_severity_timestamp ON enhanced_audit_logs(severity, timestamp);
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_review_timestamp ON enhanced_audit_logs(requires_review, timestamp);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_enhanced_audit_logs_search ON enhanced_audit_logs USING gin(to_tsvector('english', event_description || ' ' || COALESCE(username, '') || ' ' || COALESCE(resource_name, '')));

-- Audit retention policies table
CREATE TABLE IF NOT EXISTS audit_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    event_types TEXT[] NOT NULL,
    categories TEXT[] NOT NULL,
    retention_days INTEGER NOT NULL CHECK (retention_days >= 1 AND retention_days <= 3650),
    archive_after_days INTEGER CHECK (archive_after_days >= 1 AND archive_after_days <= 3650),
    delete_after_days INTEGER CHECK (delete_after_days >= 1 AND delete_after_days <= 3650),
    compress_after_days INTEGER CHECK (compress_after_days >= 1 AND compress_after_days <= 3650),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit_retention_policies
CREATE INDEX IF NOT EXISTS idx_audit_retention_policies_name ON audit_retention_policies(policy_name);
CREATE INDEX IF NOT EXISTS idx_audit_retention_policies_active ON audit_retention_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_audit_retention_policies_created_by ON audit_retention_policies(created_by);

-- Audit alerts table
CREATE TABLE IF NOT EXISTS audit_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    event_types TEXT[] NOT NULL,
    conditions JSONB NOT NULL,
    threshold INTEGER,
    time_window_minutes INTEGER,
    severity VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notification_channels TEXT[],
    escalation_rules JSONB,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit_alerts
CREATE INDEX IF NOT EXISTS idx_audit_alerts_name ON audit_alerts(alert_name);
CREATE INDEX IF NOT EXISTS idx_audit_alerts_active ON audit_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_audit_alerts_severity ON audit_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_audit_alerts_created_by ON audit_alerts(created_by);

-- Audit exports table
CREATE TABLE IF NOT EXISTS audit_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_id UUID UNIQUE NOT NULL,
    query_params JSONB NOT NULL,
    export_format VARCHAR(20) NOT NULL CHECK (export_format IN ('json', 'csv', 'excel', 'pdf')),
    include_context BOOLEAN DEFAULT TRUE,
    include_event_data BOOLEAN DEFAULT TRUE,
    compression BOOLEAN DEFAULT FALSE,
    password_protected BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    file_path VARCHAR(500),
    file_size BIGINT,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for audit_exports
CREATE INDEX IF NOT EXISTS idx_audit_exports_export_id ON audit_exports(export_id);
CREATE INDEX IF NOT EXISTS idx_audit_exports_status ON audit_exports(status);
CREATE INDEX IF NOT EXISTS idx_audit_exports_created_by ON audit_exports(created_by);
CREATE INDEX IF NOT EXISTS idx_audit_exports_created_at ON audit_exports(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_exports_expires_at ON audit_exports(expires_at);

-- Audit log cleanup function
CREATE OR REPLACE FUNCTION cleanup_enhanced_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    policy_record RECORD;
BEGIN
    -- Process each retention policy
    FOR policy_record IN 
        SELECT * FROM audit_retention_policies WHERE is_active = TRUE
    LOOP
        -- Delete logs based on retention policy
        IF policy_record.delete_after_days IS NOT NULL THEN
            DELETE FROM enhanced_audit_logs 
            WHERE event_type = ANY(policy_record.event_types)
            AND category = ANY(policy_record.categories)
            AND created_at < NOW() - INTERVAL '1 day' * policy_record.delete_after_days;
            
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
        END IF;
        
        -- Archive logs based on policy
        IF policy_record.archive_after_days IS NOT NULL THEN
            UPDATE enhanced_audit_logs 
            SET archived = TRUE
            WHERE event_type = ANY(policy_record.event_types)
            AND category = ANY(policy_record.categories)
            AND archived = FALSE
            AND created_at < NOW() - INTERVAL '1 day' * policy_record.archive_after_days;
        END IF;
    END LOOP;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Audit log statistics function
CREATE OR REPLACE FUNCTION get_enhanced_audit_log_stats(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_space_id VARCHAR(255) DEFAULT NULL
)
RETURNS TABLE(
    total_events BIGINT,
    events_by_type JSONB,
    events_by_category JSONB,
    events_by_severity JSONB,
    high_risk_events BIGINT,
    events_requiring_review BIGINT
) AS $$
DECLARE
    where_clause TEXT := '1=1';
    params TEXT[] := '{}';
BEGIN
    -- Build WHERE clause
    IF p_start_date IS NOT NULL THEN
        where_clause := where_clause || ' AND timestamp >= $1';
        params := params || p_start_date::TEXT;
    END IF;
    
    IF p_end_date IS NOT NULL THEN
        where_clause := where_clause || ' AND timestamp <= $2';
        params := params || p_end_date::TEXT;
    END IF;
    
    IF p_space_id IS NOT NULL THEN
        where_clause := where_clause || ' AND space_id = $3';
        params := params || p_space_id;
    END IF;
    
    -- Return statistics
    RETURN QUERY EXECUTE format('
        SELECT 
            COUNT(*) as total_events,
            jsonb_object_agg(event_type, type_count) as events_by_type,
            jsonb_object_agg(category, category_count) as events_by_category,
            jsonb_object_agg(severity, severity_count) as events_by_severity,
            COUNT(*) FILTER (WHERE risk_score >= 7.0) as high_risk_events,
            COUNT(*) FILTER (WHERE requires_review = TRUE) as events_requiring_review
        FROM (
            SELECT 
                event_type,
                category,
                severity,
                COUNT(*) as type_count,
                COUNT(*) as category_count,
                COUNT(*) as severity_count
            FROM enhanced_audit_logs 
            WHERE %s
            GROUP BY event_type, category, severity
        ) stats
    ', where_clause);
END;
$$ LANGUAGE plpgsql;

-- Audit log search function
CREATE OR REPLACE FUNCTION search_enhanced_audit_logs(
    p_search_text TEXT DEFAULT NULL,
    p_event_types TEXT[] DEFAULT NULL,
    p_categories TEXT[] DEFAULT NULL,
    p_severities TEXT[] DEFAULT NULL,
    p_user_id VARCHAR(255) DEFAULT NULL,
    p_space_id VARCHAR(255) DEFAULT NULL,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    id UUID,
    event_type VARCHAR(50),
    category VARCHAR(50),
    severity VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR(255),
    username VARCHAR(255),
    user_email VARCHAR(255),
    session_id VARCHAR(255),
    space_id VARCHAR(255),
    space_name VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    event_description TEXT,
    event_data JSONB,
    context JSONB,
    compliance_framework VARCHAR(100),
    risk_score DECIMAL(3,1),
    requires_review BOOLEAN,
    service_name VARCHAR(100),
    version VARCHAR(20),
    environment VARCHAR(50),
    tags TEXT[],
    retention_days INTEGER,
    archived BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    where_clause TEXT := '1=1';
    params TEXT[] := '{}';
    param_count INTEGER := 0;
BEGIN
    -- Build WHERE clause dynamically
    IF p_search_text IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND to_tsvector(''english'', event_description || '' '' || COALESCE(username, '''') || '' '' || COALESCE(resource_name, '''')) @@ plainto_tsquery(''english'', $' || param_count || ')';
        params := params || p_search_text;
    END IF;
    
    IF p_event_types IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND event_type = ANY($' || param_count || ')';
        params := params || array_to_string(p_event_types, ',');
    END IF;
    
    IF p_categories IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND category = ANY($' || param_count || ')';
        params := params || array_to_string(p_categories, ',');
    END IF;
    
    IF p_severities IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND severity = ANY($' || param_count || ')';
        params := params || array_to_string(p_severities, ',');
    END IF;
    
    IF p_user_id IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND user_id = $' || param_count;
        params := params || p_user_id;
    END IF;
    
    IF p_space_id IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND space_id = $' || param_count;
        params := params || p_space_id;
    END IF;
    
    IF p_start_date IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND timestamp >= $' || param_count;
        params := params || p_start_date::TEXT;
    END IF;
    
    IF p_end_date IS NOT NULL THEN
        param_count := param_count + 1;
        where_clause := where_clause || ' AND timestamp <= $' || param_count;
        params := params || p_end_date::TEXT;
    END IF;
    
    -- Add limit and offset
    param_count := param_count + 1;
    where_clause := where_clause || ' LIMIT $' || param_count;
    params := params || p_limit::TEXT;
    
    param_count := param_count + 1;
    where_clause := where_clause || ' OFFSET $' || param_count;
    params := params || p_offset::TEXT;
    
    -- Execute query
    RETURN QUERY EXECUTE format('
        SELECT * FROM enhanced_audit_logs 
        WHERE %s
        ORDER BY timestamp DESC
    ', where_clause) USING params;
END;
$$ LANGUAGE plpgsql;

-- Create default retention policies
INSERT INTO audit_retention_policies (policy_name, description, event_types, categories, retention_days, archive_after_days, delete_after_days, is_active, created_by) VALUES
('default_security_events', 'Default retention for security events', ARRAY['login_failure', 'unauthorized_access', 'data_breach_attempt', 'malware_detected'], ARRAY['security'], 2555, 365, 2555, TRUE, 'system'),
('default_authentication_events', 'Default retention for authentication events', ARRAY['login_success', 'login_failure', 'logout', 'mfa_setup', 'mfa_verify', 'mfa_failure'], ARRAY['authentication'], 365, 90, 365, TRUE, 'system'),
('default_data_access_events', 'Default retention for data access events', ARRAY['document_view', 'document_download', 'document_upload', 'document_delete', 'document_modify'], ARRAY['data_access'], 90, 30, 90, TRUE, 'system'),
('default_system_events', 'Default retention for system events', ARRAY['service_start', 'service_stop', 'service_error', 'system_error'], ARRAY['system'], 30, 7, 30, TRUE, 'system'),
('default_compliance_events', 'Default retention for compliance events', ARRAY['gdpr_data_request', 'gdpr_data_deletion', 'hipaa_access_log', 'sox_audit_event'], ARRAY['compliance'], 2555, 365, 2555, TRUE, 'system');

-- Create default alerts
INSERT INTO audit_alerts (alert_name, description, event_types, conditions, threshold, time_window_minutes, severity, is_active, notification_channels, created_by) VALUES
('high_risk_events', 'Alert for high-risk security events', ARRAY['unauthorized_access', 'data_breach_attempt', 'malware_detected'], '{"min_risk_score": 8.0}', 1, 5, 'critical', TRUE, ARRAY['email', 'slack'], 'system'),
('brute_force_attempts', 'Alert for brute force login attempts', ARRAY['login_failure'], '{"min_risk_score": 5.0}', 5, 10, 'high', TRUE, ARRAY['email'], 'system'),
('suspicious_activity', 'Alert for suspicious user activity', ARRAY['suspicious_activity'], '{"min_risk_score": 7.0}', 1, 5, 'high', TRUE, ARRAY['email', 'slack'], 'system'),
('data_export_events', 'Alert for data export activities', ARRAY['data_export'], '{"min_risk_score": 3.0}', 1, 60, 'medium', TRUE, ARRAY['email'], 'system'),
('admin_operations', 'Alert for administrative operations', ARRAY['user_created', 'user_deleted', 'policy_created', 'policy_deleted'], '{"min_risk_score": 5.0}', 1, 30, 'medium', TRUE, ARRAY['email'], 'system');

-- Add comments
COMMENT ON TABLE enhanced_audit_logs IS 'Enhanced audit log for comprehensive security event tracking';
COMMENT ON TABLE audit_retention_policies IS 'Policies for audit log retention and archival';
COMMENT ON TABLE audit_alerts IS 'Alert configurations for audit events';
COMMENT ON TABLE audit_exports IS 'Audit log export requests and results';

COMMENT ON COLUMN enhanced_audit_logs.risk_score IS 'Risk score from 0.0 to 10.0';
COMMENT ON COLUMN enhanced_audit_logs.requires_review IS 'Whether the event requires manual review';
COMMENT ON COLUMN enhanced_audit_logs.archived IS 'Whether the log has been archived';
COMMENT ON COLUMN enhanced_audit_logs.event_data IS 'Additional event-specific data in JSON format';
COMMENT ON COLUMN enhanced_audit_logs.context IS 'Request context including IP, user agent, etc.';
