import chainlit as cl
import uuid
from DRIVER.ui_telemetry import get_sidebar_data


# ─────────────────────────────────────────────
# TOP-LEVEL helper — callable from anywhere
# ─────────────────────────────────────────────
async def update_dashboard_element():
    """Build and return the sidebar dashboard element."""
    user_id = cl.user_session.get("user_id", "demo_user")
    data = get_sidebar_data(user_id)

    # 1. System Header
    content = f"## 📊 SYSTEM DASHBOARD\n\n**User:** `{user_id}`\n**Status:** 🟢 ACTIVE\n\n"

    # 2. Integrations Section
    content += "### 🔗 INTEGRATIONS\n"
    github_status = "✅ Connected" if "GitHub" in data.get("connections", []) else "❌ Disconnected"
    content += f"- **GitHub:** {github_status}\n"
    content += "- **Google Cal:** ✅ Connected\n\n"

    # 3. Background Workers Section
    content += "### ⚡ ACTIVE JOBS\n"
    if data.get("active_jobs"):
        for job in data["active_jobs"]:
            content += f"- {job['name']}: **{job['progress']}%**\n"
    else:
        content += "*No active background tasks.*\n"

    # Return the element — caller is responsible for attaching it to a message
    return cl.Text(name="Dashboard", content=content, display="side")


# ─────────────────────────────────────────────
# Chat start
# ─────────────────────────────────────────────
@cl.on_chat_start
async def start():
    cl.user_session.set("user_id", "demo_user")

    dashboard = await update_dashboard_element()   # ✅ call the top-level function

    await cl.Message(
        content="**SaaS Framework Active.** Click 'Dashboard' to view system status.",
        elements=[dashboard],
    ).send()


# ─────────────────────────────────────────────
# Per-message handler
# ─────────────────────────────────────────────
@cl.on_message
async def main(message: cl.Message):
    # … your core_brain.execute_task logic here …

    # Refresh the sidebar after processing
    dashboard = await update_dashboard_element()   # ✅ same top-level call

    await cl.Message(
        content="Task complete. Dashboard updated.",
        elements=[dashboard],
    ).send()
    