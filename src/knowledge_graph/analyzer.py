"""
Post Analyzer - Detects entities and theses in posts using Claude.

Uses Claude Sonnet to analyze post content and identify:
- Entities (companies, people, technologies, concepts)
- Theses the post contributes to
- Relationships between theses
"""

import os
import json
import logging
from typing import Optional
from dataclasses import dataclass

import anthropic

from .config import ANALYSIS_CONFIG
from .prompts import POST_ANALYSIS_PROMPT, POST_ANALYSIS_PROMPT_SIMPLE

logger = logging.getLogger(__name__)

# Singleton instance
_analyzer: Optional["PostAnalyzer"] = None


@dataclass
class AnalysisResult:
    """Result of analyzing a post."""

    entities: list[dict]
    theses: list[dict]
    suggested_new_category: Optional[dict]
    cross_thesis_relationships: list[dict]
    raw_response: str

    @property
    def has_results(self) -> bool:
        """Check if any entities or theses were detected."""
        return bool(self.entities or self.theses)

    def to_display_text(self) -> str:
        """Format for display in Telegram."""
        lines = []

        if self.entities:
            lines.append("<b>Entities detected:</b>")
            for e in self.entities:
                new_tag = " [NEW]" if e.get("is_new") else ""
                category = f" ({e.get('category', 'uncategorized')})" if e.get("category") else ""
                lines.append(f"  - {e['name']}{category}{new_tag}")

        if self.theses:
            if lines:
                lines.append("")
            lines.append("<b>Contributes to theses:</b>")
            for t in self.theses:
                new_tag = " [NEW]" if t.get("is_new") else ""
                lines.append(f"  - {t['name']}{new_tag}")
                if t.get("contribution_summary"):
                    # Truncate long summaries
                    summary = t["contribution_summary"][:100]
                    if len(t["contribution_summary"]) > 100:
                        summary += "..."
                    lines.append(f"    <i>\"{summary}\"</i>")

        if not lines:
            return "No entities or theses detected."

        return "\n".join(lines)


class PostAnalyzer:
    """Analyzes posts for entities and theses using Claude."""

    def __init__(self, supabase_client, api_key: str = None):
        """
        Initialize the post analyzer.

        Args:
            supabase_client: SupabaseClient instance for DB operations
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.db = supabase_client
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        self._client = anthropic.Anthropic(api_key=self.api_key)
        self.model = ANALYSIS_CONFIG["model"]
        self.max_tokens = ANALYSIS_CONFIG["max_tokens"]

        logger.info("Post analyzer initialized")

    def analyze_post(
        self,
        content: str,
        author: str = "unknown",
        tags: list[str] = None,
        topics: list[str] = None,
        notes: str = None,
    ) -> AnalysisResult:
        """
        Analyze a post for entities and theses.

        Args:
            content: The post content text
            author: Author handle
            tags: User-provided tags
            topics: User-provided topics
            notes: User-provided notes

        Returns:
            AnalysisResult with detected entities and theses
        """
        # Check rate limit
        if not self.db.check_analysis_limit(ANALYSIS_CONFIG["max_daily_analysis"]):
            logger.warning("Daily analysis limit reached")
            return AnalysisResult(
                entities=[],
                theses=[],
                suggested_new_category=None,
                cross_thesis_relationships=[],
                raw_response="Rate limit reached",
            )

        # Fetch existing data for matching
        existing_entities = self.db.get_all_entities_with_aliases()
        existing_theses = self.db.get_all_theses()
        existing_categories = self.db.get_all_entity_categories()

        # Build prompt
        prompt = POST_ANALYSIS_PROMPT.format(
            post_content=content,
            author=author,
            tags=", ".join(tags or []) or "None",
            topics=", ".join(topics or []) or "None",
            notes=notes or "None",
            existing_entities_json=json.dumps(existing_entities, indent=2) if existing_entities else "[]",
            existing_theses_json=json.dumps(existing_theses, indent=2) if existing_theses else "[]",
            existing_categories_json=json.dumps(existing_categories, indent=2) if existing_categories else "[]",
        )

        try:
            # Call Claude
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = response.content[0].text.strip()

            # Log response stats for debugging
            stop_reason = response.stop_reason
            if stop_reason == "max_tokens":
                logger.warning(f"Response truncated due to max_tokens limit")
                logger.debug(f"Truncated response: {raw_text[:500]}...")

            # Increment usage counter
            self.db.increment_analysis_count()

            # Parse JSON response
            result = self._parse_response(raw_text)

            # Log if no results found (helpful for debugging)
            if not result.has_results:
                logger.warning(f"No entities/theses detected. Raw response length: {len(raw_text)}")
                logger.debug(f"Raw response: {raw_text[:1000]}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Raw response: {raw_text}")
            return AnalysisResult(
                entities=[],
                theses=[],
                suggested_new_category=None,
                cross_thesis_relationships=[],
                raw_response=raw_text,
            )
        except Exception as e:
            logger.error(f"Post analysis failed: {e}")
            return AnalysisResult(
                entities=[],
                theses=[],
                suggested_new_category=None,
                cross_thesis_relationships=[],
                raw_response=str(e),
            )

    def _parse_response(self, raw_text: str) -> AnalysisResult:
        """Parse Claude's JSON response into AnalysisResult."""
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in raw_text:
            start = raw_text.find("```json") + 7
            end = raw_text.find("```", start)
            raw_text = raw_text[start:end].strip()
        elif "```" in raw_text:
            start = raw_text.find("```") + 3
            end = raw_text.find("```", start)
            raw_text = raw_text[start:end].strip()

        data = json.loads(raw_text)

        # Filter by confidence threshold
        min_entity_conf = ANALYSIS_CONFIG["min_entity_confidence"]
        min_thesis_conf = ANALYSIS_CONFIG["min_thesis_confidence"]

        raw_entities = data.get("entities", [])
        raw_theses = data.get("theses", [])

        entities = [
            e for e in raw_entities
            if isinstance(e, dict) and e.get("confidence", 0) >= min_entity_conf
        ]

        theses = [
            t for t in raw_theses
            if isinstance(t, dict) and t.get("confidence", 0) >= min_thesis_conf
        ]

        # Log filtering stats
        if len(raw_entities) != len(entities) or len(raw_theses) != len(theses):
            logger.info(
                f"Filtered: {len(raw_entities)} -> {len(entities)} entities, "
                f"{len(raw_theses)} -> {len(theses)} theses"
            )

        # Limit new theses
        max_new = ANALYSIS_CONFIG["max_new_theses_per_post"]
        new_theses = [t for t in theses if t.get("is_new")]
        existing_theses = [t for t in theses if not t.get("is_new")]
        if len(new_theses) > max_new:
            new_theses = sorted(new_theses, key=lambda t: t.get("confidence", 0), reverse=True)[:max_new]
        theses = existing_theses + new_theses

        return AnalysisResult(
            entities=entities,
            theses=theses,
            suggested_new_category=data.get("suggested_new_category"),
            cross_thesis_relationships=data.get("cross_thesis_relationships", []),
            raw_response=raw_text,
        )

    def apply_analysis(
        self,
        post_id: str,
        analysis: AnalysisResult,
        user_corrections: dict = None,
    ) -> dict:
        """
        Apply analysis results to the database.

        Creates entities/theses if new, links post to all detected items.

        Args:
            post_id: The post ID to link
            analysis: AnalysisResult from analyze_post()
            user_corrections: Optional dict of user edits (not yet implemented)

        Returns:
            Dict with created/linked counts
        """
        created = {"entities": 0, "theses": 0, "categories": 0}
        linked = {"entities": 0, "theses": 0}

        # Handle new category if suggested
        if analysis.suggested_new_category:
            cat = analysis.suggested_new_category
            self.db.create_entity_category(
                name=cat.get("name"),
                description=cat.get("description"),
            )
            created["categories"] += 1

        # Fetch existing entities/theses for name-based lookup (don't trust Claude's IDs)
        existing_entities = {e["name"].lower(): e["id"] for e in self.db.get_all_entities_with_aliases()}
        existing_theses = {t["name"].lower(): t["id"] for t in self.db.get_all_theses()}

        # Process entities
        for entity in analysis.entities:
            entity_name = entity.get("name", "")

            # Look up by name first (Claude's IDs might be hallucinated)
            entity_id = existing_entities.get(entity_name.lower())

            if entity_id:
                # Entity exists, just link it
                pass
            else:
                # Create new entity
                entity_id = self.db.create_entity(
                    name=entity_name,
                    category_name=entity.get("category"),
                    description=entity.get("context"),
                )
                created["entities"] += 1
                # Add to lookup for future reference in this batch
                existing_entities[entity_name.lower()] = entity_id

            if entity_id:
                self.db.link_post_entity(
                    post_id=post_id,
                    entity_id=entity_id,
                    confidence=entity.get("confidence", 1.0),
                )
                linked["entities"] += 1

        # Process theses
        for thesis in analysis.theses:
            thesis_name = thesis.get("name", "")

            # Look up by name first (Claude's IDs might be hallucinated)
            thesis_id = existing_theses.get(thesis_name.lower())

            if thesis_id:
                # Thesis exists, just link it
                pass
            else:
                # Create new thesis
                thesis_id = self.db.create_thesis(
                    name=thesis_name,
                    category=thesis.get("category", "general"),
                )
                created["theses"] += 1
                # Add to lookup for future reference in this batch
                existing_theses[thesis_name.lower()] = thesis_id

            if thesis_id:
                self.db.link_post_thesis(
                    post_id=post_id,
                    thesis_id=thesis_id,
                    contribution=thesis.get("contribution_summary"),
                    confidence=thesis.get("confidence", 1.0),
                )
                linked["theses"] += 1

                # Link entities to thesis (use our name-based lookup)
                for entity in analysis.entities:
                    entity_name = entity.get("name", "")
                    ent_id = existing_entities.get(entity_name.lower())

                    if ent_id:
                        self.db.link_entity_thesis(
                            entity_id=ent_id,
                            thesis_id=thesis_id,
                            role="subject",
                        )

        # Process cross-thesis relationships
        for rel in analysis.cross_thesis_relationships:
            # Look up thesis IDs by name
            theses_list = self.db.get_all_theses()
            thesis_a_id = None
            thesis_b_id = None

            for t in theses_list:
                if t["name"] == rel.get("thesis_a"):
                    thesis_a_id = t["id"]
                if t["name"] == rel.get("thesis_b"):
                    thesis_b_id = t["id"]

            if thesis_a_id and thesis_b_id:
                self.db.create_thesis_relationship(
                    thesis_a_id=thesis_a_id,
                    thesis_b_id=thesis_b_id,
                    relationship_type=rel.get("relationship", "related"),
                    description=rel.get("reason"),
                )

        logger.info(
            f"Applied analysis: created {created}, linked {linked}"
        )

        return {"created": created, "linked": linked}


def get_post_analyzer(supabase_client) -> PostAnalyzer:
    """Get the singleton post analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = PostAnalyzer(supabase_client)
    return _analyzer
