"""Optional review pass through any OpenAI-compatible chat completions API.

Default target is a local Ollama server (http://localhost:11434/v1).
Only a base URL is used — this module never reads, stores, or sends an
API key. Contracts are pasted by the user; nothing is collected.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are a plain-English contract reading helper for a freelancer or "
    "small business owner. You are NOT a lawyer and never give legal "
    "advice. Given contract text, write a short, warm, beginner-friendly "
    "review: (1) a one-line summary of who holds the power in this deal, "
    "(2) up to five clauses that stand out, each with a plain-English "
    "note on why, (3) any missing protection that would be normal to ask "
    "about (payment terms, kill fees, who owns the work, notice periods). "
    'End with the sentence: "Not legal advice - just where a friend '
    'would raise an eyebrow." Be concise. Use simple words.'
)


def build_messages(contract_text: str, findings_summary: str) -> list[dict]:
    user_text = (
        f"{contract_text[:12000]}\n\n"
        "Offline pattern scan already flagged these areas "
        f"(double-check them): {findings_summary}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]


def _endpoint(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"
    return base_url + "/chat/completions"


class ReviewError(RuntimeError):
    pass


def review_contract(
    contract_text: str,
    findings_summary: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
) -> str:
    if not contract_text.strip():
        raise ReviewError("contract text is empty")
    payload = json.dumps(
        {
            "model": model,
            "messages": build_messages(contract_text, findings_summary),
            "temperature": 0.3,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        _endpoint(base_url),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer ollama",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise ReviewError(
            f"review endpoint returned HTTP {exc.code}: {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReviewError(
            f"could not reach review endpoint at {base_url}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ReviewError(f"review endpoint sent non-JSON output: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ReviewError(
            f"unexpected review endpoint response shape: {exc}"
        ) from exc
