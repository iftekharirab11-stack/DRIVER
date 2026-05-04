# [GOAL] Execute code written by AI (Computer Use)
# [CONTEXT] Allows AI to run Python scripts from WORKSPACE.
# ⚠️  SECURITY: Only runs .py files from WORKSPACE directory.

import os
import subprocess
import sys
from pathlib import Path

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
    """Execute a shell command (limited to safe operations).
    
    Args:
        command: Shell command to run
        timeout: Max execution time
    
    Returns:
        Command output
    """
    # Security: Block dangerous commands
    DANGEROUS = ['rm -rf', 'format', 'mkfs', 'dd', 'shutdown', 'reboot', 'del /']
    if any(d in command.lower() for d in DANGEROUS):
        return "⛔ Dangerous command blocked for security"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        
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