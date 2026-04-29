"""
Unit tests for Settings keyring resolution of llm_api_key.

Resolution order is (first non-empty wins):
1. LLM_API_KEY env var
2. LM_API_TOKEN env var (LM Studio's official name; alias)
3. Keychain account ``lm_api_token`` (under service ``prompthub``)
4. None (no auth header sent)

Tests construct Settings with ``_env_file=None`` so the repo's ``app/.env``
doesn't leak into the test fixture, and patch the internal
``_get_from_keyring`` helper so the macOS keychain isn't touched.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip both env vars before each test so resolution is deterministic."""
    for var in ("LLM_API_KEY", "LM_API_TOKEN"):
        monkeypatch.delenv(var, raising=False)


def _make_settings(monkeypatch: pytest.MonkeyPatch, *, keyring_value: str = ""):
    """Construct a Settings with keyring stubbed to a specific return value."""
    from router.config import settings as settings_mod

    monkeypatch.setattr(
        settings_mod,
        "_get_from_keyring",
        lambda key: keyring_value if key == "lm_api_token" else "",
    )
    # _env_file=None prevents app/.env from contributing real values.
    return settings_mod.Settings(_env_file=None)


def test_llm_api_key_env_wins_over_keyring(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM_API_KEY env var takes precedence over a Keychain entry."""
    monkeypatch.setenv("LLM_API_KEY", "from-env")
    s = _make_settings(monkeypatch, keyring_value="from-keychain")
    assert s.llm_api_key == "from-env"


def test_lm_api_token_alias_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    """LM_API_TOKEN works as an alias for LLM_API_KEY (LM Studio's native name)."""
    monkeypatch.setenv("LM_API_TOKEN", "lmstudio-style-token")
    s = _make_settings(monkeypatch, keyring_value="")
    assert s.llm_api_key == "lmstudio-style-token"


def test_llm_api_key_falls_back_to_keychain(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no env vars are set, the Keychain entry lm_api_token is used."""
    s = _make_settings(monkeypatch, keyring_value="from-keychain-secret")
    assert s.llm_api_key == "from-keychain-secret"


def test_llm_api_key_is_none_when_nothing_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """No env, no Keychain entry → llm_api_key is None (no auth header)."""
    s = _make_settings(monkeypatch, keyring_value="")
    assert s.llm_api_key is None


def test_explicit_env_takes_precedence_over_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If both LLM_API_KEY and LM_API_TOKEN are set, LLM_API_KEY wins (left-to-right)."""
    monkeypatch.setenv("LLM_API_KEY", "explicit")
    monkeypatch.setenv("LM_API_TOKEN", "alias")
    s = _make_settings(monkeypatch, keyring_value="")
    assert s.llm_api_key == "explicit"
