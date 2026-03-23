"""
LangGraph API 包装文件
用于langgraph dev启动服务
"""
import sys
import os

# 将src目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rca_agent.graph.build_graph import create_rca_graph

# 导出函数供LangGraph使用
__all__ = ["create_rca_graph"]
