# [GOAL] Dynamic Sidebar for any User
# [CONTEXT] SaaS Architecture: Data is fetched per Session ID.

from typing import Dict, Any, Optional
from datetime import datetime
from DRIVER.task_manager import task_queue
from DRIVER.background_worker import bg_agent

class UserSession:
    """Represents a user session with isolated context."""
    
    def __init__(self, user_id: str, username: str = None):
        self.user_id = user_id
        self.username = username or f"user_{user_id[:8]}"
        self.created_at = datetime.now()
        self.preferences = {}
        self.active_projects = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "active_projects": self.active_projects
        }

# Global session store (in production, use Redis/DB)
_active_sessions: Dict[str, UserSession] = {}

def get_or_create_session(user_id: str, username: str = None) -> UserSession:
    """Get existing session or create new one."""
    if user_id not in _active_sessions:
        _active_sessions[user_id] = UserSession(user_id, username)
    return _active_sessions[user_id]

def get_sidebar_data(user_id: str = "default") -> Dict[str, Any]:
    """Build sidebar context for a specific user session.
    
    Args:
        user_id: Unique user identifier (from auth/token)
    
    Returns:
        Dictionary with sidebar data for UI rendering
    """
    session = get_or_create_session(user_id)
    
    # Gather system status
    queue_status = task_queue.get_status()
    bg_jobs = bg_agent.get_job_status()
    
    # Build active projects from memory
    from DRIVER.memory_system import memory_bank
    user_memories = memory_bank.get_memories("projects", limit=5)
    
    return {
        "user": session.to_dict(),
        "system": {
            "status": "🟢 Online",
            "uptime": "Active",
            "background_jobs_active": len(bg_jobs.get("active", {})),
            "queue_depth": queue_status.get("queued", 0)
        },
        "active_projects": [
            {"name": m["content"][:50], "status": "Active"} 
            for m in user_memories
        ] if user_memories else [
            {"name": "Project Alpha", "status": "Initializing"},
            {"name": "Research Task", "status": "Pending"},
            {"name": "Code Generation", "status": "Idle"}
        ],
        "eta_map": {
            job: bg_jobs["active"][job].split("→")[-1].strip() 
            for job in bg_jobs.get("active", {}) 
            if "→" in bg_jobs["active"][job]
        },
        "quick_actions": [
            {"label": "New Research", "tool": "background_research"},
            {"label": "Check Calendar", "tool": "list_calendar_events"},
            {"label": "Write Script", "tool": "write_to_workspace"},
            {"label": "Execute Code", "tool": "execute_python_code"}
        ]
    }

def update_session_preference(user_id: str, key: str, value: Any):
    """Update user session preferences."""
    session = get_or_create_session(user_id)
    session.preferences[key] = value

def add_user_project(user_id: str, project_name: str):
    """Add a project to user's active list."""
    session = get_or_create_session(user_id)
    session.active_projects.append({
        "name": project_name,
        "status": "Active",
        "created_at": datetime.now().isoformat()
    })