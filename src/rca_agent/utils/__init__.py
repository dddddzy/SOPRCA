"""
utils/__init__.py - 通用工具函数
"""

import re
import json
from typing import Any, Dict


def clean_llm_response(content: str) -> str:
    """
    清理LLM响应中的各种标签和噪声
    注意: 需要先匹配更具体的模式，再匹配通用模式
    """
    if not content:
        return content

    # 【重要】必须先匹配更具体的标签，再匹配通用标签
    # 否则 <.*?> 会先匹配掉 <thought> 中的部分字符
    patterns = [
        # 先清理think标签（中文和英文，贪婪模式）
        r'<think>[\s\S]*?</think>',
        r'<think>[\s\S]*?<\/think>',
        # 清理各种XML/HTML标签（包括自闭合和成对标签，多行模式）
        r'</?[\w-]+[\s\S]*?>',
        # 清理中文思考标签
        r'【[\s\S]*?】',
    ]

    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # 清理多余空白
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content


def parse_json_from_response(content: str) -> str:
    """
    从LLM响应中提取JSON部分 - 增强版，处理更多边界情况
    """
    if not content:
        return ""

    # 先清理思考标签
    content = clean_llm_response(content)

    if not content:
        return ""

    # 尝试多种JSON提取方式
    # 1. 标准```json代码块
    if "```json" in content:
        parts = content.split("```json")
        if len(parts) > 1:
            json_part = parts[1]
            if "```" in json_part:
                json_part = json_part.split("```")[0]
            return json_part.strip()

    # 2. 普通```代码块
    if "```" in content:
        parts = content.split("```")
        if len(parts) > 1:
            # 尝试找到JSON对象
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 代码块内容
                    part = part.strip()
                    if part.startswith('{') or part.startswith('['):
                        return part

    # 3. 直接尝试提取JSON对象（以{或[开头）
    # 匹配第一个 { 到最后一个 } 的完整JSON
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        return json_match.group(0)

    # 匹配数组格式
    json_array_match = re.search(r'\[[\s\S]*\]', content)
    if json_array_match:
        return json_array_match.group(0)

    # 4. 如果以上都失败，返回原始清理后的内容
    return content.strip()
