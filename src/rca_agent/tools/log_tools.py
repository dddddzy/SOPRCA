"""
log_tools.py - 日志相关工具
版本7: 工程化完善 - 对接日志系统
版本8: 支持kubeconfig配置
"""

import os
from typing import Dict, Any, List, Optional
import subprocess


def get_kubectl_cmd() -> str:
    """获取kubectl命令前缀（包含kubeconfig参数）"""
    kubeconfig_path = os.environ.get("KUBECONFIG_PATH", "kubeconfig.yaml")
    if not os.path.isabs(kubeconfig_path):
        current_dir = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        kubeconfig_path = os.path.join(project_root, kubeconfig_path)
    # 使用正斜杠（避免Windows路径问题）
    kubeconfig_path = kubeconfig_path.replace("\\", "/")
    return f"kubectl --kubeconfig={kubeconfig_path}"


def get_pod_logs(
    fault_info: str,
    namespace: str = "default",
    tail_lines: int = 100,
    previous: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    获取Pod日志

    Args:
        fault_info: 故障信息（包含Pod名称）
        namespace: 命名空间
        tail_lines: 返回最近多少行
        previous: 是否获取上次容器的日志（用于查看OOM）
        **kwargs: 忽略LLM传入的其他无效参数

    Returns:
        Pod日志
    """
    # 强制过滤无效参数，防止LLM幻觉
    _ = kwargs

    # 从故障信息提取Pod名
    pod_name = fault_info.split()[0] if fault_info else None

    if not pod_name:
        return {"error": "无法从故障信息中提取Pod名"}

    # 如果Pod名不完整（有可能是Deployment名），尝试获取匹配的Pod
    original_pod_name = pod_name
    if pod_name and not any(c.isdigit() for c in pod_name.split("-")[-1] if "-"):
        # Pod名不包含数字后缀，可能是Deployment名称，尝试前缀匹配
        try:
            kubectl_cmd = get_kubectl_cmd()
            # 使用jsonpath进行前缀匹配查询
            cmd = f'{kubectl_cmd} get pods -n {namespace} -o json'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                import json
                pods_data = json.loads(result.stdout)
                for item in pods_data.get("items", []):
                    pod_full_name = item.get("metadata", {}).get("name", "")
                    # 前缀匹配（pod_full_name以pod_name开头）
                    if pod_full_name.startswith(pod_name):
                        pod_name = pod_full_name
                        break
        except Exception:
            pass

    # 如果上述匹配失败，尝试直接在错误处理中通过kubectl describe找到正确Pod
    try:
        # 获取日志
        kubectl_cmd = get_kubectl_cmd()
        prev_flag = "--previous" if previous else ""
        cmd = f"{kubectl_cmd} logs {pod_name} -n {namespace} --tail={tail_lines} {prev_flag}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            # 如果是NotFound错误，尝试用Deployment名查找
            if "NotFound" in result.stderr or "not found" in result.stderr.lower():
                # 尝试通过kubectl describe找到正确的Pod
                describe_cmd = f'{kubectl_cmd} describe pod -n {namespace} -l app={original_pod_name}'
                describe_result = subprocess.run(describe_cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
                if describe_result.returncode == 0:
                    # 从describe输出中提取Pod名称
                    for line in describe_result.stdout.split('\n'):
                        if 'Name:' in line:
                            potential_pod = line.split('Name:')[1].strip()
                            if potential_pod:
                                # 递归尝试获取日志
                                return get_pod_logs(pault_info=potential_pod, namespace=namespace, tail_lines=tail_lines, previous=previous)
                return {"error": f"Pod '{original_pod_name}' 未找到，请提供完整Pod名称"}
            return {"error": result.stderr}

        # 提取关键错误信息
        logs = result.stdout
        errors = extract_errors(logs)

        return {
            "pod": pod_name,
            "namespace": namespace,
            "logs": logs[-5000:] if len(logs) > 5000 else logs,  # 限制返回长度
            "error_count": len(errors),
            "errors": errors[:10]  # 最多返回10个错误
        }

    except Exception as e:
        return {"error": str(e)}


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
    """
    搜索日志

    Args:
        keyword: 搜索关键词
        namespace: 命名空间
        since: 时间范围
        limit: 返回数量限制

    Returns:
        搜索结果
    """
    try:
        kubectl_cmd = get_kubectl_cmd()
        cmd = f'{kubectl_cmd} logs -n {namespace} --since={since} --tail=10000 | grep -i "{keyword}" | tail -{limit}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            return {"error": result.stderr}

        matches = result.stdout.strip().split("\n")

        return {
            "keyword": keyword,
            "namespace": namespace,
            "matches": matches[:limit],
            "count": len(matches)
        }

    except Exception as e:
        return {"error": str(e)}


def get_events_by_object(
    object_name: str,
    namespace: str = "default"
) -> Dict[str, Any]:
    """
    获取指定对象的事件

    Args:
        object_name: 对象名称（Pod/Service等）
        namespace: 命名空间

    Returns:
        事件列表
    """
    try:
        kubectl_cmd = get_kubectl_cmd()
        cmd = f"{kubectl_cmd} describe {object_name} -n {namespace}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')

        if result.returncode != 0:
            return {"error": result.stderr}

        # 提取Events部分
        output = result.stdout
        events_section = output.split("Events:")[-1] if "Events:" in output else ""

        events = []
        for line in events_section.split("\n")[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    events.append({
                        "type": parts[0] if parts[0] in ["Normal", "Warning"] else "Normal",
                        "reason": parts[1] if len(parts) > 1 else "",
                        "message": " ".join(parts[2:]) if len(parts) > 2 else ""
                    })

        return {
            "object": object_name,
            "namespace": namespace,
            "events": events[:20]
        }

    except Exception as e:
        return {"error": str(e)}
