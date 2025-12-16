# Congressional Data Poller Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy poller code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Copy the enhanced scheduler script
COPY scheduler.py /app/scheduler.py

# Health check
HEALTHCHECK --interval=5m --timeout=30s --retries=3 \
    CMD ls -la /app/data/analysis/comprehensive_report.json 2>/dev/null || exit 1

# Default: run scheduler
CMD ["python", "scheduler.py"]