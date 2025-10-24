-- Migration: Add Compliance Framework Tables
-- Description: Add tables for compliance framework configuration, validation, and reporting
-- Version: 003
-- Date: 2024-01-15

-- Add compliance_config column to project_spaces table
ALTER TABLE project_spaces 
ADD COLUMN IF NOT EXISTS compliance_config JSONB;

-- Create compliance_reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    report_id UUID PRIMARY KEY,
    space_id UUID NOT NULL,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_compliance_reports_space_id 
        FOREIGN KEY (space_id) 
        REFERENCES project_spaces(id) 
        ON DELETE CASCADE
);

-- Create compliance_audits table
CREATE TABLE IF NOT EXISTS compliance_audits (
    audit_id UUID PRIMARY KEY,
    space_id UUID NOT NULL,
    audit_data JSONB NOT NULL,
    auditor VARCHAR(255) NOT NULL,
    audit_type VARCHAR(50) NOT NULL DEFAULT 'internal',
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_compliance_audits_space_id 
        FOREIGN KEY (space_id) 
        REFERENCES project_spaces(id) 
        ON DELETE CASCADE
);

-- Create compliance_validations table
CREATE TABLE IF NOT EXISTS compliance_validations (
    validation_id UUID PRIMARY KEY,
    space_id UUID NOT NULL,
    requirement_id VARCHAR(100) NOT NULL,
    validation_data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    score DECIMAL(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    validated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_compliance_validations_space_id 
        FOREIGN KEY (space_id) 
        REFERENCES project_spaces(id) 
        ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_compliance_reports_space_id 
    ON compliance_reports(space_id);

CREATE INDEX IF NOT EXISTS idx_compliance_reports_generated_at 
    ON compliance_reports(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_compliance_audits_space_id 
    ON compliance_audits(space_id);

CREATE INDEX IF NOT EXISTS idx_compliance_audits_status 
    ON compliance_audits(status);

CREATE INDEX IF NOT EXISTS idx_compliance_audits_started_at 
    ON compliance_audits(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_compliance_validations_space_id 
    ON compliance_validations(space_id);

CREATE INDEX IF NOT EXISTS idx_compliance_validations_requirement_id 
    ON compliance_validations(requirement_id);

CREATE INDEX IF NOT EXISTS idx_compliance_validations_validated_at 
    ON compliance_validations(validated_at DESC);

-- Create indexes on JSONB columns for better query performance
CREATE INDEX IF NOT EXISTS idx_compliance_reports_frameworks 
    ON compliance_reports USING GIN ((report_data->'frameworks'));

CREATE INDEX IF NOT EXISTS idx_compliance_reports_overall_score 
    ON compliance_reports ((report_data->>'overall_score'));

CREATE INDEX IF NOT EXISTS idx_compliance_audits_frameworks 
    ON compliance_audits USING GIN ((audit_data->'frameworks'));

CREATE INDEX IF NOT EXISTS idx_compliance_audits_audit_type 
    ON compliance_audits ((audit_data->>'audit_type'));

-- Add comments for documentation
COMMENT ON TABLE compliance_reports IS 'Stores compliance reports generated for project spaces';
COMMENT ON TABLE compliance_audits IS 'Stores compliance audit records and findings';
COMMENT ON TABLE compliance_validations IS 'Stores individual compliance requirement validations';

COMMENT ON COLUMN project_spaces.compliance_config IS 'JSON configuration for compliance frameworks';
COMMENT ON COLUMN compliance_reports.report_data IS 'JSON data containing the full compliance report';
COMMENT ON COLUMN compliance_audits.audit_data IS 'JSON data containing audit details and findings';
COMMENT ON COLUMN compliance_validations.validation_data IS 'JSON data containing validation details and evidence';

-- Insert sample compliance configurations for existing spaces
-- This is optional and can be removed if not needed
-- UPDATE project_spaces 
-- SET compliance_config = '{"frameworks": ["GDPR"], "data_categories": ["personal_data"], "retention_policies": {"personal_data": "medium_term"}, "requirements": [], "custom_requirements": [], "audit_schedule": {"frequency": "quarterly"}, "reporting_config": {"format": "json", "auto_generate": true}}'::jsonb
-- WHERE compliance_config IS NULL;
