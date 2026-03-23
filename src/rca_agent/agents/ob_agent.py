"""
ob_agent.py - ObAgent，观测结果噪声过滤与线索提取
使用LLM从观测结果中提取结构化线索
"""

import json
from typing import Dict, Any, Optional
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import render_prompt
from ..utils import parse_json_from_response


def extract_clues(
    current_observation: str,
    executed_steps: list
) -> Dict[str, Any]:
    """ObAgent: 提取故障线索"""
    steps_text = ""
    for i, step in enumerate(executed_steps, 1):
        action = step.get('action', '')
        result = step.get('result', {})
        steps_text += f"{i}. {action}: {result}\n"

    prompt = render_prompt(
        "ob_agent",
        current_observation=current_observation or "无",
        executed_steps=steps_text or "无"
    )

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)

        # 清理并提取JSON - 使用更健壮的解析
        content = parse_json_from_response(response.content)

        # 打印调试信息（已清理的内容）
        print(f"[ObAgent Debug] LLM响应长度: {len(response.content)}")
        print(f"[ObAgent Debug] 清理并解析后内容（前200字符）: {content[:200] if content else '空'}")

        if not content:
            raise ValueError("解析后的内容为空")

        clues = json.loads(content)

        return {
            "fault_type": clues.get("fault_type", "未知"),
            "key_clues": clues.get("key_clues", []),
            "fault_location": clues.get("fault_location", "未知"),
            "possible_root_causes": clues.get("possible_root_causes", []),
            "excluded_root_causes": clues.get("excluded_root_causes", [])
        }

    except Exception as e:
        print(f"ObAgent LLM调用失败: {e}")
        # 详细打印当前观测结果
        print(f"[ObAgent Fallback] current_observation长度: {len(current_observation) if current_observation else 0}")
        print(f"[ObAgent Fallback] executed_steps数量: {len(executed_steps)}")
        return get_fallback_clues(current_observation, executed_steps)


def get_fallback_clues(current_observation: str, executed_steps: list) -> Dict[str, Any]:
    """
    兜底线索提取 - 从实际执行结果中提取线索
    版本修复：不再使用硬编码数据，而是真正解析executed_steps
    """
    key_clues = []
    possible_root_causes = []
    excluded_root_causes = []
    fault_type = "未知"
    fault_location = "未知"

    # 方法1: 尝试从current_observation中解析
    if current_observation:
        obs_lower = current_observation.lower()

        # 检测故障类型
        if "cpu" in obs_lower and "高" in current_observation:
            fault_type = "CPU过高"
        elif "memory" in obs_lower or "内存" in current_observation:
            if "oom" in obs_lower or "溢出" in current_observation:
                fault_type = "内存溢出"
            else:
                fault_type = "内存泄漏"
        elif "crash" in obs_lower or "崩溃" in current_observation:
            fault_type = "服务崩溃"

        # 检测故障位置 - 尝试从fault_info中提取
        import re
        service_match = re.search(r'(\w+service|\w+-service|\w+[-\s]pod)', current_observation, re.IGNORECASE)
        if service_match:
            fault_location = service_match.group(1)

    # 方法2: 从executed_steps中逐个解析工具返回结果
    for step in executed_steps:
        action = step.get('action', '')
        result = step.get('result', '')

        if not result:
            continue

        # 解析result - 可能是字符串或字典
        if isinstance(result, str):
            result_str = result
        else:
            result_str = str(result)

        # 提取CPU相关信息
        if 'cpu' in action.lower() or 'metric' in action.lower():
            # 尝试提取CPU数值
            cpu_match = re.search(r'["\']?cpu["\']?\s*[:=]\s*(\d+)', result_str, re.IGNORECASE)
            if cpu_match:
                cpu_val = cpu_match.group(1)
                key_clues.append(f"CPU使用率: {cpu_val}%")
                if int(cpu_val) > 90:
                    possible_root_causes.append("CPU资源不足")

            # 提取limit信息
            limit_match = re.search(r'["\']?limit["\']?\s*[:=]\s*["\']?(\d+\.?\d*)([kmg]?)', result_str, re.IGNORECASE)
            if limit_match:
                limit_val = limit_match.group(1)
                limit_unit = limit_match.group(2)
                key_clues.append(f"CPU Limit: {limit_val}{limit_unit}核")

        # 解析内存信息
        if 'memory' in action.lower() or 'mem' in action.lower():
            mem_match = re.search(r'["\']?memory["\']?\s*[:=]\s*(\d+)', result_str, re.IGNORECASE)
            if mem_match:
                mem_val = mem_match.group(1)
                key_clues.append(f"内存使用率: {mem_val}%")
                if int(mem_val) > 80:
                    possible_root_causes.append("内存使用率过高")

        # 解析Pod状态
        if 'pod' in action.lower() or 'analyze' in action.lower():
            if 'running' in result_str.lower():
                key_clues.append("Pod状态: Running")
            if 'restart' in result_str.lower():
                restart_match = re.search(r'restart[s]?\s*[:=]\s*(\d+)', result_str, re.IGNORECASE)
                if restart_match:
                    restart_val = restart_match.group(1)
                    key_clues.append(f"Pod重启次数: {restart_val}")
                    if int(restart_val) > 0:
                        possible_root_causes.append("Pod频繁重启")

        # 解析日志
        if 'log' in action.lower():
            if 'error' in result_str.lower() or 'fail' in result_str.lower():
                key_clues.append("日志包含错误信息")
            else:
                key_clues.append("日志无明显异常")
                excluded_root_causes.append("日志错误")

        # 解析事件
        if 'event' in action.lower():
            if 'backoff' in result_str.lower() or 'warning' in result_str.lower():
                key_clues.append("存在Warning/BackOff事件")
                possible_root_causes.append("容器启动失败")
            else:
                excluded_root_causes.append("事件异常")

    # 如果没有提取到任何线索，使用默认信息
    if not key_clues:
        key_clues = ["未能提取到有效线索"]

    if not fault_location:
        fault_location = "未知"

    # 基于线索更新可能根因
    if "CPU" in str(key_clues) and "接近资源上限" in str(key_clues):
        possible_root_causes.append("资源限制配置过低")

    # 排除明显不相关的根因
    if "日志无明显异常" in key_clues:
        excluded_root_causes.append("应用代码错误")

    return {
        "fault_type": fault_type,
        "key_clues": key_clues[:10],  # 最多10条线索
        "fault_location": fault_location,
        "possible_root_causes": list(set(possible_root_causes))[:5],  # 去重，最多5条
        "excluded_root_causes": list(set(excluded_root_causes))[:5]
    }
