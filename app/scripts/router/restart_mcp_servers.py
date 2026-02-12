#!/usr/bin/env python3
"""
Restart and verify all AgentHub MCP servers.

This script ensures all MCP servers have fresh stdio connections
and are responding to requests properly.
"""

import subprocess
import time
import json
import sys


def run_command(cmd):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def restart_server(server_name):
    """Restart a specific MCP server."""
    print(f"Restarting {server_name}...", end=" ", flush=True)

    # Stop (may fail if already stopped)
    run_command(f'curl -s -X POST http://localhost:9090/servers/{server_name}/stop')
    time.sleep(1)

    # Start
    code, stdout, stderr = run_command(
        f'curl -s -X POST http://localhost:9090/servers/{server_name}/start'
    )

    if code == 0:
        try:
            response = json.loads(stdout)
            if response.get("status") == "running":
                print("✅")
                return True
        except json.JSONDecodeError:
            pass

    print("❌")
    return False


def test_server(server_name, endpoint):
    """Test if a server is responding to requests."""
    print(f"Testing {server_name}...", end=" ", flush=True)

    cmd = f'''curl -s -X POST 'http://localhost:9090/mcp/{endpoint}/tools/call' \
        -H 'Content-Type: application/json' \
        -H 'X-Client-Name: test' \
        -d '{{"jsonrpc":"2.0","method":"tools/list","id":1}}'
    '''

    code, stdout, stderr = run_command(cmd)

    if code == 0:
        try:
            response = json.loads(stdout)
            if "result" in response and "tools" in response["result"]:
                tools_count = len(response["result"]["tools"])
                print(f"✅ ({tools_count} tools)")
                return True
            elif "error" in response:
                print(f"❌ Error: {response['error'].get('message', 'Unknown')}")
                return False
        except json.JSONDecodeError:
            pass

    print("❌ Request failed")
    return False


def main():
    # Servers to restart and test
    servers = [
        ("context7", "context7"),
        ("desktop-commander", "desktop-commander"),
        ("sequential-thinking", "sequential-thinking"),
        ("memory", "memory"),
        ("deepseek-reasoner", "deepseek-reasoner"),
        ("obsidian", "obsidian"),
    ]

    print("=" * 60)
    print("AgentHub MCP Server Restart & Verification")
    print("=" * 60)
    print()

    # Phase 1: Restart all servers
    print("Phase 1: Restarting servers...")
    print("-" * 60)
    for server_name, _ in servers:
        restart_server(server_name)

    print()
    print("Waiting for servers to initialize...")
    time.sleep(5)
    print()

    # Phase 2: Test all servers
    print("Phase 2: Testing MCP tool access...")
    print("-" * 60)
    results = []
    for server_name, endpoint in servers:
        success = test_server(server_name, endpoint)
        results.append((server_name, success))

    # Summary
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for server_name, success in results:
        status = "✅ OK" if success else "❌ FAILED"
        print(f"  {server_name:<25} {status}")

    print()
    print(f"Total: {success_count}/{total_count} servers responding")

    if success_count == total_count:
        print()
        print("🎉 All servers are ready for Claude Desktop!")
        print()
        print("Next step: Restart Claude Desktop and test with:")
        print('  "List available MCP tools"')
        return 0
    else:
        print()
        print("⚠️  Some servers failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
