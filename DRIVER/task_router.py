import re
import os


ROUTES = [
    (r"^(research|deep dive|find out|look into|investigate)\s+(.+)",  "background_research", "🔍 Background Research"),
    (r"^(email|send mail|gmail|send email|write email)\s*(.+)?",      "gmail",               "📧 Gmail"),
    (r"^(calendar|schedule|meeting|event|remind)\s*(.+)?",            "calendar",            "📅 Google Calendar"),
    (r"^(remember|save|store|note)\s+(.+)",                           "memory",              "🧠 Memory System"),
    (r"^(run|execute|python|script)\s+(.+)",                          "executor",            "⚙️ Python Executor"),
    (r"^(status|dashboard|health|connections|check)\s*$",             "dashboard",           "📊 Dashboard Refresh"),
    (r"^(file|read|write|open|workspace)\s+(.+)",                     "workspace",           "📁 Workspace"),
    (r"^(drive|doc|sheet|slide|docs|sheets)\s*(.+)?",                 "google_mcp",          "🗂️ Google Workspace"),
    (r"^(search|look up|find|web)\s+(.+)",                            "search",              "🌐 Web Search"),
]


class TaskRouter:

    def route(self, user_input: str) -> dict:
        text = user_input.strip().lower()

        for pattern, route, label in ROUTES:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                groups = m.groups()
                arg = groups[-1] if groups else user_input
                return {
                    "route":         route,
                    "extracted_arg": arg.strip() if arg else user_input,
                    "tool_hint":     label,
                }

        # Check if Tavily available for search-like queries
        if os.getenv("TAVILY_API_KEY") and any(
            w in text for w in ["what is", "who is", "how to", "latest", "news"]
        ):
            return {
                "route":         "search",
                "extracted_arg": user_input,
                "tool_hint":     "🌐 Web Search",
            }

        return {
            "route":         "agent",
            "extracted_arg": user_input,
            "tool_hint":     "🤖 AI Agent",
        }


# Singleton
router = TaskRouter()