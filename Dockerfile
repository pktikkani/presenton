# Use Python base image
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy FastAPI server files
COPY servers/fastapi/ /app/servers/fastapi/

# Create user_data directory for storing presentations
RUN mkdir -p /app/user_data && chmod 777 /app/user_data

# Set environment variables
ENV APP_DATA_DIRECTORY=/app/user_data
ENV PYTHONPATH=/app/servers/fastapi

# Install Python dependencies
WORKDIR /app/servers/fastapi
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for FastAPI
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting API-only server..."\n\
service redis-server start\n\
cd /app/servers/fastapi\n\
python server.py --port 8000' > /app/start-api.sh && \
    chmod +x /app/start-api.sh

# Start the API server
CMD ["/bin/bash", "/app/start-api.sh"]