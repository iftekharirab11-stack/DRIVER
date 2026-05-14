# DRIVER/agent_core.py
# [GOAL] Core execution helpers (separated to avoid circular imports)
# [ALPHA COWORK] Added Plan-Execute-Verify cycles with task_plan.json and HITL gates

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from DRIVER.telemetry_logger import telemetry

# ============================================================================
# ALPHA COWORK: PLAN-EXECUTE-VERIFY CYCLE
# ============================================================================

ALLOWED_ZONE_KEY = "WORKSPACE"
HITL_THRESHOLD_DELETE = int(os.getenv("HITL_THRESHOLD_DELETE", "10"))
HITL_THRESHOLD_MOVE = int(os.getenv("HITL_THRESHOLD_MOVE", "10"))


def create_task_plan(task_description: str, llm, tools) -> Dict[str, Any]:
    """Create a task_plan.json before any file operations (Alpha Cowork).
    
    The agent must draft a plan specifying:
    - target_files: Which files will be affected
    - operations: What will be done (read/write/move/delete/archive)
    - risk_level: Low/Medium/High based on destructive operations
    - estimated_steps: Number of operations
    - requires_hitl: Whether human confirmation is needed
    
    Args:
        task_description: User's task request
        llm: Language model to use for planning
        tools: Available tools
    
    Returns:
        Task plan dictionary
    """
    planning_prompt = SystemMessage(content=f"""
You are creating a TASK PLAN before executing: {task_description}

Format your response as JSON with these keys:
- "target_files": List of files you plan to read/modify
- "operations": List of operations (read/write/move/delete/archive)
- "risk_level": "Low" | "Medium" | "High"
- "estimated_steps": Number of discrete operations
- "requires_hitl": true if deleting/moving >{HITL_THRESHOLD_DELETE} items
- "estimated_duration": "short" | "medium" | "long"

Be conservative. If uncertain, set risk_level="High" and requires_hitl=true.
""")
    
    planner = create_react_agent(
        model=llm,
        tools=tools,
        prompt=planning_prompt,
    )
    
    result = planner.invoke({"messages": [
        {"role": "user", "content": f"Create task plan: {task_description}"}
    ]})
    
    # Extract JSON from response
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = msg.content
            # Try to extract JSON
            try:
                start = content.index('{')
                end = content.rindex('}') + 1
                plan_json = content[start:end]
                plan = json.loads(plan_json)
                # Add metadata
                plan["_task_description"] = task_description
                plan["_created_at"] = datetime.now().isoformat()
                return plan
            except (ValueError, json.JSONDecodeError):
                # Return default plan
                return {
                    "target_files": [],
                    "operations": [],
                    "risk_level": "Medium",
                    "estimated_steps": 1,
                    "requires_hitl": False,
                    "estimated_duration": "short",
                    "_task_description": task_description,
                    "_created_at": datetime.now().isoformat(),
                    "_plan_parse_error": str(content[:200])
                }
    
    return {
        "target_files": [],
        "operations": [],
        "risk_level": "Medium",
        "estimated_steps": 1,
        "requires_hitl": False,
        "estimated_duration": "short",
        "_task_description": task_description,
        "_created_at": datetime.now().isoformat()
    }


def requires_hitl_approval(task_plan: Dict[str, Any], user_id: str) -> bool:
    """Check if task requires Human-in-the-Loop approval (Alpha Cowork).
    
    HITL is required when:
    - risk_level is "High"
    - deleting files
    - moving more than HITL_THRESHOLD_MOVE items
    - estimated_steps > 20
    
    Args:
        task_plan: The task plan to evaluate
        user_id: User identifier
    
    Returns:
        True if HITL approval needed
    """
    if task_plan.get("risk_level") == "High":
        return True
    
    operations = task_plan.get("operations", [])
    delete_ops = [op for op in operations if "delete" in op.lower()]
    move_ops = [op for op in operations if "move" in op.lower()]
    
    if delete_ops and len(delete_ops) >= HITL_THRESHOLD_DELETE:
        return True
    if move_ops and len(move_ops) >= HITL_THRESHOLD_MOVE:
        return True
    
    if task_plan.get("estimated_steps", 0) > 20:
        return True
    
    return task_plan.get("requires_hitl", False)


def save_task_plan(task_plan: Dict[str, Any], user_id: str) -> str:
    """Save task_plan.json to workspace (Alpha Cowork).
    
    Args:
        task_plan: The task plan to save
        user_id: User identifier
    
    Returns:
        Path to saved plan
    """
    from DRIVER.sandbox_driver import get_workspace_path
    workspace = Path(get_workspace_path(user_id))
    plan_path = workspace / "task_plan.json"
    
    with open(plan_path, 'w') as f:
        json.dump(task_plan, f, indent=2, default=str)
    
    return str(plan_path)


def verify_execution(user_id: str, task_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Verify execution results against task plan (Alpha Cowork).
    
    Args:
        user_id: User identifier
        task_plan: Original task plan
    
    Returns:
        Verification results
    """
    from DRIVER.sandbox_driver import get_workspace_path, list_directory
    
    workspace = Path(get_workspace_path(user_id))
    expected_files = task_plan.get("target_files", [])
    
    results = {
        "plan_adhered": True,
        "files_created": [],
        "files_modified": [],
        "verification_errors": []
    }
    
    # Check workspace state
    current_files = list_directory(user_id)
    current_names = [f["name"] for f in current_files if isinstance(f, dict)]
    
    for expected in expected_files:
        if isinstance(expected, dict):
            expected = expected.get("name", str(expected))
        if str(expected) in current_names or any(str(expected) in str(n) for n in current_names):
            results["files_created"].append(str(expected))
    
    return results


def log_hitl_decision(user_id: str, task_plan: Dict[str, Any], 
                      approved: bool, decision_by: str) -> None:
    """Log HITL decision to telemetry (Alpha Cowork).
    
    Args:
        user_id: User identifier
        task_plan: Task plan being approved/rejected
        approved: Whether the action was approved
        decision_by: Who made the decision
    """
    try:
        telemetry.log(
            type(telemetry).__module__.split('.')[-1].capitalize()(
                entry_id=f"hitl_{int(datetime.now().timestamp()*1000)}",
                timestamp=datetime.now().timestamp(),
                user_id=user_id,
                session_id="unknown",
                event_type="action" if approved else "error",
                tool_name="hitl_gate",
                input_data={
                    "task_description": task_plan.get("_task_description"),
                    "risk_level": task_plan.get("risk_level"),
                    "operations": task_plan.get("operations", []),
                },
                output_data={"approved": approved, "decision_by": decision_by},
                metadata={"hitl_verified": True}
            )
        )
    except Exception:
        pass


# ============================================================================
# AGENT CREATION (Original functionality + Alpha Cowork)
# ============================================================================

def create_agent_instance(llm, tools, system_prompt: str):
    """Create a LangGraph ReAct agent.
    
    Args:
        llm: Language model
        tools: List of tools
        system_prompt: System prompt for the agent
    
    Returns:
        LangGraph agent
    """
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=system_prompt),
    )


def extract_ai_response(result: dict) -> str:
    """Extract the final AI text message from an agent result.
    
    Args:
        result: Agent result dictionary
    
    Returns:
        Extracted text response
    """
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            return msg.content
    return str(messages[-1].content) if messages else "No response"


def run_simple_agent(llm, tools, system_prompt: str, user_input: str) -> str:
    """Run a single-turn ReAct agent and return the text response.
    
    Args:
        llm: Language model
        tools: List of tools
        system_prompt: System prompt
        user_input: User message
    
    Returns:
        Agent's text response
    """
    agent = create_agent_instance(llm, tools, system_prompt)
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    return extract_ai_response(result)


def run_agent_with_plan(llm, tools, system_prompt: str, user_input: str,
                       user_id: str = "demo_user",
                       require_hitl: bool = True) -> Dict[str, Any]:
    """Run agent with Plan-Execute-Verify cycle (Alpha Cowork).
    
    This function:
    1. Creates a task_plan.json before any file operations
    2. Checks HITL requirements
    3. Executes the plan if approved
    4. Verifies results
    
    Args:
        llm: Language model
        tools: List of tools
        system_prompt: System prompt
        user_input: User message
        user_id: User identifier
        require_hitl: Whether to enforce HITL gate
    
    Returns:
        Dictionary with plan, response, and verification results
    """
    # Step 1: Create task plan
    task_plan = create_task_plan(user_input, llm, tools)
    save_task_plan(task_plan, user_id)
    
    # Step 2: Check HITL gate
    needs_hitl = requires_hitl_approval(task_plan, user_id) if require_hitl else False
    
    execution_result = {
        "task_plan": task_plan,
        "hitl_required": needs_hitl,
        "hitl_approved": not needs_hitl,  # Auto-approve if HITL not required
        "response": None,
        "verification": None
    }
    
    # Step 3: Execute (only if HITL not required or would be auto-approved)
    # Note: In production, HITL would wait for user confirmation
    if not needs_hitl:
        agent_response = run_simple_agent(llm, tools, system_prompt, user_input)
        execution_result["response"] = agent_response
        
        # Step 4: Verify
        execution_result["verification"] = verify_execution(user_id, task_plan)
    else:
        execution_result["response"] = (
            f"Task requires approval before execution. "
            f"Risk level: {task_plan.get('risk_level')}. "
            f"Please confirm to proceed with: {user_input}"
        )
    
    return execution_result