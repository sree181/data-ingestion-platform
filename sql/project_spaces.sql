-- Project Spaces Database Schema
-- This extends the existing database with Virtual Project Spaces functionality

-- Create project_spaces table
CREATE TABLE IF NOT EXISTS project_spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#1976d2', -- Hex color for UI theming
    icon VARCHAR(50) DEFAULT 'folder', -- Icon name for UI
    settings JSONB DEFAULT '{}', -- Space-specific settings
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Security fields
    security_classification VARCHAR(20) DEFAULT 'internal',
    encryption_enabled BOOLEAN DEFAULT TRUE,
    requires_mfa BOOLEAN DEFAULT FALSE,
    compliance_frameworks JSONB DEFAULT '[]',
    ip_whitelist JSONB DEFAULT '[]',
    data_retention_days INTEGER DEFAULT 365,
    allowed_domains JSONB DEFAULT '[]',
    
    UNIQUE(name, created_by) -- Prevent duplicate space names per user
);

-- Create space_members table for access control
CREATE TABLE IF NOT EXISTS space_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES project_spaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member, viewer
    permissions JSONB DEFAULT '["read"]', -- read, write, admin, delete
    added_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(space_id, user_id) -- One membership per user per space
);

-- Create space_documents table to associate documents with spaces
CREATE TABLE IF NOT EXISTS space_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES project_spaces(id) ON DELETE CASCADE,
    document_id VARCHAR(255) NOT NULL, -- References document_status.document_id
    added_by UUID NOT NULL REFERENCES users(id),
    tags JSONB DEFAULT '[]', -- Space-specific tags for the document
    metadata JSONB DEFAULT '{}', -- Space-specific metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(space_id, document_id) -- One document can only be in one space
);

-- Add space_id to document_status table (optional - for direct association)
ALTER TABLE document_status 
ADD COLUMN IF NOT EXISTS space_id UUID REFERENCES project_spaces(id) ON DELETE SET NULL;

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_project_spaces_created_by ON project_spaces(created_by);
CREATE INDEX IF NOT EXISTS idx_project_spaces_name ON project_spaces(name);
CREATE INDEX IF NOT EXISTS idx_space_members_space_id ON space_members(space_id);
CREATE INDEX IF NOT EXISTS idx_space_members_user_id ON space_members(user_id);
CREATE INDEX IF NOT EXISTS idx_space_documents_space_id ON space_documents(space_id);
CREATE INDEX IF NOT EXISTS idx_space_documents_document_id ON space_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_document_status_space_id ON document_status(space_id);

-- Create triggers for auto-updating timestamps
DROP TRIGGER IF EXISTS update_project_spaces_updated_at ON project_spaces;
CREATE TRIGGER update_project_spaces_updated_at 
    BEFORE UPDATE ON project_spaces 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create default "General" space for existing users
INSERT INTO project_spaces (name, description, color, icon, created_by)
SELECT 
    'General',
    'Default project space for general documents',
    '#1976d2',
    'folder',
    id
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM project_spaces 
    WHERE name = 'General' AND created_by = users.id
);

-- Add current users as owners of their default spaces
INSERT INTO space_members (space_id, user_id, role, permissions, added_by)
SELECT 
    ps.id,
    ps.created_by,
    'owner',
    '["read", "write", "admin", "delete"]',
    ps.created_by
FROM project_spaces ps
WHERE ps.name = 'General'
AND NOT EXISTS (
    SELECT 1 FROM space_members sm 
    WHERE sm.space_id = ps.id AND sm.user_id = ps.created_by
);

-- Create sample project spaces for demonstration
INSERT INTO project_spaces (name, description, color, icon, created_by)
SELECT 
    'Contracts',
    'Legal contracts and agreements',
    '#4caf50',
    'gavel',
    id
FROM users
WHERE username = 'admin'
AND NOT EXISTS (
    SELECT 1 FROM project_spaces 
    WHERE name = 'Contracts' AND created_by = users.id
);

INSERT INTO project_spaces (name, description, color, icon, created_by)
SELECT 
    'Research',
    'Research documents and papers',
    '#ff9800',
    'science',
    id
FROM users
WHERE username = 'admin'
AND NOT EXISTS (
    SELECT 1 FROM project_spaces 
    WHERE name = 'Research' AND created_by = users.id
);

-- Add admin as owner of sample spaces
INSERT INTO space_members (space_id, user_id, role, permissions, added_by)
SELECT 
    ps.id,
    u.id,
    'owner',
    '["read", "write", "admin", "delete"]',
    u.id
FROM project_spaces ps, users u
WHERE u.username = 'admin' 
AND ps.name IN ('Contracts', 'Research')
AND ps.created_by = u.id
AND NOT EXISTS (
    SELECT 1 FROM space_members sm 
    WHERE sm.space_id = ps.id AND sm.user_id = u.id
);

-- Create views for easier querying
CREATE OR REPLACE VIEW user_project_spaces AS
SELECT 
    ps.id,
    ps.name,
    ps.description,
    ps.color,
    ps.icon,
    ps.settings,
    ps.created_by,
    ps.created_at,
    ps.updated_at,
    sm.user_id,
    sm.role,
    sm.permissions,
    (SELECT COUNT(*) FROM space_documents sd WHERE sd.space_id = ps.id) as document_count
FROM project_spaces ps
JOIN space_members sm ON ps.id = sm.space_id;

-- Create view for space analytics
CREATE OR REPLACE VIEW space_analytics AS
SELECT 
    ps.id as space_id,
    ps.name as space_name,
    COUNT(sd.id) as total_documents,
    COUNT(CASE WHEN ds.status = 'completed' THEN 1 END) as processed_documents,
    COUNT(CASE WHEN ds.status = 'processing' THEN 1 END) as processing_documents,
    COUNT(CASE WHEN ds.status = 'failed' THEN 1 END) as failed_documents,
    AVG(ds.progress) as avg_progress,
    MAX(sd.created_at) as last_document_added,
    COUNT(DISTINCT sm.user_id) as member_count
FROM project_spaces ps
LEFT JOIN space_documents sd ON ps.id = sd.space_id
LEFT JOIN document_status ds ON sd.document_id = ds.document_id
LEFT JOIN space_members sm ON ps.id = sm.space_id
GROUP BY ps.id, ps.name;

