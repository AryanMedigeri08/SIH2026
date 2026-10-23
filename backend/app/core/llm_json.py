"""Read JSON objects from supported chat-provider function calls or text replies."""
from __future__ import annotations

import json
from typing import Any


def response_object(content: str, tool_call: dict[str, Any] | None, expected_tool: str) -> dict:
    if tool_call and tool_call.get("name") == expected_tool:
        value = tool_call.get("arguments")
        if isinstance(value, str):
            value = json.loads(value)
    else:
        text = (content or "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].lstrip()
        # Some providers append a closing fence/explanation after a valid object.
        value, _ = json.JSONDecoder().raw_decode(text)
    if not isinstance(value, dict):
        raise ValueError("Expected a structured JSON object")
    return value


def structured_response_format(model_type, name: str) -> dict:
    """Inline schema references for providers with limited nested tool support."""
    schema = model_type.model_json_schema()
    definitions = schema.get("$defs", {})
    def expand(value):
        if isinstance(value, list):
            return [expand(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return expand({**definitions[value["$ref"].rsplit("/", 1)[-1]],
                           **{key: item for key, item in value.items() if key != "$ref"}})
        result = {key: expand(item) for key, item in value.items() if key not in {"$defs", "default", "title"}}
        if result.get("type") == "object":
            result["additionalProperties"] = False
            result["required"] = list(result.get("properties", {}))
        return result
    return {"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": expand(schema)}}
