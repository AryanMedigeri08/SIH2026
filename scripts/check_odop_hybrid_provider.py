"""One manual synthetic provider call; prints metadata, never keys or model text.

Run with the local virtualenv to check the real ODOP request contract. No real
business details or persistent app drafts are used. SDK retries stay disabled.
"""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend"), str(ROOT / "backend/app/core")]

from fastapi import HTTPException
from pydantic import ValidationError
from app.core import odop_hybrid as hybrid
from app.core.odop_hybrid_store import HybridStore
from app.models.odop_hybrid import HybridRequest, HybridAssessment


def validation_issues(error):
    return [{"field": next((part for part in item["loc"] if isinstance(part, str) and part in HybridAssessment.model_fields), "response"),
             "type": item["type"]} for item in error.errors(include_input=False)][:8]


def main():
    client = hybrid._get_groq_client()
    if client is None:
        print(json.dumps({"status": "provider_unconfigured"}))
        return 1
    calls = 0
    original = client.chat.completions.create

    def tracked(**kwargs):
        nonlocal calls
        calls += 1
        try:
            response = original(**kwargs)
        except Exception as error:
            body = getattr(error, "body", None)
            detail = body.get("error", body) if isinstance(body, dict) else {}
            print(json.dumps({"provider_exception": type(error).__name__, "http_status": getattr(error, "status_code", None),
                              "provider_code": detail.get("code") if isinstance(detail, dict) else None}))
            if isinstance(detail, dict):
                # This script uses synthetic data only. Still omit generated text.
                failed = detail.get("failed_generation")
                if isinstance(failed, str):
                    print(json.dumps({"failed_content_characters": len(failed), "starts_as_object": failed.lstrip().startswith('{'), "ends_as_object": failed.rstrip().endswith('}')}))
                    try:
                        HybridAssessment.model_validate_json(failed)
                    except ValidationError as invalid:
                        print(json.dumps({"failed_validation_issues": validation_issues(invalid)}))
            raise
        choice = response.choices[0]
        print(json.dumps({"finish_reason": choice.finish_reason, "content_characters": len(choice.message.content or ""),
                          "completion_tokens": getattr(response.usage, "completion_tokens", None)}))
        try:
            HybridAssessment.model_validate_json(choice.message.content or "")
        except ValidationError as error:
            print(json.dumps({"validation_issues": validation_issues(error)}))
        return response

    wrapped = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=tracked)))
    service = hybrid.HybridEvaluator(HybridStore(SimpleNamespace(pool=None, sqlite=None)))
    request = HybridRequest(consent=True, state_name="West Bengal", district_name="Bankura",
        enterprise_name="Synthetic dairy business", business_category="manufacturing", sector="dairy",
        idea_description="Make curd using local milk and sell to nearby shops.")
    with patch.object(hybrid, "_get_groq_client", return_value=wrapped):
        try:
            result = asyncio.run(service.evaluate("synthetic-provider-check", request))
            print(json.dumps({"status": "ok", "score": result["score"], "band": result["band"], "provider_calls": calls}))
            return 0
        except HTTPException as error:
            print(json.dumps({"status": "unavailable", "http_status": error.status_code, "provider_calls": calls}))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
