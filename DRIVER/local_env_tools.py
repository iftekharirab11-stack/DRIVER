import os
from typing import List, Dict, Any
from pathlib import Path

# [CONTEXT] Safe file system operations with sandboxing
SAFE_PATHS = [
    os.getcwd(),  # Current workspace
    os.path.expanduser("~"),  # User home
    str(Path.home() / "Documents"),
    str(Path.home() / "Desktop"),
]

def _is_safe_path(path: str) -> bool:
    """Check if path is within allowed directories"""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(safe) for safe in SAFE_PATHS)

# [GOAL] Local environment tools
def list_directory(path: str = ".") -> str:
    """List files and directories in a path.
    
    Args:
        path: Relative or absolute path (default: current directory)
    
    Returns:
        Formatted directory listing
    """
    if not _is_safe_path(path):
        return "Error: Access to this path is restricted for security."
    
    try:
        items = os.listdir(path)
        output = f"=== CONTENTS OF {os.path.abspath(path)} ===\n"
        for item in sorted(items):
            full = os.path.join(path, item)
            if os.path.isdir(full):
                output += f"📁 {item}/\n"
            else:
                size = os.path.getsize(full)
                output += f"📄 {item} ({size} bytes)\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(filepath: str) -> str:
    """Read contents of a file.
    
    Args:
        filepath: Path to the file
    
    Returns:
        File contents as string
    """
    if not _is_safe_path(filepath):
        return "Error: Access to this path is restricted."
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"=== {filepath} ===\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filepath: str, content: str, overwrite: bool = True) -> str:
    """Write content to a file.
    
    Args:
        filepath: Where to write
        content: Content to write
        overwrite: If False, won't overwrite existing file
    
    Returns:
        Confirmation message
    """
    if not _is_safe_path(filepath):
        return "Error: Access to this path is restricted."
    
    if not overwrite and os.path.exists(filepath):
        return "Error: File exists and overwrite=False"
    
    try:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Written to {filepath} ({len(content)} chars)"
    except Exception as e:
        return f"Error: {str(e)}"

def create_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path: Directory path to create
    
    Returns:
        Confirmation message
    """
    if not _is_safe_path(path):
        return "Error: Access to this path is restricted."
    
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created directory: {path}"
    except Exception as e:
        return f"Error: {str(e)}"

def delete_path(path: str) -> str:
    """Delete a file or directory (use with caution).
    
    Args:
        path: Path to delete
    
    Returns:
        Confirmation message
    """
    if not _is_safe_path(path):
        return "Error: Access to this path is restricted."
    
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file: {path}"
        elif os.path.isdir(path):
            os.rmdir(path)  # Only removes empty dirs for safety
            return f"Deleted directory: {path}"
        else:
            return "Path does not exist"
    except Exception as e:
        return f"Error: {str(e)}"

def get_current_directory() -> str:
    """Get current working directory."""
    return os.getcwd()

def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a pattern.
    
    Args:
        pattern: Filename pattern (supports wildcards)
        path: Directory to search in
    
    Returns:
        List of matching files
    """
    if not _is_safe_path(path):
        return "Error: Access to this path is restricted."
    
    import glob
    try:
        matches = glob.glob(os.path.join(path, pattern), recursive=True)
        if not matches:
            return f"No files match '{pattern}' in {path}"
        output = f"=== FOUND {len(matches)} FILES ===\n"
        for m in matches[:20]:  # Limit output
            output += f"{m}\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"