"""
请求/响应 Schema
定义各个 Chain 的输入输出格式
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

from .plan import PlanSchema


class DecomposeInput(BaseModel):
    """任务拆解请求"""
    goal: str = Field(..., description="用户目标")
    context: Optional[str] = Field(None, description="背景信息")
    constraints: List[str] = Field(
        default_factory=list,
        description="用户提供的约束条件"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="用户偏好设置"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="对话历史（用于多轮交互）"
    )

    # 原有字段（兼容旧接口）
    title: Optional[str] = Field(None, description="任务标题（兼容旧版）")
    year: Optional[int] = Field(None, description="年份")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")

    class Config:
        json_schema_extra = {
            "example": {
                "goal": "开发一个任务管理小程序",
                "context": "用于个人和团队的任务追踪",
                "constraints": [
                    "预算有限，使用开源方案",
                    "需要在一周内上线MVP"
                ],
                "preferences": {
                    "output_format": "detailed",
                    "include_estimates": True
                }
            }
        }


class ClarifyInput(BaseModel):
    """澄清问题生成请求"""
    goal: str = Field(..., description="用户目标")
    partial_context: Optional[str] = Field(None, description="已有的上下文信息")
    previous_questions: Optional[List[str]] = Field(
        default_factory=list,
        description="已经问过的问题"
    )


class ClarifyOutput(BaseModel):
    """澄清问题输出"""
    questions: List[Dict[str, Any]] = Field(
        ...,
        description="建议的澄清问题列表"
    )
    reasoning: str = Field(..., description="为什么需要这些问题")
    priority: List[str] = Field(
        default_factory=list,
        description="问题优先级排序（问题ID列表）"
    )


class EvaluateInput(BaseModel):
    """计划评估请求"""
    plan: PlanSchema = Field(..., description="待评估的计划")
    evaluation_criteria: Optional[List[str]] = Field(
        default_factory=list,
        description="评估标准列表"
    )


class EvaluationIssue(BaseModel):
    """评估发现的问题"""
    severity: str = Field(..., description="严重程度: critical, high, medium, low")
    category: str = Field(..., description="问题类别: completeness, feasibility, consistency等")
    description: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="改进建议")
    affected_tasks: List[str] = Field(
        default_factory=list,
        description="受影响的任务ID"
    )


class EvaluateOutput(BaseModel):
    """计划评估输出"""
    overall_score: float = Field(..., description="总体评分 0-100")
    issues: List[EvaluationIssue] = Field(..., description="发现的问题列表")
    passed: bool = Field(..., description="是否通过评估")
    rewrite_needed: bool = Field(default=False, description="是否需要重写")
    rewrite_reason: Optional[str] = Field(None, description="需要重写的原因")


class RouterInput(BaseModel):
    """路由判断请求"""
    user_input: str = Field(..., description="用户输入")
    conversation_context: Optional[List[Dict[str, str]]] = Field(
        None,
        description="对话上下文"
    )


class RouterOutput(BaseModel):
    """路由输出"""
    intent: str = Field(
        ...,
        description="识别的意图: clarify, decompose, rag_decompose, empathize, unknown"
    )
    confidence: float = Field(..., description="置信度 0-1")
    reasoning: str = Field(..., description="判断理由")
    suggested_action: str = Field(..., description="建议的操作")


class RewriteInput(BaseModel):
    """计划重写请求"""
    original_plan: PlanSchema = Field(..., description="原始计划")
    feedback: List[str] = Field(..., description="反馈/问题列表")
    max_iterations: int = Field(default=3, description="最大重试次数")


class ChainOutput(BaseModel):
    """通用 Chain 输出包装"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
