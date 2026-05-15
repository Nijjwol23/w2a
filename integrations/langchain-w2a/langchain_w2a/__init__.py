"""
langchain-w2a — LangChain integration for the Web2Agent Protocol.

Turns any W2A-enabled website's declared skills into LangChain tools.

Usage:
    from langchain_w2a import W2AToolkit

    toolkit = await W2AToolkit.from_url("w2a-protocol.org")
    tools = toolkit.get_tools()

    # Use with any LangChain agent
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    agent = create_tool_calling_agent(llm, tools, prompt)
"""

from langchain_w2a.toolkit import W2AToolkit
from langchain_w2a.tools import W2ADiscoverTool, W2ASkillTool

__version__ = "0.1.0"

__all__ = [
    "W2AToolkit",
    "W2ADiscoverTool",
    "W2ASkillTool",
]
