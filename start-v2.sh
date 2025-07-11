#!/bin/bash

echo "Starting PresentOn V2 Servers..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Start FastAPI server
echo -e "${BLUE}Starting FastAPI server with V2 endpoints...${NC}"
cd servers/fastapi
source venv/bin/activate 2>/dev/null || source env/bin/activate 2>/dev/null || echo "No virtual environment found, using system Python"
uvicorn main:app --reload --port 8000 &
FASTAPI_PID=$!

# Wait a moment for FastAPI to start
sleep 3

# Start Next.js V2 server
echo -e "${BLUE}Starting Next.js V2 server on port 3001...${NC}"
cd ../nextjs-v2
npm run dev &
NEXTJS_PID=$!

echo -e "${GREEN}✓ V2 servers started!${NC}"
echo ""
echo "Access points:"
echo "- Next.js V2 Frontend: http://localhost:3001"
echo "- V2 Test Page: http://localhost:3001/v2-test"
echo "- FastAPI Docs: http://localhost:8000/docs"
echo "- V2 API Endpoints: http://localhost:8000/api/v2/ppt/*"
echo ""
echo "Process IDs:"
echo "- FastAPI: $FASTAPI_PID"
echo "- Next.js: $NEXTJS_PID"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
trap "echo 'Stopping servers...'; kill $FASTAPI_PID $NEXTJS_PID; exit" INT
wait