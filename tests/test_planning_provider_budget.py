"""Provider budget and cache isolation for local planning appraisals."""
from unittest.mock import Mock

from tests.test_planning_financial_baseline import frozen_evidence  # initializes core import paths
from app.core import enterprise_planning as planner
import executive_synthesizer as synthesis


def test_idea_client_disables_provider_retries(monkeypatch):
    import groq
    client = object()
    factory = Mock(return_value=client)
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-unit-test-placeholder")
    monkeypatch.setattr(groq, "Groq", factory)
    assert planner._get_groq_client() is client
    assert factory.call_args.kwargs["max_retries"] == 0
    assert factory.call_args.kwargs["timeout"] == 12.0


def test_forced_local_narrative_does_not_replace_ai_enabled_cache():
    payload = {"enterprise_name": "Synthetic planning cache isolation test", "sector": "dairy"}
    cache = synthesis.SynthesisCache()
    key = cache.compute_hash(payload, "en")
    cache.set(key, synthesis.ExecutiveSynthesis(
        "Existing AI narrative", [], "Existing memo", "en", False, False, 0, "test-ai", key,
    ))
    result = synthesis.generate_executive_synthesis(payload, force_fallback=True)
    assert result.is_fallback is True
    assert cache.get(key).executive_summary == "Existing AI narrative"
    assert cache.get(key).is_fallback is False
