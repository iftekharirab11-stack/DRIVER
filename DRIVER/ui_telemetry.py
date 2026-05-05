import os
from typing import Dict, Any, Optional
from datetime import datetime


class UserSession:
    def __init__(self, user_id: str, username: str = None):
        self.user_id         = user_id
        self.username        = username or f"user_{user_id[:8]}"
        self.created_at      = datetime.now()
        self.preferences: Dict[str, Any] = {}
        self.active_projects = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id":         self.user_id,
            "username":        self.username,
            "created_at":      self.created_at.isoformat(),
            "active_projects": self.active_projects,
        }


_active_sessions: Dict[str, UserSession] = {}


def get_or_create_session(user_id: str, username: str = None) -> UserSession:
    if user_id not in _active_sessions:
        _active_sessions[user_id] = UserSession(user_id, username)
    return _active_sessions[user_id]


def get_sidebar_data(user_id: str = "default") -> Dict[str, Any]:
    session = get_or_create_session(user_id)

    try:
        from DRIVER.task_manager import task_queue
        queue_status = task_queue.get_status()
    except Exception:
        queue_status = {"queued": 0, "running": 0}

    try:
        from DRIVER.background_worker import bg_agent
        bg_jobs = bg_agent.get_job_status()
    except Exception:
        bg_jobs = {"active": {}, "completed_files": []}

    active_projects = []
    try:
        from DRIVER.memory_system import memory_bank
        mems = memory_bank.get_memories("projects", limit=5)
        active_projects = [{"name": m["content"][:50], "status": "Active"} for m in mems]
    except Exception:
        pass

    if not active_projects:
        active_projects = [
            {"name": "Alpha Framework", "status": "Running"},
            {"name": "Background Research", "status": "Idle"},
        ]

    eta_map = {}
    for job, stat in bg_jobs.get("active", {}).items():
        if "→" in str(stat):
            eta_map[job] = stat.split("→")[-1].strip()

    active_jobs_list = [
        {"name": name, "progress": 50, "status": stat}
        for name, stat in bg_jobs.get("active", {}).items()
        if "Running" in str(stat)
    ]

    # Connection monitor
    from DRIVER.connection_monitor import monitor

    return {
        "user": session.to_dict(),
        "system": {
            "status":                 "🟢 Online",
            "uptime":                 "Active",
            "background_jobs_active": len(bg_jobs.get("active", {})),
            "queue_depth":            queue_status.get("queued", 0),
        },
        "connections":       ["GitHub", "Google Cal"],
        "active_jobs":       active_jobs_list,
        "tier":              "Pro",
        "active_projects":   active_projects,
        "eta_map":           eta_map,
        "quick_actions": [
            {"label": "New Research",   "tool": "background_research"},
            {"label": "Check Calendar", "tool": "list_calendar_events"},
            {"label": "Write Script",   "tool": "write_to_workspace"},
            {"label": "Execute Code",   "tool": "execute_python_code"},
        ],
        "connections_detail": monitor.check_all(),
        "missing_env":        monitor.get_missing_env_vars(),
        "actions_required":   monitor.get_action_required(),
        "health_score":       monitor.get_health_score(),
        "primary_model":      os.getenv("PRIMARY_MODEL", "gpt-4o"),
    }


def update_session_preference(user_id: str, key: str, value: Any):
    session = get_or_create_session(user_id)
    session.preferences[key] = value


def add_user_project(user_id: str, project_name: str):
    session = get_or_create_session(user_id)
    session.active_projects.append({
        "name":       project_name,
        "status":     "Active",
        "created_at": datetime.now().isoformat(),
    })