"""
k8s_tools.py - Kubernetes相关工具
版本7: 工程化完善 - 对接真实K8s环境
版本8: 支持kubeconfig配置
"""

import os
from typing import Dict, Any, Optional
import subprocess


def get_kubectl_cmd() -> str:
    """获取kubectl命令前缀（包含kubeconfig参数）"""
    # 从配置读取kubeconfig路径
    kubeconfig_path = os.environ.get("KUBECONFIG_PATH", "kubeconfig.yaml")
    # 转换为绝对路径
    if not os.path.isabs(kubeconfig_path):
        # 获取项目根目录（src/rca_agent/tools向上4层）
        current_dir = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        kubeconfig_path = os.path.join(project_root, kubeconfig_path)
    # 使用正斜杠（避免Windows路径问题）
    kubeconfig_path = kubeconfig_path.replace("\\", "/")
    return f"kubectl --kubeconfig={kubeconfig_path}"


def pod_analyze(fault_info: str, namespace: str = "default") -> Dict[str, Any]:
    """
    分析Pod状态

    Args:
        fault_info: 故障信息
        namespace: Kubernetes命名空间

    Returns:
        Pod状态分析结果（包含CPU/内存限制和请求配置）
    """
    try:
        # 获取Pod列表（包含完整资源信息）
        kubectl_cmd = get_kubectl_cmd()
        cmd = f"{kubectl_cmd} get pods -n {namespace} -o json"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore'
        )

        if result.returncode != 0:
            return {"error": result.stderr}

        import json
        pods = json.loads(result.stdout)

        # 提取关键信息（包括资源限制）
        pod_info = []
        for item in pods.get("items", []):
            status = item.get("status", {})
            spec = item.get("spec", {})
            container_statuses = status.get("containerStatuses", [])

            # 提取容器资源限制和请求
            containers = spec.get("containers", [])
            container_resources = []
            for container in containers:
                resources = container.get("resources", {})
                limits = resources.get("limits", {})
                requests = resources.get("requests", {})

                container_resources.append({
                    "name": container.get("name", ""),
                    "cpu_limit": limits.get("cpu", "未设置"),
                    "memory_limit": limits.get("memory", "未设置"),
                    "cpu_request": requests.get("cpu", "未设置"),
                    "memory_request": requests.get("memory", "未设置")
                })

            pod_data = {
                "name": item["metadata"]["name"],
                "status": status.get("phase", "Unknown"),
                "restarts": sum(cs.get("restartCount", 0) for cs in container_statuses),
                "ready": sum(1 for cs in container_statuses if cs.get("ready", False)),
                "total": len(container_statuses),
                "containers": container_resources
            }
            pod_info.append(pod_data)

        return {"pods": pod_info, "namespace": namespace}

    except Exception as e:
        return {"error": str(e)}


def service_analyze(fault_info: str, namespace: str = "default") -> Dict[str, Any]:
    """
    分析Service状态

    Args:
        fault_info: 故障信息
        namespace: Kubernetes命名空间

    Returns:
        Service状态分析结果
    """
    try:
        kubectl_cmd = get_kubectl_cmd()
        cmd = f"{kubectl_cmd} get svc -n {namespace} -o json"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore'
        )

        if result.returncode != 0:
            return {"error": result.stderr}

        import json
        services = json.loads(result.stdout)

        service_info = []
        for item in services.get("items", []):
            spec = item.get("spec", {})
            service_data = {
                "name": item["metadata"]["name"],
                "type": spec.get("type", "ClusterIP"),
                "cluster_ip": spec.get("clusterIP", "None"),
                "ports": [p.get("port") for p in spec.get("ports", [])],
                "selector": spec.get("selector", {})
            }
            service_info.append(service_data)

        return {"services": service_info, "namespace": namespace}

    except Exception as e:
        return {"error": str(e)}


def check_events(
    namespace: str = "default",
    since_seconds: int = 3600,
    pod_prefix: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    检查最近的事件
    """
    _ = kwargs  # 忽略所有额外参数

    try:
        kubectl_cmd = get_kubectl_cmd()

        # 【修改点1】：去掉脆弱的 --sort-by 参数，直接拉取所有事件
        cmd = f"{kubectl_cmd} get events -n {namespace} -o json"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore'
        )

        if result.returncode != 0:
            return {"error": result.stderr}

        import json
        events = json.loads(result.stdout)

        from datetime import datetime, timedelta
        # 注意：K8s事件时间戳是UTC（带Z后缀），所以阈值也要用UTC计算
        threshold = datetime.utcnow() - timedelta(seconds=since_seconds)
        threshold_str = threshold.strftime('%Y-%m-%dT%H:%M:%S')

        event_list = []
        for item in events.get("items", []):
            # 【修改点2】：兼容不同 K8s 版本的事件时间字段
            last_timestamp = item.get("lastTimestamp") or item.get("eventTime") or item.get("metadata", {}).get("creationTimestamp", "")
            # 去掉末尾Z（UTC标记），避免字符串比较出错
            if last_timestamp and last_timestamp.endswith('Z'):
                last_timestamp = last_timestamp[:-1]

            # 时间过滤：如果事件太旧则跳过（空timestamp直接跳过）
            if not last_timestamp or last_timestamp < threshold_str:
                continue

            # 如果指定了pod_prefix，只返回相关事件
            if pod_prefix:
                involved_object = item.get("involvedObject", {})
                object_name = involved_object.get("name", "")
                if not object_name.startswith(pod_prefix):
                    continue

            event_data = {
                "type": item.get("type", "Normal"),
                "reason": item.get("reason", ""),
                "message": item.get("message", ""),
                "object": item.get("involvedObject", {}).get("name", ""),
                "count": item.get("count", 1),
                "last_seen": last_timestamp
            }
            event_list.append(event_data)

        # 【修改点3】：在 Python 中根据时间倒序排序（最新的在前面）
        event_list.sort(key=lambda x: x["last_seen"], reverse=True)

        # 限制返回数量（最新20条）
        event_list = event_list[:20]

        return {"events": event_list, "namespace": namespace}

    except Exception as e:
        return {"error": str(e)}


def get_node_status() -> Dict[str, Any]:
    """获取Node状态"""
    try:
        kubectl_cmd = get_kubectl_cmd()
        cmd = f"{kubectl_cmd} get nodes -o json"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore'
        )

        if result.returncode != 0:
            return {"error": result.stderr}

        import json
        nodes = json.loads(result.stdout)

        node_info = []
        for item in nodes.get("items", []):
            status = item.get("status", {})
            node_data = {
                "name": item["metadata"]["name"],
                "status": next((c.get("type") for c in status.get("conditions", []) if c.get("type") == "Ready"), "Unknown"),
                "roles": list(item.get("metadata", {}).get("labels", {}).get("node-role.kubernetes.io/", "").split(",")),
                "version": status.get("nodeInfo", {}).get("kubeletVersion", "")
            }
            node_info.append(node_data)

        return {"nodes": node_info}

    except Exception as e:
        return {"error": str(e)}


def run_kubectl_command(command: str) -> Dict[str, Any]:
    """
    执行任意kubectl命令（需谨慎使用）

    Args:
        command: kubectl命令

    Returns:
        命令执行结果
    """
    # 安全检查：只允许查询类命令
    safe_commands = ["get", "describe", "logs", "top", "events"]
    is_safe = any(command.strip().startswith(safe) for safe in safe_commands)

    if not is_safe:
        return {"error": "只允许执行查询类命令 (get, describe, logs, top, events)"}

    try:
        kubectl_cmd = get_kubectl_cmd()
        result = subprocess.run(
            f"{kubectl_cmd} {command}", shell=True, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore'
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}
