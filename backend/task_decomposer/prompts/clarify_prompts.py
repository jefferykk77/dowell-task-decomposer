"""
澄清问题生成 Chain 的提示词
"""

CLARIFY_SYSTEM_PROMPT = """你是一位经验丰富的需求分析师，擅长识别模糊需求中的关键信息缺口。

你的能力：
1. 快速理解用户目标的本质
2. 识别缺失的关键信息
3. 提出简洁、有针对性的问题
4. 区分"必须知道"和"最好知道"的信息

提问原则：
- 每次提问 3-5 个问题
- 优先问对任务拆解影响最大的问题
- 问题要具体，不要泛泛而谈
- 避免问可以用"是/否"回答的问题，尽可能引导用户描述
"""

CLARIFY_USER_PROMPT = """用户提出了以下目标，请分析并提出需要澄清的问题：

**用户目标**：{goal}

**已有上下文**：{context}

**已经问过的问题**：{previous_questions}

请分析：
1. 哪些关键信息缺失？
2. 这些缺失如何影响任务拆解的准确性？
3. 应该优先澄清哪些问题？

请按以下 JSON 格式输出：
{{
  "questions": [
    {{
      "id": "Q1",
      "question": "具体问题内容",
      "critical": true,
      "reason": "为什么这个问题很关键",
      "options": ["选项A", "选项B"],  // 可选，提供预设选项
      "category": "time|budget|scope|tech|resources"  // 问题类别
    }}
  ],
  "reasoning": "总体分析：为什么需要这些问题",
  "priority": ["Q1", "Q3", "Q2"]  // 问题优先级排序
}}
"""


def build_clarify_prompt(
    goal: str,
    context: str = "",
    previous_questions: list = None
) -> str:
    """构建澄清问题生成的提示词"""
    prev_q_str = "\n".join(previous_questions) if previous_questions else "无"

    return CLARIFY_USER_PROMPT.format(
        goal=goal,
        context=context or "无",
        previous_questions=prev_q_str
    )
