# [GOAL] Secure Execution Environment
# [CONTEXT] Every user gets a private /sandbox/ folder.
# SECURITY: Complete isolation per user; no cross-user contamination.

import os
from typing import Optional
from pathlib import Path

# Base storage root
STORAGE_ROOT = Path("storage")
STORAGE_ROOT.mkdir(exist_ok=True)

def create_sandbox(user_id: str) -> str:
    """Create a private sandbox directory for a user.
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        Absolute path to user's sandbox
    """
    sandbox_path = STORAGE_ROOT / "sandboxes" / user_id
    
    # Create nested directories
    sandbox_path.mkdir(parents=True, exist_ok=True)
    
    # Standard subfolders
    (sandbox_path / "workspace").mkdir(exist_ok=True)
    (sandbox_path / "temp").mkdir(exist_ok=True)
    (sandbox_path / "outputs").mkdir(exist_ok=True)
    
    return str(sandbox_path.resolve())

def get_sandbox_path(user_id: str) -> Optional[str]:
    """Get existing sandbox path for a user."""
    sandbox_path = STORAGE_ROOT / "sandboxes" / user_id
    if sandbox_path.exists():
        return str(sandbox_path.resolve())
    return None

def write_to_sandbox(user_id: str, filename: str, content: str, 
                     subfolder: str = "workspace") -> str:
    """Write a file to user's sandbox.
    
    Args:
        user_id: User identifier
        filename: Name of file
        content: Content to write
        subfolder: Optional subfolder within sandbox
    
    Returns:
        Full file path or error message
    """
    sandbox = get_sandbox_path(user_id) or create_sandbox(user_id)
    target_dir = Path(sandbox) / subfolder
    target_dir.mkdir(exist_ok=True)
    
    filepath = target_dir / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(filepath)
    except Exception as e:
        return f"Error: {str(e)}"

def read_from_sandbox(user_id: str, filename: str, 
                      subfolder: str = "workspace") -> str:
    """Read a file from user's sandbox."""
    sandbox = get_sandbox_path(user_id)
    if not sandbox:
        return "Error: Sandbox not created for this user"
    
    filepath = Path(sandbox) / subfolder / filename
    
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return f"Error: File '{filename}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

def list_sandbox_contents(user_id: str, subfolder: str = None) -> str:
    """List files in user's sandbox."""
    sandbox = get_sandbox_path(user_id)
    if not sandbox:
        return "Error: Sandbox not created"
    
    base = Path(sandbox)
    if subfolder:
        base = base / subfolder
    
    if not base.exists():
        return f"Error: Path does not exist: {subfolder}"
    
    items = list(base.iterdir())
    if not items:
        return "Sandbox is empty"
    
    output = f"=== SANDBOX: {base.name} ===\n"
    for item in items:
        if item.is_dir():
            output += f"📁 {item.name}/\n"
        else:
            size = item.stat().st_size
            output += f"📄 {item.name} ({size} bytes)\n"
    return output

def delete_sandbox_file(user_id: str, filename: str, 
                        subfolder: str = "workspace") -> str:
    """Delete a file from sandbox."""
    sandbox = get_sandbox_path(user_id)
    if not sandbox:
        return "Error: Sandbox not created"
    
    filepath = Path(sandbox) / subfolder / filename
    
    try:
        if filepath.exists():
            filepath.unlink()
            return f"Deleted: {filename}"
        return f"File not found: {filename}"
    except Exception as e:
        return f"Error: {str(e)}"

def cleanup_sandbox(user_id: str, keep_files: bool = False) -> str:
    """Remove user's sandbox (for account deletion or reset).
    
    Args:
        user_id: User identifier
        keep_files: If True, archive before deletion
    
    Returns:
        Status message
    """
    sandbox = get_sandbox_path(user_id)
    if not sandbox:
        return "Sandbox did not exist"
    
    import shutil
    
    try:
        if keep_files:
            # Archive first
            archive_name = f"archive_{user_id}_{int(time.time())}"
            archive_path = STORAGE_ROOT / "archives" / archive_name
            shutil.move(sandbox, archive_path)
            return f"Archived to {archive_path}"
        else:
            shutil.rmtree(sandbox)
            return f"Deleted sandbox for {user_id}"
    except Exception as e:
        return f"Error during cleanup: {str(e)}"

# Initialize default sandbox for demo
DEFAULT_USER_ID = "demo_user"
if not get_sandbox_path(DEFAULT_USER_ID):
    create_sandbox(DEFAULT_USER_ID)