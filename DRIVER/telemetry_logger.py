# [GOAL] Transparency for SaaS Users
# [OUTPUT] A visual log of every action the AI took in the background.
# STORAGE: SQLite database for queries + in-memory cache for UI.

import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading

# ─────────────────────────────────────────────
# Data Model
# ─────────────────────────────────────────────
@dataclass
class TelemetryEntry:
    """Single logged action/thought."""
    entry_id: str
    timestamp: float
    user_id: str
    session_id: str
    event_type: str  # "thought", "action", "tool_call", "error", "completion"
    tool_name: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ─────────────────────────────────────────────
# SQLite Backend
# ─────────────────────────────────────────────
class TelemetryLogger:
    """Persistent logging system for AI actions."""
    
    def __init__(self, db_path: str = "storage/telemetry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._lock = threading.Lock()
    
    def _init_db(self):
        """Create SQLite tables if missing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    tool_name TEXT,
                    input_json TEXT,
                    output_json TEXT,
                    duration_ms REAL,
                    metadata_json TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_session 
                ON telemetry (user_id, session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON telemetry (timestamp DESC)
            """)
            conn.commit()
    
    def log(self, entry: TelemetryEntry):
        """Write a telemetry entry to DB."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO telemetry VALUES 
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.entry_id,
                        entry.timestamp,
                        entry.user_id,
                        entry.session_id,
                        entry.event_type,
                        entry.tool_name,
                        json.dumps(entry.input_data) if entry.input_data else None,
                        json.dumps(entry.output_data) if entry.output_data else None,
                        entry.duration_ms,
                        json.dumps(entry.metadata) if entry.metadata else None
                    ))
            except Exception as e:
                print(f"Telemetry logging error: {e}")
    
    def get_session_logs(self, user_id: str, session_id: str, 
                        limit: int = 50) -> List[TelemetryEntry]:
        """Fetch logs for a specific session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM telemetry 
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (user_id, session_id, limit)).fetchall()
        
        entries = []
        for row in rows:
            entry = TelemetryEntry(
                entry_id=row["id"],
                timestamp=row["timestamp"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                event_type=row["event_type"],
                tool_name=row["tool_name"],
                input_data=json.loads(row["input_json"]) if row["input_json"] else None,
                output_data=json.loads(row["output_json"]) if row["output_json"] else None,
                duration_ms=row["duration_ms"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None
            )
            entries.append(entry)
        return entries
    
    def get_recent_errors(self, hours: int = 1) -> List[TelemetryEntry]:
        """Get recent error events for monitoring."""
        cutoff = time.time() - (hours * 3600)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM telemetry 
                WHERE event_type = 'error' AND timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff,)).fetchall()
        
        return [TelemetryEntry(**dict(row)) for row in rows]

# Global logger instance
telemetry = TelemetryLogger()

# ─────────────────────────────────────────────
# Convenience Decorators
# ─────────────────────────────────────────────
def log_telemetry(event_type: str, tool_name: str = None):
    """Decorator to auto-log function calls."""
    def decorator(func):
        def wrapper(*args, user_id: str = None, session_id: str = None, **kwargs):
            if not user_id:
                return func(*args, **kwargs)
            
            entry_id = f"{event_type}_{int(time.time() * 1000)}"
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                
                telemetry.log(TelemetryEntry(
                    entry_id=entry_id + "_success",
                    timestamp=start,
                    user_id=user_id,
                    session_id=session_id or "unknown",
                    event_type=event_type,
                    tool_name=tool_name or func.__name__,
                    input_data={"args": str(args)[:200], "kwargs": {k: str(v)[:100] for k, v in kwargs.items()}},
                    output_data={"result": str(result)[:500]},
                    duration_ms=duration,
                    metadata={"status": "success"}
                ))
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                telemetry.log(TelemetryEntry(
                    entry_id=entry_id + "_error",
                    timestamp=start,
                    user_id=user_id,
                    session_id=session_id or "unknown",
                    event_type="error",
                    tool_name=tool_name or func.__name__,
                    input_data={"args": str(args)[:200]},
                    output_data={"error": str(e)},
                    duration_ms=duration,
                    metadata={"status": "failed"}
                ))
                raise
        
        return wrapper
    return decorator

# ─────────────────────────────────────────────
# Formatting for UI
# ─────────────────────────────────────────────
def format_telemetry_for_ui(entries: List[TelemetryEntry]) -> str:
    """Format entries for display in Chainlit sidebar."""
    if not entries:
        return "No recent activity"
    
def get_sidebar_data(user_id):
    return {
        "connections": ["GitHub", "Google Cal"], # Add GitHub here
        "active_jobs": [],
        "tier": "Pro"
    }
    
    output = "### Recent Activity\n\n"
    for entry in entries[:10]:  # Show last 10
        dt = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
        icon = "🧠" if entry.event_type == "thought" else \
               "🔧" if entry.event_type == "action" else \
               "✅" if entry.event_type == "completion" else \
               "❌" if entry.event_type == "error" else "📝"
        
        output += f"**{icon} {entry.event_type.title()}** · {dt}\n"
        if entry.tool_name:
            output += f"Tool: `{entry.tool_name}`\n"
        if entry.duration_ms:
            output += f"Duration: {entry.duration_ms:.0f}ms\n"
        output += "\n"
    
    return output
