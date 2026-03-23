"""
main_agent.py - 主智能体，仅负责最终动作决策
使用LLM从候选动作中选择最优动作
"""

import json
from typing import Dict, List, Any
from ..utils.llm_client import get_llm_client
from ..utils.prompt_loader import render_prompt
from ..utils import parse_json_from_response


def select_action(
    candidate_actions: List[Dict[str, str]],
    fault_info: str,
    iteration_count: int,
    has_code: bool,
    has_clues: bool,
    has_judgment: bool,
    has_matched_sop: bool = False,
    has_run_sop: bool = False,
    has_match_observation: bool = False,
    last_action: str = None
) -> Dict[str, str]:
    """MainAgent: 选择最优动作"""
    # 版本7修复：如果已经执行过match_observation，强制从候选中移除它
    action_names = [a.get("action") for a in candidate_actions]
    if has_match_observation and "match_observation" in action_names:
        candidate_actions = [a for a in candidate_actions if a.get("action") != "match_observation"]
        # 如果过滤后没有动作了，添加默认动作
        if not candidate_actions:
            candidate_actions = [
                {"action": "get_relevant_metric", "explanation": "获取服务指标数据"},
                {"action": "pod_analyze", "explanation": "分析Pod状态"}
            ]
        action_names = [a.get("action") for a in candidate_actions]

    # 版本8：格式化上一步动作
    last_action_text = f"上一步动作是: {last_action}" if last_action else "无（初始状态）"

    actions_text = ""
    for i, action in enumerate(candidate_actions, 1):
        actions_text += f"{i}. {action.get('action')}: {action.get('explanation')}\n"

    prompt = render_prompt(
        "main_agent",
        fault_info=fault_info,
        iteration_count=iteration_count,
        has_code=has_code,
        has_clues=has_clues,
        has_judgment=has_judgment,
        has_matched_sop=has_matched_sop,
        has_run_sop=has_run_sop,
        has_match_observation=has_match_observation,
        last_action=last_action_text,
        candidate_actions=actions_text
    )

    try:
        llm = get_llm_client()
        response = llm.invoke(prompt)
        content = response.content

        # 清理并提取JSON
        content = parse_json_from_response(content)
        selected = json.loads(content)

        # 版本7修复：验证选择的动作是否有效，如果已被过滤，强制选择第一个
        chosen_action = selected.get("action", "")
        if chosen_action not in action_names and candidate_actions:
            selected = candidate_actions[0]
            chosen_action = selected.get("action", "")

        # 版本7修复：如果LLM仍然选择match_observation（已被过滤），强制选择第一个
        if chosen_action == "match_observation" and candidate_actions:
            selected = candidate_actions[0]
            chosen_action = selected.get("action", "")

        # 版本7.1修复：如果候选中有generate_sop但LLM没选它，强制选择generate_sop
        if "generate_sop" in action_names and chosen_action != "generate_sop" and candidate_actions:
            # 找到generate_sop动作并选择它
            for action in candidate_actions:
                if action.get("action") == "generate_sop":
                    selected = action
                    break
            chosen_action = selected.get("action", "")

        # 版本8修复：强化规则A - generate_sop后必须选择generate_code
        if last_action == "generate_sop" and chosen_action != "generate_code":
            for action in candidate_actions:
                if action.get("action") == "generate_code":
                    selected = action
                    chosen_action = "generate_code"
                    print(f"[MainAgent] 强化规则A生效：上一步generate_sop，强制选择generate_code")
                    break

        return {
            "action": selected.get("action", candidate_actions[0].get("action")),
            "explanation": selected.get("explanation", "")
        }

    except Exception as e:
        print(f"MainAgent LLM调用失败: {e}")
        return select_fallback_action(candidate_actions, has_code)


def select_fallback_action(
    candidate_actions: List[Dict[str, str]],
    has_code: bool
) -> Dict[str, str]:
    """兜底动作选择"""
    if has_code:
        for action in candidate_actions:
            if action.get('action') == 'run_sop':
                return action

    return candidate_actions[0] if candidate_actions else {
        "action": "pod_analyze",
        "explanation": "默认动作"
    }
