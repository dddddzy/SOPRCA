"""
tools模块 - 预定义工具实现
版本9: 模块级Mock/Real切换

根据 config.yaml 中的 mock_mode 配置决定:
- mock_mode: true  -> 使用 mock_tools 中的工具
- mock_mode: false -> 使用真实的 k8s/metric/trace/log 等工具
"""

import os
import sys
from typing import Dict, Any

# 将项目根目录添加到 path（用于 config_loader）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..utils.config_loader import load_config

# 版本9: 模块级导入切换
_config = load_config()
_mock_mode = _config.get('mock_mode', True)

if _mock_mode:
    # Mock模式：导入 mock_tools 的 execute_tool
    from ..mock_tools import execute_tool as _execute_tool
else:
    # 真实模式：使用真实工具的 execute_tool
    def _execute_tool(tool_name: str, fault_info: str, **kwargs) -> Dict[str, Any]:
        """执行真实环境工具"""
        try:
            # K8s工具
            if tool_name == "pod_analyze":
                from .k8s_tools import pod_analyze
                return pod_analyze(fault_info, **kwargs)
            elif tool_name == "service_analyze":
                from .k8s_tools import service_analyze
                return service_analyze(fault_info, **kwargs)
            elif tool_name == "check_events":
                from .k8s_tools import check_events
                return check_events(**kwargs)
            elif tool_name == "get_node_status":
                from .k8s_tools import get_node_status
                return get_node_status()
            elif tool_name == "run_kubectl_command":
                from .k8s_tools import run_kubectl_command
                return run_kubectl_command(fault_info)

            # 指标工具
            elif tool_name == "get_relevant_metric":
                from .metric_tools import get_relevant_metric
                return get_relevant_metric(fault_info, **kwargs)
            elif tool_name == "whether_is_abnormal_metric":
                from .metric_tools import whether_is_abnormal_metric
                return whether_is_abnormal_metric(**kwargs)

            # 链路工具
            elif tool_name == "collect_trace":
                from .trace_tools import collect_trace
                return collect_trace(fault_info, **kwargs)
            elif tool_name == "analyze_trace_latency":
                from .trace_tools import analyze_trace_latency
                return analyze_trace_latency(**kwargs)

            # 日志工具
            elif tool_name == "get_pod_logs":
                from .log_tools import get_pod_logs
                return get_pod_logs(fault_info, **kwargs)
            elif tool_name == "search_logs":
                from .log_tools import search_logs
                return search_logs(**kwargs)
            elif tool_name == "get_events_by_object":
                from .log_tools import get_events_by_object
                return get_events_by_object(**kwargs)

            else:
                return {"error": f"未知工具: {tool_name}"}

        except Exception as e:
            return {"error": f"工具执行失败: {str(e)}"}


# 将 _execute_tool 设为模块级 execute_tool
execute_tool = _execute_tool

# 导出所有工具函数（方便直接导入，但注意直接导入不受 mock_mode 控制）
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
]
