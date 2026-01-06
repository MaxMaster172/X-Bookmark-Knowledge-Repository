"""
Configuration for Knowledge Graph Analysis.

Cost controls and model settings for Claude API usage.
"""

# Analysis configuration
ANALYSIS_CONFIG = {
    # Model selection
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4000,  # Increased for posts with many entities

    # Confidence thresholds
    "min_entity_confidence": 0.6,  # Below this, don't auto-link
    "min_thesis_confidence": 0.5,  # Below this, don't auto-link
    "max_new_theses_per_post": 2,  # Limit new thesis creation

    # Cost controls
    "max_daily_analysis": 20,
    "max_monthly_analysis": 500,
    "max_daily_synthesis": 20,
}

# Synthesis configuration (for future use)
SYNTHESIS_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 3000,

    # Regeneration triggers
    "threshold_posts": 3,  # Regenerate after N new posts
    "min_hours_between_auto": 24,  # Minimum hours between auto-regenerations
    "on_demand_cooldown_hours": 1,  # Cooldown between manual regenerations

    # Large thesis handling
    "max_posts_full_context": 50,  # Include full content up to this many posts
}
