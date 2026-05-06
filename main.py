from __future__ import annotations

import asyncio
import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from DRIVER.core_brain import execute_task
from DRIVER.task_router import router
from DRIVER.ui_telemetry import get_sidebar_data

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Alpha SaaS API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (replaces cl.user_session) ───────────────────────

class SessionStore:
    def __init__(self):
        self.sessions = {}

    def create(self, user_id: str = "demo_user") -> str:
        sid = str(uuid.uuid4())
        self.sessions[sid] = {"user_id": user_id, "history": []}
        return sid

    def get(self, sid: str, key: str, default=None):
        return self.sessions.get(sid, {}).get(key, default)

    def set(self, sid: str, key: str, value):
        if sid not in self.sessions:
            self.sessions[sid] = {}
        self.sessions[sid][key] = value

sessions = SessionStore()

# ── Dashboard builder (unchanged logic, returns plain dict) ──────────────────

def build_dashboard(user_id: str = "demo_user") -> dict:
    data = get_sidebar_data(user_id)

    conns = data.get("connections_detail", [])
    score = data.get("health_score", 0)
    model = data.get("primary_model", "?")
    missing = data.get("missing_env", [])
    actions = data.get("actions_required", [])
    system = data.get("system", {})

    filled = round(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    color = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"

    lines = []
    lines.append("## 🖥️ ALPHA DASHBOARD\n\n")
    lines.append(f"**Model:** `{model}`  {color} Health `{score}/100`\n")
    lines.append(f"`{bar}`\n\n")
    lines.append(f"**Queue:** `{system.get('queue_depth', 0)}`  ")
    lines.append(f"**BG Jobs:** `{system.get('background_jobs_active', 0)}`\n\n")

    lines.append("### 🔌 CONNECTIONS\n\n")
    for cat in ["LLM", "Google", "Memory", "Execution", "MCP"]:
        group = [c for c in conns if c["category"] == cat]
        if not group:
            continue
        lines.append(f"**{cat}**\n\n")
        lines.append("| Service | Status | Note |\n")
        lines.append("|---------|--------|------|\n")
        for c in group:
            icon = c["icon"]
            name = c["name"]
            err = (c.get("error") or "")[:60]
            miss = ", ".join(c.get("missing_env", []))
            latency = f" `{c['latency_ms']:.0f}ms`" if c.get("latency_ms") else ""
            if c["connected"]:
                lines.append(f"| {icon} **{name}** | ✅ Connected{latency} | — |\n")
            elif miss:
                lines.append(f"| {icon} **{name}** | 🔑 Missing key | `{miss}` |\n")
            else:
                lines.append(f"| {icon} **{name}** | ❌ {err} | |\n")
        lines.append("\n")

    if missing:
        lines.append("### 🔑 MISSING ENV VARS\n\n")
        for m in missing:
            lines.append(f"- `{m}`\n")
        lines.append("\n")

    if actions:
        lines.append("### ⚡ ACTION REQUIRED\n\n")
        for a in actions:
            lines.append(f"- {a}\n")
        lines.append("\n")

    lines.append("### 🔄 ACTIVE JOBS\n\n")
    jobs = data.get("active_jobs", [])
    if jobs:
        for job in jobs:
            pct = job.get("progress", 0)
            bar2 = "█" * round(pct / 10) + "░" * (10 - round(pct / 10))
            lines.append(f"- **{job['name']}** `{bar2}` {pct}%\n")
    else:
        lines.append("*No active background tasks.*\n")
    lines.append("\n")

    lines.append("### 📁 WORKSPACE\n\n")
    try:
        files = os.listdir("WORKSPACE") if os.path.exists("WORKSPACE") else []
        if files:
            for f in files[-5:]:
                size = os.path.getsize(f"WORKSPACE/{f}")
                lines.append(f"- `{f}` ({size}b)\n")
        else:
            lines.append("*Empty*\n")
    except Exception:
        lines.append("*Unavailable*\n")
    lines.append("\n")

    lines.append("### 🚦 TASK ROUTER\n\n")
    lines.append("| Say this…        | Routes to          |\n")
    lines.append("|------------------|--------------------|\n")
    lines.append("| `research [topic]` | Background worker |\n")
    lines.append("| `email [person]`   | Gmail via MCP     |\n")
    lines.append("| `calendar [event]` | Google Calendar   |\n")
    lines.append("| `remember [info]`  | Memory system     |\n")
    lines.append("| `run [script.py]`  | Python Executor   |\n")
    lines.append("| `search [query]`   | Tavily Search     |\n")
    lines.append("| `status`           | Dashboard refresh |\n")

    content = "".join(lines)
    return {"content": content, "score": score, "model": model, "system": system}

# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "Alpha SaaS (no-chainlit)",
        "endpoints": {
            "POST /session": "Create a new chat session",
            "POST /message": "Send a message (JSON: {session_id, text})",
            "GET /stream/{session_id}": "SSE stream for live dashboard updates",
            "GET /dashboard": "Get current dashboard snapshot",
        },
    }

@app.post("/session")
async def create_session():
    sid = sessions.create()
    return {"session_id": sid, "user_id": sessions.get(sid, "user_id")}

@app.get("/dashboard")
async def get_dashboard():
    return build_dashboard()

# ── Server-Sent Events stream (dashboard auto-refresh) ────────────────────────

async def dashboard_event_generator(session_id: str):
    """Yield dashboard snapshots every 30s as Server-Sent Events."""
    while True:
        await asyncio.sleep(30)
        try:
            dash = build_dashboard(sessions.get(session_id, "user_id", "demo_user"))
            yield f"data: {json.dumps(dash)}\n\n"
        except Exception:
            yield 'event: error\ndata: {"error":"dashboard unavailable"}\n\n'

@app.get("/stream/{session_id}")
async def stream_dashboard(session_id: str):
    if session_id not in sessions.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return StreamingResponse(
        dashboard_event_generator(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# ── Message handler ───────────────────────────────────────────────────────────

@app.post("/message")
async def handle_message(payload: dict):
    """
    JSON body:
    {
      "session_id": "uuid",
      "text": "research cats"
    }
    """
    session_id = payload.get("session_id")
    text = payload.get("text", "").strip()

    if not session_id or session_id not in sessions.sessions:
        raise HTTPException(status_code=400, detail="Invalid or missing session_id")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text'")

    route_info = router.route(text)
    label = route_info.get("tool_hint", "🤖 AI Agent")

    user_id = sessions.get(session_id, "user_id", "demo_user")
    history = sessions.get(session_id, "history", [])

    try:
        # Pass user_id explicitly in case execute_task signature changes
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: execute_task(text, user_id=user_id)
        )
    except Exception as e:
        response = (
            f"⚠️ **Error:** `{type(e).__name__}: {e}`\n\n"
            "Check Dashboard → **ACTION REQUIRED** for missing keys."
        )

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response})
    sessions.set(session_id, "history", history[-20:])

    # Include job status for background tasks
    job_status = None
    try:
        from DRIVER.background_worker import bg_agent
        job_status = bg_agent.get_job_status()
    except Exception:
        pass

    return {
        "session_id": session_id,
        "label": label,
        "input": text,
        "response": response,
        "dashboard": build_dashboard(user_id),
        "history": history[-20:],
        "job_status": job_status,
    }

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get status of a specific task."""
    try:
        from DRIVER.background_worker import bg_agent
        status = bg_agent.get_job_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/jobs/status")
async def check_job_status(payload: dict):
    """Check status of a background job."""
    job_name = payload.get("job_name")
    if not job_name:
        raise HTTPException(status_code=400, detail="job_name required")
    try:
        from DRIVER.background_worker import bg_agent
        status = bg_agent.get_job_status(job_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/integrations")
async def list_integrations():
    """List available integrations and their status."""
    try:
        from DRIVER.connection_monitor import monitor
        return monitor.check_all()
    except Exception as e:
        return []

from fastapi import UploadFile, File

@app.post("/files/upload")
async def upload_file(session_id: str = None, file: UploadFile = File(...)):
    """Upload a file to user's workspace."""
    user_id = "demo_user"
    from DRIVER.sandbox_driver import write_to_sandbox, create_sandbox
    create_sandbox(user_id)
    
    content = await file.read()
    try:
        text = content.decode('utf-8')
        result = write_to_sandbox(user_id, file.filename, text)
        return {"filename": file.filename, "path": result, "status": "uploaded"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.get("/files")
async def list_files():
    """List files in workspace."""
    from DRIVER.sandbox_driver import list_directory, create_sandbox
    create_sandbox("demo_user")
    files = list_directory("demo_user")
    return {"files": files}

@app.get("/files/{filename}")
async def read_file(filename: str):
    """Read a file from workspace."""
    from DRIVER.sandbox_driver import read_from_sandbox
    content = read_from_sandbox("demo_user", filename)
    return {"filename": filename, "content": content}

@app.get("/health")
async def health():
    return {"status": "ok"}
