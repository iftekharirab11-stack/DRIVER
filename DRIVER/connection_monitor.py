import os
import subprocess
from typing import TypedDict

class ConnectionStatus(TypedDict):
    name       : str
    category   : str
    connected  : bool
    error      : str | None
    missing_env: list
    latency_ms : float | None
    icon       : str


class ConnectionMonitor:

    # ── helpers ──────────────────────────────────────────────

    def _env(self, *keys) -> tuple[bool, list]:
        missing = [k for k in keys if not os.getenv(k)]
        return (len(missing) == 0), missing

    def _ok(self, name, cat, latency=None) -> ConnectionStatus:
        return ConnectionStatus(name=name, category=cat, connected=True,
                                error=None, missing_env=[], latency_ms=latency, icon="✅")

    def _fail(self, name, cat, error, missing=None, icon="🔴") -> ConnectionStatus:
        return ConnectionStatus(name=name, category=cat, connected=False,
                                error=error, missing_env=missing or [], latency_ms=None, icon=icon)

    # ── LLM providers ────────────────────────────────────────

    def _check_openai(self):
        ok, miss = self._env("OPENAI_API_KEY")
        if not ok:
            return self._fail("OpenAI", "LLM", "API key missing", miss, "🔑")
        try:
            import time, openai
            t = time.time()
            openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")).models.list()
            return self._ok("OpenAI", "LLM", round((time.time()-t)*1000))
        except ImportError:
            return self._fail("OpenAI", "LLM", "pip install openai", icon="📦")
        except Exception as e:
            return self._fail("OpenAI", "LLM", str(e)[:80])

    def _check_anthropic(self):
        ok, miss = self._env("ANTHROPIC_API_KEY")
        if not ok:
            return self._fail("Anthropic", "LLM", "API key missing", miss, "🔑")
        try:
            import anthropic
            anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")).models.list()
            return self._ok("Anthropic", "LLM")
        except ImportError:
            return self._fail("Anthropic", "LLM", "pip install anthropic", icon="📦")
        except Exception as e:
            return self._fail("Anthropic", "LLM", str(e)[:80])

    def _check_gemini(self):
        ok, miss = self._env("GOOGLE_API_KEY")
        if not ok:
            return self._fail("Google Gemini", "LLM", "API key missing", miss, "🔑")
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            return self._ok("Google Gemini", "LLM")
        except ImportError:
            return self._fail("Google Gemini", "LLM", "pip install google-generativeai", icon="📦")
        except Exception as e:
            return self._fail("Google Gemini", "LLM", str(e)[:80])

    def _check_ollama(self):
        try:
            import time, requests
            t = time.time()
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                return self._ok("Ollama (local)", "LLM", round((time.time()-t)*1000))
            return self._fail("Ollama (local)", "LLM", f"HTTP {r.status_code}")
        except Exception:
            return self._fail("Ollama (local)", "LLM", "Server not running", icon="⚠️")

    # ── Google Workspace ─────────────────────────────────────

    def _check_google_service(self, name):
        if not os.path.exists("credentials.json"):
            return self._fail(name, "Google", "credentials.json missing — download from GCloud", icon="🔐")
        if not os.path.exists("token.json"):
            return self._fail(name, "Google", "Not authenticated — run auth flow once", icon="🔐")
        return self._ok(name, "Google")

    # ── Memory / Storage ─────────────────────────────────────

    def _check_memory(self):
        try:
            path = "memory_store.json"
            if os.path.exists(path):
                open(path).read()
            return self._ok("Local Memory", "Memory")
        except Exception as e:
            return self._fail("Local Memory", "Memory", str(e)[:80])

    def _check_telemetry_db(self):
        try:
            os.makedirs("storage", exist_ok=True)
            test = "storage/.write_test"
            open(test, "w").close()
            os.remove(test)
            return self._ok("SQLite Telemetry", "Memory")
        except Exception as e:
            return self._fail("SQLite Telemetry", "Memory", str(e)[:80])

    # ── Execution ─────────────────────────────────────────────

    def _check_workspace(self):
        try:
            os.makedirs("WORKSPACE", exist_ok=True)
            test = "WORKSPACE/.write_test"
            open(test, "w").close()
            os.remove(test)
            return self._ok("Python Executor", "Execution")
        except Exception as e:
            return self._fail("Python Executor", "Execution", str(e)[:80])

    def _check_sandbox(self):
        try:
            os.makedirs("storage/sandboxes", exist_ok=True)
            return self._ok("Sandbox", "Execution")
        except Exception as e:
            return self._fail("Sandbox", "Execution", str(e)[:80])

    # ── MCP servers ───────────────────────────────────────────

    def _check_mcp_google_workspace(self):
        try:
            r = subprocess.run(
                ["uvx", "google-workspace-mcp", "--version"],
                capture_output=True, timeout=3
            )
            if r.returncode == 0:
                return self._ok("Google Workspace MCP", "MCP")
            return self._fail("Google Workspace MCP", "MCP",
                              "uvx google-workspace-mcp not found — pip install google-workspace-mcp", icon="📦")
        except FileNotFoundError:
            return self._fail("Google Workspace MCP", "MCP", "uvx not found — install uv", icon="📦")
        except Exception as e:
            return self._fail("Google Workspace MCP", "MCP", str(e)[:80])

    def _check_tavily(self):
        ok, miss = self._env("TAVILY_API_KEY")
        if not ok:
            return self._fail("Tavily Search", "MCP", "API key missing", miss, "🔑")
        try:
            from tavily import TavilyClient
            return self._ok("Tavily Search", "MCP")
        except ImportError:
            return self._fail("Tavily Search", "MCP", "pip install tavily-python", icon="📦")

    # ── Public API ────────────────────────────────────────────

    def check_all(self) -> list:
        return [
            self._check_openai(),
            self._check_anthropic(),
            self._check_gemini(),
            self._check_ollama(),
            self._check_google_service("Gmail"),
            self._check_google_service("Google Calendar"),
            self._check_google_service("Google Drive"),
            self._check_google_service("Google Docs"),
            self._check_google_service("Google Sheets"),
            self._check_memory(),
            self._check_telemetry_db(),
            self._check_workspace(),
            self._check_sandbox(),
            self._check_mcp_google_workspace(),
            self._check_tavily(),
        ]

    def get_missing_env_vars(self) -> list:
        keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "TAVILY_API_KEY", "PRIMARY_MODEL", "CHAINLIT_AUTH_SECRET",
        ]
        missing = [k for k in keys if not os.getenv(k)]
        warn = []
        if os.getenv("DISCORD_BOT_TOKEN"):
            warn.append("⚠️  DISCORD_BOT_TOKEN is set — remove it to stop Discord auto-open")
        return missing + warn

    def get_action_required(self) -> list:
        actions = []
        if not os.path.exists("credentials.json"):
            actions.append("Download credentials.json from Google Cloud Console → APIs & Services → Credentials")
        if os.path.exists("credentials.json") and not os.path.exists("token.json"):
            actions.append("Run auth flow: python -c \"from DRIVER.calendar_tools import get_calendar_service; get_calendar_service()\"")
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            actions.append("Set at least ONE LLM key in .env (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)")
        return actions

    def get_health_score(self) -> int:
        results = self.check_all()
        if not results:
            return 0
        connected = sum(1 for r in results if r["connected"])
        return round((connected / len(results)) * 100)


# Singleton
monitor = ConnectionMonitor()