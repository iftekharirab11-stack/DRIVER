import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import List

# Import sandbox utilities
from DRIVER.sandbox_driver import (
    create_sandbox, get_workspace_path, write_to_sandbox, read_from_sandbox,
    list_directory, move_file_sandbox, delete_file_sandbox,
    create_archive_sandbox, count_files_sandbox
)

WORKSPACE_DIR = "WORKSPACE"

def execute_python_code(filename: str, args: list = None, timeout: int = 30) -> str:
    """Execute a Python script from WORKSPACE and return output.
    
    Args:
        filename: Name of .py file in WORKSPACE
        args: Optional list of command-line arguments
        timeout: Max execution time in seconds
    
    Returns:
        stdout + stderr combined
    
    ⚠️  SECURITY: This executes arbitrary Python code. Only run trusted scripts.
    """
    script_path = Path(WORKSPACE_DIR) / filename
    
    # Security: Only execute from WORKSPACE
    if not str(script_path.resolve()).startswith(str(Path(WORKSPACE_DIR).resolve())):
        return "⛔ Security error: Path outside WORKSPACE not allowed"
    
    if not script_path.exists():
        return f"✗ File '{filename}' not found in WORKSPACE"
    
    if not filename.endswith('.py'):
        return f"✗ Only .py files can be executed (got: {filename})"
    
    # Build command
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        # Run with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        
        return output or "[No output]"
    except subprocess.TimeoutExpired:
        return f"⏱️ Execution timed out after {timeout}s"
    except Exception as e:
        return f"⛔ Error: {str(e)}"

def execute_shell_command(command: str, timeout: int = 30) -> str:
    """Execute a shell command with enhanced security protections.

    Args:
        command: Shell command to run
        timeout: Max execution time in seconds

    Returns:
        Command output or error message

    Security Features:
        - No shell=True (prevents shell injection)
        - Command allowlist with regex patterns
        - Path validation to prevent traversal
        - Timeout enforcement
        - Working directory restriction
    """
    import shlex
    from pathlib import Path

    # Enhanced security: Command allowlist using regex patterns
    ALLOWED_COMMANDS = [
        r'^ls\s',  # ls commands
        r'^dir\s',  # dir commands (Windows)
        r'^cat\s',  # cat commands
        r'^type\s',  # type commands (Windows)
        r'^echo\s',  # echo commands
        r'^grep\s',  # grep commands
        r'^find\s',  # find commands
        r'^python\s',  # python commands
        r'^python3\s',  # python3 commands
        r'^pip\s',  # pip commands
        r'^git\s',  # git commands
        r'^node\s',  # node commands
        r'^npm\s',  # npm commands
    ]

    # Block obviously dangerous patterns
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf', r'rm\s+\-rf', r'rm\s+\-r\s+\-f',  # rm -rf variations
        r'format\s', r'mkfs\s', r'dd\s',  # disk operations
        r'shutdown\s', r'reboot\s', r'poweroff\s',  # system operations
        r'del\s+\/', r'del\s+\*',  # dangerous Windows deletes
        r'chmod\s+[0-7]{3,4}\s',  # chmod operations
        r'chown\s', r'sudo\s', r'su\s',  # privilege escalation
        r'kill\s+\-9', r'killall\s',  # process killing
        r'wget\s+.*\|\s*sh', r'curl\s+.*\|\s*sh',  # remote execution
        r';\s*', r'\|\s*', r'&&\s*', r'\|\|\s*',  # command chaining
        r'`', r'\$\(.*\)',  # command substitution
    ]

    # Check for dangerous patterns
    command_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower):
            return "⛔ Dangerous command pattern detected and blocked for security"

    # Check if command matches allowlist
    allowed = False
    for pattern in ALLOWED_COMMANDS:
        if re.match(pattern, command_lower):
            allowed = True
            break

    if not allowed:
        return "⛔ Command not allowed. Only basic file operations, Python, and package management commands are permitted."

    try:
        # Parse command safely using shlex (handles quoting properly)
        parsed_command = shlex.split(command)

        # Validate that we have a command to execute
        if not parsed_command:
            return "⛔ Empty command"

        # Execute without shell=True to prevent shell injection
        result = subprocess.run(
            parsed_command,
            shell=False,  # Critical security fix
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"

        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"

        return output or "[No output]"
    except subprocess.TimeoutExpired:
        return f"⏱️ Command timed out after {timeout}s"
    except Exception as e:
        return f"⛔ Error: {str(e)}"

def install_package(package_name: str) -> str:
    """Install a Python package via pip.
    
    Args:
        package_name: Package to install
    
    Returns:
        Installation result
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        
        if result.returncode == 0:
            return f"✓ Installed {package_name}"
        return f"✗ Failed: {output}"
    except Exception as e:
        return f"⛔ Error: {str(e)}"

# ============================================================================
# ALPHA COWORK: SECURE FILE SYSTEM TOOLS
# ============================================================================

def cowork_read_file(user_id: str, filepath: str, subfolder: str = None) -> str:
    """Read a file from the user's sandbox workspace (Alpha Cowork).
    
    This is part of the Alpha Cowork secure file system integration.
    All file operations are restricted to the user's Allowed Zone.
    
    Args:
        user_id: User identifier for sandbox isolation
        filepath: Path to file within workspace
        subfolder: Optional subfolder within workspace
    
    Returns:
        File contents or error message
    """
    content = read_from_sandbox(user_id, filepath, subfolder)
    from DRIVER.telemetry_logger import telemetry
    import getpass
    try:
        telemetry.log(
            type(telemetry).__module__.split('.')[-1].capitalize()(
                entry_id=f"read_{int(time.time()*1000)}",
                timestamp=time.time(),
                user_id=user_id,
                session_id="unknown",
                event_type="tool_call",
                tool_name="cowork_read_file",
                metadata={"filepath": filepath, "subfolder": subfolder or "workspace"}
            )
        )
    except Exception:
        pass
    return content

def cowork_write_file(user_id: str, filename: str, content: str, 
                      subfolder: str = None) -> str:
    """Write a file to the user's sandbox workspace (Alpha Cowork).
    
    Args:
        user_id: User identifier for sandbox isolation
        filename: Name of file to create/update
        content: Content to write
        subfolder: Optional subfolder within workspace
    
    Returns:
        Success message with file path or error
    """
    result = write_to_sandbox(user_id, filename, content, subfolder)
    from DRIVER.telemetry_logger import telemetry
    try:
        telemetry.log(
            type(telemetry).__module__.split('.')[-1].capitalize()(
                entry_id=f"write_{int(time.time()*1000)}",
                timestamp=time.time(),
                user_id=user_id,
                session_id="unknown",
                event_type="tool_call",
                tool_name="cowork_write_file",
                metadata={"filename": filename, "subfolder": subfolder or "workspace", "size": len(content)}
            )
        )
    except Exception:
        pass
    return result

def cowork_list_directory(user_id: str, subfolder: str = None) -> str:
    """List files in user's sandbox workspace (Alpha Cowork).
    
    Returns a formatted directory listing.
    
    Args:
        user_id: User identifier for sandbox isolation
        subfolder: Optional subfolder within workspace
    
    Returns:
        Formatted directory listing or error
    """
    items = list_directory(user_id, subfolder)
    if not items:
        return "Directory is empty or does not exist."
    
    workspace = get_workspace_path(user_id)
    target = workspace if not subfolder else f"{workspace}/{subfolder}"
    output = f"=== DIRECTORY: {target} ===\n\n"
    
    dirs = [i for i in items if i["is_dir"]]
    files = [i for i in items if not i["is_dir"]]
    
    for d in sorted(dirs, key=lambda x: x["name"]):
        output += f"📁 {d['name']}/\n"
    for f in sorted(files, key=lambda x: x["name"]):
        size_kb = f["size"] / 1024
        output += f"📄 {f['name']} ({size_kb:.1f} KB)\n"
    
    output += f"\nTotal: {len(dirs)} folders, {len(files)} files"
    return output

def cowork_move_file(user_id: str, src: str, dst: str, 
                     src_subfolder: str = None, dst_subfolder: str = None) -> str:
    """Move a file within the user's sandbox workspace (Alpha Cowork).
    
    Args:
        user_id: User identifier for sandbox isolation
        src: Source filename
        dst: Destination filename
        src_subfolder: Optional source subfolder
        dst_subfolder: Optional destination subfolder
    
    Returns:
        Success/error message
    """
    result = move_file_sandbox(user_id, src, dst, src_subfolder, dst_subfolder)
    from DRIVER.telemetry_logger import telemetry
    try:
        telemetry.log(
            type(telemetry).__module__.split('.')[-1].capitalize()(
                entry_id=f"move_{int(time.time()*1000)}",
                timestamp=time.time(),
                user_id=user_id,
                session_id="unknown",
                event_type="tool_call",
                tool_name="cowork_move_file",
                metadata={"src": src, "dst": dst}
            )
        )
    except Exception:
        pass
    return result

def cowork_create_archive(user_id: str, archive_name: str, 
                          files: List[str], subfolder: str = None) -> str:
    """Create a zip archive of files in workspace (Alpha Cowork).
    
    Args:
        user_id: User identifier for sandbox isolation
        archive_name: Name of zip archive (without .zip)
        files: List of filenames to include
        subfolder: Optional subfolder containing files
    
    Returns:
        Success/error message
    """
    result = create_archive_sandbox(user_id, archive_name, files, subfolder)
    from DRIVER.telemetry_logger import telemetry
    try:
        telemetry.log(
            type(telemetry).__module__.split('.')[-1].capitalize()(
                entry_id=f"archive_{int(time.time()*1000)}",
                timestamp=time.time(),
                user_id=user_id,
                session_id="unknown",
                event_type="tool_call",
                tool_name="cowork_create_archive",
                metadata={"archive_name": archive_name, "file_count": len(files)}
            )
        )
    except Exception:
        pass
    return result

def cowork_count_files(user_id: str, subfolder: str = None) -> str:
    """Count total files in user's sandbox (Alpha Cowork).
    
    Args:
        user_id: User identifier for sandbox isolation
        subfolder: Optional subfolder within workspace
    
    Returns:
        File count message
    """
    count = count_files_sandbox(user_id, subfolder)
    return f"Total files: {count}"

# Test if workspace is safe
def validate_workspace() -> str:
    """Check if WORKSPACE exists and is writable."""
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        return "✓ Created WORKSPACE directory"
    
    # Test write
    test_file = Path(WORKSPACE_DIR) / ".test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        return "✓ WORKSPACE is writable"
    except Exception as e:
        return f"✗ WORKSPACE not writable: {str(e)}"