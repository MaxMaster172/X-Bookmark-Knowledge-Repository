-- API Usage Tracking Table
-- Tracks daily API calls for cost control

CREATE TABLE IF NOT EXISTS api_usage (
    date DATE PRIMARY KEY,
    analysis_count INTEGER DEFAULT 0,
    synthesis_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comment for documentation
COMMENT ON TABLE api_usage IS 'Tracks daily Claude API usage for cost control';
COMMENT ON COLUMN api_usage.analysis_count IS 'Number of post analysis calls today';
COMMENT ON COLUMN api_usage.synthesis_count IS 'Number of synthesis regeneration calls today';
