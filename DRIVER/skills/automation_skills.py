# Example skill: Automation & Scripting
from DRIVER.tool_registry import registry

@registry.register(name="run_script", description="Execute a local script or command (caution)")
def run_script(script_path: str) -> str:
    """Run a Python script in workspace."""
    return f"Would execute: {script_path} (sandboxed)"

@registry.register(name="schedule_job", description="Schedule a recurring task")
def schedule_job(task_name: str, cron_expr: str) -> str:
    """Schedule automated task."""
    return f"Scheduled '{task_name}' with cron: {cron_expr}"