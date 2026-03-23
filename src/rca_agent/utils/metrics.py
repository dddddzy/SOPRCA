"""
metrics.py - 框架运行指标暴露
版本7: 工程化完善 - Prometheus指标监控
"""

from typing import Dict, Any
import time
from functools import wraps

# 简单的内存指标存储（生产环境应使用Prometheus）
_metrics_store = {
    "rca_total": 0,
    "rca_success": 0,
    "rca_failed": 0,
    "rca_timeout": 0,
    "path_lengths": [],
    "durations": [],
    "start_time": time.time()
}


def record_rca_start():
    """记录RCA开始"""
    _metrics_store["rca_total"] += 1


def record_rca_success(path_length: int, duration: float):
    """记录RCA成功"""
    _metrics_store["rca_success"] += 1
    _metrics_store["path_lengths"].append(path_length)
    _metrics_store["durations"].append(duration)


def record_rca_failed():
    """记录RCA失败"""
    _metrics_store["rca_failed"] += 1


def record_rca_timeout():
    """记录RCA超时"""
    _metrics_store["rca_timeout"] += 1


def get_metrics() -> Dict[str, Any]:
    """获取所有指标"""
    total = _metrics_store["rca_total"]
    success = _metrics_store["rca_success"]
    failed = _metrics_store["rca_failed"]
    timeout = _metrics_store["rca_timeout"]

    path_lengths = _metrics_store["path_lengths"]
    durations = _metrics_store["durations"]

    # 计算平均值
    avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "rca_total": total,
        "rca_success": success,
        "rca_failed": failed,
        "rca_timeout": timeout,
        "success_rate": success / total if total > 0 else 0,
        "avg_path_length": avg_path_length,
        "avg_duration": avg_duration,
        "uptime": time.time() - _metrics_store["start_time"]
    }


def reset_metrics():
    """重置指标"""
    global _metrics_store
    _metrics_store = {
        "rca_total": 0,
        "rca_success": 0,
        "rca_failed": 0,
        "rca_timeout": 0,
        "path_lengths": [],
        "durations": [],
        "start_time": time.time()
    }


class RCA_metrics:
    """RCA指标上下文管理器"""

    def __init__(self):
        self.start_time = None
        self.path_length = 0

    def __enter__(self):
        self.start_time = time.time()
        record_rca_start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is not None:
            record_rca_failed()
        else:
            record_rca_success(self.path_length, duration)

    def set_path_length(self, length: int):
        """设置路径长度"""
        self.path_length = length


# Prometheus格式暴露（可选）
def get_prometheus_metrics() -> str:
    """获取Prometheus格式的指标"""
    metrics = get_metrics()

    lines = [
        "# HELP rca_total RCA总次数",
        "# TYPE rca_total counter",
        f'rca_total {metrics["rca_total"]}',
        "",
        "# HELP rca_success RCA成功次数",
        "# TYPE rca_success counter",
        f'rca_success {metrics["rca_success"]}',
        "",
        "# HELP rca_failed RCA失败次数",
        "# TYPE rca_failed counter",
        f'rca_failed {metrics["rca_failed"]}',
        "",
        "# HELP success_rate RCA成功率",
        "# TYPE success_rate gauge",
        f'success_rate {metrics["success_rate"]:.4f}',
        "",
        "# HELP avg_path_length 平均路径长度",
        "# TYPE avg_path_length gauge",
        f'avg_path_length {metrics["avg_path_length"]:.2f}',
        "",
        "# HELP avg_duration 平均执行时间",
        "# TYPE avg_duration gauge",
        f'avg_duration {metrics["avg_duration"]:.2f}',
    ]

    return "\n".join(lines)
