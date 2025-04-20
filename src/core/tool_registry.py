"""ToolRegistry metadata module for ForgeNews."""

from typing import Dict, Any, List, Optional


class ToolInfo:
    """Metadata for a single tool."""
    def __init__(self, name: str, risk_level: str, tool_type: str):
        self.name = name
        self.risk_level = risk_level
        self.tool_type = tool_type


class ToolRegistry:
    """Registry that holds metadata for all available tools."""
    def __init__(self) -> None:
        self.tools: Dict[str, ToolInfo] = {}

    def register(self, tool_name: str, risk_level: str, tool_type: str) -> None:
        self.tools[tool_name] = ToolInfo(tool_name, risk_level, tool_type)

    def get(self, tool_name: str) -> Optional[ToolInfo]:
        return self.tools.get(tool_name)

    def block_high_risk(self) -> List[str]:
        """Return names of tools that are high-risk."""
        return [name for name, info in self.tools.items() if info.risk_level.lower() == 'high']


# Initialize default registry with conflict_agent tools
registry = ToolRegistry()
registry.register('get_conflict_feed', risk_level='low', tool_type='fetch')
registry.register('flag_event', risk_level='medium', tool_type='analysis')
