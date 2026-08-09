"""Ollama provider — offline-verifiable tests (no live endpoint required).

All tests here run without Ollama installed, without the openai SDK, and
without any API key. They validate:
  - Registry membership and field values
  - Call-time OLLAMA_BASE_URL override
  - Keyless provider: no RuntimeError when OLLAMA_API_KEY is absent
  - Routing through the shared OpenAI-compatible abstraction
  - CLI auto-mock logic treats ollama as always live-ready
  - No secrets committed to the repo
"""
from __future__ import annotations

import re
from pathlib import Path



from tjbench.models.openai_compatible import (
    PROVIDERS,
    OpenAICompatibleClient,
    is_openai_compatible,
)
from tjbench.models.registry import get_client


# ---------------------------------------------------------------------------
# Registry / provider contract
# ---------------------------------------------------------------------------


def test_ollama_is_a_registered_openai_compatible_provider():
    assert "ollama" in PROVIDERS
    prov = PROVIDERS["ollama"]
    assert prov.base_url == "http://localhost:11434/v1"
    assert prov.api_key_env == "OLLAMA_API_KEY"
    assert prov.api_key_required is False          # keyless provider
    assert prov.default_model == "llama3"
    assert is_openai_compatible("ollama")


def test_registry_resolves_ollama_through_the_shared_abstraction():
    client = get_client("ollama:llama3")
    assert isinstance(client, OpenAICompatibleClient)
    assert client.provider == "ollama"
    assert client.model == "llama3"


def test_ollama_is_openai_compatible_returns_true():
    assert is_openai_compatible("ollama")
    # Sanity: other known providers still resolve correctly.
    assert is_openai_compatible("openai")
    assert is_openai_compatible("deepseek")


# ---------------------------------------------------------------------------
# Keyless behaviour: no OLLAMA_API_KEY needed
# ---------------------------------------------------------------------------


def test_ollama_does_not_raise_when_api_key_env_is_absent(monkeypatch):
    """Building the client must not raise even with no key in env."""
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    # Instantiation is always fine — key is only checked at call time.
    client = OpenAICompatibleClient("llama3", "ollama")
    assert client.provider == "ollama"


def test_key_not_required_does_not_store_on_instance(monkeypatch):
    """The 'ollama' placeholder key must not surface via repr(vars(...))."""
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    client = OpenAICompatibleClient("llama3", "ollama")
    # The placeholder (provider name as key) should not appear as a secret
    # on the client object — it isn't an attribute at all.
    assert "api_key" not in vars(client)


# ---------------------------------------------------------------------------
# Call-time OLLAMA_BASE_URL override
# ---------------------------------------------------------------------------


def test_ollama_base_url_default_is_localhost():
    prov = PROVIDERS["ollama"]
    assert prov.base_url == "http://localhost:11434/v1"


def test_ollama_base_url_env_override_is_respected_at_call_time(monkeypatch):
    """OLLAMA_BASE_URL read inside _make_openai_client, not at import time."""
    custom_url = "http://192.168.1.42:11434/v1"
    monkeypatch.setenv("OLLAMA_BASE_URL", custom_url)
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    # We only need to confirm the URL is passed; intercept openai.OpenAI so no
    # live network call is made (and openai SDK is not required to be installed).
    captured: dict = {}

    class _FakeOAI:
        def __init__(self, *, api_key, base_url):
            captured["api_key"] = api_key
            captured["base_url"] = base_url

    import sys
    import types

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = _FakeOAI           # type: ignore[attr-defined]
    fake_openai.BadRequestError = Exception  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    from tjbench.models.openai_compatible import _make_openai_client
    _make_openai_client(PROVIDERS["ollama"])

    assert captured["base_url"] == custom_url, (
        f"Expected {custom_url!r}, got {captured['base_url']!r}"
    )


def test_ollama_base_url_falls_back_to_localhost_when_env_not_set(monkeypatch):
    """Without OLLAMA_BASE_URL, the provider's default is used."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    captured: dict = {}

    class _FakeOAI:
        def __init__(self, *, api_key, base_url):
            captured["base_url"] = base_url

    import sys
    import types

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = _FakeOAI           # type: ignore[attr-defined]
    fake_openai.BadRequestError = Exception  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    from tjbench.models.openai_compatible import _make_openai_client
    _make_openai_client(PROVIDERS["ollama"])

    assert captured["base_url"] == "http://localhost:11434/v1"


# ---------------------------------------------------------------------------
# CLI auto-mock guard
# ---------------------------------------------------------------------------


def test_provider_has_key_returns_true_for_ollama(monkeypatch):
    """Ollama must never be silently auto-mocked by the CLI."""
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)

    from tjbench.cli import _provider_has_key
    assert _provider_has_key("ollama:llama3") is True
    assert _provider_has_key("ollama:mistral") is True


# ---------------------------------------------------------------------------
# Repo hygiene: no secrets committed
# ---------------------------------------------------------------------------


def test_no_api_key_is_committed_in_the_repo():
    root = Path(__file__).resolve().parent.parent
    skip = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "results",
            ".venv", ".deepeval"}
    key_re = re.compile(r"sk-[A-Za-z0-9]{16,}")
    offenders = []
    for p in root.rglob("*"):
        if not p.is_file() or any(part in skip for part in p.parts):
            continue
        if p.suffix not in {".py", ".md", ".toml", ".txt", ".json", ".cfg", ".sh"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in key_re.findall(text):
            if m != "sk-should-not-be-stored":
                offenders.append(f"{p.name}: {m[:6]}...")
    assert not offenders, f"possible committed secrets: {offenders}"
