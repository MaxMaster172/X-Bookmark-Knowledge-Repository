"""
Vision extraction prompts for different image categories.

Categories:
- text_heavy: Screenshots, code snippets, text-based images
- chart: Graphs, charts, data visualizations
- general: Photos, illustrations, memes
"""

# Prompt to classify the image category
CATEGORY_DETECTION_PROMPT = """Classify this image into exactly one category:

1. text_heavy - Screenshots of text, code snippets, terminal output, articles, documentation
2. chart - Graphs, charts, diagrams, data visualizations, flowcharts
3. general - Photos, illustrations, memes, artwork, screenshots with minimal text

Respond with ONLY the category name: text_heavy, chart, or general"""

# Prompt for text-heavy images (screenshots, code, articles)
TEXT_HEAVY_PROMPT = """You are extracting text content from a screenshot or text-based image.

Your task: Transcribe ALL visible text verbatim, preserving the structure.

Guidelines:
- Include ALL text you can see, even if partially visible
- Preserve formatting (headers, bullet points, code blocks)
- For code: include syntax exactly as shown
- For articles/tweets: capture the full text content
- Note any UI elements that provide context (e.g., "Twitter post", "Terminal output")

If this is a code snippet, wrap it in appropriate markdown code blocks.

Provide the complete transcription:"""

# Prompt for charts and visualizations
CHART_PROMPT = """You are analyzing a data visualization (chart, graph, or diagram).

Your task: Extract the key information and insights from this visualization.

Include:
1. Type of visualization (bar chart, line graph, pie chart, flowchart, etc.)
2. Title/labels if visible
3. Key data points or trends
4. The main insight or message the visualization conveys
5. Any notable patterns, outliers, or comparisons

Be specific about numbers and percentages when visible.

Describe the visualization and its insights:"""

# Prompt for general images (photos, illustrations)
GENERAL_PROMPT = """You are describing an image for a knowledge archive.

Your task: Provide a semantic description that will help this image be found through search.

Include:
1. Main subject(s) of the image
2. Key visual elements and composition
3. Any text visible in the image
4. Context clues (setting, time period, mood)
5. Why this image might be saved as a reference

Focus on searchable, descriptive terms.

Describe the image:"""


def get_extraction_prompt(category: str, post_context: str = None) -> str:
    """
    Get the appropriate extraction prompt for a category.

    Args:
        category: One of 'text_heavy', 'chart', or 'general'
        post_context: Optional context from the post text

    Returns:
        The extraction prompt string
    """
    prompts = {
        "text_heavy": TEXT_HEAVY_PROMPT,
        "chart": CHART_PROMPT,
        "general": GENERAL_PROMPT,
    }

    base_prompt = prompts.get(category, GENERAL_PROMPT)

    # Add context if available
    if post_context:
        context_addition = f"\n\nContext from the post: {post_context[:500]}"
        return base_prompt + context_addition

    return base_prompt
