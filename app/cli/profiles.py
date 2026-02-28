"""
Profile loader — reads api-keys.json and enhancement-rules.json
to build ClientProfile instances.
"""

import json
import logging
from pathlib import Path

from cli.models import ClientProfile, ClientType

logger = logging.getLogger(__name__)


class ProfileLoader:
    """
    Loads client profiles from PromptHub config files.

    Merges data from:
    - api-keys.json: bearer tokens and enhance flags
    - enhancement-rules.json: models, system prompts, privacy levels
    """

    def __init__(self, configs_dir: Path | None = None):
        if configs_dir is None:
            configs_dir = (
                Path.home()
                / ".local"
                / "share"
                / "prompthub"
                / "app"
                / "configs"
            )
        self.configs_dir = configs_dir.resolve()

    def _load_json(self, filename: str) -> dict:
        """Load a JSON config file, returning {} on any error."""
        path = self.configs_dir / filename
        try:
            return json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("Could not load %s: %s", path, e)
            return {}

    def _find_api_key(
        self, keys_data: dict, client_name: str
    ) -> tuple[str | None, bool]:
        """Find the API key and enhance flag for a client name."""
        for key_value, info in keys_data.get("keys", {}).items():
            if info.get("client_name") == client_name:
                return key_value, info.get("enhance", False)
        return None, False

    def load(self, client_type: ClientType) -> ClientProfile:
        """
        Load a complete profile for the given client type.

        Merges api-keys.json (auth) with enhancement-rules.json (behavior).
        """
        client_name = client_type.value
        keys_data = self._load_json("api-keys.json")
        rules_data = self._load_json("enhancement-rules.json")

        # Auth from api-keys.json
        api_key, enhance = self._find_api_key(keys_data, client_name)

        # Behavior from enhancement-rules.json
        client_rules = rules_data.get("clients", {}).get(client_name, {})
        default_rules = rules_data.get("default", {})

        return ClientProfile(
            client_name=client_name,
            client_type=client_type,
            api_key=api_key,
            enhance=enhance,
            privacy_level=client_rules.get(
                "privacy_level",
                default_rules.get("privacy_level", "local_only"),
            ),
            model=client_rules.get(
                "model", default_rules.get("model", "llama3.2:latest")
            ),
            system_prompt=client_rules.get("system_prompt"),
        )

    def list_profiles(self) -> list[ClientProfile]:
        """Load profiles for all known client types."""
        return [self.load(ct) for ct in ClientType]
