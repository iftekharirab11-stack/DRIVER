"""
Session Management Module for Driver AI
Handles session creation, validation, and expiration
"""

import time
import uuid
import threading
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.SESSION_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds
        self.MAX_SESSIONS_PER_USER = 5  # Prevent session flooding
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # Cleanup every hour

    def create(self, user_id: str) -> str:
        """Create a new session"""
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            "user_id": user_id,
            "history": [],
            "created_at": time.time(),
            "last_accessed": time.time()
        }
        return sid

    def get(self, sid: str, key: str, default: Any = None) -> Any:
        """Get a value from a session"""
        session = self.sessions.get(sid)
        if session and self._is_session_valid(session):
            session["last_accessed"] = time.time()
            return session.get(key, default)
        return default

    def set(self, sid: str, key: str, value: Any) -> None:
        """Set a value in a session"""
        session = self.sessions.get(sid)
        if session and self._is_session_valid(session):
            session["last_accessed"] = time.time()
            session[key] = value
        elif not session:
            # Cannot create session without user context - this should not happen in production
            raise ValueError("Cannot set value on non-existent session. Session must be created with a valid user_id first.")

    def _is_session_valid(self, session: Dict[str, Any]) -> bool:
        """Check if session is still valid (not expired)"""
        return time.time() - session["last_accessed"] < self.SESSION_EXPIRATION

    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if current_time - session["last_accessed"] >= self.SESSION_EXPIRATION
        ]
        for sid in expired_sessions:
            del self.sessions[sid]

    def is_valid_session(self, sid: str) -> bool:
        """Check if a session ID is valid and not expired"""
        session = self.sessions.get(sid)
        return session is not None and self._is_session_valid(session)

    def create_for_user(self, user_id: str) -> str:
        """Create a new session for a specific user with proper validation"""
        with self._lock:
            # Check if user already has too many active sessions
            user_sessions = [sid for sid, session in self.sessions.items()
                           if session.get("user_id") == user_id and self._is_session_valid(session)]

            if len(user_sessions) >= self.MAX_SESSIONS_PER_USER:
                raise RuntimeError(f"User {user_id} has too many active sessions ({len(user_sessions)} >= {self.MAX_SESSIONS_PER_USER})")

            # Create new session
            sid = str(uuid.uuid4())
            self.sessions[sid] = {
                "user_id": user_id,
                "history": [],
                "created_at": time.time(),
                "last_accessed": time.time(),
                "ip_address": None,
                "user_agent": None
            }

            logger.info(f"Created session {sid} for user {user_id}")
            return sid

    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active session IDs for a user"""
        return [sid for sid, session in self.sessions.items()
               if session.get("user_id") == user_id and self._is_session_valid(session)]

    def terminate_user_sessions(self, user_id: str) -> int:
        """Terminate all sessions for a specific user"""
        with self._lock:
            terminated = 0
            for sid, session in list(self.sessions.items()):
                if session.get("user_id") == user_id:
                    del self.sessions[sid]
                    terminated += 1
                    logger.info(f"Terminated session {sid} for user {user_id}")

            return terminated

    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if current_time - session["last_accessed"] >= self.SESSION_EXPIRATION
        ]
        for sid in expired_sessions:
            user_id = self.sessions[sid].get("user_id", "unknown")
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session {sid} for user {user_id}")

    def auto_cleanup_if_needed(self) -> None:
        """Automatically cleanup sessions if interval has passed"""
        current_time = time.time()
        if current_time - self._last_cleanup >= self._cleanup_interval:
            self.cleanup_expired_sessions()
            self._last_cleanup = current_time

    def get_session_user(self, sid: str) -> Optional[str]:
        """Get the user ID for a session"""
        session = self.sessions.get(sid)
        if session and self._is_session_valid(session):
            return session.get("user_id")
        return None

    def validate_session_ownership(self, sid: str, user_id: str) -> bool:
        """Validate that a session belongs to the specified user"""
        session = self.sessions.get(sid)
        if not session or not self._is_session_valid(session):
            return False
        return session.get("user_id") == user_id

    def update_session_activity(self, sid: str) -> bool:
        """Update last accessed time for a session"""
        session = self.sessions.get(sid)
        if session and self._is_session_valid(session):
            session["last_accessed"] = time.time()
            return True
        return False
