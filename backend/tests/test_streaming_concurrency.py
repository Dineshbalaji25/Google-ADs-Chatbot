import pytest
import asyncio
import time
from unittest.mock import patch
from tests.conftest import TestingSessionLocal
from database.connection import get_db
from main import app

@pytest.mark.asyncio
async def test_streaming_concurrency(client):
    """
    Test that two streaming chat requests can run concurrently.
    If the event loop is blocked, the total time will be the sum of both.
    If they are concurrent, the total time should be close to the time of one.
    """
    # 1. Signup a new user for testing
    await client.post(
        "/api/auth/signup",
        json={"email": "concurrency@example.com", "password": "password123"}
    )
    
    # 2. Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "concurrency@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create two concurrent requests
    async def make_request(session_id):
        payload = {
            "content": "Tell me about your business",
            "session_id": session_id
        }
        response = await client.post("/api/chat", json=payload, headers=headers)
        assert response.status_code == 200
        assert "event: token" in response.text
        return response

    start_time = time.time()
    
    # Fire requests concurrently. Mock commit and add to prevent SQLAlchemy
    # 'Session is already flushing' errors from the shared db_session fixture.
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", new_callable=asyncio.Future):
        with patch("sqlalchemy.ext.asyncio.AsyncSession.add"):
            with patch("sqlalchemy.ext.asyncio.AsyncSession.refresh", new_callable=asyncio.Future):
                # Using a side_effect of an async function for async mocks
                async def mock_async_op(*args, **kwargs):
                    pass
                with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=mock_async_op):
                    with patch("sqlalchemy.ext.asyncio.AsyncSession.refresh", side_effect=mock_async_op):
                        results = await asyncio.gather(
                            make_request("session_C_1"),
                            make_request("session_C_2")
                        )
    
    duration = time.time() - start_time
    
    assert len(results) == 2
    
    # We assert it's less than 2.0s to prove they ran concurrently.
    assert duration < 2.0, f"Requests took {duration}s, suggesting they ran serially."
