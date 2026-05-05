from __future__ import annotations

# Ensure Discord bot does not auto-launch by clearing any Discord token
import os
os.environ["DISCORD_BOT_TOKEN"] = ""

import chainlit as cl
import uuid
import asyncio
import json
from DRIVER.ui_telemetry import get_sidebar_data
from DRIVER.cowork_console import cowork_console
from DRIVER.sandbox_driver import get_workspace_path, list_directory


# ─────────────────────────────────────────────
# Direct Action Handlers
# ─────────────────────────────────────────────

async def handle_triage_folder(user_id: str) -> str:
    """Triage folder: scans sandbox and suggests organization."""
    from DRIVER.task_manager import submit_file_sort_task, task_queue
    
    task_id = submit_file_sort_task(task_queue, user_id, "")
    await task_queue.process_queue()
    
    status = task_queue.get_status(task_id)
    return f"📂 Folder triage started: {task_id}\n{json.dumps(status, indent=2)}"


async def handle_extract_data(user_id: str) -> str:
    """Extract Data: bulk processes docs in sandbox into structured format."""
    from DRIVER.task_manager import submit_doc_summary_task, task_queue
    
    task_id = submit_doc_summary_task(task_queue, user_id, "")
    await task_queue.process_queue()
    
    # Read generated summary
    from DRIVER.sandbox_driver import read_from_sandbox
    summary = read_from_sandbox(user_id, "summary.txt")
    return f"📄 Document extraction complete:\n{summary}"


async def handle_teaching_mode(user_id: str, session_history: list) -> str:
    """Teaching Mode: records session parameters as reusable Skill."""
    import os
    skills_dir = os.path.join(os.path.dirname(__file__), "DRIVER", "skills")
    os.makedirs(skills_dir, exist_ok=True)
    
    timestamp = int(asyncio.get_event_loop().time())
    skill_name = f"skill_{timestamp}.py"
    skill_path = os.path.join(skills_dir, skill_name)
    
    # Create a template skill from session
    skill_content = f'''# Auto-generated skill from session
from DRIVER.tool_registry import registry

@registry.register(
    name="learned_skill_{timestamp}",
    description="Skill learned from user session - auto-generated"
)
def learned_skill(user_id: str, **kwargs):
    """Reusable skill based on session pattern."""
    # TODO: Implement based on session history
    return f"Executed learned skill for {{user_id}} with {{len(kwargs)}} parameters"
'''
    
    with open(skill_path, 'w') as f:
        f.write(skill_content)
    
    return f"📚 Teaching Mode: Skill saved as {skill_name}"


async def build_file_explorer(user_id: str) -> str:
    """Build a file tree view of the sandbox workspace.
    
    Returns:
        Formatted file tree string
    """
    workspace = get_workspace_path(user_id)
    
    try:
        items = list_directory(user_id, "")
        if not items:
            return "📁 Workspace is empty"
        
        output = "📁 Workspace File Tree:\n\n"
        for item in items:
            if isinstance(item, dict):
                icon = "📁" if item.get("is_dir") else "📄"
                size = item.get("size", 0)
                size_str = f" ({size} bytes)" if size > 0 and not item.get("is_dir") else ""
                output += f"{icon} **{item['name']}**{size_str}\n"
        
        return output
    except Exception as e:
        return f"Error building file explorer: {str(e)}"


async def update_dashboard_element():
    """Build and return the sidebar dashboard Text element."""
    user_id = cl.user_session.get("user_id", "demo_user")
    data = get_sidebar_data(user_id)
    
    content = f"## 📊 SYSTEM DASHBOARD\n\n**User:** `{user_id}`\n**Status:** 🟢 ACTIVE\n\n"
    
    # Integrations
    content += "### 🔗 INTEGRATIONS\n"
    connections = data.get("connections", [])
    github_status = "✅ Connected" if "GitHub" in connections else "❌ Disconnected"
    gcal_status   = "✅ Connected" if "Google Cal" in connections else "❌ Disconnected"
    content += f"- **GitHub:** {github_status}\n"
    content += f"- **Google Cal:** {gcal_status}\n\n"
    
    # Active jobs
    content += "### ⚡ ACTIVE JOBS\n"
    active_jobs = data.get("active_jobs", [])
    if active_jobs:
        for job in active_jobs:
            content += f"- {job['name']}: **{job.get('progress', 0)}%**\n"
    else:
        content += "*No active background tasks.*\n"
    
    # System stats
    system = data.get("system", {})
    if system:
        content += f"\n### 📈 SYSTEM\n"
        content += f"- Queue depth: `{system.get('queue_depth', 0)}`\n"
        content += f"- BG jobs running: `{system.get('background_jobs_active', 0)}`\n"
    
    return content


async def update_cowork_sidebar(user_id: str):
    """Update the Alpha Cowork sidebar with live operations."""
    content = cowork_console.generate_sidebar_content(user_id)
    return cl.Text(name="Cowork", content=content, display="side")


# ─────────────────────────────────────────────
# Direct Action Buttons
# ─────────────────────────────────────────────

@cl.action_callback("triage_folder")
async def on_triage_folder():
    user_id = cl.user_session.get("user_id", "demo_user")
    result = await handle_triage_folder(user_id)
    await cl.Message(content=result).send()


@cl.action_callback("extract_data")
async def on_extract_data():
    user_id = cl.user_session.get("user_id", "demo_user")
    result = await handle_extract_data(user_id)
    await cl.Message(content=result).send()


@cl.action_callback("teaching_mode")
async def on_teaching_mode():
    user_id = cl.user_session.get("user_id", "demo_user")
    history = cl.user_session.get("history", [])
    result = await handle_teaching_mode(user_id, history)
    await cl.Message(content=result).send()


# ─────────────────────────────────────────────
# Chat start
# ─────────────────────────────────────────────
@cl.on_chat_start
async def start():
    session_id = str(uuid.uuid4())
    cl.user_session.set("user_id", "demo_user")
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("history", [])
    
    # Create default sandbox for demo user
    from DRIVER.sandbox_driver import create_sandbox
    create_sandbox("demo_user")
    
    dashboard = await update_dashboard_element()
    cowork = await update_cowork_sidebar("demo_user")
    
    # Direct Action menu buttons - use payload instead of value for newer chainlit
    actions = [
        cl.Action(name="triage_folder", label="Triage Folder", payload={"action": "triage"}),
        cl.Action(name="extract_data", label="Extract Data", payload={"action": "extract"}),
        cl.Action(name="teaching_mode", label="Teaching Mode", payload={"action": "teach"}),
    ]
    
    await cl.Message(
        content=(
            "## Alpha SaaS Framework Active\n\n"
            "I'm your autonomous AI assistant. I can:\n"
            "- Research topics in the background\n"
            "- Manage your calendar\n"
            "- Write & execute code\n"
            "- Remember information across sessions\n"
            "- Organize files in sandbox (Alpha Cowork)\n\n"
            "Click Dashboard (top-right) to monitor system status.\n"
            "Use the action buttons below for quick tasks.\n\n"
            "What would you like me to do?"
        ),
        elements=[dashboard, cowork],
        actions=actions,
    ).send()


# ─────────────────────────────────────────────
# Per-message handler
# ─────────────────────────────────────────────
@cl.on_message
async def main(message: cl.Message):
    cl.user_session.get("user_id", "demo_user")
    history = cl.user_session.get("history", [])
    
    # Show a thinking indicator while the agent works
    thinking_msg = cl.Message(content="⏳ Processing…")
    await thinking_msg.send()
    
    try:
        # Lazy import keeps startup fast and avoids circular issues at module load
        from DRIVER.core_brain import execute_task
        
        response = await cl.make_async(execute_task)(
            message.content,
            use_orchestrator=False,
        )
    except Exception as e:
        response = (
            f"⚠️ **Agent error:** `{type(e).__name__}: {e}`\n\n"
            "Make sure your API keys are set correctly in `.env`.\n"
            "Required: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`."
        )
    
    # Persist turn to session history (rolling 10-turn window)
    history.append({"role": "user",      "content": message.content})
    history.append({"role": "assistant", "content": response})
    cl.user_session.set("history", history[-20:])
    
    # Refresh dashboard and cowork sidebar and send final reply
    dashboard = await update_dashboard_element()
    cowork = await update_cowork_sidebar(cl.user_session.get("user_id", "demo_user"))
    await thinking_msg.remove()
    await cl.Message(content=response, elements=[dashboard, cowork]).send()