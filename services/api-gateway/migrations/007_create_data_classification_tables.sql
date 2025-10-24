-- Data Classification Management Tables
-- Comprehensive data classification and handling policies

-- Classification rules table
CREATE TABLE IF NOT EXISTS classification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pattern TEXT NOT NULL,
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('regex', 'keyword', 'nlp', 'ml')),
    classification_level VARCHAR(50) NOT NULL CHECK (classification_level IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    data_category VARCHAR(50) NOT NULL CHECK (data_category IN ('personal_data', 'financial_data', 'health_data', 'intellectual_property', 'trade_secrets', 'legal_documents', 'research_data', 'operational_data', 'technical_data', 'marketing_data')),
    sensitivity VARCHAR(50) NOT NULL CHECK (sensitivity IN ('low', 'medium', 'high', 'critical')),
    confidence_threshold DECIMAL(3,2) DEFAULT 0.8 CHECK (confidence_threshold >= 0.0 AND confidence_threshold <= 1.0),
    handling_actions JSONB NOT NULL DEFAULT '[]',
    compliance_requirements JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Classification policies table
CREATE TABLE IF NOT EXISTS classification_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    classification_level VARCHAR(50) NOT NULL CHECK (classification_level IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    data_category VARCHAR(50) NOT NULL CHECK (data_category IN ('personal_data', 'financial_data', 'health_data', 'intellectual_property', 'trade_secrets', 'legal_documents', 'research_data', 'operational_data', 'technical_data', 'marketing_data')),
    sensitivity VARCHAR(50) NOT NULL CHECK (sensitivity IN ('low', 'medium', 'high', 'critical')),
    handling_actions JSONB NOT NULL DEFAULT '[]',
    compliance_requirements JSONB NOT NULL DEFAULT '[]',
    retention_period_days INTEGER,
    access_controls JSONB DEFAULT '{}',
    sharing_restrictions JSONB DEFAULT '{}',
    encryption_required BOOLEAN DEFAULT true,
    audit_required BOOLEAN DEFAULT true,
    backup_required BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data classifications table
CREATE TABLE IF NOT EXISTS data_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) NOT NULL UNIQUE,
    classification_level VARCHAR(50) NOT NULL CHECK (classification_level IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    data_category VARCHAR(50) NOT NULL CHECK (data_category IN ('personal_data', 'financial_data', 'health_data', 'intellectual_property', 'trade_secrets', 'legal_documents', 'research_data', 'operational_data', 'technical_data', 'marketing_data')),
    sensitivity VARCHAR(50) NOT NULL CHECK (sensitivity IN ('low', 'medium', 'high', 'critical')),
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    classification_method VARCHAR(50) NOT NULL CHECK (classification_method IN ('automatic', 'manual', 'rule_based', 'ai_powered', 'policy_based')),
    applied_rules JSONB DEFAULT '[]',
    handling_actions JSONB NOT NULL DEFAULT '[]',
    compliance_requirements JSONB NOT NULL DEFAULT '[]',
    classification_reasoning TEXT NOT NULL,
    classified_by VARCHAR(255) NOT NULL,
    classified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    requires_review BOOLEAN DEFAULT false,
    review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Classification audit logs table
CREATE TABLE IF NOT EXISTS classification_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    old_classification VARCHAR(50) CHECK (old_classification IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    new_classification VARCHAR(50) CHECK (new_classification IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    old_category VARCHAR(50) CHECK (old_category IN ('personal_data', 'financial_data', 'health_data', 'intellectual_property', 'trade_secrets', 'legal_documents', 'research_data', 'operational_data', 'technical_data', 'marketing_data')),
    new_category VARCHAR(50) CHECK (new_category IN ('personal_data', 'financial_data', 'health_data', 'intellectual_property', 'trade_secrets', 'legal_documents', 'research_data', 'operational_data', 'technical_data', 'marketing_data')),
    old_sensitivity VARCHAR(50) CHECK (old_sensitivity IN ('low', 'medium', 'high', 'critical')),
    new_sensitivity VARCHAR(50) CHECK (new_sensitivity IN ('low', 'medium', 'high', 'critical')),
    reason TEXT NOT NULL,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    additional_data JSONB DEFAULT '{}'
);

-- Classification reports table
CREATE TABLE IF NOT EXISTS classification_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    query_params JSONB NOT NULL,
    generated_by VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500),
    file_size BIGINT,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_public BOOLEAN DEFAULT false,
    access_token VARCHAR(255)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_classification_rules_active ON classification_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_classification_rules_priority ON classification_rules(priority);
CREATE INDEX IF NOT EXISTS idx_classification_rules_level ON classification_rules(classification_level);
CREATE INDEX IF NOT EXISTS idx_classification_rules_category ON classification_rules(data_category);

CREATE INDEX IF NOT EXISTS idx_classification_policies_active ON classification_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_classification_policies_level ON classification_policies(classification_level);
CREATE INDEX IF NOT EXISTS idx_classification_policies_category ON classification_policies(data_category);

CREATE INDEX IF NOT EXISTS idx_data_classifications_document_id ON data_classifications(document_id);
CREATE INDEX IF NOT EXISTS idx_data_classifications_level ON data_classifications(classification_level);
CREATE INDEX IF NOT EXISTS idx_data_classifications_category ON data_classifications(data_category);
CREATE INDEX IF NOT EXISTS idx_data_classifications_sensitivity ON data_classifications(sensitivity);
CREATE INDEX IF NOT EXISTS idx_data_classifications_method ON data_classifications(classification_method);
CREATE INDEX IF NOT EXISTS idx_data_classifications_requires_review ON data_classifications(requires_review);
CREATE INDEX IF NOT EXISTS idx_data_classifications_classified_at ON data_classifications(classified_at);

CREATE INDEX IF NOT EXISTS idx_classification_audit_logs_document_id ON classification_audit_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_classification_audit_logs_action ON classification_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_classification_audit_logs_changed_by ON classification_audit_logs(changed_by);
CREATE INDEX IF NOT EXISTS idx_classification_audit_logs_changed_at ON classification_audit_logs(changed_at);

CREATE INDEX IF NOT EXISTS idx_classification_reports_generated_by ON classification_reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_classification_reports_generated_at ON classification_reports(generated_at);
CREATE INDEX IF NOT EXISTS idx_classification_reports_type ON classification_reports(report_type);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_classification_rules_name_fts ON classification_rules USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_classification_policies_name_fts ON classification_policies USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX IF NOT EXISTS idx_classification_audit_logs_reason_fts ON classification_audit_logs USING gin(to_tsvector('english', reason));

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_classification_rules_updated_at 
    BEFORE UPDATE ON classification_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classification_policies_updated_at 
    BEFORE UPDATE ON classification_policies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_classifications_updated_at 
    BEFORE UPDATE ON data_classifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default classification rules
INSERT INTO classification_rules (name, description, pattern, pattern_type, classification_level, data_category, sensitivity, confidence_threshold, handling_actions, compliance_requirements, created_by) VALUES
('Personal Data Detection', 'Detect personal data patterns', '\b(?:ssn|social security|credit card|phone|email|address|name|birth|age)\b', 'regex', 'confidential', 'personal_data', 'high', 0.8, '["encrypt", "access_control", "audit_log"]', '["gdpr", "ccpa"]', 'system'),
('Financial Data Detection', 'Detect financial data patterns', '\b(?:account|balance|transaction|payment|invoice|receipt|tax|financial)\b', 'regex', 'confidential', 'financial_data', 'high', 0.8, '["encrypt", "access_control", "audit_log"]', '["sox", "pci_dss"]', 'system'),
('Health Data Detection', 'Detect health data patterns', '\b(?:medical|health|patient|diagnosis|treatment|medication|hospital|clinic)\b', 'regex', 'restricted', 'health_data', 'critical', 0.9, '["encrypt", "access_control", "audit_log", "anonymize"]', '["hipaa"]', 'system'),
('Intellectual Property Detection', 'Detect intellectual property patterns', '\b(?:patent|copyright|trademark|proprietary|confidential|trade secret|invention)\b', 'regex', 'restricted', 'intellectual_property', 'critical', 0.9, '["encrypt", "access_control", "audit_log", "sharing_restricted"]', '[]', 'system'),
('Public Information Detection', 'Detect public information patterns', '\b(?:public|announcement|news|press release|marketing|advertisement)\b', 'regex', 'public', 'marketing_data', 'low', 0.7, '["audit_log"]', '[]', 'system');

-- Insert default classification policies
INSERT INTO classification_policies (name, description, classification_level, data_category, sensitivity, handling_actions, compliance_requirements, retention_period_days, encryption_required, audit_required, backup_required, created_by) VALUES
('Public Data Policy', 'Policy for public data', 'public', 'operational_data', 'low', '["audit_log"]', '[]', 365, false, true, false, 'system'),
('Internal Data Policy', 'Policy for internal data', 'internal', 'operational_data', 'medium', '["access_control", "audit_log"]', '[]', 1095, false, true, true, 'system'),
('Confidential Data Policy', 'Policy for confidential data', 'confidential', 'personal_data', 'high', '["encrypt", "access_control", "audit_log", "backup_required"]', '["gdpr"]', 2555, true, true, true, 'system'),
('Restricted Data Policy', 'Policy for restricted data', 'restricted', 'health_data', 'critical', '["encrypt", "access_control", "audit_log", "backup_required", "sharing_restricted"]', '["hipaa"]', 2555, true, true, true, 'system'),
('Top Secret Data Policy', 'Policy for top secret data', 'top_secret', 'trade_secrets', 'critical', '["encrypt", "access_control", "audit_log", "backup_required", "sharing_restricted", "delete_after_use"]', '[]', 365, true, true, true, 'system');

-- Create views for common queries
CREATE OR REPLACE VIEW classification_summary AS
SELECT 
    classification_level,
    data_category,
    sensitivity,
    COUNT(*) as document_count,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN requires_review = true THEN 1 END) as requires_review_count
FROM data_classifications
GROUP BY classification_level, data_category, sensitivity
ORDER BY classification_level, data_category, sensitivity;

CREATE OR REPLACE VIEW classification_compliance_summary AS
SELECT 
    compliance_requirement,
    COUNT(*) as document_count
FROM data_classifications,
     jsonb_array_elements_text(compliance_requirements) as compliance_requirement
GROUP BY compliance_requirement
ORDER BY document_count DESC;

CREATE OR REPLACE VIEW recent_classification_activity AS
SELECT 
    dc.document_id,
    dc.classification_level,
    dc.data_category,
    dc.sensitivity,
    dc.classified_by,
    dc.classified_at,
    dc.requires_review
FROM data_classifications dc
ORDER BY dc.classified_at DESC
LIMIT 100;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON classification_rules TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON classification_policies TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_classifications TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON classification_audit_logs TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON classification_reports TO your_app_user;
-- GRANT SELECT ON classification_summary TO your_app_user;
-- GRANT SELECT ON classification_compliance_summary TO your_app_user;
-- GRANT SELECT ON recent_classification_activity TO your_app_user;
