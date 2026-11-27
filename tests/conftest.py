from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "cases"


@pytest.fixture
def examples():
    return EXAMPLES


class FakePost:
    """Stands in for the network: returns queued answers and records requests."""

    def __init__(self, *answers, provider="anthropic"):
        self.answers, self.provider, self.requests = list(answers), provider, []

    def __call__(self, url, payload, headers, timeout):
        self.requests.append({"url": url, "payload": payload, "headers": headers})
        text = self.answers.pop(0) if self.answers else ""
        if callable(text):
            text = text(payload)
        if self.provider == "anthropic":
            return {"content": [{"type": "text", "text": text}], "usage": {"input_tokens": 10, "output_tokens": 5}}
        return {"choices": [{"message": {"content": text}}], "usage": {"total_tokens": 15}}
