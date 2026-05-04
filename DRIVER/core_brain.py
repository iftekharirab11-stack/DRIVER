import os
from dotenv import load_dotenv
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

# Import tool registry
from DRIVER.tool_registry import registry, system_status, list_all_tools

# Import built-in tools (they auto-register on import)
from DRIVER.memory_system import remember, recall, search_memory, clear_memory
from DRIVER.calendar_tools import list_calendar_events, create_calendar_event, delete_calendar_event, get_calendar_event
from DRIVER.local_env_tools import list_directory, read_file, write_file, create_directory, delete_path, get_current_directory, search_files
from DRIVER.scheduler_driver import get_night_shift_plan, schedule_task_tool
from DRIVER.workspace_driver import write_to_workspace, read_from_workspace, list_workspace_files
from DRIVER.sandbox_driver import write_to_sandbox, read_from_sandbox, list_sandbox_contents
from DRIVER.executor_driver import execute_python_code, execute_shell_command, install_package, validate_workspace

# Background worker (no circular import - just the instance)
from DRIVER.background_worker import bg_agent

# Load environment
load_dotenv()

def get_all_tools():
    """Aggregate all tools from registry + built-ins."""
    # Get registry tools (auto-discovered from /skills)
    registry_tools = registry.get_tools_as_langchain()
    
    # Built-in tools
    built_in_tools = [
        remember, recall, search_memory, clear_memory,
        list_calendar_events, create_calendar_event, delete_calendar_event, get_calendar_event,
        list_directory, read_file, write_file, create_directory, delete_path, get_current_directory, search_files,
        get_night_shift_plan, schedule_task_tool,
        # Workspace (legacy - keep for compatibility)
        write_to_workspace, read_from_workspace, list_workspace_files,
        # Sandbox (per-user secure)
        write_to_sandbox, read_from_sandbox, list_sandbox_contents,
        # Execution
        execute_python_code, execute_shell_command, install_package, validate_workspace,
        # Background worker methods
        bg_agent.run_complex_job,
        bg_agent.get_job_status,
        bg_agent.read_job_result,
        # Registry tools
        system_status, list_all_tools
    ]
    
    # Convert built-ins to LangChain tools
    from langchain_core.tools import StructuredTool
    built_in_lc = [StructuredTool.from_function(f) for f in built_in_tools]
    
    # Combine (priority: built-in first, then registry)
    return built_in_lc + registry_tools

def get_llm():
    """Create LLM based on config."""
    from DRIVER.config_manager import get_provider_config
    config = get_provider_config()
    primary_model = config["primary_brain"]
    
    if primary_model.startswith("gpt") or "gpt" in primary_model.lower():
        return ChatOpenAI(model=primary_model, temperature=0)
    elif primary_model.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=primary_model, temperature=0)
    elif primary_model.startswith("claude") or "anthropic" in primary_model.lower():
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=primary_model, temperature=0)
    else:
        return ChatOpenAI(model="gpt-4o", temperature=0)

def create_simple_agent():
    """Create a standard agent (single task)."""
    from langchain.agents import create_agent
    
    llm = get_llm()
    tools = get_all_tools()
    
    system_prompt = """You are Alpha, an autonomous assistant.

Memory: remember() / recall() / search_memory()
Calendar: list_calendar_events() / create_calendar_event() / delete_calendar_event()
Files: list_directory() / read_file() / write_file() (safe paths)
Workspace: write_to_workspace() / read_from_workspace() (AI-generated content)
Sandbox: write_to_sandbox() / read_from_sandbox() / list_sandbox_contents() (per-user secure storage)
Execution: execute_python_code() — review code before running
Background: background_research() for long-running tasks
Batch: separate multiple tasks with ';'

SECURITY: 
- Sandbox is isolated per user. Never write outside it.
- Review Python code before execution.

IMPORTANT: Always explain your actions before calling tools."""
    
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)

def create_orchestrator():
    """Create the LangGraph orchestrator (complex loops)."""
    from DRIVER.orchestrator import orchestrate_task
    llm = get_llm()
    tools_dict = {t.name: t for t in get_all_tools()}
    return {"llm": llm, "tools": tools_dict, "orchestrate": orchestrate_task}

def execute_task(user_input: str, use_orchestrator: bool = False) -> str:
    """
    Execute user task (single).
    
    Args:
        user_input: The task/query
        use_orchestrator: If True, uses LangGraph loop
    
    Returns:
        Agent response
    """
    if use_orchestrator:
        config = create_orchestrator()
        import asyncio
        return asyncio.run(config["orchestrate"](user_input, config["llm"], config["tools"]))
    else:
        agent = create_simple_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                return msg.content
        return str(messages[-1].content if messages else "No response")

def execute_batch(tasks: list, parallel: bool = False) -> Dict[str, str]:
    """
    Execute multiple tasks at once.
    
    Args:
        tasks: List of task strings
        parallel: If True, run concurrently via task_queue
        
    Returns:
        Dict mapping task index -> result
    """
    if parallel and len(tasks) > 1:
        # Use task queue for parallel execution
        import asyncio
        
        async def run_parallel():
            # Submit all tasks
            task_ids = []
            for i, task in enumerate(tasks):
                tid = _submit_task(f"batch_{i}", execute_task, task)
                task_ids.append(tid)
            
            # Wait for all
            await _run_all_tasks()
            
            # Collect results
            results = {}
            for i, tid in enumerate(task_ids):
                results[str(i)] = task_queue.results.get(tid, "Unknown result")
            return results
        
        return asyncio.run(run_parallel())
    else:
        # Sequential execution
        results = {}
        for i, task in enumerate(tasks):
            results[str(i)] = execute_task(task)
        return results