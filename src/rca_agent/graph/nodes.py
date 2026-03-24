"""
nodes.py - 所有节点的统一注册
版本6: 沙箱安全执行 + 完整防死循环与审计
"""

import sys
import time
from typing import Dict, Any, List
from .state import RCAState
from ..agents.action_agent import generate_candidate_actions
from ..agents.main_agent import select_action
from ..agents.code_agent import generate_code
from ..agents.ob_agent import extract_clues
from ..agents.judge_agent import judge_root_cause
from ..tools import execute_tool
from ..knowledge_base.sop_store import match_sop
from ..knowledge_base.history_store import match_history_faults, init_history_knowledge_base
from ..knowledge_base.generate_sop import generate_sop as generate_sop_tool
from ..utils.logger import AuditLogger


def match_sop_node(state: RCAState) -> Dict[str, Any]:
    """节点: 匹配SOP

    版本8修复：只有当匹配到新的或不同的SOP时才重置状态
    """
    AuditLogger.log_node_entry("match_sop", state)

    fault_info = state.get("fault_info", "")
    current_sop = state.get("matched_sop", {})
    current_sop_id = current_sop.get("sop_id") if current_sop else None

    print(f"    [MatchSOP] 开始匹配SOP...", file=sys.stderr)
    print(f"    [MatchSOP] 故障信息: {fault_info}", file=sys.stderr)
    print(f"    [MatchSOP] 当前SOP: {current_sop.get('sop_name', '无') if current_sop else '无'}", file=sys.stderr)

    matched_sop = match_sop(fault_info)

    if matched_sop:
        matched_sop_id = matched_sop.get("sop_id")
        is_new_sop = current_sop_id != matched_sop_id

        print(f"    [MatchSOP] 匹配成功!", file=sys.stderr)
        print(f"    [MatchSOP]   SOP名称: {matched_sop.get('sop_name', 'N/A')}", file=sys.stderr)
        print(f"    [MatchSOP]   故障类型: {matched_sop.get('fault_type', 'N/A')}", file=sys.stderr)
        print(f"    [MatchSOP]   SOP ID: {matched_sop_id}", file=sys.stderr)
        steps = matched_sop.get('steps', [])
        print(f"    [MatchSOP]   步骤数: {len(steps)}", file=sys.stderr)
        print(f"    [MatchSOP]   是否新SOP: {is_new_sop}", file=sys.stderr)

        # 版本8.1回调修正：只有匹配到新的或不同的SOP时才重置状态
        # 注意：保留 action_history 和 iteration_count，维护全局试错记忆
        if is_new_sop:
            result = {
                "matched_sop": matched_sop,
                "generated_code": "",  # 清空旧代码，迫使重新生成
                # 版本8修复：不再清空executed_steps，保留执行记忆防止死循环
                "consecutive_no_gain": 0,
                # 保留 action_history 和 iteration_count
            }
            print(f"    [MatchSOP] 新SOP已匹配，状态已重置（保留action_history和iteration_count）", file=sys.stderr)
        else:
            # 同SOP不重置状态，保留已有的执行进度
            result = {
                "matched_sop": matched_sop
            }
            print(f"    [MatchSOP] 同SOP不重置状态", file=sys.stderr)
    else:
        print(f"    [MatchSOP] 未匹配到SOP，将触发自动生成", file=sys.stderr)
        # 未匹配到SOP也重置（因为无法继续当前SOP流程）
        # 版本8修复：保留 executed_steps，维护执行记忆
        result = {
            "matched_sop": matched_sop,
            "generated_code": "",
            "consecutive_no_gain": 0,
            # 保留 action_history 和 iteration_count
        }

    AuditLogger.log_node_exit("match_sop", result)
    return result


def generate_sop_node(state: RCAState) -> Dict[str, Any]:
    """节点: 生成SOP（版本7新增）

    当MainAgent选择generate_sop动作时调用此节点
    版本8修复：生成新SOP后必须强制重置状态，迫使重新走代码生成流程
    """
    AuditLogger.log_node_entry("generate_sop", state)

    fault_info = state.get("fault_info", "")
    similar_history_faults = state.get("similar_history_faults", [])

    print(f"    [GenerateSOP] 开始生成SOP...", file=sys.stderr)
    print(f"    [GenerateSOP] 故障信息: {fault_info}", file=sys.stderr)
    if similar_history_faults:
        print(f"    [GenerateSOP] 参考历史故障数: {len(similar_history_faults)}", file=sys.stderr)
    print(f"    [GenerateSOP] 调用LLM生成SOP...", file=sys.stderr)

    # 调用SOP生成工具
    from ..knowledge_base.generate_sop import generate_sop as generate_sop_tool
    new_sop = generate_sop_tool(
        fault_info=fault_info,
        similar_history_faults=similar_history_faults,
        similar_sops=None
    )

    if new_sop:
        print(f"    [GenerateSOP] SOP生成完成!", file=sys.stderr)
        print(f"    [GenerateSOP]   名称: {new_sop.get('sop_name', 'N/A')}", file=sys.stderr)
        print(f"    [GenerateSOP]   故障类型: {new_sop.get('fault_type', 'N/A')}", file=sys.stderr)
        steps = new_sop.get('steps', [])
        print(f"    [GenerateSOP]   步骤数: {len(steps)}", file=sys.stderr)

        # 版本8修复：只重置代码生成相关状态，保留全局执行记忆
        result = {
            "matched_sop": new_sop,
            "generated_code": "",  # 清空旧代码，迫使重新生成
            # 版本8修复：不再清空executed_steps，保留执行记忆防止死循环
            "consecutive_no_gain": 0,
            # 注意：保留 action_history 和 iteration_count，维护全局试错记忆和死循环保护
        }
        print(f"    [GenerateSOP] 状态已重置：generated_code=''（保留executed_steps/action_history/iteration_count）", file=sys.stderr)
    else:
        print(f"    [GenerateSOP] SOP生成失败!", file=sys.stderr)
        result = {
            "matched_sop": new_sop
        }

    AuditLogger.log_node_exit("generate_sop", result)
    return result


def match_observation_node(state: RCAState) -> Dict[str, Any]:
    """节点: 匹配相似历史故障（版本5新增）"""
    AuditLogger.log_node_entry("match_observation", state)

    fault_info = state.get("fault_info", "")
    current_observation = state.get("current_observation", "")

    # 初始化历史知识库
    try:
        init_history_knowledge_base()
    except Exception as e:
        print(f"初始化历史知识库失败: {e}")

    # 如果有当前观测结果，匹配相似历史故障
    similar_history_faults = []
    if current_observation:
        # 1. 动态获取 State 中的变量，提供默认值防止 KeyError
        fault_info = state.get("fault_info", "")
        extracted_clues = state.get("extracted_clues", "")
        current_observation = state.get("current_observation", "")

        # 2. 健壮的动态拼接逻辑
        if extracted_clues:
            # 理想情况：ObAgent 已经提取了线索
            query = f"故障现象: {fault_info}\\n关键线索: {extracted_clues}"
            print(f"    [match_observation] 使用语义线索检索: {query[:100]}", file=sys.stderr)
        else:
            # Fallback 情况：利用初始故障信息 + 刚刚执行工具得到的原始观测数据
            # 使用 str() 强制转换以防数据是 dict，并截取前500字符防止查询过长
            obs_text = str(current_observation)[:500] if current_observation else "无"
            query = f"故障现象: {fault_info}\\n观测数据: {obs_text}"
            print(f"    [match_observation] 触发Fallback，结合 fault_info 与 current_observation 进行检索", file=sys.stderr)

        # 3. 使用动态生成的 query 进行检索
        similar_history_faults = match_history_faults(query, top_k=3)

    # 如果没有匹配到SOP，尝试生成新SOP
    matched_sop = state.get("matched_sop")
    new_generated_sop = None

    if not matched_sop and fault_info:
        # 基于故障信息生成新SOP
        new_generated_sop = generate_sop_tool(
            fault_info=fault_info,
            similar_history_faults=similar_history_faults,
            similar_sops=None
        )
        matched_sop = new_generated_sop

    # 版本7修复：记录已执行的 match_observation 动作到 executed_steps
    executed_steps = state.get("executed_steps", [])
    new_step = {
        "action": "match_observation",
        "explanation": "匹配历史故障案例，获取参考根因",
        "result": f"找到 {len(similar_history_faults)} 个相似历史故障"
    }
    executed_steps = executed_steps + [new_step]

    result = {
        "similar_history_faults": similar_history_faults,
        "new_generated_sop": new_generated_sop,
        "matched_sop": matched_sop,
        "executed_steps": executed_steps
    }

    AuditLogger.log_node_exit("match_observation", result)
    return result


def action_agent_node(state: RCAState) -> Dict[str, Any]:
    """节点: ActionAgent - 生成候选动作集"""
    AuditLogger.log_node_entry("action_agent", state)

    fault_info = state.get("fault_info", "")
    matched_sop = state.get("matched_sop")
    executed_steps = state.get("executed_steps", [])
    current_observation = state.get("current_observation")
    has_code = bool(state.get("generated_code", ""))  # 版本8.2修复：使用bool()而非is not None
    iteration_count = state.get("iteration_count", 0)

    print(f"", file=sys.stderr)
    print(f"    [ActionAgent] 生成候选动作集...", file=sys.stderr)
    print(f"    [ActionAgent]   故障信息: {fault_info}", file=sys.stderr)
    print(f"    [ActionAgent]   已匹配SOP: {'是' if matched_sop else '否'}", file=sys.stderr)
    print(f"    [ActionAgent]   已生成代码: {'是' if has_code else '否'}", file=sys.stderr)
    print(f"    [ActionAgent]   已执行步骤: {len(executed_steps)}", file=sys.stderr)

    # 版本9修复：从state中提取JudgeAgent判定结果，控制是否加入generate_report动作
    judge_result = state.get("judge_result", {})
    is_root_cause_found = judge_result.get("is_root_cause_found", False) if judge_result else False
    print(f"    [ActionAgent]   JudgeAgent已找到根因: {'是' if is_root_cause_found else '否'}", file=sys.stderr)

    candidate_actions = generate_candidate_actions(
        fault_info, matched_sop, executed_steps, current_observation,
        has_code=has_code, iteration_count=iteration_count,
        is_root_cause_found=is_root_cause_found
    )

    print(f"    [ActionAgent] 生成完成，共{len(candidate_actions)}个候选动作", file=sys.stderr)

    result = {"candidate_action_set": candidate_actions}
    AuditLogger.log_node_exit("action_agent", result)
    return result


def main_agent_node(state: RCAState) -> Dict[str, Any]:
    """节点: MainAgent - 选择最终动作"""
    AuditLogger.log_node_entry("main_agent", state)

    candidate_actions = state.get("candidate_action_set", [])
    fault_info = state.get("fault_info", "")
    iteration_count = state.get("iteration_count", 0)
    has_code = bool(state.get("generated_code", ""))  # 版本8.2修复：使用bool()而非is not None，避免空字符串被误判为有代码
    has_clues = state.get("extracted_clues") is not None
    has_judgment = state.get("judge_result") is not None
    has_matched_sop = state.get("matched_sop") is not None
    # 版本7新增：检查是否已执行过run_sop和match_observation
    executed_steps = state.get("executed_steps", [])
    has_run_sop = any(s.get("action") == "run_sop" for s in executed_steps)
    has_match_observation = any(s.get("action") == "match_observation" for s in executed_steps)

    # 版本8新增：获取上一步动作，用于路由规则
    last_action = executed_steps[-1].get("action") if executed_steps else None

    selected = select_action(
        candidate_actions,
        fault_info,
        iteration_count,
        has_code,
        has_clues,
        has_judgment,
        has_matched_sop,
        has_run_sop,
        has_match_observation,
        last_action=last_action
    )

    print(f"", file=sys.stderr)
    print(f"    [MainAgent] 选择动作...", file=sys.stderr)
    print(f"    [MainAgent]   候选动作数: {len(candidate_actions)}", file=sys.stderr)
    if selected:
        print(f"    [MainAgent]   选中: {selected.get('action', 'N/A')}", file=sys.stderr)
        print(f"    [MainAgent]   原因: {selected.get('explanation', 'N/A')[:100]}", file=sys.stderr)
    AuditLogger.log_action(selected.get("action", ""), selected.get("explanation", ""))

    result = {"selected_action": selected}
    AuditLogger.log_node_exit("main_agent", result)
    return result


def code_agent_node(state: RCAState) -> Dict[str, Any]:
    """节点: CodeAgent - 生成代码"""
    AuditLogger.log_node_entry("code_agent", state)

    matched_sop = state.get("matched_sop")
    fault_info = state.get("fault_info", "")

    print(f"    [CodeAgent] 开始生成代码...", file=sys.stderr)
    print(f"    [CodeAgent] 故障信息: {fault_info}", file=sys.stderr)
    if matched_sop:
        print(f"    [CodeAgent] 基于SOP: {matched_sop.get('sop_name', 'N/A')}", file=sys.stderr)
    print(f"    [CodeAgent] 调用CodeAgent生成代码...", file=sys.stderr)

    generated_code = generate_code(matched_sop, fault_info)

    print(f"    [CodeAgent] 代码生成完成，长度: {len(generated_code) if generated_code else 0}字符", file=sys.stderr)
    if generated_code:
        print(f"    [CodeAgent] 代码预览:", file=sys.stderr)
        for line in generated_code.split('\n')[:15]:
            print(f"        {line}", file=sys.stderr)
        if len(generated_code.split('\n')) > 15:
            print(f"        ... (共{len(generated_code.split(chr(10)))}行)", file=sys.stderr)

    result = {"generated_code": generated_code}
    AuditLogger.log_node_exit("code_agent", result)
    return result


def tool_executor_node(state: RCAState) -> Dict[str, Any]:
    """节点: ToolExecutor - 执行工具（版本6：沙箱执行）"""
    AuditLogger.log_node_entry("tool_executor", state)

    selected_action = state.get("selected_action")
    fault_info = state.get("fault_info", "")
    matched_sop = state.get("matched_sop")

    if not selected_action:
        return {
            "current_observation": "无选中动作",
            "iteration_count": state.get("iteration_count", 0) + 1
        }

    tool_name = selected_action.get("action")

    # 打印分隔线和执行信息
    print(f"", file=sys.stderr)
    print(f"═══════════════════════════════════════════", file=sys.stderr)
    print(f"  工具执行: {tool_name}", file=sys.stderr)
    print(f"═══════════════════════════════════════════", file=sys.stderr)

    # 执行工具（版本6：如果是run_sop，使用沙箱执行）
    if tool_name == "run_sop" and matched_sop:
        generated_code = state.get("generated_code", "")
        if generated_code:
            # 版本8：直接执行代码（跳过沙箱，因为kubectl本身有安全机制）
            print(f"    [执行] 直接执行SOP代码...", file=sys.stderr)
            print(f"    [执行] 故障信息: {fault_info}", file=sys.stderr)
            print(f"    [执行] SOP名称: {matched_sop.get('sop_name', 'N/A')}", file=sys.stderr)
            print(f"    [执行] 生成代码长度: {len(generated_code)}字符", file=sys.stderr)
            print(f"    [执行] 代码内容预览:", file=sys.stderr)
            for line in generated_code.split('\n')[:10]:
                print(f"        {line}", file=sys.stderr)

            try:
                # 导入真实工具函数
                from ..tools.metric_tools import get_relevant_metric as _get_metric
                from ..tools.k8s_tools import pod_analyze as _pod_analyze, check_events as _check_events, service_analyze as _service_analyze
                from ..tools.log_tools import get_pod_logs as _get_pod_logs

                # 预定义工具函数包装（避免名称冲突）
                tool_wrapper_code = f'''
def get_relevant_metric(fault_info):
    return _get_metric(fault_info)

def pod_analyze(fault_info):
    return _pod_analyze(fault_info)

def check_events(*args, **kwargs):
    return _check_events()

def service_analyze(fault_info):
    return _service_analyze(fault_info)

def get_pod_logs(fault_info):
    return _get_pod_logs(fault_info)
'''
                # 合并工具函数和生成的代码
                full_code = tool_wrapper_code + "\n" + generated_code

                # 将工具函数注入exec上下文
                exec_result = {
                    '_get_metric': _get_metric,
                    '_pod_analyze': _pod_analyze,
                    '_check_events': _check_events,
                    '_service_analyze': _service_analyze,
                    '_get_pod_logs': _get_pod_logs,
                }
                exec(full_code, exec_result)

                # 获取返回值
                if "run_sop" in exec_result:
                    result_val = exec_result["run_sop"](fault_info)
                    tool_result = {"success": True, "result": result_val}
                    print(f"    [执行] 代码执行成功，返回值: {str(result_val)[:200]}", file=sys.stderr)
                else:
                    tool_result = {"success": True, "result": "代码执行完成（无返回值）"}
                    print(f"    [执行] 代码执行成功", file=sys.stderr)

            except Exception as e:
                tool_result = {"success": False, "error": str(e)}
                print(f"    [执行] 代码执行失败: {str(e)[:100]}", file=sys.stderr)

            tool_result = str(tool_result)
        else:
            # 版本8.2修复：run_sop在没有代码时绝对不能使用mock数据，必须抛出明确错误
            error_msg = "致命错误：没有找到可执行的SOP代码，请先执行generate_code生成诊断代码"
            print(f"    [执行] {error_msg}", file=sys.stderr)
            tool_result = {"success": False, "error": error_msg}
    else:
        # 打印工具执行信息
        print(f"    [执行] 调用工具: {tool_name}", file=sys.stderr)
        from ..utils.config_loader import load_config
        config = load_config()
        mock_mode = config.get('mock_mode', True)
        print(f"    [执行] 模式: {'Mock' if mock_mode else '真实环境'}", file=sys.stderr)
        tool_result = execute_tool(tool_name, fault_info)
        if tool_result.get('error'):
            print(f"    [执行] 工具执行出错: {tool_result.get('error')[:100]}", file=sys.stderr)
        else:
            print(f"    [执行] 工具执行成功", file=sys.stderr)

    # 格式化观测结果
    observation = f"执行动作: {tool_name}\n"
    observation += f"解释: {selected_action.get('explanation')}\n"
    observation += f"结果: {tool_result}\n"

    # 更新已执行步骤
    executed_steps = state.get("executed_steps", [])
    new_step = {
        "action": tool_name,
        "explanation": selected_action.get("explanation"),
        "result": tool_result
    }
    executed_steps = executed_steps + [new_step]

    # 更新动作历史
    action_history = state.get("action_history", [])
    action_history = action_history + [{
        "action": tool_name,
        "params": {"fault_info": fault_info},
        "timestamp": time.time()
    }]

    result = {
        "current_observation": observation,
        "executed_steps": executed_steps,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "action_history": action_history
    }

    print(f"═══════════════════════════════════════════", file=sys.stderr)
    print(f"", file=sys.stderr)

    AuditLogger.log_node_exit("tool_executor", result)
    return result


def ob_agent_node(state: RCAState) -> Dict[str, Any]:
    """节点: ObAgent - 提取线索"""
    AuditLogger.log_node_entry("ob_agent", state)

    current_observation = state.get("current_observation", "")
    executed_steps = state.get("executed_steps", [])
    similar_history_faults = state.get("similar_history_faults", [])

    print(f"", file=sys.stderr)
    print(f"    [ObAgent] 开始提取线索...", file=sys.stderr)
    print(f"    [ObAgent] 已执行步骤数: {len(executed_steps)}", file=sys.stderr)

    # 将历史故障信息包含在观测结果中
    history_info = ""
    if similar_history_faults:
        history_info = "\n\n## 历史相似故障参考：\n"
        for i, hist in enumerate(similar_history_faults[:3], 1):
            history_info += f"- [{i}] {hist.get('fault_info', 'N/A')}\n"
            sim_score = hist.get('similarity_score')
            if sim_score is not None and isinstance(sim_score, (int, float)):
                history_info += f"  相似度: {sim_score:.2f}\n"
            else:
                history_info += "  相似度: N/A\n"
            history_info += f"  根因: {hist.get('root_cause', 'N/A')}\n"

    # 将历史信息附加到观测结果中
    enhanced_observation = current_observation + history_info

    extracted_clues = extract_clues(enhanced_observation, executed_steps)

    print(f"    [ObAgent] 线索提取完成!", file=sys.stderr)
    print(f"    [ObAgent]   故障类型: {extracted_clues.get('fault_type', 'N/A')}", file=sys.stderr)
    print(f"    [ObAgent]   故障位置: {extracted_clues.get('fault_location', 'N/A')}", file=sys.stderr)
    key_clues = extracted_clues.get('key_clues', [])
    print(f"    [ObAgent]   关键线索: {len(key_clues)}条", file=sys.stderr)
    possible_causes = extracted_clues.get('possible_root_causes', [])
    print(f"    [ObAgent]   可能根因: {len(possible_causes)}个", file=sys.stderr)

    # 将历史故障信息也添加到线索中
    if similar_history_faults:
        extracted_clues["similar_history_faults"] = similar_history_faults

    result = {"extracted_clues": extracted_clues}
    AuditLogger.log_node_exit("ob_agent", result)
    return result


def judge_agent_node(state: RCAState) -> Dict[str, Any]:
    """节点: JudgeAgent - 判定根因（版本6：完整防死循环）"""
    AuditLogger.log_node_entry("judge_agent", state)

    fault_info = state.get("fault_info", "")
    extracted_clues = state.get("extracted_clues", {})
    executed_steps = state.get("executed_steps", [])
    iteration_count = state.get("iteration_count", 0)
    consecutive_no_gain = state.get("consecutive_no_gain", 0)
    action_history = state.get("action_history", [])
    global_start_time = state.get("global_start_time")

    print(f"", file=sys.stderr)
    print(f"    [JudgeAgent] 开始根因判定...", file=sys.stderr)
    print(f"    [JudgeAgent]   迭代次数: {iteration_count}", file=sys.stderr)
    print(f"    [JudgeAgent]   无增益次数: {consecutive_no_gain}", file=sys.stderr)

    # 版本6：调用带防死循环的判定
    judge_result = judge_root_cause(
        fault_info,
        extracted_clues,
        executed_steps,
        iteration_count,
        consecutive_no_gain,
        max_iterations=10,
        action_history=action_history,
        global_start_time=global_start_time
    )

    is_root_cause_found = judge_result.get("is_root_cause_found", False)
    print(f"    [JudgeAgent]   找到根因: {'是' if is_root_cause_found else '否'}", file=sys.stderr)

    # 检查是否终止
    termination_reason = judge_result.get("termination_reason", "")
    should_terminate = is_root_cause_found or termination_reason != ""

    # 检查信息增益
    if not should_terminate:
        has_gain = check_information_gain(executed_steps, extracted_clues)
        new_no_gain = 0 if has_gain else consecutive_no_gain + 1

        if new_no_gain >= 3:
            should_terminate = True
            judge_result["explanation"] = "连续3轮无信息增益，强制终止"
        print(f"    [JudgeAgent]   本轮有增益: {'是' if has_gain else '否'}", file=sys.stderr)
    else:
        new_no_gain = 0

    print(f"    [JudgeAgent]   终止: {'是' if should_terminate else '否'}", file=sys.stderr)

    result = {
        "judge_result": judge_result,
        "consecutive_no_gain": new_no_gain,
        "should_terminate": should_terminate
    }

    AuditLogger.log_node_exit("judge_agent", result)
    return result


def check_information_gain(executed_steps: List[Dict], extracted_clues: Dict) -> bool:
    """检查本轮是否有信息增益"""
    if not executed_steps:
        return True

    current_key_clues = extracted_clues.get("key_clues", [])
    current_possible_causes = extracted_clues.get("possible_root_causes", [])

    if current_key_clues or current_possible_causes:
        return True

    return False


def generate_report_node(state: RCAState) -> Dict[str, Any]:
    """节点: 生成根因报告（版本7：论文格式）"""
    AuditLogger.log_node_entry("generate_report", state)

    fault_info = state.get("fault_info", "")
    matched_sop = state.get("matched_sop")
    new_generated_sop = state.get("new_generated_sop")
    executed_steps = state.get("executed_steps", [])
    extracted_clues = state.get("extracted_clues", {})
    judge_result = state.get("judge_result", {})
    similar_history_faults = state.get("similar_history_faults", [])

    # 保存新生成的SOP到知识库
    if new_generated_sop:
        try:
            from ..knowledge_base.history_store import add_sop_to_knowledgebase, init_history_knowledge_base
            import chromadb

            init_history_knowledge_base()
            chroma_client = chromadb.PersistentClient(path="data/chroma")

            sop_id = add_sop_to_knowledgebase(new_generated_sop, chroma_client)
            print(f"[知识库] 新SOP已保存: {sop_id}")
        except Exception as e:
            print(f"[知识库] 保存SOP失败: {e}")

    # 保存故障到历史知识库
    fault_id = None
    try:
        from ..knowledge_base.history_store import add_fault_to_history, init_history_knowledge_base
        init_history_knowledge_base()

        observation = ""
        if extracted_clues:
            observation += f"故障类型: {extracted_clues.get('fault_type', '未知')}\n"
            observation += f"故障位置: {extracted_clues.get('fault_location', '未知')}\n"
            observation += f"关键线索: {extracted_clues.get('key_clues', [])}\n"
            observation += f"可能根因: {extracted_clues.get('possible_root_causes', [])}"

        root_cause = judge_result.get('explanation', '') if judge_result else ''
        fault_type = extracted_clues.get('fault_type', '未知') if extracted_clues else '未知'

        fault_id = add_fault_to_history(
            fault_info=fault_info,
            fault_type=fault_type,
            observation=observation,
            root_cause=root_cause,
            sop_id=matched_sop.get('sop_id') if matched_sop else None,
            matched_sop_name=matched_sop.get('sop_name') if matched_sop else None,
            is_generated_sop=1 if new_generated_sop else 0
        )
        print(f"[知识库] 历史故障已保存: {fault_id}")
    except Exception as e:
        print(f"[知识库] 保存历史故障失败: {e}")

    # 构建诊断路径（APL计算）
    action_names = [s.get('action') for s in executed_steps]
    diagnostic_path = " → ".join(action_names) if action_names else "无"
    apl = len(executed_steps)

    # 构建历史参考
    history_ref = ""
    if similar_history_faults:
        for i, hist in enumerate(similar_history_faults[:3], 1):
            hist_id = hist.get('fault_id', 'N/A')
            hist_sim = hist.get('similarity_score', 0)  # 修复：使用 similarity_score 而不是 similarity
            hist_root = hist.get('root_cause', 'N/A')
            # 评估相似度等级
            if hist_sim >= 0.9:
                similarity_desc = "高度一致"
            elif hist_sim >= 0.7:
                similarity_desc = "中度相似"
            else:
                similarity_desc = "略有参考价值"
            history_ref += f"Top-{i}：{hist_id}（相似度 {hist_sim:.2f}）—— 历史根因：{hist_root}（{similarity_desc}）\n"

    # 获取最终根因
    final_root_cause = ""
    if extracted_clues and extracted_clues.get('possible_root_causes'):
        final_root_cause = extracted_clues.get('possible_root_causes', [])[0]

    # 生成报告（论文格式，无分割线）
    report = f"""# 根因分析报告（Flow-of-Action SOP 架构 v7）

**故障信息**  \n{fault_info}

**匹配SOP**  \n"""
    if matched_sop:
        sop_id = matched_sop.get('sop_id', 'N/A')
        sop_name = matched_sop.get('sop_name', 'N/A')
        steps_count = len(matched_sop.get('steps', []))
        report += f"{sop_id}：{sop_name}（{steps_count}步）\n"
    else:
        report += "未匹配到SOP\n"

    # 诊断路径
    report += f"\n**诊断路径（APL = {apl}）**  \n{diagnostic_path}\n"

    # 历史参考
    if history_ref:
        report += f"\n**历史相似故障参考（match_observation）**  \n{history_ref}"

    # ObAgent提取线索
    if extracted_clues:
        key_clues = extracted_clues.get('key_clues', [])
        excluded_causes = extracted_clues.get('excluded_root_causes', [])

        report += f"\n**ObAgent 提取线索**  \n"
        report += f"- 故障类型：{extracted_clues.get('fault_type', '未知')}\n"
        report += f"- 故障位置：{extracted_clues.get('fault_location', '未知')}\n"
        report += f"- 关键线索（{len(key_clues)}条）：\n"
        for clue in key_clues:
            report += f"  - {clue}\n"
        report += f"- 已排除根因（{len(excluded_causes)}条）：\n"
        for cause in excluded_causes:
            report += f"  - {cause}\n"

    # JudgeAgent根因判定
    is_root_cause_found = judge_result.get('is_root_cause_found', False) if judge_result else False

    if is_root_cause_found:
        report += f"\n**JudgeAgent 根因判定**  \n"
        report += f"已找到根因（三要素均满足）\n"

        # 详细判定说明
        explanation = judge_result.get('explanation', '') if judge_result else ''
        if explanation:
            report += f"- 判定依据：{explanation}\n"

        # 最终根因
        if final_root_cause:
            report += f"\n**最终根因**  \n"
            report += f"**{final_root_cause}**\n"

        # 修复建议
        suggested = judge_result.get('suggested_actions', []) if judge_result else []
        if suggested:
            report += f"\n**修复建议**  \n"
            for action in suggested:
                report += f"- {action}\n"
    else:
        # 未找到根因的情况
        report += f"\n**JudgeAgent 根因判定**  \n"
        report += f"未找到根因\n"
        explanation = judge_result.get('explanation', '') if judge_result else ''
        if explanation:
            report += f"- 判定说明：{explanation}\n"

        # 建议操作
        suggested = judge_result.get('suggested_actions', []) if judge_result else []
        if suggested:
            report += f"\n**建议操作**  \n"
            for action in suggested:
                report += f"- {action}\n"

        # 建议操作
        suggested = judge_result.get('suggested_actions', []) if judge_result else []
        if suggested:
            report += f"\n**建议操作**  \n"
            for action in suggested:
                report += f"- {action}\n"

    # 本次诊断贡献
    if fault_id:
        report += f"\n**本次诊断贡献**  \n已将完整诊断过程存入历史故障库（{fault_id}），供后续相似故障参考。\n"

    AuditLogger.log_node_exit("generate_report", {"final_report": report.strip()})
    return {"final_report": report.strip()}


# 路由函数
def route_after_main_agent(state: RCAState) -> str:
    """MainAgent之后的路由"""
    selected = state.get("selected_action", {})
    action = selected.get("action", "")

    if action == "generate_code":
        return "code_agent"
    elif action == "generate_sop":
        return "generate_sop"
    elif action == "match_sop":
        return "match_sop"
    elif action == "match_observation":
        return "match_observation"
    elif action == "generate_report":
        return "generate_report"
    else:
        return "tool_executor"


def route_after_tool_executor(state: RCAState) -> str:
    """ToolExecutor之后的路由

    版本8修复：ToolExecutor执行完毕后应无条件交回大脑(action_agent)重新决策
    ob_agent和judge_agent由match_observation和judge_agent的条件边触发
    """
    return "action_agent"


