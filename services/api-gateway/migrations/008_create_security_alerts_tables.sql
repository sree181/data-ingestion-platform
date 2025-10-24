-- Security Alerts and Notifications Tables
-- Comprehensive security alerting and notification systems

-- Security alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    category VARCHAR(50) NOT NULL CHECK (category IN ('authentication', 'authorization', 'data_access', 'data_breach', 'system_security', 'network_security', 'compliance', 'malware', 'intrusion', 'privilege_escalation', 'data_exfiltration', 'suspicious_activity', 'policy_violation', 'configuration_change', 'vulnerability')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'investigating', 'resolved', 'suppressed', 'false_positive')),
    source VARCHAR(50) NOT NULL CHECK (source IN ('siem', 'ids_ips', 'firewall', 'antivirus', 'dlp', 'iam', 'audit_log', 'manual', 'api', 'scheduled_scan', 'real_time_monitoring')),
    source_id VARCHAR(255),
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_name VARCHAR(500),
    event_data JSONB DEFAULT '{}',
    correlation_id VARCHAR(255),
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution_notes TEXT,
    escalation_level VARCHAR(20) DEFAULT 'level_1' CHECK (escalation_level IN ('level_1', 'level_2', 'level_3', 'level_4', 'executive')),
    escalation_history JSONB DEFAULT '[]',
    false_positive BOOLEAN DEFAULT false,
    suppression_until TIMESTAMP WITH TIME ZONE,
    risk_score DECIMAL(3,1) DEFAULT 0.0 CHECK (risk_score >= 0.0 AND risk_score <= 10.0),
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    condition TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    category VARCHAR(50) NOT NULL CHECK (category IN ('authentication', 'authorization', 'data_access', 'data_breach', 'system_security', 'network_security', 'compliance', 'malware', 'intrusion', 'privilege_escalation', 'data_exfiltration', 'suspicious_activity', 'policy_violation', 'configuration_change', 'vulnerability')),
    source VARCHAR(50) NOT NULL CHECK (source IN ('siem', 'ids_ips', 'firewall', 'antivirus', 'dlp', 'iam', 'audit_log', 'manual', 'api', 'scheduled_scan', 'real_time_monitoring')),
    enabled BOOLEAN DEFAULT true,
    threshold DECIMAL(15,2),
    time_window INTEGER, -- in minutes
    aggregation VARCHAR(20), -- count, sum, avg, max, min
    notification_channels JSONB DEFAULT '[]',
    escalation_enabled BOOLEAN DEFAULT true,
    escalation_delay_minutes INTEGER DEFAULT 30,
    escalation_levels JSONB DEFAULT '[]',
    suppression_enabled BOOLEAN DEFAULT true,
    suppression_duration_minutes INTEGER DEFAULT 60,
    tags JSONB DEFAULT '[]',
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0
);

-- Notification templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'slack', 'teams', 'webhook', 'dashboard', 'mobile_app', 'pager_duty')),
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT true,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification subscriptions table
CREATE TABLE IF NOT EXISTS notification_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_phone VARCHAR(20),
    channels JSONB NOT NULL DEFAULT '[]',
    severity_filter JSONB DEFAULT '[]',
    category_filter JSONB DEFAULT '[]',
    source_filter JSONB DEFAULT '[]',
    time_filter JSONB,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert correlations table
CREATE TABLE IF NOT EXISTS alert_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id VARCHAR(255) NOT NULL UNIQUE,
    alert_ids JSONB NOT NULL DEFAULT '[]',
    correlation_type VARCHAR(100) NOT NULL,
    correlation_score DECIMAL(3,2) DEFAULT 0.0 CHECK (correlation_score >= 0.0 AND correlation_score <= 1.0),
    pattern_description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert suppressions table
CREATE TABLE IF NOT EXISTS alert_suppressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(255),
    condition TEXT NOT NULL,
    reason TEXT NOT NULL,
    suppressed_by VARCHAR(255) NOT NULL,
    suppressed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_security_alerts_category ON security_alerts(category);
CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(status);
CREATE INDEX IF NOT EXISTS idx_security_alerts_source ON security_alerts(source);
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_ip_address ON security_alerts(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resource_type ON security_alerts(resource_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resource_id ON security_alerts(resource_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_correlation_id ON security_alerts(correlation_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_security_alerts_escalation_level ON security_alerts(escalation_level);
CREATE INDEX IF NOT EXISTS idx_security_alerts_risk_score ON security_alerts(risk_score);
CREATE INDEX IF NOT EXISTS idx_security_alerts_false_positive ON security_alerts(false_positive);

CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);
CREATE INDEX IF NOT EXISTS idx_alert_rules_category ON alert_rules(category);
CREATE INDEX IF NOT EXISTS idx_alert_rules_source ON alert_rules(source);
CREATE INDEX IF NOT EXISTS idx_alert_rules_created_by ON alert_rules(created_by);
CREATE INDEX IF NOT EXISTS idx_alert_rules_last_triggered ON alert_rules(last_triggered);

CREATE INDEX IF NOT EXISTS idx_notification_templates_channel ON notification_templates(channel);
CREATE INDEX IF NOT EXISTS idx_notification_templates_enabled ON notification_templates(enabled);
CREATE INDEX IF NOT EXISTS idx_notification_templates_created_by ON notification_templates(created_by);

CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_user_id ON notification_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_user_email ON notification_subscriptions(user_email);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_enabled ON notification_subscriptions(enabled);

CREATE INDEX IF NOT EXISTS idx_alert_correlations_correlation_id ON alert_correlations(correlation_id);
CREATE INDEX IF NOT EXISTS idx_alert_correlations_correlation_type ON alert_correlations(correlation_type);
CREATE INDEX IF NOT EXISTS idx_alert_correlations_correlation_score ON alert_correlations(correlation_score);

CREATE INDEX IF NOT EXISTS idx_alert_suppressions_rule_id ON alert_suppressions(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_suppressions_suppressed_by ON alert_suppressions(suppressed_by);
CREATE INDEX IF NOT EXISTS idx_alert_suppressions_is_active ON alert_suppressions(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_suppressions_expires_at ON alert_suppressions(expires_at);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_security_alerts_title_fts ON security_alerts USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_alert_rules_name_fts ON alert_rules USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_notification_templates_name_fts ON notification_templates USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_security_alerts_updated_at 
    BEFORE UPDATE ON security_alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_rules_updated_at 
    BEFORE UPDATE ON alert_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_templates_updated_at 
    BEFORE UPDATE ON notification_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_subscriptions_updated_at 
    BEFORE UPDATE ON notification_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_correlations_updated_at 
    BEFORE UPDATE ON alert_correlations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default alert rules
INSERT INTO alert_rules (name, description, condition, severity, category, source, threshold, time_window, aggregation, notification_channels, escalation_levels, created_by) VALUES
('Multiple Failed Login Attempts', 'Alert when multiple failed login attempts detected', 'failed_login_count > 5', 'high', 'authentication', 'iam', 5, 15, 'count', '["email", "slack"]', '["level_2", "level_3"]', 'system'),
('Unauthorized Data Access', 'Alert when unauthorized data access is attempted', 'access_denied = true AND resource_type = sensitive', 'critical', 'data_access', 'audit_log', NULL, NULL, NULL, '["email", "slack", "sms"]', '["level_2", "level_3", "executive"]', 'system'),
('Suspicious File Download', 'Alert when suspicious file download pattern detected', 'download_size > 100000000 AND download_count > 10', 'medium', 'suspicious_activity', 'dlp', 100000000, 60, 'sum', '["email"]', '[]', 'system'),
('Privilege Escalation Attempt', 'Alert when privilege escalation is attempted', 'privilege_escalation = true', 'critical', 'privilege_escalation', 'iam', NULL, NULL, NULL, '["email", "slack", "sms"]', '["level_2", "level_3", "executive"]', 'system'),
('Data Exfiltration Pattern', 'Alert when data exfiltration pattern detected', 'data_export_size > 50000000 AND export_frequency > 5', 'critical', 'data_exfiltration', 'dlp', 50000000, 120, 'sum', '["email", "slack", "sms"]', '["level_2", "level_3", "executive"]', 'system');

-- Insert default notification templates
INSERT INTO notification_templates (name, description, channel, subject_template, body_template, variables, created_by) VALUES
('Critical Alert Email', 'Email template for critical alerts', 'email', '🚨 CRITICAL SECURITY ALERT: {alert_title}', '<h2>Critical Security Alert</h2><p><strong>Alert:</strong> {alert_title}</p><p><strong>Description:</strong> {alert_description}</p><p><strong>Severity:</strong> {alert_severity}</p><p><strong>Category:</strong> {alert_category}</p><p><strong>Source:</strong> {alert_source}</p><p><strong>Time:</strong> {alert_time}</p><p><strong>Risk Score:</strong> {risk_score}/10</p><p><strong>IP Address:</strong> {ip_address}</p><p><strong>User:</strong> {user_id}</p><hr><p><em>This is an automated security alert. Please investigate immediately.</em></p>', '["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score", "ip_address", "user_id"]', 'system'),
('High Alert Slack', 'Slack template for high severity alerts', 'slack', NULL, '🚨 *HIGH SECURITY ALERT*\n*Alert:* {alert_title}\n*Description:* {alert_description}\n*Severity:* {alert_severity}\n*Category:* {alert_category}\n*Source:* {alert_source}\n*Time:* {alert_time}\n*Risk Score:* {risk_score}/10\n*IP Address:* {ip_address}\n*User:* {user_id}', '["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score", "ip_address", "user_id"]', 'system'),
('Medium Alert Teams', 'Teams template for medium severity alerts', 'teams', NULL, '<h3>⚠️ Medium Security Alert</h3><p><strong>Alert:</strong> {alert_title}</p><p><strong>Description:</strong> {alert_description}</p><p><strong>Severity:</strong> {alert_severity}</p><p><strong>Category:</strong> {alert_category}</p><p><strong>Source:</strong> {alert_source}</p><p><strong>Time:</strong> {alert_time}</p><p><strong>Risk Score:</strong> {risk_score}/10</p>', '["alert_title", "alert_description", "alert_severity", "alert_category", "alert_source", "alert_time", "risk_score"]', 'system');

-- Insert default notification subscriptions
INSERT INTO notification_subscriptions (user_id, user_email, channels, severity_filter, category_filter) VALUES
('admin@company.com', 'admin@company.com', '["email", "slack", "sms"]', '["high", "critical"]', '["authentication", "data_access", "data_breach"]'),
('security@company.com', 'security@company.com', '["email", "slack"]', '["medium", "high", "critical"]', '[]'),
('compliance@company.com', 'compliance@company.com', '["email"]', '["high", "critical"]', '["compliance", "policy_violation"]');

-- Create views for common queries
CREATE OR REPLACE VIEW alert_summary AS
SELECT 
    severity,
    category,
    status,
    COUNT(*) as alert_count,
    AVG(risk_score) as avg_risk_score,
    AVG(confidence_score) as avg_confidence_score,
    COUNT(CASE WHEN false_positive = true THEN 1 END) as false_positive_count
FROM security_alerts
GROUP BY severity, category, status
ORDER BY severity, category, status;

CREATE OR REPLACE VIEW recent_alerts AS
SELECT 
    id,
    title,
    severity,
    category,
    status,
    source,
    user_id,
    ip_address,
    created_at,
    risk_score
FROM security_alerts
ORDER BY created_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW alert_trends AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    severity,
    COUNT(*) as alert_count
FROM security_alerts
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), severity
ORDER BY hour DESC, severity;

CREATE OR REPLACE VIEW top_alert_sources AS
SELECT 
    source,
    COUNT(*) as alert_count,
    AVG(risk_score) as avg_risk_score,
    COUNT(CASE WHEN false_positive = true THEN 1 END) as false_positive_count
FROM security_alerts
GROUP BY source
ORDER BY alert_count DESC;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON security_alerts TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON alert_rules TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON notification_templates TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON notification_subscriptions TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON alert_correlations TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON alert_suppressions TO your_app_user;
-- GRANT SELECT ON alert_summary TO your_app_user;
-- GRANT SELECT ON recent_alerts TO your_app_user;
-- GRANT SELECT ON alert_trends TO your_app_user;
-- GRANT SELECT ON top_alert_sources TO your_app_user;
