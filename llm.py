"""
llm.py — Provider-agnostic completion layer for HoodaAgents.

One function, complete(prompt, provider), routes to OpenAI (Responses API) or
Anthropic (Messages API). Model IDs come from env vars so they can be bumped
without a code change:

    OPENAI_MODEL      (default: gpt-5.4-mini)
    ANTHROPIC_MODEL   (default: claude-sonnet-5)

Keys:
    OPENAI_API_KEY  for provider="openai"
    ANTHROPIC_API_KEY for provider="anthropic"/"claude"
"""

import os

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

PROVIDERS = ("openai", "anthropic")


def normalize_provider(p):
    p = (p or "openai").lower()
    return "anthropic" if p in ("anthropic", "claude") else "openai"


def complete(prompt, provider="openai", system=None):
    """Return the model's text output for a single prompt."""
    if normalize_provider(provider) == "anthropic":
        return _anthropic(prompt, system)
    return _openai(prompt, system)


def _openai(prompt, system):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    kwargs = {"model": OPENAI_MODEL, "input": prompt}
    if system:
        kwargs["instructions"] = system
    resp = client.responses.create(**kwargs)
    return resp.output_text


def _anthropic(prompt, system):
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    kwargs = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": _MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
