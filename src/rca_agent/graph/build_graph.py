"""
build_graph.py - Graph编译、入口封装
版本6: 沙箱安全执行 + 完整防死循环与审计
版本7修复: 移除硬编码前置节点，match_sop/match_observation由ActionAgent决策执行
版本7.1: 添加LangSmith支持
"""

import sys
from langgraph.graph import StateGraph, END
from .state import RCAState
from .nodes import (
    match_sop_node,
    generate_sop_node,
    match_observation_node,
    action_agent_node,
    main_agent_node,
    code_agent_node,
    tool_executor_node,
    ob_agent_node,
    judge_agent_node,
    generate_report_node,
    route_after_main_agent,
    route_after_judge_agent
)


def create_rca_graph():
    graph = StateGraph(RCAState)

    graph.add_node("match_sop", match_sop_node)
    graph.add_node("generate_sop", generate_sop_node)
    graph.add_node("match_observation", match_observation_node)
    graph.add_node("action_agent", action_agent_node)
    graph.add_node("main_agent", main_agent_node)
    graph.add_node("code_agent", code_agent_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("ob_agent", ob_agent_node)
    graph.add_node("judge_agent", judge_agent_node)
    graph.add_node("generate_report", generate_report_node)

    # 设置入口点 - 先尝试匹配SOP，匹配失败再生成
    graph.set_entry_point("match_sop")

    # 流程边
    # 1. action_agent -> main_agent
    graph.add_edge("action_agent", "main_agent")

    # 2. main_agent -> (code_agent 或 tool_executor) 条件边
    graph.add_conditional_edges(
        "main_agent",
        route_after_main_agent,
        {
            "code_agent": "code_agent",
            "generate_sop": "generate_sop",
            "tool_executor": "tool_executor",
            "match_sop": "match_sop",
            "match_observation": "match_observation",
            "generate_report": "generate_report"  # 版本9：JudgeAgent判定根因后，由MainAgent选择生成报告
        }
    )

    # 3. generate_sop -> action_agent (生成SOP后重新生成动作集)
    # 版本8.1回调修正：所有工具执行完毕统一流向action_agent，保持MAS统一循环
    # Rule A硬性检查保留在main_agent.py中作为兜底
    graph.add_edge("generate_sop", "action_agent")

    # 4. match_sop -> action_agent (匹配完SOP后重新生成动作集)
    graph.add_edge("match_sop", "action_agent")

    # 4. match_observation -> ob_agent (匹配完历史故障后必须提取线索，版本5论文设计)
    graph.add_edge("match_observation", "ob_agent")

    # 5. code_agent -> action_agent (生成代码后重新生成动作集)
    graph.add_edge("code_agent", "action_agent")

    # 6. tool_executor -> action_agent (版本8修复：执行完毕无条件交回大脑)
    graph.add_edge("tool_executor", "action_agent")

    # 7. ob_agent -> judge_agent
    graph.add_edge("ob_agent", "judge_agent")

    # 8. judge_agent -> (action_agent 或 generate_report 或 match_sop) 条件边
    # 版本9修复：检查 should_terminate，如果为 True 则终止流程生成报告
    # 版本9.1修复：添加 match_sop 目标以支持收敛机制
    graph.add_conditional_edges(
        "judge_agent",
        route_after_judge_agent,
        {
            "action_agent": "action_agent",
            "generate_report": "generate_report",
            "match_sop": "match_sop"  # 版本9.1：收敛机制，回到match_sop用细化问题重新匹配
        }
    )

    # 9. generate_report -> 结束
    graph.add_edge("generate_report", END)

    # 编译图（版本7.1：添加LangSmith支持）
    from ..utils.config_loader import load_config
    config = load_config()
    langsmith_config = config.get('langsmith', {})

    compile_kwargs = {}
    if langsmith_config.get('enabled', False):
        import os
        api_key = langsmith_config.get('api_key', '')
        if api_key:
            os.environ["LANGCHAIN_API_KEY"] = api_key
        project_name = langsmith_config.get('project_name', 'SOPRCA-RCA')
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name
        print(f"LangSmith已启用，项目: {project_name}", file=sys.stderr)

    return graph.compile(**compile_kwargs)


def run_rca(fault_info: str) -> RCAState:
    """运行RCA流程"""
    rca_graph = create_rca_graph()

    initial_state: RCAState = {
        "fault_info": fault_info,
        "matched_sop": None,
        # 版本5新增：双知识库
        "similar_history_faults": None,
        "new_generated_sop": None,
        # 动作选择
        "candidate_action_set": None,
        "selected_action": None,
        # 执行结果
        "current_observation": None,
        # CodeAgent
        "generated_code": None,
        # ObAgent
        "extracted_clues": None,
        # JudgeAgent
        "judge_result": None,
        # 执行记录
        "executed_steps": [],
        "iteration_count": 0,
        "consecutive_no_gain": 0,
        # 版本6新增：防死循环与审计
        "action_history": [],
        "global_start_time": None,
        "should_terminate": False,
        # 版本7新增：论文强制步骤
        "need_match_observation": False,
        # 版本9新增：收敛机制
        "refined_problem_statement": None,
        # 最终结果
        "final_report": None
    }

    return rca_graph.invoke(initial_state)
