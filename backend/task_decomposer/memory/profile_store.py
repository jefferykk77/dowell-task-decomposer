"""
Profile Store - 长期记忆（LTM）
存储用户画像、偏好、历史经验
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path


class ProfileStore:
    """
    用户画像存储
    用于跨会话保存用户偏好和历史经验
    """

    def __init__(self, user_id: str, storage_path: Optional[str] = None):
        """
        初始化用户画像

        Args:
            user_id: 用户ID
            storage_path: 存储路径（如果不提供，使用默认路径）
        """
        self.user_id = user_id
        self.storage_path = storage_path or self._get_default_storage_path()
        self._profile = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "preferences": {},  # 用户偏好
            "demographics": {},  # 用户角色等信息
            "history": [],  # 历史任务记录
            "templates": [],  # 常用任务模板
            "stats": {}  # 统计信息
        }

        # 尝试加载已有画像
        self._load()

    def _get_default_storage_path(self) -> str:
        """获取默认存储路径"""
        base_dir = Path(__file__).parent.parent.parent
        profiles_dir = base_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        return str(profiles_dir / f"{self.user_id}.json")

    def _load(self):
        """加载已有的画像数据"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self._profile = json.load(f)
                print(f"用户画像加载成功: {self.user_id}")
        except Exception as e:
            print(f"用户画像加载失败: {e}")

    def _save(self):
        """保存画像数据"""
        try:
            self._profile["updated_at"] = datetime.utcnow().isoformat()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"用户画像保存失败: {e}")

    # === 偏好设置 ===

    def set_preference(self, key: str, value: Any):
        """设置偏好"""
        self._profile["preferences"][key] = self._save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取偏好"""
        return self._profile["preferences"].get(key, default)

    def get_all_preferences(self) -> Dict[str, Any]:
        """获取所有偏好"""
        return self._profile["preferences"].copy()

    # === 用户信息 ===

    def set_role(self, role: str):
        """设置用户角色（如：PM, 开发, 运营）"""
        self._profile["demographics"]["role"] = role
        self._save()

    def get_role(self) -> Optional[str]:
        """获取用户角色"""
        return self._profile["demographics"].get("role")

    def set_skill_level(self, level: str):
        """设置技能水平（如：初级, 中级, 高级）"""
        self._profile["demographics"]["skill_level"] = level
        self._save()

    def get_skill_level(self) -> Optional[str]:
        """获取技能水平"""
        return self._profile["demographics"].get("skill_level")

    # === 历史记录 ===

    def add_history(
        self,
        goal: str,
        plan: Any,
        tags: List[str] = None
    ):
        """
        添加历史记录

        Args:
            goal: 任务目标
            plan: 任务计划
            tags: 标签
        """
        # 序列化 plan
        if hasattr(plan, 'model_dump'):
            plan_data = plan.model_dump()
        elif hasattr(plan, 'dict'):
            plan_data = plan.dict()
        else:
            plan_data = plan

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "goal": goal,
            "plan_summary": {
                "task_count": len(plan_data.get("tasks", [])),
                "milestone_count": len(plan_data.get("milestones", [])),
                "total_hours": sum(
                    t.get("estimate_hours", 0)
                    for t in plan_data.get("tasks", [])
                )
            },
            "tags": tags or []
        }

        self._profile["history"].append(history_entry)

        # 限制历史记录数量（最多保留 100 条）
        if len(self._profile["history"]) > 100:
            self._profile["history"] = self._profile["history"][-100:]

        self._save()

    def get_history(
        self,
        limit: int = 10,
        tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Args:
            limit: 返回数量
            tags: 标签过滤

        Returns:
            历史记录列表
        """
        history = self._profile["history"]

        # 标签过滤
        if tags:
            history = [
                h for h in history
                if any(tag in h.get("tags", []) for tag in tags)
            ]

        # 返回最近的 N 条
        return history[-limit:]

    def get_similar_tasks(self, goal: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        获取相似的历史任务（简化实现）

        Args:
            goal: 当前目标
            top_k: 返回数量

        Returns:
            相似任务列表
        """
        # 简化实现：返回包含相似关键词的任务
        # 实际应该使用向量相似度
        keywords = goal.lower().split()

        similar_tasks = []
        for history in self._profile["history"]:
            history_goal = history["goal"].lower()
            score = sum(1 for kw in keywords if kw in history_goal)

            if score > 0:
                similar_tasks.append({
                    "task": history,
                    "score": score
                })

        # 按相关性排序
        similar_tasks.sort(key=lambda x: x["score"], reverse=True)

        return [t["task"] for t in similar_tasks[:top_k]]

    # === 模板管理 ===

    def save_template(self, name: str, template: Dict[str, Any]):
        """
        保存任务模板

        Args:
            name: 模板名称
            template: 模板内容
        """
        template_entry = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "template": template
        }

        # 检查是否已存在
        for i, t in enumerate(self._profile["templates"]):
            if t["name"] == name:
                self._profile["templates"][i] = template_entry
                self._save()
                return

        # 添加新模板
        self._profile["templates"].append(template_entry)
        self._save()

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        for t in self._profile["templates"]:
            if t["name"] == name:
                return t["template"]
        return None

    def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板"""
        return [t["template"] for t in self._profile["templates"]]

    # === 统计信息 ===

    def update_stats(self, key: str, value: Any):
        """更新统计信息"""
        self._profile["stats"][key] = value
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._profile["stats"].copy()

    def get_summary(self) -> Dict[str, Any]:
        """获取画像摘要"""
        return {
            "user_id": self.user_id,
            "role": self.get_role(),
            "skill_level": self.get_skill_level(),
            "total_tasks": len(self._profile["history"]),
            "total_templates": len(self._profile["templates"]),
            "created_at": self._profile["created_at"],
            "updated_at": self._profile["updated_at"]
        }

    def export_to_json(self) -> str:
        """导出为 JSON"""
        return json.dumps(self._profile, ensure_ascii=False, indent=2)

    def import_from_json(self, json_str: str):
        """从 JSON 导入"""
        self._profile = json.loads(json_str)
        self._save()
