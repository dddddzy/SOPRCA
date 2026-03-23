"""
base_tool.py - 工具基类
"""

from typing import Dict, Any


class BaseTool:
    """工具基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def run(self, **kwargs) -> Dict[str, Any]:
        """运行工具"""
        raise NotImplementedError
