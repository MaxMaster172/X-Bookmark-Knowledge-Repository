"""
Claude prompts for knowledge graph analysis.

Based on docs/THESIS_SYSTEM_DESIGN.md
"""

POST_ANALYSIS_PROMPT = """Analyze this archived post for knowledge graph integration.

## POST CONTENT
{post_content}

## POST METADATA
Author: {author}
Tags: {tags}
Topics: {topics}
User notes: {notes}

## EXISTING ENTITIES (match these first before creating new)
{existing_entities_json}

## EXISTING THESES (match these first before creating new)
{existing_theses_json}

## EXISTING ENTITY CATEGORIES
{existing_categories_json}

## INSTRUCTIONS
1. Identify all entities mentioned (companies, people, substances, technologies, etc.)
2. Match to existing entities when possible (check aliases)
3. Identify which theses this post supports or adds to
4. For new entities/theses, suggest appropriate categorization
5. Keep confidence scores realistic - 0.9+ only for explicit, clear mentions

## MULTILINGUAL SUPPORT
- The post content may be in ANY language (Japanese, Korean, Chinese, etc.)
- Analyze the content in its original language
- Return entity names in their ORIGINAL LANGUAGE as they appear in the post
- For well-known entities, also check if English aliases exist in the existing entities list
- Thesis names should be in ENGLISH for consistency across the knowledge graph
- The contribution_summary should be in ENGLISH

Return valid JSON only (no markdown code blocks):
{{
    "entities": [
        {{
            "name": "Entity Name",
            "existing_id": "uuid-if-matched-or-null",
            "category": "Category Name",
            "category_id": "uuid-if-matched-or-null",
            "is_new": true,
            "confidence": 0.85,
            "context": "brief context of how entity is mentioned"
        }}
    ],
    "theses": [
        {{
            "name": "Thesis Name",
            "existing_id": "uuid-if-matched-or-null",
            "category": "investing|health|tech|general",
            "is_new": false,
            "confidence": 0.80,
            "contribution_summary": "One sentence explaining how this post adds to the thesis"
        }}
    ],
    "suggested_new_category": null,
    "cross_thesis_relationships": []
}}

IMPORTANT:
- Return ONLY valid JSON, no explanations or markdown
- Match existing entities/theses by name when possible
- Set is_new=false and include existing_id when matching existing items
- Keep contribution_summary concise (1-2 sentences max)
- If no entities or theses detected, return empty arrays
"""

# Simpler fallback prompt for when we have no existing data
POST_ANALYSIS_PROMPT_SIMPLE = """Analyze this post and identify:
1. Key entities (companies, people, technologies, concepts)
2. Main topics/theses the post contributes to

POST:
{post_content}

Author: {author}
Tags: {tags}
Topics: {topics}
Notes: {notes}

MULTILINGUAL: The post may be in any language (Japanese, Korean, Chinese, etc.).
- Analyze content in its original language
- Entity names: keep in original language
- Thesis names and contribution_summary: use ENGLISH

Return valid JSON only:
{{
    "entities": [
        {{"name": "Entity", "category": "Category", "confidence": 0.8, "context": "how mentioned"}}
    ],
    "theses": [
        {{"name": "Thesis Name", "category": "investing|health|tech|general", "confidence": 0.7, "contribution_summary": "how this post adds"}}
    ]
}}
"""
