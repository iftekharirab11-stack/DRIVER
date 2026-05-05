# [GOAL] Parallel Task Execution & Queueing
# [CONTEXT] Handle multiple works without "Boring" the user or the system.
# [ALPHA COWORK] Enhanced with BackgroundWorker parallel processing and file task support

import asyncio
import time
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


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
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0  # 0-100 percentage


class BackgroundWorker:
    """Worker that executes file and compute tasks in parallel.
    
    Supports:
    - File operations (sorting, organizing)
    - Document processing (summarization)
    - Long-running tasks without blocking chat
    """
    
    def __init__(self, worker_id: str, max_concurrent: int = 3):
        self.worker_id = worker_id
        self.queue: List[QueuedTask] = []
        self.results: Dict[str, Any] = {}
        self.max_concurrent = max_concurrent
        self.running: List[QueuedTask] = []
        self.completed: List[QueuedTask] = []
        self._lock = asyncio.Lock()
        self._running = False
    
    def add_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Add a task to the worker queue.
        
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
        return task_id
    
    async def process_queue(self):
        """Process all queued tasks with concurrency limit."""
        self._running = True
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
        
        self._running = False
    
    async def _execute_task(self, task: QueuedTask):
        """Execute a single task."""
        try:
            # Support both sync and async functions
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, task.func, *task.args, **task.kwargs
                )
            
            task.result = result
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            self.results[task.task_id] = result
            self.completed.append(task)
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.progress = 0
            task.completed_at = datetime.now()
            self.results[task.task_id] = f"ERROR: {str(e)}"
        finally:
            self.running = [t for t in self.running if t.task_id != task.task_id]
    
    def get_job_status(self, task_id: str = None) -> Dict[str, Any]:
        """Get status of one job or all jobs.
        
        Args:
            task_id: Optional specific task ID
        
        Returns:
            Status dictionary
        """
        if task_id:
            task = next((t for t in self.queue + self.running + self.completed 
                        if t.task_id == task_id), None)
            if task:
                return {
                    "task_id": task.task_id,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "result": task.result,
                    "error": task.error
                }
            return {"error": f"Task {task_id} not found"}
        
        # Summary all
        return {
            "active": len(self.running),
            "queued": len(self.queue),
            "completed": len([t for t in self.completed if t.status == "completed"]),
            "failed": len([t for t in self.completed if t.status == "failed"]),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "status": t.status,
                    "progress": t.progress
                }
                for t in (self.queue + self.running + self.completed)
            ]
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task.
        
        Args:
            task_id: ID of task to cancel
        
        Returns:
            True if cancelled
        """
        for i, task in enumerate(self.queue):
            if task.task_id == task_id:
                self.queue.pop(i)
                task.status = "cancelled"
                return True
        return False


class TaskQueue:
    """Manages parallel task execution with tracking.
    
    Coordinates multiple BackgroundWorkers for high-throughput processing.
    """
    
    def __init__(self, max_concurrent: int = 3, num_workers: int = 2):
        self.workers: List[BackgroundWorker] = [
            BackgroundWorker(f"worker_{i}", max_concurrent)
            for i in range(num_workers)
        ]
        self.results: Dict[str, Any] = {}
        self._task_to_worker: Dict[str, int] = {}
        self.max_concurrent = max_concurrent
    
    def add_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Add a task to the least-busy worker.
        
        Args:
            task_id: Unique identifier
            func: Function to execute
            *args, **kwargs: Arguments to pass
        
        Returns:
            Task ID for tracking
        """
        # Find least busy worker
        worker_idx = min(
            range(len(self.workers)),
            key=lambda i: len(self.workers[i].queue) + len(self.workers[i].running)
        )
        
        self.workers[worker_idx].add_task(task_id, func, *args, **kwargs)
        self._task_to_worker[task_id] = worker_idx
        return task_id
    
    async def process_queue(self):
        """Process all workers' queues concurrently."""
        await asyncio.gather(
            *[worker.process_queue() for worker in self.workers]
        )
    
    def get_status(self, task_id: str = None) -> Dict[str, Any]:
        """Get task status."""
        if task_id:
            worker_idx = self._task_to_worker.get(task_id)
            if worker_idx is not None:
                return self.workers[worker_idx].get_job_status(task_id)
            return {"error": f"Task {task_id} not found"}
        
        # Summary all workers
        all_tasks = []
        for worker in self.workers:
            all_tasks.extend(worker.queue)
            all_tasks.extend(worker.running)
            all_tasks.extend(worker.completed)
        
        return {
            "queued": len([t for t in all_tasks if t.status == "pending"]),
            "running": len([t for t in all_tasks if t.status == "running"]),
            "completed": len([t for t in all_tasks if t.status == "completed"]),
            "failed": len([t for t in all_tasks if t.status == "failed"]),
        }
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get all task results."""
        results = {}
        for worker in self.workers:
            results.update(worker.results)
        return results
    
    async def wait_for_task(self, task_id: str, timeout: float = 30) -> Any:
        """Wait for a specific task to complete.
        
        Args:
            task_id: ID of task to wait for
            timeout: Max wait time in seconds
        
        Returns:
            Task result
        
        Raises:
            TimeoutError: If task times out
        """
        import asyncio
        start = asyncio.get_event_loop().time()
        while True:
            worker_idx = self._task_to_worker.get(task_id)
            if worker_idx is not None:
                worker = self.workers[worker_idx]
                task = next((t for t in worker.completed if t.task_id == task_id), None)
                if task and task.status == "completed":
                    return task.result
                if task and task.status == "failed":
                    raise RuntimeError(f"Task failed: {task.error}")
            
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.5)


def submit_file_sort_task(task_queue: TaskQueue, user_id: str, folder: str):
    """Submit a file sorting task to the queue.
    
    Args:
        task_queue: Task queue
        user_id: User identifier
        folder: Folder to sort
    
    Returns:
        Task ID
    """
    from DRIVER.sandbox_driver import list_directory
    
    task_id = f"file_sort_{uuid.uuid4().hex[:8]}"
    
    def sort_files():
        """Sort files by type into subfolders."""
        items = list_directory(user_id, folder)
        if isinstance(items, list):
            docs = [i for i in items if isinstance(i, dict) and not i.get('is_dir')]
            
            # Group by extension
            by_ext = {}
            for doc in docs:
                ext = doc['name'].split('.')[-1].lower()
                if ext not in by_ext:
                    by_ext[ext] = []
                by_ext[ext].append(doc['name'])
            
            # Create subfolders and move files
            from DRIVER.sandbox_driver import move_file_sandbox
            for ext, files in by_ext.items():
                if len(files) > 1:
                    folder_name = f"{ext}_files"
                    for fname in files:
                        move_file_sandbox(user_id, fname, fname, folder, folder_name)
            
            return f"Sorted {len(docs)} files into {len(by_ext)} categories"
        return "No files found"
    
    task_queue.add_task(task_id, sort_files)
    return task_id


def submit_doc_summary_task(task_queue: TaskQueue, user_id: str, folder: str):
    """Submit a document summarization task to the queue.
    
    Args:
        task_queue: Task queue
        user_id: User identifier  
        folder: Folder containing documents
    
    Returns:
        Task ID
    """
    from DRIVER.sandbox_driver import list_directory, read_from_sandbox
    
    task_id = f"doc_summary_{uuid.uuid4().hex[:8]}"
    
    def summarize_docs():
        """Summarize all documents in folder."""
        items = list_directory(user_id, folder)
        if isinstance(items, list):
            summaries = []
            for item in items:
                if isinstance(item, dict) and not item.get('is_dir'):
                    content = read_from_sandbox(user_id, item['name'], folder)
                    # Simple word count summary
                    word_count = len(str(content).split())
                    summaries.append(f"{item['name']}: {word_count} words")
            
            # Save summary
            summary_text = "\n".join(summaries)
            from DRIVER.sandbox_driver import write_to_sandbox
            write_to_sandbox(user_id, "summary.txt", summary_text, folder)
            
            return f"Summarized {len(summaries)} documents"
        return "No documents found"
    
    task_queue.add_task(task_id, summarize_docs)
    return task_id


# Global singleton
task_queue = TaskQueue(max_concurrent=3, num_workers=2)


# Convenience wrapper functions
def submit_task(name: str, func: Callable, *args, **kwargs) -> str:
    """Submit a task to the queue.
    
    Args:
        name: Task name
        func: Function to execute
        *args, **kwargs: Arguments
    
    Returns:
        Task ID
    """
    task_id = f"{name}_{uuid.uuid4().hex[:8]}"
    return task_queue.add_task(task_id, func, *args, **kwargs)


async def run_all_tasks():
    """Start processing the queue."""
    await task_queue.process_queue()