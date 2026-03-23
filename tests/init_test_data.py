"""
测试数据初始化脚本
用于版本7 Mock测试 - 初始化测试用SOP和历史故障数据
"""

import sqlite3
import chromadb
import json
import os
import shutil

# 路径配置 - 使用独立的测试目录
KB_DIR = "data"
TEST_DIR = f"{KB_DIR}/test"
SOP_DB = f"{TEST_DIR}/sop.db"
HISTORY_DB = f"{TEST_DIR}/history.db"
CHROMA_PATH = f"{TEST_DIR}/chroma"


def init_test_knowledge_base():
    """初始化测试知识库"""
    # 先删除旧目录
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)

    # SOP知识库
    conn = sqlite3.connect(SOP_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sop_table (
            sop_id TEXT PRIMARY KEY,
            sop_name TEXT NOT NULL,
            parent_id TEXT,
            fault_type TEXT NOT NULL,
            description TEXT,
            steps TEXT NOT NULL,
            version TEXT DEFAULT '1.0',
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # 历史故障知识库
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history_fault_table (
            fault_id TEXT PRIMARY KEY,
            fault_info TEXT NOT NULL,
            fault_type TEXT,
            root_cause TEXT,
            observation TEXT,
            sop_id TEXT,
            matched_sop_name TEXT,
            is_generated_sop INTEGER DEFAULT 0,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    # Chroma向量库
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_client.create_collection(name="sop_collection")
    chroma_client.create_collection(name="history_fault_collection")

    print("已清空并重建测试知识库")
    return chroma_client


def add_test_sops(chroma_client):
    """添加测试用SOP数据（3条核心场景）"""
    sops = [
        {
            "sop_id": "SOP-TEST-001",
            "sop_name": "微服务CPU使用率过高根因诊断SOP",
            "fault_type": "CPU过高",
            "description": "K8s微服务CPU使用率持续超过80%的故障场景",
            "steps": [
                {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取服务CPU使用率、限制、核数等核心指标"},
                {"step_num": 2, "tool_name": "pod_analyze", "description": "获取Pod的资源配置、运行状态、重启记录"},
                {"step_num": 3, "tool_name": "get_pod_logs", "description": "查看服务业务日志，排查代码异常"},
                {"step_num": 4, "tool_name": "service_analyze", "description": "查看服务QPS/请求量变化"}
            ]
        },
        {
            "sop_id": "SOP-TEST-002",
            "sop_name": "微服务内存泄漏诊断SOP",
            "fault_type": "内存泄漏",
            "description": "微服务内存使用率持续上涨、OOM killed故障场景",
            "steps": [
                {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取内存使用率、限制、RSS指标"},
                {"step_num": 2, "tool_name": "pod_analyze", "description": "查看Pod重启记录、OOM事件"},
                {"step_num": 3, "tool_name": "get_pod_logs", "description": "查看JVM/程序内存报错日志"}
            ]
        },
        {
            "sop_id": "SOP-TEST-003",
            "sop_name": "Pod CrashLoopBackOff故障诊断SOP",
            "fault_type": "Pod异常",
            "description": "Pod反复重启、无法正常提供服务场景",
            "steps": [
                {"step_num": 1, "tool_name": "pod_analyze", "description": "查看Pod状态、重启次数、最近终止原因"},
                {"step_num": 2, "tool_name": "get_pod_logs", "description": "查看容器启动日志、崩溃日志"},
                {"step_num": 3, "tool_name": "check_events", "description": "查看命名空间下的K8s事件"}
            ]
        }
    ]

    conn = sqlite3.connect(SOP_DB)
    cursor = conn.cursor()

    for sop in sops:
        cursor.execute("""
            INSERT OR REPLACE INTO sop_table
            (sop_id, sop_name, fault_type, description, steps, version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sop['sop_id'],
            sop['sop_name'],
            sop['fault_type'],
            sop['description'],
            json.dumps(sop['steps'], ensure_ascii=False),
            '1.0'
        ))

    conn.commit()
    conn.close()

    # 添加到向量库
    collection = chroma_client.get_or_create_collection(name="sop_collection")
    for sop in sops:
        doc = f"{sop['sop_name']} {sop['fault_type']} {sop['description']}"
        collection.upsert(
            ids=[sop['sop_id']],
            documents=[doc],
            metadatas=[{"fault_type": sop['fault_type']}]
        )

    print(f"已添加 {len(sops)} 条测试SOP")


def add_test_history_faults(chroma_client):
    """添加测试用历史故障数据（2条）"""
    faults = [
        {
            "fault_id": "FAULT-TEST-001",
            "fault_info": "productcatalogservice CPU使用率98%",
            "fault_type": "CPU过高",
            "root_cause": "Pod CPU limit设置为0.1核，远低于业务正常需求，导致CPU被打满",
            "observation": "故障类型: CPU过高\n故障位置: productcatalogservice Pod\n关键线索: CPU使用率98%，内存正常，日志无报错，Pod无重启，QPS无突增\n可能根因: CPU资源配置不足"
        },
        {
            "fault_id": "FAULT-TEST-002",
            "fault_info": "paymentservice OOM killed",
            "fault_type": "内存泄漏",
            "root_cause": "程序内存泄漏，堆内存无限制，持续上涨触发OOM",
            "observation": "故障类型: 内存泄漏\n故障位置: paymentservice Pod\n关键线索: 内存使用率从30%持续涨到95%，Pod反复重启，重启原因为OOM killed，日志有内存溢出报错\n可能根因: 应用内存泄漏"
        }
    ]

    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    for fault in faults:
        cursor.execute("""
            INSERT OR REPLACE INTO history_fault_table
            (fault_id, fault_info, fault_type, root_cause, observation, is_generated_sop)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fault['fault_id'],
            fault['fault_info'],
            fault['fault_type'],
            fault['root_cause'],
            fault['observation'],
            0
        ))

    conn.commit()
    conn.close()

    # 添加到向量库
    collection = chroma_client.get_or_create_collection(name="history_fault_collection")
    for fault in faults:
        collection.upsert(
            ids=[fault['fault_id']],
            documents=[fault['observation']],
            metadatas=[
                {"fault_info": fault['fault_info'], "fault_type": fault['fault_type'], "root_cause": fault['root_cause']}
            ]
        )

    print(f"已添加 {len(faults)} 条测试历史故障")


def run():
    """运行初始化"""
    print("=" * 50)
    print("测试数据初始化")
    print("=" * 50)

    chroma_client = init_test_knowledge_base()
    add_test_sops(chroma_client)
    add_test_history_faults(chroma_client)

    print("=" * 50)
    print("测试数据初始化完成!")
    print("=" * 50)
    print(f"SOP知识库: {SOP_DB}")
    print(f"历史故障库: {HISTORY_DB}")
    print(f"Chroma路径: {CHROMA_PATH}")


if __name__ == "__main__":
    run()
