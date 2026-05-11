"""
添加假数据：cartservice节点响应缓慢的SOP和历史案例
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rca_agent.knowledge_base.sop_store import add_sop_to_knowledgebase, init_sop_knowledge_base
from src.rca_agent.knowledge_base.history_store import add_fault_to_history, init_history_knowledge_base
import chromadb

def main():
    # 初始化知识库
    print("初始化SOP知识库...")
    init_sop_knowledge_base()
    chroma_client = chromadb.PersistentClient(path="data/chroma")

    # 1. 添加 cartservice 网络延迟 SOP
    cartservice_sop = {
        "sop_id": "SOP-CARTSERVICE-NET-LATENCY",
        "sop_name": "cartservice节点响应缓慢 - 网络延迟异常",
        "parent_id": None,
        "fault_type": "网络延迟异常",
        "description": "cartservice节点响应缓慢，入站网络延迟异常",
        "steps": [
            {"order": 1, "tool": "check_network_policy", "description": "检查cartservice网络策略配置", "expectedResult": "确认网络策略无异常"},
            {"order": 2, "tool": "check_ingress_controller", "description": "检查Ingress控制器状态", "expectedResult": "Ingress配置正常"},
            {"order": 3, "tool": "check_service_endpoints", "description": "检查cartservice Service端点", "expectedResult": "Service端点正常"},
            {"order": 4, "tool": "ping_test", "description": "测试cartservice网络连通性", "expectedResult": "网络连通"},
            {"order": 5, "tool": "tc_qdisc_show", "description": "检查网络队列规则", "expectedResult": "队列配置正常"},
            {"order": 6, "tool": "check_chaos_mesh", "description": "检查是否有Chaos Mesh故障注入", "expectedResult": "确认故障注入状态"},
            {"order": 7, "tool": "analyze_latency", "description": "分析入站延迟原因", "expectedResult": "定位到根因"}
        ],
        "version": "1.0",
        "status": "active"
    }

    print("添加 cartservice 网络延迟 SOP...")
    add_sop_to_knowledgebase(cartservice_sop, chroma_client)
    print(f"SOP添加成功: {cartservice_sop['sop_id']}")

    # 2. 添加历史故障案例
    print("\n初始化历史故障知识库...")
    init_history_knowledge_base()

    print("添加 cartservice 网络延迟 历史案例...")
    fault_id = add_fault_to_history(
        fault_info="cartservice节点响应缓慢",
        fault_type="网络延迟异常",
        observation="""故障类型: 网络延迟异常
故障位置: cartservice
关键线索:
- cartservice响应时间从50ms增加到2000ms
- 入站网络延迟异常
- Chaos Mesh检测到网络延迟故障注入
- Pod本身资源正常
可能根因: 入站网络延迟异常
已排除根因:
- CPU Throttling (排除，CPU使用率正常)
- 内存问题 (排除，内存使用率正常)
- OOMKill (排除，Pod未重启)""",
        root_cause="入站网络延迟异常",
        sop_id="SOP-CARTSERVICE-NET-LATENCY",
        matched_sop_name="cartservice节点响应缓慢 - 网络延迟异常",
        is_generated_sop=0
    )
    print(f"历史案例添加成功: {fault_id}")

    print("\n=== 假数据添加完成 ===")
    print("现在输入 'cartservice节点响应缓慢' 应该能匹配到正确的SOP")

if __name__ == "__main__":
    main()
