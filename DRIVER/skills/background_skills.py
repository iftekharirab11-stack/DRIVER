# Background research skill - runs complex tasks in background
from DRIVER.tool_registry import registry
from DRIVER.background_worker import bg_agent
import asyncio

@registry.register(name="background_research", description="Start a deep research task that runs in background while you do other work")
def background_research(topic: str, job_name: str = None) -> str:
    """Launch a complex research task that runs asynchronously.
    
    Args:
        topic: What to research
        job_name: Optional custom name for the job
    
    Returns:
        Job identifier and status
    """
    import uuid
    
    safe_name = job_name or f"Research_{topic[:30].replace(' ', '_')}"
    prompt = f"Conduct comprehensive research on: {topic}. Include latest info, key findings, and actionable insights."
    
    # Start background task (fire and forget)
    async def start_job():
        return await bg_agent.run_complex_job(safe_name, prompt)
    
    # Run in background
    import threading
    thread = threading.Thread(target=lambda: asyncio.run(start_job()), daemon=True)
    thread.start()
    
    return f"✓ Started background research: '{safe_name}'\nYou can continue chatting. Check status with: get_job_status('{safe_name}')"

@registry.register(name="get_job_status", description="Check status of a background job")
def get_job_status(job_name: str = None) -> str:
    """Get status of background tasks.
    
    Args:
        job_name: Optional specific job name; if None, shows all
    
    Returns:
        Status information
    """
    if job_name:
        status = bg_agent.get_job_status(job_name)
        output = f"Job: {job_name}\nStatus: {status['status']}\n"
        if status['output_file']:
            output += f"Output: {status['output_file']}"
        return output
    else:
        all_status = bg_agent.get_job_status()
        if not all_status['active']:
            return "No active background jobs."
        output = "=== BACKGROUND JOBS ===\n"
        for name, stat in all_status['active'].items():
            output += f"\n• {name}: {stat}\n"
        return output

@registry.register(name="read_job_result", description="Read output file from a completed background job")
def read_job_result(job_name: str) -> str:
    """Read the result of a finished background job.
    
    Args:
        job_name: Name of the job
    
    Returns:
        Job output content
    """
    return bg_agent.read_job_result(job_name)