"""
sop_store.py - SOP知识库读写
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
import chromadb
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
            SOP_DB_PATH = os.path.join(KB_DIR, "sop.db")
            CHROMA_PATH = os.path.join(KB_DIR, "chroma")
        else:
            KB_DIR = "data"
            SOP_DB_PATH = kb_config.get('sop_db_path', "data/sop_knowledge.db")
            CHROMA_PATH = kb_config.get('chroma_path', "data/chroma")

        _kb_config = {
            'KB_DIR': KB_DIR,
            'SOP_DB_PATH': SOP_DB_PATH,
            'CHROMA_PATH': CHROMA_PATH
        }
    return _kb_config

# 默认值
KB_DIR = "data"
SOP_DB_PATH = "data/sop_knowledge.db"
CHROMA_PATH = "data/chroma"
SOP_TABLE = "sop_table"


def init_sop_knowledge_base():
    """初始化SOP知识库"""
    kb_paths = _get_kb_paths()
    kb_dir = kb_paths['KB_DIR']
    sop_db_path = kb_paths['SOP_DB_PATH']
    chroma_path = kb_paths['CHROMA_PATH']

    os.makedirs(kb_dir, exist_ok=True)
    os.makedirs(chroma_path, exist_ok=True)

    conn = sqlite3.connect(sop_db_path)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {SOP_TABLE} (
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

    chroma_client = chromadb.PersistentClient(path=chroma_path)
    try:
        chroma_client.get_collection(name="sop_collection")
    except Exception:
        chroma_client.create_collection(name="sop_collection")

    return chroma_client


def add_sop_to_knowledgebase(sop_data: Dict[str, Any], chroma_client):
    """添加SOP到知识库"""
    kb_paths = _get_kb_paths()
    sop_db_path = kb_paths['SOP_DB_PATH']

    conn = sqlite3.connect(sop_db_path)
    cursor = conn.cursor()

    steps_json = json.dumps(sop_data['steps'], ensure_ascii=False)

    cursor.execute(f"""
        INSERT OR REPLACE INTO {SOP_TABLE}
        (sop_id, sop_name, parent_id, fault_type, description, steps, version)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        sop_data['sop_id'],
        sop_data['sop_name'],
        sop_data.get('parent_id'),
        sop_data['fault_type'],
        sop_data.get('description'),
        steps_json,
        sop_data.get('version', '1.0')
    ))

    conn.commit()
    conn.close()

    collection = chroma_client.get_collection(name="sop_collection")
    collection.upsert(
        ids=[sop_data['sop_id']],
        documents=[sop_data['sop_name']],
        metadatas=[{"fault_type": sop_data['fault_type']}]
    )


def search_sop_by_vector(query_text: str, chroma_client, top_k: int = 3) -> List[str]:
    """通过向量检索SOP"""
    collection = chroma_client.get_collection(name="sop_collection")

    # 距离阈值：Chroma使用L2距离，越小越相似
    # 0.0-0.5: 高度相似
    # 0.5-0.7: 中度相似
    # >0.70: 认为不匹配（触发generate_sop）
    DISTANCE_THRESHOLD = 0.70

    try:
        results = collection.query(query_texts=[query_text], n_results=top_k)
        if results and results.get('ids') and results['ids'][0]:
            distances = results.get('distances', [[]])[0]
            if distances:
                min_distance = distances[0]
                print(f"[search_sop_by_vector Debug] 检索到 {len(results['ids'][0])} 个SOP，距离: {[f'{d:.3f}' for d in distances]}")
                if min_distance > DISTANCE_THRESHOLD:
                    print(f"[MatchSOP] 最大匹配度低于阈值({DISTANCE_THRESHOLD:.2f})，判定为无匹配SOP (最小距离={min_distance:.3f})")
                    return []
            return results['ids'][0]
    except Exception as e:
        print(f"[search_sop_by_vector] 向量检索异常: {e}")

    return []


def get_sop_by_id(sop_id: str) -> Optional[Dict[str, Any]]:
    """根据SOP ID获取完整SOP信息"""
    kb_paths = _get_kb_paths()
    sop_db_path = kb_paths['SOP_DB_PATH']

    conn = sqlite3.connect(sop_db_path)
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT sop_id, sop_name, parent_id, fault_type, description, steps, version
        FROM {SOP_TABLE}
        WHERE sop_id = ?
    """, (sop_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "sop_id": row[0],
            "sop_name": row[1],
            "parent_id": row[2],
            "fault_type": row[3],
            "description": row[4],
            "steps": json.loads(row[5]),
            "version": row[6]
        }

    return None


def init_default_sops(chroma_client):
    """初始化默认SOP"""
    sops = [
        {
            "sop_id": "SOP-001",
            "sop_name": "CPU过高诊断SOP",
            "parent_id": None,
            "fault_type": "CPU过高",
            "description": "用于诊断CPU过高问题的标准操作流程",
            "steps": [
                {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取相关指标数据"},
                {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod状态"}
            ],
            "version": "1.0"
        },
        {
            "sop_id": "SOP-002",
            "sop_name": "内存过高诊断SOP",
            "parent_id": None,
            "fault_type": "内存过高",
            "description": "用于诊断内存过高问题的标准操作流程",
            "steps": [
                {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取相关指标数据"},
                {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod状态"},
                {"step_num": 3, "tool_name": "analyze_memory", "description": "分析内存使用详情"}
            ],
            "version": "1.0"
        },
        {
            "sop_id": "SOP-003",
            "sop_name": "Pod异常诊断SOP",
            "parent_id": None,
            "fault_type": "Pod异常",
            "description": "用于诊断Pod异常状态的标准操作流程",
            "steps": [
                {"step_num": 1, "tool_name": "pod_analyze", "description": "分析Pod状态"},
                {"step_num": 2, "tool_name": "get_pod_logs", "description": "获取Pod日志"},
                {"step_num": 3, "tool_name": "check_events", "description": "检查相关事件"}
            ],
            "version": "1.0"
        },
        {
            "sop_id": "SOP-004",
            "sop_name": "网络故障诊断SOP",
            "parent_id": None,
            "fault_type": "网络故障",
            "description": "用于诊断网络波动、延迟、丢包等网络问题的标准操作流程",
            "steps": [
                {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取网络相关指标数据"},
                {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod网络状态"},
                {"step_num": 3, "tool_name": "get_pod_logs", "description": "获取网络相关日志"},
                {"step_num": 4, "tool_name": "check_events", "description": "检查网络相关事件"}
            ],
            "version": "1.0"
        }
    ]

    for sop in sops:
        add_sop_to_knowledgebase(sop, chroma_client)

    print(f"已初始化 {len(sops)} 个默认SOP到知识库")


def extract_fault_type(fault_info: str) -> str:
    """从故障信息中提取故障类型"""
    fault_info_lower = fault_info.lower()

    if "cpu" in fault_info_lower and "高" in fault_info:
        return "CPU过高"
    elif "内存" in fault_info or "memory" in fault_info_lower:
        return "内存过高"
    elif "网络" in fault_info or "network" in fault_info_lower or "波动" in fault_info or "延迟" in fault_info or "丢包" in fault_info:
        return "网络故障"
    elif "pod" in fault_info_lower or "异常" in fault_info:
        return "Pod异常"

    return fault_info


def match_sop(fault_info: str) -> Optional[Dict[str, Any]]:
    """匹配SOP"""
    chroma_client = init_sop_knowledge_base()

    collection = chroma_client.get_collection(name="sop_collection")
    if collection.count() == 0:
        init_default_sops(chroma_client)

    fault_type = extract_fault_type(fault_info)
    sop_ids = search_sop_by_vector(fault_type, chroma_client)

    if sop_ids:
        return get_sop_by_id(sop_ids[0])

    return None
