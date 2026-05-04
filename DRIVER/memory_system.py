import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# [CONTEXT] Simple file-based memory system
class MemoryBank:
    def __init__(self, storage_path: str = "memory_store.json"):
        self.storage_path = storage_path
        self.memories: Dict[str, List[Dict[str, Any]]] = {}
        self._load()
    
    def _load(self):
        """Load memories from disk"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                self.memories = json.load(f)
    
    def _save(self):
        """Persist memories to disk"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.memories, f, indent=2, default=str)
    
    def add_memory(self, key: str, content: str, metadata: Optional[Dict] = None):
        """Store a memory under a key (e.g., 'user_info', 'preferences', 'tasks')"""
        if key not in self.memories:
            self.memories[key] = []
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "metadata": metadata or {}
        }
        self.memories[key].append(entry)
        self._save()
    
    def get_memories(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent memories for a key"""
        return self.memories.get(key, [])[-limit:]
    
    def recall(self, key: str, query: Optional[str] = None) -> str:
        """Get formatted memory context for a key"""
        memories = self.get_memories(key)
        if not memories:
            return f"No memories found for '{key}'"
        
        result = f"=== {key.upper()} MEMORY ===\n"
        for mem in reversed(memories):  # Most recent first
            result += f"[{mem['timestamp']}] {mem['content']}\n"
        return result
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword search across all memories"""
        results = []
        for key, entries in self.memories.items():
            for entry in entries:
                if query.lower() in entry['content'].lower():
                    results.append({**entry, "key": key})
        return results
    
    def clear(self, key: Optional[str] = None):
        """Clear all memories or specific key"""
        if key:
            self.memories.pop(key, None)
        else:
            self.memories = {}
        self._save()

# Global memory instance
memory_bank = MemoryBank()

# [GOAL] Memory tools for the agent
def remember(key: str, content: str, metadata: dict = None) -> str:
    """Store information in long-term memory.
    
    Args:
        key: Category like 'user_profile', 'tasks', 'preferences'
        content: The information to remember
        metadata: Optional metadata dict
    
    Returns:
        Confirmation message
    """
    memory_bank.add_memory(key, content, metadata)
    return f"Remembered under '{key}': {content[:100]}..."

def recall(key: str, limit: int = 5) -> str:
    """Recall stored memories for a category.
    
    Args:
        key: Memory category to retrieve
        limit: Number of recent memories to return
    
    Returns:
        Formatted memory list
    """
    return memory_bank.recall(key, limit)

def search_memory(query: str) -> str:
    """Search memories by keyword.
    
    Args:
        query: Search term
    
    Returns:
        Matching memories
    """
    results = memory_bank.search(query)
    if not results:
        return f"No memories match '{query}'"
    
    output = f"Found {len(results)} matches:\n"
    for r in results[:10]:
        output += f"[{r['key']}] {r['content'][:100]}\n"
    return output

def clear_memory(key: str = None) -> str:
    """Clear memories.
    
    Args:
        key: Optional key to clear; if None, clears all
    
    Returns:
        Confirmation
    """
    memory_bank.clear(key)
    return f"Cleared memory for: {key if key else 'ALL'}"