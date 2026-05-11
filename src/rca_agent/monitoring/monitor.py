"""
monitor.py - 简单巡检监控
超阈值自动触发诊断
"""

import threading
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MonitorService:
    """简单监控服务"""

    def __init__(self):
        self._enabled = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_check = None
        self._last_trigger = None
        self._trigger_count = 0

        # 阈值配置
        self.thresholds = {
            'cpu_percent': 90,
            'memory_percent': 85,
            'disk_percent': 90,
            'restart_count': 3,
        }

        self._diagnosis_callback = None

    def set_diagnosis_callback(self, callback):
        """设置诊断回调，用于触发诊断"""
        self._diagnosis_callback = callback

    @property
    def is_running(self) -> bool:
        return self._enabled and self._thread is not None and self._thread.is_alive()

    def get_status(self) -> Dict[str, Any]:
        return {
            'enabled': self._enabled,
            'is_running': self.is_running,
            'last_check': self._last_check,
            'last_trigger': self._last_trigger,
            'trigger_count': self._trigger_count,
            'thresholds': self.thresholds
        }

    def toggle(self, enabled: bool = None) -> Dict[str, Any]:
        """切换监控状态"""
        if enabled is None:
            enabled = not self._enabled

        if enabled and not self._enabled:
            self._start()
        elif not enabled and self._enabled:
            self._stop()

        return self.get_status()

    def _start(self):
        """启动监控"""
        if self._thread and self._thread.is_alive():
            return

        self._enabled = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("[Monitor] 监控已启动")

    def _stop(self):
        """停止监控"""
        self._enabled = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("[Monitor] 监控已停止")

    def _run(self):
        """监控主循环"""
        import kubernetes
        from kubernetes import client, config
        import os

        # 尝试多种方式加载 K8s 配置
        # 1. 优先使用项目内的 kubeconfig.yaml
        kubeconfig_path = "kubeconfig.yaml"
        if not os.path.exists(kubeconfig_path):
            kubeconfig_path = os.path.expanduser("~/.kube/config")

        loaded = False
        for kf in ["kubeconfig.yaml", os.path.expanduser("~/.kube/config"), "/etc/kubernetes/admin.conf"]:
            if os.path.exists(kf):
                try:
                    config.load_kube_config(config_file=kf)
                    logger.info(f"[Monitor] 已加载 kubeconfig: {kf}")
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"[Monitor] 加载 {kf} 失败: {e}")

        if not loaded:
            try:
                config.load_incluster_config()
                logger.info("[Monitor] 使用 incluster 配置")
                loaded = True
            except Exception as e:
                logger.warning(f"[Monitor] 无法连接 K8s: {e}")
                return

        v1 = client.CoreV1Api()

        # 尝试获取 metrics API
        metrics_available = False
        try:
            custom_api = client.CustomObjectsApi()
            metrics = custom_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")
            metrics_available = True
            logger.info("[Monitor] metrics-server 可用")
        except Exception as e:
            logger.info(f"[Monitor] metrics-server 不可用: {e}")

        while not self._stop_event.is_set():
            try:
                self._last_check = time.strftime('%H:%M:%S')
                # 优先使用 metrics API，否则尝试 kubectl top
                pod_metrics = self._get_pod_metrics_by_kubectl()
                self._check_pods(v1, metrics_available, pod_metrics)

                # 每30秒检查一次
                self._stop_event.wait(30)
            except Exception as e:
                logger.error(f"[Monitor] 检查失败: {e}")
                self._stop_event.wait(30)

    def _get_pod_metrics_by_kubectl(self) -> Dict[str, float]:
        """使用 kubectl top pod 获取 CPU 使用率（millicores），作为 metrics-server 的备用"""
        pod_metrics = {}
        try:
            import subprocess
            import os
            import shutil
            kubectl_path = shutil.which('kubectl') or 'kubectl'
            # 优先使用项目内的 kubeconfig.yaml
            kubeconfig = "kubeconfig.yaml"
            if not os.path.exists(kubeconfig):
                kubeconfig = os.path.expanduser("~/.kube/config")
            env = os.environ.copy()
            env['KUBECONFIG'] = kubeconfig
            logger.info(f"[Monitor] 执行: {kubectl_path} top pods -A --kubeconfig={kubeconfig}")
            result = subprocess.run(
                [kubectl_path, 'top', 'pods', '--no-headers', '-A', '--kubeconfig', kubeconfig],
                capture_output=True, text=True, timeout=15, env=env
            )
            logger.info(f"[Monitor] kubectl top 返回码: {result.returncode}")
            if result.stdout:
                logger.info(f"[Monitor] kubectl top 输出(前500字符): {result.stdout[:500]}")
            if result.stderr:
                logger.warning(f"[Monitor] kubectl top stderr: {result.stderr[:200]}")
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        ns = parts[0]
                        name = parts[1]
                        cpu_str = parts[2]
                        key = f"{ns}/{name}"
                        # 解析 CPU，如 "120m" 或 "0.12"
                        if cpu_str.endswith('m'):
                            pod_metrics[key] = float(cpu_str[:-1])
                        else:
                            pod_metrics[key] = float(cpu_str) * 1000
                logger.info(f"[Monitor] kubectl top 获取到 {len(pod_metrics)} 个 Pod 指标")
            else:
                logger.warning(f"[Monitor] kubectl top 失败: {result.stderr[:200]}")
        except FileNotFoundError:
            logger.warning("[Monitor] kubectl 未找到，请确保已安装并配置在 PATH 中")
        except subprocess.TimeoutExpired:
            logger.warning("[Monitor] kubectl top 超时")
        except Exception as e:
            logger.warning(f"[Monitor] kubectl top 失败: {e}")
        return pod_metrics

    def _check_pods(self, v1, metrics_available=False, kubectl_metrics=None):
        """检查所有 Pod，找到超阈值的"""
        kubectl_metrics = kubectl_metrics or {}
        from kubernetes import client
        try:
            pods = v1.list_pod_for_all_namespaces(watch=False).items

            # 获取 metrics 数据（如果可用）
            pod_metrics = {}
            if metrics_available:
                try:
                    custom_api = client.CustomObjectsApi()
                    metrics = custom_api.list_cluster_custom_object(
                        "metrics.k8s.io", "v1beta1", "pods"
                    )
                    for item in metrics.get('items', []):
                        pod_name = item['metadata']['name']
                        pod_ns = item['metadata']['namespace']
                        key = f"{pod_ns}/{pod_name}"
                        containers = item.get('containers', [])
                        if containers:
                            # 使用第一个容器的 CPU 用量
                            cpu_nano = int(containers[0].get('usage', {}).get('cpu', '0'))
                            # 转换为 millicores
                            pod_metrics[key] = cpu_nano / 1000000
                except Exception as e:
                    logger.warning(f"[Monitor] 获取 metrics 失败: {e}")
                    metrics_available = False

            # 合并 kubectl top 数据到 pod_metrics
            for key, cpu_val in kubectl_metrics.items():
                if key not in pod_metrics:
                    pod_metrics[key] = cpu_val

            for pod in pods:
                # 只检测 default 和 kube-system 之外的 namespace（业务 Pod）
                if pod.metadata.namespace in ['kube-system', 'chaos-mesh', 'monitoring', 'observability']:
                    continue

                # 跳过 completed 和 failed 的 pods
                if pod.status.phase in ['Succeeded', 'Failed']:
                    continue

                # 获取 CPU 使用率
                cpu_percent = self._get_cpu_percent(pod, pod_metrics, metrics_available)
                pod_key = f"{pod.metadata.namespace}/{pod.metadata.name}"
                logger.info(f"[Monitor] 检查 Pod {pod_key}: CPU={cpu_percent}, 阈值={self.thresholds['cpu_percent']}")
                if cpu_percent and cpu_percent > self.thresholds['cpu_percent']:
                    msg = f"检测到异常: {pod.metadata.namespace}/{pod.metadata.name} CPU {cpu_percent}%"
                    logger.warning(f"[Monitor] {msg}")
                    self._trigger_diagnosis(msg, pod, cpu_percent)
                    continue

                # 检查重启次数（只针对非系统 Pod）
                restart_count = sum(
                    cs.restart_count for cs in (pod.status.container_statuses or [])
                )
                # 提高阈值到 10 次，避免系统 Pod 干扰
                if restart_count >= max(10, self.thresholds['restart_count']):
                    msg = f"检测到异常: {pod.metadata.namespace}/{pod.metadata.name} 重启 {restart_count} 次"
                    logger.warning(f"[Monitor] {msg}")
                    self._trigger_diagnosis(msg, pod, restart_count)

        except Exception as e:
            logger.error(f"[Monitor] 获取 Pod 列表失败: {e}")

    def _get_cpu_percent(self, pod, pod_metrics=None, metrics_available=False) -> Optional[float]:
        """获取 CPU 使用率（millicores）"""
        try:
            pod_key = f"{pod.metadata.namespace}/{pod.metadata.name}"

            # 如果有 metrics 数据（API 或 kubectl top），直接使用
            if pod_metrics and pod_key in pod_metrics:
                cpu_millicores = pod_metrics[pod_key]
                return cpu_millicores  # 返回 millicores 值，与阈值90比较

            # 备用：基于 container status 估算
            containers = pod.status.containers
            if not containers:
                return None

            # 获取 CPU limit
            for container in containers:
                resources = container.resources
                if resources and resources.limits and resources.limits.get('cpu'):
                    cpu_limit_str = resources.limits.get('cpu')
                    # 解析 CPU limit (如 "100m" 或 "1")
                    if cpu_limit_str.endswith('m'):
                        cpu_limit = int(cpu_limit_str[:-1])
                    else:
                        cpu_limit = int(float(cpu_limit_str) * 1000)

                    # 如果有 metrics，使用真实使用率
                    if metrics_available and pod_metrics and pod_key in pod_metrics:
                        usage = pod_metrics[pod_key]
                        return (usage / cpu_limit) * 100 if cpu_limit > 0 else None

                    # 否则返回 CPU 负载指示（stress chaos 会导致高 CPU）
                    # 这里无法准确获取，使用备用逻辑
                    return None

            return None

        except Exception:
            return None

    def _trigger_diagnosis(self, msg: str, pod, value):
        """触发诊断"""
        self._last_trigger = time.strftime('%H:%M:%S')
        self._trigger_count += 1

        logger.info(f"[Monitor] 触发诊断 ({self._trigger_count})")

        # 调用诊断回调
        if self._diagnosis_callback:
            try:
                self._diagnosis_callback(msg)
            except Exception as e:
                logger.error(f"[Monitor] 触发诊断失败: {e}")


# 全局单例
_monitor_service = MonitorService()

def get_monitor_service() -> MonitorService:
    return _monitor_service