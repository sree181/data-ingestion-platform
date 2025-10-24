-- Migration: Add Access Control Tables
-- Description: Add tables for IP whitelist, domain restrictions, and access control policies
-- Version: 004
-- Date: 2024-01-15

-- Add access_control_policy column to project_spaces table
ALTER TABLE project_spaces 
ADD COLUMN IF NOT EXISTS access_control_policy JSONB;

-- Create access_logs table
CREATE TABLE IF NOT EXISTS access_logs (
    log_id UUID PRIMARY KEY,
    space_id UUID NOT NULL,
    log_data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_access_logs_space_id 
        FOREIGN KEY (space_id) 
        REFERENCES project_spaces(id) 
        ON DELETE CASCADE
);

-- Create ip_ranges table for reusable IP range definitions
CREATE TABLE IF NOT EXISTS ip_ranges (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ip_address VARCHAR(255) NOT NULL,
    range_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Foreign key constraint
    CONSTRAINT fk_ip_ranges_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create domain_restrictions table for reusable domain definitions
CREATE TABLE IF NOT EXISTS domain_restrictions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    domain VARCHAR(255) NOT NULL,
    domain_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Foreign key constraint
    CONSTRAINT fk_domain_restrictions_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create geographic_restrictions table
CREATE TABLE IF NOT EXISTS geographic_restrictions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    regions JSONB NOT NULL DEFAULT '[]'::jsonb,
    countries JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_allowlist BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Foreign key constraint
    CONSTRAINT fk_geographic_restrictions_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create time_restrictions table
CREATE TABLE IF NOT EXISTS time_restrictions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    restriction_type VARCHAR(50) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    days_of_week JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Foreign key constraint
    CONSTRAINT fk_time_restrictions_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create access_control_rules table
CREATE TABLE IF NOT EXISTS access_control_rules (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100 CHECK (priority >= 1 AND priority <= 1000),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    action VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Foreign key constraint
    CONSTRAINT fk_access_control_rules_created_by 
        FOREIGN KEY (created_by) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_access_logs_space_id 
    ON access_logs(space_id);

CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp 
    ON access_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_access_logs_action 
    ON access_logs((log_data->>'action'));

CREATE INDEX IF NOT EXISTS idx_ip_ranges_created_by 
    ON ip_ranges(created_by);

CREATE INDEX IF NOT EXISTS idx_ip_ranges_is_active 
    ON ip_ranges(is_active);

CREATE INDEX IF NOT EXISTS idx_ip_ranges_range_type 
    ON ip_ranges(range_type);

CREATE INDEX IF NOT EXISTS idx_domain_restrictions_created_by 
    ON domain_restrictions(created_by);

CREATE INDEX IF NOT EXISTS idx_domain_restrictions_is_active 
    ON domain_restrictions(is_active);

CREATE INDEX IF NOT EXISTS idx_domain_restrictions_domain_type 
    ON domain_restrictions(domain_type);

CREATE INDEX IF NOT EXISTS idx_geographic_restrictions_created_by 
    ON geographic_restrictions(created_by);

CREATE INDEX IF NOT EXISTS idx_geographic_restrictions_is_active 
    ON geographic_restrictions(is_active);

CREATE INDEX IF NOT EXISTS idx_time_restrictions_created_by 
    ON time_restrictions(created_by);

CREATE INDEX IF NOT EXISTS idx_time_restrictions_is_active 
    ON time_restrictions(is_active);

CREATE INDEX IF NOT EXISTS idx_time_restrictions_restriction_type 
    ON time_restrictions(restriction_type);

CREATE INDEX IF NOT EXISTS idx_access_control_rules_created_by 
    ON access_control_rules(created_by);

CREATE INDEX IF NOT EXISTS idx_access_control_rules_is_active 
    ON access_control_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_access_control_rules_priority 
    ON access_control_rules(priority);

CREATE INDEX IF NOT EXISTS idx_access_control_rules_rule_type 
    ON access_control_rules(rule_type);

-- Create indexes on JSONB columns for better query performance
CREATE INDEX IF NOT EXISTS idx_access_logs_ip_address 
    ON access_logs ((log_data->>'ip_address'));

CREATE INDEX IF NOT EXISTS idx_access_logs_user_id 
    ON access_logs ((log_data->>'user_id'));

CREATE INDEX IF NOT EXISTS idx_ip_ranges_ip_address 
    ON ip_ranges (ip_address);

CREATE INDEX IF NOT EXISTS idx_domain_restrictions_domain 
    ON domain_restrictions (domain);

CREATE INDEX IF NOT EXISTS idx_geographic_restrictions_regions 
    ON geographic_restrictions USING GIN ((regions));

CREATE INDEX IF NOT EXISTS idx_geographic_restrictions_countries 
    ON geographic_restrictions USING GIN ((countries));

CREATE INDEX IF NOT EXISTS idx_time_restrictions_days_of_week 
    ON time_restrictions USING GIN ((days_of_week));

CREATE INDEX IF NOT EXISTS idx_access_control_rules_conditions 
    ON access_control_rules USING GIN ((conditions));

-- Add comments for documentation
COMMENT ON TABLE access_logs IS 'Stores access control logs and violations';
COMMENT ON TABLE ip_ranges IS 'Stores reusable IP range definitions';
COMMENT ON TABLE domain_restrictions IS 'Stores reusable domain restriction definitions';
COMMENT ON TABLE geographic_restrictions IS 'Stores geographic access restrictions';
COMMENT ON TABLE time_restrictions IS 'Stores time-based access restrictions';
COMMENT ON TABLE access_control_rules IS 'Stores general access control rules';

COMMENT ON COLUMN project_spaces.access_control_policy IS 'JSON configuration for access control policies';
COMMENT ON COLUMN access_logs.log_data IS 'JSON data containing the full access log entry';
COMMENT ON COLUMN ip_ranges.ip_address IS 'IP address, CIDR block, or IP range';
COMMENT ON COLUMN ip_ranges.range_type IS 'Type of IP range: single_ip, cidr_block, ip_range, wildcard';
COMMENT ON COLUMN domain_restrictions.domain IS 'Domain pattern to match';
COMMENT ON COLUMN domain_restrictions.domain_type IS 'Type of domain restriction: email_domain, allowed_domains, blocked_domains, wildcard_domain';
COMMENT ON COLUMN geographic_restrictions.regions IS 'JSON array of geographic regions';
COMMENT ON COLUMN geographic_restrictions.countries IS 'JSON array of country codes (ISO 3166-1 alpha-2)';
COMMENT ON COLUMN time_restrictions.restriction_type IS 'Type of time restriction: business_hours, custom_hours, weekdays_only, weekends_only, maintenance_window';
COMMENT ON COLUMN time_restrictions.start_time IS 'Start time in HH:MM format';
COMMENT ON COLUMN time_restrictions.end_time IS 'End time in HH:MM format';
COMMENT ON COLUMN time_restrictions.days_of_week IS 'JSON array of days (0=Monday, 6=Sunday)';
COMMENT ON COLUMN access_control_rules.rule_type IS 'Type of access control rule: ip_whitelist, ip_blacklist, domain_restriction, geographic_restriction, time_based_restriction';
COMMENT ON COLUMN access_control_rules.action IS 'Action to take: allow, deny, challenge, redirect';
COMMENT ON COLUMN access_control_rules.conditions IS 'JSON object containing rule conditions';
COMMENT ON COLUMN access_control_rules.priority IS 'Rule priority (1-1000, lower = higher priority)';

-- Insert sample access control configurations for existing spaces
-- This is optional and can be removed if not needed
-- UPDATE project_spaces 
-- SET access_control_policy = '{"policy_name": "Default Policy", "description": "Default access control policy", "is_active": true, "ip_whitelist": [], "ip_blacklist": [], "allowed_domains": [], "blocked_domains": [], "geographic_restrictions": [], "time_restrictions": [], "default_action": "allow", "enable_logging": true, "enable_notifications": true}'::jsonb
-- WHERE access_control_policy IS NULL;
