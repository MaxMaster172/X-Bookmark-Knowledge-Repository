"""
Vision module for image content extraction.

Provides:
- ImageExtractor: Claude Vision API wrapper for semantic image descriptions
- get_image_extractor: Singleton accessor
"""

from .extractor import ImageExtractor, get_image_extractor

__all__ = ["ImageExtractor", "get_image_extractor"]
