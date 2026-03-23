"""
llm_client.py - LLM客户端封装
"""

from langchain_openai import ChatOpenAI
from .config_loader import get_llm_config

_llm_client = None


def get_llm_client() -> ChatOpenAI:
    """获取LLM客户端"""
    global _llm_client
    if _llm_client is None:
        config = get_llm_config()
        _llm_client = ChatOpenAI(
            model=config.get('model', 'gpt-3.5-turbo'),
            api_key=config.get('api_key', 'dummy'),
            base_url=config.get('base_url', ''),
            temperature=config.get('temperature', 0.7),
            timeout=config.get('timeout', 60)  # 版本8：添加超时配置
        )
    return _llm_client
