-- NeGD Portal — Optimized Supabase Schema for SeMT Monthly Reports
-- Run this in Supabase SQL Editor

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

----------------------------------------------------------
-- 2. Reports (Top-level metadata per uploaded PDF)
----------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state TEXT NOT NULL,
    reporting_month TEXT NOT NULL,     -- Format: YYYY-MM
    scheme TEXT DEFAULT NULL,
    file_url TEXT,
    file_name TEXT NOT NULL,

    semt_team JSONB DEFAULT NULL,      -- List of team members

    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_status TEXT DEFAULT 'pending'
        CHECK (processed_status IN ('pending', 'processing', 'indexed', 'failed')),
    chunk_count INT DEFAULT 0,
    error_message TEXT DEFAULT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_reports_state ON reports(state);
CREATE INDEX IF NOT EXISTS idx_reports_month ON reports(reporting_month);
CREATE INDEX IF NOT EXISTS idx_reports_state_month ON reports(state, reporting_month);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(processed_status);

----------------------------------------------------------
-- 3. Report Sections (Structured tagging per section)
----------------------------------------------------------
CREATE TABLE IF NOT EXISTS report_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,

    section_type TEXT NOT NULL
        CHECK (section_type IN (
            'ongoing_projects',
            'documents_submitted',
            'major_activities',
            'proposed_activities'
        )),

    practice_area TEXT DEFAULT NULL,  -- e.g., "Digital Transformation"
    title TEXT DEFAULT NULL,
    content TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sections_report_id ON report_sections(report_id);
CREATE INDEX IF NOT EXISTS idx_sections_type ON report_sections(section_type);

----------------------------------------------------------
-- 4. Report Chunks (RAG layer with embeddings)
----------------------------------------------------------
CREATE TABLE IF NOT EXISTS report_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,

    section_type TEXT NOT NULL,
    practice_area TEXT DEFAULT NULL,

    chunk_text TEXT NOT NULL,
    page_number INT DEFAULT NULL,
    chunk_index INT DEFAULT 0,

    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_report_id ON report_chunks(report_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section_type ON report_chunks(section_type);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON report_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

----------------------------------------------------------
-- 5. Semantic Search Function
----------------------------------------------------------
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(384),
    filter_state TEXT DEFAULT NULL,
    filter_month TEXT DEFAULT NULL,
    filter_section TEXT DEFAULT NULL,
    match_count INT DEFAULT 8
)
RETURNS TABLE (
    id UUID,
    report_id UUID,
    chunk_text TEXT,
    section_type TEXT,
    practice_area TEXT,
    state TEXT,
    reporting_month TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id,
        rc.report_id,
        rc.chunk_text,
        rc.section_type,
        rc.practice_area,
        r.state,
        r.reporting_month,
        1 - (rc.embedding <=> query_embedding) AS similarity
    FROM report_chunks rc
    JOIN reports r ON rc.report_id = r.id
    WHERE
        (filter_state IS NULL OR r.state = filter_state)
        AND (filter_month IS NULL OR r.reporting_month = filter_month)
        AND (filter_section IS NULL OR rc.section_type = filter_section)
        AND rc.embedding IS NOT NULL
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

----------------------------------------------------------
-- 6. Comparison Function
----------------------------------------------------------
CREATE OR REPLACE FUNCTION match_chunks_for_comparison(
    query_embedding VECTOR(384),
    filter_state TEXT,
    filter_month_a TEXT,
    filter_month_b TEXT,
    match_count INT DEFAULT 6
)
RETURNS TABLE (
    id UUID,
    report_id UUID,
    chunk_text TEXT,
    section_type TEXT,
    practice_area TEXT,
    state TEXT,
    reporting_month TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id,
        rc.report_id,
        rc.chunk_text,
        rc.section_type,
        rc.practice_area,
        r.state,
        r.reporting_month,
        1 - (rc.embedding <=> query_embedding) AS similarity
    FROM report_chunks rc
    JOIN reports r ON rc.report_id = r.id
    WHERE
        r.state = filter_state
        AND r.reporting_month IN (filter_month_a, filter_month_b)
        AND rc.embedding IS NOT NULL
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;