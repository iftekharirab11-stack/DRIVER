# [GOAL] Parallel Execution (CrewAI style)
# [CONTEXT] Perform research while the user does something else.

import asyncio
from typing import Dict, Any
from DRIVER.workspace_driver import write_to_workspace
from DRIVER.agent_core import run_simple_agent

class BackgroundAgent:
    """Runs long-running tasks in background without blocking the main conversation."""
    
    def __init__(self):
        self.active_tasks: Dict[str, str] = {}
        self.results: Dict[str, Any] = {}
        
    async def run_complex_job(self, job_name: str, prompt: str, tools=None) -> str:
        """Executes a long-running task and writes the result to a file.
        
        Args:
            job_name: Descriptive name for the job
            prompt: The task to execute
            tools: Optional tool list (uses default if None)
        
        Returns:
            Job identifier and status
        """
        from DRIVER.config_manager import get_provider_config
        from DRIVER.core_brain import get_llm, get_all_tools
        
        safe_name = "".join(c for c in job_name if c.isalnum() or c in "_- ").replace(" ", "_")
        filename = f"{safe_name}.md"
        
        self.active_tasks[job_name] = "Running"
        
        try:
            # Get LLM and tools if not provided
            if tools is None:
                tools = get_all_tools()
            
            llm = get_llm()
            
            # Execute the complex task
            result = await asyncio.to_thread(run_simple_agent, llm, tools, 
                "You are running a deep research task. Be thorough.", prompt)
            
            # Save result to workspace
            write_to_workspace(filename, result, overwrite=True)
            
            self.results[job_name] = filename
            self.active_tasks[job_name] = f"✓ Completed → {filename}"
            
            return result
        except Exception as e:
            self.active_tasks[job_name] = f"✗ Failed: {str(e)}"
            return f"Error: {str(e)}"
    
    def get_job_status(self, job_name: str = None) -> Dict[str, Any]:
        """Check status of background jobs."""
        if job_name:
            return {
                "job": job_name,
                "status": self.active_tasks.get(job_name, "Not found"),
                "output_file": self.results.get(job_name)
            }
        return {
            "active": self.active_tasks,
            "completed_files": list(self.results.values())
        }
    
    def read_job_result(self, job_name: str) -> str:
        """Read the output file of a completed job."""
        if job_name not in self.results:
            return f"Job '{job_name}' not found or not completed."
        
        from DRIVER.workspace_driver import read_from_workspace
        filename = self.results[job_name]
        return read_from_workspace(filename)

# Global background agent
bg_agent = BackgroundAgent()