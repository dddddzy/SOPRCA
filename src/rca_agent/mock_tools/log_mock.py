"""
log_mock.py - 日志工具的Mock实现
对应真实工具: log_tools.py
"""

from typing import Dict, Any, List


def detect_scenario(fault_info: str) -> str:
    """根据故障信息推断场景"""
    fault_lower = fault_info.lower() if fault_info else ""

    if "oom" in fault_lower or "内存" in fault_info or "memory" in fault_lower:
        return "memory_oom"
    elif "crash" in fault_lower or "restart" in fault_lower or "重启" in fault_info:
        return "crashloop"
    else:
        return "cpu_high"


def get_pod_logs(
    fault_info: str,
    namespace: str = "default",
    tail_lines: int = 100,
    previous: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """获取Pod日志"""
    _ = kwargs  # 忽略额外参数

    scenario = detect_scenario(fault_info)

    if scenario == "memory_oom":
        return {
            "success": True,
            "pod": fault_info.split()[0] if fault_info else "unknown",
            "namespace": namespace,
            "logs": "java.lang.OutOfMemoryError: Java heap space\nat com.payment.Service.process(Service.java:125)\njava.lang.OutOfMemoryError: GC overhead limit exceeded",
            "has_error": True,
            "error_type": "OOM"
        }
    elif scenario == "crashloop":
        return {
            "success": True,
            "pod": fault_info.split()[0] if fault_info else "unknown",
            "namespace": namespace,
            "logs": "Error: failed to load config file: config.yaml: no such file or directory\nUnable to start application",
            "has_error": True,
            "error_type": "ConfigError"
        }
    else:
        return {
            "success": True,
            "pod": fault_info.split()[0] if fault_info else "unknown",
            "namespace": namespace,
            "logs": "2026-03-11 服务正常启动，持续处理请求，无报错日志，无异常堆栈信息",
            "has_error": False
        }


def extract_errors(logs: str) -> List[str]:
    """从日志中提取错误信息"""
    error_keywords = ["ERROR", "Error", "error", "FATAL", "Fatal", "CRITICAL", "Critical", "Exception", "exception"]
    lines = logs.split("\n")
    errors = []

    for line in lines:
        if any(keyword in line for keyword in error_keywords):
            errors.append(line.strip())

    return errors


def search_logs(
    keyword: str,
    namespace: str = "default",
    since: str = "1h",
    limit: int = 50
) -> Dict[str, Any]:
    """搜索日志"""
    return {
        "success": True,
        "keyword": keyword,
        "namespace": namespace,
        "matches": [
            f"2026-03-11 10:00:00 INFO {keyword} - Request processed successfully",
            f"2026-03-11 10:00:01 DEBUG {keyword} - Cache hit"
        ],
        "count": 2
    }


def get_events_by_object(
    object_name: str,
    namespace: str = "default"
) -> Dict[str, Any]:
    """获取指定对象的事件"""
    return {
        "success": True,
        "object": object_name,
        "namespace": namespace,
        "events": [
            {"type": "Normal", "reason": "Scheduled", "message": "Successfully assigned pod to node"},
            {"type": "Normal", "reason": "Pulled", "message": "Container image already present"},
            {"type": "Normal", "reason": "Created", "message": "Created container cart"},
            {"type": "Normal", "reason": "Started", "message": "Started container cart"}
        ]
    }
