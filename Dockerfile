FROM python:3.11-slim-bookworm

# Install Node.js and npm and build dependencies
RUN apt-get update && apt-get install -y \
    nodejs \  
    npm \
    nginx \
    curl \
    redis-server \
    build-essential \
    pkg-config \
    libssl-dev \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Add Rust to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Create a working directory
WORKDIR /app  

# Set environment variables
ENV APP_DATA_DIRECTORY=/app/user_data
ENV TEMP_DIRECTORY=/tmp/presenton

# Install ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install dependencies for FastAPI
COPY servers/fastapi/requirements.txt ./
# Install maturin first for building Rust-based packages
RUN pip install maturin
RUN pip install -r requirements.txt

# Manually build and install fastembed-vectorstore
RUN git clone https://github.com/sauravniraula/fastembed_vectorstore /tmp/fastembed_vectorstore && \
    cd /tmp/fastembed_vectorstore && \
    maturin develop --release && \
    rm -rf /tmp/fastembed_vectorstore

# Install dependencies for Next.js
WORKDIR /app/servers/nextjs
COPY servers/nextjs/package.json servers/nextjs/package-lock.json ./
RUN npm install

# Install chrome for puppeteer
RUN npx puppeteer browsers install chrome --install-deps

# Copy Next.js app
COPY servers/nextjs/ /app/servers/nextjs/

# Build the Next.js app
WORKDIR /app/servers/nextjs
RUN npm run build

WORKDIR /app

# Copy FastAPI and start script
COPY servers/fastapi/ ./servers/fastapi/
COPY start.js LICENSE NOTICE ./

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy start script
COPY docker-start.sh /app/docker-start.sh

# Expose the port
EXPOSE 80

# Start the servers
CMD ["/bin/bash", "/app/docker-start.sh"]