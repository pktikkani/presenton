#!/bin/bash

# Start Redis
redis-server --daemonize yes

# Start FastAPI server (serves both V1 and V2 endpoints)
cd /app/servers/fastapi
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start Next.js V1 server
cd /app/servers/nextjs
npm start &

# Start Next.js V2 server on port 3001
cd /app/servers/nextjs-v2
npm start &

# Start nginx
nginx -g 'daemon off;'