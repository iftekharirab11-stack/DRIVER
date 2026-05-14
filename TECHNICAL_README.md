# Alpha SaaS - Technical Documentation

## 🏗️ Architecture Overview

Alpha SaaS is a production-ready AI platform built with a modular architecture supporting multiple LLM providers, secure file operations, and asynchronous task processing.

### Core Components

```
DRIVER/
├── main.py                    # FastAPI entry point, routes, middleware
├── session_manager.py         # Session lifecycle management
├── DRIVER/
│   ├── core_brain.py         # Central AI orchestration (LLM + tools)
│   ├── orchestrator.py       # LangGraph multi-step reasoning
│   ├── agent_core.py         # Plan-Execute-Verify cycles
│   ├── executor_driver.py    # Shell/Python code execution
│   ├── sandbox_driver.py     # User-isolated workspace
│   ├── workspace_driver.py   # Legacy file operations
│   ├── tool_registry.py    # Skill/tool discovery
│   ├── memory_system.py      # Persistent memory store
│   ├── background_worker.py  # Async task processing
│   ├── task_manager.py       # Task queue management
│   ├── task_router.py        # Natural language routing
│   ├── connection_monitor.py # Health checks
│   ├── monitoring_middleware.py # Request tracing
│   ├── telemetry_logger.py   # Action logging
│   ├── ui_telemetry.py       # Sidebar data aggregation
│   ├── ai_orchestrator.py    # Provider failover
│   └── skills/               # Custom tool modules
project/frontend/            # React frontend
```

---

## 🔧 Module Details

### Core Brain (`DRIVER/core_brain.py`)
- **Purpose**: Central orchestration layer wiring LLM + tools
- **Key Functions**:
  - `get_all_tools()` - Aggregates tools from registry and modules
  - `get_llm()` - Instantiates configured LLM (OpenAI/Gemini/Anthropic)
  - `execute_task()` - Single-turn agent execution
  - `execute_batch()` - Parallel task execution
- **Expected Outcome**: Returns structured AI responses with tool usage

### Orchestrator (`DRIVER/orchestrator.py`)
- **Purpose**: LangGraph-based multi-step reasoning agent
- **Key Features**: Up to 8 iterations, automatic tool call detection
- **Expected Outcome**: Complex task completion with reasoning trace

### Agent Core (`DRIVER/agent_core.py`)
- **Purpose**: Plan-Execute-Verify cycle for safe file operations
- **Key Functions**:
  - `create_task_plan()` - Generates JSON plan before file ops
  - `requires_hitl_approval()` - Checks for human confirmation
  - `run_agent_with_plan()` - Executes with safety validation
- **Expected Outcome**: Controlled file operations with audit trail

### Executor Driver (`DRIVER/executor_driver.py`)
- **Purpose**: Secure code execution with sandboxing
- **Security**: Command allowlist, no `shell=True`, path validation
- **Cowork Tools**: `cowork_read_file`, `cowork_write_file`, `cowork_list_directory`, `cowork_move_file`, `cowork_create_archive`, `cowork_count_files`
- **Expected Outcome**: Safe execution within user's Allowed Zone

### Sandbox Driver (`DRIVER/sandbox_driver.py`)
- **Purpose**: Per-user isolated workspace
- **Structure**: `storage/sandboxes/{user_id}/WORKSPACE/`
- **Key Functions**: `write_to_sandbox`, `read_from_sandbox`, `list_directory`
- **Expected Outcome**: Complete isolation between users

### Task Manager (`DRIVER/task_manager.py`)
- **Purpose**: Parallel task queue with tracking
- **Classes**: `TaskQueue`, `BackgroundWorker`, `QueuedTask`
- **Expected Outcome**: Concurrent execution of long-running tasks

### Memory System (`DRIVER/memory_system.py`)
- **Purpose**: Persistent key-value storage
- **Functions**: `remember()`, `recall()`, `search_memory()`, `clear_memory()`
- **Expected Outcome**: Context retention across sessions

---

## 🔌 API Endpoints

### Session Management
```
POST /api/session
  Headers: X-User-ID
  Returns: {session_id, user_id}

GET /api/dashboard
  Returns: Health score, connections, active jobs, workspace files
```

### Messaging
```
POST /api/message
  Body: {session_id, text}
  Returns: {response, label, dashboard, history, job_status}
```

### File Operations
```
POST /api/files/upload
  Headers: X-User-ID or X-Session-ID
  Body: multipart file
  Returns: {filename, path, status}

GET /api/files
  Headers: X-User-ID or X-Session-ID
  Returns: {files: [{name, size, is_dir}]}

GET /api/files/{filename}
  Headers: X-User-ID or X-Session-ID
  Returns: {filename, content}
```

---

## 🛡️ Security Model

### Sandbox Isolation
- Each user gets `storage/sandboxes/{user_id}/WORKSPACE/`
- Path traversal blocked via `_enforce_allowed_zone()`
- File operations restricted to Allowed Zone only

### Shell Command Security
```python
ALLOWED_COMMANDS = [
    r'^ls\s', r'^python\s', r'^pip\s', r'^git\s', ...
]
DANGEROUS_PATTERNS = [
    r'rm\s+-rf', r'sudo\s', r';\s*', r'\|\|', ...
]
```

### HITL (Human-in-the-Loop)
- Risk level: Low/Medium/High based on operations
- Auto-approval thresholds configurable via env vars
- Required for >10 file deletions/moves

---

## 🚀 Expected Outcomes

### Normal Operation
1. User sends message → routed via `task_router.py`
2. Agent executes with tools from `core_brain.py`
3. File operations trigger Plan-Execute-Verify cycle
4. Results logged to telemetry, returned to user

### Success Responses
```json
{
  "session_id": "uuid",
  "label": "🤖 AI Agent",
  "response": "Task completed successfully",
  "dashboard": { "health_score": 90, ... },
  "history": [...],
  "job_status": {...}
}
```

### Error Responses
```json
{
  "detail": "Invalid request payload"
}
```

---

## 📊 Monitoring

### Health Check
```
GET /api/health
Response: {"status": "ok"}
```

### Performance Metrics
```
GET /api/monitoring/metrics
Returns: requests_per_second, success_rate, avg_response_time
```

### Active Sessions
```
GET /api/monitoring/sessions
Returns: active_sessions, sessions[]
```

---

## ⚙️ Environment Configuration

```bash
# Required (at least one LLM provider)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
PRIMARY_MODEL=gpt-4o

# Optional
TAVILY_API_KEY=...
CHATNOT_API_KEY=...
VITE_API_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000
SANDBOX_ROOT=WORKSPACE
MAX_FILES_PER_OPERATION=100
HITL_THRESHOLD_DELETE=10
```

---

## 🧪 Testing Commands

```bash
# Syntax check
python -m py_compile DRIVER/*.py main.py

# Run server
uvicorn main:app --reload --port 8000

# Test API
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/session -H "X-User-ID: test"
curl -X POST http://localhost:8000/api/message -H "Content-Type: application/json" -d '{"session_id":"...","text":"Hello"}'
```

---

## 🐛 Known Limitations

1. File upload limited to text files (binary not fully supported)
2. Rate limiting configured but not enforced
3. Session store in-memory (Redis recommended for production)
4. No OAuth2/JWT authentication (session-based only)