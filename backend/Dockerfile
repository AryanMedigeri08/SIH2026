# ============================================================================
# Udyam Saathi — Backend Dockerfile (Python 3.11 Slim + Non-Root Security)
# Optimized for Google Cloud Run, Docker Compose & Microservices Architecture
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

# Copy backend codebase, catalogs, ML models & pipeline modules
COPY backend /app/backend
COPY data* /app/data/
COPY models* /app/models/
COPY government_schemes.json district_resources.json growth_rates.json model_metadata.json /app/
COPY viability_xgb.joblib /app/
COPY dpr_generator.py financial_calculator.py market_analyzer.py risk_analyzer.py swot_analyzer.py pricing_engine.py /app/
COPY .env.example /app/.env.example

# Create SQLite cache data folder and non-root app user
RUN mkdir -p /app/backend/app/data && \
    useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check against production health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v2/health || exit 1

# Start Uvicorn ASGI Server with dynamic Cloud Run PORT binding
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
