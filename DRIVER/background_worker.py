# DRIVER/background_worker.py
# [GOAL] Parallel execution — long tasks run in background without blocking chat.
# [ALPHA COWORK] Enhanced with file operation support and task queue integration

import asyncio
import threading
import time
from typing import Dict, Any, List, Optional
import uuid

from DRIVER.task_manager import task_queue, BackgroundWorker
from DRIVER.sandbox_driver import (
    get_workspace_path, write_to_sandbox, read_from_sandbox,
    list_directory
)
from DRIVER.agent_core import run_agent_with_plan, create_task_plan


class BackgroundAgent:
    """Runs long-running tasks asynchronously; results are written to WORKSPACE.
    
    Alpha Cowork enhancements:
    - Supports parallel file sorting and document summarization
    - Integrated with TaskQueue for concurrent execution
    - Creates task_plan.json before file operations
    """
    
    def __init__(self):
        self.active_tasks: Dict[str, str] = {}
        self.results: Dict[str, Any] = {}
        self.worker = BackgroundWorker("bg_agent_worker", max_concurrent=3)
        self._processing = False
    
    async def run_complex_job(self, job_name: str, prompt: str,
                             user_id: str,
                             llm=None, tools=None) -> str:
        """
        Execute a long-running task in a thread and save output to WORKSPACE.
        
        Alpha Cowork: Supports Plan-Execute-Verify cycle with task_plan.json.
        
        Args:
            job_name: Human-readable name for this job
            prompt: The research/task prompt
            user_id: User identifier for sandbox isolation
            llm: Language model (optional)
            tools: Available tools (optional)
        
        Returns:
            The result string (also written to WORKSPACE/<job_name>.md)
        """
        safe_name = "".join(
            c for c in job_name if c.isalnum() or c in "_- "
        ).replace(" ", "_")
        filename = f"{safe_name}.md"
        
        self.active_tasks[job_name] = "Running"
        
        try:
            if "file sort" in prompt.lower() or "organize" in prompt.lower():
                return await self._run_file_sort_task(job_name, safe_name, user_id)
            elif "summar" in prompt.lower() or "summary" in prompt.lower():
                return await self._run_summary_task(job_name, safe_name, user_id, prompt)
            else:
                return await self._run_research_task(
                    job_name, safe_name, filename, prompt, user_id, llm, tools
                )
        except Exception as exc:
            err = f"Error in background job '{job_name}': {exc}"
            self.active_tasks[job_name] = f"✗ Failed: {exc}"
            return err
    
    async def _run_research_task(self, job_name: str, safe_name: str, 
                                 filename: str, prompt: str, user_id: str,
                                 llm=None, tools=None) -> str:
        """Run a research task with Plan-Execute-Verify."""
        def _run():
            from DRIVER.core_brain import get_llm, get_all_tools
            
            _llm = llm or get_llm()
            _tools = tools or get_all_tools()
            
            # Use Plan-Execute-Verify if llm and tools available
            if llm or tools:
                from DRIVER.agent_core import run_agent_with_plan
                from DRIVER.ui_telemetry import get_sidebar_data
                
                system_prompt = (
                    "You are conducting deep research. "
                    "Be thorough, cite sources, and structure findings clearly.\n\n"
                    "You have access to sandbox file tools. "
                    "Always create a task_plan.json before file operations.\n\n"
                    f"User prompt: {prompt}"
                )
                
                try:
                    result = run_agent_with_plan(
                        _llm, _tools, system_prompt, prompt, user_id
                    )
                    return str(result)
                except Exception:
                    # Fallback to simple run
                    from DRIVER.agent_core import run_simple_agent
                    return run_simple_agent(_llm, _tools, system_prompt, prompt)
            else:
                from DRIVER.core_brain import execute_task
                return execute_task(prompt, use_orchestrator=False)
        
        result = await asyncio.to_thread(_run)
        
        write_to_workspace_result = write_to_sandbox(user_id, filename, result)
        self.results[job_name] = filename
        self.active_tasks[job_name] = f"✓ Completed → {filename}"
        
        return result
    
    async def _run_file_sort_task(self, job_name: str, safe_name: str, 
                                  user_id: str) -> str:
        """Run a file sorting task in parallel."""
        from DRIVER.task_manager import task_queue, submit_file_sort_task
        
        # Submit to task queue
        task_id = submit_file_sort_task(task_queue, user_id, "")
        
        self.active_tasks[job_name] = f"Running (task: {task_id})"
        
        # Process queue in background
        async def process():
            await task_queue.process_queue()
        
        # Start processing (don't wait for completion)
        asyncio.create_task(process())
        
        result = f"Started file sort task: {task_id}\n"
        result += "Files are being organized in the background.\n"
        result += "Check status with get_job_status()."
        
        self.results[job_name] = task_id
        # Don't mark as completed - task runs in background
        
        return result
    
    async def _run_summary_task(self, job_name: str, safe_name: str,
                                user_id: str, prompt: str) -> str:
        """Run a document summarization task in parallel."""
        from DRIVER.task_manager import task_queue, submit_doc_summary_task
        
        task_id = submit_doc_summary_task(task_queue, user_id, "")
        
        self.active_tasks[job_name] = f"Running (task: {task_id})"
        
        async def process():
            await task_queue.process_queue()
        
        asyncio.create_task(process())
        
        result = f"Started document summary task: {task_id}\n"
        result += "Documents are being processed in the background.\n"
        result += "Summary will be saved as summary.txt."
        
        self.results[job_name] = task_id
        
        return result
    
    async def run_parallel_tasks(self, tasks: List[Dict[str, Any]],
                                 user_id: str) -> Dict[str, Any]:
        """Run multiple tasks in parallel (Alpha Cowork).
        
        Example:
            tasks = [
                {"type": "file_sort", "folder": "documents"},
                {"type": "summarize", "folder": "reports"},
            ]
        
        Args:
            tasks: List of task dictionaries
            user_id: User identifier
        
        Returns:
            Dictionary with all task IDs and statuses
        """
        from DRIVER.task_manager import task_queue, submit_file_sort_task, submit_doc_summary_task
        
        task_ids = []
        
        for i, task in enumerate(tasks):
            task_type = task.get("type", "")
            folder = task.get("folder", "")
            
            if task_type == "file_sort":
                task_id = submit_file_sort_task(task_queue, user_id, folder)
            elif task_type == "summarize":
                task_id = submit_doc_summary_task(task_queue, user_id, folder)
            else:
                continue
            
            task_ids.append(task_id)
        
        # Process all tasks concurrently
        async def run_all():
            await task_queue.process_queue()
        
        asyncio.create_task(run_all())
        
        return {
            "submitted_tasks": task_ids,
            "status": "processing",
            "message": f"Started {len(task_ids)} parallel tasks"
        }
    
    def get_job_status(self, job_name: str = None) -> Dict[str, Any]:
        """
        Return status of one job or all jobs.
        
        Args:
            job_name: Optional. If omitted, returns all jobs.
        
        Returns:
            Status information
        """
        if job_name:
            if job_name in self.active_tasks:
                # Check if it's a background task queue job
                from DRIVER.task_manager import task_queue
                
                task_job_id = self.results.get(job_name)
                if isinstance(task_job_id, str) and task_job_id.startswith(("file_sort_", "doc_summary_")):
                    task_status = task_queue.get_status(task_job_id)
                    return {
                        "job": job_name,
                        "type": "background_queue_task",
                        "queue_status": task_job_id,
                        "queue_details": task_status,
                        "status": self.active_tasks.get(job_name, "unknown"),
                        "output_file": self.results.get(job_name)
                    }
                
                return {
                    "job": job_name,
                    "type": "research_job",
                    "status": self.active_tasks.get(job_name, "unknown"),
                    "output_file": self.results.get(job_name)
                }
            return {"error": f"Job '{job_name}' not found"}
        
        # Get queue status for all tasks
        from DRIVER.task_manager import task_queue
        queue_status = task_queue.get_status()
        
        return {
            "active": {},  # Empty dict for compatibility with ui_telemetry.items() call
            "queued": queue_status.get("queued", 0),
            "completed_tasks": queue_status.get("completed", 0),
            "failed_tasks": queue_status.get("failed", 0),
            "active_jobs": self.active_tasks,
            "completed_files": list(self.results.values())
        }
    
    def read_job_result(self, job_name: str, user_id: str) -> str:
        """
        Read the WORKSPACE file written by a completed job.

        Args:
            job_name: The job's name
            user_id: User identifier for sandbox isolation

        Returns:
            Job output content
        """
        if job_name not in self.results:
            return f"Job '{job_name}' not found or not yet completed."

        filename = self.results[job_name]

        # If it's a queue task ID, check queue status
        if isinstance(filename, str) and filename.startswith(("file_sort_", "doc_summary_")):
            from DRIVER.task_manager import task_queue
            status = task_queue.get_status(filename)
            return f"Background task status: {status}"

        return read_from_sandbox(user_id, filename)
    
    async def wait_for_queue(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Wait for all background tasks to complete.
        
        Args:
            timeout: Max wait time in seconds
        
        Returns:
            Final queue status
        """
        from DRIVER.task_manager import task_queue
        import asyncio
        
        try:
            # Start processing if not already running
            asyncio.create_task(task_queue.process_queue())
            
            # Wait for queue to drain
            start = asyncio.get_event_loop().time()
            while True:
                status = task_queue.get_status()
                if status["queued"] == 0 and status["running"] == 0:
                    break
                
                if asyncio.get_event_loop().time() - start > timeout:
                    return {"status": "timeout", "queue": status}
                
                await asyncio.sleep(0.5)
            
            return task_queue.get_status()
        except Exception as e:
            return {"error": str(e)}


# Global singleton
bg_agent = BackgroundAgent()


# Convenience function for quick background research
async def background_research(topic: str, user_id: str) -> str:
    """Start a background research job.
    
    Args:
        topic: Research topic
        user_id: User identifier
    
    Returns:
        Job ID and status
    """
    job_name = f"Research_{topic[:30].replace(' ', '_')}"
    prompt = f"Conduct comprehensive research on: {topic}. Include latest info, key findings, and actionable insights."
    
    result = await bg_agent.run_complex_job(job_name, prompt, user_id)
    return result