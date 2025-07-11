# PresentOn V2 Features

This document describes the enhanced features available in the V2 API endpoints.

## Overview

The V2 API provides several enhancements over V1:
- Dynamic model selection with validation
- Enhanced slide modes (compact, normal, detailed)
- Multiple image generation providers including Flux
- Better content generation based on slide mode

## API Endpoints

### 1. Get Available Models
```bash
GET /api/v2/ppt/models
```

Returns list of available models for the current LLM provider.

**Response:**
```json
{
  "provider": "openai",
  "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  "default_model": "gpt-4o"
}
```

### 2. Generate Presentation (Enhanced)
```bash
POST /api/v2/ppt/generate/presentation
```

**Form Parameters:**
- `prompt` (required): Main presentation topic
- `n_slides`: Number of slides (3-20, default: 8)
- `language`: Language for presentation (default: "English")
- `theme`: Visual theme (light, dark, royal_blue, cream, light_red, dark_pink, faint_yellow)
- `slide_mode`: Content density mode (compact, normal, detailed)
- `model`: Specific LLM model to use (optional, validated against available models)
- `image_provider`: Image generation provider (openai, google, flux, pexels)
- `flux_model`: Specific Flux model if using Flux (kontext-max, kontext-pro, pro-1.1-ultra, pro-1.1, pro, dev)
- `export_as`: Export format (pptx, pdf)

## Slide Modes

### Compact Mode
- **Word count**: 10-20 words per slide
- **Use case**: Executive summaries, quick overviews
- **Characteristics**:
  - Ultra-concise titles (3-5 words)
  - Minimal body text (1-2 short sentences)
  - Bullet points with keywords only
  - Maximum 3 items per list

### Normal Mode (Default)
- **Word count**: 50-80 words per slide
- **Use case**: Standard business presentations
- **Characteristics**:
  - Clear descriptive titles (6-10 words)
  - Balanced body text (3-5 sentences)
  - Complete sentence bullet points
  - Maximum 5 items per list

### Detailed Mode
- **Word count**: 150-250 words per slide
- **Use case**: Educational content, training materials
- **Characteristics**:
  - Comprehensive titles (up to 15 words)
  - Multiple paragraphs of body text
  - Detailed bullet points with explanations
  - Maximum 8 items per list
  - Includes examples and context

## Model Selection

### OpenAI Models
- `gpt-4o`: Most capable, best for complex content
- `gpt-4o-mini`: Cost-effective for simpler content
- `gpt-4-turbo`: Previous generation, still very capable
- `gpt-3.5-turbo`: Fastest and most economical

### Google Models
- `gemini-2.0-flash`: Fast and efficient
- `gemini-1.5-pro`: More capable for complex tasks
- `gemini-1.5-flash`: Balance of speed and capability

## Image Generation

### Providers

1. **OpenAI (DALL-E 3)**
   - High quality artistic images
   - Best for abstract concepts
   - Requires OpenAI API key

2. **Google (Gemini)**
   - Integrated with Google's models
   - Good for diverse image styles
   - Requires Google API key

3. **Flux**
   - Multiple model options for different quality/speed tradeoffs
   - Requires BFL_API_KEY
   - Models:
     - `dev`: Development model, fastest and cheapest ($0.025/image)
     - `pro`: Professional quality ($0.05/image)
     - `pro-1.1`: Enhanced professional ($0.04/image)
     - `pro-1.1-ultra`: Highest quality ($0.06/image)
     - `kontext-pro`: Specialized model ($0.04/image)
     - `kontext-max`: Maximum context ($0.08/image)

4. **Pexels**
   - Stock photos
   - Free with API key
   - Best for real-world imagery

## Examples

### Compact Executive Summary
```bash
curl -X POST http://localhost:8000/api/v2/ppt/generate/presentation \
  -F "prompt=Q4 2024 Financial Results Summary" \
  -F "n_slides=5" \
  -F "slide_mode=compact" \
  -F "model=gpt-4o-mini"
```

### Detailed Training Material
```bash
curl -X POST http://localhost:8000/api/v2/ppt/generate/presentation \
  -F "prompt=Complete Guide to Python Programming for Beginners" \
  -F "n_slides=15" \
  -F "slide_mode=detailed" \
  -F "model=gpt-4o" \
  -F "image_provider=flux" \
  -F "flux_model=pro"
```

### Standard Presentation with Specific Model
```bash
curl -X POST http://localhost:8000/api/v2/ppt/generate/presentation \
  -F "prompt=Digital Transformation Strategy" \
  -F "n_slides=8" \
  -F "slide_mode=normal" \
  -F "model=gpt-4-turbo" \
  -F "theme=royal_blue"
```

## Environment Variables

### For Flux Image Generation
```bash
export BFL_API_KEY="your-flux-api-key"
export FLUX_MODEL="dev"  # Default Flux model
export FLUX_RAW_MODE="false"  # For ultra model
```

### For Model Selection
```bash
export LLM="openai"  # or "google"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
```

## Migration from V1

The V2 API is backward compatible. V1 endpoints continue to work as before. To use V2 features:

1. Change endpoint from `/api/v1/ppt/` to `/api/v2/ppt/`
2. Add optional parameters as needed
3. V1 parameters work the same in V2

## Error Handling

V2 provides enhanced error messages:
- Invalid model names return list of available models
- Validation errors include specific field issues
- Image generation failures fall back gracefully

## Performance Considerations

- **Compact mode**: Uses smaller models by default for cost efficiency
- **Detailed mode**: Uses larger models for better quality
- **Model validation**: Cached for 1 hour to reduce API calls
- **Image generation**: Parallel processing for multiple images