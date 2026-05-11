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
    重点：识别CPU使用率接近资源限制的情况
    """
    key_clues = []
    possible_root_causes = []
    excluded_root_causes = []
    fault_type = "未知"
    fault_location = "未知"

    import re

    # 用于累计CPU数据的变量
    cpu_data = []  # [(pod_name, cpu_value, limit_value), ...]

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

        # 检测故障位置 - 尝试从current_observation中提取
        service_match = re.search(r'([a-zA-Z0-9_-]+(?:service|pod)[a-zA-Z0-9_-]*)', current_observation, re.IGNORECASE)
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

        # 提取CPU相关信息 - 通用正则匹配各种格式
        if 'cpu' in action.lower() or 'metric' in action.lower() or 'pod' in action.lower():
            # 尝试提取CPU数值 (支持 '28m', '250m', '0.25' 等格式)
            cpu_matches = re.findall(r"['\"]?cpu['\"]?\s*[:=]\s*['\"]?(\d+\.?\d*)([kmg])?['\"]?", result_str, re.IGNORECASE)
            for cpu_match in cpu_matches:
                cpu_val_str = cpu_match[0]
                cpu_unit = cpu_match[1] if len(cpu_match) > 1 else ''
                try:
                    cpu_val = float(cpu_val_str)
                    if cpu_unit.lower() == 'm':
                        cpu_val = cpu_val / 1000  # 毫核转核
                    cpu_data.append(('unknown', cpu_val, None))
                    key_clues.append(f"检测到CPU: {cpu_val_str}{cpu_unit}")
                except:
                    pass

            # 尝试提取limit信息
            limit_matches = re.findall(r"['\"]?(?:cpu)?limit['\"]?\s*[:=]\s*['\"]?(\d+\.?\d*)([kmg])?['\"]?", result_str, re.IGNORECASE)
            for i, limit_match in enumerate(limit_matches):
                limit_val_str = limit_match[0]
                limit_unit = limit_match[1] if len(limit_match) > 1 else ''
                try:
                    limit_val = float(limit_val_str)
                    if limit_unit.lower() == 'm':
                        limit_val = limit_val / 1000
                    if i < len(cpu_data):
                        cpu_data[-1] = (cpu_data[-1][0], cpu_data[-1][1], limit_val)
                    key_clues.append(f"CPU Limit: {limit_val_str}{limit_unit}")
                except:
                    pass

            # 尝试提取request信息
            request_match = re.findall(r"['\"]?(?:cpu)?request['\"]?\s*[:=]\s*['\"]?(\d+\.?\d*)([kmg])?['\"]?", result_str, re.IGNORECASE)
            if request_match:
                req_match = request_match[0]
                req_val_str = req_match[0]
                req_unit = req_match[1] if len(req_match) > 1 else ''
                key_clues.append(f"CPU Request: {req_val_str}{req_unit}")

        # 解析Pod状态
        if 'pod' in action.lower() or 'analyze' in action.lower():
            # 检测Pod名称
            pod_matches = re.findall(r"['\"]?name['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?", result_str)
            if pod_matches and fault_location == "未知":
                fault_location = pod_matches[0]

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

    # 分析CPU数据，检测是否接近资源上限
    for pod_name, cpu_val, limit_val in cpu_data:
        if cpu_val is not None and limit_val is not None:
            if limit_val > 0:
                usage_ratio = cpu_val / limit_val
                if usage_ratio >= 0.9:
                    possible_root_causes.append("CPU资源配置过低（使用率超过90%限制）")
                    key_clues.append(f"CPU使用率({cpu_val:.2f}核) >= 90%限制({limit_val:.2f}核)")
                    excluded_root_causes.append("应用代码错误")
                elif usage_ratio >= 0.7:
                    possible_root_causes.append("CPU资源可能不足")
                    key_clues.append(f"CPU使用率偏高({cpu_val:.2f}核/{limit_val:.2f}核)")

    # 如果没有提取到任何线索，使用默认信息
    if not key_clues:
        key_clues = ["未能提取到有效线索"]

    if not fault_location:
        fault_location = "未知"

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
