# DRIVER/cowork_console.py
# [GOAL] Sidebar Live Operations tab for Alpha Cowork
# [CONTEXT] Real-time tracking of background tasks, file operations, and progress

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from DRIVER.task_manager import task_queue
from DRIVER.background_worker import bg_agent
from DRIVER.telemetry_logger import telemetry


class CoworkConsole:
    """Manages the Live Operations sidebar UI state for Alpha Cowork.
    
    Provides real-time tracking of:
    - Background file operations (sorting, archiving, moving)
    - Parallel task execution status
    - Progress bars for long-running jobs
    - Recent file system changes
    """
    
    def __init__(self):
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.completed_operations: List[Dict[str, Any]] = []
        self.max_history = 50
    
    def record_operation(self, operation_id: str, op_type: str, 
                        description: str, total_steps: int = 1,
                        metadata: Dict[str, Any] = None) -> None:
        """Record a new file operation.
        
        Args:
            operation_id: Unique operation identifier
            op_type: Type of operation (file_sort, archive, move, etc.)
            description: Human-readable description
            total_steps: Total number of steps in this operation
            metadata: Additional metadata
        """
        self.active_operations[operation_id] = {
            "id": operation_id,
            "type": op_type,
            "description": description,
            "status": "running",
            "progress": 0,
            "total_steps": total_steps,
            "current_step": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "metadata": metadata or {},
            "messages": []
        }
    
    def update_progress(self, operation_id: str, progress: int, 
                       message: str = None) -> None:
        """Update progress of an operation.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
            message: Status message
        """
        if operation_id in self.active_operations:
            self.active_operations[operation_id]["progress"] = progress
            if message:
                self.active_operations[operation_id]["messages"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                })
    
    def complete_operation(self, operation_id: str, result: Any = None) -> None:
        """Mark operation as completed.
        
        Args:
            operation_id: Operation ID
            result: Result data
        """
        if operation_id in self.active_operations:
            op = self.active_operations[operation_id]
            op["status"] = "completed"
            op["progress"] = 100
            op["completed_at"] = datetime.now().isoformat()
            op["result"] = result
            
            self.completed_operations.insert(0, op)
            del self.active_operations[operation_id]
            
            # Trim history
            if len(self.completed_operations) > self.max_history:
                self.completed_operations = self.completed_operations[:self.max_history]
    
    def fail_operation(self, operation_id: str, error: str) -> None:
        """Mark operation as failed.
        
        Args:
            operation_id: Operation ID
            error: Error message
        """
        if operation_id in self.active_operations:
            op = self.active_operations[operation_id]
            op["status"] = "failed"
            op["error"] = error
            op["completed_at"] = datetime.now().isoformat()
            
            self.completed_operations.insert(0, op)
            del self.active_operations[operation_id]
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific operation.
        
        Args:
            operation_id: Operation ID
        
        Returns:
            Operation status or None
        """
        return self.active_operations.get(operation_id)
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get all active operations.
        
        Returns:
            List of active operation dicts
        """
        return list(self.active_operations.values())
    
    def generate_sidebar_content(self, user_id: str) -> str:
        """Generate formatted sidebar content for Chainlit.
        
        Includes task queue status, background worker status, and
        active file operations.
        
        Args:
            user_id: User identifier
        
        Returns:
            Formatted markdown string
        """
        output = "## 🔧 Alpha Cowork - Live Operations\n\n"
        
        # Task Queue Status
        queue_status = task_queue.get_status()
        output += "### 📊 Task Queue\n"
        output += f"- **Queued:** {queue_status.get('queued', 0)}\n"
        output += f"- **Running:** {queue_status.get('running', 0)}\n"
        output += f"- **Completed:** {queue_status.get('completed', 0)}\n"
        output += f"- **Failed:** {queue_status.get('failed', 0)}\n\n"
        
        # Background Agent Status
        agent_status = bg_agent.get_job_status()
        output += "### 🔄 Background Jobs\n"
        output += f"- **Active:** {agent_status.get('active', 0)}\n"
        output += f"- **Queued:** {agent_status.get('queued', 0)}\n"
        
        active_jobs = agent_status.get('active_jobs', [])
        if active_jobs:
            output += "\n#### Running Tasks\n"
            for job in active_jobs:
                progress = job.get('progress', 0)
                bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
                output += f"\n- **{job['name']}** [{bar}] {progress}%\n"
        else:
            output += "\n*No active background jobs*\n"
        
        # File Operations
        output += "\n### 📁 File Operations\n"
        active_file_ops = self.get_active_operations()
        if active_file_ops:
            for op in active_file_ops:
                bar = "█" * (op['progress'] // 10) + "░" * (10 - op['progress'] // 10)
                output += f"\n- **{op['type']}** [{bar}] {op['progress']}%\n"
                output += f"  {op['description']}\n"
        else:
            output += "*No active file operations*\n"
        
        # Workspace stats
        try:
            from DRIVER.sandbox_driver import count_files_sandbox
            file_count = count_files_sandbox(user_id)
            output += f"\n### 📈 Workspace Stats\n"
            output += f"- **Total files:** {file_count}\n"
            
            from DRIVER.task_manager import task_queue as tq
            output += f"- **Active workers:** {len(tq.workers)}\n"
        except Exception:
            pass
        
        # Quick Actions
        output += "\n### ⚡ Quick Actions\n"
        output += "- **Triage Folder:** `/triage` - Organize workspace files\n"
        output += "- **Extract Data:** `/extract` - Process images/PDFs to Excel\n"
        output += "- **Teaching Mode:** `/teach` - Record session as reusable skill\n"
        
        return output
    
    async def process_file_sort(self, user_id: str, folder: str) -> Dict[str, Any]:
        """Process file sorting operation with progress tracking.
        
        Args:
            user_id: User identifier
            folder: Folder to sort
        
        Returns:
            Operation result
        """
        op_id = f"filesort_{datetime.now().timestamp()}"
        self.record_operation(
            op_id, "file_sort",
            f"Sorting files in '{folder}'",
            total_steps=5
        )
        
        try:
            from DRIVER.sandbox_driver import list_directory, move_file_sandbox
            
            self.update_progress(op_id, 10, "Listing files...")
            items = list_directory(user_id, folder)
            
            if not isinstance(items, list):
                self.fail_operation(op_id, "Could not list directory")
                return {"error": "Could not list directory"}
            
            docs = [i for i in items if isinstance(i, dict) and not i.get('is_dir')]
            self.update_progress(op_id, 30, f"Found {len(docs)} files")
            
            # Group by extension
            by_ext = {}
            for doc in docs:
                ext = doc['name'].split('.')[-1].lower()
                if ext not in by_ext:
                    by_ext[ext] = []
                by_ext[ext].append(doc['name'])
            
            self.update_progress(op_id, 50, f"Organizing into {len(by_ext)} categories")
            
            # Create subfolders and move files
            moved = 0
            total = len(docs)
            for ext, files in by_ext.items():
                if len(files) > 1:
                    folder_name = f"{ext}_files"
                    for i, fname in enumerate(files):
                        move_file_sandbox(user_id, fname, fname, folder, folder_name)
                        moved += 1
                        prog = 50 + int((moved / total) * 40)
                        self.update_progress(op_id, prog, 
                                           f"Moving {fname} to {folder_name}/")
            
            self.update_progress(op_id, 100, "File sorting complete!")
            self.complete_operation(op_id, {
                "files_processed": total,
                "categories": len(by_ext),
                "files_moved": moved
            })
            
            return {
                "status": "success",
                "files_processed": total,
                "categories": len(by_ext),
                "message": f"Sorted {total} files into {len(by_ext)} categories"
            }
        except Exception as e:
            self.fail_operation(op_id, str(e))
            return {"status": "error", "message": str(e)}
    
    async def process_doc_summary(self, user_id: str, folder: str) -> Dict[str, Any]:
        """Process document summarization with progress tracking.
        
        Args:
            user_id: User identifier
            folder: Folder containing documents
        
        Returns:
            Operation result
        """
        op_id = f"docsum_{datetime.now().timestamp()}"
        self.record_operation(
            op_id, "doc_summary",
            f"Summarizing documents in '{folder}'",
            total_steps=4
        )
        
        try:
            from DRIVER.sandbox_driver import list_directory, read_from_sandbox, write_to_sandbox
            
            self.update_progress(op_id, 10, "Listing documents...")
            items = list_directory(user_id, folder)
            
            if not isinstance(items, list):
                self.fail_operation(op_id, "Could not list directory")
                return {"error": "Could not list directory"}
            
            docs = [i for i in items if isinstance(i, dict) and not i.get('is_dir')]
            self.update_progress(op_id, 30, f"Found {len(docs)} documents")
            
            summaries = []
            for idx, item in enumerate(docs):
                content = read_from_sandbox(user_id, item['name'], folder)
                word_count = len(str(content).split())
                summaries.append(f"{item['name']}: {word_count} words")
                prog = 30 + int(((idx + 1) / len(docs)) * 50)
                self.update_progress(op_id, prog, 
                                   f"Processing {item['name']}...")
            
            summary_text = "\n".join(summaries)
            write_to_sandbox(user_id, "summary.txt", summary_text, folder)
            
            self.update_progress(op_id, 100, "Summary complete!")
            self.complete_operation(op_id, {
                "documents_processed": len(docs),
                "output_file": "summary.txt"
            })
            
            return {
                "status": "success",
                "documents_processed": len(docs),
                "message": "Summary saved to summary.txt"
            }
        except Exception as e:
            self.fail_operation(op_id, str(e))
            return {"status": "error", "message": str(e)}


# Global singleton
cowork_console = CoworkConsole()