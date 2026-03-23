"""
logger.py - 全链路日志与审计日志器
版本6: 沙箱安全执行 + 防死循环与审计
"""

import logging
import os
import time
from typing import Any, Dict, Optional
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


class AuditLogger:
    """审计日志记录器"""

    @staticmethod
    def log_node_entry(node_name: str, state: Dict[str, Any]):
        """记录节点入口"""
        audit_logger.info(f"[NODE_ENTRY] {node_name}")

    @staticmethod
    def log_node_exit(node_name: str, state: Dict[str, Any]):
        """记录节点出口"""
        audit_logger.info(f"[NODE_EXIT] {node_name}")

    @staticmethod
    def log_tool_call(tool_name: str, params: Dict, result: Any, duration: float):
        """记录工具调用"""
        audit_logger.info(
            f"[TOOL_CALL] tool={tool_name} duration={duration:.2f}s"
        )

    @staticmethod
    def log_action(action: str, explanation: str):
        """记录动作选择"""
        audit_logger.info(f"[ACTION] {action}: {explanation}")

    @staticmethod
    def log_judge(judge_result: Dict[str, Any]):
        """记录判定结果"""
        is_found = judge_result.get("is_root_cause_found", False)
        audit_logger.info(f"[JUDGE] root_cause_found={is_found}")

    @staticmethod
    def log_termination(reason: str):
        """记录终止原因"""
        audit_logger.info(f"[TERMINATE] {reason}")

    @staticmethod
    def log_error(error: str):
        """记录错误"""
        audit_logger.error(f"[ERROR] {error}")


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
