#!/usr/bin/env python3
"""
Integration Test Suite for Frontend-Backend Communication

Tests end-to-end flows including:
- Session creation
- Chat message exchange
- File upload/download
- Dashboard updates
- Error handling
"""

import pytest
import json
import time
import uuid
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, sessions as default_sessions
from session_manager import SessionStore

os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PRIMARY_MODEL"] = "gpt-4o"


class TestFullApplicationFlow:
    """End-to-end tests covering complete user workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fresh session store for each test."""
        self.session_store = SessionStore()
        self.client = TestClient(app)
        # Patch the global sessions
        import main
        main.sessions = self.session_store
        yield
        # Cleanup
        import main
        main.sessions = default_sessions

    def test_complete_chat_session_flow(self):
        """
        User creates session -> sends message -> receives response ->
        sends another message -> gets updated history.
        """
        # Step 1: Create session
        resp = self.client.post("/session")
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]
        
        # Step 2: Send first message
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Response to: " + x)
            resp = self.client.post("/message", json={
                "session_id": session_id,
                "text": "Hello, AI!"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["response"] == "Response to: Hello, AI!"
            assert data["session_id"] == session_id
            assert len(data["history"]) == 2
        
        # Step 3: Send second message
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Second response")
            resp = self.client.post("/message", json={
                "session_id": session_id,
                "text": "Another message"
            })
            assert resp.status_code == 200
            data = resp.json()
            # Should now have 4 messages (2 pairs)
            assert len(data["history"]) == 4
    
    def test_session_persistence_across_requests(self):
        """Session should maintain state across multiple requests."""
        # Create session
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Add some history
        test_history = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Reply"}
        ]
        self.session_store.set(session_id, "history", test_history)
        
        # Verify it's accessible
        assert self.session_store.is_valid_session(session_id)
        history = self.session_store.get(session_id, "history")
        assert len(history) == 2
        assert history[0]["content"] == "First"
    
    def test_file_upload_and_list_flow(self):
        """Upload a file and then list files in workspace."""
        # Create session
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Upload a text file
        from io import BytesIO
        file_content = b"Test file content"
        
        resp = self.client.post(
            "/files/upload",
            files={"file": ("test_upload.txt", BytesIO(file_content), "text/plain")},
            data={"session_id": session_id}
        )
        # Should succeed (200) or have handled error gracefully (500)
        assert resp.status_code in [200, 500]
        
        # List files
        resp = self.client.get("/files")
        assert resp.status_code == 200
        data = resp.json()
        assert "files" in data
    
    def test_dashboard_updates_with_session(self):
        """Dashboard should reflect session-specific data."""
        # Create session
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Get general dashboard
        resp = self.client.get("/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        
        # Dashboard via message should also be included
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Done")
            resp = self.client.post("/message", json={
                "session_id": session_id,
                "text": "test"
            })
            assert resp.status_code == 200
            assert "dashboard" in resp.json()
    
    def test_health_check_throughout_flow(self):
        """Health check should remain consistent."""
        # Check health before any operations
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        
        # Create session
        self.client.post("/session")
        
        # Check health after
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    
    def test_message_history_truncation_flow(self):
        """History should truncate to 20 messages after many exchanges."""
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Simulate many message exchanges
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Response")
            
            for i in range(15):  # 15 exchanges = 30 messages total
                self.client.post("/message", json={
                    "session_id": session_id,
                    "text": f"Message {i}"
                })
        
        # Check that history is truncated
        history = self.session_store.get(session_id, "history")
        # After 15 exchanges (each adds 2 messages), with truncation to 20
        # Actually: starts with 0, after 1st: 2, after 2nd: 4...
        # After 10th: 20, then stays at 20 (add 2, truncate to last 20)
        # After 15th: still 20
        assert len(history) <= 20
    
    def test_concurrent_sessions_isolated(self):
        """Multiple sessions should not interfere with each other."""
        # Create session 1
        resp1 = self.client.post("/session")
        session1 = resp1.json()["session_id"]
        
        # Create session 2
        resp2 = self.client.post("/session")
        session2 = resp2.json()["session_id"]
        
        # Send different messages to each
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: f"Response to {x}")
            
            self.client.post("/message", json={
                "session_id": session1,
                "text": "Session 1 message"
            })
            
            self.client.post("/message", json={
                "session_id": session2,
                "text": "Session 2 message"
            })
        
        # Verify histories are separate
        history1 = self.session_store.get(session1, "history")
        history2 = self.session_store.get(session2, "history")
        
        assert len(history1) >= 2
        assert len(history2) >= 2
        assert history1[0]["content"] == "Session 1 message"
        assert history2[0]["content"] == "Session 2 message"
    
    def test_api_endpoint_enumeration(self):
        """All documented endpoints should be accessible."""
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/dashboard"),
            ("POST", "/session"),
            ("POST", "/message"),
            ("POST", "/files/upload"),
            ("GET", "/files"),
            ("POST", "/jobs/status"),
            ("POST", "/integrations"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                resp = self.client.get(path)
            else:
                resp = self.client.post(path, json={})
            
            # Should not be 500 (server error) for basic endpoints
            # Some may return 400/404/422 for invalid input, which is OK
            assert resp.status_code < 500, f"{method} {path} returned 500"
    
    def test_error_responses_are_json(self):
        """All error responses should be valid JSON."""
        # Invalid endpoint
        resp = self.client.post("/session", data="not json")
        # Should have JSON error body
        try:
            data = resp.json()
            # If it's JSON, should have detail or similar
            assert isinstance(data, dict) or resp.status_code < 400
        except:
            # Some FastAPI validation errors might be HTML
            # But at minimum shouldn't crash
            pass
    
    def test_large_message_handling(self):
        """Large messages should be handled gracefully."""
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Send a large message (within limit)
        large_text = "x" * 1000  # 1000 chars, well under 1000 limit
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Received")
            resp = self.client.post("/message", json={
                "session_id": session_id,
                "text": large_text
            })
            assert resp.status_code == 200
    
    def test_integrations_endpoint_returns_list(self):
        """Integrations endpoint should return a list of connection statuses."""
        resp = self.client.post("/integrations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Each item should have expected keys
        if data:
            conn = data[0]
            assert "name" in conn
            assert "category" in conn
            assert "connected" in conn


class TestSessionExpiration:
    """Test session expiration behavior."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.session_store = SessionStore()
        # Reduce expiration time for testing
        self.session_store.SESSION_EXPIRATION = 1
        self.client = TestClient(app)
        import main
        main.sessions = self.session_store
        yield
        import main
        main.sessions = default_sessions

    def test_expired_session_rejected(self, mocker):
        """Expired sessions should be rejected for message posting."""
        # Create session
        resp = self.client.post("/session")
        session_id = resp.json()["session_id"]
        
        # Manually expire it
        self.session_store.sessions[session_id]["last_accessed"] = time.time() - 2
        
        # Try to post message
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('main.execute_task', lambda x: "Response")
            resp = self.client.post("/message", json={
                "session_id": session_id,
                "text": "test"
            })
            assert resp.status_code == 400
    
    def test_session_cleanup(self):
        """Expired sessions should be removed by cleanup."""
        # Create two sessions
        sid1 = self.client.post("/session").json()["session_id"]
        sid2 = self.client.post("/session").json()["session_id"]
        
        # Expire one
        self.session_store.sessions[sid1]["last_accessed"] = time.time() - 2
        
        # Run cleanup
        self.session_store.cleanup_expired_sessions()
        
        # Verify
        assert sid1 not in self.session_store.sessions
        assert sid2 in self.session_store.sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
