FROM python:3.11-slim

# SECURITY: Create non-root user
RUN groupadd -r clinichub && useradd -r -g clinichub clinichub

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# SECURITY: Create logs directory with proper permissions
RUN mkdir -p logs && chown -R clinichub:clinichub /app

# SECURITY: Switch to non-root user
USER clinichub

# Expose port
EXPOSE 8001

# Health check (updated for production)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# SECURITY: Production command without --reload
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]