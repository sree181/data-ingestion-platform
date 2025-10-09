-- Multi-Source Data Integration Schema
-- ====================================
-- 
-- This schema supports the multi-source data integration system
-- with support for 38+ external data sources, unified document
-- storage, and cross-source entity linking.
--
-- Author: Document Intelligence Platform Team
-- Date: October 2025

-- ===========================================
-- DATA SOURCES MANAGEMENT
-- ===========================================

-- Table to track all available data sources
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'pubmed', 'clinicaltrials', etc
    display_name VARCHAR(200) NOT NULL,
    source_type VARCHAR(50) NOT NULL,   -- 'research_paper', 'clinical_trial', etc
    description TEXT,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'disabled', 'maintenance'
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_second INTEGER DEFAULT 3,
    rate_limit_per_minute INTEGER DEFAULT 100,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    rate_limit_per_day INTEGER DEFAULT 10000,
    last_sync_at TIMESTAMP,
    last_health_check TIMESTAMP,
    health_status VARCHAR(20) DEFAULT 'unknown', -- 'healthy', 'unhealthy', 'unknown'
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    config JSONB DEFAULT '{}',  -- Source-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for data_sources
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_data_sources_status ON data_sources(status);
CREATE INDEX IF NOT EXISTS idx_data_sources_health ON data_sources(health_status);

-- ===========================================
-- INGESTION JOBS
-- ===========================================

-- Table to track multi-source ingestion jobs
CREATE TABLE IF NOT EXISTS source_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) UNIQUE NOT NULL,  -- Human-readable job ID
    project_space_id UUID NOT NULL,
    query TEXT NOT NULL,
    sources JSONB DEFAULT '[]',  -- List of source names
    filters JSONB DEFAULT '{}',  -- Source-specific filters
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    total_documents INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_space_id) REFERENCES project_spaces(id) ON DELETE CASCADE
);

-- Indexes for source_sync_jobs
CREATE INDEX IF NOT EXISTS idx_sync_jobs_project ON source_sync_jobs(project_space_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON source_sync_jobs(status);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_created ON source_sync_jobs(created_at);

-- ===========================================
-- UNIFIED DOCUMENTS
-- ===========================================

-- Main documents table (extends existing documents table)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES data_sources(id),
    source_document_id VARCHAR(200) NOT NULL,  -- Original ID from source (PMID, NCT ID, etc)
    project_space_id UUID,
    title TEXT NOT NULL,
    abstract TEXT,
    content TEXT,  -- Full text if available
    summary TEXT,  -- AI-generated summary
    document_type VARCHAR(50) NOT NULL,  -- 'research_article', 'clinical_trial', etc
    language VARCHAR(10) DEFAULT 'en',
    publication_date TIMESTAMP,
    url TEXT,
    alternate_urls JSONB DEFAULT '[]',
    doi VARCHAR(200),
    pmid VARCHAR(50),
    pmcid VARCHAR(50),
    citations JSONB DEFAULT '[]',  -- List of citation IDs
    quality_score FLOAT DEFAULT 0.0,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_errors JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',  -- Source-specific fields
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique documents per source
    UNIQUE(source_id, source_document_id),
    FOREIGN KEY (project_space_id) REFERENCES project_spaces(id) ON DELETE SET NULL
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_space ON documents(project_space_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(publication_date);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_doi ON documents(doi) WHERE doi IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_pmid ON documents(pmid) WHERE pmid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_quality ON documents(quality_score);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_documents_search ON documents USING gin(
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(abstract, '') || ' ' || coalesce(content, ''))
);

-- ===========================================
-- AUTHORS
-- ===========================================

-- Authors table (normalized)
CREATE TABLE IF NOT EXISTS document_authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    affiliation TEXT,
    orcid VARCHAR(50),
    email VARCHAR(255),
    position INTEGER,  -- Order in author list
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_authors
CREATE INDEX IF NOT EXISTS idx_authors_document ON document_authors(document_id);
CREATE INDEX IF NOT EXISTS idx_authors_name ON document_authors(name);
CREATE INDEX IF NOT EXISTS idx_authors_orcid ON document_authors(orcid) WHERE orcid IS NOT NULL;

-- ===========================================
-- ENTITIES
-- ===========================================

-- Extracted entities from documents
CREATE TABLE IF NOT EXISTS document_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'DRUG', 'DISEASE', 'GENE', etc
    entity_value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,  -- Standardized name for linking
    confidence FLOAT NOT NULL,
    start_pos INTEGER,
    end_pos INTEGER,
    context TEXT,
    source VARCHAR(100),  -- Which AI model extracted this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_entities
CREATE INDEX IF NOT EXISTS idx_entities_document ON document_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON document_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_value ON document_entities(normalized_value);
CREATE INDEX IF NOT EXISTS idx_entities_confidence ON document_entities(confidence);
CREATE INDEX IF NOT EXISTS idx_entities_composite ON document_entities(entity_type, normalized_value);

-- ===========================================
-- RELATIONSHIPS
-- ===========================================

-- Relationships between entities
CREATE TABLE IF NOT EXISTS document_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    context TEXT,
    source VARCHAR(100),  -- Which AI model extracted this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_relationships
CREATE INDEX IF NOT EXISTS idx_relationships_document ON document_relationships(document_id);
CREATE INDEX IF NOT EXISTS idx_relationships_subject ON document_relationships(subject);
CREATE INDEX IF NOT EXISTS idx_relationships_object ON document_relationships(object);
CREATE INDEX IF NOT EXISTS idx_relationships_predicate ON document_relationships(predicate);

-- ===========================================
-- CROSS-SOURCE LINKS
-- ===========================================

-- Links between entities across different sources
CREATE TABLE IF NOT EXISTS cross_source_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    normalized_value TEXT NOT NULL,
    source_1 VARCHAR(100) NOT NULL,
    source_id_1 VARCHAR(200) NOT NULL,
    source_2 VARCHAR(100) NOT NULL,
    source_id_2 VARCHAR(200) NOT NULL,
    link_type VARCHAR(50) NOT NULL,  -- 'same_entity', 'related', 'contradicts'
    confidence FLOAT NOT NULL,
    evidence JSONB DEFAULT '{}',  -- Supporting evidence for the link
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cross_source_links
CREATE INDEX IF NOT EXISTS idx_links_entity ON cross_source_links(entity_type, normalized_value);
CREATE INDEX IF NOT EXISTS idx_links_source1 ON cross_source_links(source_1, source_id_1);
CREATE INDEX IF NOT EXISTS idx_links_source2 ON cross_source_links(source_2, source_id_2);
CREATE INDEX IF NOT EXISTS idx_links_type ON cross_source_links(link_type);

-- ===========================================
-- KEY CONCEPTS
-- ===========================================

-- Key concepts extracted from documents
CREATE TABLE IF NOT EXISTS document_key_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    relevance_score FLOAT DEFAULT 0.0,
    source VARCHAR(100),  -- Which AI model extracted this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_key_concepts
CREATE INDEX IF NOT EXISTS idx_concepts_document ON document_key_concepts(document_id);
CREATE INDEX IF NOT EXISTS idx_concepts_concept ON document_key_concepts(concept);
CREATE INDEX IF NOT EXISTS idx_concepts_score ON document_key_concepts(relevance_score);

-- ===========================================
-- TAGS
-- ===========================================

-- Tags associated with documents
CREATE TABLE IF NOT EXISTS document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag VARCHAR(200) NOT NULL,
    source VARCHAR(100),  -- 'manual', 'ai', 'auto'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_tags
CREATE INDEX IF NOT EXISTS idx_tags_document ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON document_tags(tag);

-- ===========================================
-- SEARCH ANALYTICS
-- ===========================================

-- Track search queries and results for analytics
CREATE TABLE IF NOT EXISTS search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    query TEXT NOT NULL,
    sources_searched JSONB DEFAULT '[]',
    total_results INTEGER DEFAULT 0,
    results_by_source JSONB DEFAULT '{}',
    filters_applied JSONB DEFAULT '{}',
    search_time_ms INTEGER,
    clicked_documents JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search_analytics
CREATE INDEX IF NOT EXISTS idx_analytics_user ON search_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_query ON search_analytics(query);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON search_analytics(created_at);

-- ===========================================
-- VIEWS FOR COMMON QUERIES
-- ===========================================

-- View for document search with all related data
CREATE OR REPLACE VIEW document_search_view AS
SELECT 
    d.id,
    d.title,
    d.abstract,
    d.content,
    d.summary,
    d.document_type,
    d.publication_date,
    d.url,
    d.doi,
    d.pmid,
    d.quality_score,
    d.processing_status,
    d.created_at,
    d.updated_at,
    ds.name as source_name,
    ds.display_name as source_display_name,
    ds.source_type,
    -- Aggregate authors
    COALESCE(
        json_agg(
            json_build_object(
                'name', da.name,
                'affiliation', da.affiliation,
                'orcid', da.orcid,
                'email', da.email,
                'position', da.position
            ) ORDER BY da.position
        ) FILTER (WHERE da.id IS NOT NULL),
        '[]'::json
    ) as authors,
    -- Aggregate entities by type
    COALESCE(
        json_object_agg(
            de.entity_type,
            json_agg(
                json_build_object(
                    'value', de.entity_value,
                    'normalized_value', de.normalized_value,
                    'confidence', de.confidence,
                    'context', de.context
                )
            ) FILTER (WHERE de.entity_type IS NOT NULL)
        ),
        '{}'::json
    ) as entities,
    -- Aggregate key concepts
    COALESCE(
        json_agg(DISTINCT dkc.concept) FILTER (WHERE dkc.concept IS NOT NULL),
        '[]'::json
    ) as key_concepts,
    -- Aggregate tags
    COALESCE(
        json_agg(DISTINCT dt.tag) FILTER (WHERE dt.tag IS NOT NULL),
        '[]'::json
    ) as tags
FROM documents d
LEFT JOIN data_sources ds ON d.source_id = ds.id
LEFT JOIN document_authors da ON d.id = da.document_id
LEFT JOIN document_entities de ON d.id = de.document_id
LEFT JOIN document_key_concepts dkc ON d.id = dkc.document_id
LEFT JOIN document_tags dt ON d.id = dt.document_id
WHERE d.is_deleted = false
GROUP BY d.id, ds.name, ds.display_name, ds.source_type;

-- View for source statistics
CREATE OR REPLACE VIEW source_statistics AS
SELECT 
    ds.name,
    ds.display_name,
    ds.source_type,
    ds.status,
    ds.health_status,
    ds.last_sync_at,
    COUNT(d.id) as total_documents,
    COUNT(d.id) FILTER (WHERE d.processing_status = 'completed') as processed_documents,
    COUNT(d.id) FILTER (WHERE d.processing_status = 'failed') as failed_documents,
    AVG(d.quality_score) as avg_quality_score,
    MAX(d.created_at) as last_document_created
FROM data_sources ds
LEFT JOIN documents d ON ds.id = d.source_id AND d.is_deleted = false
GROUP BY ds.id, ds.name, ds.display_name, ds.source_type, ds.status, ds.health_status, ds.last_sync_at;

-- ===========================================
-- FUNCTIONS
-- ===========================================

-- Function to get document by source and source_id
CREATE OR REPLACE FUNCTION get_document_by_source(
    p_source_name VARCHAR(100),
    p_source_document_id VARCHAR(200)
) RETURNS TABLE (
    id UUID,
    title TEXT,
    abstract TEXT,
    source_name VARCHAR(100),
    source_document_id VARCHAR(200)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.title,
        d.abstract,
        ds.name as source_name,
        d.source_document_id
    FROM documents d
    JOIN data_sources ds ON d.source_id = ds.id
    WHERE ds.name = p_source_name 
      AND d.source_document_id = p_source_document_id
      AND d.is_deleted = false;
END;
$$ LANGUAGE plpgsql;

-- Function to search documents across all sources
CREATE OR REPLACE FUNCTION search_documents_unified(
    p_query TEXT,
    p_sources JSONB DEFAULT NULL,
    p_document_types JSONB DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
) RETURNS TABLE (
    id UUID,
    title TEXT,
    abstract TEXT,
    source_name VARCHAR(100),
    document_type VARCHAR(50),
    publication_date TIMESTAMP,
    quality_score FLOAT,
    rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.title,
        d.abstract,
        ds.name as source_name,
        d.document_type,
        d.publication_date,
        d.quality_score,
        ts_rank(
            to_tsvector('english', coalesce(d.title, '') || ' ' || coalesce(d.abstract, '') || ' ' || coalesce(d.content, '')),
            plainto_tsquery('english', p_query)
        ) as rank
    FROM documents d
    JOIN data_sources ds ON d.source_id = ds.id
    WHERE d.is_deleted = false
      AND ds.status = 'active'
      AND (
        p_sources IS NULL OR 
        ds.name = ANY(SELECT jsonb_array_elements_text(p_sources))
      )
      AND (
        p_document_types IS NULL OR 
        d.document_type = ANY(SELECT jsonb_array_elements_text(p_document_types))
      )
      AND (
        to_tsvector('english', coalesce(d.title, '') || ' ' || coalesce(d.abstract, '') || ' ' || coalesce(d.content, ''))
        @@ plainto_tsquery('english', p_query)
      )
    ORDER BY rank DESC, d.quality_score DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- INITIAL DATA
-- ===========================================

-- Insert default data sources (will be populated by the application)
INSERT INTO data_sources (name, display_name, source_type, description, status, api_key_required) VALUES
('pubmed', 'PubMed', 'research_paper', 'NCBI PubMed database of biomedical literature', 'active', false),
('clinicaltrials', 'ClinicalTrials.gov', 'clinical_trial', 'US National Library of Medicine clinical trials database', 'active', false),
('fda', 'FDA OpenFDA', 'regulatory', 'US Food and Drug Administration open data', 'active', false),
('chembl', 'ChEMBL', 'chemical', 'EMBL-EBI chemical database of bioactive molecules', 'active', true),
('pubchem', 'PubChem', 'chemical', 'NIH chemical compound database', 'active', false),
('europepmc', 'Europe PMC', 'research_paper', 'European PubMed Central', 'active', false),
('semanticscholar', 'Semantic Scholar', 'research_paper', 'AI-powered research tool for scientific literature', 'active', false)
ON CONFLICT (name) DO NOTHING;

-- ===========================================
-- COMMENTS
-- ===========================================

COMMENT ON TABLE data_sources IS 'Registry of all available external data sources';
COMMENT ON TABLE source_sync_jobs IS 'Multi-source ingestion job tracking';
COMMENT ON TABLE documents IS 'Unified document storage across all sources';
COMMENT ON TABLE document_authors IS 'Document authors (normalized)';
COMMENT ON TABLE document_entities IS 'AI-extracted entities from documents';
COMMENT ON TABLE document_relationships IS 'Relationships between entities';
COMMENT ON TABLE cross_source_links IS 'Links between same entities across sources';
COMMENT ON TABLE document_key_concepts IS 'Key concepts extracted from documents';
COMMENT ON TABLE document_tags IS 'Tags associated with documents';
COMMENT ON TABLE search_analytics IS 'Search query analytics and tracking';

COMMENT ON VIEW document_search_view IS 'Complete document view with all related data for search';
COMMENT ON VIEW source_statistics IS 'Statistics about each data source';
