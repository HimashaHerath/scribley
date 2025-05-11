# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Scribley Team"
LABEL description="Medium automation tool"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install application
COPY . .
RUN pip install -e .

# Create data directory for SQLite
RUN mkdir -p data

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["python", "run_server.py"] 