#!/bin/bash

# Test script for V2 API features

echo "PresentOn V2 API Test Suite"
echo "=========================="
echo ""

# Base URL
BASE_URL="http://localhost:8000"

# Test 1: Get available models
echo "1. Testing available models endpoint..."
curl -X GET "$BASE_URL/api/v2/ppt/models" \
  -H "Content-Type: application/json" | jq '.'
echo ""

# Test 2: Generate presentation with compact mode
echo "2. Testing presentation generation with COMPACT mode..."
curl -X POST "$BASE_URL/api/v2/ppt/generate/presentation" \
  -F "prompt=Introduction to Renewable Energy Sources" \
  -F "n_slides=5" \
  -F "language=English" \
  -F "theme=light" \
  -F "slide_mode=compact" \
  -F "export_as=pptx"
echo -e "\n"

# Test 3: Generate presentation with detailed mode and specific model
echo "3. Testing presentation generation with DETAILED mode and specific model..."
curl -X POST "$BASE_URL/api/v2/ppt/generate/presentation" \
  -F "prompt=Deep dive into Machine Learning algorithms and their applications" \
  -F "n_slides=10" \
  -F "language=English" \
  -F "theme=dark" \
  -F "slide_mode=detailed" \
  -F "model=gpt-4o" \
  -F "export_as=pptx"
echo -e "\n"

# Test 4: Generate presentation with Flux image generation
echo "4. Testing presentation with Flux image generation..."
curl -X POST "$BASE_URL/api/v2/ppt/generate/presentation" \
  -F "prompt=The Future of Space Exploration" \
  -F "n_slides=6" \
  -F "language=English" \
  -F "theme=royal_blue" \
  -F "slide_mode=normal" \
  -F "image_provider=flux" \
  -F "flux_model=dev" \
  -F "export_as=pptx"
echo -e "\n"

# Test 5: Test with invalid model
echo "5. Testing error handling with invalid model..."
curl -X POST "$BASE_URL/api/v2/ppt/generate/presentation" \
  -F "prompt=Test presentation" \
  -F "n_slides=5" \
  -F "language=English" \
  -F "theme=light" \
  -F "slide_mode=normal" \
  -F "model=invalid-model-123" \
  -F "export_as=pptx"
echo -e "\n"

echo "V2 API tests completed!"