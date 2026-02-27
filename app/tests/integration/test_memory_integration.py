"""
Integration tests for session memory endpoints.

Requires a running PromptHub server on localhost:9090.
"""

import httpx
import pytest


@pytest.fixture
async def client():
    """Create an async test client pointing to running server."""
    async with httpx.AsyncClient(base_url="http://localhost:9090") as client:
        yield client


@pytest.mark.asyncio
async def test_create_session_endpoint(client):
    """Test POST /sessions endpoint."""
    response = await client.post(
        "/sessions",
        json={"client_id": "test-client", "memory_mcp_sync": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "test-client"
    assert data["status"] == "active"
    assert data["fact_count"] == 0


@pytest.mark.asyncio
async def test_list_sessions_endpoint(client):
    """Test GET /sessions endpoint."""
    # Create sessions
    resp1 = await client.post(
        "/sessions", json={"client_id": "client-1"}
    )
    session1_id = resp1.json()["id"]

    resp2 = await client.post(
        "/sessions", json={"client_id": "client-2"}
    )
    session2_id = resp2.json()["id"]

    # List all
    response = await client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

    # Filter by client
    response = await client.get("/sessions?client_id=client-1")
    assert response.status_code == 200
    data = response.json()
    assert all(s["client_id"] == "client-1" for s in data["sessions"])


@pytest.mark.asyncio
async def test_get_session_endpoint(client):
    """Test GET /sessions/{id} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Get session
    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["client_id"] == "test-client"


@pytest.mark.asyncio
async def test_close_session_endpoint(client):
    """Test DELETE /sessions/{id} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Close session
    response = await client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"

    # Verify closed
    response = await client.get(f"/sessions/{session_id}")
    data = response.json()
    assert data["status"] == "closed"


@pytest.mark.asyncio
async def test_add_fact_endpoint(client):
    """Test POST /sessions/{id}/facts endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Add fact
    response = await client.post(
        f"/sessions/{session_id}/facts",
        json={
            "fact": "User likes Python",
            "tags": ["preferences", "python"],
            "source": "manual",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fact"] == "User likes Python"
    assert data["tags"] == ["preferences", "python"]
    assert data["source"] == "manual"
    assert data["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_get_facts_endpoint(client):
    """Test GET /sessions/{id}/facts endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Add facts
    await client.post(
        f"/sessions/{session_id}/facts",
        json={"fact": "Fact 1", "tags": ["tag1"]},
    )
    await client.post(
        f"/sessions/{session_id}/facts",
        json={"fact": "Fact 2", "tags": ["tag2"]},
    )

    # Get facts
    response = await client.get(f"/sessions/{session_id}/facts")
    assert response.status_code == 200
    facts = response.json()
    assert len(facts) == 2


@pytest.mark.asyncio
async def test_delete_fact_endpoint(client):
    """Test DELETE /sessions/{id}/facts/{fact_id} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Add fact
    fact_resp = await client.post(
        f"/sessions/{session_id}/facts",
        json={"fact": "Test fact"},
    )
    fact_id = fact_resp.json()["id"]

    # Delete fact
    response = await client.delete(
        f"/sessions/{session_id}/facts/{fact_id}"
    )
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify deleted
    facts_resp = await client.get(f"/sessions/{session_id}/facts")
    assert len(facts_resp.json()) == 0


@pytest.mark.asyncio
async def test_upsert_memory_block_endpoint(client):
    """Test PUT /sessions/{id}/memory/{key} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Upsert block
    response = await client.put(
        f"/sessions/{session_id}/memory/preferences",
        json={"value": {"language": "python", "framework": "fastapi"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "preferences"
    assert data["value"]["language"] == "python"

    # Update block
    response = await client.put(
        f"/sessions/{session_id}/memory/preferences",
        json={"value": {"language": "python", "framework": "django"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["value"]["framework"] == "django"


@pytest.mark.asyncio
async def test_get_memory_block_endpoint(client):
    """Test GET /sessions/{id}/memory/{key} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Upsert block
    await client.put(
        f"/sessions/{session_id}/memory/test_key",
        json={"value": "test_value"},
    )

    # Get block
    response = await client.get(
        f"/sessions/{session_id}/memory/test_key"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "test_key"
    assert data["value"] == "test_value"


@pytest.mark.asyncio
async def test_delete_memory_block_endpoint(client):
    """Test DELETE /sessions/{id}/memory/{key} endpoint."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Upsert block
    await client.put(
        f"/sessions/{session_id}/memory/test_key",
        json={"value": "test_value"},
    )

    # Delete block
    response = await client.delete(
        f"/sessions/{session_id}/memory/test_key"
    )
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify deleted
    response = await client.get(
        f"/sessions/{session_id}/memory/test_key"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_context_endpoint(client):
    """Test GET /sessions/{id}/context endpoint (full context)."""
    # Create session
    resp = await client.post(
        "/sessions", json={"client_id": "test-client"}
    )
    session_id = resp.json()["id"]

    # Add facts
    await client.post(
        f"/sessions/{session_id}/facts",
        json={"fact": "Fact 1"},
    )

    # Add memory blocks
    await client.put(
        f"/sessions/{session_id}/memory/key1",
        json={"value": "value1"},
    )

    # Get context
    response = await client.get(f"/sessions/{session_id}/context")
    assert response.status_code == 200
    data = response.json()

    assert "session" in data
    assert "facts" in data
    assert "memory_blocks" in data
    assert "mcp_graph_summary" in data

    assert len(data["facts"]) == 1
    assert len(data["memory_blocks"]) == 1


@pytest.mark.asyncio
async def test_full_session_lifecycle(client):
    """Test complete session lifecycle."""
    # 1. Create session
    create_resp = await client.post(
        "/sessions",
        json={"client_id": "test-client", "memory_mcp_sync": False},
    )
    session_id = create_resp.json()["id"]
    assert create_resp.status_code == 200

    # 2. Add facts
    fact_resp = await client.post(
        f"/sessions/{session_id}/facts",
        json={
            "fact": "User prefers Python",
            "tags": ["preferences"],
        },
    )
    assert fact_resp.status_code == 200

    # 3. Add memory blocks
    block_resp = await client.put(
        f"/sessions/{session_id}/memory/settings",
        json={"value": {"theme": "dark"}},
    )
    assert block_resp.status_code == 200

    # 4. Get context
    context_resp = await client.get(f"/sessions/{session_id}/context")
    assert context_resp.status_code == 200
    context = context_resp.json()
    assert len(context["facts"]) == 1
    assert len(context["memory_blocks"]) == 1

    # 5. Close session
    close_resp = await client.delete(f"/sessions/{session_id}")
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    # 6. Verify closed
    get_resp = await client.get(f"/sessions/{session_id}")
    assert get_resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_session_not_found_errors(client):
    """Test 404 errors for non-existent sessions."""
    fake_id = "non-existent-session-id"

    # Get non-existent session
    response = await client.get(f"/sessions/{fake_id}")
    assert response.status_code == 404

    # Add fact to non-existent session
    response = await client.post(
        f"/sessions/{fake_id}/facts",
        json={"fact": "Test"},
    )
    assert response.status_code == 404

    # Get memory block from non-existent session
    response = await client.get(f"/sessions/{fake_id}/memory/key")
    assert response.status_code == 404
