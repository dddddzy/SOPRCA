"""
history_store.py - 历史故障知识库读写
实现双知识库架构：SOP知识库 + 历史故障知识库
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from datetime import datetime
from ..utils.config_loader import load_config

# 从配置读取知识库路径
_kb_config = None

def _get_kb_paths():
    """获取知识库路径"""
    global _kb_config
    if _kb_config is None:
        config = load_config()
        kb_config = config.get('knowledge_base', {})
        mock_mode = config.get('mock_mode', False)

        if mock_mode:
            # Mock模式使用测试目录
            KB_DIR = "data/test"
            HISTORY_DB_PATH = os.path.join(KB_DIR, "history.db")
            CHROMA_PATH = os.path.join(KB_DIR, "chroma")
        else:
            KB_DIR = "data"
            HISTORY_DB_PATH = kb_config.get('history_fault_db_path', "data/history_knowledge.db")
            CHROMA_PATH = kb_config.get('chroma_path', "data/chroma")

        _kb_config = {
            'KB_DIR': KB_DIR,
            'HISTORY_DB_PATH': HISTORY_DB_PATH,
            'CHROMA_PATH': CHROMA_PATH
        }
    return _kb_config

# 默认值
KB_DIR = "data"
HISTORY_DB_PATH = "data/history_knowledge.db"
CHROMA_PATH = "data/chroma"
HISTORY_TABLE = "history_fault_table"


def init_history_knowledge_base():
    """初始化历史故障知识库"""
    kb_paths = _get_kb_paths()
    kb_dir = kb_paths['KB_DIR']
    history_db_path = kb_paths['HISTORY_DB_PATH']
    chroma_path = kb_paths['CHROMA_PATH']

    os.makedirs(kb_dir, exist_ok=True)
    os.makedirs(chroma_path, exist_ok=True)

    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
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

    # 初始化Chroma集合
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma_client.get_collection(name="history_fault_collection")
    except Exception:
        chroma_client.create_collection(name="history_fault_collection")

    return chroma_client


def add_fault_to_history(
    fault_info: str,
    fault_type: str,
    observation: str,
    root_cause: str,
    sop_id: str = None,
    matched_sop_name: str = None,
    is_generated_sop: int = 0
) -> str:
    """添加故障到历史知识库"""
    import uuid
    fault_id = f"FAULT-{uuid.uuid4().hex[:8]}"

    kb_paths = _get_kb_paths()
    history_db_path = kb_paths['HISTORY_DB_PATH']
    chroma_path = kb_paths['CHROMA_PATH']

    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO {HISTORY_TABLE}
        (fault_id, fault_info, fault_type, root_cause, observation, sop_id, matched_sop_name, is_generated_sop)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fault_id, fault_info, fault_type, root_cause, observation, sop_id, matched_sop_name, is_generated_sop))

    conn.commit()
    conn.close()

    # 添加到向量库
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_or_create_collection(name="history_fault_collection")

    # 将observation转为向量（使用ID作为占位，后续可以用embedding函数）
    collection.add(
        ids=[fault_id],
        documents=[observation],
        metadatas=[{
            "fault_info": fault_info,
            "fault_type": fault_type,
            "root_cause": root_cause
        }]
    )

    return fault_id


def match_history_faults(
    observation: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """匹配相似历史故障

    Args:
        observation: 当前观测结果
        top_k: 返回Top-K个相似故障

    Returns:
        相似历史故障列表
    """
    kb_paths = _get_kb_paths()
    history_db_path = kb_paths['HISTORY_DB_PATH']
    chroma_path = kb_paths['CHROMA_PATH']

    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_or_create_collection(name="history_fault_collection")

    # 查询相似故障
    results = collection.query(
        query_texts=[observation],
        n_results=top_k
    )

    # 调试信息
    print(f"[match_history_faults Debug] results keys: {results.keys() if results else 'None'}")
    if results and results.get("distances"):
        print(f"[match_history_faults Debug] distances: {results['distances']}")

    if not results or not results.get("ids") or len(results["ids"][0]) == 0:
        return []

    # 获取详细元数据
    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    matched_faults = []
    for fault_id in results["ids"][0]:
        cursor.execute(f"""
            SELECT fault_id, fault_info, fault_type, root_cause, observation, sop_id, matched_sop_name, is_generated_sop
            FROM {HISTORY_TABLE}
            WHERE fault_id = ?
        """, (fault_id,))

        row = cursor.fetchone()
        if row:
            matched_faults.append({
                "fault_id": row[0],
                "fault_info": row[1],
                "fault_type": row[2],
                "root_cause": row[3],
                "observation": row[4],
                "sop_id": row[5],
                "matched_sop_name": row[6],
                "is_generated_sop": bool(row[7]) if row[7] else False
            })

    conn.close()

    # 添加相似度分数，并过滤低质量结果
    if results.get("distances") and len(results["distances"][0]) > 0:
        for i, fault in enumerate(matched_faults):
            distance = results["distances"][0][i]
            fault["similarity_score"] = 1 - distance  # 距离转相似度
            print(f"[match_history_faults Debug] fault_id={fault.get('fault_id')}, distance={distance:.4f}, similarity_score={fault['similarity_score']:.4f}")

    # 版本8修复：过滤低相似度结果，只保留 similarity_score >= 0 的记录
    SIMILARITY_THRESHOLD = 0.1
    original_count = len(matched_faults)
    matched_faults = [f for f in matched_faults if f.get("similarity_score", 0) >= SIMILARITY_THRESHOLD]
    print(f"[match_history_faults] 相似度过滤: {original_count} -> {len(matched_faults)} 条 (阈值={SIMILARITY_THRESHOLD})")

    return matched_faults


def add_sop_to_knowledgebase(sop_data: Dict[str, Any], chroma_client):
    """添加新生成的SOP到知识库"""
    import uuid

    sop_id = f"SOP-{uuid.uuid4().hex[:8]}"

    conn = sqlite3.connect(HISTORY_DB_PATH.replace("history_knowledge.db", "sop_knowledge.db"))
    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO sop_table
        (sop_id, sop_name, fault_type, description, steps, version)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        sop_id,
        sop_data.get("sop_name", "未命名SOP"),
        sop_data.get("fault_type", "未知"),
        sop_data.get("description", ""),
        json.dumps(sop_data.get("steps", []), ensure_ascii=False),
        "1.0"
    ))

    conn.commit()
    conn.close()

    # 添加到向量库
    collection = chroma_client.get_or_create_collection(name="sop_collection")

    # 构建检索文本
    sop_text = f"{sop_data.get('sop_name', '')} {sop_data.get('fault_type', '')} {sop_data.get('description', '')}"

    collection.add(
        ids=[sop_id],
        documents=[sop_text],
        metadatas=[{
            "sop_name": sop_data.get("sop_name", ""),
            "fault_type": sop_data.get("fault_type", "")
        }]
    )

    return sop_id
