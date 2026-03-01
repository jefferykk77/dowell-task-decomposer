"""
统一的任务计划 Schema
这是整个任务拆解器的核心数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum


class PriorityLevel(str, Enum):
    """任务优先级"""
    P0 = "P0"  # 最高优先级，必须完成
    P1 = "P1"  # 高优先级
    P2 = "P2"  # 中等优先级
    P3 = "P3"  # 低优先级


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class ConstraintSchema(BaseModel):
    """约束条件"""
    type: str = Field(..., description="约束类型: time, budget, tech_stack, forbidden等")
    description: str = Field(..., description="约束描述")
    value: Optional[str] = Field(None, description="约束的具体值")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "time",
                "description": "项目必须在两周内完成",
                "value": "2 weeks"
            }
        }


class OpenQuestionSchema(BaseModel):
    """待向用户确认的问题"""
    id: str = Field(..., description="问题ID，如 Q1, Q2...")
    question: str = Field(..., description="问题内容")
    critical: bool = Field(default=True, description="是否为关键问题")
    reason: Optional[str] = Field(None, description="为什么需要这个问题")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "Q1",
                "question": "你的项目预算范围是多少？",
                "critical": True,
                "reason": "预算会影响技术栈和功能范围的选择"
            }
        }


class MilestoneSchema(BaseModel):
    """里程碑"""
    id: str = Field(..., description="里程碑ID，如 M1, M2...")
    title: str = Field(..., description="里程碑标题")
    description: Optional[str] = Field(None, description="里程碑描述")
    due: Optional[str] = Field(None, description="预计完成日期，格式 YYYY-MM-DD")
    definition_of_done: str = Field(..., description="完成标准/验收标准")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "M1",
                "title": "核心功能完成",
                "description": "完成所有核心功能的开发和测试",
                "due": "2025-02-15",
                "definition_of_done": "所有核心功能通过测试，无P0级别bug"
            }
        }


class TaskSchema(BaseModel):
    """
    任务节点
    支持层级结构（通过 depends_on 和 parent_task_id）
    """
    id: str = Field(..., description="任务ID，如 T1, T2...")
    title: str = Field(..., description="任务标题")
    description: str = Field(..., description="详细描述：做什么、为什么")
    inputs: List[str] = Field(default_factory=list, description="需要的输入资源")
    outputs: List[str] = Field(default_factory=list, description="预期的产出物")
    depends_on: List[str] = Field(default_factory=list, description="依赖的任务ID列表")
    parent_task_id: Optional[str] = Field(None, description="父任务ID，用于构建层级结构（如月度任务下包含周任务）")
    estimate_hours: Optional[float] = Field(None, description="预估工时（小时）")
    priority: PriorityLevel = Field(default=PriorityLevel.P2, description="优先级")
    risk: RiskLevel = Field(default=RiskLevel.MEDIUM, description="风险等级")
    definition_of_done: str = Field(..., description="验收标准")
    start_date: Optional[str] = Field(None, description="开始日期，格式 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期，格式 YYYY-MM-DD")
    assignee: Optional[str] = Field(None, description="负责人")
    tags: List[str] = Field(default_factory=list, description="标签")
    level: Optional[str] = Field(None, description="任务层级：month, week, day")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "T1",
                "title": "设计数据库schema",
                "description": "根据需求文档设计数据库表结构和关系",
                "inputs": ["需求文档", "业务流程图"],
                "outputs": ["数据库ER图", "DDL脚本"],
                "depends_on": [],
                "estimate_hours": 4.0,
                "priority": "P1",
                "risk": "低",
                "definition_of_done": "ER图通过评审，DDL脚本在测试环境执行成功",
                "start_date": "2025-01-15",
                "end_date": "2025-01-16",
                "assignee": "张三",
                "tags": ["backend", "database"]
            }
        }


class PlanMetadata(BaseModel):
    """计划元数据"""
    version: str = Field(default="1.0", description="计划版本")
    created_at: str = Field(..., description="创建时间，ISO格式")
    updated_at: str = Field(..., description="更新时间，ISO格式")
    model_used: Optional[str] = Field(None, description="使用的模型")
    rag_enabled: bool = Field(default=False, description="是否使用了RAG增强")


class PlanSchema(BaseModel):
    """
    完整的任务计划 Schema
    这是所有 Chain 的统一输出格式
    """
    # 核心信息
    goal: str = Field(..., description="用户要达成的目标")
    context: Optional[str] = Field(None, description="背景信息")

    # 约束与假设
    constraints: List[ConstraintSchema] = Field(
        default_factory=list,
        description="时间/预算/技术栈/禁用项等约束"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="做出的假设（信息不足时）"
    )
    open_questions: List[OpenQuestionSchema] = Field(
        default_factory=list,
        description="需要向用户确认的关键问题"
    )

    # 里程碑
    milestones: List[MilestoneSchema] = Field(
        default_factory=list,
        description="关键里程碑"
    )

    # 任务树
    tasks: List[TaskSchema] = Field(
        default_factory=list,
        description="任务列表（支持通过depends_on构建依赖关系）"
    )

    # 时间层级结构（新增）
    time_hierarchy: Optional[Dict[str, Any]] = Field(
        None,
        description="基于时间粒度的层级结构（year/quarter/month/week/day）"
    )

    # 元数据
    metadata: Optional[PlanMetadata] = Field(None, description="计划元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "goal": "开发一个电商小程序",
                "context": "需要在一个月内上线，支持微信支付",
                "constraints": [
                    {
                        "type": "time",
                        "description": "项目周期30天",
                        "value": "30 days"
                    },
                    {
                        "type": "budget",
                        "description": "预算有限，使用开源方案",
                        "value": "low"
                    }
                ],
                "assumptions": [
                    "使用微信小程序原生框架",
                    "后端使用Python Flask"
                ],
                "open_questions": [
                    {
                        "id": "Q1",
                        "question": "需要支持哪些支付方式？",
                        "critical": True,
                        "reason": "影响开发工作量"
                    }
                ],
                "milestones": [
                    {
                        "id": "M1",
                        "title": "原型设计完成",
                        "description": "完成所有页面的原型设计",
                        "due": "2025-01-20",
                        "definition_of_done": "原型通过评审"
                    }
                ],
                "tasks": [
                    {
                        "id": "T1",
                        "title": "设计数据库",
                        "description": "设计商品、订单、用户等表",
                        "inputs": ["需求文档"],
                        "outputs": ["数据库设计文档"],
                        "depends_on": [],
                        "estimate_hours": 8,
                        "priority": "P1",
                        "risk": "低",
                        "definition_of_done": "设计文档评审通过"
                    }
                ],
                "metadata": {
                    "version": "1.0",
                    "created_at": "2025-01-15T10:00:00Z",
                    "updated_at": "2025-01-15T10:00:00Z",
                    "model_used": "deepseek-chat",
                    "rag_enabled": True
                }
            }
        }

    def get_task_by_id(self, task_id: str) -> Optional[TaskSchema]:
        """根据ID获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_priority(self, priority: PriorityLevel) -> List[TaskSchema]:
        """根据优先级获取任务"""
        return [t for t in self.tasks if t.priority == priority]

    def get_critical_path(self) -> List[str]:
        """获取关键路径（依赖链最长的路径）"""
        # 简化实现：返回所有P0任务的ID
        return [t.id for t in self.tasks if t.priority == PriorityLevel.P0]

    def estimate_total_hours(self) -> float:
        """估算总工时"""
        return sum(t.estimate_hours or 0 for t in self.tasks)

    def validate_dependencies(self) -> List[str]:
        """验证依赖关系的完整性"""
        errors = []
        task_ids = {t.id for t in self.tasks}

        for task in self.tasks:
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    errors.append(f"任务 {task.id} 依赖的任务 {dep_id} 不存在")

        return errors
