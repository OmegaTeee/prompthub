#!/usr/bin/env python3
"""
Restart and verify all PromptHub MCP servers.

Fetches the server list dynamically from the router's /servers endpoint,
restarts each auto_start server, and verifies tool access.

Usage:
    python scripts/router/restart_mcp_servers.py           # Restart all auto_start servers
    python scripts/router/restart_mcp_servers.py --all     # Restart all servers including stopped
    python scripts/router/restart_mcp_servers.py obsidian  # Restart specific server
"""

import subprocess
import time
import json
import sys

ROUTER_URL = "http://localhost:9090"


def run_command(cmd):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def fetch_servers():
    """Fetch server list from the router."""
    code, stdout, _ = run_command(f"curl -s {ROUTER_URL}/servers")
    if code != 0:
        print("ERROR: Cannot reach router at", ROUTER_URL)
        sys.exit(1)

    try:
        data = json.loads(stdout)
        return data.get("servers", [])
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON from /servers")
        sys.exit(1)


def restart_server(server_name):
    """Restart a specific MCP server via the router API."""
    print(f"  Restarting {server_name}...", end=" ", flush=True)

    run_command(f"curl -s -X POST {ROUTER_URL}/servers/{server_name}/stop")
    time.sleep(1)

    code, stdout, _ = run_command(
        f"curl -s -X POST {ROUTER_URL}/servers/{server_name}/start"
    )

    if code == 0:
        try:
            response = json.loads(stdout)
            if response.get("status") == "running":
                print("OK")
                return True
        except json.JSONDecodeError:
            pass

    print("FAILED")
    return False


def test_server(server_name):
    """Test if a server responds to tools/list."""
    print(f"  Testing {server_name}...", end=" ", flush=True)

    cmd = (
        f"curl -s -X POST '{ROUTER_URL}/mcp/{server_name}/tools/call' "
        f"-H 'Content-Type: application/json' "
        f"-H 'X-Client-Name: test' "
        f'-d \'{{"jsonrpc":"2.0","method":"tools/list","id":1}}\''
    )

    code, stdout, _ = run_command(cmd)

    if code == 0:
        try:
            response = json.loads(stdout)
            if "result" in response and "tools" in response["result"]:
                tools_count = len(response["result"]["tools"])
                print(f"OK ({tools_count} tools)")
                return True
            elif "error" in response:
                print(f"FAILED: {response['error'].get('message', 'Unknown')}")
                return False
        except json.JSONDecodeError:
            pass

    print("FAILED: no response")
    return False


def main():
    include_all = "--all" in sys.argv
    specific = [a for a in sys.argv[1:] if not a.startswith("-")]

    servers = fetch_servers()

    if specific:
        targets = [s for s in servers if s["name"] in specific]
        if not targets:
            print(f"ERROR: Server(s) not found: {', '.join(specific)}")
            print(f"Available: {', '.join(s['name'] for s in servers)}")
            sys.exit(1)
    elif include_all:
        targets = servers
    else:
        targets = [s for s in servers if s.get("auto_start", False)]

    print("=" * 60)
    print("PromptHub MCP Server Restart & Verification")
    print("=" * 60)
    print()
    print(f"Targets: {len(targets)} servers")
    print()

    # Phase 1: Restart
    print("Phase 1: Restarting servers...")
    print("-" * 60)
    for server in targets:
        restart_server(server["name"])

    print()
    print("Waiting for servers to initialize...")
    time.sleep(3)
    print()

    # Phase 2: Test
    print("Phase 2: Testing MCP tool access...")
    print("-" * 60)
    results = []
    for server in targets:
        success = test_server(server["name"])
        results.append((server["name"], success))

    # Summary
    print()
    print("=" * 60)
    success_count = sum(1 for _, ok in results if ok)
    total_count = len(results)

    for name, ok in results:
        print(f"  {name:<25} {'OK' if ok else 'FAILED'}")

    print()
    print(f"Result: {success_count}/{total_count} servers responding")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
