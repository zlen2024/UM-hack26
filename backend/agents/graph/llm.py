"""Centralized LLM client and structured-output helpers for the CS agent.

The agent talks to an OpenAI-compatible chat endpoint. Provider, model, and key
are all environment-configurable so the backend can point at any compatible
gateway (opencode zen / DeepSeek, Ilmu, OpenAI, OpenRouter, ...) without code
changes.
"""

import json
import os
import re

from openai import OpenAI

# Provider endpoint (OpenAI-compatible). NOTE: this is the base URL only — the
# SDK appends "/chat/completions" itself, so do NOT include that suffix here.
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("ILMU_BASE_URL")  # backwards compatibility
    or "https://opencode.ai/zen/v1"
)

# Model id served by the provider above.
CHAT_MODEL = os.getenv("AGENT_CHAT_MODEL", "deepseek-v4-flash-free")


def _api_key() -> str:
    return (
        os.getenv("LLM_API_KEY")
        or os.getenv("ILMU_API_KEY")  # backwards compatibility
        or os.getenv("OPENAI_API_KEY")
        or ""
    )


def get_chat_client() -> OpenAI:
    """Return an OpenAI-compatible client for the configured provider."""
    return OpenAI(base_url=LLM_BASE_URL, api_key=_api_key())


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


def complete_json(messages, *, schema=None, schema_name="response",
                  max_tokens=2000, temperature=0) -> dict:
    """Get a JSON object from the chat model, degrading response_format support.

    Providers vary in what structured-output modes they support. We try, in
    order: strict ``json_schema`` (if a schema is given), then ``json_object``,
    then no ``response_format`` at all (relying on the prompt + ``parse_llm_json``).
    The first attempt that returns parseable JSON wins.
    """
    client = get_chat_client()

    formats = []
    if schema is not None:
        formats.append({
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        })
    formats.append({"type": "json_object"})
    formats.append(None)

    last_error = None
    for response_format in formats:
        try:
            kwargs = {
                "model": CHAT_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
            response = client.chat.completions.create(**kwargs)
            return parse_llm_json(response.choices[0].message.content)
        except Exception as e:  # unsupported format, parse error, or API error
            last_error = e
            continue

    raise last_error if last_error else RuntimeError("complete_json failed")


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
