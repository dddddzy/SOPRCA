"""
trace_mock.py - 链路追踪工具的Mock实现
对应真实工具: trace_tools.py
"""

from typing import Dict, Any, List, Optional


def collect_trace(
    fault_info: str,
    service_name: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """收集链路追踪数据"""
    if not service_name:
        service_name = fault_info.split()[0] if fault_info else "unknown"

    return {
        "success": True,
        "service": service_name,
        "traces": [
            {
                "trace_id": "abc123def456",
                "duration": 100,
                "spans": [
                    {
                        "operation_name": "/api/product",
                        "service": service_name,
                        "duration": 50,
                        "status": "ok"
                    },
                    {
                        "operation_name": "/api/catalog",
                        "service": service_name,
                        "duration": 30,
                        "status": "ok"
                    }
                ]
            },
            {
                "trace_id": "abc123def456",
                "duration": 550, # 模拟 500ms 网络延迟
                "spans": [
                    {
                        "operation_name": "/cart/checkout",
                        "service": service_name,
                        "duration": 520, # 核心超时点
                        "status": "error"
                    }
                ]
            },
            {
                "trace_id": "def789ghi012",
                "duration": 150,
                "spans": [
                    {
                        "operation_name": "/api/product",
                        "service": service_name,
                        "duration": 80,
                        "status": "ok"
                    },
                    {
                        "operation_name": "/api/review",
                        "service": service_name,
                        "duration": 60,
                        "status": "ok"
                    }
                ]
            }
        ]
    }


def parse_jaeger_response(data: Dict, service_name: str) -> Dict[str, Any]:
    """解析Jaeger响应（Mock版本）"""
    return {
        "service": service_name,
        "traces": []
    }


def analyze_trace_latency(
    service_name: str,
    percentiles: List[int] = [50, 90, 99]
) -> Dict[str, Any]:
    """分析链路延迟"""
    return {
        "success": True,
        "service": service_name,
        "percentiles": {
            "p50": 50,
            "p90": 120,
            "p99": 200
        },
        "unit": "ms"
    }
