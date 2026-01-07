from __future__ import annotations
import os
import requests

# This uses the OpenAI Responses API (recommended for new projects).
# Docs: https://platform.openai.com/docs/api-reference/responses

OPENAI_BASE = "https://api.openai.com/v1/responses"

def dd_note_from_context(context: dict, model: str | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    model = model or os.getenv("OPENAI_MODEL", "gpt-5.2")

    instructions = """You are an analyst generating a DD memo for a short-horizon trade candidate.
Return markdown with:
- Recommendation tier: Favorable, Neutral, Unfavorable
- Confidence: Low, Medium, High
- Setup fit: earnings anticipation or post-earnings continuation
- Key positives (bullets)
- Key risks (bullets), especially dilution and financing
- What would invalidate the thesis (bullets)
Do not predict price targets. Do not mention placing trades.
"""

    payload = {
        "model": model,
        "input": [
            {"role": "developer", "content": instructions},
            {"role": "user", "content": f"Context JSON:\n{context}"},
        ],
        "max_output_tokens": 800,
    }
    r = requests.post(
        OPENAI_BASE,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    # Responses API returns an output array. We'll join text parts.
    out = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out.append(c.get("text", ""))
    return "\n".join(out).strip()
