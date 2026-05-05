# DRIVER/telemetry_logger.py
# [GOAL] Persistent action log for SaaS transparency.

import time
import json
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class TelemetryEntry:
    """A single logged action / thought."""
    entry_id:    str
    timestamp:   float
    user_id:     str
    session_id:  str
    event_type:  str          # "thought" | "action" | "tool_call" | "error" | "completion"
    tool_name:   Optional[str]            = None
    input_data:  Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float]          = None
    metadata:    Dict[str, Any]           = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── SQLite backend ────────────────────────────────────────────────────────────

class TelemetryLogger:
    """Thread-safe persistent telemetry store."""

    def __init__(self, db_path: str = "storage/telemetry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id           TEXT PRIMARY KEY,
                    timestamp    REAL NOT NULL,
                    user_id      TEXT NOT NULL,
                    session_id   TEXT NOT NULL,
                    event_type   TEXT NOT NULL,
                    tool_name    TEXT,
                    input_json   TEXT,
                    output_json  TEXT,
                    duration_ms  REAL,
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
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO telemetry VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            entry.entry_id,
                            entry.timestamp,
                            entry.user_id,
                            entry.session_id,
                            entry.event_type,
                            entry.tool_name,
                            json.dumps(entry.input_data)  if entry.input_data  else None,
                            json.dumps(entry.output_data) if entry.output_data else None,
                            entry.duration_ms,
                            json.dumps(entry.metadata)    if entry.metadata    else None,
                        ),
                    )
            except Exception as exc:
                print(f"[Telemetry] Write error: {exc}")

    def get_session_logs(self, user_id: str, session_id: str,
                         limit: int = 50) -> List[TelemetryEntry]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM telemetry
                   WHERE user_id = ? AND session_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, session_id, limit),
            ).fetchall()

        result = []
        for row in rows:
            result.append(TelemetryEntry(
                entry_id=row["id"],
                timestamp=row["timestamp"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                event_type=row["event_type"],
                tool_name=row["tool_name"],
                input_data=json.loads(row["input_json"])     if row["input_json"]   else None,
                output_data=json.loads(row["output_json"])   if row["output_json"]  else None,
                duration_ms=row["duration_ms"],
                metadata=json.loads(row["metadata_json"])    if row["metadata_json"] else {},
            ))
        return result


# Global logger
telemetry = TelemetryLogger()


# ── Decorator ─────────────────────────────────────────────────────────────────

def log_telemetry(event_type: str, tool_name: str = None):
    """Decorator — auto-logs function calls to telemetry DB."""
    def decorator(func):
        def wrapper(*args, user_id: str = None, session_id: str = None, **kwargs):
            if not user_id:
                return func(*args, **kwargs)

            start    = time.time()
            entry_id = f"{event_type}_{int(start * 1000)}"
            try:
                result   = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                telemetry.log(TelemetryEntry(
                    entry_id=entry_id + "_ok",
                    timestamp=start,
                    user_id=user_id,
                    session_id=session_id or "unknown",
                    event_type=event_type,
                    tool_name=tool_name or func.__name__,
                    input_data={"kwargs": {k: str(v)[:100] for k, v in kwargs.items()}},
                    output_data={"result": str(result)[:500]},
                    duration_ms=duration,
                    metadata={"status": "success"},
                ))
                return result
            except Exception as exc:
                duration = (time.time() - start) * 1000
                telemetry.log(TelemetryEntry(
                    entry_id=entry_id + "_err",
                    timestamp=start,
                    user_id=user_id,
                    session_id=session_id or "unknown",
                    event_type="error",
                    tool_name=tool_name or func.__name__,
                    output_data={"error": str(exc)},
                    duration_ms=duration,
                    metadata={"status": "failed"},
                ))
                raise
        return wrapper
    return decorator


# ── UI formatter ──────────────────────────────────────────────────────────────

def format_telemetry_for_ui(entries: List[TelemetryEntry]) -> str:
    """Format telemetry entries for display in the Chainlit sidebar."""
    if not entries:
        return "No recent activity"

    icons = {
        "thought":    "🧠",
        "action":     "🔧",
        "tool_call":  "🔧",
        "completion": "✅",
        "error":      "❌",
    }

    output = "### Recent Activity\n\n"
    for entry in entries[:10]:
        dt   = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
        icon = icons.get(entry.event_type, "📝")
        output += f"**{icon} {entry.event_type.title()}** · {dt}\n"
        if entry.tool_name:
            output += f"Tool: `{entry.tool_name}`\n"
        if entry.duration_ms:
            output += f"Duration: {entry.duration_ms:.0f}ms\n"
        output += "\n"

    return output