# tests/test_routes.py
import pytest
from database.models import User, Message, Conversation
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_auth_and_protected_routes(client):
    # 1. Signup a new user
    signup_response = await client.post(
        "/api/auth/signup",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert signup_response.status_code == 200
    signup_data = signup_response.json()
    assert "access_token" in signup_data
    assert signup_data["email"] == "test@example.com"
    
    # Assert signup user duplication prevention
    dup_response = await client.post(
        "/api/auth/signup",
        json={"email": "test@example.com", "password": "differentpwd"}
    )
    assert dup_response.status_code == 400

    # 2. Login the user
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test google ads redirect URL endpoint
    url_response = await client.get("/api/auth/google/url")
    assert url_response.status_code == 200
    assert "url" in url_response.json()

    # 4. Test chat endpoint
    chat_response = await client.post(
        "/api/chat",
        json={"content": "I want to create an ad for Pizza", "session_id": "sess_123"},
        headers=headers
    )
    assert chat_response.status_code == 200
    assert "event: token" in chat_response.text
    assert "event: campaign_data" in chat_response.text

    # 5. Test campaign preview endpoint
    preview_response = await client.post(
        "/api/campaign/preview",
        json={"type": "restaurant", "name": "Pizza Planet", "location": "New York"},
        headers=headers
    )
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert "headlines" in preview_data

    # 6. Test campaign create endpoint
    create_response = await client.post(
        "/api/campaign/create",
        json={
            "headlines": ["Best Pizza", "Delicious Dining"],
            "descriptions": ["Fresh out of the oven pizza in NYC."],
            "keywords": ["pizza", "nyc pizza"],
            "daily_budget": 50.0,
            "location": "New York"
        },
        headers=headers
    )
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert "campaign_id" in create_data

@pytest.mark.asyncio
async def test_session_isolation_regression(client, db_session):
    """
    Regression test asserting that conversation histories of two different session IDs
    are completely isolated in the database and do not cross-talk.
    """
    # Create and login user
    await client.post(
        "/api/auth/signup",
        json={"email": "session@example.com", "password": "password123"}
    )
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "session@example.com", "password": "password123"}
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Send first message in Session A
    res_a = await client.post(
        "/api/chat",
        json={"content": "Session A unique message content", "session_id": "session_A"},
        headers=headers
    )
    assert res_a.status_code == 200

    # Send message in Session B
    res_b = await client.post(
        "/api/chat",
        json={"content": "Session B unique message content", "session_id": "session_B"},
        headers=headers
    )
    assert res_b.status_code == 200

    # Direct database verification
    # Query conversation session A
    result_a = await db_session.execute(
        select(Conversation).filter(Conversation.session_id == "session_A")
    )
    conv_a = result_a.scalars().first()
    assert conv_a is not None

    messages_a = await db_session.execute(
        select(Message).filter(Message.conversation_id == conv_a.id)
    )
    msgs_a = messages_a.scalars().all()
    assert len(msgs_a) > 0
    # Confirm it has user content A and NOT user content B
    assert any("Session A" in m.content for m in msgs_a)
    assert not any("Session B" in m.content for m in msgs_a)

    # Query conversation session B
    result_b = await db_session.execute(
        select(Conversation).filter(Conversation.session_id == "session_B")
    )
    conv_b = result_b.scalars().first()
    assert conv_b is not None

    messages_b = await db_session.execute(
        select(Message).filter(Message.conversation_id == conv_b.id)
    )
    msgs_b = messages_b.scalars().all()
    assert len(msgs_b) > 0
    # Confirm it has user content B and NOT user content A
    assert any("Session B" in m.content for m in msgs_b)
    assert not any("Session A" in m.content for m in msgs_b)

@pytest.mark.asyncio
async def test_meta_campaign_preview(client, db_session):
    await client.post("/api/auth/signup", json={"email": "meta@example.com", "password": "password123"})
    login_res = await client.post("/api/auth/login", json={"email": "meta@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    preview_response = await client.post(
        "/api/campaign/preview",
        json={"type": "restaurant", "name": "Pizza Planet", "location": "New York", "platform": "meta"},
        headers=headers
    )
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    assert preview_data["platform"] == "meta"
    assert "primary_texts" in preview_data

@pytest.mark.asyncio
async def test_both_platforms_create_partial_failure(client, db_session):
    await client.post("/api/auth/signup", json={"email": "both@example.com", "password": "password123"})
    login_res = await client.post("/api/auth/login", json={"email": "both@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    from unittest.mock import patch
    with patch("services.meta_ads_service.MockMetaAdsService.create_campaign", side_effect=Exception("Meta API Down")):
        create_response = await client.post(
            "/api/campaign/create",
            json={
                "platform": "both",
                "headlines": ["Best Pizza", "Delicious Dining"],
                "descriptions": ["Fresh out of the oven pizza in NYC."],
                "keywords": ["pizza", "nyc pizza"],
                "daily_budget": 50.0,
                "location": "New York",
                "primary_texts": ["Get the best pizza."]
            },
            headers=headers
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["platform"] == "both"
        assert create_data["status"] == "partial_success"
        assert create_data["results"]["google"]["status"] == "success"
        assert create_data["results"]["meta"]["status"] == "failed"
