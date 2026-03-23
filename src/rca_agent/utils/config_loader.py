"""
config_loader.py - 配置文件加载
版本7: 工程化完善
"""

import yaml
import os

_config = None


def load_config() -> dict:
    """加载配置文件"""
    global _config
    if _config is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f)
    return _config


def reload_config():
    """重新加载配置"""
    global _config
    _config = None
    return load_config()


def get_llm_config() -> dict:
    """获取LLM配置"""
    config = load_config()
    return config.get('llm', {})


def get_loop_config() -> dict:
    """获取循环配置"""
    config = load_config()
    return config.get('anti_loop', {})


def get_knowledge_base_config() -> dict:
    """获取知识库配置"""
    config = load_config()
    return config.get('knowledge_base', {})


def get_tools_config() -> dict:
    """获取工具配置"""
    config = load_config()
    return config.get('tools', {})


def get_logging_config() -> dict:
    """获取日志配置"""
    config = load_config()
    return config.get('log', {})
