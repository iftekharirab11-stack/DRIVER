from __future__ import annotations

import asyncio
import json
import uuid
import logging
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
import os
import re
import time
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from DRIVER.core_brain import execute_task
from DRIVER.task_router import router
from DRIVER.ui_telemetry import get_sidebar_data
from session_manager import SessionStore

# ── Session Management ───────────────────────────────────────────────────────

sessions = SessionStore()

# ── Input Validation Models ───────────────────────────────────────────────────

class MessagePayload(BaseModel):
    session_id: str = Field(..., min_length=36, max_length=36)
    text: str = Field(..., min_length=1, max_length=1000)

    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v):
            raise ValueError('Invalid session ID format')
        return v

class JobStatusPayload(BaseModel):
    session_id: Optional[str] = Field(None, min_length=36, max_length=36)
    job_name: str = Field(..., min_length=1, max_length=100)

    @validator('session_id')
    def validate_session_id(cls, v):
        if v and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v):
            raise ValueError('Invalid session ID format')
        return v

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Alpha SaaS API", version="1.0")

# Get allowed origins from environment or use default
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3001,http://localhost:3000").split(",")

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "PRIMARY_MODEL"
]

# Check if at least one LLM key is available
llm_keys_available = any([
    os.getenv("OPENAI_API_KEY"),
    os.getenv("GOOGLE_API_KEY"),
    os.getenv("ANTHROPIC_API_KEY")
])

missing_env_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if not llm_keys_available:
    raise RuntimeError(
        "❌ CRITICAL: No LLM API keys configured. "
        "Please set at least one of: OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY in your .env file."
    )

if missing_env_vars:
    print(f"⚠️  Warning: Missing recommended environment variables: {', '.join(missing_env_vars)}")
    print("   Application will run but some features may be limited.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-Request-ID"],
)

# Add monitoring middleware
from DRIVER.monitoring_middleware import MonitoringMiddleware
app.add_middleware(MonitoringMiddleware)

# ── Error Handling ───────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request payload", "errors": exc.errors()},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# ── Dashboard builder (unchanged logic, returns plain dict) ──────────────────

def build_dashboard(user_id: str) -> dict:
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

API_PREFIX = "/api"

@app.get("/")
async def root():
    return {
        "service": "Alpha SaaS (no-chainlit)",
        "endpoints": {
            f"POST {API_PREFIX}/session": "Create a new chat session",
            f"POST {API_PREFIX}/message": "Send a message (JSON: {{session_id, text}})",
            f"GET {API_PREFIX}/stream/{{session_id}}": "SSE stream for live dashboard updates",
            f"GET {API_PREFIX}/dashboard": "Get current dashboard snapshot",
        },
    }

@app.post(f"{API_PREFIX}/session")
async def create_session(request: Request):
    """
    Create a new session with user authentication
    """
    # Get user ID from request - requires proper authentication
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required: X-User-ID header missing")

    try:
        # Create session with proper user isolation
        sid = sessions.create_for_user(user_id)

        # Auto-cleanup if needed
        sessions.auto_cleanup_if_needed()

        logger.info(f"Session created: {sid} for user: {user_id}")
        return {"session_id": sid, "user_id": user_id}
    except RuntimeError as e:
        logger.warning(f"Session creation failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))

@app.get(f"{API_PREFIX}/dashboard")
async def get_dashboard():
    # Get default user_id for dashboard
    return build_dashboard("default")

# ── Server-Sent Events stream (dashboard auto-refresh) ────────────────────────

async def dashboard_event_generator(session_id: str):
    """Yield dashboard snapshots every 30s as Server-Sent Events."""
    while True:
        try:
            await asyncio.sleep(30)
            user_id = sessions.get(session_id, "user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid session: user not found")
            dash = build_dashboard(user_id)
            yield f"data: {json.dumps(dash)}\n\n"
        except Exception as e:
            print(f"SSE error: {str(e)}")
            yield 'event: error\ndata: {"error":"dashboard unavailable"}\n\n'

@app.get(f"{API_PREFIX}/stream/{{session_id}}")
async def stream_dashboard(session_id: str):
    if not sessions.is_valid_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return StreamingResponse(
        dashboard_event_generator(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# ── Message handler ───────────────────────────────────────────────────────────

@app.post(f"{API_PREFIX}/message")
async def handle_message(payload: dict):
    """
    JSON body:
    {
      "session_id": "uuid",
      "text": "research cats"
    }
    """
    try:
        validated = MessagePayload(**payload)
        session_id = validated.session_id
        text = validated.text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

    if not sessions.is_valid_session(session_id):
        raise HTTPException(status_code=400, detail="Invalid or expired session_id")

    route_info = router.route(text)
    label = route_info.get("tool_hint", "🤖 AI Agent")

    user_id = sessions.get(session_id, "user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session: user not found")
    history = sessions.get(session_id, "history", [])

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: execute_task(text)
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

@app.get(f"{API_PREFIX}/tasks/{{task_id}}")
async def get_task(task_id: str):
    """Get status of a specific task."""
    try:
        from DRIVER.background_worker import bg_agent
        status = bg_agent.get_job_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post(f"{API_PREFIX}/jobs/status")
async def check_job_status(payload: dict):
    """Check status of a background job."""
    try:
        validated = JobStatusPayload(**payload)
        job_name = validated.job_name
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    try:
        from DRIVER.background_worker import bg_agent
        status = bg_agent.get_job_status(job_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post(f"{API_PREFIX}/integrations")
async def list_integrations():
    """List available integrations and their status."""
    try:
        from DRIVER.connection_monitor import monitor
        return monitor.check_all()
    except Exception as e:
        return []

@app.post(f"{API_PREFIX}/files/upload")
async def upload_file(request: Request, file: UploadFile = File(...), session_id: str = None):
    """Upload a file to user's workspace."""
    from DRIVER.sandbox_driver import write_to_sandbox, create_sandbox
    
    # Validate file size and type
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES = {
        'text/plain': ['.txt'],
        'text/markdown': ['.md'],
        'application/json': ['.json'],
        'text/csv': ['.csv'],
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    }

    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    content_type = file.content_type
    allowed_extensions = []

    for mime_type, extensions in ALLOWED_FILE_TYPES.items():
        if content_type == mime_type:
            allowed_extensions = extensions
            break

    if not allowed_extensions or file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(sum(ALLOWED_FILE_TYPES.values(), []))}"
        )

    # Get user_id from session or authentication header
    user_id = None
    if session_id:
        user_id = sessions.get(session_id, "user_id")
    
    if not user_id:
        user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    create_sandbox(user_id)

    try:
        content = await file.read()

        # For text files, try to decode as UTF-8
        if content_type.startswith('text/') or file_ext in ['.json', '.md', '.txt', '.csv']:
            try:
                text = content.decode('utf-8')
                result = write_to_sandbox(user_id, file.filename, text)
            except UnicodeDecodeError:
                # If UTF-8 decode fails, write as-is (binary mode)
                result = write_to_sandbox(user_id, file.filename, "")
        else:
            # For binary files, write empty placeholder (binary not fully supported)
            result = write_to_sandbox(user_id, file.filename, "")

        return {"filename": file.filename, "path": result, "status": "uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get(f"{API_PREFIX}/files")
async def list_files(request: Request, session_id: str = None):
    """List files in workspace."""
    from DRIVER.sandbox_driver import list_directory, create_sandbox
    
    # Get user_id from session or authentication header
    user_id = None
    if session_id:
        user_id = sessions.get(session_id, "user_id")

    if not user_id:
        user_id = request.headers.get("X-User-ID")

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    create_sandbox(user_id)
    files = list_directory(user_id)
    return {"files": files}

@app.get(f"{API_PREFIX}/files/{{filename}}")
async def read_file(filename: str, request: Request, session_id: str = None):
    """Read a file from workspace."""
    from DRIVER.sandbox_driver import read_from_sandbox, create_sandbox
    
    # Get user_id from session or authentication header
    user_id = None
    sid_header = request.headers.get("X-Session-ID")
    if sid_header:
        user_id = sessions.get(sid_header, "user_id")

    if not user_id:
        user_id = request.headers.get("X-User-ID")

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    create_sandbox(user_id)
    content = read_from_sandbox(user_id, filename)
    return {"filename": filename, "content": content}

@app.get(f"{API_PREFIX}/health")
async def health():
    return {"status": "ok"}

# ── Monitoring Endpoints ───────────────────────────────────────────────────────

@app.get(f"{API_PREFIX}/monitoring/metrics")
async def get_monitoring_metrics():
    """Get performance monitoring metrics"""
    from DRIVER.monitoring_middleware import get_performance_monitor
    monitor = get_performance_monitor()

    return {
        "service": "Alpha SaaS Monitoring",
        "metrics": monitor.get_metrics(),
        "timestamp": time.time()
    }

@app.get(f"{API_PREFIX}/monitoring/sessions")
async def get_active_sessions():
    """Get active session information"""
    active_sessions = []
    for sid, session in sessions.sessions.items():
        if sessions._is_session_valid(session):
            active_sessions.append({
                "session_id": sid,
                "user_id": session.get("user_id", "unknown"),
                "created_at": session.get("created_at"),
                "last_accessed": session.get("last_accessed"),
                "history_count": len(session.get("history", []))
            })

    return {
        "active_sessions": len(active_sessions),
        "sessions": active_sessions,
        "timestamp": time.time()
    }

@app.get(f"{API_PREFIX}/monitoring/ai")
async def get_ai_metrics():
    """Get AI orchestration metrics"""
    from DRIVER.ai_orchestrator import get_ai_orchestrator, get_ai_context_manager

    orchestrator = get_ai_orchestrator()
    context_manager = get_ai_context_manager()

    return {
        "service": "Alpha SaaS AI Monitoring",
        "orchestration_metrics": orchestrator.get_metrics(),
        "context_metrics": context_manager.get_context_summary(),
        "timestamp": time.time()
    }

@app.get(f"{API_PREFIX}/monitoring/ai/reset")
async def reset_ai_metrics():
    """Reset AI monitoring metrics"""
    from DRIVER.ai_orchestrator import get_ai_orchestrator

    orchestrator = get_ai_orchestrator()
    orchestrator.reset_metrics()

    return {
        "status": "success",
        "message": "AI metrics reset successfully",
        "timestamp": time.time()
    }
