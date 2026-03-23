"""
mock_tools.py - Mock工具，用于测试与演示
版本7: 工程化完善 - 符合测试方案的完整Mock
根据故障信息自动推断场景，返回对应的Mock数据
"""

from typing import Dict, Any, List


def detect_scenario(fault_info: str) -> str:
    """根据故障信息推断场景"""
    fault_lower = fault_info.lower() if fault_info else ""

    if "oom" in fault_lower or "内存" in fault_info or "memory" in fault_lower:
        return "memory_oom"
    elif "crash" in fault_lower or "restart" in fault_lower or "重启" in fault_info:
        return "crashloop"
    elif "cpu" in fault_lower or "cpu" in fault_lower:
        return "cpu_high"
    else:
        return "cpu_high"  # 默认


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


def mock_get_relevant_metric_cpu(fault_info: str) -> Dict[str, Any]:
    """获取指标 - CPU过高场景"""
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
            "qps": 50,
            "qps_change": "无明显突增"
        },
        "error": ""
    }


def mock_get_pod_logs_cpu(fault_info: str) -> Dict[str, Any]:
    """获取日志 - CPU过高场景(无报错)"""
    return {
        "success": True,
        "data": {
            "logs": "2026-03-11 服务正常启动，持续处理请求，无报错日志，无异常堆栈信息",
            "has_error": False
        },
        "error": ""
    }


# ========== 内存泄漏/OOM场景 ==========

def mock_pod_analyze_oom(fault_info: str) -> Dict[str, Any]:
    """Pod分析 - OOM场景"""
    return {
        "success": True,
        "data": {
            "service": "paymentservice",
            "namespace": "default",
            "cpu_usage": "30%",
            "cpu_limit": "1核",
            "memory_usage": "99%",
            "memory_limit": "512Mi",
            "memory_rss": "500Mi",
            "status": "Running",
            "restarts": 5,
            "restart_reason": "OOM killed"
        },
        "error": ""
    }


def mock_get_relevant_metric_oom(fault_info: str) -> Dict[str, Any]:
    """获取指标 - OOM场景"""
    return {
        "success": True,
        "data": {
            "service": "paymentservice",
            "namespace": "default",
            "cpu_usage": "30%",
            "memory_usage": "99%",
            "memory_limit": "512Mi",
            "memory_rss": "500Mi",
            "memory_oom_count": 5,
            "trend": "持续上涨"
        },
        "error": ""
    }


def mock_get_pod_logs_oom(fault_info: str) -> Dict[str, Any]:
    """获取日志 - OOM场景"""
    return {
        "success": True,
        "data": {
            "logs": "java.lang.OutOfMemoryError: Java heap space\nat com.payment.Service.process(Service.java:125)\njava.lang.OutOfMemoryError: GC overhead limit exceeded",
            "has_error": True,
            "error_type": "OOM"
        },
        "error": ""
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


def mock_get_pod_logs_crash(fault_info: str) -> Dict[str, Any]:
    """获取日志 - CrashLoopBackOff场景"""
    return {
        "success": True,
        "data": {
            "logs": "Error: failed to load config file: config.yaml: no such file or directory\nUnable to start application",
            "has_error": True,
            "error_type": "ConfigError"
        },
        "error": ""
    }


def mock_check_events_crash(fault_info: str) -> Dict[str, Any]:
    """检查事件 - CrashLoopBackOff场景"""
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


# ========== 通用场景 ==========

def mock_pod_analyze(fault_info: str) -> Dict[str, Any]:
    """Pod分析 - 根据场景自动推断"""
    scenario = detect_scenario(fault_info)
    if scenario == "memory_oom":
        return mock_pod_analyze_oom(fault_info)
    elif scenario == "crashloop":
        return mock_pod_analyze_crash(fault_info)
    else:
        return mock_pod_analyze_cpu(fault_info)


def mock_get_relevant_metric(fault_info: str) -> Dict[str, Any]:
    """获取指标 - 根据场景自动推断"""
    scenario = detect_scenario(fault_info)
    if scenario == "memory_oom":
        return mock_get_relevant_metric_oom(fault_info)
    else:
        return mock_get_relevant_metric_cpu(fault_info)


def mock_analyze_memory(fault_info: str) -> Dict[str, Any]:
    """分析内存使用"""
    return {
        "success": True,
        "data": {
            "service": "paymentservice",
            "memory_usage": "99%",
            "memory_limit": "512Mi",
            "memory_rss": "500Mi",
            "oom_count": 5,
            "restart_reason": "OOM killed"
        },
        "error": ""
    }


def mock_get_pod_logs(fault_info: str) -> Dict[str, Any]:
    """获取Pod日志 - 根据场景自动推断"""
    scenario = detect_scenario(fault_info)
    if scenario == "memory_oom":
        return mock_get_pod_logs_oom(fault_info)
    elif scenario == "crashloop":
        return mock_get_pod_logs_crash(fault_info)
    else:
        return mock_get_pod_logs_cpu(fault_info)


def mock_check_events(fault_info: str) -> Dict[str, Any]:
    """检查事件"""
    scenario = detect_scenario(fault_info)
    if scenario == "crashloop":
        return mock_check_events_crash(fault_info)
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


def mock_service_analyze(fault_info: str) -> Dict[str, Any]:
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


def mock_collect_trace(fault_info: str) -> Dict[str, Any]:
    """链路追踪"""
    return {
        "success": True,
        "data": {
            "service": "productcatalogservice",
            "traces": [
                {"trace_id": "abc123", "duration": 100, "status": "ok"},
                {"trace_id": "def456", "duration": 150, "status": "ok"}
            ]
        },
        "error": ""
    }


# ========== 异常场景Mock ==========

def mock_tool_failed(fault_info: str) -> Dict[str, Any]:
    """工具执行失败"""
    return {
        "success": False,
        "data": {},
        "error": "工具执行失败，K8s API连接超时"
    }


def mock_empty_result(fault_info: str) -> Dict[str, Any]:
    """返回空数据"""
    return {
        "success": True,
        "data": {},
        "error": ""
    }


def mock_syntax_error(fault_info: str) -> str:
    """返回非结构化内容"""
    return "This is not a structured response"


# ========== SOP生成 ==========

def mock_generate_sop(fault_info: str) -> Dict[str, Any]:
    """Mock: 生成新SOP

    注意：实际生成逻辑在knowledge_base.generate_sop中
    这里仅作为工具映射的兜底实现
    """
    return {
        "status": "success",
        "message": "SOP生成功能已通过tool_executor_node调用真实函数",
        "sop_name": "生成的SOP",
        "steps": []
    }


# ========== SOP执行 ==========

def mock_run_sop(fault_info: str, matched_sop: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行SOP流程"""
    if not matched_sop:
        return {
            "status": "error",
            "error": "无匹配的SOP",
            "sop_name": "未知"
        }

    sop_name = matched_sop.get("sop_name", "未知SOP")
    steps = matched_sop.get("steps", [])

    if not steps:
        return {
            "status": "error",
            "error": "SOP没有步骤",
            "sop_name": sop_name
        }

    results = []
    for step in steps:
        step_num = step.get("step_num", 0)
        tool_name = step.get("tool_name", "")
        description = step.get("description", "")

        if tool_name in TOOL_MAP:
            tool_result = TOOL_MAP[tool_name](fault_info)
            results.append({
                "step_num": step_num,
                "tool_name": tool_name,
                "description": description,
                "status": "success",
                "result": tool_result
            })

    return {
        "status": "success",
        "sop_name": sop_name,
        "total_steps": len(steps),
        "executed_steps": len(results),
        "results": results
    }


# 工具映射表
TOOL_MAP = {
    "pod_analyze": mock_pod_analyze,
    "get_relevant_metric": mock_get_relevant_metric,
    "analyze_memory": mock_analyze_memory,
    "get_pod_logs": mock_get_pod_logs,
    "check_events": mock_check_events,
    "service_analyze": mock_service_analyze,
    "collect_trace": mock_collect_trace,
    # 版本7新增：SOP生成与执行工具
    "generate_sop": mock_generate_sop,
    "run_sop": mock_run_sop,
    # 异常场景
    "mock_failed": mock_tool_failed,
    "mock_empty": mock_empty_result,
}


def execute_tool(tool_name: str, fault_info: str) -> Dict[str, Any]:
    """执行工具

    Args:
        tool_name: 工具名称
        fault_info: 故障信息

    Returns:
        工具执行结果
    """
    # 版本8修改：根据mock_mode决定使用真实工具还是mock工具
    from ..utils.config_loader import load_config
    config = load_config()
    mock_mode = config.get('mock_mode', True)

    if not mock_mode:
        # 真实环境模式：调用真实工具
        return execute_real_tool(tool_name, fault_info)

    # Mock模式：使用mock工具
    if tool_name in TOOL_MAP:
        return TOOL_MAP[tool_name](fault_info)
    else:
        return {"error": f"未知工具: {tool_name}"}


def execute_real_tool(tool_name: str, fault_info: str) -> Dict[str, Any]:
    """执行真实环境工具

    版本8新增：真实环境下调用k8s/日志/指标工具
    """
    try:
        # 指标工具
        if tool_name == "get_relevant_metric":
            from .metric_tools import get_relevant_metric
            return get_relevant_metric(fault_info)

        # Pod分析
        elif tool_name == "pod_analyze":
            from .k8s_tools import pod_analyze
            return pod_analyze(fault_info)

        # Service分析
        elif tool_name == "service_analyze":
            from .k8s_tools import service_analyze
            return service_analyze(fault_info)

        # 事件检查
        elif tool_name == "check_events":
            from .k8s_tools import check_events
            return check_events()

        # Node状态
        elif tool_name == "get_node_status":
            from .k8s_tools import get_node_status
            return get_node_status()

        # Pod日志
        elif tool_name == "get_pod_logs":
            from .log_tools import get_pod_logs
            return get_pod_logs(fault_info)

        # 日志搜索
        elif tool_name == "search_logs":
            from .log_tools import search_logs
            return search_logs(fault_info)

        # kubectl命令
        elif tool_name == "run_kubectl_command":
            from .k8s_tools import run_kubectl_command
            return run_kubectl_command(fault_info)

        # 链路追踪
        elif tool_name == "collect_trace":
            # 真实环境暂不支持链路追踪，返回模拟数据
            return {"error": "真实环境暂不支持链路追踪"}

        elif tool_name == "analyze_trace_latency":
            return {"error": "真实环境暂不支持链路追踪"}

        else:
            return {"error": f"未知工具: {tool_name}"}

    except Exception as e:
        return {"error": f"工具执行失败: {str(e)}"}
