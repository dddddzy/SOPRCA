"""
metric_tools.py - 指标相关工具
版本7: 工程化完善 - 对接Prometheus
版本8: 使用Prometheus HTTP API获取指标
"""

import os
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin


# Prometheus 配置
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://192.168.100.132:30090/")
PROMETHEUS_USER = os.environ.get("PROMETHEUS_USER", "admin")
PROMETHEUS_PASSWORD = os.environ.get("PROMETHEUS_PASSWORD", "qwer1234")


def _query_prometheus(query: str) -> dict:
    """
    向Prometheus发送查询请求

    Args:
        query: PromQL查询语句

    Returns:
        Prometheus API响应字典，包含status和data
    """
    url = urljoin(PROMETHEUS_URL, "/api/v1/query")
    try:
        response = requests.get(
            url,
            params={"query": query},
            auth=(PROMETHEUS_USER, PROMETHEUS_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        # 检查Prometheus返回状态
        if result.get("status") == "success":
            return result
        else:
            print(f"[Prometheus Query] API返回非success状态: {result}")
            return {"status": "error", "data": {"result": []}}

    except requests.exceptions.Timeout:
        print(f"[Prometheus Query] 请求超时: {query}")
        return {"status": "error", "data": {"result": []}, "error": "请求超时"}
    except requests.exceptions.ConnectionError as e:
        print(f"[Prometheus Query] 连接失败: {e}")
        return {"status": "error", "data": {"result": []}, "error": f"连接失败: {e}"}
    except requests.exceptions.HTTPError as e:
        print(f"[Prometheus Query] HTTP错误: {e}")
        return {"status": "error", "data": {"result": []}, "error": f"HTTP错误: {e}"}
    except Exception as e:
        print(f"[Prometheus Query] 未知错误: {e}")
        return {"status": "error", "data": {"result": []}, "error": str(e)}


def _parse_cpu_value(cpu_str: str) -> float:
    """
    解析CPU字符串为毫核数值（millicores）

    Args:
        cpu_str: CPU字符串，如 "500m", "0.5", "1"

    Returns:
        毫核数值，如 500 表示 0.5核
    """
    cpu_str = cpu_str.strip()
    if not cpu_str or cpu_str == "0":
        return 0.0

    # 单位：毫核 (如 "500m")
    if cpu_str.endswith("m"):
        try:
            return float(cpu_str[:-1])
        except ValueError:
            return 0.0

    # 无单位小数 (如 "0.5")
    try:
        return float(cpu_str) * 1000
    except ValueError:
        return 0.0


def _parse_memory_value(mem_str: str) -> float:
    """
    解析内存字符串为MiB数值

    Args:
        mem_str: 内存字符串，如 "512Mi", "1Gi", "524288Ki"

    Returns:
        MiB数值
    """
    mem_str = mem_str.strip()
    if not mem_str:
        return 0.0

    units = {
        "Ki": 1.0 / 1024,      # Kibibyte -> MiB
        "Mi": 1.0,              # Mibibyte -> MiB
        "Gi": 1024.0,           # Gibibyte -> MiB
        "Ki": 1.0 / 1024,
        "K": 1.0 / 1024,       # Kilobyte (IEC兼容)
        "M": 1.0,              # Megabyte
        "G": 1024.0,           # Gigabyte
    }

    # 尝试分离数字和单位
    for unit in sorted(units.keys(), key=len, reverse=True):
        if mem_str.endswith(unit):
            num_part = mem_str[:-len(unit)]
            try:
                value = float(num_part)
                return value * units[unit]
            except ValueError:
                return 0.0

    # 纯数字（假设是bytes）
    try:
        return float(mem_str) / (1024 * 1024)
    except ValueError:
        return 0.0


def get_relevant_metric(
    fault_info: str,
    metric_name: Optional[str] = None,
    namespace: str = "default",
    duration: str = "5m"
) -> Dict[str, Any]:
    """
    获取相关指标数据

    Args:
        fault_info: 故障信息
        metric_name: 指标名称，如果为None则自动推断 (cpu/memory/network)
        namespace: 命名空间
        duration: 查询时间范围（PromQL的[r]）

    Returns:
        指标数据（与原kubectl top格式兼容）
    """
    # 如果没有指定指标名，从故障信息推断
    if not metric_name:
        fault_lower = fault_info.lower()
        if "cpu" in fault_lower:
            metric_name = "cpu"
        elif "内存" in fault_info or "memory" in fault_lower:
            metric_name = "memory"
        elif "网络" in fault_info or "network" in fault_lower:
            metric_name = "network"
        else:
            metric_name = "cpu"

    try:
        pods_data = []

        if metric_name == "cpu":
            # PromQL: 获取过去1分钟的CPU使用率（毫核）
            query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!=""}}[1m])) by (pod)'
            result = _query_prometheus(query)

            if result.get("status") == "success":
                for item in result.get("data", {}).get("result", []):
                    pod_name = item.get("metric", {}).get("pod", "")
                    # container_cpu_usage_seconds_total 是累积计数器，rate()得到的是核数/秒，乘以1000得到毫核
                    cpu_value = item.get("value", [0, 0])[1]
                    cpu_millicores = float(cpu_value) * 1000
                    pods_data.append({
                        "name": pod_name,
                        "cpu": f"{cpu_millicores:.0f}m"
                    })

            if not pods_data:
                # Fallback: 尝试 alternative 指标名
                query_alt = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[1m])) by (pod)'
                result_alt = _query_prometheus(query_alt)
                if result_alt.get("status") == "success":
                    for item in result_alt.get("data", {}).get("result", []):
                        pod_name = item.get("metric", {}).get("pod", "")
                        cpu_value = item.get("value", [0, 0])[1]
                        cpu_millicores = float(cpu_value) * 1000
                        pods_data.append({
                            "name": pod_name,
                            "cpu": f"{cpu_millicores:.0f}m"
                        })

            return {
                "success": True,
                "metric_type": "cpu",
                "namespace": namespace,
                "pods": pods_data
            }

        elif metric_name == "memory":
            # PromQL: 获取内存使用量（Working Set Bytes）
            query = f'sum(container_memory_working_set_bytes{{namespace="{namespace}", container!=""}}) by (pod)'
            result = _query_prometheus(query)

            if result.get("status") == "success":
                for item in result.get("data", {}).get("result", []):
                    pod_name = item.get("metric", {}).get("pod", "")
                    mem_bytes = float(item.get("value", [0, 0])[1])
                    mem_mib = mem_bytes / (1024 * 1024)
                    pods_data.append({
                        "name": pod_name,
                        "memory": f"{mem_mib:.0f}Mi"
                    })

            if not pods_data:
                # Fallback: 尝试不含container!=""的查询
                query_alt = f'sum(container_memory_working_set_bytes{{namespace="{namespace}"}}) by (pod)'
                result_alt = _query_prometheus(query_alt)
                if result_alt.get("status") == "success":
                    for item in result_alt.get("data", {}).get("result", []):
                        pod_name = item.get("metric", {}).get("pod", "")
                        mem_bytes = float(item.get("value", [0, 0])[1])
                        mem_mib = mem_bytes / (1024 * 1024)
                        pods_data.append({
                            "name": pod_name,
                            "memory": f"{mem_mib:.0f}Mi"
                        })

            return {
                "success": True,
                "metric_type": "memory",
                "namespace": namespace,
                "pods": pods_data
            }

        elif metric_name == "network":
            # PromQL: 获取网络接收速率（Bytes/s）
            query_rx = f'sum(rate(container_network_receive_bytes_total{{namespace="{namespace}"}}[1m])) by (pod)'
            result_rx = _query_prometheus(query_rx)

            # PromQL: 获取网络发送速率（Bytes/s）
            query_tx = f'sum(rate(container_network_transmit_bytes_total{{namespace="{namespace}"}}[1m])) by (pod)'
            result_tx = _query_prometheus(query_tx)

            # PromQL: 获取网络错误包数（接收方向）
            query_err = f'sum(rate(container_network_receive_errors_total{{namespace="{namespace}"}}[1m])) by (pod)'
            result_err = _query_prometheus(query_err)

            # 建立pod名称到tx/err数据的索引
            tx_map = {}
            err_map = {}
            if result_tx.get("status") == "success":
                for item in result_tx.get("data", {}).get("result", []):
                    pod_name = item.get("metric", {}).get("pod", "")
                    tx_bytes_per_sec = float(item.get("value", [0, 0])[1])
                    tx_map[pod_name] = tx_bytes_per_sec
            if result_err.get("status") == "success":
                for item in result_err.get("data", {}).get("result", []):
                    pod_name = item.get("metric", {}).get("pod", "")
                    err_count = float(item.get("value", [0, 0])[1])
                    err_map[pod_name] = err_count

            if result_rx.get("status") == "success":
                for item in result_rx.get("data", {}).get("result", []):
                    pod_name = item.get("metric", {}).get("pod", "")
                    rx_bytes_per_sec = float(item.get("value", [0, 0])[1])

                    # 格式化 rx
                    if rx_bytes_per_sec > 1024 * 1024:
                        rx_str = f"{rx_bytes_per_sec / (1024 * 1024):.1f}MB/s"
                    elif rx_bytes_per_sec > 1024:
                        rx_str = f"{rx_bytes_per_sec / 1024:.1f}KB/s"
                    else:
                        rx_str = f"{rx_bytes_per_sec:.0f}B/s"

                    pod_entry = {"name": pod_name, "network_rx": rx_str}

                    # 格式化 tx
                    if pod_name in tx_map:
                        tx_bytes_per_sec = tx_map[pod_name]
                        if tx_bytes_per_sec > 1024 * 1024:
                            tx_str = f"{tx_bytes_per_sec / (1024 * 1024):.1f}MB/s"
                        elif tx_bytes_per_sec > 1024:
                            tx_str = f"{tx_bytes_per_sec / 1024:.1f}KB/s"
                        else:
                            tx_str = f"{tx_bytes_per_sec:.0f}B/s"
                        pod_entry["network_tx"] = tx_str

                    # 记录网络错误包（如果有）
                    if pod_name in err_map and err_map[pod_name] > 0:
                        pod_entry["network_errors"] = f"{err_map[pod_name]:.0f}/s"

                    pods_data.append(pod_entry)

            # 版本9：跨模态诊断提示，引导大模型调用Trace工具
            diagnostic_hint = (
                "注意：Prometheus 基础网络指标仅反映吞吐量，无法直接体现 TCP 阻塞或业务延迟。 "
                "如果日志或事件中存在 'timeout'、'deadline'、'connection reset' 等超时报错，"
                "强烈建议调用 trace_tools（如 collect_trace 或 analyze_trace_latency）进一步分析具体的请求调用链耗时。"
            )

            return {
                "success": True,
                "metric_type": "network",
                "namespace": namespace,
                "pods": pods_data,
                "diagnostic_hint": diagnostic_hint
            }

        else:
            return {
                "success": False,
                "error": f"不支持的指标类型: {metric_name}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"获取指标失败: {str(e)}"
        }


def whether_is_abnormal_metric(
    metric_name: str,
    threshold: float = 80.0,
    namespace: str = "default"
) -> Dict[str, Any]:
    """
    判断指标是否异常

    Args:
        metric_name: 指标名称 (cpu/memory)
        threshold: 阈值（百分比，0-100）
        namespace: 命名空间

    Returns:
        异常判断结果
    """
    try:
        abnormal_pods = []

        if metric_name == "cpu":
            # 获取CPU使用率（毫核）
            query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", container!=""}}[1m])) by (pod)'
            result = _query_prometheus(query)

            if result.get("status") != "success":
                return {
                    "is_abnormal": False,
                    "reason": f"Prometheus查询失败: {result.get('error', '未知错误')}"
                }

            for item in result.get("data", {}).get("result", []):
                pod_name = item.get("metric", {}).get("pod", "")
                cpu_value = float(item.get("value", [0, 0])[1])
                cpu_millicores = cpu_value * 1000

                # 阈值判断：threshold是百分比，假设1核=100%
                # 如果CPU使用超过 threshold% 的1核，即 threshold m
                threshold_m = threshold * 10  # 80% -> 800m
                if cpu_millicores > threshold_m:
                    abnormal_pods.append({
                        "pod": pod_name,
                        "cpu": f"{cpu_millicores:.0f}m",
                        "cpu_percent": cpu_millicores / 10  # 转换为百分比
                    })

        elif metric_name == "memory":
            # 获取内存使用量（Bytes）
            query = f'sum(container_memory_working_set_bytes{{namespace="{namespace}", container!=""}}) by (pod)'
            result = _query_prometheus(query)

            if result.get("status") != "success":
                return {
                    "is_abnormal": False,
                    "reason": f"Prometheus查询失败: {result.get('error', '未知错误')}"
                }

            for item in result.get("data", {}).get("result", []):
                pod_name = item.get("metric", {}).get("pod", "")
                mem_bytes = float(item.get("value", [0, 0])[1])
                mem_mib = mem_bytes / (1024 * 1024)

                # threshold是百分比，假设100Mi = 100%
                if mem_mib > threshold:  # 直接用MiB对比百分比
                    abnormal_pods.append({
                        "pod": pod_name,
                        "memory": f"{mem_mib:.0f}Mi",
                        "memory_percent": mem_mib  # 简化处理
                    })

        elif metric_name == "network":
            # PromQL: 获取网络错误包速率
            query_err = f'sum(rate(container_network_receive_errors_total{{namespace="{namespace}"}}[1m])) by (pod)'
            result_err = _query_prometheus(query_err)

            if result_err.get("status") != "success":
                return {
                    "is_abnormal": False,
                    "reason": f"Prometheus查询失败: {result_err.get('error', '未知错误')}"
                }

            abnormal_pods = []
            for item in result_err.get("data", {}).get("result", []):
                pod_name = item.get("metric", {}).get("pod", "")
                err_rate = float(item.get("value", [0, 0])[1])
                if err_rate > 0:
                    abnormal_pods.append({
                        "pod": pod_name,
                        "network_errors": f"{err_rate:.2f}/s"
                    })

            if abnormal_pods:
                return {
                    "is_abnormal": True,
                    "reason": "检测到网络错误包增速 > 0，存在网络异常",
                    "abnormal_pods": abnormal_pods
                }

            # 基础吞吐正常，但无法排除延迟问题
            return {
                "is_abnormal": False,
                "reason": "基础网络吞吐正常，但 Prometheus 基础指标无法体现 TCP 重传或业务层延迟，建议查阅 Trace（collect_trace / analyze_trace_latency）进一步排查"
            }

        else:
            return {
                "is_abnormal": False,
                "reason": f"不支持的指标类型: {metric_name}"
            }

        if abnormal_pods:
            return {
                "is_abnormal": True,
                "threshold": threshold,
                "abnormal_pods": abnormal_pods
            }

        return {
            "is_abnormal": False,
            "threshold": threshold,
            "message": "未检测到异常"
        }

    except Exception as e:
        return {
            "is_abnormal": False,
            "reason": f"Prometheus 查询失败: {str(e)}"
        }
