"""
sop_mock.py - SOP工具的Mock实现
对应真实工具: sop_tools.py
"""

from typing import Dict, Any, Optional


def match_sop_tool(fault_info: str) -> Optional[Dict[str, Any]]:
    """匹配SOP工具（Mock版本）

    注意：实际匹配逻辑在 knowledge_base.sop_store.match_sop
    这里仅作为工具映射的Mock实现
    """
    return {
        "success": True,
        "matched": False,
        "message": "Mock模式：未进行真实SOP匹配",
        "sop_name": None,
        "steps": []
    }


def generate_sop_tool(fault_info: str, similar_sops: list) -> Dict[str, Any]:
    """生成新SOP工具（Mock版本）

    注意：实际生成逻辑在 knowledge_base.generate_sop
    这里仅作为工具映射的兜底实现
    """
    return {
        "status": "success",
        "message": "Mock模式：SOP生成功能已通过tool_executor_node调用真实函数",
        "sop_name": "生成的SOP",
        "steps": []
    }
