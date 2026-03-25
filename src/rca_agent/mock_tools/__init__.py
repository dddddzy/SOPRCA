"""
mock_tools - Mock工具包
版本9: 与真实tools一一对应的Mock实现

注意: 此模块中的 execute_tool 只调用Mock实现，不做任何切换。
真实工具的调用由 tools/__init__.py 根据配置决定。
"""

from typing import Dict, Any

# 工具映射表 - Mock工具
TOOL_MAP = {
    # K8s工具
    "pod_analyze": "k8s_mock",
    "service_analyze": "k8s_mock",
    "check_events": "k8s_mock",
    "get_node_status": "k8s_mock",
    "run_kubectl_command": "k8s_mock",
    # 指标工具
    "get_relevant_metric": "metric_mock",
    "whether_is_abnormal_metric": "metric_mock",
    # 链路工具
    "collect_trace": "trace_mock",
    "analyze_trace_latency": "trace_mock",
    # 日志工具
    "get_pod_logs": "log_mock",
    "search_logs": "log_mock",
    "get_events_by_object": "log_mock",
    # SOP工具
    "match_sop_tool": "sop_mock",
    "generate_sop_tool": "sop_mock",
}


def execute_tool(tool_name: str, fault_info: str, **kwargs) -> Dict[str, Any]:
    """执行Mock工具

    Args:
        tool_name: 工具名称
        fault_info: 故障信息
        **kwargs: 工具特定参数

    Returns:
        Mock工具执行结果
    """
    if tool_name not in TOOL_MAP:
        return {"error": f"未知工具: {tool_name}"}

    module_name = TOOL_MAP[tool_name]

    try:
        if module_name == "k8s_mock":
            from . import k8s_mock
            func = getattr(k8s_mock, tool_name, None)
            if func:
                return func(fault_info, **kwargs)
        elif module_name == "metric_mock":
            from . import metric_mock
            func = getattr(metric_mock, tool_name, None)
            if func:
                return func(fault_info, **kwargs)
        elif module_name == "trace_mock":
            from . import trace_mock
            func = getattr(trace_mock, tool_name, None)
            if func:
                return func(fault_info, **kwargs)
        elif module_name == "log_mock":
            from . import log_mock
            func = getattr(log_mock, tool_name, None)
            if func:
                return func(fault_info, **kwargs)
        elif module_name == "sop_mock":
            from . import sop_mock
            func = getattr(sop_mock, tool_name, None)
            if func:
                return func(fault_info, **kwargs)

        return {"error": f"工具 {tool_name} 未找到对应Mock实现"}

    except Exception as e:
        return {"error": f"Mock工具执行失败: {str(e)}"}


# 导出所有Mock工具函数（方便直接导入）
from .k8s_mock import (
    pod_analyze,
    service_analyze,
    check_events,
    get_node_status,
    run_kubectl_command,
)
from .metric_mock import (
    get_relevant_metric,
    whether_is_abnormal_metric,
)
from .trace_mock import (
    collect_trace,
    analyze_trace_latency,
)
from .log_mock import (
    get_pod_logs,
    search_logs,
    get_events_by_object,
)
from .sop_mock import (
    match_sop_tool,
    generate_sop_tool,
)

__all__ = [
    "execute_tool",
    # K8s工具
    "pod_analyze",
    "service_analyze",
    "check_events",
    "get_node_status",
    "run_kubectl_command",
    # 指标工具
    "get_relevant_metric",
    "whether_is_abnormal_metric",
    # 链路工具
    "collect_trace",
    "analyze_trace_latency",
    # 日志工具
    "get_pod_logs",
    "search_logs",
    "get_events_by_object",
    # SOP工具
    "match_sop_tool",
    "generate_sop_tool",
]
