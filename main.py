"""
主入口文件 - 测试RCA流程
版本7: 工程化完善 + 论文效果复现准备
简化输出，显示配置信息
"""

from src.rca_agent.graph import create_rca_graph, RCAState
from src.rca_agent.utils.config_loader import load_config, get_llm_config, get_knowledge_base_config


def print_config():
    """打印当前配置信息"""
    import sys

    config = load_config()

    print("-" * 50, file=sys.stderr)
    print("当前配置", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    print(f"环境: {config.get('env', 'dev')}", file=sys.stderr)
    print(f"Mock模式: {'开启' if config.get('mock_mode') else '关闭'}", file=sys.stderr)

    # LLM配置
    llm_config = get_llm_config()
    print(f"模型: {llm_config.get('model', 'N/A')}", file=sys.stderr)
    print(f"温度: {llm_config.get('temperature', 'N/A')}", file=sys.stderr)

    # 知识库配置 - 使用实际路径
    from src.rca_agent.knowledge_base.sop_store import _get_kb_paths as get_sop_paths
    from src.rca_agent.knowledge_base.history_store import _get_kb_paths as get_history_paths

    sop_paths = get_sop_paths()
    history_paths = get_history_paths()

    print(f"SOP库: {sop_paths.get('SOP_DB_PATH', 'N/A')}", file=sys.stderr)
    print(f"历史库: {history_paths.get('HISTORY_DB_PATH', 'N/A')}", file=sys.stderr)
    print(f"向量库: {sop_paths.get('CHROMA_PATH', 'N/A')}", file=sys.stderr)

    print("-" * 50, file=sys.stderr)
    print(file=sys.stderr)


def run_rca_with_trace(fault_info: str):
    """运行RCA流程并输出每个环节的信息"""
    import time

    rca_graph = create_rca_graph()

    initial_state: RCAState = {
        "fault_info": fault_info,
        "matched_sop": None,
        # 版本5新增字段
        "similar_history_faults": None,
        "new_generated_sop": None,
        "candidate_action_set": None,
        "selected_action": None,
        "current_observation": None,
        "generated_code": None,
        "extracted_clues": None,
        "judge_result": None,
        "executed_steps": [],
        "iteration_count": 0,
        "consecutive_no_gain": 0,
        # 版本6新增字段
        "action_history": [],
        "global_start_time": time.time(),
        "should_terminate": False,
        # 版本7新增字段
        "need_match_observation": False,
        "final_report": None
    }

    print(f"故障输入: {fault_info}")
    print()

    current_state = initial_state
    step_num = 0
    start_time = time.time()

    # 用于统计
    action_set_list = []  # 记录所有Action Set

    # 使用stream逐步执行并输出每个节点的信息
    for step in rca_graph.stream(current_state):
        for step_name, step_output in step.items():
            step_num += 1
            print(f"[{step_num}] 节点: {step_name}")

            # 打印该节点的输出
            if step_name == "generate_sop":
                # 版本7.1新增：显示生成的SOP
                matched_sop = step_output.get("matched_sop")
                if matched_sop:
                    print(f"    -> 已生成SOP: {matched_sop.get('sop_name')}")
                    print(f"    -> 步骤数: {len(matched_sop.get('steps', []))}")
                    steps = matched_sop.get('steps', [])
                    if steps:
                        print(f"    -> SOP步骤明细:")
                        for step in steps:
                            print(f"        {step.get('step_num')}. {step.get('tool_name')}: {step.get('description')}")
                else:
                    print(f"    -> SOP生成失败")

            elif step_name == "match_sop":
                matched_sop = step_output.get("matched_sop")
                if matched_sop:
                    print(f"    -> 匹配到SOP: {matched_sop.get('sop_name')}")
                    print(f"    -> 步骤数: {len(matched_sop.get('steps', []))}")
                    # 显示SOP步骤明细
                    steps = matched_sop.get('steps', [])
                    if steps:
                        print(f"    -> SOP步骤明细:")
                        for s in steps:
                            print(f"        {s.get('step_num')}. {s.get('tool_name')}: {s.get('description')}")
                else:
                    print(f"    -> 未匹配到SOP")

            # 【新增1】显式显示 match_observation 步骤
            elif step_name == "match_observation":
                similar_history = step_output.get("similar_history_faults", [])
                new_sop = step_output.get("new_generated_sop")
                matched_sop = step_output.get("matched_sop")

                # 输出相似历史故障
                if similar_history:
                    print(f"    -> 相似历史故障: {len(similar_history)}个")
                    for i, hist in enumerate(similar_history, 1):
                        print(f"        [{i}] {hist.get('fault_info', 'N/A')}")
                        print(f"            相似度: {hist.get('similarity', 'N/A')}")
                        print(f"            故障类型: {hist.get('fault_type', 'N/A')}")
                        if hist.get('root_cause'):
                            print(f"            根因: {hist.get('root_cause')}")
                else:
                    print(f"    -> 无相似历史故障")

                # 输出新生成的SOP
                if new_sop:
                    print(f"    -> 自动生成新SOP: {new_sop.get('sop_name')}")
                elif matched_sop:
                    print(f"    -> 使用预定义SOP: {matched_sop.get('sop_name')}")

            # 【新增2】每次 Action Set 的完整内容
            elif step_name == "action_agent":
                actions = step_output.get("candidate_action_set", [])
                print(f"    -> Action Set 完整内容 ({len(actions)}个动作):")
                for i, a in enumerate(actions, 1):
                    print(f"        [{i}] action: {a.get('action')}")
                    print(f"            explanation: {a.get('explanation')}")
                # 记录用于统计
                action_set_list.append({
                    "step": step_num,
                    "actions": actions
                })

            elif step_name == "main_agent":
                selected = step_output.get("selected_action")
                if selected:
                    action = selected.get('action', '')
                    explanation = selected.get('explanation', '')[:80]
                    print(f"    -> 选中: {action}")
                    print(f"    -> 原因: {explanation}")

            elif step_name == "code_agent":
                code = step_output.get("generated_code", "")
                if code:
                    print(f"    -> 已生成代码 ({len(code)}字符)")
                    # 显示代码内容
                    print(f"    -> 生成代码内容:")
                    for line in code.split('\n'):
                        print(f"        {line}")

            elif step_name == "tool_executor":
                iteration = step_output.get("iteration_count", 0)
                executed = step_output.get("executed_steps", [])
                print(f"    -> 第{iteration}轮执行完成，共{len(executed)}步")

                # 【增强3】完整 SOP 执行步骤明细（每个 step 的 tool 结果）
                if executed:
                    print(f"    -> SOP执行步骤明细:")
                    for i, step in enumerate(executed, 1):
                        action = step.get('action', '')
                        result = step.get('result', '')
                        explanation = step.get('explanation', '')
                        print(f"        ┌─ Step {i}: {action}")
                        print(f"        │  解释: {explanation[:80] if explanation else 'N/A'}")
                        # 打印工具返回结果（格式化显示）
                        if result:
                            result_str = str(result)
                            # 格式化JSON结果
                            if result_str.startswith('{') or result_str.startswith('['):
                                try:
                                    import json
                                    result_obj = json.loads(result_str) if isinstance(result_str, str) else result_str
                                    if isinstance(result_obj, dict):
                                        print(f"        │  结果:")
                                        for k, v in list(result_obj.items())[:10]:
                                            v_str = str(v)[:100]
                                            print(f"        │    - {k}: {v_str}")
                                    else:
                                        print(f"        │    结果: {result_str[:200]}")
                                except:
                                    print(f"        │    结果: {result_str[:200]}")
                            else:
                                print(f"        │    结果: {result_str[:200]}")
                        else:
                            print(f"        │    结果: N/A")
                        print(f"        └─")

            elif step_name == "ob_agent":
                clues = step_output.get("extracted_clues", {})
                fault_type = clues.get('fault_type', '未知')
                location = clues.get('fault_location', '未知')
                key_clues = clues.get('key_clues', [])
                possible_causes = clues.get('possible_root_causes', [])
                excluded_causes = clues.get('excluded_root_causes', [])
                similar_history = clues.get('similar_history_faults', [])

                print(f"    -> 故障类型: {fault_type}")
                print(f"    -> 位置: {location}")

                # 显示历史相似故障
                if similar_history:
                    print(f"    -> 历史相似故障 ({len(similar_history)}个):")
                    for i, hist in enumerate(similar_history, 1):
                        sim = hist.get('similarity_score', 0)
                        hist_root = hist.get('root_cause', 'N/A')
                        if sim:
                            print(f"        [{i}] 相似度: {sim:.2f} - 根因: {hist_root[:80]}...")
                        else:
                            print(f"        [{i}] 根因: {hist_root[:80]}...")

                if key_clues:
                    print(f"    -> 关键线索 ({len(key_clues)}条):")
                    for i, clue in enumerate(key_clues, 1):
                        print(f"        {i}. {clue}")
                if possible_causes:
                    print(f"    -> 可能根因 ({len(possible_causes)}个):")
                    for i, cause in enumerate(possible_causes, 1):
                        print(f"        {i}. {cause}")
                if excluded_causes:
                    print(f"    -> 已排除根因 ({len(excluded_causes)}个):")
                    for i, cause in enumerate(excluded_causes, 1):
                        print(f"        {i}. {cause}")

            elif step_name == "judge_agent":
                result = step_output.get("judge_result", {})
                no_gain = step_output.get("consecutive_no_gain", 0)
                is_found = result.get('is_root_cause_found', False)
                explanation = result.get('explanation', '')

                print(f"    -> 找到根因: {'是' if is_found else '否'}")
                print(f"    -> 无增益次数: {no_gain}")
                if explanation:
                    print(f"    -> 判定说明:")
                    for line in explanation.split('\n'):
                        if line.strip():
                            print(f"        {line.strip()}")

            elif step_name == "generate_report":
                print(f"    -> 报告已生成")

            print()

            # 更新状态（版本7.1修复：检查step_output是否为None）
            if step_output:
                current_state = {**current_state, **step_output}

    # 【论文指标】计算（不输出，仅用于统计）
    end_time = time.time()
    total_time = end_time - start_time
    total_steps = step_num
    main_agent_decisions = current_state.get('iteration_count', 0)

    return current_state


def main():
    import sys
    #fault_info = "productcatalogservice CPU过高"#1.1
    fault_info = "cartservice 出现严重的 TCP 阻塞和未知网络延迟，导致结账请求超时"#1.2
    #fault_info = "cartservice 出现严重的 TCP 阻塞和未知网络延迟，导致结账请求超时"
    #fault_info = "frontend 服务响应极其缓慢，页面加载卡顿"
    #fault_info = "frontend 页面报错，提示调用外部第三方支付网关 external-credit-card-api 发生 502 Bad Gateway 错误，疑似外部网络或者第三方服务宕机"
    #fault_info = "外星人攻打麒麟软件了"

    # 先打印配置信息
    print_config()

    print("开始RCA故障分析...", file=sys.stderr)
    print(file=sys.stderr)

    result = run_rca_with_trace(fault_info)

    print("-" * 50, file=sys.stderr)
    print("分析完成", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    # 最终报告
    print()
    print("--- 根因报告 ---")
    print(result.get("final_report", "无"))


if __name__ == "__main__":
    main()
