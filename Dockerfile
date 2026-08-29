# ============================================================================
# Udyam Saathi — Root Dockerfile for Google Cloud Run / Container Registry
# ============================================================================
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY data* /app/data/
COPY models* /app/models/
COPY government_schemes.json district_resources.json growth_rates.json model_metadata.json /app/
COPY viability_xgb.joblib /app/
COPY dpr_generator.py financial_calculator.py market_analyzer.py risk_analyzer.py swot_analyzer.py pricing_engine.py /app/
COPY .env.example /app/.env.example

RUN mkdir -p /app/backend/app/data && \
    useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v2/health || exit 1

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
