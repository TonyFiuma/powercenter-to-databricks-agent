"""
Experimental PowerCenter agent built with LangChain's create_agent.

This module represents the first agentic approach developed for the
PowerCenter-to-Databricks migration project.

The agent uses a local Qwen3:4b model through Ollama and exposes tools
for tasks such as:

- Parsing Informatica PowerCenter XML mappings.
- Retrieving relevant information from the PowerCenter documentation
  through the local RAG pipeline.

This implementation was created to test LLM-driven tool orchestration.
During testing, the local Qwen3:4b model was able to call individual
tools but did not reliably orchestrate multiple tools in sequence
(e.g. parse mapping -> retrieve documentation -> generate response).

For this reason, this module is kept as an experimental implementation
and is not the main architecture of the project.

The main migration agent uses LangGraph with an explicit and
deterministic workflow, where parsing, retrieval, planning, and
PySpark generation are executed as predefined graph nodes.
"""

from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from tools.powercenter_docs_tool import search_powercenter_documentation
from tools.powercenter_parser_tool import parse_powercenter_mapping


SYSTEM_PROMPT = """
You are a PowerCenter migration analysis agent.

When analyzing a PowerCenter XML:

- Base your analysis only on information returned by the available tools.
- Do not invent business purposes, business rules, compliance requirements,
  validation logic, or data quality logic unless explicitly present in the XML
  or documentation returned by a tool.
- Clearly distinguish facts from assumptions.
- Use the parsed data_flow to determine the actual mapping flow.
- Report transformation names and transformation types exactly as parsed.
- When analyzing expressions, report the expression exactly as parsed.
- If information is missing, say that it is not available in the parsed XML.
- Do not infer what a mapping is used for only from table names or field names.
"""


def create_powercenter_agent():

    llm = ChatOllama(
        model="qwen3:4b"
    )

    tools = [
        search_powercenter_documentation,
        parse_powercenter_mapping
    ]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )

    return agent