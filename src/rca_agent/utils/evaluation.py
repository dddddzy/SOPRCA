"""
evaluation.py - 论文评估指标计算
版本7: 工程化完善 - LA、TA、APL指标
"""

from typing import Dict, Any, List, Optional
import json
import os


class RCAResult:
    """单次RCA执行结果"""

    def __init__(
        self,
        fault_id: str,
        fault_info: str,
        ground_truth_root_cause: str,
        ground_truth_type: str,
        predicted_root_cause: str = "",
        predicted_type: str = "",
        found_root_cause: bool = False,
        path_length: int = 0,
        duration: float = 0.0,
        success: bool = False
    ):
        self.fault_id = fault_id
        self.fault_info = fault_info
        self.ground_truth_root_cause = ground_truth_root_cause
        self.ground_truth_type = ground_truth_type
        self.predicted_root_cause = predicted_root_cause
        self.predicted_type = predicted_type
        self.found_root_cause = found_root_cause
        self.path_length = path_length
        self.duration = duration
        self.success = success

    def to_dict(self) -> Dict:
        return {
            "fault_id": self.fault_id,
            "fault_info": self.fault_info,
            "ground_truth_root_cause": self.ground_truth_root_cause,
            "ground_truth_type": self.ground_truth_type,
            "predicted_root_cause": self.predicted_root_cause,
            "predicted_type": self.predicted_type,
            "found_root_cause": self.found_root_cause,
            "path_length": self.path_length,
            "duration": self.duration,
            "success": self.success
        }


class EvaluationEngine:
    """评估引擎"""

    def __init__(self):
        self.results: List[RCAResult] = []

    def add_result(self, result: RCAResult):
        """添加RCA结果"""
        self.results.append(result)

    def calculate_la(self) -> float:
        """
        计算LA（Root Cause Localization Accuracy）
        根因定位准确率 = 定位到真实根因的次数 / 总次数
        """
        if not self.results:
            return 0.0

        found_count = sum(1 for r in self.results if r.found_root_cause)
        return found_count / len(self.results)

    def calculate_ta(self) -> float:
        """
        计算TA（Root Cause Type Accuracy）
        根因类型准确率 = 根因类型正确的次数 / 总次数
        """
        if not self.results:
            return 0.0

        type_correct = sum(
            1 for r in self.results
            if r.predicted_type and r.predicted_type == r.ground_truth_type
        )
        return type_correct / len(self.results)

    def calculate_apl(self) -> float:
        """
        计算APL（Average Path Length）
        平均路径长度 = 所有成功RCA的路径长度之和 / 成功次数
        """
        successful_results = [r for r in self.results if r.success]

        if not successful_results:
            return 0.0

        total_path_length = sum(r.path_length for r in successful_results)
        return total_path_length / len(successful_results)

    def calculate_avg_duration(self) -> float:
        """计算平均执行时间"""
        if not self.results:
            return 0.0

        total_duration = sum(r.duration for r in self.results)
        return total_duration / len(self.results)

    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.results:
            return 0.0

        success_count = sum(1 for r in self.results if r.success)
        return success_count / len(self.results)

    def get_summary(self) -> Dict[str, Any]:
        """获取评估摘要"""
        return {
            "total_faults": len(self.results),
            "LA": self.calculate_la(),
            "TA": self.calculate_ta(),
            "APL": self.calculate_apl(),
            "avg_duration": self.calculate_avg_duration(),
            "success_rate": self.calculate_success_rate()
        }

    def save_results(self, filepath: str):
        """保存评估结果到文件"""
        data = {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results]
        }

        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_results(self, filepath: str):
        """从文件加载评估结果"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.results = []
        for r in data.get("results", []):
            result = RCAResult(
                fault_id=r["fault_id"],
                fault_info=r["fault_info"],
                ground_truth_root_cause=r["ground_truth_root_cause"],
                ground_truth_type=r["ground_truth_type"],
                predicted_root_cause=r.get("predicted_root_cause", ""),
                predicted_type=r.get("predicted_type", ""),
                found_root_cause=r.get("found_root_cause", False),
                path_length=r.get("path_length", 0),
                duration=r.get("duration", 0.0),
                success=r.get("success", False)
            )
            self.results.append(result)


def evaluate_single_rca(
    fault_id: str,
    fault_info: str,
    ground_truth_root_cause: str,
    ground_truth_type: str,
    judge_result: Dict[str, Any],
    executed_steps: List[Dict]
) -> RCAResult:
    """
    评估单次RCA结果

    Args:
        fault_id: 故障ID
        fault_info: 故障信息
        ground_truth_root_cause: 真实根因
        ground_truth_type: 真实根因类型
        judge_result: JudgeAgent的判定结果
        executed_steps: 已执行的步骤

    Returns:
        评估结果
    """
    found_root_cause = judge_result.get("is_root_cause_found", False)
    predicted_root_cause = judge_result.get("explanation", "")
    predicted_type = ""

    # 判断根因类型
    if "CPU" in predicted_root_cause or "cpu" in predicted_root_cause.lower():
        predicted_type = "CPU过高"
    elif "内存" in predicted_root_cause or "memory" in predicted_root_cause.lower():
        predicted_type = "内存过高"
    elif "OOM" in predicted_root_cause or "oom" in predicted_root_cause.lower():
        predicted_type = "内存溢出"

    # 判断是否找到真实根因
    is_correct = found_root_cause and (
        ground_truth_root_cause.lower() in predicted_root_cause.lower() or
        any(keyword in predicted_root_cause.lower() for keyword in ground_truth_root_cause.lower().split())
    )

    return RCAResult(
        fault_id=fault_id,
        fault_info=fault_info,
        ground_truth_root_cause=ground_truth_root_cause,
        ground_truth_type=ground_truth_type,
        predicted_root_cause=predicted_root_cause,
        predicted_type=predicted_type,
        found_root_cause=is_correct,
        path_length=len(executed_steps),
        duration=0.0,  # 应该在执行时记录
        success=is_correct
    )
