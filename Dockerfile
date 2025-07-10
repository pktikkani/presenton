# Use the pre-built image as base
FROM ghcr.io/presenton/presenton:latest

# Copy our modified files
COPY servers/fastapi/image_processor/images_finder.py /app/servers/fastapi/image_processor/images_finder.py
COPY servers/fastapi/api/routers/presentation/handlers/generate_stream.py /app/servers/fastapi/api/routers/presentation/handlers/generate_stream.py
COPY servers/fastapi/api/routers/presentation/handlers/generate_presentation.py /app/servers/fastapi/api/routers/presentation/handlers/generate_presentation.py
COPY servers/fastapi/api/routers/presentation/models.py /app/servers/fastapi/api/routers/presentation/models.py
COPY servers/fastapi/api/routers/presentation/mixins/fetch_assets_on_generation.py /app/servers/fastapi/api/routers/presentation/mixins/fetch_assets_on_generation.py
COPY servers/fastapi/api/utils/model_utils.py /app/servers/fastapi/api/utils/model_utils.py
COPY servers/fastapi/ppt_generator/generator.py /app/servers/fastapi/ppt_generator/generator.py

COPY servers/nextjs/app/\(presentation-generator\)/utils/language-helper.ts /app/servers/nextjs/app/\(presentation-generator\)/utils/language-helper.ts
COPY servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type2Layout.tsx /app/servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type2Layout.tsx
COPY servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type6Layout.tsx /app/servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type6Layout.tsx
COPY servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type9Layout.tsx /app/servers/nextjs/app/\(presentation-generator\)/components/slide_layouts/Type9Layout.tsx

# Rebuild Next.js app with the updated files
WORKDIR /app/servers/nextjs
RUN npm run build

WORKDIR /app

# Create user_data directory for storing presentations and settings
RUN mkdir -p /app/user_data && chmod 777 /app/user_data

# The rest remains the same
