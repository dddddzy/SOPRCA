#!/usr/bin/env python
"""
初始化知识库脚本
用于初始化SOP知识库和历史故障知识库

用法:
    python scripts/init_knowledge_base.py          # 初始化全部（带默认SOP）
    python scripts/init_knowledge_base.py --reset  # 重置并重新初始化
    python scripts/init_knowledge_base.py --status # 查看知识库状态
"""

import sys
import os
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rca_agent.knowledge_base.sop_store import (
    init_sop_knowledge_base,
    init_default_sops,
    get_sop_by_id,
    search_sop_by_vector,
    SOP_TABLE
)
from src.rca_agent.knowledge_base.history_store import (
    init_history_knowledge_base,
    add_fault_to_history,
    match_history_faults,
    HISTORY_TABLE
)
from src.rca_agent.utils.config_loader import load_config


def get_kb_paths():
    """获取知识库路径"""
    config = load_config()
    kb_config = config.get('knowledge_base', {})
    mock_mode = config.get('mock_mode', False)

    if mock_mode:
        KB_DIR = "data/test"
    else:
        KB_DIR = "data"

    return {
        'KB_DIR': KB_DIR,
        'SOP_DB_PATH': kb_config.get('sop_db_path', "data/sop_knowledge.db"),
        'HISTORY_DB_PATH': kb_config.get('history_fault_db_path', "data/history_knowledge.db"),
        'CHROMA_PATH': kb_config.get('chroma_path', "data/chroma")
    }


def reset_knowledge_base():
    """重置知识库（删除所有数据）"""
    kb_paths = get_kb_paths()

    import shutil
    import sqlite3

    # 删除目录
    for path in [kb_paths['SOP_DB_PATH'], kb_paths['HISTORY_DB_PATH'], kb_paths['CHROMA_PATH']]:
        dir_path = os.path.dirname(path)
        if os.path.exists(dir_path):
            print(f"  删除目录: {dir_path}")
            shutil.rmtree(dir_path)

    print("知识库已重置")


def init_all(include_sample_history=True):
    """初始化全部知识库"""
    kb_paths = get_kb_paths()

    print("=" * 50)
    print("初始化知识库")
    print("=" * 50)
    print(f"  数据目录: {kb_paths['KB_DIR']}")
    print(f"  SOP数据库: {kb_paths['SOP_DB_PATH']}")
    print(f"  历史数据库: {kb_paths['HISTORY_DB_PATH']}")
    print(f"  向量数据库: {kb_paths['CHROMA_PATH']}")
    print()

    # 初始化SOP知识库
    print("[1/4] 初始化SOP知识库...")
    chroma_client = init_sop_knowledge_base()
    print("      SQLite表已创建")

    # 初始化默认SOP
    print("[2/4] 添加默认SOP...")
    init_default_sops(chroma_client)

    # 初始化历史故障知识库
    print("[3/4] 初始化历史故障知识库...")
    chroma_client_history = init_history_knowledge_base()
    print("      SQLite表已创建")

    # 添加示例历史故障（可选）
    if include_sample_history:
        print("[4/4] 添加示例历史故障...")
        add_sample_history_faults()

    print()
    print("=" * 50)
    print("知识库初始化完成!")
    print("=" * 50)


def add_sample_history_faults():
    """添加示例历史故障"""
    sample_faults = [
        {
            "fault_info": "productcatalogservice CPU过高",
            "fault_type": "CPU过高",
            "observation": "故障现象：productcatalogservice Pod的CPU使用率高达98%，接近资源上限。指标数据：CPU使用率98%，内存使用正常。Pod状态：Running，restarts=1，ready=1/1。资源配置：CPU limit配置仅为0.1核（100m），CPU request配置为0.05核（50m）。",
            "root_cause": "Pod的CPU资源limit配置过低（100m），无法满足服务实际运行需求。当业务负载增加时，CPU使用率迅速达到上限导致节流。"
        },
        {
            "fault_info": "frontend服务内存过高",
            "fault_type": "内存过高",
            "observation": "故障现象：frontend Pod内存使用率持续走高。指标数据：内存使用率85%。Pod状态：Running，restarts=3。",
            "root_cause": "内存泄漏导致，需排查代码或增加内存限制。"
        },
        {
            "fault_info": "redis-cart网络延迟",
            "fault_type": "网络故障",
            "observation": "故障现象：redis-cart服务响应延迟增加。指标数据：网络延迟200ms。Pod状态：Running，restarts=0。",
            "root_cause": "网络带宽受限或对端服务响应慢。"
        }
    ]

    for fault in sample_faults:
        fault_id = add_fault_to_history(
            fault_info=fault["fault_info"],
            fault_type=fault["fault_type"],
            observation=fault["observation"],
            root_cause=fault["root_cause"]
        )
        print(f"      添加: {fault['fault_info']} -> {fault_id}")

    print(f"      共添加 {len(sample_faults)} 个示例历史故障")


def show_status():
    """显示知识库状态"""
    kb_paths = get_kb_paths()

    print("=" * 50)
    print("知识库状态")
    print("=" * 50)
    print(f"  数据目录: {kb_paths['KB_DIR']}")
    print()

    import sqlite3

    # SOP数据库状态
    print("[SOP知识库]")
    sop_db_path = kb_paths['SOP_DB_PATH']
    if os.path.exists(sop_db_path):
        conn = sqlite3.connect(sop_db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {SOP_TABLE}")
        count = cursor.fetchone()[0]
        print(f"  数据库: {sop_db_path}")
        print(f"  SOP数量: {count}")

        # 显示所有SOP
        cursor.execute(f"SELECT sop_id, sop_name, fault_type FROM {SOP_TABLE}")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]} ({row[2]})")
        conn.close()
    else:
        print(f"  数据库不存在: {sop_db_path}")

    print()

    # 历史故障数据库状态
    print("[历史故障知识库]")
    history_db_path = kb_paths['HISTORY_DB_PATH']
    if os.path.exists(history_db_path):
        conn = sqlite3.connect(history_db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {HISTORY_TABLE}")
        count = cursor.fetchone()[0]
        print(f"  数据库: {history_db_path}")
        print(f"  历史故障数量: {count}")

        # 显示所有历史故障
        cursor.execute(f"SELECT fault_id, fault_info, fault_type FROM {HISTORY_TABLE} LIMIT 10")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]} ({row[2]})")
        conn.close()
    else:
        print(f"  数据库不存在: {history_db_path}")

    print()

    # Chroma向量库状态
    print("[向量数据库]")
    chroma_path = kb_paths['CHROMA_PATH']
    if os.path.exists(chroma_path):
        print(f"  目录: {chroma_path}")
        import chromadb
        chroma_client = chromadb.PersistentClient(path=chroma_path)

        try:
            sop_collection = chroma_client.get_collection(name="sop_collection")
            print(f"  SOP向量数: {sop_collection.count()}")
        except Exception:
            print("  SOP向量数: 0")

        try:
            history_collection = chroma_client.get_collection(name="history_fault_collection")
            print(f"  历史故障向量数: {history_collection.count()}")
        except Exception:
            print("  历史故障向量数: 0")
    else:
        print(f"  目录不存在: {chroma_path}")

    print("=" * 50)


def test_search():
    """测试检索功能"""
    print("=" * 50)
    print("测试检索功能")
    print("=" * 50)

    # 测试SOP检索
    print("\n[SOP检索测试]")
    test_queries = ["CPU过高", "内存泄漏", "网络波动"]
    for query in test_queries:
        sop = search_sop_by_vector(query, init_sop_knowledge_base())
        print(f"  查询 '{query}': {'找到' if sop else '未找到'}")

    # 测试历史故障检索
    print("\n[历史故障检索测试]")
    test_observation = "productcatalogservice CPU使用率98%，内存正常，Pod运行正常"
    results = match_history_faults(test_observation)
    print(f"  查询: {test_observation[:30]}...")
    print(f"  找到 {len(results)} 个相似历史故障")

    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化RCA知识库")
    parser.add_argument("--reset", action="store_true", help="重置知识库（删除所有数据）")
    parser.add_argument("--status", action="store_true", help="查看知识库状态")
    parser.add_argument("--test", action="store_true", help="测试检索功能")
    parser.add_argument("--no-sample", action="store_true", help="初始化时不添加示例历史故障")

    args = parser.parse_args()

    if args.reset:
        reset_knowledge_base()

    if args.status:
        show_status()
    elif args.test:
        test_search()
    else:
        init_all(include_sample_history=not args.no_sample)
