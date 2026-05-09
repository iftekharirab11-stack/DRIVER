"""
Enhanced AI Orchestration System
Provides robust AI execution with retries, failover, and monitoring
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
import asyncio
from datetime import datetime

# Configure AI orchestration logger
ai_logger = logging.getLogger("ai_orchestrator")
ai_logger.setLevel(logging.INFO)

class AIExecutionError(Exception):
    """Custom exception for AI execution failures"""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.timestamp = datetime.now()

class AIProvider:
    """Base class for AI providers with failover capabilities"""

    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.is_available = True
        self.last_failure = None
        self.failure_count = 0
        self.success_count = 0
        self.last_used = None

    def check_health(self) -> bool:
        """Check if provider is healthy and available"""
        return self.is_available

    def record_success(self):
        """Record successful execution"""
        self.success_count += 1
        self.failure_count = max(0, self.failure_count - 1)  # Reset failure count
        self.last_used = datetime.now()

    def record_failure(self, error: Exception):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure = error
        self.last_used = datetime.now()

        # Disable provider if too many consecutive failures
        if self.failure_count >= 3:
            self.is_available = False
            ai_logger.warning(f"Disabled provider {self.name} due to repeated failures")

    def reset(self):
        """Reset provider statistics"""
        self.failure_count = 0
        self.is_available = True
        self.last_failure = None

class AIProviderManager:
    """Manages multiple AI providers with failover and load balancing"""

    def __init__(self):
        self.providers: List[AIProvider] = []
        self.current_provider_index = 0

    def add_provider(self, provider: AIProvider):
        """Add a provider to the pool"""
        self.providers.append(provider)
        self.providers.sort(key=lambda p: p.priority)
        ai_logger.info(f"Added AI provider: {provider.name} (priority: {provider.priority})")

    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available providers"""
        return [p for p in self.providers if p.check_health()]

    def get_next_provider(self) -> Optional[AIProvider]:
        """Get next available provider using round-robin strategy"""
        available_providers = self.get_available_providers()
        if not available_providers:
            return None

        # Round-robin selection
        provider = available_providers[self.current_provider_index % len(available_providers)]
        self.current_provider_index += 1
        return provider

    def reset_all_providers(self):
        """Reset all providers"""
        for provider in self.providers:
            provider.reset()
        ai_logger.info("Reset all AI providers")

class AITaskOrchestrator:
    """Orchestrates AI task execution with retries, timeouts, and monitoring"""

    def __init__(self, max_retries: int = 2, timeout: float = 30.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self.provider_manager = AIProviderManager()
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "retry_count": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }

    def add_provider(self, provider: AIProvider):
        """Add an AI provider"""
        self.provider_manager.add_provider(provider)

    def record_execution(self, success: bool, duration: float):
        """Record task execution metrics"""
        self.metrics["total_tasks"] += 1
        if success:
            self.metrics["successful_tasks"] += 1
        else:
            self.metrics["failed_tasks"] += 1

        self.metrics["total_execution_time"] += duration
        self.metrics["avg_execution_time"] = (
            self.metrics["total_execution_time"] / max(1, self.metrics["total_tasks"])
        )

    async def execute_with_retry(self, task_func: Callable, *args, **kwargs) -> Any:
        """
        Execute a task with retry logic and provider failover

        Args:
            task_func: Function to execute
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result of the task execution

        Raises:
            AIExecutionError: If all retries fail
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries + 1):
            provider = self.provider_manager.get_next_provider()
            if not provider:
                raise AIExecutionError("No available AI providers", last_error)

            try:
                ai_logger.info(f"Executing task (attempt {attempt + 1}/{self.max_retries + 1}) with provider: {provider.name}")

                # Execute with timeout
                if asyncio.iscoroutinefunction(task_func):
                    result = await asyncio.wait_for(task_func(*args, **kwargs), timeout=self.timeout)
                else:
                    # Run sync function in executor with timeout
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: task_func(*args, **kwargs)),
                        timeout=self.timeout
                    )

                # Record success
                duration = time.time() - start_time
                provider.record_success()
                self.record_execution(True, duration)

                ai_logger.info(f"Task completed successfully with provider: {provider.name} (duration: {duration:.2f}s)")
                return result

            except asyncio.TimeoutError:
                last_error = AIExecutionError(f"Task timed out after {self.timeout} seconds", None)
                ai_logger.warning(f"Timeout on attempt {attempt + 1} with provider {provider.name}: {str(last_error)}")
                provider.record_failure(last_error)
                self.metrics["retry_count"] += 1

            except Exception as e:
                last_error = AIExecutionError(f"Execution failed with provider {provider.name}", e)
                ai_logger.error(f"Error on attempt {attempt + 1} with provider {provider.name}: {str(e)}")
                provider.record_failure(last_error)
                self.metrics["retry_count"] += 1

            # Small delay before retry
            if attempt < self.max_retries:
                await asyncio.sleep(min(2 ** attempt, 5))  # Exponential backoff

        # All retries failed
        self.record_execution(False, time.time() - start_time)
        raise last_error

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestration metrics"""
        provider_stats = {
            p.name: {
                "success_count": p.success_count,
                "failure_count": p.failure_count,
                "is_available": p.is_available,
                "last_failure": str(p.last_failure) if p.last_failure else None
            }
            for p in self.provider_manager.providers
        }

        return {
            **self.metrics,
            "providers": provider_stats,
            "success_rate": self.metrics["successful_tasks"] / max(1, self.metrics["total_tasks"]),
            "failure_rate": self.metrics["failed_tasks"] / max(1, self.metrics["total_tasks"])
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "retry_count": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }

def create_ai_task_monitor():
    """Create a global AI task monitor instance"""
    return AITaskOrchestrator()

# Global AI orchestrator instance
ai_orchestrator = create_ai_task_monitor()

def with_ai_monitoring(func):
    """Decorator to add AI execution monitoring to functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            ai_logger.info(f"AI task completed: {func.__name__} (duration: {duration:.2f}s)")
            return result
        except Exception as e:
            duration = time.time() - start_time
            ai_logger.error(f"AI task failed: {func.__name__} (duration: {duration:.2f}s) - {str(e)}")
            raise
    return wrapper

class AIContextManager:
    """Manages AI execution context with token budgeting and memory management"""

    def __init__(self, max_tokens: int = 4096, max_history: int = 10):
        self.max_tokens = max_tokens
        self.max_history = max_history
        self.current_context = {
            "token_usage": 0,
            "history": [],
            "tools_used": []
        }

    def add_to_context(self, content: str, token_count: int):
        """Add content to execution context"""
        self.current_context["token_usage"] += token_count
        self.current_context["history"].append(content)

        # Enforce token budget
        if self.current_context["token_usage"] > self.max_tokens * 0.9:  # 90% threshold
            self.truncate_context()

        # Enforce history limit
        if len(self.current_context["history"]) > self.max_history:
            self.current_context["history"] = self.current_context["history"][-self.max_history:]

    def add_tool_usage(self, tool_name: str):
        """Record tool usage"""
        self.current_context["tools_used"].append(tool_name)

    def truncate_context(self):
        """Truncate context to stay within token budget"""
        if len(self.current_context["history"]) > 1:
            # Keep the most recent 50% of history
            keep_count = max(1, len(self.current_context["history"]) // 2)
            removed = self.current_context["history"][:len(self.current_context["history"]) - keep_count]
            self.current_context["history"] = self.current_context["history"][-keep_count:]

            # Estimate tokens removed (simple approximation)
            avg_token_per_item = self.current_context["token_usage"] / max(1, len(self.current_context["history"]) + len(removed))
            self.current_context["token_usage"] -= len(removed) * avg_token_per_item

            ai_logger.info(f"Truncated AI context: removed {len(removed)} items, kept {len(self.current_context['history'])} items")

    def get_context_summary(self) -> Dict[str, Any]:
        """Get current context summary"""
        return {
            "token_usage": self.current_context["token_usage"],
            "token_limit": self.max_tokens,
            "token_utilization": self.current_context["token_usage"] / max(1, self.max_tokens),
            "history_count": len(self.current_context["history"]),
            "tools_used": len(self.current_context["tools_used"]),
            "tools_list": self.current_context["tools_used"][-5:]  # Last 5 tools
        }

    def reset_context(self):
        """Reset execution context"""
        self.current_context = {
            "token_usage": 0,
            "history": [],
            "tools_used": []
        }
        ai_logger.info("Reset AI execution context")

# Global AI context manager
ai_context_manager = AIContextManager()

def get_ai_orchestrator() -> AITaskOrchestrator:
    """Get global AI orchestrator instance"""
    return ai_orchestrator

def get_ai_context_manager() -> AIContextManager:
    """Get global AI context manager instance"""
    return ai_context_manager