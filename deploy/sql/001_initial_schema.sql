-- ============================================
-- X-Bookmark Knowledge Repository - Initial Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- CORE POSTS TABLE
-- ============================================

CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    author_handle TEXT,
    author_name TEXT,
    content TEXT,
    posted_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archived_via TEXT DEFAULT 'telegram',
    tags TEXT[],
    topics TEXT[],
    notes TEXT,
    importance TEXT,
    thread_position INTEGER,
    is_thread BOOLEAN DEFAULT FALSE,

    -- Quoted post (embedded)
    quoted_post_id TEXT,
    quoted_text TEXT,
    quoted_author TEXT,
    quoted_url TEXT,

    -- Embedding vector (384 dimensions for BGE)
    embedding VECTOR(384)
);

-- ============================================
-- MEDIA ITEMS (one-to-many)
-- ============================================

CREATE TABLE post_media (
    id SERIAL PRIMARY KEY,
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    type TEXT,
    url TEXT,
    category TEXT,  -- 'text_heavy', 'chart', 'general'
    description TEXT,
    extracted_at TIMESTAMPTZ,
    extraction_model TEXT
);

-- ============================================
-- RESEARCH SESSIONS (for RAG chat)
-- ============================================

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    conversation JSONB
);

CREATE TABLE session_posts (
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (session_id, post_id)
);

-- ============================================
-- THESIS SYSTEM TABLES
-- ============================================

-- Entity categories (umbrella groups: Amino Acids, Memory Companies)
CREATE TABLE entity_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entities (nouns: Glycine, SK Hynix, Vitamin D)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category_id UUID REFERENCES entity_categories(id) ON DELETE SET NULL,
    description TEXT,
    aliases TEXT[] DEFAULT '{}',
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, category_id)
);

-- Theses (evolving understanding: Sleep, HBM Memory Leadership)
CREATE TABLE theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    category TEXT,  -- 'investing', 'health', 'tech'
    description TEXT,
    current_synthesis TEXT,
    synthesis_updated_at TIMESTAMPTZ,
    synthesis_post_count INTEGER DEFAULT 0,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Junction: Posts <-> Entities
CREATE TABLE post_entities (
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    manually_verified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (post_id, entity_id)
);

-- Junction: Posts <-> Theses (with contribution summary)
CREATE TABLE post_theses (
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    thesis_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    contribution TEXT,
    confidence FLOAT DEFAULT 1.0,
    manually_verified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (post_id, thesis_id)
);

-- Junction: Entities <-> Theses
CREATE TABLE entity_theses (
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    thesis_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'subject',
    PRIMARY KEY (entity_id, thesis_id)
);

-- Thesis relationships (Vitamin D <-> K2)
CREATE TABLE thesis_relationships (
    thesis_a_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    thesis_b_id UUID REFERENCES theses(id) ON DELETE CASCADE,
    relationship_type TEXT,
    description TEXT,
    PRIMARY KEY (thesis_a_id, thesis_b_id),
    CHECK (thesis_a_id < thesis_b_id)
);

-- Corrections (for learning from user steering)
CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
    correction_type TEXT NOT NULL,
    original_value JSONB,
    corrected_value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Posts indexes
CREATE INDEX posts_author_idx ON posts(author_handle);
CREATE INDEX posts_archived_at_idx ON posts(archived_at DESC);
CREATE INDEX posts_tags_idx ON posts USING GIN(tags);
CREATE INDEX posts_topics_idx ON posts USING GIN(topics);
CREATE INDEX posts_embedding_idx ON posts USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Media index
CREATE INDEX post_media_post_id_idx ON post_media(post_id);

-- Thesis system indexes
CREATE INDEX entities_category_idx ON entities(category_id);
CREATE INDEX entities_embedding_idx ON entities USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX theses_category_idx ON theses(category);
CREATE INDEX theses_embedding_idx ON theses USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX post_entities_entity_idx ON post_entities(entity_id);
CREATE INDEX post_theses_thesis_idx ON post_theses(thesis_id);

-- ============================================
-- ROW LEVEL SECURITY (optional, enable later)
-- ============================================

-- ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow authenticated read" ON posts FOR SELECT USING (true);
-- CREATE POLICY "Allow authenticated insert" ON posts FOR INSERT WITH CHECK (true);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_posts(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        posts.id,
        posts.content,
        1 - (posts.embedding <=> query_embedding) AS similarity
    FROM posts
    WHERE posts.embedding IS NOT NULL
        AND 1 - (posts.embedding <=> query_embedding) > match_threshold
    ORDER BY posts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
