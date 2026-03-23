"""
generate_sop.py - SOP自动生成工具
基于相似历史故障和SOP，自动生成新的SOP
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import render_prompt
from .history_store import match_history_faults


# 预定义工具清单（所有SOP步骤必须使用这些工具）
PREDEFINED_TOOLS = [
    {"name": "get_relevant_metric", "description": "获取相关指标数据"},
    {"name": "pod_analyze", "description": "分析Pod状态"},
    {"name": "get_pod_logs", "description": "获取Pod日志"},
    {"name": "check_events", "description": "检查Kubernetes事件"},
    {"name": "analyze_memory", "description": "分析内存使用"},
]


def generate_sop(
    fault_info: str,
    similar_history_faults: List[Dict[str, Any]] = None,
    similar_sops: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate SOP: 基于相似案例生成新SOP

    Args:
        fault_info: 故障信息
        similar_history_faults: 相似历史故障列表
        similar_sops: 相似SOP列表

    Returns:
        生成的新SOP
    """
    # 构建上下文
    context = f"故障信息: {fault_info}\n\n"

    # 添加相似SOP作为示例
    if similar_sops:
        context += "相似SOP参考:\n"
        for sop in similar_sops[:3]:
            context += f"- SOP名称: {sop.get('sop_name', '未知')}\n"
            context += f"  故障类型: {sop.get('fault_type', '未知')}\n"
            steps = sop.get('steps', [])
            if isinstance(steps, str):
                steps = json.loads(steps) if steps else []
            context += f"  步骤: {len(steps)}步\n"
            for step in steps[:3]:
                context += f"    - {step.get('step_num')}. {step.get('tool_name')}: {step.get('description')}\n"
            context += "\n"

    # 添加相似历史故障作为示例
    if similar_history_faults:
        context += "相似历史故障参考:\n"
        for fault in similar_history_faults[:3]:
            context += f"- 故障: {fault.get('fault_info', '未知')}\n"
            context += f"  根因: {fault.get('root_cause', '未知')}\n"
            context += f"  观测: {fault.get('observation', '未知')[:100]}...\n\n"

    # 添加工具清单
    context += "可用工具清单（必须使用这些工具）:\n"
    for tool in PREDEFINED_TOOLS:
        context += f"- {tool['name']}: {tool['description']}\n"

    # 生成SOP
    prompt = render_prompt(
        "generate_sop",
        fault_info=fault_info,
        context=context,
        predefined_tools=str(PREDEFINED_TOOLS)
    )

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)
        content = response.content

        # 尝试提取JSON
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        sop_data = json.loads(content)

        # 验证SOP格式
        if "steps" not in sop_data:
            sop_data["steps"] = []

        # 确保每个步骤有必要的字段
        for step in sop_data.get("steps", []):
            if "step_num" not in step:
                step["step_num"] = sop_data["steps"].index(step) + 1
            if "tool_name" not in step:
                # 尝试从description推断工具
                step["tool_name"] = infer_tool_from_description(step.get("description", ""))

        return {
            "status": "success",
            "sop_name": sop_data.get("sop_name", f"自动生成SOP-{fault_info}"),
            "fault_type": sop_data.get("fault_type", infer_fault_type(fault_info)),
            "description": sop_data.get("description", ""),
            "steps": sop_data.get("steps", [])
        }

    except Exception as e:
        print(f"Generate SOP失败: {e}")
        # 返回默认SOP
        return get_default_sop(fault_info)


def infer_tool_from_description(description: str) -> str:
    """从描述推断工具名称"""
    description = description.lower()
    if "指标" in description or "metric" in description:
        return "get_relevant_metric"
    elif "pod" in description or "状态" in description:
        return "pod_analyze"
    elif "日志" in description or "log" in description:
        return "get_pod_logs"
    elif "事件" in description or "event" in description:
        return "check_events"
    elif "内存" in description or "memory" in description:
        return "analyze_memory"
    return "pod_analyze"  # 默认


def infer_fault_type(fault_info: str) -> str:
    """从故障信息推断故障类型"""
    fault_info = fault_info.lower()
    if "cpu" in fault_info or "CPU" in fault_info:
        return "CPU过高"
    elif "内存" in fault_info or "memory" in fault_info:
        return "内存泄漏"
    elif "io" in fault_info or "IO" in fault_info:
        return "IO错误"
    elif "网络" in fault_info or "network" in fault_info:
        return "网络问题"
    elif "pod" in fault_info or "Pod" in fault_info:
        return "Pod故障"
    return "未知故障"


def get_default_sop(fault_info: str) -> Dict[str, Any]:
    """获取默认SOP"""
    fault_type = infer_fault_type(fault_info)
    return {
        "status": "success",
        "sop_name": f"{fault_type}诊断SOP",
        "fault_type": fault_type,
        "description": f"自动生成的{fault_type}诊断SOP",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取相关指标数据"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod状态"},
            {"step_num": 3, "tool_name": "get_pod_logs", "description": "获取Pod日志"},
            {"step_num": 4, "tool_name": "check_events", "description": "检查Kubernetes事件"}
        ]
    }
