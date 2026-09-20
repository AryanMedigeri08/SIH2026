"""
action_registry.py — Single Source of Truth for Voice-Triggerable UI Actions.

Shared between the Groq tool-calling schema (backend) and the frontend
action dispatcher (via the API response's tool_call field).

Architecture: This file is consumed by chat_service.py when building the
Groq API call's `tools` parameter.  The frontend ChatContext.jsx mirrors
these action names in its dispatcher map.
"""

from __future__ import annotations

# OpenAI-compatible tool-calling schema for Groq
ACTION_REGISTRY_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to_tab",
            "description": "Switch the user's dashboard view to a different section/tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tab": {
                        "type": "string",
                        "enum": [
                            "business_plan",
                            "govt_schemes",
                            "dashboard",
                            "dpr",
                            "risk_analysis",
                        ],
                    }
                },
                "required": ["tab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_language",
            "description": (
                "Change the dashboard's displayed UI language (text/labels), "
                "independent of the voice agent's spoken language which is "
                "auto-detected per turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["en", "hi", "mr", "ta", "te", "kn"],
                    }
                },
                "required": ["language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_analysis",
            "description": "Re-run the feasibility analysis pipeline for the current project.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_dpr",
            "description": "Trigger the bank-ready DPR export/download flow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["pdf"],
                    }
                },
            },
        },
    },
]

# Flat list of action names for quick validation
ACTION_NAMES = [tool["function"]["name"] for tool in ACTION_REGISTRY_SCHEMA]
