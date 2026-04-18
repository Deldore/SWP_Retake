"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.db import get_session
from app.main import app
from app.models.tables import Poem, UserProfile


@pytest.fixture(name="test_engine")
def test_engine_fixture():
    """Create an in-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="client")
def client_fixture(test_engine):
    """Create a test client with in-memory database."""

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_endpoint_basic(self, client, test_engine):
        """Test basic chat endpoint."""
        # Create a test poem
        poem = Poem(
            title="Test Poem",
            author="Test Author",
            language="en",
            difficulty="easy",
            theme="nature",
            text="Test poem text",
            first_line="Test poem text",
            is_active=True,
        )
        with Session(test_engine) as session:
            session.add(poem)
            session.commit()

        payload = {
            "telegram_user_id": 123456789,
            "text": "I want an easy poem about nature",
            "full_name": "Test User",
            "username": "testuser",
            "ui_language": "en",
        }

        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "reply_text" in data
        assert "action" in data

    def test_chat_endpoint_creates_user(self, client):
        """Test that chat endpoint creates new users."""
        payload = {
            "telegram_user_id": 987654321,
            "text": "Hello",
            "full_name": "New User",
            "username": "newuser",
            "ui_language": "en",
        }

        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200


class TestAudioEndpoint:
    """Tests for audio message endpoint."""

    def test_audio_endpoint(self, client):
        """Test audio message endpoint."""
        payload = {
            "telegram_user_id": 123456789,
            "file_id": "test_file_id_12345",
            "duration_seconds": 30,
            "mime_type": "audio/ogg",
            "full_name": "Test User",
            "username": "testuser",
            "ui_language": "en",
        }

        response = client.post("/api/audio-message", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "reply_text" in data
        assert data["action"] == "audio_received"


class TestMemorizedPoemsEndpoint:
    """Tests for memorized poems endpoint."""

    def test_memorized_poems_endpoint(self, client):
        """Test getting memorized poems."""
        payload = {
            "telegram_user_id": 123456789,
            "ui_language": "en",
        }

        response = client.post("/api/memorized-poems", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "reply_text" in data
        assert "memorized_poems" in data
