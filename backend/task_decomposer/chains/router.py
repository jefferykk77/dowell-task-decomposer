"""
意图路由 Chain
根据用户输入判断应该使用哪个处理流程
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .base import BaseChain
from task_decomposer.schemas import RouterOutput
from task_decomposer.prompts import ROUTER_SYSTEM_PROMPT, build_router_prompt


class RouterChain(BaseChain[RouterOutput]):
    """
    意图路由链
    输入：用户输入 + 对话历史
    输出：路由决策
    """

    # 支持的路由类型
    INTENT_CLARIFY = "clarify"
    INTENT_DECOMPOSE = "decompose"
    INTENT_RAG_DECOMPOSE = "rag_decompose"
    INTENT_EMPATHIZE = "empathize"
    INTENT_UNKNOWN = "unknown"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._llm:
            self._build_chain(
                ROUTER_SYSTEM_PROMPT,
                "{input}"
            )

    def run(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None,
        **kwargs
    ) -> RouterOutput:
        """
        执行路由判断

        Args:
            user_input: 用户输入
            conversation_history: 对话历史

        Returns:
            RouterOutput: 路由决策
        """
        # 构建 Prompt
        prompt = build_router_prompt(
            user_input=user_input,
            conversation_history=conversation_history
        )

        on_event = kwargs.get("on_event")
        if on_event:
            try:
                on_event({"type": "router_prompt_ready", "ts": datetime.utcnow().isoformat()})
            except Exception:
                pass

        # 调用 LLM
        if self._chain:
            response = self._chain.run(input=prompt)
        elif self._llm:
            response = self._llm.invoke(prompt).content
        else:
            raise RuntimeError("LLM 未初始化，无法执行路由")

        print(f"RouterChain Raw Response:\n{response[:500]}...")

        # 解析响应
        if on_event:
            try:
                on_event({"type": "router_raw_response", "ts": datetime.utcnow().isoformat(), "data": {"preview": response[:800]}})
            except Exception:
                pass

        try:
            data = self._parse_json_response(response)
        except Exception as e:
            if on_event:
                try:
                    on_event({"type": "router_parse_error", "ts": datetime.utcnow().isoformat(), "data": {"error": str(e)}})
                except Exception:
                    pass
            raise

        # 转换为 RouterOutput
        output = self._to_router_output(data)
        if on_event:
            try:
                on_event({"type": "router_output", "ts": datetime.utcnow().isoformat(), "data": output.model_dump() if hasattr(output, "model_dump") else {"intent": output.intent}})
            except Exception:
                pass
        return output

    def _to_router_output(self, data: Dict[str, Any]) -> RouterOutput:
        """
        将 LLM 输出转换为 RouterOutput

        Args:
            data: LLM 解析后的数据

        Returns:
            RouterOutput 实例
        """
        intent = data.get("intent", self.INTENT_UNKNOWN)

        # 验证 intent 是否合法
        valid_intents = [
            self.INTENT_CLARIFY,
            self.INTENT_DECOMPOSE,
            self.INTENT_RAG_DECOMPOSE,
            self.INTENT_EMPATHIZE,
            self.INTENT_UNKNOWN
        ]

        if intent not in valid_intents:
            intent = self.INTENT_UNKNOWN

        return RouterOutput(
            intent=intent,
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", ""),
            suggested_action=data.get("suggested_action", "")
        )

    def should_clarify(self, user_input: str, **kwargs) -> bool:
        """
        快速判断是否需要澄清

        Args:
            user_input: 用户输入

        Returns:
            是否需要先澄清
        """
        result = self.run(user_input=user_input, **kwargs)
        return result.intent == self.INTENT_CLARIFY

    def should_use_rag(self, user_input: str, **kwargs) -> bool:
        """
        判断是否需要使用 RAG

        Args:
            user_input: 用户输入

        Returns:
            是否需要 RAG 辅助
        """
        result = self.run(user_input=user_input, **kwargs)
        return result.intent == self.INTENT_RAG_DECOMPOSE
