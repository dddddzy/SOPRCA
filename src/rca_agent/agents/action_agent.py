"""
action_agent.py - ActionAgent，动作集生成与更新
使用LLM生成候选动作集
"""

import json
from typing import Dict, List, Optional
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import load_prompt, render_prompt
from ..utils import clean_llm_response, parse_json_from_response


# 预定义工具白名单（与action_agent.yaml保持一致）
TOOL_WHITELIST = [
    "match_sop",  # 匹配SOP
    "match_observation",  # 匹配历史故障
    "generate_code",
    "generate_sop",  # SOP自动生成
    "run_sop",
    "get_relevant_metric",
    "pod_analyze",
    "get_pod_logs",
    "check_events",
    "collect_trace",
    "analyze_trace_latency"
]


def generate_candidate_actions(
    fault_info: str,
    matched_sop: Optional[Dict],
    executed_steps: List[Dict],
    current_observation: Optional[str],
    has_code: bool = False,
    iteration_count: int = 0,
    is_root_cause_found: bool = False
) -> List[Dict[str, str]]:
    """使用LLM生成候选动作集"""
    sop_text = "无"
    if matched_sop:
        sop_text = f"SOP名称: {matched_sop.get('sop_name')}\n"
        sop_text += f"步骤: {matched_sop.get('steps')}"

    steps_text = "无"
    if executed_steps:
        steps_text = "\n".join([
            f"- {s.get('action')}: {s.get('explanation')}"
            for s in executed_steps[-5:]
        ])

    obs_text = current_observation or "无"

    config = load_prompt("action_agent")
    tool_whitelist = config.get('tool_whitelist', TOOL_WHITELIST)

    prompt = render_prompt(
        "action_agent",
        fault_info=fault_info,
        matched_sop=sop_text,
        executed_steps=steps_text,
        current_observation=obs_text,
        has_code=has_code,
        iteration_count=iteration_count,
        tool_whitelist=", ".join(tool_whitelist)
    )

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)
        content = response.content

        # 清理思考标签并提取JSON
        content = parse_json_from_response(content)
        actions = json.loads(content)

        # 过滤
        filtered = [a for a in actions if a.get("action") in tool_whitelist]
        filtered = ensure_required_actions(filtered, has_code, executed_steps, matched_sop, is_root_cause_found)
        return filtered[:5]

    except Exception as e:
        print(f"LLM调用失败: {e}")
        return get_fallback_actions(matched_sop, has_code, is_root_cause_found)


def ensure_required_actions(
    actions: List[Dict],
    has_code: bool,
    executed_steps: List[Dict] = None,
    matched_sop: Optional[Dict] = None,
    is_root_cause_found: bool = False
) -> List[Dict]:
    """确保包含必要的动作，避免重复执行某些动作

    Args:
        actions: 当前候选动作列表
        has_code: 是否已生成代码
        executed_steps: 已执行的步骤列表
        matched_sop: 匹配的SOP（版本5新增）
    """
    action_names = [a.get("action") for a in actions]
    executed_actions = []
    if executed_steps:
        executed_actions = [s.get("action") for s in executed_steps]

    # 版本7修复：初始场景下强制添加match_sop
    # 初始场景：没有matched_sop且没有已执行的步骤
    is_initial_scene = matched_sop is None and len(executed_actions) == 0

    # 版本7.1修复：如果matched_sop为None（未匹配到SOP），应该选择generate_sop而不是match_sop
    # 先移除可能存在的match_sop，确保不会重复匹配
    if matched_sop is None:
        actions = [a for a in actions if a.get("action") != "match_sop"]

    if is_initial_scene and matched_sop is not None and "match_sop" not in action_names:
        # 只有matched_sop存在时才添加match_sop
        match_sop_action = {"action": "match_sop", "explanation": "首先匹配SOP知识库，获取标准化故障处理流程"}
        actions.insert(0, match_sop_action)

    # 只检查是否执行过run_sop（避免重复执行SOP）
    has_run_sop = "run_sop" in executed_actions

    # 如果已经执行过run_sop，从候选中移除它
    if has_run_sop:
        actions = [a for a in actions if a.get("action") != "run_sop"]

    # 版本5：没有匹配到SOP时，添加generate_sop动作
    has_generate_sop = "generate_sop" in executed_actions

    if not matched_sop and not has_generate_sop and "generate_sop" not in action_names:
        actions.insert(0, {"action": "generate_sop", "explanation": "没有匹配到SOP，自动生成新SOP"})

    # 版本7修复：如果已经生成代码，移除generate_code动作
    if has_code:
        actions = [a for a in actions if a.get("action") != "generate_code"]

    if not has_code and "generate_code" not in action_names:
        actions.insert(0, {"action": "generate_code", "explanation": "生成可执行代码进行故障诊断"})
    elif has_code and not has_run_sop and "run_sop" not in action_names:
        # 只有未执行过run_sop时才添加
        actions.insert(0, {"action": "run_sop", "explanation": "执行已生成的代码获取观测结果"})

    # 版本7修复：检查是否已执行过match_observation
    has_match_observation = "match_observation" in executed_actions

    # 如果已经执行过match_observation，强制从候选中移除它
    if has_match_observation:
        actions = [a for a in actions if a.get("action") != "match_observation"]
        # 如果过滤后没有动作了，添加默认动作
        if not actions:
            actions = [
                {"action": "get_relevant_metric", "explanation": "获取服务指标数据"},
                {"action": "pod_analyze", "explanation": "分析Pod状态"}
            ]

    # 如果已执行run_sop但还没有执行match_observation，添加它
    if has_run_sop and not has_match_observation:
        # 满足论文条件：已执行run_sop + 尚未匹配历史故障
        match_obs_action = {"action": "match_observation", "explanation": "获取历史故障参考，辅助根因判定"}

        # 移除可能重复的match_observation
        actions = [a for a in actions if a.get("action") != "match_observation"]
        # 插入到最前面
        actions.insert(0, match_obs_action)
        # 只保留前2个动作
        actions = actions[:2]

    # 版本9修复：JudgeAgent判定找到根因后，强制在候选动作中加入generate_report
    if is_root_cause_found and "generate_report" not in action_names:
        actions = [a for a in actions if a.get("action") != "generate_report"]
        actions.insert(0, {
            "action": "generate_report",
            "explanation": "JudgeAgent已判定找到根因，建议生成最终报告并结束排查"
        })
        actions = actions[:3]

    return actions


def get_fallback_actions(matched_sop: Optional[Dict], has_code: bool, is_root_cause_found: bool = False) -> List[Dict[str, str]]:
    """兜底动作生成"""
    actions = []

    # 版本9：JudgeAgent已找到根因时，优先提供generate_report
    if is_root_cause_found:
        actions.append({"action": "generate_report", "explanation": "JudgeAgent已判定找到根因，生成最终报告并结束排查"})

    if not has_code:
        actions.append({"action": "generate_code", "explanation": "生成可执行代码"})
    else:
        actions.append({"action": "run_sop", "explanation": "执行SOP代码"})

    if matched_sop and matched_sop.get("steps"):
        for step in matched_sop["steps"]:
            tool = step.get("tool_name")
            if tool in TOOL_WHITELIST and tool not in ["generate_code", "run_sop"]:
                actions.append({"action": tool, "explanation": f"执行SOP步骤: {step.get('description')}"})

    if len(actions) < 2:
        actions.append({"action": "pod_analyze", "explanation": "分析Pod状态获取基础信息"})
        actions.append({"action": "get_relevant_metric", "explanation": "获取相关指标"})

    return actions[:5]
