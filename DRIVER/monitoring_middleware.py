"""
Monitoring Middleware for Alpha SaaS
Provides request tracing, logging, and performance monitoring
"""

import time
import uuid
import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure monitoring logger
monitoring_logger = logging.getLogger("monitoring")
monitoring_logger.setLevel(logging.INFO)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing, logging, and performance monitoring"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Get user info if available
        user_id = request.headers.get("X-User-ID", "anonymous")
        session_id = request.headers.get("X-Session-ID", "none")

        # Get path and method
        path = request.url.path
        method = request.method

        # Start timing
        start_time = time.time()

        # Log request start
        monitoring_logger.info(
            f"REQUEST_START | {request_id} | {user_id} | {session_id} | {method} {path}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Log request completion
            monitoring_logger.info(
                f"REQUEST_END | {request_id} | {user_id} | {session_id} | {method} {path} | "
                f"status={status_code} | duration={duration:.4f}s"
            )

            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.4f}"

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            monitoring_logger.error(
                f"REQUEST_ERROR | {request_id} | {user_id} | {session_id} | {method} {path} | "
                f"error={str(e)} | duration={duration:.4f}s"
            )

            # Re-raise the exception
            raise

class PerformanceMonitor:
    """Performance monitoring utilities"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "requests_by_endpoint": {},
            "requests_by_user": {},
            "current_concurrent_requests": 0,
            "max_concurrent_requests": 0
        }
        self.start_time = time.time()

    def record_request(self, endpoint: str, user_id: str, duration: float, success: bool):
        """Record a request for performance metrics"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        self.metrics["total_response_time"] += duration
        self.metrics["avg_response_time"] = self.metrics["total_response_time"] / max(1, self.metrics["total_requests"])

        # Track by endpoint
        endpoint_metrics = self.metrics["requests_by_endpoint"].setdefault(endpoint, {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0
        })
        endpoint_metrics["count"] += 1
        endpoint_metrics["total_time"] += duration
        endpoint_metrics["avg_time"] = endpoint_metrics["total_time"] / endpoint_metrics["count"]

        # Track by user
        user_metrics = self.metrics["requests_by_user"].setdefault(user_id, {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0
        })
        user_metrics["count"] += 1
        user_metrics["total_time"] += duration
        user_metrics["avg_time"] = user_metrics["total_time"] / user_metrics["count"]

    def start_request(self):
        """Increment concurrent request counter"""
        self.metrics["current_concurrent_requests"] += 1
        self.metrics["max_concurrent_requests"] = max(
            self.metrics["max_concurrent_requests"],
            self.metrics["current_concurrent_requests"]
        )

    def end_request(self):
        """Decrement concurrent request counter"""
        self.metrics["current_concurrent_requests"] = max(0, self.metrics["current_concurrent_requests"] - 1)

    def get_metrics(self):
        """Get current performance metrics"""
        uptime = time.time() - self.start_time

        return {
            "uptime_seconds": uptime,
            "requests_per_second": self.metrics["total_requests"] / max(1, uptime),
            "success_rate": self.metrics["successful_requests"] / max(1, self.metrics["total_requests"]),
            "failure_rate": self.metrics["failed_requests"] / max(1, self.metrics["total_requests"]),
            "average_response_time_seconds": self.metrics["avg_response_time"],
            "current_concurrent_requests": self.metrics["current_concurrent_requests"],
            "max_concurrent_requests": self.metrics["max_concurrent_requests"],
            "top_endpoints": sorted(
                self.metrics["requests_by_endpoint"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5],
            "top_users": sorted(
                self.metrics["requests_by_user"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5]
        }

    def reset_metrics(self):
        """Reset performance metrics (useful for testing)"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "requests_by_endpoint": {},
            "requests_by_user": {},
            "current_concurrent_requests": 0,
            "max_concurrent_requests": 0
        }
        self.start_time = time.time()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_monitoring_middleware() -> MonitoringMiddleware:
    """Get configured monitoring middleware instance"""
    return MonitoringMiddleware

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return performance_monitor