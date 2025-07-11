"""Enhanced slide mode configuration for V2 with better differentiation"""
from typing import Dict, Any

# Enhanced slide mode configuration with more nuanced limits and prompts
SLIDE_MODE_LIMITS_V2 = {
    "compact": {
        "title": {"min": 5, "max": 40},
        "body": {"min": 20, "max": 150},  # Reduced from 200
        "description": {"min": 15, "max": 80},  # Reduced from 100
        "item_title": {"min": 3, "max": 25},  # Reduced from 30
        "item_description": {"min": 15, "max": 60},  # Reduced from 80
        "image_prompt": {"min": 10, "max": 60},
        "icon_query": {"min": 5, "max": 25},
        "max_items": 3,
        "word_count_guide": "10-20 words per slide",
        "bullet_points": 3,
        "sentences_per_paragraph": 2
    },
    "normal": {
        "title": {"min": 10, "max": 70},
        "body": {"min": 80, "max": 400},  # Increased from 300
        "description": {"min": 60, "max": 150},  # Increased from 120
        "item_title": {"min": 8, "max": 50},
        "item_description": {"min": 60, "max": 150},  # Increased from 120
        "image_prompt": {"min": 15, "max": 100},
        "icon_query": {"min": 10, "max": 40},
        "max_items": 5,
        "word_count_guide": "50-80 words per slide",
        "bullet_points": 5,
        "sentences_per_paragraph": 4
    },
    "detailed": {
        "title": {"min": 15, "max": 100},
        "body": {"min": 200, "max": 1200},  # Increased from 1000
        "description": {"min": 150, "max": 400},  # Increased from 300
        "item_title": {"min": 10, "max": 80},
        "item_description": {"min": 150, "max": 400},  # Increased from 300
        "image_prompt": {"min": 20, "max": 180},
        "icon_query": {"min": 10, "max": 60},
        "max_items": 8,
        "word_count_guide": "150-250 words per slide",
        "bullet_points": 8,
        "sentences_per_paragraph": 6
    }
}

def get_slide_mode_prompt_v2(mode: str) -> str:
    """Enhanced LLM prompt instructions for specific slide mode"""
    prompts = {
        "compact": """
COMPACT MODE - ULTRA CONCISE CONTENT:
- Title: 3-5 words maximum, punchy and direct
- Body: 1-2 very short sentences (10-20 words total)
- Bullet points: 2-4 words each, keywords only
- NO elaboration, NO examples, NO context
- Style: Telegram-like brevity, essential facts only
- Think: Executive summary highlights
- Each slide = One key message
Example bullet point: "Cost reduction"
Example body: "AI reduces operational costs. ROI within 6 months."
""",
        
        "normal": """
NORMAL MODE - BALANCED PROFESSIONAL CONTENT:
- Title: 6-10 words, clear and descriptive
- Body: 3-5 sentences forming a coherent paragraph (50-80 words)
- Bullet points: One complete sentence each (8-15 words)
- Include: Key context and brief explanations
- Style: Business presentation standard
- Balance: Information density with readability
- Each slide = Complete thought with supporting points
Example bullet point: "Implement automated testing to reduce bugs by 40%"
Example body: "Machine learning transforms business operations through intelligent automation. Companies report 30-50% efficiency gains within the first year. Key applications include customer service, data analysis, and predictive maintenance."
""",
        
        "detailed": """
DETAILED MODE - COMPREHENSIVE EDUCATIONAL CONTENT:
- Title: Full descriptive phrase (up to 15 words)
- Body: 2-3 full paragraphs (150-250 words total)
- Bullet points: Complete thoughts with explanations (15-30 words each)
- Include: Background, examples, data, implications, case studies
- Style: Academic or training material depth
- Depth: Assume audience wants thorough understanding
- Each slide = Mini-lesson with complete coverage
Example bullet point: "Cloud migration reduces infrastructure costs by 40% while improving scalability and disaster recovery capabilities"
Example body: "Artificial Intelligence represents a paradigm shift in how businesses operate and compete. Modern AI systems can process vast amounts of data, identify patterns invisible to human analysts, and make predictions with unprecedented accuracy. 

Leading organizations are leveraging AI across multiple domains: customer experience optimization, supply chain management, financial forecasting, and product development. McKinsey reports that AI adoption has increased by 250% since 2020, with early adopters seeing revenue increases of 10-20%.

The key to successful AI implementation lies in strategic planning, quality data, and change management. Organizations must invest in both technology and talent, ensuring their workforce is prepared for AI-augmented operations."
"""
    }
    return prompts.get(mode, prompts["normal"])

def get_content_guidelines_v2(mode: str, slide_type: int) -> Dict[str, Any]:
    """Get specific content guidelines based on mode and slide type"""
    base_limits = SLIDE_MODE_LIMITS_V2.get(mode, SLIDE_MODE_LIMITS_V2["normal"])
    
    # Adjust limits based on slide type
    type_adjustments = {
        1: {"body_multiplier": 1.2},  # Text slides can be longer
        2: {"max_items_multiplier": 1.0},  # List slides standard
        3: {"body_multiplier": 0.8, "max_items_multiplier": 1.2},  # Image slides less text
        4: {"max_items_multiplier": 0.8},  # Timeline slides fewer items
        5: {"body_multiplier": 0.6},  # Funnel slides minimal text
        6: {"body_multiplier": 0.5},  # Quadrant slides very minimal
        7: {"body_multiplier": 0.7},  # Comparison slides moderate text
        8: {"body_multiplier": 0.6},  # Stats slides minimal text
        9: {"body_multiplier": 0.8},  # Quote slides moderate text
    }
    
    adjustments = type_adjustments.get(slide_type, {})
    
    # Apply adjustments
    adjusted_limits = base_limits.copy()
    if "body_multiplier" in adjustments:
        adjusted_limits["body"]["max"] = int(base_limits["body"]["max"] * adjustments["body_multiplier"])
    if "max_items_multiplier" in adjustments:
        adjusted_limits["max_items"] = int(base_limits["max_items"] * adjustments["max_items_multiplier"])
    
    return adjusted_limits

def get_system_prompt_for_mode(mode: str) -> str:
    """Get system-level prompt to set the tone for content generation"""
    system_prompts = {
        "compact": "You are creating a high-impact executive presentation. Every word must count. Be extremely concise.",
        "normal": "You are creating a professional business presentation. Balance clarity with completeness.",
        "detailed": "You are creating an educational presentation. Provide comprehensive information with examples and context."
    }
    return system_prompts.get(mode, system_prompts["normal"])