# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/timesheets/excel \
    /app/timesheets/pdf \
    /app/salary_slips \
    /app/logs

# Set proper permissions
RUN chmod -R 755 /app

# Expose port (if we add a web interface later)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden for different modes)
# Modes: "batch" (main.py), "api" (backend/api.py)
ENV RUN_MODE=batch

CMD if [ "$RUN_MODE" = "api" ]; then \
        uvicorn backend.api:app --host 0.0.0.0 --port 8000; \
    else \
        python main.py; \
    fi
