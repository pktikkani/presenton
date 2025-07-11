from typing import Dict, Any

# Slide mode configuration with character limits and generation guidelines
SLIDE_MODE_LIMITS = {
    "compact": {
        "title": {"min": 10, "max": 50},
        "body": {"min": 30, "max": 200},
        "description": {"min": 20, "max": 100},
        "item_title": {"min": 5, "max": 30},
        "item_description": {"min": 20, "max": 80},
        "image_prompt": {"min": 10, "max": 80},
        "icon_query": {"min": 10, "max": 30},
        "max_items": 3,
        "word_count_guide": "15-30 words per slide"
    },
    "normal": {
        "title": {"min": 10, "max": 80},
        "body": {"min": 50, "max": 300},
        "description": {"min": 50, "max": 120},
        "item_title": {"min": 10, "max": 40},
        "item_description": {"min": 50, "max": 120},
        "image_prompt": {"min": 10, "max": 100},
        "icon_query": {"min": 10, "max": 40},
        "max_items": 5,
        "word_count_guide": "40-60 words per slide"
    },
    "detailed": {
        "title": {"min": 10, "max": 120},
        "body": {"min": 100, "max": 1000},
        "description": {"min": 100, "max": 300},
        "item_title": {"min": 10, "max": 80},
        "item_description": {"min": 100, "max": 300},
        "image_prompt": {"min": 10, "max": 150},
        "icon_query": {"min": 10, "max": 60},
        "max_items": 8,
        "word_count_guide": "120-180 words per slide"
    }
}

def get_slide_mode_prompt(mode: str) -> str:
    """Get LLM prompt instructions for specific slide mode"""
    prompts = {
        "compact": """
Generate VERY BRIEF and CONCISE content:
- Title: Maximum 6 words, straight to the point
- Body: 2-3 short sentences (15-30 words total)
- Bullet points: 3-5 words each, key concepts only
- Focus: Essential information only, no elaboration
- Style: Crisp, minimal, high-impact phrases
""",
        
        "normal": """
Generate BALANCED content:
- Title: 6-10 words, clear and descriptive
- Body: 3-4 sentences (40-60 words total)
- Bullet points: One complete line each
- Focus: Good balance of detail and clarity
- Style: Professional, informative, well-structured
""",
        
        "detailed": """
Generate COMPREHENSIVE and THOROUGH content:
- Title: Can be descriptive (up to 15 words)
- Body: Full paragraph with 8-10 sentences (120-180 words)
- Bullet points: Can include explanations and examples
- Focus: In-depth coverage with context and examples
- Style: Educational, detailed, thorough explanations
- Include: Background information, examples, implications
"""
    }
    return prompts.get(mode, prompts["normal"])

def get_limits_for_mode(mode: str) -> Dict[str, Any]:
    """Get character limits for a specific slide mode"""
    return SLIDE_MODE_LIMITS.get(mode, SLIDE_MODE_LIMITS["normal"])