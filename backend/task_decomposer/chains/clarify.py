"""
澄清问题生成 Chain
当信息不足时，智能生成需要向用户确认的问题
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .base import BaseChain
from task_decomposer.schemas import ClarifyOutput
from task_decomposer.prompts import CLARIFY_SYSTEM_PROMPT, build_clarify_prompt


class ClarifyChain(BaseChain[ClarifyOutput]):
    """
    澄清问题生成链
    输入：用户目标 + 部分上下文
    输出：建议的澄清问题列表
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._llm:
            self._build_chain(
                CLARIFY_SYSTEM_PROMPT,
                "{input}"
            )

    def run(
        self,
        goal: str,
        context: str = "",
        previous_questions: List[str] = None,
        **kwargs
    ) -> ClarifyOutput:
        """
        生成澄清问题

        Args:
            goal: 用户目标
            context: 已有的上下文信息
            previous_questions: 已经问过的问题（避免重复）

        Returns:
            ClarifyOutput: 澄清问题列表
        """
        # 构建 Prompt
        prompt = build_clarify_prompt(
            goal=goal,
            context=context,
            previous_questions=previous_questions or []
        )

        on_event = kwargs.get("on_event")
        if on_event:
            try:
                on_event({"type": "clarify_prompt_ready", "ts": datetime.utcnow().isoformat()})
            except Exception:
                pass

        # 调用 LLM
        if self._chain:
            response = self._chain.run(input=prompt)
        elif self._llm:
            response = self._llm.invoke(prompt).content
        else:
            raise RuntimeError("LLM 未初始化，无法生成澄清问题")

        print(f"ClarifyChain Raw Response:\n{response[:500]}...")

        # 解析响应
        if on_event:
            try:
                on_event({"type": "clarify_raw_response", "ts": datetime.utcnow().isoformat(), "data": {"preview": response[:800]}})
            except Exception:
                pass

        try:
            data = self._parse_json_response(response)
        except Exception as e:
            if on_event:
                try:
                    on_event({"type": "clarify_parse_error", "ts": datetime.utcnow().isoformat(), "data": {"error": str(e)}})
                except Exception:
                    pass
            raise

        # 转换为 ClarifyOutput
        output = self._to_clarify_output(data)
        if on_event:
            try:
                on_event({"type": "clarify_output", "ts": datetime.utcnow().isoformat(), "data": output.model_dump() if hasattr(output, "model_dump") else {"questions": getattr(output, "questions", [])}})
            except Exception:
                pass
        return output

    def _to_clarify_output(self, data: Dict[str, Any]) -> ClarifyOutput:
        """
        将 LLM 输出转换为 ClarifyOutput

        Args:
            data: LLM 解析后的数据

        Returns:
            ClarifyOutput 实例
        """
        questions = data.get("questions", [])

        # 确保每个问题都有必需字段
        for i, q in enumerate(questions):
            if isinstance(q, dict):
                if "id" not in q:
                    q["id"] = f"Q{i+1}"
                if "critical" not in q:
                    q["critical"] = True
                if "reason" not in q:
                    q["reason"] = ""

        return ClarifyOutput(
            questions=questions,
            reasoning=data.get("reasoning", ""),
            priority=data.get("priority", [f"Q{i+1}" for i in range(len(questions))])
        )

    def suggest_next_questions(
        self,
        goal: str,
        answers_so_far: Dict[str, str],
        **kwargs
    ) -> ClarifyOutput:
        """
        基于已有的回答，建议下一批问题

        Args:
            goal: 用户目标
            answers_so_far: 用户已回答的问题字典

        Returns:
            下一批建议的问题
        """
        # 构建上下文，包含已有回答
        context_parts = []
        for q_id, answer in answers_so_far.items():
            context_parts.append(f"{q_id}: {answer}")

        context = "\n".join(context_parts) if context_parts else ""

        # 已问过的问题
        previous_questions = list(answers_so_far.keys())

        return self.run(
            goal=goal,
            context=context,
            previous_questions=previous_questions,
            **kwargs
        )
