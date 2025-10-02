-- Add security fields to existing project_spaces table
-- This migration adds the security fields that were missing

-- Add security fields to project_spaces table
ALTER TABLE project_spaces 
ADD COLUMN IF NOT EXISTS security_classification VARCHAR(20) DEFAULT 'internal',
ADD COLUMN IF NOT EXISTS encryption_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS requires_mfa BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS compliance_frameworks JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS ip_whitelist JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS data_retention_days INTEGER DEFAULT 365,
ADD COLUMN IF NOT EXISTS allowed_domains JSONB DEFAULT '[]';

-- Update existing spaces with default security values
UPDATE project_spaces 
SET 
    security_classification = 'internal',
    encryption_enabled = TRUE,
    requires_mfa = FALSE,
    compliance_frameworks = '["GDPR", "SOX"]',
    ip_whitelist = '[]',
    data_retention_days = 365,
    allowed_domains = '["company.com"]'
WHERE security_classification IS NULL;