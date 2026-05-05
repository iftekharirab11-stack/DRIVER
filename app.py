from __future__ import annotations

import asyncio
import os
import uuid

import chainlit as cl
from DRIVER.ui_telemetry import get_sidebar_data


# ── Dashboard builder ─────────────────────────────────────────────────────────

def _status_row(conn: dict) -> str:
    icon    = conn["icon"]
    name    = conn["name"]
    err     = (conn.get("error") or "")[:60]
    miss    = ", ".join(conn.get("missing_env", []))
    latency = f" `{conn['latency_ms']:.0f}ms`" if conn.get("latency_ms") else ""
    if conn["connected"]:
        return f"| {icon} **{name}** | ✅ Connected{latency} | — |\n"
    elif miss:
        return f"| {icon} **{name}** | 🔑 Missing key | `{miss}` |\n"
    else:
        return f"| {icon} **{name}** | ❌ {err} | |\n"


async def update_dashboard_element() -> cl.Text:
    user_id = cl.user_session.get("user_id", "demo_user")
    data    = get_sidebar_data(user_id)

    conns   = data.get("connections_detail", [])
    score   = data.get("health_score", 0)
    model   = data.get("primary_model", "?")
    missing = data.get("missing_env", [])
    actions = data.get("actions_required", [])
    system  = data.get("system", {})

    filled = round(score / 10)
    bar    = "█" * filled + "░" * (10 - filled)
    color  = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"

    lines = []

    # Header
    lines += [
        "## 🖥️ ALPHA DASHBOARD\n\n",
        f"**Model:** `{model}`  {color} Health `{score}/100`\n",
        f"`{bar}`\n\n",
        f"**Queue:** `{system.get('queue_depth', 0)}`  ",
        f"**BG Jobs:** `{system.get('background_jobs_active', 0)}`\n\n",
    ]

    # Connections grouped by category
    lines.append("### 🔌 CONNECTIONS\n\n")
    for cat in ["LLM", "Google", "Memory", "Execution", "MCP"]:
        group = [c for c in conns if c["category"] == cat]
        if not group:
            continue
        lines.append(f"**{cat}**\n\n")
        lines.append("| Service | Status | Note |\n")
        lines.append("|---------|--------|------|\n")
        for c in group:
            lines.append(_status_row(c))
        lines.append("\n")

    # Missing env vars
    if missing:
        lines.append("### 🔑 MISSING ENV VARS\n\n")
        for m in missing:
            lines.append(f"- `{m}`\n")
        lines.append("\n")

    # Actions required
    if actions:
        lines.append("### ⚡ ACTION REQUIRED\n\n")
        for a in actions:
            lines.append(f"- {a}\n")
        lines.append("\n")

    # Active jobs
    lines.append("### 🔄 ACTIVE JOBS\n\n")
    jobs = data.get("active_jobs", [])
    if jobs:
        for job in jobs:
            pct  = job.get("progress", 0)
            bar2 = "█" * round(pct / 10) + "░" * (10 - round(pct / 10))
            lines.append(f"- **{job['name']}** `{bar2}` {pct}%\n")
    else:
        lines.append("*No active background tasks.*\n")
    lines.append("\n")

    # Workspace files
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

    # Task router legend
    lines += [
        "### 🚦 TASK ROUTER\n\n",
        "| Say this…        | Routes to          |\n",
        "|------------------|--------------------|\n",
        "| `research [topic]` | Background worker |\n",
        "| `email [person]`   | Gmail via MCP     |\n",
        "| `calendar [event]` | Google Calendar   |\n",
        "| `remember [info]`  | Memory system     |\n",
        "| `run [script.py]`  | Python Executor   |\n",
        "| `search [query]`   | Tavily Search     |\n",
        "| `status`           | Dashboard refresh |\n",
    ]

    return cl.Text(name="Dashboard", content="".join(lines), display="side")


# ── Chat start ────────────────────────────────────────────────────────────────

@cl.on_chat_start
async def start():
    cl.user_session.set("user_id", "demo_user")
    cl.user_session.set("history", [])

    dashboard = await update_dashboard_element()

    await cl.Message(
        content=(
            "## 🤖 Alpha SaaS Active\n\n"
            "I'm your autonomous AI assistant.\n\n"
            "**Quick commands:**\n"
            "- `research [topic]` — background deep research\n"
            "- `email [person]` — Gmail\n"
            "- `calendar` — view / create events\n"
            "- `status` — refresh this dashboard\n\n"
            "Click **Dashboard** on any message to monitor connections."
        ),
        elements=[dashboard],
    ).send()

    # Refresh dashboard every 30 s
    async def _refresh_loop():
        while True:
            await asyncio.sleep(30)
            try:
                dash = await update_dashboard_element()
                await dash.send()
            except Exception:
                pass

    asyncio.create_task(_refresh_loop())


# ── Per-message handler ───────────────────────────────────────────────────────

@cl.on_message
async def main(message: cl.Message):
    from DRIVER.task_router import router
    from DRIVER.core_brain import execute_task

    route_info = router.route(message.content)
    label      = route_info.get("tool_hint", "🤖 AI Agent")

    thinking = cl.Message(content=f"⚡ **Routing to:** {label}…")
    await thinking.send()

    try:
        response = await cl.make_async(execute_task)(message.content)
    except Exception as e:
        response = (
            f"⚠️ **Error:** `{type(e).__name__}: {e}`\n\n"
            "Check Dashboard → **ACTION REQUIRED** for missing keys."
        )

    history = cl.user_session.get("history", [])
    history.append({"role": "user",      "content": message.content})
    history.append({"role": "assistant", "content": response})
    cl.user_session.set("history", history[-20:])

    dashboard = await update_dashboard_element()
    await thinking.remove()
    await cl.Message(content=response, elements=[dashboard]).send()