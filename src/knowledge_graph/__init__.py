"""
Knowledge Graph Module - Entity and thesis detection for posts.

Provides AI-powered analysis to detect entities and theses mentioned in posts,
building a knowledge graph of related concepts.
"""

from .analyzer import PostAnalyzer, get_post_analyzer
from .config import ANALYSIS_CONFIG

__all__ = ["PostAnalyzer", "get_post_analyzer", "ANALYSIS_CONFIG"]
