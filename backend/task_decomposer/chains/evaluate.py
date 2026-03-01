"""
计划评估与重写 Chain
对生成的任务计划进行质量评估和改进
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .base import BaseChain
from task_decomposer.schemas import PlanSchema, EvaluateOutput, EvaluationIssue
from task_decomposer.prompts import EVALUATE_SYSTEM_PROMPT, build_evaluate_prompt


class EvaluateChain(BaseChain[EvaluateOutput]):
    """
    计划评估链
    输入：任务计划
    输出：评估结果 + 问题列表
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._llm:
            self._build_chain(
                EVALUATE_SYSTEM_PROMPT,
                "{input}"
            )

    def run(
        self,
        plan: PlanSchema,
        custom_criteria: List[str] = None,
        **kwargs
    ) -> EvaluateOutput:
        """
        评估任务计划

        Args:
            plan: 待评估的计划
            custom_criteria: 自定义评估标准

        Returns:
            EvaluateOutput: 评估结果
        """
        # 生成任务摘要
        task_summary = self._generate_task_summary(plan)

        # 构建 Prompt
        prompt = build_evaluate_prompt(plan, task_summary)

        on_event = kwargs.get("on_event")
        if on_event:
            try:
                on_event({"type": "evaluate_prompt_ready", "ts": datetime.utcnow().isoformat(), "data": {"tasks": len(plan.tasks)}})
            except Exception:
                pass

        # 调用 LLM
        if self._chain:
            response = self._chain.run(input=prompt)
        elif self._llm:
            response = self._llm.invoke(prompt).content
        else:
            raise RuntimeError("LLM 未初始化，无法评估计划")

        print(f"EvaluateChain Raw Response:\n{response[:500]}...")

        # 解析响应
        if on_event:
            try:
                on_event({"type": "evaluate_raw_response", "ts": datetime.utcnow().isoformat(), "data": {"preview": response[:800]}})
            except Exception:
                pass

        try:
            data = self._parse_json_response(response)
        except Exception as e:
            if on_event:
                try:
                    on_event({"type": "evaluate_parse_error", "ts": datetime.utcnow().isoformat(), "data": {"error": str(e)}})
                except Exception:
                    pass
            raise

        # 转换为 EvaluateOutput
        output = self._to_evaluate_output(data)
        if on_event:
            try:
                on_event({"type": "evaluate_output", "ts": datetime.utcnow().isoformat(), "data": output.model_dump() if hasattr(output, "model_dump") else {"overall_score": getattr(output, "overall_score", None)}})
            except Exception:
                pass
        return output

    def _generate_task_summary(self, plan: PlanSchema) -> str:
        """
        生成任务摘要

        Args:
            plan: 任务计划

        Returns:
            任务摘要字符串
        """
        summary_lines = []

        for i, task in enumerate(plan.tasks[:10], 1):  # 只显示前10个
            deps = ", ".join(task.depends_on) if task.depends_on else "无"
            summary_lines.append(
                f"{i}. [{task.id}] {task.title}\n"
                f"   优先级: {task.priority} | 风险: {task.risk} | "
                f"依赖: {deps}\n"
                f"   描述: {task.description[:100]}..."
            )

        if len(plan.tasks) > 10:
            summary_lines.append(f"\n... 还有 {len(plan.tasks) - 10} 个任务")

        return "\n".join(summary_lines)

    def _to_evaluate_output(self, data: Dict[str, Any]) -> EvaluateOutput:
        """
        将 LLM 输出转换为 EvaluateOutput

        Args:
            data: LLM 解析后的数据

        Returns:
            EvaluateOutput 实例
        """
        # 处理问题列表
        issues = []
        for issue_data in data.get("issues", []):
            if isinstance(issue_data, dict):
                # 设置默认值
                if "affected_tasks" not in issue_data:
                    issue_data["affected_tasks"] = []
                issues.append(EvaluationIssue(**issue_data))

        return EvaluateOutput(
            overall_score=data.get("overall_score", 0),
            issues=issues,
            passed=data.get("passed", False),
            rewrite_needed=data.get("rewrite_needed", False),
            rewrite_reason=data.get("rewrite_reason")
        )

    def evaluate_and_rewrite(
        self,
        plan: PlanSchema,
        decompose_chain: 'DecomposeChain',
        max_iterations: int = 3,
        min_score: float = 80.0,
        **kwargs
    ) -> tuple[PlanSchema, EvaluateOutput]:
        """
        评估并迭代改进计划

        Args:
            plan: 待评估和改进的计划
            decompose_chain: 用于重写的 DecomposeChain
            max_iterations: 最大迭代次数
            min_score: 最低合格分数

        Returns:
            (改进后的计划, 最终评估结果)
        """
        current_plan = plan
        current_score = 0

        for iteration in range(1, max_iterations + 1):
            print(f"\n评估迭代 {iteration}/{max_iterations}")

            # 评估当前计划
            eval_result = self.run(plan=current_plan)
            current_score = eval_result.overall_score

            print(f"评分: {current_score}/100")

            # 如果达到标准，退出
            if current_score >= min_score and not eval_result.rewrite_needed:
                print("计划达到质量标准")
                break

            # 如果是最后一次迭代，不再重写
            if iteration >= max_iterations:
                print("达到最大迭代次数")
                break

            # 收集反馈
            feedback = [
                f"{issue.severity}: {issue.description}\n建议: {issue.suggestion}"
                for issue in eval_result.issues
            ]

            print(f"发现 {len(feedback)} 个问题，开始重写...")

            # 使用反馈重写计划
            # 这里简化处理：实际应该调用专门的 rewrite_chain
            # 暂时返回原计划
            current_plan = plan

        return current_plan, eval_result
