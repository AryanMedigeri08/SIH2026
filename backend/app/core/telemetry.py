"""
telemetry.py — Correlation Tracing, Latency Measurement, and Structured Telemetry.

Document 3, Gates 20, 21, 24.
Production observability:
    - Distributed tracing via X-Correlation-ID / X-Request-ID propagation.
    - Accurate latency tracking via X-Response-Time-ms.
    - Structured access logging with PII sanitization.
"""

from __future__ import annotations
import json
import logging
import re
import time
import uuid
from typing import Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("udyam_saathi.telemetry")

# Sensitive key patterns to sanitize from logs (PII & secrets)
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"aadhaar", re.IGNORECASE),
    re.compile(r"pan", re.IGNORECASE),
    re.compile(r"phone", re.IGNORECASE),
    re.compile(r"mobile", re.IGNORECASE),
    re.compile(r"api[-_]?key", re.IGNORECASE),
]


def sanitize_value(key: str, val: Any) -> Any:
    """Mask sensitive string values if key matches sensitive patterns."""
    if any(p.search(key) for p in SENSITIVE_KEY_PATTERNS):
        if isinstance(val, str) and len(val) > 4:
            return f"***{val[-4:]}"
        return "***REDACTED***"
    if isinstance(val, dict):
        return {k: sanitize_value(k, v) for k, v in val.items()}
    if isinstance(val, list):
        return [sanitize_value(key, item) for item in val]
    return val


def sanitize_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Sanitize dictionary keys and values for log output."""
    return {k: sanitize_value(k, v) for k, v in d.items()}


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches correlation IDs, tracks request duration,
    adds trace headers, and emits structured access logs.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Resolve or generate Correlation ID
        incoming_cid = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        correlation_id = incoming_cid.strip() if incoming_cid else f"CID-{uuid.uuid4().hex[:12].upper()}"

        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id

        # 2. Timing
        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"

        # Log incoming request
        sanitized_params = sanitize_dict(dict(request.query_params))
        logger.info(
            f"[{correlation_id}] ➡️ INCOMING {request.method} {request.url.path} "
            f"from {client_host} | params={sanitized_params}"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Attach tracing and latency headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = correlation_id
            response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"

            logger.info(
                f"[{correlation_id}] ⬅️ RESPONSE {response.status_code} "
                f"{request.method} {request.url.path} in {duration_ms:.2f}ms"
            )
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"[{correlation_id}] ❌ ERROR in {duration_ms:.2f}ms on {request.method} {request.url.path}: {exc}",
                exc_info=True,
            )
            raise exc
