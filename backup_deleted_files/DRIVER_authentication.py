# [GOAL] Multi-Tenant Auth & Session Management
# [CONTEXT] Limits: Free = 100K tokens/mo, Pro = Unlimited.

import secrets
import hashlib
import json
import os
from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# Subscription tiers
class Tier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

TIER_LIMITS = {
    Tier.FREE: {"monthly_tokens": 100_000, "max_concurrent": 3, "features": ["basic"]},
    Tier.PRO: {"monthly_tokens": float('inf'), "max_concurrent": 10, "features": ["all"]},
    Tier.ENTERPRISE: {"monthly_tokens": float('inf'), "max_concurrent": 100, "features": ["all", "custom"]}
}

@dataclass
class User:
    """User account with subscription."""
    user_id: str
    username: str
    email: str
    tier: Tier = Tier.FREE
    token_usage_month: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    subscription_end: Optional[datetime] = None
    
    def is_pro(self) -> bool:
        return self.tier != Tier.FREE
    
    def remaining_tokens(self) -> int:
        limit = TIER_LIMITS[self.tier]["monthly_tokens"]
        used = self.token_usage_month
        return max(0, limit - used) if limit != float('inf') else float('inf')
    
    def can_use_more(self, requested_tokens: int = 1000) -> bool:
        return self.remaining_tokens() >= requested_tokens

@dataclass
class Session:
    """Active user session."""
    session_id: str
    user: User
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def is_valid(self, max_hours: int = 24) -> bool:
        age = datetime.now() - self.created_at
        return age < timedelta(hours=max_hours)
    
    def touch(self):
        self.last_active = datetime.now()

class AuthManager:
    """Handles authentication, sessions, and tier enforcement."""
    
    def __init__(self, storage_path: str = "auth_store.json"):
        self.storage_path = storage_path
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self._load()
    
    def _load(self):
        """Load auth data from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Load users
                    for uid, udata in data.get("users", {}).items():
                        tier = Tier(udata.get("tier", "free"))
                        user = User(
                            user_id=uid,
                            username=udata["username"],
                            email=udata["email"],
                            tier=tier,
                            token_usage_month=udata.get("token_usage_month", 0),
                            created_at=datetime.fromisoformat(udata["created_at"]),
                            subscription_end=datetime.fromisoformat(udata["subscription_end"]) 
                                            if udata.get("subscription_end") else None
                        )
                        self.users[uid] = user
            except Exception:
                pass
    
    def _save(self):
        """Persist auth data."""
        data = {
            "users": {
                uid: {
                    "username": u.username,
                    "email": u.email,
                    "tier": u.tier.value,
                    "token_usage_month": u.token_usage_month,
                    "created_at": u.created_at.isoformat(),
                    "subscription_end": u.subscription_end.isoformat() if u.subscription_end else None
                }
                for uid, u in self.users.items()
            }
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def register_user(self, username: str, email: str, password: str, 
                      tier: Tier = Tier.FREE) -> User:
        """Register a new user."""
        user_id = secrets.token_urlsafe(16)
        # In production, hash the password properly
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            tier=tier
        )
        self.users[user_id] = user
        self._save()
        return user
    
    def login(self, email: str, password: str) -> Optional[Session]:
        """Authenticate user and create session."""
        # Find user by email (simplified - in prod use proper auth)
        user = next((u for u in self.users.values() if u.email == email), None)
        if not user:
            return None
        
        # In production, verify password hash
        session_id = secrets.token_urlsafe(32)
        session = Session(
            session_id=session_id,
            user=user,
            ip_address="0.0.0.0"  # Would be extracted from request
        )
        self.sessions[session_id] = session
        return session
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate and refresh session."""
        session = self.sessions.get(session_id)
        if session and session.is_valid():
            session.touch()
            return session
        return None
    
    def logout(self, session_id: str) -> bool:
        """Invalidate session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def upgrade_user(self, user_id: str, new_tier: Tier) -> bool:
        """Upgrade user subscription."""
        user = self.users.get(user_id)
        if user:
            user.tier = new_tier
            self._save()
            return True
        return False
    
    def add_usage(self, user_id: str, tokens: int):
        """Add token usage to user's monthly total."""
        user = self.users.get(user_id)
        if user:
            user.token_usage_month += tokens
            self._save()

# Global auth manager
auth = AuthManager()

# [GOAL] Middleware helpers for FastAPI/Chainlit
def get_current_user(session_id: str) -> Optional[User]:
    """Extract user from session."""
    session = auth.validate_session(session_id)
    return session.user if session else None

def check_rate_limit(user: User, requested_tokens: int = 1000) -> tuple[bool, str]:
    """Check if user can make this call."""
    if not user.can_use_more(requested_tokens):
        remaining = user.remaining_tokens()
        return False, f"Token limit exceeded. Remaining: {remaining}"
    
    limits = TIER_LIMITS[user.tier]
    active_sessions = sum(1 for s in auth.sessions.values() 
                         if s.user.user_id == user.user_id and s.is_valid())
    if active_sessions >= limits["max_concurrent"]:
        return False, "Max concurrent sessions reached"
    
    return True, "OK"

def create_demo_user() -> User:
    """Create a demo user for testing."""
    return auth.register_user(
        username="demo",
        email="demo@alpha.ai",
        password="demo123",
        tier=Tier.FREE
    )