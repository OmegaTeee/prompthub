#!/usr/bin/env python3
"""
Test script for keyring integration.

Run with: source .venv/bin/activate && python test_keyring_integration.py
"""

import sys
from pathlib import Path

# Add router to path
sys.path.insert(0, str(Path(__file__).parent))

from router.keyring_manager import get_keyring_manager

def test_keyring_basic():
    """Test basic keyring functionality."""
    print("=" * 60)
    print("Test 1: Basic Keyring Functionality")
    print("=" * 60)

    km = get_keyring_manager()

    # Test retrieval
    print("\n✓ Keyring manager initialized")
    print(f"  Service: {km.service_name}")
    print(f"  Enabled: {km.enabled}")

    # Try to get obsidian key
    key = km.get_credential("obsidian_api_key")
    if key:
        print(f"\n✓ Retrieved obsidian_api_key")
        print(f"  Length: {len(key)} characters")
    else:
        print("\n✗ Failed to retrieve obsidian_api_key")
        return False

    return True


def test_process_env_config():
    """Test environment config processing."""
    print("\n" + "=" * 60)
    print("Test 2: Environment Config Processing")
    print("=" * 60)

    km = get_keyring_manager()

    # Test config with keyring reference
    test_config = {
        "OBSIDIAN_API_KEY": {
            "source": "keyring",
            "service": "agenthub",
            "key": "obsidian_api_key"
        },
        "OBSIDIAN_HOST": "https://127.0.0.1",
        "OBSIDIAN_PORT": "27124",
        "_comment": "This should be skipped"
    }

    print("\nInput config:")
    for k, v in test_config.items():
        if not k.startswith("_"):
            print(f"  {k}: {v if isinstance(v, str) else '[keyring reference]'}")

    processed = km.process_env_config(test_config)

    print("\nProcessed environment:")
    for k, v in processed.items():
        if k == "OBSIDIAN_API_KEY":
            print(f"  {k}: [retrieved from keyring, {len(v)} chars]")
        else:
            print(f"  {k}: {v}")

    # Verify all keys present
    expected_keys = {"OBSIDIAN_API_KEY", "OBSIDIAN_HOST", "OBSIDIAN_PORT"}
    missing = expected_keys - set(processed.keys())

    if missing:
        print(f"\n✗ Missing keys: {missing}")
        return False

    if not processed.get("OBSIDIAN_API_KEY"):
        print("\n✗ OBSIDIAN_API_KEY is empty")
        return False

    print("\n✓ All environment variables processed correctly")
    return True


def test_mcp_server_config():
    """Test with actual MCP server config format."""
    print("\n" + "=" * 60)
    print("Test 3: MCP Server Config Format")
    print("=" * 60)

    import json
    from pathlib import Path

    config_path = Path(__file__).parent / "configs" / "mcp-servers.json"

    print(f"\nReading config: {config_path}")
    with open(config_path) as f:
        config = json.load(f)

    obsidian_config = config["servers"]["obsidian"]

    print("\nObsidian server config:")
    print(f"  Command: {obsidian_config['command']}")
    print(f"  Env keys: {list(obsidian_config['env'].keys())}")

    # Process env
    km = get_keyring_manager()
    processed_env = km.process_env_config(obsidian_config['env'])

    print("\nProcessed environment:")
    for k, v in processed_env.items():
        if "KEY" in k.upper():
            print(f"  {k}: [retrieved, {len(v)} chars]")
        else:
            print(f"  {k}: {v}")

    if not processed_env.get("OBSIDIAN_API_KEY"):
        print("\n✗ Failed to retrieve OBSIDIAN_API_KEY")
        return False

    print("\n✓ MCP server config processing successful")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KEYRING INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Keyring", test_keyring_basic),
        ("Env Config Processing", test_process_env_config),
        ("MCP Server Config", test_mcp_server_config),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n✅ All tests passed! Keyring integration is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
