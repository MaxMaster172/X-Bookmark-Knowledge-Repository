"""
Image Extractor - Extracts semantic descriptions from images using Claude Vision API.

Uses Claude 3.5 Sonnet for high-quality vision understanding:
- Detects image category (text_heavy, chart, general)
- Extracts appropriate description based on category
- Supports context hints from post text
"""

import os
import base64
import logging
import time
from typing import Optional

import httpx
import anthropic

from .prompts import CATEGORY_DETECTION_PROMPT, get_extraction_prompt

logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "claude-3-5-sonnet-20241022"
MAX_IMAGE_SIZE_MB = 5
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_IMAGES = 0.5

# Singleton instance
_extractor: Optional["ImageExtractor"] = None


class ImageExtractor:
    """Extracts semantic descriptions from images using Claude Vision API."""

    def __init__(self, api_key: str = None):
        """
        Initialize the image extractor.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        self._client = anthropic.Anthropic(api_key=self.api_key)
        self._http_client = httpx.Client(timeout=REQUEST_TIMEOUT)
        logger.info("Image extractor initialized")

    def describe_image(
        self,
        image_url: str,
        post_context: str = None,
        category_hint: str = None,
    ) -> dict:
        """
        Extract a semantic description from an image.

        Args:
            image_url: URL of the image to analyze
            post_context: Optional text from the post for context
            category_hint: Optional category hint (text_heavy, chart, general)

        Returns:
            Dict with keys:
                - description: The extracted description
                - category: The detected category
                - extraction_model: The model used
        """
        try:
            # Fetch and encode the image
            image_data = self._fetch_image(image_url)
            if not image_data:
                logger.warning(f"Failed to fetch image: {image_url}")
                return None

            # Determine category
            category = category_hint
            if not category:
                category = self._infer_category_from_context(post_context)
            if not category:
                category = self._detect_category(image_data)

            # Extract description
            description = self._extract_description(image_data, post_context, category)

            # Rate limiting
            time.sleep(DELAY_BETWEEN_IMAGES)

            return {
                "description": description,
                "category": category,
                "extraction_model": MODEL_NAME,
            }

        except Exception as e:
            logger.error(f"Failed to describe image {image_url}: {e}")
            return None

    def _fetch_image(self, url: str) -> Optional[dict]:
        """
        Fetch an image and encode it as base64.

        Args:
            url: URL of the image

        Returns:
            Dict with 'type', 'media_type', and 'data' keys, or None on failure
        """
        try:
            response = self._http_client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Check size
            content_length = len(response.content)
            if content_length > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                logger.warning(
                    f"Image too large ({content_length / 1024 / 1024:.1f}MB > {MAX_IMAGE_SIZE_MB}MB): {url}"
                )
                return None

            # Determine media type
            content_type = response.headers.get("content-type", "image/jpeg")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()

            # Map common types
            media_type_map = {
                "image/jpeg": "image/jpeg",
                "image/jpg": "image/jpeg",
                "image/png": "image/png",
                "image/gif": "image/gif",
                "image/webp": "image/webp",
            }
            media_type = media_type_map.get(content_type, "image/jpeg")

            # Encode as base64
            encoded = base64.standard_b64encode(response.content).decode("utf-8")

            return {
                "type": "base64",
                "media_type": media_type,
                "data": encoded,
            }

        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching image {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching image {url}: {e}")
            return None

    def _infer_category_from_context(self, context: str) -> Optional[str]:
        """
        Infer image category from post text context.

        Args:
            context: The post text

        Returns:
            Category string or None if cannot be inferred
        """
        if not context:
            return None

        context_lower = context.lower()

        # Keywords suggesting text_heavy
        text_keywords = [
            "screenshot",
            "code",
            "terminal",
            "snippet",
            "documentation",
            "article",
            "tweet",
            "post",
            "message",
        ]
        if any(kw in context_lower for kw in text_keywords):
            return "text_heavy"

        # Keywords suggesting chart
        chart_keywords = [
            "chart",
            "graph",
            "data",
            "visualization",
            "metrics",
            "stats",
            "statistics",
            "trend",
            "growth",
            "decline",
            "percentage",
            "diagram",
            "flowchart",
        ]
        if any(kw in context_lower for kw in chart_keywords):
            return "chart"

        return None

    def _detect_category(self, image_data: dict) -> str:
        """
        Detect image category using Claude Vision.

        Args:
            image_data: Dict with base64 image data

        Returns:
            Category string (text_heavy, chart, or general)
        """
        try:
            message = self._client.messages.create(
                model=MODEL_NAME,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": image_data,
                            },
                            {
                                "type": "text",
                                "text": CATEGORY_DETECTION_PROMPT,
                            },
                        ],
                    }
                ],
            )

            response_text = message.content[0].text.strip().lower()

            # Parse response
            if "text_heavy" in response_text:
                return "text_heavy"
            elif "chart" in response_text:
                return "chart"
            else:
                return "general"

        except Exception as e:
            logger.warning(f"Category detection failed, defaulting to general: {e}")
            return "general"

    def _extract_description(
        self,
        image_data: dict,
        context: str,
        category: str,
    ) -> str:
        """
        Extract description using category-appropriate prompt.

        Args:
            image_data: Dict with base64 image data
            context: Optional post context
            category: Image category

        Returns:
            Extracted description string
        """
        prompt = get_extraction_prompt(category, context)

        try:
            message = self._client.messages.create(
                model=MODEL_NAME,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": image_data,
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            return message.content[0].text.strip()

        except Exception as e:
            logger.error(f"Description extraction failed: {e}")
            return f"[Image extraction failed: {category}]"

    def close(self):
        """Close the HTTP client."""
        self._http_client.close()


def get_image_extractor() -> ImageExtractor:
    """Get the singleton image extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = ImageExtractor()
    return _extractor
