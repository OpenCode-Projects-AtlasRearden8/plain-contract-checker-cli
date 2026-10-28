"""Tests for the optional OpenAI-compatible review pass.

No network access is needed: requests are pointed at a local test HTTP
server, and there is deliberately no API key handling anywhere.
"""

import http.server
import json
import threading
import urllib.request

import pytest

from contract_checker.review import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ReviewError,
    _endpoint,
    build_messages,
    review_contract,
)


class FakeOpenAIHandler(http.server.BaseHTTPRequestHandler):
    bad_payload = False

    def do_POST(self):  # noqa: N802 (stdlib naming)
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))
        assert payload["messages"][0]["role"] == "system"
        assert "NOT a lawyer" in payload["messages"][0]["content"]
        assert "SPEEDSIGN" in payload["messages"][1]["content"]
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Looks one-sided. Not legal advice - just "
                                "where a friend would raise an eyebrow."
                            )
                        }
                    }
                ]
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class BrokenHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        self.send_response(500)
        self.end_headers()
        self.wfile.write(b"boom")

    def log_message(self, *args):
        pass


def run_server(handler):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_default_target_is_local_ollama_without_key():
    assert DEFAULT_BASE_URL.startswith("http://localhost")
    assert "/v1" in DEFAULT_BASE_URL
    assert _endpoint("http://localhost:11434").endswith(
        "localhost:11434/v1/chat/completions"
    )
    assert _endpoint("http://localhost:11434/v1/").endswith(
        "localhost:11434/v1/chat/completions"
    )


def test_build_messages_keeps_findings_summary():
    messages = build_messages("CONTRACT", "unilateral_change, auto_renew")
    assert messages[1]["role"] == "user"
    assert "unilateral_change" in messages[1]["content"]
    assert "Not" in messages[0]["content"]


def test_review_success_against_fake_endpoint():
    with run_server(FakeOpenAIHandler) as server:
        text = review_contract(
            "Hello SPEEDSIGN world",
            "none",
            base_url=f"http://127.0.0.1:{server.server_address[1]}",
            timeout=5,
        )
    assert "Not legal advice" in text


def test_review_endpoint_error_becomes_review_error():
    with run_server(BrokenHandler) as server:
        with pytest.raises(ReviewError):
            review_contract(
                "text",
                "none",
                base_url=f"http://127.0.0.1:{server.server_address[1]}",
                timeout=5,
            )


def test_review_unreachable_endpoint():
    with pytest.raises(ReviewError):
        review_contract(
            "text",
            "none",
            base_url="http://127.0.0.1:1",
            timeout=1,
        )


def test_review_empty_contract_rejected():
    with pytest.raises(ReviewError):
        review_contract("   ", "none")


def test_review_never_sends_api_key(monkeypatch):
    captured = {}

    class Recorder(FakeOpenAIHandler):
        def do_POST(self):  # noqa: N802
            captured["authorization"] = self.headers.get("Authorization")
            FakeOpenAIHandler.do_POST(self)

    with run_server(Recorder) as server:
        review_contract(
            "Hello SPEEDSIGN world",
            "none",
            base_url=f"http://127.0.0.1:{server.server_address[1]}",
        )
    assert "Bearer ollama" in captured["authorization"]
