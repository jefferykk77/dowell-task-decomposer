"""
Session Store - 短期记忆（STM）
存储单次任务拆解会话的上下文
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class SessionStore:
    """
    会话存储
    用于存储任务拆解过程中的临时状态
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化会话

        Args:
            session_id: 会话ID（如果不提供，自动生成）
        """
        self.session_id = session_id or self._generate_session_id()
        self.created_at = datetime.utcnow()
        self._data = {
            "goal": "",
            "context": "",
            "constraints": [],
            "answers": {},  # 用户回答的问题
            "iterations": [],  # 历史计划版本
            "current_step": "start",  # 当前步骤
            "metadata": {}
        }

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return f"session_{datetime.utcnow().timestamp()}"

    def set_goal(self, goal: str):
        """设置目标"""
        self._data["goal"] = goal

    def set_context(self, context: str):
        """设置背景"""
        self._data["context"] = context

    def add_constraint(self, constraint: str):
        """添加约束"""
        if constraint not in self._data["constraints"]:
            self._data["constraints"].append(constraint)

    def add_constraints(self, constraints: List[str]):
        """批量添加约束"""
        for c in constraints:
            self.add_constraint(c)

    def record_answer(self, question_id: str, answer: str):
        """
        记录用户回答

        Args:
            question_id: 问题ID
            answer: 用户回答
        """
        self._data["answers"][question_id] = answer

    def get_answer(self, question_id: str) -> Optional[str]:
        """获取用户回答"""
        return self._data["answers"].get(question_id)

    def get_all_answers(self) -> Dict[str, str]:
        """获取所有回答"""
        return self._data["answers"].copy()

    def save_plan_version(self, plan: Any, version: Optional[str] = None):
        """
        保存计划版本

        Args:
            plan: 计划对象（PlanSchema）
            version: 版本号（如果不提供，自动生成）
        """
        if version is None:
            version = f"v{len(self._data['iterations']) + 1}"

        # 将 plan 序列化
        if hasattr(plan, 'model_dump'):
            plan_data = plan.model_dump()
        elif hasattr(plan, 'dict'):
            plan_data = plan.dict()
        else:
            plan_data = plan

        self._data["iterations"].append({
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "plan": plan_data
        })

    def get_latest_plan(self) -> Optional[Dict[str, Any]]:
        """获取最新的计划"""
        if not self._data["iterations"]:
            return None
        return self._data["iterations"][-1]["plan"]

    def get_plan_version(self, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的计划"""
        for iteration in self._data["iterations"]:
            if iteration["version"] == version:
                return iteration["plan"]
        return None

    def get_all_versions(self) -> List[Dict[str, Any]]:
        """获取所有版本"""
        return self._data["iterations"].copy()

    def set_current_step(self, step: str):
        """设置当前步骤"""
        self._data["current_step"] = step

    def get_current_step(self) -> str:
        """获取当前步骤"""
        return self._data["current_step"]

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self._data["metadata"][key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        return self._data["metadata"].get(key)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取会话摘要

        Returns:
            会话摘要字典
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "current_step": self._data["current_step"],
            "goal": self._data["goal"],
            "constraints_count": len(self._data["constraints"]),
            "answers_count": len(self._data["answers"]),
            "iterations_count": len(self._data["iterations"])
        }

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "data": self._data
        }

    def from_dict(self, data: Dict[str, Any]):
        """从字典导入"""
        self.session_id = data["session_id"]
        self.created_at = datetime.fromisoformat(data["created_at"])
        self._data = data["data"]

    def clear(self):
        """清空会话数据"""
        self._data = {
            "goal": "",
            "context": "",
            "constraints": [],
            "answers": {},
            "iterations": [],
            "current_step": "start",
            "metadata": {}
        }

    def export_to_json(self) -> str:
        """导出为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def import_from_json(self, json_str: str):
        """从 JSON 字符串导入"""
        data = json.loads(json_str)
        self.from_dict(data)
