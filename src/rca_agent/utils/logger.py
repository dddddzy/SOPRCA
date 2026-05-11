"""
logger.py - 全链路日志与审计日志器
版本6: 沙箱安全执行 + 防死循环与审计
版本7: 添加SSE日志回调支持
"""

import logging
import os
import time
import sys
from typing import Any, Dict, Optional, Callable
from datetime import datetime

# 日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/runtime.log"),
        logging.StreamHandler()
    ]
)

# 审计日志器
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler(f"{LOG_DIR}/audit.log")
audit_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
audit_logger.addHandler(audit_handler)

# SSE日志回调 - 用于将日志实时推送到前端
_sse_log_callback: Optional[Callable[[str], None]] = None

def set_sse_log_callback(callback: Callable[[str], None]):
    """设置SSE日志回调，用于将日志实时推送到前端"""
    global _sse_log_callback
    _sse_log_callback = callback

def clear_sse_log_callback():
    """清除SSE日志回调"""
    global _sse_log_callback
    _sse_log_callback = None

class AuditLogger:
    """审计日志记录器"""

    @staticmethod
    def log_node_entry(node_name: str, state: Dict[str, Any]):
        """记录节点入口"""
        msg = f"[NODE_ENTRY] {node_name}"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_node_exit(node_name: str, state: Dict[str, Any]):
        """记录节点出口"""
        msg = f"[NODE_EXIT] {node_name}"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_tool_call(tool_name: str, params: Dict, result: Any, duration: float):
        """记录工具调用"""
        msg = f"[TOOL_CALL] tool={tool_name} duration={duration:.2f}s"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_action(action: str, explanation: str):
        """记录动作选择"""
        msg = f"[ACTION] {action}: {explanation}"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_judge(judge_result: Dict[str, Any]):
        """记录判定结果"""
        is_found = judge_result.get("is_root_cause_found", False)
        msg = f"[JUDGE] root_cause_found={is_found}"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_termination(reason: str):
        """记录终止原因"""
        msg = f"[TERMINATE] {reason}"
        audit_logger.info(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log_error(error: str):
        """记录错误"""
        msg = f"[ERROR] {error}"
        audit_logger.error(msg)
        if _sse_log_callback:
            _sse_log_callback(msg)

    @staticmethod
    def log(msg: str):
        """通用日志 - 同时输出到stderr和SSE"""
        print(msg, file=sys.stderr)
        if _sse_log_callback:
            _sse_log_callback(msg)


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.duration = time.time() - self.start_time
        if self.name:
            audit_logger.info(f"[TIMER] {self.name}: {self.duration:.2f}s")
