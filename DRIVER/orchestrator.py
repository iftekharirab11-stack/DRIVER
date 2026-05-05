# DRIVER/orchestrator.py
# [GOAL] LangGraph "while-loop" orchestrator for multi-step complex tasks.

from __future__ import annotations

import asyncio
from typing import TypedDict, Annotated, Sequence, Dict, Any
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage,
)


# ── State schema ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task:      str
    iteration: int


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def call_model(state: AgentState, llm, tools_by_name: Dict) -> AgentState:
    """Reason about next action."""
    tool_list   = list(tools_by_name.values())
    bound_model = llm.bind_tools(tool_list) if tool_list else llm

    messages = [
        SystemMessage(content=(
            "You are an autonomous agent. "
            "Use tools to accomplish the task. "
            "When done, respond with your final answer (no tool calls). "
            f"Task: {state['task']}"
        ))
    ] + list(state["messages"])

    response = await bound_model.ainvoke(messages)

    return {
        "messages":  [response],
        "task":      state["task"],
        "iteration": state.get("iteration", 0) + 1,
    }


async def execute_tools(state: AgentState, tools_by_name: Dict) -> AgentState:
    """Execute any tool calls in the last message."""
    last_msg = state["messages"][-1]
    if not getattr(last_msg, "tool_calls", None):
        return {"messages": [], "task": state["task"], "iteration": state["iteration"]}

    tool_messages = []
    for tc in last_msg.tool_calls:
        tool_func = tools_by_name.get(tc["name"])
        if not tool_func:
            result = f"Tool '{tc['name']}' not found."
        else:
            try:
                args = tc.get("args", {})
                if hasattr(tool_func, "ainvoke"):
                    result = await tool_func.ainvoke(args)
                elif callable(tool_func):
                    result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
                else:
                    result = str(tool_func)
            except Exception as exc:
                result = f"Error executing {tc['name']}: {exc}"

        tool_messages.append(ToolMessage(
            content=str(result),
            tool_call_id=tc["id"],
            name=tc["name"],
        ))

    return {
        "messages":  tool_messages,
        "task":      state["task"],
        "iteration": state["iteration"],
    }


# ── Graph factory ─────────────────────────────────────────────────────────────

def build_graph(llm, tools_dict: Dict):
    """Assemble the agent workflow graph."""

    async def agent_node(state):
        return await call_model(state, llm, tools_dict)

    async def tools_node(state):
        return await execute_tools(state, tools_dict)

    def router(state) -> str:
        last = state["messages"][-1]
        if state.get("iteration", 0) >= 8:
            return END
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    wf = StateGraph(AgentState)
    wf.add_node("agent", agent_node)
    wf.add_node("tools", tools_node)
    wf.set_entry_point("agent")
    wf.add_conditional_edges("agent", router, {"tools": "tools", END: END})
    wf.add_edge("tools", "agent")
    return wf.compile()


# ── Public entry point ────────────────────────────────────────────────────────

async def orchestrate_task(task: str, llm, tools_registry: Dict) -> str:
    """Run the full agent loop until the task is complete or 8 iterations pass."""
    graph = build_graph(llm, tools_registry)

    init_state: AgentState = {
        "messages":  [HumanMessage(content=task)],
        "task":      task,
        "iteration": 0,
    }

    try:
        final = await graph.ainvoke(init_state)
        for msg in reversed(final["messages"]):
            if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                return msg.content
        return "Task completed (no final text response found)."
    except Exception as exc:
        return f"Orchestration error: {exc}"