"""
任务拆解 Chain
核心功能：将用户目标转化为结构化任务计划
支持根据时间范围自动判断粒度并按层级拆解到天级别
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime, date

from .base import BaseChain
from task_decomposer.schemas import PlanSchema, DecomposeInput
from task_decomposer.prompts import DECOMPOSE_SYSTEM_PROMPT, build_decompose_prompt
from task_decomposer.utils import decompose_task_by_time, TimeGranularity


class DecomposeChain(BaseChain[PlanSchema]):
    """
    任务拆解链
    输入：用户目标 + 上下文
    输出：结构化任务计划
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._llm:
            self._build_chain(
                DECOMPOSE_SYSTEM_PROMPT,
                "{input}"
            )

    def run(
        self,
        goal: str,
        context: str = "",
        constraints: List[str] = None,
        rag_query: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        work_hours_per_day: float = 8.0,
        work_days_per_week: List[int] = None,
        **kwargs
    ) -> PlanSchema:
        """
        执行任务拆解

        Args:
            goal: 用户目标
            context: 背景信息
            constraints: 约束条件列表
            rag_query: RAG 检索查询（如果不提供，使用 goal）
            start_date: 开始日期（可选，用于时间粒度判断）
            end_date: 结束日期（可选，用于时间粒度判断）
            work_hours_per_day: 每天工作小时数
            work_days_per_week: 每周工作日列表（0=周一, 6=周日）

        Returns:
            PlanSchema: 结构化任务计划
        """
        # 如果提供了时间范围，先进行时间粒度判断和拆解
        time_hierarchy = None
        if start_date and end_date:
            try:
                time_hierarchy = decompose_task_by_time(
                    goal=goal,
                    start_date=start_date,
                    end_date=end_date,
                    work_hours_per_day=work_hours_per_day,
                    work_days_per_week=work_days_per_week
                )
                print(f"时间粒度: {time_hierarchy['granularity']}")
                print(f"总天数: {time_hierarchy['total_days']}")
            except Exception as e:
                print(f"时间粒度判断失败: {e}")

        # 构建 Prompt，添加时间层级信息
        base_prompt = build_decompose_prompt(
            goal=goal,
            context=context,
            constraints=constraints
        )

        # 如果有时间层级信息，添加到提示词中
        if time_hierarchy:
            base_prompt += f"""

**时间规划信息**：
- 时间范围: {time_hierarchy['start_date']} ~ {time_hierarchy['end_date']}
- 时间粒度: {time_hierarchy['granularity']}
- 总天数: {time_hierarchy['total_days']}天

请根据这个时间范围，将任务合理分配到对应的时间层级中（年度/季度/月度/周度/日度）。
确保每个任务都有明确的开始和结束日期（start_date 和 end_date 字段）。
"""

        # RAG 增强
        query = rag_query or goal
        enhanced_prompt = self._enhance_prompt_with_rag(
            base_prompt,
            query
        )

        on_event = kwargs.get("on_event")
        if on_event:
            try:
                on_event({
                    "type": "decompose_prompt_ready",
                    "ts": datetime.utcnow().isoformat(),
                    "data": {
                        "rag_applied": enhanced_prompt != base_prompt,
                        "constraints": len(constraints or [])
                    }
                })
            except Exception:
                pass

        # 调用 LLM
        if self._chain:
            response = self._chain.run(input=enhanced_prompt)
        elif self._llm:
            # 回退到直接调用
            response = self._llm.invoke(enhanced_prompt).content
        else:
            raise RuntimeError("LLM 未初始化，无法执行任务拆解")

        print(f"DecomposeChain Raw Response:\n{response[:500]}...")

        # 解析响应
        if on_event:
            try:
                on_event({"type": "decompose_raw_response", "ts": datetime.utcnow().isoformat(), "data": {"preview": response[:800]}})
            except Exception:
                pass

        try:
            data = self._parse_json_response(response)
        except Exception as e:
            if on_event:
                try:
                    on_event({"type": "decompose_parse_error", "ts": datetime.utcnow().isoformat(), "data": {"error": str(e)}})
                except Exception:
                    pass
            raise

        if on_event:
            try:
                tasks_count = len(data.get("tasks", []) or [])
                milestones_count = len(data.get("milestones", []) or [])
                on_event({
                    "type": "decompose_parsed",
                    "ts": datetime.utcnow().isoformat(),
                    "data": {"tasks": tasks_count, "milestones": milestones_count}
                })
            except Exception:
                pass

        # 转换为 PlanSchema，并传入时间层级信息
        plan = self._to_plan_schema(data, goal, time_hierarchy)
        if on_event:
            try:
                on_event({
                    "type": "decompose_output",
                    "ts": datetime.utcnow().isoformat(),
                    "data": {"tasks": len(getattr(plan, "tasks", []) or []), "milestones": len(getattr(plan, "milestones", []) or [])}
                })
            except Exception:
                pass
        return plan

    def _to_plan_schema(
        self,
        data: Dict[str, Any],
        original_goal: str,
        time_hierarchy: Optional[Dict[str, Any]] = None
    ) -> PlanSchema:
        """
        将 LLM 输出转换为 PlanSchema

        Args:
            data: LLM 解析后的数据
            original_goal: 原始目标

        Returns:
            PlanSchema 实例
        """
        from task_decomposer.schemas.plan import (
            PlanMetadata,
            MilestoneSchema,
            TaskSchema,
            ConstraintSchema,
            OpenQuestionSchema
        )

        # 处理约束
        constraints = []
        for c in data.get("constraints", []):
            if isinstance(c, dict):
                constraints.append(ConstraintSchema(**c))
            elif isinstance(c, str):
                constraints.append(ConstraintSchema(
                    type="general",
                    description=c
                ))

        # 处理开放问题
        open_questions = []
        for q in data.get("open_questions", []):
            if isinstance(q, dict):
                open_questions.append(OpenQuestionSchema(**q))

        # 处理里程碑
        milestones = []
        for m in data.get("milestones", []):
            if isinstance(m, dict):
                milestones.append(MilestoneSchema(**m))

        # 处理任务
        tasks = []
        for t in data.get("tasks", []):
            if isinstance(t, dict):
                # 确保有必需字段
                if "description" not in t:
                    t["description"] = t.get("title", "")
                if "definition_of_done" not in t:
                    t["definition_of_done"] = "完成该任务"
                tasks.append(TaskSchema(**t))

        # 创建元数据
        metadata = PlanMetadata(
            version="1.0",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            model_used=getattr(self._llm, "model_name", "unknown") if self._llm else None,
            rag_enabled=self._enable_rag
        )

        # 构建完整的 Plan，包含时间层级结构
        return PlanSchema(
            goal=data.get("goal", original_goal),
            context=data.get("context"),
            constraints=constraints,
            assumptions=data.get("assumptions", []),
            open_questions=open_questions,
            milestones=milestones,
            tasks=tasks,
            time_hierarchy=time_hierarchy,  # 添加时间层级信息
            metadata=metadata
        )

    def batch_run(
        self,
        inputs: List[DecomposeInput]
    ) -> List[PlanSchema]:
        """
        批量执行任务拆解

        Args:
            inputs: 拆解请求列表

        Returns:
            任务计划列表
        """
        results = []
        for inp in inputs:
            try:
                plan = self.run(
                    goal=inp.goal,
                    context=inp.context or "",
                    constraints=inp.constraints
                )
                results.append(plan)
            except Exception as e:
                print(f"批量拆解失败: {inp.goal}, 错误: {e}")
                # 可以选择返回空计划或抛出异常
                raise

        return results
