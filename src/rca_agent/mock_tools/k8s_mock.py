"""
k8s_mock.py - K8s工具的Mock实现
对应真实工具: k8s_tools.py
"""

from typing import Dict, Any, Optional


def detect_scenario(fault_info: str) -> str:
    """根据故障信息推断场景"""
    fault_lower = fault_info.lower() if fault_info else ""

    if "oom" in fault_lower or "内存" in fault_info or "memory" in fault_lower:
        return "memory_oom"
    # 场景 4.1: 故意报错测试
    elif "mockerror" in fault_lower:
        return "force_error"
    # 场景 4.2: 防死循环测试（无异常数据）
    elif "deadlock" in fault_lower:
        return "deadlock_test"
    elif "crash" in fault_lower or "restart" in fault_lower or "重启" in fault_info:
        return "crashloop"
    elif "cpu" in fault_lower:
        return "cpu_high"
    elif "网络" in fault_info or "network" in fault_lower or "延迟" in fault_info:
        return "network"
    else:
        return "cpu_high"  # 默认


def mock_pod_analyze_network(fault_info: str) -> Dict[str, Any]:
    """Pod分析 - 网络延迟场景（指标全绿，无异常）"""
    return {
        "pods": [
            {
                "name": "cartservice-685bbd5d74-7vz5g",
                "status": "Running",
                "restarts": 0,  # 没有异常重启
                "ready": 1,
                "total": 1,
                "containers": [
                    {
                        "name": "cartservice",
                        "cpu_limit": "500m",
                        "memory_limit": "512Mi",
                        "cpu_request": "200m",
                        "memory_request": "256Mi"
                    }
                ]
            }
        ],
        "namespace": "default"
    }

# ========== CPU过高场景 ==========

def mock_pod_analyze_cpu(fault_info: str) -> Dict[str, Any]:
    """Pod分析 - CPU过高场景"""
    return {
        "success": True,
        "data": {
            "service": "productcatalogservice",
            "namespace": "default",
            "cpu_usage": "98%",
            "cpu_limit": "0.1核",
            "cpu_request": "0.05核",
            "memory_usage": "45%",
            "memory_limit": "512Mi",
            "status": "Running",
            "restarts": 0,
            "qps": 50,
            "qps_change": "无明显突增"
        },
        "error": ""
    }


# ========== 内存泄漏/OOM场景 ==========

def mock_pod_analyze_oom(fault_info: str) -> Dict[str, Any]:
    """对齐真实 k8s_tools.py 的返回值结构"""
    return {
        "pods": [
            {
                "name": "cartservice-685bbd5d74-7vz5g",
                "status": "Running",
                "restarts": 12,  # 模拟频繁重启
                "ready": 0,
                "total": 1,
                "containers": [
                    {
                        "name": "cartservice",
                        "cpu_limit": "300m",
                        "memory_limit": "128Mi",  # 极小内存引发 OOM 幻觉
                        "cpu_request": "200m",
                        "memory_request": "64Mi"
                    }
                ]
            }
        ],
        "namespace": "default"
    }

# ========== CrashLoopBackOff场景 ==========

def mock_pod_analyze_crash(fault_info: str) -> Dict[str, Any]:
    """Pod分析 - CrashLoopBackOff场景"""
    return {
        "success": True,
        "data": {
            "service": "cartservice",
            "namespace": "default",
            "status": "CrashLoopBackOff",
            "restarts": 10,
            "last_termination_reason": "Error",
            "last_termination_message": "container \"cart\" exited unexpectedly with code 1",
            "restart_count": 10
        },
        "error": ""
    }


def pod_analyze(fault_info: str, namespace: str = "default") -> Dict[str, Any]:
    """Pod分析 - 根据场景自动推断"""
    scenario = detect_scenario(fault_info)
    if scenario == "memory_oom":
        return mock_pod_analyze_oom(fault_info)
    elif scenario == "crashloop":
        return mock_pod_analyze_crash(fault_info)
    elif scenario == "force_error":
        return {"error": "模拟连接超时，服务无响应"}
    elif scenario == "deadlock_test":
        return {"一切指标正常"}
    elif scenario == "network":
        return mock_pod_analyze_network(fault_info)
    else:
        return mock_pod_analyze_cpu(fault_info)


def service_analyze(fault_info: str, namespace: str = "default") -> Dict[str, Any]:
    """Service分析"""
    return {
        "success": True,
        "data": {
            "service": "productcatalogservice",
            "namespace": "default",
            "endpoints": 2,
            "healthy": True,
            "selector": {"app": "productcatalogservice"}
        },
        "error": ""
    }


def check_events(
    namespace: str = "default",
    since_seconds: int = 3600,
    pod_prefix: str = None,
    **kwargs
) -> Dict[str, Any]:
    """检查事件"""
    scenario = detect_scenario(pod_prefix or "")
    if scenario == "crashloop":
        return {
            "success": True,
            "data": {
                "events": [
                    {"type": "Warning", "reason": "BackOff", "message": "Back-off restarting failed container"},
                    {"type": "Warning", "reason": "Failed", "message": "Error: failed to load config file"}
                ]
            },
            "error": ""
        }
    return {
        "success": True,
        "data": {
            "events": [
                {"type": "Normal", "reason": "Scheduled", "message": "Successfully assigned pod to node"},
                {"type": "Normal", "reason": "Pulled", "message": "Container image already present"}
            ]
        },
        "error": ""
    }


def get_node_status() -> Dict[str, Any]:
    """获取Node状态"""
    return {
        "success": True,
        "data": {
            "nodes": [
                {"name": "node-1", "status": "Ready", "roles": ["control-plane", "master"], "version": "v1.28.0"},
                {"name": "node-2", "status": "Ready", "roles": ["worker"], "version": "v1.28.0"}
            ]
        },
        "error": ""
    }


def run_kubectl_command(command: str) -> Dict[str, Any]:
    """执行kubectl命令（Mock版本）"""
    return {
        "stdout": "Mock kubectl output",
        "stderr": "",
        "returncode": 0
    }
