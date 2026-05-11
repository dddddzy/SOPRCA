"""
主入口文件 - 测试RCA流程
版本7: 工程化完善 + 论文效果复现准备
简化输出，显示配置信息

支持两种模式：
  python main.py              # CLI 模式
  python main.py --server     # HTTP 服务模式
"""

import argparse
import asyncio
import json
import queue
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
        # 版本9新增字段
        "refined_problem_statement": None,
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
    fault_info = "productcatalogservice CPU过高"#1.1
    #fault_info = "cartservice 出现严重的 TCP 阻塞和未知网络延迟，导致结账请求超时"#1.2
    #fault_info = "cartservice 出现严重的 TCP 阻塞和未知网络延迟，导致结账请求超时"
    #fault_info = "服务响应缓慢"
    #fault_info = "frontend 页面报错，提示调用外部第三方支付网关 external-credit-card-api 发生 502 Bad Gateway 错误，疑似外部网络或者第三方服务宕机"

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


def run_server():
    """启动 FastAPI HTTP 服务"""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI(title="SOPRCA API", version="1.0.0")

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class DiagnoseRequest(BaseModel):
        fault_info: str

    class ModelConfigRequest(BaseModel):
        apiEndpoint: str
        modelName: str
        apiKey: str
        temperature: float
        maxTokens: int

    class KnowledgeQARequest(BaseModel):
        question: str

    @app.get("/")
    async def root():
        return {"message": "SOPRCA API", "version": "1.0.0"}

    @app.get("/api/settings/model")
    async def get_model_config():
        """获取当前模型配置"""
        config = load_config()
        llm_config = config.get('llm', {})
        return {
            "apiEndpoint": llm_config.get('base_url', ''),
            "modelName": llm_config.get('model', ''),
            "apiKey": llm_config.get('api_key', ''),
            "temperature": llm_config.get('temperature', 0.7),
            "maxTokens": llm_config.get('max_tokens', 8192)
        }

    @app.post("/api/settings/model")
    async def save_model_config(req: ModelConfigRequest):
        """保存模型配置到 config.yaml"""
        import yaml

        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        # 读取现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 更新 LLM 配置
        if 'llm' not in config_data:
            config_data['llm'] = {}
        config_data['llm']['base_url'] = req.apiEndpoint
        config_data['llm']['model'] = req.modelName
        config_data['llm']['api_key'] = req.apiKey
        config_data['llm']['temperature'] = req.temperature
        config_data['llm']['timeout'] = 60
        config_data['llm']['max_retries'] = 2

        # 写回 config.yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        return {"success": True, "message": "配置已保存，重启后端服务后生效"}

    @app.post("/api/settings/model/test")
    async def test_model_connection(req: ModelConfigRequest):
        """测试模型连接"""
        from langchain_openai import ChatOpenAI

        try:
            llm = ChatOpenAI(
                model=req.modelName,
                api_key=req.apiKey,
                base_url=req.apiEndpoint,
                temperature=0.7,
                timeout=60,
                max_retries=2
            )
            # 发送一个简单的测试消息
            response = llm.invoke("Hello, please reply with 'OK' if you can understand me.")
            return {"success": True, "message": "连接成功", "response": str(response.content)}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    @app.get("/api/settings/cluster")
    async def get_cluster_config():
        """获取集群配置"""
        config = load_config()
        return {
            "server": config.get('kubeconfig', ''),
            "context": config.get('context', 'default'),
            "env": config.get('env', 'dev'),
            "mockMode": config.get('mock_mode', False)
        }

    @app.post("/api/settings/cluster")
    async def save_cluster_config(req: dict):
        """保存集群配置到 config.yaml"""
        import yaml

        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        config_data['kubeconfig'] = req.get('server', '')
        config_data['context'] = req.get('context', 'default')
        config_data['env'] = req.get('env', 'dev')
        config_data['mock_mode'] = req.get('mockMode', False)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        return {"success": True, "message": "配置已保存"}

    @app.get("/api/settings/anti-loop")
    async def get_anti_loop_config():
        """获取防死循环配置"""
        from src.rca_agent.utils.config_loader import get_loop_config
        config = get_loop_config()
        return {
            "success": True,
            "data": {
                "max_cycle_limit": config.get('max_cycle_limit', 20),
                "max_no_gain_times": config.get('max_no_gain_times', 3),
                "max_repeat_action_times": config.get('max_repeat_action_times', 2),
                "global_timeout": config.get('global_timeout', 600)
            }
        }

    @app.post("/api/settings/anti-loop")
    async def save_anti_loop_config(req: dict):
        """保存防死循环配置到 config.yaml"""
        import yaml
        import os

        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        if 'anti_loop' not in config_data:
            config_data['anti_loop'] = {}

        config_data['anti_loop']['max_cycle_limit'] = req.get('maxCycleLimit', 20)
        config_data['anti_loop']['max_no_gain_times'] = req.get('maxNoGainTimes', 3)
        config_data['anti_loop']['max_repeat_action_times'] = req.get('maxRepeatActionTimes', 2)
        config_data['anti_loop']['global_timeout'] = req.get('globalTimeout', 600)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        # 清除配置缓存，使其重新加载
        from src.rca_agent.utils import config_loader
        config_loader._config = None

        return {"success": True, "message": "防死循环配置已保存"}

    @app.get("/api/sops")
    async def get_sops():
        """获取所有SOP列表"""
        from src.rca_agent.knowledge_base.sop_store import init_sop_knowledge_base, get_sop_by_id, SOP_TABLE
        import sqlite3

        chroma_client = init_sop_knowledge_base()

        conn = sqlite3.connect('data/sop_knowledge.db')
        cursor = conn.cursor()

        cursor.execute(f"SELECT sop_id, sop_name, fault_type, description, steps, create_time, match_count FROM {SOP_TABLE}")
        rows = cursor.fetchall()
        conn.close()

        sops = []
        for row in rows:
            steps = json.loads(row[4]) if row[4] else []
            sops.append({
                "id": row[0],
                "name": row[1],
                "faultType": row[2],
                "description": row[3] or "",
                "steps": [{"order": s["step_num"], "tool": s["tool_name"], "description": s["description"]} for s in steps],
                "status": "active",  # 默认状态
                "createdAt": row[5],
                "updatedAt": row[5],
                "matchCount": row[6] if row[6] else 0
            })

        return {"success": True, "data": sops}

    @app.get("/api/sops/{sop_id}")
    async def get_sop(sop_id: str):
        """获取单个SOP详情"""
        from src.rca_agent.knowledge_base.sop_store import get_sop_by_id

        sop = get_sop_by_id(sop_id)
        if not sop:
            return {"success": False, "message": "SOP不存在"}

        steps = sop.get('steps', [])
        return {
            "success": True,
            "data": {
                "id": sop['sop_id'],
                "name": sop['sop_name'],
                "faultType": sop['fault_type'],
                "description": sop.get('description', ''),
                "steps": [{"order": s["step_num"], "tool": s["tool_name"], "description": s["description"]} for s in steps],
                "status": "active",
                "createdAt": sop.get('create_time', ''),
                "updatedAt": sop.get('create_time', ''),
                "matchCount": 0
            }
        }

    @app.put("/api/sops/{sop_id}")
    async def update_sop(sop_id: str, req: dict):
        """更新SOP"""
        from src.rca_agent.knowledge_base.sop_store import add_sop_to_knowledgebase, init_sop_knowledge_base, _get_kb_paths
        import sqlite3

        init_sop_knowledge_base()
        kb_paths = _get_kb_paths()
        sop_db_path = kb_paths['SOP_DB_PATH']

        steps = req.get('steps', [])
        formatted_steps = [{"step_num": s["order"], "tool_name": s["tool"], "description": s["description"]} for s in steps]

        sop_data = {
            "sop_id": sop_id,
            "sop_name": req.get('name', '未命名'),
            "fault_type": req.get('faultType', '未知'),
            "description": req.get('description', ''),
            "steps": formatted_steps,
            "status": req.get('status', 'active')
        }

        add_sop_to_knowledgebase(sop_data, None)
        return {"success": True, "message": "SOP已更新"}

    @app.delete("/api/sops/{sop_id}")
    async def delete_sop(sop_id: str):
        """删除SOP"""
        from src.rca_agent.knowledge_base.sop_store import init_sop_knowledge_base, _get_kb_paths, SOP_TABLE
        import sqlite3

        init_sop_knowledge_base()
        kb_paths = _get_kb_paths()
        sop_db_path = kb_paths['SOP_DB_PATH']

        conn = sqlite3.connect(sop_db_path)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SOP_TABLE} WHERE sop_id = ?", (sop_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            return {"success": True, "message": "SOP已删除"}
        return {"success": False, "message": "SOP不存在"}

    # 历史案例 API
    @app.get("/api/history")
    async def get_history_cases():
        """获取所有历史案例"""
        from src.rca_agent.knowledge_base.history_store import HISTORY_TABLE
        import sqlite3

        conn = sqlite3.connect('data/history_knowledge.db')
        cursor = conn.cursor()

        cursor.execute(f"SELECT fault_id, fault_info, fault_type, root_cause, observation, matched_sop_name, create_time FROM {HISTORY_TABLE}")
        rows = cursor.fetchall()
        conn.close()

        cases = []
        for row in rows:
            cases.append({
                "id": row[0],
                "faultInfo": row[1],
                "faultType": row[2],
                "rootCause": row[3],
                "observation": row[4],
                "matchedSopName": row[5],
                "createdAt": row[6]
            })

        return {"success": True, "data": cases}

    @app.post("/api/history")
    async def create_history_case(req: dict):
        """创建新历史案例"""
        import uuid
        from src.rca_agent.knowledge_base.history_store import HISTORY_TABLE
        import sqlite3

        fault_id = f"FAULT-{uuid.uuid4().hex[:8]}"

        conn = sqlite3.connect('data/history_knowledge.db')
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {HISTORY_TABLE}
            (fault_id, fault_info, fault_type, root_cause, observation, matched_sop_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fault_id,
            req.get('faultInfo', ''),
            req.get('faultType', ''),
            req.get('rootCause', ''),
            req.get('observation', ''),
            req.get('matchedSopName', '')
        ))
        conn.commit()
        conn.close()
        return {"success": True, "message": "案例已创建", "id": fault_id}

    @app.put("/api/history/{fault_id}")
    async def create_sop(req: dict):
        """创建新SOP"""
        import uuid
        from src.rca_agent.knowledge_base.sop_store import add_sop_to_knowledgebase, init_sop_knowledge_base, _get_kb_paths
        import sqlite3

        init_sop_knowledge_base()
        kb_paths = _get_kb_paths()
        sop_db_path = kb_paths['SOP_DB_PATH']
        chroma_path = kb_paths['CHROMA_PATH']

        import chromadb
        chroma_client = chromadb.PersistentClient(path=chroma_path)

        sop_id = f"SOP-{uuid.uuid4().hex[:8]}"
        steps = req.get('steps', [])
        formatted_steps = [{"step_num": s["order"], "tool_name": s.get("tool", ""), "description": s.get("description", "")} for s in steps]

        sop_data = {
            "sop_id": sop_id,
            "sop_name": req.get('name', '未命名'),
            "fault_type": req.get('faultType', '未知'),
            "description": req.get('description', ''),
            "steps": formatted_steps
        }

        add_sop_to_knowledgebase(sop_data, chroma_client)
        return {"success": True, "message": "SOP已创建", "id": sop_id}

    @app.put("/api/history/{fault_id}")
    async def update_history_case(fault_id: str, req: dict):
        """更新历史案例"""
        from src.rca_agent.knowledge_base.history_store import HISTORY_TABLE
        import sqlite3

        conn = sqlite3.connect('data/history_knowledge.db')
        cursor = conn.cursor()

        cursor.execute(f"""
            UPDATE {HISTORY_TABLE}
            SET fault_info = ?, fault_type = ?, root_cause = ?, observation = ?, matched_sop_name = ?
            WHERE fault_id = ?
        """, (
            req.get('faultInfo', ''),
            req.get('faultType', ''),
            req.get('rootCause', ''),
            req.get('observation', ''),
            req.get('matchedSopName', ''),
            fault_id
        ))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            return {"success": True, "message": "案例已更新"}
        return {"success": False, "message": "案例不存在"}

    @app.delete("/api/history/{fault_id}")
    async def delete_history_case(fault_id: str):
        """删除历史案例"""
        from src.rca_agent.knowledge_base.history_store import HISTORY_TABLE
        import sqlite3

        conn = sqlite3.connect('data/history_knowledge.db')
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {HISTORY_TABLE} WHERE fault_id = ?", (fault_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            return {"success": True, "message": "案例已删除"}
        return {"success": False, "message": "案例不存在"}

    # 知识问答 API
    @app.post("/api/knowledge/qa")
    async def knowledge_qa(req: KnowledgeQARequest):
        """知识问答 - 基于SOP和历史案例回答问题"""
        from src.rca_agent.knowledge_base.sop_store import search_sop_by_vector, get_sop_by_id, SOP_TABLE
        from src.rca_agent.knowledge_base.history_store import match_history_faults, HISTORY_TABLE
        from src.rca_agent.utils.llm_client import get_llm_client
        import sqlite3
        import json

        question = req.question
        if not question:
            return {"success": False, "message": "问题不能为空"}

        # 1. 检索SOP知识库
        sops = []
        sop_collection_data = []
        try:
            conn = sqlite3.connect('data/sop_knowledge.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT sop_id, sop_name, fault_type, description, steps FROM {SOP_TABLE}")
            for row in cursor.fetchall():
                steps = json.loads(row[4]) if row[4] else []
                sop_text = f"{row[1]} {row[2]} {row[3] or ''}"
                sops.append({
                    "id": row[0],
                    "name": row[1],
                    "faultType": row[2],
                    "description": row[3] or '',
                    "steps": [{"order": s['step_num'], "tool": s['tool_name'], "description": s['description']} for s in steps],
                    "text": sop_text
                })
            conn.close()
        except Exception as e:
            print(f"[KnowledgeQA] SOP查询异常: {e}")

        # 2. 检索历史案例
        history_cases = []
        try:
            conn = sqlite3.connect('data/history_knowledge.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT fault_id, fault_info, fault_type, root_cause, observation FROM {HISTORY_TABLE}")
            for row in cursor.fetchall():
                history_cases.append({
                    "id": row[0],
                    "faultInfo": row[1],
                    "faultType": row[2],
                    "rootCause": row[3],
                    "observation": row[4] or ''
                })
            conn.close()
        except Exception as e:
            print(f"[KnowledgeQA] 历史案例查询异常: {e}")

        # 3. 简单的关键词匹配（更好的做法是用向量检索）
        relevant_sops = []
        relevant_history = []

        question_lower = question.lower()

        # SOP关键词匹配
        for sop in sops:
            if any(kw in sop['text'].lower() for kw in ['cpu', '内存', '网络', 'pod', '磁盘', '延迟', '重启', '500', '502', '故障']):
                relevant_sops.append(sop)

        # 历史案例关键词匹配
        for case in history_cases:
            text = f"{case['faultInfo']} {case['faultType']} {case['observation']}".lower()
            if any(kw in text for kw in ['cpu', '内存', '网络', 'pod', '磁盘', '延迟', '重启', '500', '502', '故障']):
                relevant_history.append(case)

        # 如果没有匹配，返回提示
        if not relevant_sops and not relevant_history:
            return {
                "success": True,
                "answer": "抱歉，我在知识库中没有找到与您问题相关的信息。您可以尝试询问关于CPU过高、内存泄漏、网络故障、Pod异常等常见故障的诊断方法。",
                "citations": []
            }

        # 4. 构建上下文
        context_parts = []

        if relevant_sops:
            sop_context = "【SOP知识库】\n"
            for sop in relevant_sops[:3]:  # 最多3个
                sop_context += f"\n## {sop['name']} ({sop['faultType']})\n"
                sop_context += f"描述: {sop['description']}\n"
                if sop['steps']:
                    sop_context += "诊断步骤:\n"
                    for step in sop['steps']:
                        sop_context += f"  {step['order']}. {step['tool']}: {step['description']}\n"
            context_parts.append(sop_context)

        if relevant_history:
            history_context = "\n【历史案例库】\n"
            for case in relevant_history[:3]:  # 最多3个
                history_context += f"\n## {case['faultInfo']}\n"
                history_context += f"类型: {case['faultType']}\n"
                if case['observation']:
                    history_context += f"观测: {case['observation'][:200]}...\n"
                if case['rootCause']:
                    history_context += f"根因: {case['rootCause']}\n"
            context_parts.append(history_context)

        context = "\n".join(context_parts)

        # 5. 调用LLM生成回答
        try:
            llm = get_llm_client()
            prompt = f"""你是RCA智能问答助手，专门帮助用户解答运维和故障诊断相关的问题。

请根据以下知识库内容，用自然、友好的方式回答用户的问题。

---
【知识库内容】

{context}

---
【用户问题】
{question}

请像一位经验丰富的运维工程师一样，用简洁专业的语言回答问题。可以：
1. 直接给出有用的建议和步骤
2. 适当引用具体的案例或SOP来说明
3. 如果知识库中没有直接相关的信息，诚实告知并给出合理的推测建议

注意：
- 回答要自然流畅，不要生硬地罗列知识
- 可以用"根据xxx案例..."、"参考SOP《xxx》..."等自然过渡
- 适当总结归纳，不要照搬原文

回答:"""

            response = llm.invoke(prompt)
            answer = str(response.content) if hasattr(response, 'content') else str(response)

            # 构建引用列表
            citations = []
            for sop in relevant_sops[:3]:
                citations.append({"type": "sop", "name": sop['name'], "id": sop['id']})
            for case in relevant_history[:3]:
                citations.append({"type": "history", "name": case['faultInfo'], "id": case['id']})

            # 更新SOP匹配次数
            try:
                conn = sqlite3.connect('data/sop_knowledge.db')
                cursor = conn.cursor()
                for sop in relevant_sops[:3]:
                    cursor.execute(f"UPDATE {SOP_TABLE} SET match_count = match_count + 1 WHERE sop_id = ?", (sop['id'],))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[KnowledgeQA] 更新SOP匹配次数异常: {e}")

            return {
                "success": True,
                "answer": answer,
                "citations": citations,
                "relevantCount": len(relevant_sops) + len(relevant_history)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"生成回答失败: {str(e)}",
                "citations": []
            }

    @app.post("/api/diagnose")
    async def diagnose(req: DiagnoseRequest):
        """流式返回诊断步骤"""
        from fastapi.responses import StreamingResponse
        import time
        import sys
        import io
        from src.rca_agent.utils.logger import set_sse_log_callback, clear_sse_log_callback

        # 用于收集日志的队列
        from collections import deque
        import threading
        log_queue = deque()
        log_lock = threading.Lock()

        def sse_log_callback(log_msg: str):
            """SSE日志回调，将日志放入队列"""
            with log_lock:
                log_queue.append(log_msg)

        def generate():
            rca_graph = create_rca_graph()

            # 设置日志回调
            set_sse_log_callback(sse_log_callback)

            # 保存原始stderr
            old_stderr = sys.stderr
            # 创建自定义stderr来捕获所有输出
            stderr_capture = io.StringIO()

            try:
                # 重定向stderr到自定义捕获流
                sys.stderr = stderr_capture

                initial_state: RCAState = {
                    "fault_info": req.fault_info,
                    "matched_sop": None,
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
                    "action_history": [],
                    "global_start_time": time.time(),
                    "should_terminate": False,
                    "need_match_observation": False,
                    "refined_problem_statement": None,
                    "final_report": None
                }

                pending_logs = []

                # 流式输出每个步骤
                for step in rca_graph.stream(initial_state):
                    # 先读取stderr捕获的内容作为日志
                    stderr_content = stderr_capture.getvalue()
                    if stderr_content:
                        # 按行分割日志
                        for line in stderr_content.strip().split('\n'):
                            if line.strip():
                                pending_logs.append(line.strip())
                        # 清空捕获流
                        stderr_capture.truncate(0)
                        stderr_capture.seek(0)

                    # 先发送这段时间积累的日志
                    with log_lock:
                        while log_queue:
                            pending_logs.append(log_queue.popleft())

                    if pending_logs:
                        # 发送日志
                        for log_msg in pending_logs:
                            data = {
                                "type": "log",
                                "message": log_msg
                            }
                            yield json.dumps(data, ensure_ascii=False) + "\n"
                        pending_logs = []

                    # 发送节点输出
                    for step_name, step_output in step.items():
                        data = {
                            "step": step_name,
                            "output": {k: v for k, v in step_output.items() if v is not None}
                        }
                        yield json.dumps(data, ensure_ascii=False) + "\n"

                # 发送剩余日志
                stderr_content = stderr_capture.getvalue()
                if stderr_content:
                    for line in stderr_content.strip().split('\n'):
                        if line.strip():
                            pending_logs.append(line.strip())

                with log_lock:
                    while log_queue:
                        pending_logs.append(log_queue.popleft())

                for log_msg in pending_logs:
                    data = {
                        "type": "log",
                        "message": log_msg
                    }
                    yield json.dumps(data, ensure_ascii=False) + "\n"

                # 发送完成信号
                yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

            finally:
                # 恢复原始stderr
                sys.stderr = old_stderr
                # 清除日志回调
                clear_sse_log_callback()

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.post("/api/monitor/toggle")
    async def monitor_toggle():
        """开关自动巡检"""
        from src.rca_agent.monitoring import get_monitor_service
        monitor = get_monitor_service()
        status = monitor.toggle()
        return {"success": True, "data": status}

    @app.get("/api/monitor/status")
    async def monitor_status():
        """获取巡检状态"""
        from src.rca_agent.monitoring import get_monitor_service
        monitor = get_monitor_service()
        return {"success": True, "data": monitor.get_status()}

    @app.get("/api/monitor/sse")
    async def monitor_sse():
        """SSE连接，用于接收自动巡检触发的诊断实时更新"""
        from fastapi.responses import StreamingResponse
        q: queue.Queue = queue.Queue()
        _sse_clients.add(q)

        async def generate():
            try:
                while True:
                    try:
                        item = q.get_nowait()
                        if item is None:
                            break
                        yield item
                    except queue.Empty:
                        # 没有数据时等待一小段时间，避免busy loop
                        await asyncio.sleep(0.1)
                        continue
            except asyncio.CancelledError:
                pass
            finally:
                _sse_clients.discard(q)

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.post("/api/monitor/thresholds")
    async def monitor_thresholds(req: dict):
        """更新阈值配置"""
        from src.rca_agent.monitoring import get_monitor_service
        monitor = get_monitor_service()
        if 'cpu_percent' in req:
            monitor.thresholds['cpu_percent'] = int(req['cpu_percent'])
        if 'memory_percent' in req:
            monitor.thresholds['memory_percent'] = int(req['memory_percent'])
        if 'disk_percent' in req:
            monitor.thresholds['disk_percent'] = int(req['disk_percent'])
        if 'restart_count' in req:
            monitor.thresholds['restart_count'] = int(req['restart_count'])
        return {"success": True, "data": monitor.thresholds}

    print("启动 HTTP 服务...")
    print("API 地址: http://localhost:8001")
    print("文档地址: http://localhost:8001/docs")
    print()

    # 设置监控回调
    from src.rca_agent.monitoring import get_monitor_service
    monitor = get_monitor_service()

    def run_diagnosis_async(fault_info: str):
        """后台运行诊断 - 将结果通过SSE推送给前端"""
        import threading
        def _run():
            asyncio.run(push_to_clients_async(fault_info))
        threading.Thread(target=_run, daemon=True).start()

    async def push_to_clients_async(fault_info: str):
        """将诊断结果推送给所有SSE客户端"""
        from src.rca_agent.graph import create_rca_graph
        graph = create_rca_graph()
        import time

        initial_state: RCAState = {
            "fault_info": fault_info,
            "matched_sop": None,
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
            "action_history": [],
            "global_start_time": time.time(),
            "should_terminate": False,
            "need_match_observation": False,
            "refined_problem_statement": None,
            "final_report": None
        }

        from io import StringIO
        import sys
        old_stderr = sys.stderr
        stderr_capture = StringIO()

        def sse_log(msg: str):
            msg_data = json.dumps({'type': 'log', 'message': msg}, ensure_ascii=False) + "\n"
            for client in list(_sse_clients):
                try:
                    client.put_nowait(msg_data)
                except:
                    pass

        try:
            sys.stderr = stderr_capture

            for step in graph.stream(initial_state):
                for step_name, step_output in step.items():
                    # 直接发送JSON，不用加"data: "前缀，因为StreamingResponse会自动处理
                    data = json.dumps({'step': step_name, 'output': {k: v for k, v in step_output.items() if v is not None}}, ensure_ascii=False) + "\n"
                    for client in list(_sse_clients):
                        try:
                            client.put_nowait(data)
                        except:
                            pass

                    stderr_content = stderr_capture.getvalue()
                    if stderr_content:
                        for line in stderr_content.strip().split('\n'):
                            if line.strip():
                                sse_log(line.strip())
                        stderr_capture.truncate(0)
                        stderr_capture.seek(0)

            done_msg = json.dumps({'type': 'done'}, ensure_ascii=False) + "\n"
            for client in list(_sse_clients):
                try:
                    client.put_nowait(done_msg)
                except:
                    pass
        finally:
            sys.stderr = old_stderr

    # SSE客户端队列集合 (使用queue.Queue用于跨线程通信)
    _sse_clients: set = set()

    def register_sse_client(q: queue.Queue):
        _sse_clients.add(q)
        return lambda: _sse_clients.discard(q)

    def unregister_sse_client(q: queue.Queue):
        _sse_clients.discard(q)

    monitor.set_diagnosis_callback(run_diagnosis_async)

    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOPRCA - 智能根因分析系统")
    parser.add_argument("--server", action="store_true", help="启动 HTTP 服务模式")
    args = parser.parse_args()

    if args.server:
        run_server()
    else:
        main()
