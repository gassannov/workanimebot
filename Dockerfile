# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy anipy-cli directory (required for local editable dependency)
COPY anipy-cli/ ./anipy-cli/

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy the bot source code
COPY bot/ ./bot/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot using uv
CMD ["uv", "run", "python", "-m", "bot"]