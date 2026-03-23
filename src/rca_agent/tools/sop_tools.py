"""
sop_tools.py - SOP相关工具
"""

from typing import Dict, Any, Optional


def match_sop_tool(fault_info: str) -> Optional[Dict[str, Any]]:
    """匹配SOP工具"""
    from ..knowledge_base.sop_store import match_sop
    return match_sop(fault_info)


def generate_sop_tool(fault_info: str, similar_sops: list) -> Dict[str, Any]:
    """生成新SOP工具"""
    pass
