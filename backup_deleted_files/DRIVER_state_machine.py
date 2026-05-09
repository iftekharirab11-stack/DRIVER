# [GOAL] Worker State Machine for Background Execution
# [CONTEXT] Track task progress, estimate TTC (Time To Complete), handle retries.

import time
from enum import Enum, auto
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio

class TaskState(Enum):
    """Finite state machine for task lifecycle."""
    PENDING = auto()
    RUNNING = auto()
    WAITING = auto()  # Waiting for dependency or resource
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()
    CANCELLED = auto()

@dataclass
class TaskStep:
    """A single step within a task."""
    name: str
    estimated_duration: float  # seconds
    actual_duration: float = 0.0
    status: TaskState = TaskState.PENDING
    error: str = None
    
    @property
    def is_complete(self) -> bool:
        return self.status in [TaskState.COMPLETED, TaskState.FAILED]

@dataclass
class WorkerTask:
    """Represents a tracked background task with state machine."""
    task_id: str
    description: str
    steps: list[TaskStep] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    current_step_index: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    progress_callback: Optional[Callable] = None
    
    @property
    def progress_percent(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.is_complete)
        return (completed / len(self.steps)) * 100
    
    @property
    def elapsed_seconds(self) -> float:
        start = self.started_at or self.created_at
        return (datetime.now() - start).total_seconds()
    
    @property
    def eta_seconds(self) -> float:
        """Estimate remaining time based on actual step timings."""
        if self.current_step_index >= len(self.steps):
            return 0
        
        # Calculate average duration of completed steps
        completed_steps = [s for s in self.steps if s.is_complete and s.actual_duration > 0]
        if not completed_steps:
            # No completed steps, use estimates
            remaining_estimates = [s.estimated_duration for s in self.steps[self.current_step_index:]]
            return sum(remaining_estimates)
        
        avg_step_time = sum(s.actual_duration for s in completed_steps) / len(completed_steps)
        remaining_steps = len(self.steps) - self.current_step_index
        return avg_step_time * remaining_steps
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "state": self.state.name,
            "progress": round(self.progress_percent, 1),
            "current_step": self.current_step_index + 1,
            "total_steps": len(self.steps),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "eta_seconds": round(self.eta_seconds, 1),
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat()
        }

class TaskStateMachine:
    """Manages task state transitions and tracking."""
    
    def __init__(self):
        self.tasks: Dict[str, WorkerTask] = {}
        self._lock = asyncio.Lock()
    
    def create_task(self, task_id: str, description: str, steps: list) -> WorkerTask:
        """Create a new tracked task."""
        task = WorkerTask(
            task_id=task_id,
            description=description,
            steps=[TaskStep(name=s["name"], estimated_duration=s.get("estimate", 10.0)) 
                   for s in steps]
        )
        self.tasks[task_id] = task
        return task
    
    async def transition_to(self, task_id: str, new_state: TaskState, step_index: int = None):
        """Safely transition task state."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            task.state = new_state
            
            if new_state == TaskState.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            elif new_state == TaskState.COMPLETED:
                task.completed_at = datetime.now()
                task.current_step_index = len(task.steps)
            elif new_state == TaskState.FAILED:
                task.retry_count += 1
                if task.retry_count < task.max_retries:
                    task.state = TaskState.RETRYING
            
            if step_index is not None:
                task.current_step_index = step_index
            
            # Invoke callback if registered
            if task.progress_callback:
                try:
                    task.progress_callback(task.to_dict())
                except Exception:
                    pass  # Don't break on callback errors
    
    def get_task(self, task_id: str) -> Optional[WorkerTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(self, state: TaskState = None) -> list:
        """List all tasks, optionally filtered by state."""
        tasks = list(self.tasks.values())
        if state:
            tasks = [t for t in tasks if t.state == state]
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self.tasks.get(task_id)
        if task and task.state in [TaskState.PENDING, TaskState.RUNNING]:
            task.state = TaskState.CANCELLED
            return True
        return False
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for tid, task in self.tasks.items():
            if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                if task.completed_at and task.completed_at < cutoff:
                    to_remove.append(tid)
        
        for tid in to_remove:
            del self.tasks[tid]

# Global state machine instance
state_machine = TaskStateMachine()

# [HELPER] Decorator to auto-wrap functions as tracked tasks
def tracked_task(description: str = None):
    """Decorator to automatically track function execution."""
    def decorator(func: Callable):
        def wrapper(*args, task_id: str = None, **kwargs):
            if task_id is None:
                import uuid
                task_id = f"{func.__name__}_{uuid.uuid4().hex[:8]}"
            
            task_desc = description or f"Execute {func.__name__}"
            task = state_machine.create_task(task_id, task_desc, [
                {"name": "Initialize", "estimate": 1.0},
                {"name": "Execute", "estimate": 5.0},
                {"name": "Finalize", "estimate": 1.0}
            ])
            
            # Auto-execute with state tracking
            import asyncio
            
            async def run_tracked():
                try:
                    await state_machine.transition_to(task_id, TaskState.RUNNING, 0)
                    result = await asyncio.to_thread(func, *args, **kwargs)
                    await state_machine.transition_to(task_id, TaskState.COMPLETED)
                    return result
                except Exception as e:
                    await state_machine.transition_to(task_id, TaskState.FAILED)
                    raise
            
            return asyncio.create_task(run_tracked()), task_id
        
        return wrapper
    return decorator

# [EXAMPLE] Usage
@tracked_task("Deep web research")
def perform_research(query: str):
    """Example tracked task."""
    time.sleep(2)  # Simulate work
    return f"Research complete: {query}"