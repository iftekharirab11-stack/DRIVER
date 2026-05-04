# [GOAL] Create a "While Loop" for task execution.
# [CONTEXT] Not just a chatbot—a worker that stays active until the job is done.

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from typing import TypedDict, Annotated, Sequence, Callable, Any
import operator
import asyncio

# [STATE] The working memory of the agent
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task: str
    iteration: int

# [MODEL] The reasoning engine
async def call_model(state: AgentState, llm, tools_by_name):
    """Decide next action based on current state."""
    from langchain_core.prompts import ChatPromptTemplate
    
    # Build tool descriptions
    tools_desc = "\n".join([f"- {name}: {func.__doc__ or 'No description'}" 
                           for name, func in tools_by_name.items()])
    
    system_prompt = f"""You are an autonomous agent. Available tools:

{tools_desc}

INSTRUCTIONS:
- If task is complete, respond with final answer (no tool calls)
- If you need information, call the appropriate tool
- After tool returns, analyze result and continue if needed
- Maximum 5 iterations per task

Think step-by-step."""
    
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    
    # Bind tools
    tool_schemas = []
    for tool in tools_by_name.values():
        if hasattr(tool, 'args_schema'):
            tool_schemas.append(tool.args_schema)
    
    chain = llm
    if tool_schemas:
        # Create tool calling chain
        from langchain.agents import create_agent
        from langchain import hub
        prompt = hub.pull("hwchase17/openai-functions-agent")
        chain = create_agent(llm, list(tools_by_name.values()), prompt)
        response = await chain.ainvoke({"messages": messages, "input": state["task"]})
        return response
    
    # Fallback: simple invoke
    resp = await llm.ainvoke(messages)
    return {"messages": [resp], "task": state["task"], "iteration": state.get("iteration", 0) + 1}

# [TOOLS] Execute the chosen tool
async def execute_tools(state: AgentState, tools_by_name):
    """Run the tool and capture output."""
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"next": "end"}
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        
        tool_func = tools_by_name.get(tool_name)
        if tool_func:
            try:
                if hasattr(tool_func, 'ainvoke'):
                    result = await tool_func.ainvoke(tool_args)
                else:
                    result = tool_func(**tool_args) if isinstance(tool_args, dict) else tool_func(tool_args)
                tool_messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                    name=tool_name
                ))
            except Exception as e:
                tool_messages.append(ToolMessage(
                    content=f"Error: {str(e)}",
                    tool_call_id=tool_call["id"],
                    name=tool_name
                ))
    
    return {"messages": tool_messages, "iteration": state.get("iteration", 0) + 1}

# [ORCHESTRATOR] Build the execution graph
def build_graph(llm, tools_dict):
    """Construct the agent workflow graph."""
    
    async def agent_node(state):
        return await call_model(state, llm, tools_dict)
    
    async def tools_node(state):
        return await execute_tools(state, tools_dict)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    
    workflow.set_entry_point("agent")
    
    # Decision routing
    def router(state):
        last_msg = state["messages"][-1]
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            return "tools"
        if state.get("iteration", 0) >= 5:
            return END
        return END
    
    workflow.add_conditional_edges("agent", router, {
        "tools": "tools",
        END: END
    })
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# [PUBLIC] Main orchestration function
async def orchestrate_task(task: str, llm, tools_registry) -> str:
    """Run the full agent loop until task completion."""
    
    graph = build_graph(llm, tools_registry)
    
    initial_state = {
        "messages": [SystemMessage(content="Alpha Agent Online.")],
        "task": task,
        "iteration": 0
    }
    
    try:
        final_state = await graph.ainvoke(initial_state)
        
        # Extract final answer
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                return msg.content
        
        return "Task completed after max iterations."
    except Exception as e:
        return f"Orchestration error: {str(e)}"