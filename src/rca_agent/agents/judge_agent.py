"""
judge_agent.py - JudgeAgent，根因判定与循环拦截
版本6: 沙箱安全执行 + 完整防死循环与审计
"""

import json
import time
from typing import Dict, Any, List, Optional
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import render_prompt
from ..utils import parse_json_from_response
from ..utils.logger import AuditLogger

# 防死循环配置
MAX_ITERATIONS = 10  # 最大循环次数
MAX_NO_GAIN = 3  # 最大无增益次数
REPEAT_THRESHOLD = 2  # 重复动作检测阈值
GLOBAL_TIMEOUT = 300  # 全局超时5分钟


def judge_root_cause(
    fault_info: str,
    extracted_clues: Dict[str, Any],
    executed_steps: List[Dict],
    iteration_count: int,
    consecutive_no_gain: int,
    max_iterations: int = MAX_ITERATIONS,
    action_history: Optional[List[Dict]] = None,
    global_start_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    JudgeAgent: 判定是否找到根因 + 防死循环判定
    版本6: 整合所有防死循环逻辑
    版本7修复: 先判定根因，再检查是否终止（避免误判）
    """
    # 记录审计日志
    AuditLogger.log_judge({
        "iteration": iteration_count,
        "no_gain": consecutive_no_gain
    })

    # 1. 全局超时检测 - 立即终止
    if global_start_time:
        elapsed = time.time() - global_start_time
        if elapsed > GLOBAL_TIMEOUT:
            AuditLogger.log_termination("全局超时")
            return {
                "is_root_cause_found": False,
                "explanation": f"全局超时({elapsed:.0f}秒)，强制终止",
                "suggested_actions": ["生成报告"],
                "termination_reason": "global_timeout"
            }

    # 2. 最大循环次数检测 - 立即终止
    if iteration_count >= max_iterations:
        AuditLogger.log_termination(f"达到最大循环次数({max_iterations})")
        return {
            "is_root_cause_found": False,
            "explanation": f"达到最大循环次数({max_iterations})，强制终止",
            "suggested_actions": ["生成报告"],
            "termination_reason": "max_iterations"
        }

    # 3. 先调用LLM判定是否找到根因（版本7修复：这是核心逻辑，必须先执行）
    clues_text = f"故障类型: {extracted_clues.get('fault_type', '未知')}\n"
    clues_text += f"故障位置: {extracted_clues.get('fault_location', '未知')}\n"
    clues_text += f"关键线索: {extracted_clues.get('key_clues', [])}\n"
    clues_text += f"可能根因: {extracted_clues.get('possible_root_causes', [])}\n"
    clues_text += f"已排除根因: {extracted_clues.get('excluded_root_causes', [])}\n"

    steps_text = ""
    for i, step in enumerate(executed_steps, 1):
        steps_text += f"{i}. {step.get('action')}: {step.get('explanation')}\n"

    prompt = render_prompt(
        "judge_agent",
        fault_info=fault_info,
        clues=clues_text,
        executed_steps=steps_text,
        iteration_count=iteration_count,
        no_gain_count=consecutive_no_gain
    )

    llm_found_root_cause = False
    llm_result = None

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)

        # 清理并提取JSON
        content = parse_json_from_response(response.content)
        llm_result = json.loads(content)
        llm_found_root_cause = llm_result.get("is_root_cause_found", False)

        # 如果找到根因，立即返回（版本7修复：不再继续检查重复动作）
        if llm_found_root_cause:
            AuditLogger.log_termination("找到根因")
            return {
                "is_root_cause_found": True,
                "explanation": llm_result.get("explanation", "已找到根因"),
                "suggested_actions": llm_result.get("suggested_actions", ["生成报告"]),
                "termination_reason": "root_cause_found"
            }

    except Exception as e:
        print(f"JudgeAgent LLM调用失败: {e}")
        AuditLogger.log_error(str(e))
        # LLM失败时使用兜底判定
        llm_result = get_fallback_judgment(iteration_count, consecutive_no_gain, max_iterations)

    # 4. LLM判定未找到根因时，检查是否应该终止（版本7修复：移到LLM判定之后）
    # 4a. 重复动作检测
    if action_history and len(action_history) >= REPEAT_THRESHOLD:
        is_repeat = check_repeat_actions(action_history, REPEAT_THRESHOLD)
        if is_repeat:
            AuditLogger.log_termination("重复动作")
            return {
                "is_root_cause_found": False,
                "explanation": "连续执行相同动作，无新增入参，判定为无效循环",
                "suggested_actions": ["生成报告"],
                "termination_reason": "repeat_action"
            }

    # 4b. 无增益检测
    if consecutive_no_gain >= MAX_NO_GAIN:
        AuditLogger.log_termination(f"连续{MAX_NO_GAIN}轮无信息增益")
        return {
            "is_root_cause_found": False,
            "explanation": f"连续{MAX_NO_GAIN}轮无信息增益，强制终止",
            "suggested_actions": ["生成报告"],
            "termination_reason": "no_gain"
        }

    # 返回LLM判定结果
    return llm_result


def check_repeat_actions(action_history: List[Dict], threshold: int = 2) -> bool:
    """
    检查是否连续执行相同动作

    Args:
        action_history: 动作历史
        threshold: 连续相同动作次数阈值

    Returns:
        是否检测到重复动作
    """
    if len(action_history) < threshold:
        return False

    # 获取最近threshold个动作
    recent_actions = action_history[-threshold:]

    # 检查是否所有动作都相同
    if len(set(a.get("action") for a in recent_actions)) == 1:
        # 检查是否入参也相同
        first_params = recent_actions[0].get("params", {})
        all_same_params = all(
            a.get("params", {}) == first_params
            for a in recent_actions
        )
        if all_same_params:
            return True

    return False


def get_fallback_judgment(
    iteration_count: int,
    consecutive_no_gain: int,
    max_iterations: int
) -> Dict[str, Any]:
    """兜底判定"""
    if iteration_count >= max_iterations:
        return {
            "is_root_cause_found": False,
            "explanation": "达到最大循环次数，强制终止（未找到根因）",
            "suggested_actions": ["生成报告"],
            "termination_reason": "max_iterations"
        }

    if consecutive_no_gain >= MAX_NO_GAIN:
        return {
            "is_root_cause_found": False,
            "explanation": f"连续{MAX_NO_GAIN}轮无信息增益，强制终止",
            "suggested_actions": ["生成报告"],
            "termination_reason": "no_gain"
        }

    return {
        "is_root_cause_found": False,
        "explanation": "需要更多排查",
        "suggested_actions": ["继续执行更多工具"]
    }
