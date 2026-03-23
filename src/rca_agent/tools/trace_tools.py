"""
trace_tools.py - 链路追踪相关工具
版本7: 工程化完善 - 对接Jaeger
"""

from typing import Dict, Any, List, Optional
import subprocess
import json


# Jaeger配置
JAEGER_URL = "http://192.168.100.132:30086"


def collect_trace(
    fault_info: str,
    service_name: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    收集链路追踪数据

    Args:
        fault_info: 故障信息
        service_name: 服务名称
        limit: 返回数量限制

    Returns:
        链路追踪数据
    """
    # 从故障信息提取服务名
    if not service_name:
        service_name = fault_info.split()[0] if fault_info else None

    if not service_name:
        return {"error": "无法从故障信息中提取服务名"}

    try:
        # 调用Jaeger API
        cmd = f'curl -s "{JAEGER_URL}/api/traces?service={service_name}&limit={limit}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return {"error": f"Jaeger API调用失败: {result.stderr or '未知错误'}"}

        data = json.loads(result.stdout)
        return parse_jaeger_response(data, service_name)

    except Exception as e:
        return {"error": f"获取链路追踪数据失败: {str(e)}"}


def parse_jaeger_response(data: Dict, service_name: str) -> Dict[str, Any]:
    """解析Jaeger响应"""
    try:
        traces = data.get("data", [])

        if not traces:
            return {"service": service_name, "traces": []}

        parsed_traces = []
        for trace in traces[:10]:
            spans = trace.get("spans", [])

            trace_data = {
                "trace_id": trace.get("traceID", ""),
                "duration": trace.get("duration", 0),
                "spans": [
                    {
                        "operation_name": span.get("operationName", ""),
                        "service": next((t.get("serviceName", "") for t in span.get("process", {}).get("tags", [])), ""),
                        "duration": span.get("duration", 0),
                        "status": "ok" if span.get("flags", 0) == 0 else "error"
                    }
                    for span in spans
                ]
            }
            parsed_traces.append(trace_data)

        return {
            "service": service_name,
            "traces": parsed_traces
        }

    except Exception as e:
        return {"error": str(e)}


def analyze_trace_latency(
    service_name: str,
    percentiles: List[int] = [50, 90, 99]
) -> Dict[str, Any]:
    """
    分析链路延迟

    Args:
        service_name: 服务名称
        percentiles: 百分位数列表

    Returns:
        延迟分析结果
    """
    try:
        cmd = f'curl -s "{JAEGER_URL}/api/traces?service={service_name}&limit=100"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return {"error": f"Jaeger API调用失败: {result.stderr or '未知错误'}"}

        data = json.loads(result.stdout)
        traces = data.get("data", [])
        if not traces:
            return {"error": f"未找到服务 {service_name} 的链路数据"}

        # 计算延迟百分位数（从span duration计算）
        durations = []
        for trace in traces:
            for span in trace.get("spans", []):
                if span.get("duration"):
                    durations.append(span["duration"])

        if not durations:
            return {"error": "未找到有效链路数据"}

        durations.sort()
        result_percentiles = {}
        for p in percentiles:
            idx = int(len(durations) * p / 100)
            idx = min(idx, len(durations) - 1)
            result_percentiles[f"p{p}"] = durations[idx]

        return {
            "service": service_name,
            "percentiles": result_percentiles
        }

    except Exception as e:
        return {"error": f"分析链路延迟失败: {str(e)}"}
