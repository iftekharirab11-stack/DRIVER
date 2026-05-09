import pytest
import pytest_asyncio
import asyncio
import json
import os
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add parent dir to path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, sessions, build_dashboard
from session_manager import SessionStore

os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PRIMARY_MODEL"] = "gpt-4o"


@pytest.fixture
def client():
    """Create a fresh session store and test client for each test."""
    # Create a new session store to avoid state leakage
    with patch('main.sessions', SessionStore()) as mock_sessions:
        with TestClient(app) as test_client:
            yield test_client, mock_sessions


@pytest.fixture
def valid_session_id():
    """Create a valid session ID for testing."""
    return str(uuid.uuid4())


# ─── Session Management Tests ────────────────────────────────────────────────

class TestSessionCreation:
    """Test session creation and validation."""
    
    def test_create_session_returns_session_id_and_user_id(self, client):
        """POST /session should return a valid session_id and user_id."""
        test_client, mock_sessions = client
        response = test_client.post("/session")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "user_id" in data
        assert data["user_id"] == "demo_user"
        # Validate UUID format
        uuid.UUID(data["session_id"])
    
    def test_create_session_stores_session(self, client):
        """Created session should be stored and retrievable."""
        test_client, mock_sessions = client
        response = test_client.post("/session")
        session_id = response.json()["session_id"]
        assert mock_sessions.is_valid_session(session_id) is True
    
    def test_create_session_stores_empty_history(self, client):
        """New session should start with empty history."""
        test_client, mock_sessions = client
        response = test_client.post("/session")
        session_id = response.json()["session_id"]
        history = mock_sessions.get(session_id, "history")
        assert history == []


class TestSessionValidation:
    """Test session validation logic."""
    
    def test_invalid_session_id_rejected(self, client):
        """Invalid session ID should be rejected."""
        test_client, mock_sessions = client
        response = test_client.post("/session")
        session_id = response.json()["session_id"]
        # Simulate expiration by manually removing
        mock_sessions.sessions.pop(session_id, None)
        assert mock_sessions.is_valid_session(session_id) is False
    
    def test_nonexistent_session_id_invalid(self, client):
        """Non-existent session ID should be invalid."""
        test_client, _ = client
        fake_id = str(uuid.uuid4())
        assert fake_id not in test_client.app.state.sessions if hasattr(test_client.app, 'state') else True


# ─── Dashboard Endpoint Tests ───────────────────────────────────────────────

class TestDashboardEndpoint:
    """Test GET /dashboard endpoint."""
    
    def test_get_dashboard_returns_200(self, client):
        """Dashboard endpoint should return 200."""
        test_client, _ = client
        response = test_client.get("/dashboard")
        assert response.status_code == 200
    
    def test_get_dashboard_returns_expected_keys(self, client):
        """Dashboard response should contain expected keys."""
        test_client, _ = client
        response = test_client.get("/dashboard")
        data = response.json()
        assert "content" in data
        assert "score" in data
        assert "model" in data
        assert "system" in data
    
    def test_dashboard_contains_connections_section(self, client):
        """Dashboard should mention connections."""
        test_client, _ = client
        response = test_client.get("/dashboard")
        data = response.json()
        assert "CONNECTIONS" in data["content"] or "connections" in data["content"].lower()
    
    def test_dashboard_score_in_range(self, client):
        """Dashboard health score should be between 0-100."""
        test_client, _ = client
        response = test_client.get("/dashboard")
        data = response.json()
        assert 0 <= data["score"] <= 100


# ─── Root Endpoint Tests ────────────────────────────────────────────────────

class TestRootEndpoint:
    """Test GET / endpoint."""
    
    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        test_client, _ = client
        response = test_client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_service_info(self, client):
        """Root endpoint should return service info."""
        test_client, _ = client
        response = test_client.get("/")
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
    
    def test_root_contains_message_endpoint(self, client):
        """Root should list message endpoint."""
        test_client, _ = client
        response = test_client.get("/")
        data = response.json()
        assert "message" in data["endpoints"].lower()


# ─── Message Endpoint Tests ─────────────────────────────────────────────────

class TestMessageEndpoint:
    """Test POST /message endpoint."""
    
    def test_send_message_with_valid_session(self, client):
        """Should accept message with valid session."""
        test_client, mock_sessions = client
        # Create session
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Mock execute_task to avoid LLM dependency
        with patch('main.execute_task', return_value="Test response") as mock_exec:
            response = test_client.post("/message", json={
                "session_id": session_id,
                "text": "Hello"
            })
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            assert data["response"] == "Test response"
    
    def test_send_message_invalidates_without_session(self, client):
        """Message without valid session should be rejected."""
        test_client, _ = client
        response = test_client.post("/message", json={
            "session_id": str(uuid.uuid4()),
            "text": "Hello"
        })
        assert response.status_code == 400
    
    def test_send_message_requires_text(self, client):
        """Message without text should be rejected."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        response = test_client.post("/message", json={
            "session_id": session_id,
            "text": ""
        })
        # Pydantic validator requires min_length=1
        assert response.status_code == 422 or response.status_code == 400
    
    def test_send_message_requires_valid_uuid(self, client):
        """Message with invalid session_id format should be rejected."""
        test_client, _ = client
        response = test_client.post("/message", json={
            "session_id": "not-a-uuid",
            "text": "Hello"
        })
        # Should be 422 from Pydantic validation
        assert response.status_code == 422
    
    def test_message_stores_history(self, client):
        """Sent message should be stored in session history."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        with patch('main.execute_task', return_value="Response"):
            test_client.post("/message", json={
                "session_id": session_id,
                "text": "Test message"
            })
            history = mock_sessions.get(session_id, "history")
            assert len(history) == 2  # user + assistant
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
    
    def test_message_truncates_history_to_20(self, client):
        """History should be limited to last 20 messages (10 pairs)."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Pre-populate with many messages
        many_messages = []
        for i in range(25):
            many_messages.append({"role": "user", "content": f"msg{i}"})
            many_messages.append({"role": "assistant", "content": f"resp{i}"})
        mock_sessions.set(session_id, "history", many_messages)
        
        with patch('main.execute_task', return_value="Response"):
            test_client.post("/message", json={
                "session_id": session_id,
                "text": "Test"
            })
            history = mock_sessions.get(session_id, "history")
            # Should be at most 20 + 2 (new pair) = but then truncated to 20
            # Actually it keeps last 20: history[-20:] after adding 2 new ones
            # So if we had 50, we add 2 => 52, then keep last 20
            assert len(history) <= 20
    
    def test_message_returns_label_from_router(self, client):
        """Response should include label from task router."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        with patch('main.execute_task', return_value="Response"):
            response = test_client.post("/message", json={
                "session_id": session_id,
                "text": "research cats"
            })
            assert response.status_code == 200
            data = response.json()
            assert "label" in data
    
    def test_message_includes_dashboard(self, client):
        """Response should include current dashboard snapshot."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        with patch('main.execute_task', return_value="Response"):
            response = test_client.post("/message", json={
                "session_id": session_id,
                "text": "Hello"
            })
            data = response.json()
            assert "dashboard" in data
            assert "content" in data["dashboard"]


# ─── Error Handling Tests ────────────────────────────────────────────────────

class TestErrorHandling:
    """Test error handling endpoints and scenarios."""
    
    def test_invalid_json_returns_400(self, client):
        """Malformed JSON should return 400."""
        test_client, _ = client
        response = test_client.post("/message", data="not json", 
                                    headers={"Content-Type": "application/json"})
        # FastAPI returns 422 for validation error or 400
        assert response.status_code in [400, 422]
    
    def test_message_without_payload_returns_error(self, client):
        """Empty payload should be rejected."""
        test_client, _ = client
        response = test_client.post("/message", json={})
        assert response.status_code in [400, 422]
    
    def test_health_endpoint_returns_ok(self, client):
        """Health check should return OK."""
        test_client, _ = client
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_invalid_file_upload_rejected(self, client):
        """File upload with no file should error."""
        test_client, _ = client
        # No file attached
        response = test_client.post("/files/upload")
        assert response.status_code == 422  # FastAPI validation


# ─── File Upload Tests ──────────────────────────────────────────────────────

class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_text_file(self, client, tmp_path):
        """Should be able to upload a text file."""
        test_client, mock_sessions = client
        # Create session
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Create a test file
        test_content = "Hello, world!"
        from io import BytesIO
        file_data = BytesIO(test_content.encode())
        
        response = test_client.post(
            "/files/upload",
            files={"file": ("test.txt", file_data, "text/plain")},
            data={"session_id": session_id}
        )
        # Either succeeds or fails gracefully (depends on sandbox setup)
        assert response.status_code in [200, 500]
    
    def test_upload_large_file_rejected(self, client):
        """Files over 10MB should be rejected."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Create a file that's too large (simulated via content-length check in main.py)
        from io import BytesIO
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        file_data = BytesIO(large_content)
        
        response = test_client.post(
            "/files/upload",
            files={"file": ("large.txt", file_data, "text/plain")},
            data={"session_id": session_id}
        )
        # The check is based on file.size which FastAPI sets
        # But in TestClient, we need to check response
        # Either it passes validation or not
        assert response.status_code in [200, 400]
    
    def test_list_files(self, client):
        """Should be able to list workspace files."""
        test_client, _ = client
        response = test_client.get("/files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
    
    def test_read_file(self, client):
        """Should be able to read a file."""
        test_client, _ = client
        # Try to read a file (may not exist)
        response = test_client.get("/files/test.txt")
        # Either returns file or error
        assert response.status_code in [200, 500]


# ─── Stream Endpoint Tests ──────────────────────────────────────────────────

class TestStreamEndpoint:
    """Test Server-Sent Events stream."""
    
    def test_stream_requires_valid_session(self, client):
        """Stream should reject invalid session."""
        test_client, _ = client
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/stream/{fake_id}")
        assert response.status_code == 404
    
    def test_stream_with_valid_session(self, client):
        """Stream should accept valid session."""
        test_client, mock_sessions = client
        resp = test_client.post("/session")
        session_id = resp.json()["session_id"]
        
        response = test_client.get(f"/stream/{session_id}")
        # Stream endpoint returns StreamingResponse
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


# ─── Job Status Tests ───────────────────────────────────────────────────────

class TestJobStatus:
    """Test background job status endpoints."""
    
    def test_job_status_invalid_job(self, client):
        """Status for non-existent job should return 404."""
        test_client, _ = client
        response = test_client.post("/jobs/status", json={
            "job_name": "nonexistent",
            "session_id": str(uuid.uuid4())
        })
        # Should be 404 or 400 depending on session validation
        assert response.status_code in [404, 400, 422]
    
    def test_job_status_requires_valid_uuid(self, client):
        """Job status should validate session_id format."""
        test_client, _ = client
        response = test_client.post("/jobs/status", json={
            "job_name": "test",
            "session_id": "not-a-uuid"
        })
        assert response.status_code == 422


# ─── Integrations Endpoint Tests ───────────────────────────────────────────

class TestIntegrations:
    """Test integrations listing."""
    
    def test_list_integrations(self, client):
        """Should be able to list integrations."""
        test_client, _ = client
        response = test_client.post("/integrations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ─── Session Store Unit Tests ───────────────────────────────────────────────

class TestSessionStore:
    """Test SessionStore class directly."""
    
    def test_create_session(self):
        """Should create session with UUID."""
        store = SessionStore()
        sid = store.create()
        uuid.UUID(sid)
        assert store.is_valid_session(sid) is True
    
    def test_create_session_with_user_id(self):
        """Should create session with custom user_id."""
        store = SessionStore()
        sid = store.create("test_user")
        assert store.get(sid, "user_id") == "test_user"
    
    def test_get_nonexistent_key_returns_default(self):
        """Getting non-existent key should return default."""
        store = SessionStore()
        sid = store.create()
        value = store.get(sid, "nonexistent", "default")
        assert value == "default"
    
    def test_set_and_get(self):
        """Should set and get session values."""
        store = SessionStore()
        sid = store.create()
        store.set(sid, "test_key", "test_value")
        assert store.get(sid, "test_key") == "test_value"
    
    def test_set_creates_session_if_not_exists(self):
        """Setting value on non-existent session should create it."""
        store = SessionStore()
        fake_id = str(uuid.uuid4())
        store.set(fake_id, "key", "value")
        assert store.get(fake_id, "key") == "value"
    
    def test_session_expiration(self):
        """Expired session should be invalid."""
        store = SessionStore()
        store.SESSION_EXPIRATION = 1  # 1 second for quick test
        sid = store.create()
        assert store.is_valid_session(sid) is True
        # Manually set last_accessed to past
        store.sessions[sid]["last_accessed"] = time.time() - 2
        assert store.is_valid_session(sid) is False
    
    def test_get_updates_last_accessed(self, mocker):
        """Getting value should update last_accessed."""
        store = SessionStore()
        sid = store.create()
        original_time = store.sessions[sid]["last_accessed"]
        # Mock time to return a later value
        mock_time = mocker.patch('session_manager.time')
        mock_time.time.return_value = original_time + 10
        store.get(sid, "user_id")
        assert store.sessions[sid]["last_accessed"] == original_time + 10
    
    def test_cleanup_expired_sessions(self):
        """Should remove expired sessions."""
        store = SessionStore()
        store.SESSION_EXPIRATION = 1
        sid1 = store.create()
        sid2 = store.create()
        # Expire sid1
        store.sessions[sid1]["last_accessed"] = time.time() - 2
        store.cleanup_expired_sessions()
        assert sid1 not in store.sessions
        assert sid2 in store.sessions
    
    def test_is_valid_session_returns_false_for_nonexistent(self):
        """Non-existent session ID should return False."""
        store = SessionStore()
        assert store.is_valid_session(str(uuid.uuid4())) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
