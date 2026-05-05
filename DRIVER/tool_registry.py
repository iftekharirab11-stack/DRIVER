# [GOAL] Allow anyone to add "Skills" by just dropping a file in /skills
# [CONSTRAINTS] Must be plug-and-play.

import importlib
import inspect
import os
from pathlib import Path
from typing import Callable, List, Dict, Any

class ToolRegistry:
    """Auto-discovery registry for tools/skills."""
    
    def __init__(self, skills_folder: str = "DRIVER/skills"):
        self.tools: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.skills_folder = Path(skills_folder)
        self._cowork_tools_registered = False
        
    def register(self, name: str = None, description: str = None):
        """Decorator to register a tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            self.metadata[tool_name] = {
                "name": tool_name,
                "description": description or func.__doc__ or "",
                "function": func,
                "signature": str(inspect.signature(func))
            }
            return func
        return decorator
    
    def register_cowork_tools(self):
        """Register all Alpha Cowork file system tools.
        
        These tools require a user_id parameter for sandbox isolation.
        They are wrapped to work with LangChain Tool format.
        """
        if self._cowork_tools_registered:
            return
        
        # Import cowork tools from executor_driver
        from DRIVER.executor_driver import (
            cowork_read_file,
            cowork_write_file,
            cowork_list_directory,
            cowork_move_file,
            cowork_create_archive,
            cowork_count_files,
        )
        from DRIVER.executor_driver import execute_python_code, execute_shell_command, install_package, validate_workspace
        
        # Register each tool
        cowork_tools = [
            ("cowork_read_file", cowork_read_file, "Read a file from the sandbox workspace. Requires user_id."),
            ("cowork_write_file", cowork_write_file, "Write a file to the sandbox workspace. Requires user_id."),
            ("cowork_list_directory", cowork_list_directory, "List directory contents in sandbox. Requires user_id."),
            ("cowork_move_file", cowork_move_file, "Move a file within sandbox. Requires user_id."),
            ("cowork_create_archive", cowork_create_archive, "Create a zip archive of files. Requires user_id."),
            ("cowork_count_files", cowork_count_files, "Count files in sandbox. Requires user_id."),
            ("execute_python_code", execute_python_code, "Execute a Python script from WORKSPACE."),
            ("execute_shell_command", execute_shell_command, "Execute a safe shell command."),
            ("install_package", install_package, "Install a Python package via pip."),
            ("validate_workspace", validate_workspace, "Validate workspace is writable."),
        ]
        
        for name, func, desc in cowork_tools:
            self.register(name=name, description=desc)(func)
        
        self._cowork_tools_registered = True
    
    def discover(self):
        """Auto-discover and load all tools from skills folder."""
        if not self.skills_folder.exists():
            self.skills_folder.mkdir(parents=True, exist_ok=True)
            return
        
        # Load all .py files in skills folder (skip __init__.py)
        for file in self.skills_folder.glob("*.py"):
            if file.name.startswith("__"):
                continue
            
            module_name = f"DRIVER.skills.{file.stem}"
            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"Failed to load skill {file.name}: {e}")
    
    def get_tool(self, name: str) -> Callable:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with metadata."""
        return list(self.metadata.values())
    
    def get_tools_as_langchain(self):
        """Export tools in LangChain format."""
        from langchain_core.tools import StructuredTool
        
        langchain_tools = []
        for name, func in self.tools.items():
            try:
                langchain_tools.append(StructuredTool.from_function(func))
            except Exception as e:
                print(f"Failed to wrap tool '{name}' for LangChain: {e}")
        return langchain_tools


# Global registry instance
registry = ToolRegistry()
registry.discover()

# Example built-in tools
@registry.register(name="system_status", description="Get system status and health")
def system_status() -> str:
    """Check if all systems are operational."""
    return "All systems operational. Chainlit running on port 8000."

@registry.register(name="list_tools", description="List all available tools/skills")
def list_all_tools() -> str:
    """Show every tool the AI can use right now."""
    tools = registry.list_tools()
    output = f"=== AVAILABLE TOOLS ({len(tools)}) ===\n"
    for t in tools:
        output += f"\n🔧 {t['name']}\n   {t['description']}\n"
    return output