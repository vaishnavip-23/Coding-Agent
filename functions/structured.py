from pydantic import BaseModel, Field
from typing import List

class ToolCall(BaseModel):
    """Represents a tool call the agent would make"""
    tool: str = Field(
        description="Exact function name: get_files_info, read, write, run_python, delete, or search_memory"
    )

class Step(BaseModel):
    """Represents a step in the agent's plan"""
    action: str = Field(description="What the agent will do in this step")
    reason: str = Field(description="Why this step is necessary")

class Plan(BaseModel):
    """
    Structured output model for the agent's planning mode.
    Returns a JSON plan of what the agent would do without actually executing tools.
    """
    goal: str = Field(description="The main objective the agent is trying to accomplish")
    steps: List[Step] = Field(description="List of actions the agent plans to take")
    tool_calls: List[ToolCall] = Field(
        description="List of tool calls the agent would make. Always include even if empty.",
        default_factory=list
    )
