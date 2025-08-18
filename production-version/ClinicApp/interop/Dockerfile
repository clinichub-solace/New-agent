FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r interop && useradd -r -g interop interop

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R interop:interop /app

# Switch to non-root user
USER interop

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the interop worker
CMD ["python", "worker.py"]