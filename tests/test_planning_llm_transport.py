"""Structured output requirements reach both configured chat providers."""
from types import SimpleNamespace
import sys

from backend.app.core import chat_service as chat_module


def test_sarvam_receives_the_requested_response_schema(monkeypatch):
    captured = {}
    schema = {"type": "json_schema", "json_schema": {"name": "test", "schema": {"type": "object"}}}
    monkeypatch.setattr(chat_module.settings, "SARVAM_API_KEY", "synthetic-test-key")
    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, endpoint, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(status_code=200, json=lambda: {"choices": [{"message": {"content": '{"ok":true}'}}]})
    monkeypatch.setattr(chat_module.httpx, "Client", Client)
    content, _, _ = chat_module.chat_service._call_llm_chat_completion(
        messages=[{"role": "user", "content": "Synthetic test"}], response_format=schema, timeout_s=12)
    assert content == '{"ok":true}'
    assert captured["json"]["response_format"] == schema
    assert captured["timeout"] == 12


def test_groq_fallback_receives_the_same_schema_and_timeout(monkeypatch):
    captured = {}
    schema = {"type": "json_schema", "json_schema": {"name": "test", "schema": {"type": "object"}}}
    monkeypatch.setattr(chat_module.settings, "SARVAM_API_KEY", None)
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setattr(chat_module.settings, "GROQ_CHAT_KEY", "synthetic-test-key")
    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}', tool_calls=None))])
    def client(**kwargs):
        captured["client"] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=client))
    content, _, _ = chat_module.chat_service._call_llm_chat_completion(
        messages=[{"role": "user", "content": "Synthetic test"}], response_format=schema, timeout_s=18)
    assert content == '{"ok":true}'
    assert captured["response_format"] == schema
    assert captured["client"]["timeout"] == 18


def test_calculation_mode_prefers_the_configured_reasoning_model(monkeypatch):
    captured = {}
    schema = {"type": "json_schema", "json_schema": {"name": "test", "schema": {"type": "object"}}}
    monkeypatch.setattr(chat_module.settings, "GROQ_API_KEY_LLM", "synthetic-calculation-key")
    monkeypatch.setattr(chat_module.settings, "GROQ_LLM_MODEL", "openai/gpt-oss-20b")
    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))])
    def client(**kwargs):
        captured["client"] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=client))
    monkeypatch.setattr(chat_module.httpx, "Client", lambda **kwargs: (_ for _ in ()).throw(AssertionError("Sarvam should not run")))
    content, _, model = chat_module.chat_service._call_llm_chat_completion(
        messages=[{"role": "user", "content": "Synthetic test"}], calculation_mode=True,
        response_format=schema, timeout_s=18)
    assert content == '{"ok":true}'
    assert model == "groq:openai/gpt-oss-20b"
    assert captured["reasoning_effort"] == "medium"
    assert captured["client"]["max_retries"] == 0
    assert captured["response_format"] == schema
