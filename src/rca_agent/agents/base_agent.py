"""
base_agent.py - 智能体基类
"""

from typing import Dict, Any


class BaseAgent:
    """智能体基类"""

    def __init__(self, name: str):
        self.name = name

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """运行智能体"""
        raise NotImplementedError
