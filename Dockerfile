# ============================================================================
# Udyam Saathi — Backend Dockerfile (Root Entrypoint for Cloud Run)
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
COPY data /app/data
COPY models /app/models
COPY dpr_generator.py /app/
COPY financial_calculator.py /app/
COPY market_analyzer.py /app/
COPY risk_analyzer.py /app/
COPY swot_analyzer.py /app/
COPY pricing_engine.py /app/
COPY .env.example /app/.env.example

RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
