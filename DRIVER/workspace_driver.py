# [GOAL] Enable AI to Write, Edit, and Read files locally
# [CONTEXT] Works like Claude Desktop "Co-work" - AI manages its own files.

import os

WORKSPACE_DIR = "WORKSPACE"

if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

def write_to_workspace(filename: str, content: str, overwrite: bool = True) -> str:
    """Allows the AI to save its research or code.
    
    Args:
        filename: Name of file (with extension)
        content: Content to write
        overwrite: If False, won't overwrite existing file
    
    Returns:
        Confirmation message with path
    """
    path = os.path.join(WORKSPACE_DIR, filename)
    
    if not overwrite and os.path.exists(path):
        return f"File {filename} exists. Use overwrite=True to replace."
    
    os.makedirs(os.path.dirname(path) or WORKSPACE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✓ Saved to {path} ({len(content)} chars)"

def read_from_workspace(filename: str) -> str:
    """Allows the AI to retrieve previously saved data.
    
    Args:
        filename: Name of file to read
    
    Returns:
        File contents or error message
    """
    path = os.path.join(WORKSPACE_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"=== {filename} ===\n{content}"
    return f"✗ File '{filename}' not found in WORKSPACE."

def list_workspace_files() -> str:
    """Gives the AI a 'Memory' of what it has already done.
    
    Returns:
        Formatted list of files with sizes
    """
    files = os.listdir(WORKSPACE_DIR)
    if not files:
        return "Workspace is empty."
    
    output = f"=== WORKSPACE FILES ({len(files)}) ===\n"
    for f in sorted(files):
        path = os.path.join(WORKSPACE_DIR, f)
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)
        output += f"📄 {f} ({size} bytes, modified {os.path.basename(path)})\n"
    return output

def append_to_workspace(filename: str, content: str) -> str:
    """Append content to an existing file.
    
    Args:
        filename: Name of file
        content: Content to append
    
    Returns:
        Confirmation message
    """
    path = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(path):
        return f"File {filename} not found. Use write_to_workspace() first."
    
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + content)
    return f"✓ Appended to {path}"

def delete_from_workspace(filename: str) -> str:
    """Delete a file from workspace.
    
    Args:
        filename: Name of file to delete
    
    Returns:
        Confirmation or error
    """
    path = os.path.join(WORKSPACE_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return f"✓ Deleted {filename}"
    return f"✗ File '{filename}' not found"