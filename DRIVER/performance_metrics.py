# [GOAL] Track Token Usage, Cost, and Aggregation for SaaS Billing
# [CONTEXT] Per-user/per-session tracking for AI spending.

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os

@dataclass
class TokenUsage:
    """Represents a single LLM API call."""
    user_id: str
    session_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.now)
    endpoint: str = "chat"  # chat, research, etc.
    
    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint
        }

class PerformanceMetrics:
    """Aggregates usage data for billing and monitoring."""
    
    # Pricing per 1K tokens (approximate, update as needed)
    PRICING = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    def __init__(self, storage_path: str = "metrics_store.json"):
        self.storage_path = storage_path
        self.usage_log: Dict[str, TokenUsage] = {}
        self.session_totals: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        """Load metrics from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Reconstruct usage log
                    for record in data.get("usage", []):
                        usage = TokenUsage(
                            user_id=record["user_id"],
                            session_id=record["session_id"],
                            model=record["model"],
                            prompt_tokens=record["prompt_tokens"],
                            completion_tokens=record["completion_tokens"],
                            total_tokens=record["total_tokens"],
                            cost_usd=record["cost_usd"],
                            timestamp=datetime.fromisoformat(record["timestamp"]),
                            endpoint=record.get("endpoint", "chat")
                        )
                        self.usage_log[record["timestamp"]] = usage
            except Exception:
                pass  # Corrupted file, start fresh
    
    def _save(self):
        """Persist metrics to disk."""
        data = {
            "usage": [u.as_dict for u in self.usage_log.values()],
            "session_totals": self.session_totals
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def record_usage(self, usage: TokenUsage):
        """Record a new usage event."""
        key = f"{usage.user_id}_{usage.session_id}_{usage.timestamp.isoformat()}"
        self.usage_log[key] = usage
        
        # Update session totals
        sid = usage.session_id
        if sid not in self.session_totals:
            self.session_totals[sid] = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "requests": 0,
                "user_id": usage.user_id
            }
        
        sess = self.session_totals[sid]
        sess["total_tokens"] += usage.total_tokens
        sess["total_cost"] += usage.cost_usd
        sess["requests"] += 1
        
        self._save()
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on model and token counts."""
        pricing = self.PRICING.get(model, {"input": 0.001, "output": 0.002})
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    def get_user_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregated stats for a user."""
        cutoff = datetime.now() - timedelta(days=days)
        
        user_usages = [
            u for u in self.usage_log.values()
            if u.user_id == user_id and u.timestamp >= cutoff
        ]
        
        if not user_usages:
            return {"error": "No usage data"}
        
        total_tokens = sum(u.total_tokens for u in user_usages)
        total_cost = sum(u.cost_usd for u in user_usages)
        
        # Breakdown by model
        by_model = {}
        for u in user_usages:
            if u.model not in by_model:
                by_model[u.model] = {"tokens": 0, "cost": 0.0, "requests": 0}
            by_model[u.model]["tokens"] += u.total_tokens
            by_model[u.model]["cost"] += u.cost_usd
            by_model[u.model]["requests"] += 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": len(user_usages),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "breakdown_by_model": by_model,
            "avg_tokens_per_request": round(total_tokens / len(user_usages), 1)
        }
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        recent = [u for u in self.usage_log.values() if u.timestamp >= last_hour]
        
        return {
            "timestamp": now.isoformat(),
            "requests_last_hour": len(recent),
            "tokens_last_hour": sum(u.total_tokens for u in recent),
            "cost_last_hour": round(sum(u.cost_usd for u in recent), 6),
            "active_sessions": len(self.session_totals),
            "top_users": self._get_top_users(limit=5)
        }
    
    def _get_top_users(self, limit: int = 5) -> list:
        """Get top users by token usage."""
        user_totals = {}
        for usage in self.usage_log.values():
            uid = usage.user_id
            if uid not in user_totals:
                user_totals[uid] = {"tokens": 0, "cost": 0.0}
            user_totals[uid]["tokens"] += usage.total_tokens
            user_totals[uid]["cost"] += usage.cost_usd
        
        sorted_users = sorted(user_totals.items(), 
                            key=lambda x: x[1]["tokens"], reverse=True)
        return [{"user_id": uid, "tokens": data["tokens"], "cost": data["cost"]} 
                for uid, data in sorted_users[:limit]]

# Global metrics instance
metrics = PerformanceMetrics()

# [GOAL] Hook into LangChain to auto-track
def track_llm_call(user_id: str, session_id: str, model: str, 
                   prompt_tokens: int, completion_tokens: int):
    """Record an LLM API call."""
    total = prompt_tokens + completion_tokens
    cost = metrics.calculate_cost(model, prompt_tokens, completion_tokens)
    
    usage = TokenUsage(
        user_id=user_id,
        session_id=session_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total,
        cost_usd=cost
    )
    metrics.record_usage(usage)
    return usage