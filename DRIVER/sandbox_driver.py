# [GOAL] Secure Execution Environment
# [CONTEXT] Every user gets a private /sandbox/ folder.
# SECURITY: Complete isolation per user; no cross-user contamination.

import os
import zipfile
import io
from typing import Optional, List, Dict, Any
from pathlib import Path

# Base storage root
STORAGE_ROOT = Path("storage")
STORAGE_ROOT.mkdir(exist_ok=True)

# Allowed zone - loaded from .env
import dotenv
dotenv.load_dotenv()
SANDBOX_ROOT = os.getenv("SANDBOX_ROOT", "WORKSPACE")
MAX_FILES_PER_OPERATION = int(os.getenv("MAX_FILES_PER_OPERATION", "100"))
HITL_THRESHOLD_DELETE = int(os.getenv("HITL_THRESHOLD_DELETE", "10"))
HITL_THRESHOLD_MOVE = int(os.getenv("HITL_THRESHOLD_MOVE", "10"))

def create_sandbox(user_id: str) -> str:
    """Create a private sandbox directory for a user with permanent workspace.
    
    Creates nested structure:
    - WORKSPACE/          (permanent file operations zone)
    - temp/               (temporary files)
    - outputs/            (generated results)
    """
    sandbox_path = STORAGE_ROOT / "sandboxes" / user_id
    
    # Create nested directories
    sandbox_path.mkdir(parents=True, exist_ok=True)
    
    # Permanent workspace (Allowed Zone for file ops)
    workspace_path = sandbox_path / SANDBOX_ROOT
    workspace_path.mkdir(exist_ok=True)
    
    # Standard subfolders
    for subfolder in ["temp", "outputs", "archive"]:
        (sandbox_path / subfolder).mkdir(exist_ok=True)
    
    return str(sandbox_path.resolve())

def get_sandbox_path(user_id: str) -> Optional[str]:
    """Get existing sandbox path for a user."""
    sandbox_path = STORAGE_ROOT / "sandboxes" / user_id
    if sandbox_path.exists():
        return str(sandbox_path.resolve())
    return None

def get_workspace_path(user_id: str) -> str:
    """Get the permanent workspace (Allowed Zone) path for a user.
    
    This is the ONLY directory where the agent can perform file operations.
    """
    sandbox = get_sandbox_path(user_id) or create_sandbox(user_id)
    workspace = Path(sandbox) / SANDBOX_ROOT
    workspace.mkdir(exist_ok=True)
    return str(workspace)

def _enforce_allowed_zone(user_id: str, filepath: Path) -> bool:
    """Verify filepath is within the user's Allowed Zone (workspace).
    
    Returns True if path is safe, False otherwise.
    """
    workspace = Path(get_workspace_path(user_id)).resolve()
    try:
        target = filepath.resolve()
        # Must be within workspace
        return str(target).startswith(str(workspace))
    except Exception:
        return False

def write_to_sandbox(user_id: str, filename: str, content: str, 
                     subfolder: str = None) -> str:
    """Write a file to user's sandbox workspace.
    
    Args:
        user_id: User identifier
        filename: Name of file
        content: Content to write
        subfolder: Optional subfolder within workspace (defaults to workspace root)
    
    Returns:
        Full file path or error message
    """
    workspace = Path(get_workspace_path(user_id))
    
    target_dir = workspace if not subfolder else (workspace / subfolder)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = target_dir / filename
    
    # Security check
    if not _enforce_allowed_zone(user_id, filepath):
        return f"⛔ Security error: Path outside Allowed Zone not allowed: {filepath}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(filepath)
    except Exception as e:
        return f"Error: {str(e)}"

def read_from_sandbox(user_id: str, filename: str, 
                      subfolder: str = None) -> str:
    """Read a file from user's sandbox."""
    workspace = Path(get_workspace_path(user_id))
    
    if subfolder:
        filepath = workspace / subfolder / filename
    else:
        filepath = workspace / filename
    
    # Security check
    if not _enforce_allowed_zone(user_id, filepath):
        return f"⛔ Security error: Path outside Allowed Zone"
    
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        # Try as relative path within workspace
        alt = workspace / filename
        if alt.exists():
            with open(alt, 'r', encoding='utf-8') as f:
                return f.read()
        return f"Error: File '{filename}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

def list_directory(user_id: str, subfolder: str = None) -> List[Dict[str, Any]]:
    """List files in user's sandbox directory.
    
    Returns structured list of file info dicts.
    """
    workspace = Path(get_workspace_path(user_id))
    
    target_dir = workspace if not subfolder else (workspace / subfolder)
    
    # Security check
    if not _enforce_allowed_zone(user_id, target_dir):
        return []
    
    if not target_dir.exists():
        return []
    
    items = []
    for item in sorted(target_dir.iterdir()):
        try:
            stat = item.stat()
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime
            })
        except Exception:
            pass
    
    return items

def move_file_sandbox(user_id: str, src: str, dst: str, 
                      src_subfolder: str = None, dst_subfolder: str = None) -> str:
    """Move a file within sandbox workspace.
    
    Args:
        user_id: User identifier
        src: Source filename
        dst: Destination filename
        src_subfolder: Optional source subfolder
        dst_subfolder: Optional destination subfolder
    
    Returns:
        Success/error message
    """
    workspace = Path(get_workspace_path(user_id))
    
    src_path = workspace / src if not src_subfolder else (workspace / src_subfolder / src)
    dst_path = workspace / dst if not dst_subfolder else (workspace / dst_subfolder / dst)
    
    # Security check
    if not _enforce_allowed_zone(user_id, src_path):
        return f"⛔ Security error: Source outside Allowed Zone"
    if not _enforce_allowed_zone(user_id, dst_path):
        return f"⛔ Security error: Destination outside Allowed Zone"
    
    try:
        if not src_path.exists():
            return f"Error: Source file '{src}' not found"
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)
        return f"✓ Moved '{src}' → '{dst}'"
    except Exception as e:
        return f"Error: {str(e)}"

def delete_file_sandbox(user_id: str, filename: str, 
                        subfolder: str = None) -> str:
    """Delete a file from sandbox workspace."""
    workspace = Path(get_workspace_path(user_id))
    
    filepath = workspace / filename if not subfolder else (workspace / subfolder / filename)
    
    # Security check
    if not _enforce_allowed_zone(user_id, filepath):
        return f"⛔ Security error: Path outside Allowed Zone"
    
    try:
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return f"✓ Deleted '{filename}'"
        return f"Error: File '{filename}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

def create_archive_sandbox(user_id: str, archive_name: str, 
                           files: List[str], subfolder: str = None) -> str:
    """Create a zip archive of files in workspace.
    
    Args:
        user_id: User identifier
        archive_name: Name of zip archive (without .zip)
        files: List of filenames to include
        subfolder: Optional subfolder containing files
    
    Returns:
        Success/error message
    """
    workspace = Path(get_workspace_path(user_id))
    
    base_dir = workspace if not subfolder else (workspace / subfolder)
    archive_path = base_dir / f"{archive_name}.zip"
    
    # Security check
    if not _enforce_allowed_zone(user_id, archive_path):
        return f"⛔ Security error: Path outside Allowed Zone"
    
    if len(files) > MAX_FILES_PER_OPERATION:
        return f"Error: Too many files ({len(files)} > {MAX_FILES_PER_OPERATION})"
    
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fname in files:
                fpath = base_dir / fname
                if fpath.exists() and fpath.is_file():
                    # Check security
                    if _enforce_allowed_zone(user_id, fpath):
                        zf.write(fpath, fname)
        
        if archive_path.exists():
            return f"✓ Created archive '{archive_name}.zip' with {len(files)} files"
        return "Error: Archive creation failed"
    except Exception as e:
        return f"Error: {str(e)}"

def count_files_sandbox(user_id: str, subfolder: str = None) -> int:
    """Count total files in sandbox directory."""
    workspace = Path(get_workspace_path(user_id))
    target = workspace if not subfolder else (workspace / subfolder)
    
    if not target.exists():
        return 0
    
    return sum(1 for p in target.rglob("*") if p.is_file())

def cleanup_sandbox(user_id: str, keep_files: bool = False) -> str:
    """Remove user's sandbox (for account deletion or reset).
    
    Args:
        user_id: User identifier
        keep_files: If True, archive before deletion
    
    Returns:
        Status message
    """
    import shutil
    
    sandbox = get_sandbox_path(user_id)
    if not sandbox:
        return "Sandbox did not exist"
    
    try:
        if keep_files:
            import time
            archive_name = f"archive_{user_id}_{int(time.time())}"
            archive_path = STORAGE_ROOT / "archives" / archive_name
            archive_path.parent.mkdir(parents=True, exist_ok=True)
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