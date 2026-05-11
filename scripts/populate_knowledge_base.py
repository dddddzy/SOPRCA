#!/usr/bin/env python
"""
填充知识库脚本
用于向SOP知识库和历史故障知识库添加丰富的演示案例

用法:
    python scripts/populate_knowledge_base.py          # 添加所有案例
    python scripts/populate_knowledge_base.py --sops   # 只添加SOP
    python scripts/populate_knowledge_base.py --history # 只添加历史案例
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rca_agent.knowledge_base.sop_store import (
    init_sop_knowledge_base,
    add_sop_to_knowledgebase,
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
import chromadb


def get_kb_paths():
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


# 丰富的SOP库
SOP_LIB = [
    # ====== 现有SOP ======
    {
        "sop_id": "SOP-CPU-001",
        "sop_name": "CPU过高诊断标准流程",
        "fault_type": "CPU过高",
        "description": "用于诊断CPU使用率过高问题的标准操作流程，适用于压力测试、资源限制等场景",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取CPU使用率指标数据，确认识别到CPU过高的Pod"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod资源配置与实际使用情况"},
            {"step_num": 3, "tool_name": "check_resource_limits", "description": "检查CPU限制配置是否合理"},
            {"step_num": 4, "tool_name": "analyze_load", "description": "分析负载情况，判断是否正常业务流量"}
        ]
    },
    {
        "sop_id": "SOP-MEM-001",
        "sop_name": "内存过高诊断标准流程",
        "fault_type": "内存过高",
        "description": "用于诊断内存使用率过高问题的标准操作流程，适用于内存泄漏、OOM等场景",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取内存使用率指标数据"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod内存配置和使用情况"},
            {"step_num": 3, "tool_name": "analyze_memory", "description": "分析内存使用详情，识别内存泄漏"},
            {"step_num": 4, "tool_name": "check_oom_events", "description": "检查OOM Kill事件"}
        ]
    },
    {
        "sop_id": "SOP-POD-001",
        "sop_name": "Pod异常状态诊断标准流程",
        "fault_type": "Pod异常",
        "description": "用于诊断Pod处于Pending、Error、CrashLoopBackOff等异常状态的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "pod_analyze", "description": "分析Pod当前状态和事件"},
            {"step_num": 2, "tool_name": "get_pod_logs", "description": "获取Pod日志，分析错误原因"},
            {"step_num": 3, "tool_name": "check_events", "description": "检查Kubernetes事件"},
            {"step_num": 4, "tool_name": "check_resource_quotas", "description": "检查资源配额是否耗尽"}
        ]
    },
    {
        "sop_id": "SOP-NET-001",
        "sop_name": "网络故障诊断标准流程",
        "fault_type": "网络故障",
        "description": "用于诊断网络延迟、丢包、连接超时等网络问题的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取网络相关指标数据"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod网络状态和连接情况"},
            {"step_num": 3, "tool_name": "check_network_policy", "description": "检查网络策略配置"},
            {"step_num": 4, "tool_name": "traceroute", "description": "追踪网络路径，定位故障点"}
        ]
    },
    # ====== 新增SOP ======
    {
        "sop_id": "SOP-DISK-001",
        "sop_name": "磁盘IO过高诊断标准流程",
        "fault_type": "磁盘IO过高",
        "description": "用于诊断磁盘使用率过高、IO读写压力大等磁盘问题的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取磁盘使用率和IO指标数据"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod存储挂载和使用情况"},
            {"step_num": 3, "tool_name": "check_storage_class", "description": "检查存储类配置和容量"},
            {"step_num": 4, "tool_name": "analyze_disk_usage", "description": "分析磁盘使用详情，识别异常文件"}
        ]
    },
    {
        "sop_id": "SOP-RESTART-001",
        "sop_name": "Pod频繁重启诊断标准流程",
        "fault_type": "Pod频繁重启",
        "description": "用于诊断Pod频繁重启、restart count持续增加问题的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取Pod重启次数和间隔指标"},
            {"step_num": 2, "tool_name": "get_pod_logs", "description": "获取Pod历史日志，分析重启原因"},
            {"step_num": 3, "tool_name": "check_oom_events", "description": "检查是否因OOM导致重启"},
            {"step_num": 4, "tool_name": "check_liveness_probe", "description": "检查健康检查配置是否合理"},
            {"step_num": 5, "tool_name": "analyze_exit_code", "description": "分析容器退出码确定具体原因"}
        ]
    },
    {
        "sop_id": "SOP-LATENCY-001",
        "sop_name": "服务响应延迟诊断标准流程",
        "fault_type": "服务响应延迟",
        "description": "用于诊断服务响应时间变慢、延迟增加等性能问题的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "get_relevant_metric", "description": "获取延迟百分位指标（p50/p90/p99）"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析后端Pod资源使用情况"},
            {"step_num": 3, "tool_name": "check_dependencies", "description": "检查依赖服务响应时间"},
            {"step_num": 4, "tool_name": "analyze_traces", "description": "分析分布式追踪，定位慢请求"}
        ]
    },
    {
        "sop_id": "SOP-500-001",
        "sop_name": "服务500错误诊断标准流程",
        "fault_type": "服务500错误",
        "description": "用于诊断服务返回500 Internal Server Error的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "get_pod_logs", "description": "获取服务端错误日志"},
            {"step_num": 2, "tool_name": "pod_analyze", "description": "分析Pod状态和资源情况"},
            {"step_num": 3, "tool_name": "check_dependency_health", "description": "检查依赖服务（数据库、缓存）健康状态"},
            {"step_num": 4, "tool_name": "analyze_exceptions", "description": "分析异常堆栈定位代码问题"}
        ]
    },
    {
        "sop_id": "SOP-502-001",
        "sop_name": "网关502错误诊断标准流程",
        "fault_type": "网关502错误",
        "description": "用于诊断Kubernetes Ingress或Service返回502 Bad Gateway的标准操作流程",
        "steps": [
            {"step_num": 1, "tool_name": "pod_analyze", "description": "分析后端Pod是否正常运行"},
            {"step_num": 2, "tool_name": "check_endpoints", "description": "检查Service endpoints是否为空"},
            {"step_num": 3, "tool_name": "get_pod_logs", "description": "获取后端服务日志"},
            {"step_num": 4, "tool_name": "check_network_connectivity", "description": "检查网络连通性"}
        ]
    }
]


# 丰富的历史案例库
HISTORY_LIB = [
    # ====== CPU过高案例 ======
    {
        "fault_info": "productcatalogservice CPU使用率超过90%",
        "fault_type": "CPU过高",
        "observation": "productcatalogservice Pod的CPU使用率达到95%，内存使用率60%正常。Pod状态Running，restarts=0。CPU limit配置为500m，request为200m。",
        "root_cause": "Pod资源配置不足，CPU limit仅为0.5核，无法应对正常业务负载",
        "matched_sop": "SOP-CPU-001"
    },
    {
        "fault_info": "cartservice CPU突然打满",
        "fault_type": "CPU过高",
        "observation": "cartservice Pod CPU使用率从30%突然上升到100%，持续5分钟。内存和网络正常。Pod重启次数增加。",
        "root_cause": "Chaos Mesh注入CPU压力故障，模拟业务高峰场景"
    },
    {
        "fault_info": "checkoutservice 订单结算时CPU飙高",
        "fault_type": "CPU过高",
        "observation": "checkoutservice在处理批量订单时CPU达到98%，内存使用正常。延迟增加。日常正常时段CPU仅30%。",
        "root_cause": "批量结算逻辑未做限流，导致CPU过载"
    },

    # ====== 内存过高案例 ======
    {
        "fault_info": "paymentservice 内存使用率持续走高",
        "fault_type": "内存过高",
        "observation": "paymentservice Pod内存使用率从50%持续上升到85%，CPU使用正常。Pod重启次数=2。内存泄漏告警触发。",
        "root_cause": "SDK连接池未正确释放，导致内存泄漏"
    },
    {
        "fault_info": "userservice 内存溢出导致Pod被OOM Kill",
        "fault_type": "内存过高",
        "observation": "userservice Pod内存使用率达到90%后被OOM Kill，restart count=5。事件显示Last State: Terminated, Reason: OOMKilled。",
        "root_cause": "内存限制配置过小(256Mi)，无法满足峰值需求"
    },
    {
        "fault_info": "recommendationservice 缓存服务内存过高",
        "fault_type": "内存过高",
        "observation": "recommendationservice内存使用率85%，缓存命中率下降。应用响应时间增加。",
        "root_cause": "缓存未设置过期时间，内存持续增长"
    },

    # ====== 磁盘IO案例 ======
    {
        "fault_info": "mongodb 数据盘使用率超过80%",
        "fault_type": "磁盘IO过高",
        "observation": "mongodb Pod数据盘使用率82%，IO读写延迟增加。日志显示磁盘空间警告。",
        "root_cause": "数据量增长未及时清理或扩容"
    },
    {
        "fault_info": "logs-collector 日志写入导致磁盘IO高",
        "fault_type": "磁盘IO过高",
        "observation": "logs-collector Pod磁盘IO使用率100%，写入速度慢。影响同节点其他Pod性能。",
        "root_cause": "日志轮转配置缺失，大量小文件频繁写入"
    },

    # ====== Pod重启案例 ======
    {
        "fault_info": "shippingservice Pod频繁重启",
        "fault_type": "Pod频繁重启",
        "observation": "shippingservice Pod在30分钟内重启8次。日志显示connection refused错误。重启间隔呈规律性。",
        "root_cause": "健康检查阈值设置过严，业务高峰期被误杀"
    },
    {
        "fault_info": "productcatalogservice Pod处于CrashLoopBackOff状态",
        "fault_type": "Pod异常",
        "observation": "productcatalogservice Pod状态CrashLoopBackOff，restart count=5。错误日志：FATAL: could not open configuration file",
        "root_cause": "配置文件挂载失败，ConfigMap未正确挂载"
    },

    # ====== 网络故障案例 ======
    {
        "fault_info": "cartservice 访问redis超时",
        "fault_type": "网络故障",
        "observation": "cartservice访问redis-cart超时，延迟>2s。redis-cart Pod正常Running。服务间调用链显示超时。",
        "root_cause": "网络策略配置错误，阻断了cartservice到redis的流量"
    },
    {
        "fault_info": "frontend 调用支付网关出现502错误",
        "fault_type": "网关502错误",
        "observation": "frontend Pod连接external-credit-card-api返回502。外部网关Pod正常。错误日志：upstream prematurely closed connection",
        "root_cause": "支付网关服务异常断开连接"
    },

    # ====== 延迟案例 ======
    {
        "fault_info": "productcatalogservice 响应时间突然变慢",
        "fault_type": "服务响应延迟",
        "observation": "productcatalogservice P99延迟从50ms上升到500ms。CPU、内存指标正常。无错误日志。",
        "root_cause": "数据库连接池耗尽，等待时间增加"
    },
    {
        "fault_info": "checkoutservice 结算延迟增加",
        "fault_type": "服务响应延迟",
        "observation": "checkoutservice延迟增加2倍。支付服务响应变慢。整体链路延迟监控显示瓶颈在payment环节。",
        "root_cause": "payment服务被限流，响应时间增加"
    },

    # ====== 500错误案例 ======
    {
        "fault_info": "userservice 返回500内部错误",
        "fault_type": "服务500错误",
        "observation": "userservice 500错误率10%。错误日志：NullPointerException in UserService.getUser()。部分用户无法登录。",
        "root_cause": "代码bug：用户缓存为空时未做空值检查"
    },
    {
        "fault_info": "orderservice 数据库连接池耗尽",
        "fault_type": "服务500错误",
        "observation": "orderservice 500错误率上升。日志：Cannot acquire connection from pool。数据库CPU正常。",
        "root_cause": "长事务未提交，连接池被耗尽"
    },

    # ====== 新案例：用于生成新SOP ======
    {
        "fault_info": "notificationservice 发送邮件延迟增加但各项指标正常",
        "fault_type": "服务响应延迟",
        "observation": "notificationservice P99延迟从100ms上升到2s。CPU、内存、网络、磁盘IO指标均正常。外部邮件服务API响应慢。日志无异常。",
        "root_cause": "外部邮件服务供应商SMTP服务器响应变慢，非本服务问题",
        "is_novel": True  # 标记为需要生成新SOP的案例
    }
]


def populate_sops():
    """填充SOP知识库"""
    print("\n" + "=" * 50)
    print("填充SOP知识库")
    print("=" * 50)

    kb_paths = get_kb_paths()
    chroma_path = kb_paths['CHROMA_PATH']

    os.makedirs(chroma_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    try:
        collection = chroma_client.get_collection(name="sop_collection")
        existing_count = collection.count()
        print(f"当前已有 {existing_count} 个SOP")
    except:
        chroma_client.create_collection(name="sop_collection")
        existing_count = 0
        print("SOP集合已创建")

    added = 0
    skipped = 0

    for sop in SOP_LIB:
        # 检查是否已存在
        existing = search_sop_by_vector(sop['fault_type'], chroma_client)
        if existing:
            print(f"  跳过(已存在): {sop['sop_name']}")
            skipped += 1
            continue

        add_sop_to_knowledgebase(sop, chroma_client)
        print(f"  添加: {sop['sop_name']} [{sop['fault_type']}]")
        added += 1

    print(f"\nSOP填充完成: 新增 {added} 个，跳过 {skipped} 个")


def populate_history():
    """填充历史案例知识库"""
    print("\n" + "=" * 50)
    print("填充历史案例知识库")
    print("=" * 50)

    kb_paths = get_kb_paths()
    chroma_path = kb_paths['CHROMA_PATH']

    os.makedirs(chroma_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    try:
        collection = chroma_client.get_collection(name="history_fault_collection")
        existing_count = collection.count()
        print(f"当前已有 {existing_count} 个历史案例")
    except:
        chroma_client.create_collection(name="history_fault_collection")
        existing_count = 0
        print("历史案例集合已创建")

    added = 0

    for fault in HISTORY_LIB:
        fault_id = add_fault_to_history(
            fault_info=fault["fault_info"],
            fault_type=fault["fault_type"],
            observation=fault["observation"],
            root_cause=fault["root_cause"],
            matched_sop_name=fault.get("matched_sop", None),
            is_generated_sop=1 if fault.get("is_novel") else 0
        )
        print(f"  添加: {fault['fault_info'][:40]}...")
        print(f"        类型: {fault['fault_type']} | SOP: {fault.get('matched_sop', 'N/A')}")
        added += 1

    print(f"\n历史案例填充完成: 新增 {added} 个")


def show_stats():
    """显示知识库统计"""
    kb_paths = get_kb_paths()
    chroma_path = kb_paths['CHROMA_PATH']

    print("\n" + "=" * 50)
    print("知识库统计")
    print("=" * 50)

    if os.path.exists(chroma_path):
        chroma_client = chromadb.PersistentClient(path=chroma_path)

        try:
            sop_collection = chroma_client.get_collection(name="sop_collection")
            print(f"SOP数量: {sop_collection.count()}")
        except:
            print("SOP数量: 0")

        try:
            history_collection = chroma_client.get_collection(name="history_fault_collection")
            print(f"历史案例数量: {history_collection.count()}")
        except:
            print("历史案例数量: 0")

    print("\n可用的演示案例:")
    print("-" * 50)
    print("【匹配SOP类】CPU过高:")
    print("  - productcatalogservice CPU使用率超过90%")
    print("  - cartservice CPU突然打满")
    print("")
    print("【匹配SOP类】内存过高:")
    print("  - paymentservice 内存使用率持续走高")
    print("  - userservice 内存溢出导致Pod被OOM Kill")
    print("")
    print("【匹配SOP类】磁盘IO:")
    print("  - mongodb 数据盘使用率超过80%")
    print("  - logs-collector 日志写入导致磁盘IO高")
    print("")
    print("【匹配SOP类】Pod异常:")
    print("  - shippingservice Pod频繁重启")
    print("  - productcatalogservice Pod处于CrashLoopBackOff状态")
    print("")
    print("【匹配SOP类】网络/网关:")
    print("  - cartservice 访问redis超时")
    print("  - frontend 调用支付网关出现502错误")
    print("")
    print("【生成新SOP类】:")
    print("  - notificationservice 发送邮件延迟增加但各项指标正常")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="填充RCA知识库")
    parser.add_argument("--sops", action="store_true", help="只填充SOP")
    parser.add_argument("--history", action="store_true", help="只填充历史案例")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    args = parser.parse_args()

    # 初始化知识库
    init_sop_knowledge_base()
    init_history_knowledge_base()

    if args.stats:
        show_stats()
    elif args.sops:
        populate_sops()
    elif args.history:
        populate_history()
    else:
        populate_sops()
        populate_history()
        show_stats()
