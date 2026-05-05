# DRIVER/core_brain.py
# [GOAL] Central brain — wires LLM + tools + agent loop together.
# [ALPHA COWORK] Added cowork file tools and task queue integration

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ── Lazy imports inside functions to prevent circular-import problems ──────────

def get_all_tools() -> List:
    """Aggregate tools from the skill registry and all built-in modules."""
    from DRIVER.tool_registry import registry, system_status, list_all_tools
    from DRIVER.memory_system import remember, recall, search_memory, clear_memory
    from DRIVER.local_env_tools import (
        list_directory, read_file, write_file,
        create_directory, delete_path, get_current_directory, search_files,
    )
    from DRIVER.scheduler_driver import get_night_shift_plan, schedule_task_tool
    from DRIVER.workspace_driver import (
        write_to_workspace, read_from_workspace, list_workspace_files,
    )
    from DRIVER.executor_driver import (
        execute_python_code, execute_shell_command,
        install_package, validate_workspace,
        # Alpha Cowork cowork file tools
        cowork_read_file,
        cowork_write_file,
        cowork_list_directory,
        cowork_move_file,
        cowork_create_archive,
        cowork_count_files,
    )
    from DRIVER.background_worker import bg_agent, BackgroundAgent

    built_in_funcs = [
        # Memory tools
        remember, recall, search_memory, clear_memory,
        # Local env tools
        list_directory, read_file, write_file,
        create_directory, delete_path, get_current_directory, search_files,
        # Scheduler tools
        get_night_shift_plan, schedule_task_tool,
        # Workspace tools
        write_to_workspace, read_from_workspace, list_workspace_files,
        # Executor tools (standard + Alpha Cowork)
        execute_python_code, execute_shell_command,
        install_package, validate_workspace,
        cowork_read_file,
        cowork_write_file,
        cowork_list_directory,
        cowork_move_file,
        cowork_create_archive,
        cowork_count_files,
        # Background worker
        bg_agent.get_job_status,
        bg_agent.read_job_result,
        # Registry tools
        system_status, list_all_tools,
    ]

    # Calendar tools — graceful fallback if google-auth is unavailable
    try:
        from DRIVER.calendar_tools import (
            list_calendar_events, create_calendar_event,
            delete_calendar_event, get_calendar_event,
        )
        built_in_funcs += [
            list_calendar_events, create_calendar_event,
            delete_calendar_event, get_calendar_event,
        ]
    except Exception:
        pass  # Google Calendar credentials not configured

    # Background-worker async methods (wrapped)
    built_in_funcs += [
        bg_agent.get_job_status,
        bg_agent.read_job_result,
    ]

    # Convert plain functions to LangChain StructuredTools
    lc_tools = []
    for func in built_in_funcs:
        try:
            lc_tools.append(StructuredTool.from_function(func))
        except Exception as e:
            pass  # Skip tools that can't be wrapped

    # Merge in registry-discovered tools
    try:
        registry_tools = registry.get_tools_as_langchain()
        lc_tools += registry_tools
    except Exception:
        pass

    return lc_tools


def get_llm():
    """Instantiate the configured LLM."""
    from DRIVER.config_manager import get_provider_config
    cfg = get_provider_config()
    model = cfg.get("primary_brain", "gpt-4o")

    if "gpt" in model.lower() or model.startswith("o"):
        api_key = cfg.get("openai_key") or os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(model=model, temperature=0, api_key=api_key)

    if "gemini" in model.lower():
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = cfg.get("gemini_key") or os.getenv("GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(model=model, temperature=0, google_api_key=api_key)

    if "claude" in model.lower() or "anthropic" in model.lower():
        from langchain_anthropic import ChatAnthropic
        api_key = cfg.get("anthropic_key") or os.getenv("ANTHROPIC_API_KEY")
        return ChatAnthropic(model=model, temperature=0, anthropic_api_key=api_key)

    # Default fallback
    return ChatOpenAI(model="gpt-4o", temperature=0)


_SYSTEM_PROMPT = """You are Alpha, an autonomous AI assistant inside a SaaS framework.

Available capability categories:
  Memory    → remember() / recall() / search_memory()
  Calendar  → list_calendar_events() / create_calendar_event() / delete_calendar_event()
  Files     → cowork_read_file() / cowork_write_file() / cowork_list_directory() / cowork_move_file() / cowork_create_archive()
  Workspace → write_to_workspace() / read_from_workspace() / list_workspace_files()
  Sandbox   → write_to_sandbox() / read_from_sandbox()
  Execution → execute_python_code() / execute_shell_command()
  Research  → background_research() (runs async, returns immediately)
  Status    → get_job_status() / read_job_result()

ALPHA COWORK RULES:
  1. ALWAYS create a task_plan.json before any file operation using create_task_plan()
  2. Review the plan: risk_level, operations, requires_hitl flag
  3. Sandbox is isolated per user — NEVER write outside Allowed Zone (workspace)
  4. If a task is long-running, launch it via background_research() or task queue
  5. If deleting/moving >10 items, require HITL confirmation
  6. Verify execution results against the plan
  7. Explain what you are doing before calling a tool.
"""


def _build_agent():
    """Build a new ReAct agent with all tools attached."""
    llm   = get_llm()
    tools = get_all_tools()
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=_SYSTEM_PROMPT),
    )
    return agent


def _extract_response(result: dict) -> str:
    """Pull the final AI text reply out of a LangGraph agent result dict."""
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            return msg.content
    return str(messages[-1].content) if messages else "No response generated."


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def execute_task(user_input: str, use_orchestrator: bool = False) -> str:
    """
    Run a single-turn task through the agent.

    Args:
        user_input     : The user's message / task.
        use_orchestrator: If True, use the LangGraph loop (slower, for complex tasks).

    Returns:
        Agent's text response.
    """
    if use_orchestrator:
        import asyncio
        from DRIVER.orchestrator import orchestrate_task
        tools_dict = {t.name: t for t in get_all_tools()}
        return asyncio.run(orchestrate_task(user_input, get_llm(), tools_dict))

    agent  = _build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    return _extract_response(result)


def execute_batch(tasks: List[str], parallel: bool = False) -> Dict[str, str]:
    """
    Execute multiple tasks.

    Args:
        tasks    : List of task strings.
        parallel : If True, run tasks concurrently (best-effort).

    Returns:
        Dict mapping index → result string.
    """
    if parallel and len(tasks) > 1:
        import asyncio
        from DRIVER.task_manager import submit_task, run_all_tasks, task_queue

        for i, task in enumerate(tasks):
            submit_task(f"batch_{i}", execute_task, task)

        asyncio.run(run_all_tasks())
        return {str(i): task_queue.results.get(f"batch_{i}", "pending")
                for i in range(len(tasks))}

    return {str(i): execute_task(task) for i, task in enumerate(tasks)}