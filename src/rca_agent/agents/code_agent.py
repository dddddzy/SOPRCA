"""
code_agent.py - CodeAgent，SOP转可执行代码
使用LLM将SOP步骤转换为Python代码
"""

import re
from typing import Dict, Any, Optional
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import render_prompt
from ..utils import clean_llm_response


def extract_code(content: str) -> str:
    """从LLM输出中提取Python代码"""
    # 清理思考标签
    content = clean_llm_response(content)

    # 尝试提取代码块
    code_block_match = re.search(r'```python\s*(.*?)\s*```', content, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # 尝试提取普通的```代码块
    code_block_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
    if code_block_match:
        code = code_block_match.group(1).strip()
        # 检查是否像Python代码
        if 'def ' in code or 'import ' in code or 'return ' in code:
            return code

    # 如果没有代码块，找到第一个def run_sop开始的位置
    lines = content.split('\n')
    code_lines = []
    started = False

    for line in lines:
        # 找到def run_sop开始
        if 'def run_sop' in line:
            started = True
        if started:
            code_lines.append(line)

    if code_lines:
        code = '\n'.join(code_lines)
        if 'def run_sop' in code:
            # 找到函数结束（下一个def或文件结束）
            final_lines = []
            for line in code_lines:
                if line.strip().startswith('def ') and 'def run_sop' not in line:
                    break
                final_lines.append(line)
            return '\n'.join(final_lines)

    # 如果都不行，返回原始内容
    return content


def generate_code(matched_sop: Optional[Dict], fault_info: str) -> str:
    """CodeAgent: 将SOP转换为可执行代码"""
    if not matched_sop:
        return "# No SOP, cannot generate code"

    # 构建SOP信息（使用英文）
    sop_info = "SOP Name: " + matched_sop.get('sop_name', '') + "\nSteps:\n"
    for step in matched_sop.get('steps', []):
        sop_info += f"  - {step.get('step_num')}. {step.get('tool_name')}: {step.get('description')}\n"

    prompt = render_prompt(
        "code_agent",
        fault_info=fault_info,
        sop_info=sop_info
    )

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)
        # 提取Python代码
        code = extract_code(response.content)
        return code
    except Exception as e:
        print(f"CodeAgent LLM调用失败: {e}")
        return get_fallback_code(matched_sop)


def get_fallback_code(matched_sop: Dict) -> str:
    """兜底代码生成"""
    steps = matched_sop.get('steps', [])
    code_lines = [
        "def run_sop(fault_info: str) -> dict:",
        "    results = []",
        "    for step in steps:",
        "        tool_name = step.get('tool_name')",
        "        results.append({'tool': tool_name, 'status': 'mock'})",
        "    return {'status': 'success', 'results': results}",
        "",
        "steps = " + str(steps),
        "fault_info = 'productcatalogservice CPU过高'"
    ]
    return "\n".join(code_lines)
