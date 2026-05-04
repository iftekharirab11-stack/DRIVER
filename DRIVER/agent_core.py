# [GOAL] Core execution logic (separated to avoid circular imports)
from typing import Dict, Any
from langchain.agents import create_agent
from langchain_core.messages import AIMessage

def create_agent_instance(llm, tools, system_prompt: str):
    """Helper to create a LangChain agent."""
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)

def extract_ai_response(result) -> str:
    """Extract AI message from agent result."""
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
            return msg.content
    return str(messages[-1].content if messages else "No response")

def run_simple_agent(llm, tools, system_prompt: str, user_input: str) -> str:
    """Run single-turn agent."""
    agent = create_agent_instance(llm, tools, system_prompt)
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    return extract_ai_response(result)