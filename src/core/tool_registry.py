"""ToolRegistry metadata module for ForgeNews."""

import os
import sys
from typing import Dict, Any, List, Optional

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


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
registry.register('get_summary', risk_level='low', tool_type='data')

# Register AI news agent tools
registry.register('get_ai_news', risk_level='low', tool_type='fetch')

# Register insight agent tools
registry.register('analyze_conflict', risk_level='medium', tool_type='analysis')

# Register report agent tools
registry.register('generate_report', risk_level='medium', tool_type='content')

# Register llm report agent tools
registry.register('generate_llm_report', risk_level='high', tool_type='llm')

# Register substack agent tools
registry.register('get_content', risk_level='low', tool_type='fetch')
registry.register('publish_newsletter', risk_level='high', tool_type='publish')

# Register ctrl agent tools
registry.register('monitor_agents', risk_level='low', tool_type='monitoring')
