# [GOAL] Parallel Task Execution & Queueing
# [CONTEXT] Handle multiple works without "Boring" the user or the system.

import asyncio
from typing import Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class QueuedTask:
    """Represents a single task in the queue."""
    task_id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: str = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None

class TaskQueue:
    """Manages parallel task execution with tracking."""
    
    def __init__(self, max_concurrent: int = 3):
        self.queue: List[QueuedTask] = []
        self.results: Dict[str, Any] = {}
        self.max_concurrent = max_concurrent
        self.running: List[QueuedTask] = []
        
    def add_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Add a task to the queue.
        
        Args:
            task_id: Unique identifier
            func: Function to execute
            *args, **kwargs: Arguments to pass
            
        Returns:
            Task ID for tracking
        """
        task = QueuedTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs
        )
        self.queue.append(task)
        print(f"[QUEUE] Added task '{task_id}' (queue size: {len(self.queue)})")
        return task_id
    
    async def process_queue(self):
        """Process all queued tasks with concurrency limit."""
        while self.queue or self.running:
            # Start new tasks if capacity available
            while len(self.running) < self.max_concurrent and self.queue:
                task = self.queue.pop(0)
                task.status = "running"
                task.started_at = datetime.now()
                self.running.append(task)
                
                # Execute in background
                asyncio.create_task(self._execute_task(task))
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
        
        print("[QUEUE] All tasks completed")
    
    async def _execute_task(self, task: QueuedTask):
        """Execute a single task."""
        try:
            # Support both sync and async functions
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.status = "completed"
            self.results[task.task_id] = result
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self.results[task.task_id] = f"ERROR: {str(e)}"
        finally:
            task.completed_at = datetime.now()
            self.running.remove(task)
    
    def get_status(self, task_id: str = None) -> Dict[str, Any]:
        """Get task status."""
        if task_id:
            task = next((t for t in self.queue + self.running if t.task_id == task_id), None)
            if task:
                return {
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": task.result,
                    "error": task.error,
                    "created_at": task.created_at.isoformat()
                }
            return {"error": f"Task {task_id} not found"}
        
        # Summary all
        return {
            "queued": len(self.queue),
            "running": len(self.running),
            "completed": len([t for t in self.results.values() if not str(t).startswith("ERROR")]),
            "failed": len([t for t in self.results.values() if str(t).startswith("ERROR")])
        }
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get all task results."""
        return self.results
    
    async def wait_for_task(self, task_id: str, timeout: float = 30) -> Any:
        """Wait for a specific task to complete."""
        import asyncio
        start = asyncio.get_event_loop().time()
        while True:
            if task_id in self.results:
                return self.results[task_id]
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            await asyncio.sleep(0.5)

# Global singleton
task_queue = TaskQueue(max_concurrent=3)

# [GOAL] Convenience wrapper functions
def submit_task(name: str, func: Callable, *args, **kwargs) -> str:
    """Submit a task to the queue."""
    import uuid
    task_id = f"{name}_{uuid.uuid4().hex[:8]}"
    return task_queue.add_task(task_id, func, *args, **kwargs)

async def run_all_tasks():
    """Start processing the queue."""
    await task_queue.process_queue()