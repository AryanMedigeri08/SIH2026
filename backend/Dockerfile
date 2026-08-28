# ============================================================================
# Udyam Saathi — Backend Dockerfile (Python 3.11 Slim + Non-Root User)
# ============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8000

WORKDIR /app

# Install system dependencies needed for compiling C extensions & SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase, core modules, schemas, data catalogs & pre-trained ML models
COPY backend /app/backend
COPY data /app/data
COPY models /app/models
COPY dpr_generator.py /app/
COPY financial_calculator.py /app/
COPY market_analyzer.py /app/
COPY risk_analyzer.py /app/
COPY swot_analyzer.py /app/
COPY pricing_engine.py /app/
COPY .env.example /app/.env.example

# Create dedicated non-root user for container security
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check against production endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v2/health || exit 1

# Start Uvicorn ASGI Server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
