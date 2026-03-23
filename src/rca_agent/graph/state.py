"""
State定义 - 全量State覆盖所有智能体输出字段
版本6: 沙箱安全执行 + 防死循环与审计
"""

from typing import TypedDict, Optional, List, Dict, Any


class RCAState(TypedDict):
    """
    RCA系统的核心状态结构

    # 基础信息
    - fault_info: 初始故障信息
    - matched_sop: 匹配到的SOP

    # 双知识库相关（版本5新增）
    - similar_history_faults: 相似历史故障列表
    - new_generated_sop: 新生成的SOP

    # 动作选择相关
    - candidate_action_set: 候选动作集
    - selected_action: 选中的动作

    # 执行结果
    - current_observation: 当前观测结果

    # CodeAgent
    - generated_code: 生成的代码

    # ObAgent
    - extracted_clues: 提取的故障线索

    # JudgeAgent
    - judge_result: 根因判定结果

    # 执行记录
    - executed_steps: 已执行的步骤
    - iteration_count: 循环次数
    - consecutive_no_gain: 连续无信息增益次数

    # 版本6新增：防死循环与审计
    - action_history: 动作历史记录
    - global_start_time: 流程启动时间
    - should_terminate: 是否应该终止

    # 最终结果
    - final_report: 最终根因报告
    """
    fault_info: str
    matched_sop: Optional[Dict[str, Any]]

    # 双知识库相关（版本5新增）
    similar_history_faults: Optional[List[Dict[str, Any]]]
    new_generated_sop: Optional[Dict[str, Any]]

    # 动作选择
    candidate_action_set: Optional[List[Dict[str, str]]]
    selected_action: Optional[Dict[str, str]]

    # 执行结果
    current_observation: Optional[str]

    # CodeAgent
    generated_code: Optional[str]

    # ObAgent
    extracted_clues: Optional[Dict[str, Any]]

    # JudgeAgent
    judge_result: Optional[Dict[str, Any]]

    # 执行记录
    executed_steps: List[Dict[str, Any]]
    iteration_count: int
    consecutive_no_gain: int

    # 版本6新增：防死循环与审计
    action_history: List[Dict[str, Any]]
    global_start_time: Optional[float]
    should_terminate: bool

    # 版本7新增：论文强制步骤 - run_sop后必须走match_observation
    need_match_observation: bool

    # 最终结果
    final_report: Optional[str]
