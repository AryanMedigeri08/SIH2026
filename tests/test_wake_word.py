"""
Unit tests for 'Hey Siri' Wake-Word Regex and Trailing Query Extraction
Matches the exact JavaScript logic implemented in frontend/src/hooks/useWakeWord.js
"""
import re
import pytest

WAKE_WORD_REGEX = re.compile(
    r"\b(?:hey|hay|ay|hello|hi|ok|okay)?\s*(?:siri|seeree|sery|ciri|serious|sarah)\b",
    re.IGNORECASE
)
SAATHI_ALIAS_REGEX = re.compile(
    r"\b(?:hey|namaste|hello|ok)?\s*(?:saathi|sathi|udyam)\b",
    re.IGNORECASE
)

def match_wake_word(text: str) -> bool:
    if not text:
        return False
    return bool(WAKE_WORD_REGEX.search(text) or SAATHI_ALIAS_REGEX.search(text))

def extract_trailing_prompt(full_text: str) -> str:
    if not full_text:
        return ""
    m = WAKE_WORD_REGEX.search(full_text)
    if not m:
        m = SAATHI_ALIAS_REGEX.search(full_text)
    if not m:
        return ""
    match_end = m.end()
    trailing = full_text[match_end:].lstrip(" ,.").strip()
    return trailing

class TestWakeWordDetection:
    @pytest.mark.parametrize("phrase,expected_match,expected_prompt", [
        ("Hey Siri", True, ""),
        ("hey siri", True, ""),
        ("HEY SIRI", True, ""),
        ("Hello Siri", True, ""),
        ("ok siri", True, ""),
        ("Siri", True, ""),
        ("hey siri what is dairy demand in Thane", True, "what is dairy demand in Thane"),
        ("Hey Siri, summarize this page for me", True, "summarize this page for me"),
        ("Namaste Saathi", True, ""),
        ("hey saathi show me MSMEs in Pune", True, "show me MSMEs in Pune"),
        ("Just a normal conversation without triggers", False, ""),
        ("Today is a sunny Saturday morning", False, ""),
    ])
    def test_wake_word_matching_and_extraction(self, phrase, expected_match, expected_prompt):
        assert match_wake_word(phrase) == expected_match
        if expected_match:
            assert extract_trailing_prompt(phrase) == expected_prompt
