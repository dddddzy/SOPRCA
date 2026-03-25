"""
metric_mock.py - 指标工具的Mock实现
对应真实工具: metric_tools.py
"""

from typing import Dict, Any, Optional


def detect_scenario(fault_info: str) -> str:
    """根据故障信息推断场景"""
    fault_lower = fault_info.lower() if fault_info else ""

    if "oom" in fault_lower or "内存" in fault_info or "memory" in fault_lower:
        return "memory_oom"
    elif "cpu" in fault_lower:
        return "cpu_high"
    elif "网络" in fault_info or "network" in fault_lower:
        return "network"
    elif "mockerror" in fault_lower:
        return "force_error"
    # 场景 4.2: 防死循环测试（无异常数据）
    elif "deadlock" in fault_lower:
        return "deadlock_test"
    else:
        return "cpu_high"


def get_relevant_metric(
    fault_info: str,
    metric_name: Optional[str] = None,
    namespace: str = "default",
    duration: str = "5m"
) -> Dict[str, Any]:
    """获取相关指标数据"""
    if not metric_name:
        scenario = detect_scenario(fault_info)
        if scenario == "memory_oom":
            metric_name = "memory"
        elif scenario == "network":
            metric_name = "network"
        else:
            metric_name = "cpu"

    if metric_name == "cpu":
        return {
            "success": True,
            "metric_type": "cpu",
            "namespace": namespace,
            "pods": [
                {"name": "productcatalogservice-abc123", "cpu": "980m"},
                {"name": "productcatalogservice-xyz789", "cpu": "950m"}
            ],
            "diagnostic_hint": "CPU使用率接近限制，建议检查是否有异常流量或资源耗尽"
        }
    elif metric_name == "memory":
        return {
            "success": True,
            "metric_type": "memory",
            "namespace": namespace,
            "pods": [
                {"name": "paymentservice-def456", "memory": "500Mi"},
                {"name": "paymentservice-ghi789", "memory": "510Mi"}
            ],
            "diagnostic_hint": "内存使用率偏高，建议检查内存泄漏"
        }
    elif metric_name == "network":
        return {
            "success": True,
            "metric_type": "network",
            "namespace": namespace,
            "pods": [
                {"name": "frontend-jkl012", "network_rx": "1.2MB/s", "network_tx": "800KB/s"},
                {"name": "frontend-mno345", "network_rx": "1.1MB/s", "network_tx": "750KB/s"}
            ],
            "diagnostic_hint": "注意：Prometheus 基础网络指标仅反映吞吐量，无法直接体现 TCP 阻塞或业务延迟。如果日志或事件中存在 'timeout'、'deadline'、'connection reset' 等超时报错，强烈建议调用 trace_tools（如 collect_trace 或 analyze_trace_latency）进一步分析具体的请求调用链耗时。"
        }
    elif metric_name == "force_error":
        return {"error": "模拟连接超时，服务无响应"}
    elif metric_name == "deadlock_test":
        return {"一切指标正常"}
    else:
        return {
            "success": False,
            "error": f"不支持的指标类型: {metric_name}"
        }


def whether_is_abnormal_metric(
    metric_name: str,
    threshold: float = 80.0,
    namespace: str = "default"
) -> Dict[str, Any]:
    """判断指标是否异常"""
    if metric_name == "cpu":
        return {
            "is_abnormal": True,
            "threshold": threshold,
            "abnormal_pods": [
                {"pod": "productcatalogservice-abc123", "cpu": "980m", "cpu_percent": 98.0}
            ]
        }
    elif metric_name == "memory":
        return {
            "is_abnormal": True,
            "threshold": threshold,
            "abnormal_pods": [
                {"pod": "paymentservice-def456", "memory": "500Mi", "memory_percent": 98.0}
            ]
        }
    elif metric_name == "network":
        return {
            "is_abnormal": False,
            "reason": "基础网络吞吐正常，但 Prometheus 基础指标无法体现 TCP 重传或业务层延迟，建议查阅 Trace（collect_trace / analyze_trace_latency）进一步排查"
        }
    else:
        return {
            "is_abnormal": False,
            "reason": f"不支持的指标类型: {metric_name}"
        }
