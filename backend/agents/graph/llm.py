"""Centralized LLM client and structured-output helpers for the CS agent.

Every node in the agent graph talks to the same provider (Ilmu AI) through
``get_chat_client`` / ``CHAT_MODEL`` so the model can be swapped in one place.
"""

import json
import os
import re

from openai import OpenAI

ILMU_BASE_URL = os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1")
CHAT_MODEL = os.getenv("AGENT_CHAT_MODEL", "ilmu-glm-5.1")


def get_chat_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at the Ilmu AI gateway."""
    return OpenAI(base_url=ILMU_BASE_URL, api_key=os.getenv("ILMU_API_KEY", ""))


# Backwards-compatible alias used by older imports.
get_ilmu_client = get_chat_client


def parse_llm_json(content: str) -> dict:
    """Parse a JSON object out of an LLM response, tolerating markdown fences."""
    if not content:
        raise ValueError("LLM returned empty content")

    content = content.strip()

    # Extract from a ```json ... ``` block if present.
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)

    # Fall back to the first '{' .. last '}' span.
    start_idx = content.find("{")
    end_idx = content.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        content = content[start_idx:end_idx + 1]

    return json.loads(content)


def format_tool_to_openai(tool) -> dict:
    """Convert a LangChain tool into an OpenAI function-tool definition."""
    if hasattr(tool, "args_schema") and tool.args_schema:
        if hasattr(tool.args_schema, "model_json_schema"):
            parameters = tool.args_schema.model_json_schema()
        else:
            parameters = tool.args_schema.schema()
    else:
        parameters = {"type": "object", "properties": {}}

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters,
        },
    }
