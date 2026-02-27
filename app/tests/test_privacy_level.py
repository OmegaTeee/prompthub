"""
Tests for privacy boundary system (Path C).

Covers:
- PrivacyLevel enum values and parsing
- resolve_privacy_level downgrade-only semantics
- EnhancementRule privacy_level default and explicit
- EnhancementResult carries privacy_level
- Config loading with mixed privacy levels
"""

import json

import pytest

from router.enhancement.service import (
    EnhancementResult,
    EnhancementRule,
    PrivacyLevel,
    resolve_privacy_level,
)


class TestPrivacyLevelEnum:
    """Test PrivacyLevel enum basics."""

    def test_values(self):
        assert PrivacyLevel.LOCAL_ONLY == "local_only"
        assert PrivacyLevel.FREE_OK == "free_ok"
        assert PrivacyLevel.ANY == "any"

    def test_from_string(self):
        assert PrivacyLevel("local_only") is PrivacyLevel.LOCAL_ONLY
        assert PrivacyLevel("free_ok") is PrivacyLevel.FREE_OK
        assert PrivacyLevel("any") is PrivacyLevel.ANY

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            PrivacyLevel("cloud_only")


class TestResolvePrivacyLevel:
    """Test downgrade-only header resolution."""

    def test_no_header_returns_config(self):
        result = resolve_privacy_level(PrivacyLevel.FREE_OK, None)
        assert result == PrivacyLevel.FREE_OK

    def test_header_same_as_config(self):
        result = resolve_privacy_level(
            PrivacyLevel.FREE_OK, PrivacyLevel.FREE_OK,
        )
        assert result == PrivacyLevel.FREE_OK

    def test_header_downgrades_any_to_local(self):
        """Header can make MORE restrictive."""
        result = resolve_privacy_level(
            PrivacyLevel.ANY, PrivacyLevel.LOCAL_ONLY,
        )
        assert result == PrivacyLevel.LOCAL_ONLY

    def test_header_downgrades_free_ok_to_local(self):
        result = resolve_privacy_level(
            PrivacyLevel.FREE_OK, PrivacyLevel.LOCAL_ONLY,
        )
        assert result == PrivacyLevel.LOCAL_ONLY

    def test_header_downgrades_any_to_free_ok(self):
        result = resolve_privacy_level(
            PrivacyLevel.ANY, PrivacyLevel.FREE_OK,
        )
        assert result == PrivacyLevel.FREE_OK

    def test_header_cannot_upgrade_local_to_any(self):
        """Header cannot make LESS restrictive."""
        result = resolve_privacy_level(
            PrivacyLevel.LOCAL_ONLY, PrivacyLevel.ANY,
        )
        assert result == PrivacyLevel.LOCAL_ONLY

    def test_header_cannot_upgrade_local_to_free(self):
        result = resolve_privacy_level(
            PrivacyLevel.LOCAL_ONLY, PrivacyLevel.FREE_OK,
        )
        assert result == PrivacyLevel.LOCAL_ONLY

    def test_header_cannot_upgrade_free_to_any(self):
        result = resolve_privacy_level(
            PrivacyLevel.FREE_OK, PrivacyLevel.ANY,
        )
        assert result == PrivacyLevel.FREE_OK


class TestEnhancementRulePrivacy:
    """Test privacy_level on EnhancementRule model."""

    def test_default_is_local_only(self):
        rule = EnhancementRule()
        assert rule.privacy_level == PrivacyLevel.LOCAL_ONLY

    def test_explicit_free_ok(self):
        rule = EnhancementRule(privacy_level="free_ok")
        assert rule.privacy_level == PrivacyLevel.FREE_OK

    def test_explicit_any(self):
        rule = EnhancementRule(privacy_level="any")
        assert rule.privacy_level == PrivacyLevel.ANY

    def test_from_json_dict(self):
        """Simulates loading from enhancement-rules.json."""
        data = {
            "model": "llama3.2:latest",
            "system_prompt": "test",
            "privacy_level": "free_ok",
        }
        rule = EnhancementRule(**data)
        assert rule.privacy_level == PrivacyLevel.FREE_OK

    def test_from_json_dict_no_privacy_field(self):
        """Missing field defaults to local_only."""
        data = {"model": "llama3.2:latest", "system_prompt": "test"}
        rule = EnhancementRule(**data)
        assert rule.privacy_level == PrivacyLevel.LOCAL_ONLY


class TestEnhancementResultPrivacy:
    """Test privacy_level on EnhancementResult model."""

    def test_default_is_local_only(self):
        result = EnhancementResult(original="test", enhanced="test")
        assert result.privacy_level == PrivacyLevel.LOCAL_ONLY

    def test_explicit_privacy_level(self):
        result = EnhancementResult(
            original="test",
            enhanced="test enhanced",
            privacy_level=PrivacyLevel.FREE_OK,
        )
        assert result.privacy_level == PrivacyLevel.FREE_OK

    def test_serialization_includes_privacy(self):
        result = EnhancementResult(
            original="test",
            enhanced="test",
            privacy_level=PrivacyLevel.ANY,
        )
        d = result.model_dump()
        assert d["privacy_level"] == "any"


class TestConfigLoadingWithPrivacy:
    """Test that enhancement rules load privacy_level correctly."""

    def test_load_mixed_privacy_config(self, tmp_path):
        """Config with some clients having privacy_level, others not."""
        config = {
            "default": {
                "enabled": True,
                "model": "llama3.2:latest",
                "system_prompt": "Default prompt.",
            },
            "clients": {
                "perplexity": {
                    "model": "llama3.2:latest",
                    "system_prompt": "Perplexity prompt.",
                    "privacy_level": "free_ok",
                },
                "vscode": {
                    "model": "llama3.2:latest",
                    "system_prompt": "VS Code prompt.",
                },
            },
        }
        config_file = tmp_path / "enhancement-rules.json"
        config_file.write_text(json.dumps(config))

        # Simulate the rule loading logic from service._load_rules_async
        default_rule = EnhancementRule(**config["default"])
        assert default_rule.privacy_level == PrivacyLevel.LOCAL_ONLY

        for name, rule_data in config["clients"].items():
            merged = default_rule.model_dump()
            merged.update(rule_data)
            rule = EnhancementRule(**merged)

            if name == "perplexity":
                assert rule.privacy_level == PrivacyLevel.FREE_OK
            elif name == "vscode":
                assert rule.privacy_level == PrivacyLevel.LOCAL_ONLY
