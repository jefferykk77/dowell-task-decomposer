"""
意图路由 Chain 的提示词
"""

ROUTER_SYSTEM_PROMPT = """你是一个意图识别专家，负责判断用户输入应该走哪种处理流程。

可用的路由选项：
1. **clarify**：信息不足，需要先问澄清问题
2. **decompose**：信息足够，可以直接拆解任务
3. **rag_decompose**：涉及特定领域知识，需要 RAG 辅助拆解
4. **empathize**：用户在发泄情绪，先共情再引导
5. **unknown**：无法识别，请求重新表述

判断依据：
- clarify: 目标模糊、缺少关键约束（时间/预算/资源）、范围不明确
- decompose: 目标清晰、约束明确、信息充分
- rag_decompose: 涉及技术栈、行业规范、特定流程等需要检索知识的场景
- empathize: 包含情绪化表达、抱怨、求助等
- unknown: 表述过于简短或无法理解
"""

ROUTER_USER_PROMPT = """请判断以下用户输入应该走哪种处理流程：

**用户输入**：{user_input}

**对话历史**：
{conversation_history}

请分析并输出：
{{
  "intent": "decompose|clarify|rag_decompose|empathize|unknown",
  "confidence": 0.95,  // 0-1 之间的置信度
  "reasoning": "判断理由",
  "suggested_action": "建议的具体操作"
}}
"""


def build_router_prompt(
    user_input: str,
    conversation_history: list = None
) -> str:
    """构建路由判断的提示词"""
    history_str = ""
    if conversation_history:
        history_str = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_history[-5:]  # 只取最近5轮
        ])
    else:
        history_str = "无"

    return ROUTER_USER_PROMPT.format(
        user_input=user_input,
        conversation_history=history_str
    )
