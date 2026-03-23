"""
prompt_loader.py - Prompt文件加载与渲染
"""

import yaml
import os
from typing import Dict, Any


_prompts_cache = {}


def load_prompt(prompt_name: str) -> Dict[str, Any]:
    """
    加载Prompt文件

    Args:
        prompt_name: Prompt文件名（不含.yaml后缀）

    Returns:
        Prompt配置字典
    """
    if prompt_name in _prompts_cache:
        return _prompts_cache[prompt_name]

    # 查找prompts目录
    current_dir = os.path.dirname(__file__)
    # 从 src/rca_agent/utils/ 往回找到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    prompt_path = os.path.join(project_root, "prompts", f"{prompt_name}.yaml")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    _prompts_cache[prompt_name] = config
    return config


def get_prompt_template(prompt_name: str) -> str:
    """获取Prompt模板"""
    config = load_prompt(prompt_name)
    return config.get('prompt', '')


def render_prompt(prompt_name: str, **kwargs) -> str:
    """
    渲染Prompt模板

    Args:
        prompt_name: Prompt文件名
        **kwargs: 模板变量

    Returns:
        渲染后的Prompt
    """
    template = get_prompt_template(prompt_name)

    # 使用SafeTemplate避免双花括号问题
    # 先将{{替换为占位符，渲染后再替换回来
    template = template.replace('{{', '\x00').replace('}}', '\x01')

    # 渲染
    for key, value in kwargs.items():
        placeholder = f'{{{key}}}'
        template = template.replace(placeholder, str(value))

    # 恢复双花括号（原来是转义的单花括号）
    template = template.replace('\x00', '{').replace('\x01', '}')

    return template
