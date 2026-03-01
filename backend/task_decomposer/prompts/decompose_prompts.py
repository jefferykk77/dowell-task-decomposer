"""
任务拆解 Chain 的提示词
"""

DECOMPOSE_SYSTEM_PROMPT = """你是一位资深的项目经理和任务拆解专家，擅长将模糊的目标转化为可执行的结构化计划。

你的核心能力：
1. 理解用户的真实意图，即使描述模糊
2. 识别任务的关键依赖关系和风险点
3. 生成具体、可落地的行动步骤
4. 预估合理的时间和资源需求

输出要求：
- 必须严格输出符合 Schema 的纯 JSON 格式
- 不要包含任何 Markdown 标记（如 ```json）
- 确保所有属性名都使用双引号
- 任务描述要具体、可执行，避免空泛的描述
- 优先级要合理分配，不要所有任务都是 P0
- 每个任务都要有明确的验收标准
"""

DECOMPOSE_USER_PROMPT = """请将以下目标拆解为结构化的任务计划：

**用户目标**：{goal}

**背景信息**：{context}

**约束条件**：{constraints}

**输出要求**：
1. 生成 3-5 个里程碑（milestones）
2. 拆解为 15-40 个具体任务（tasks），按照 **月度 -> 周度 -> 日度** 的层级结构组织
3. 如果信息不足，在 open_questions 中列出需要澄清的问题
4. 在 assumptions 中列出你做出的合理假设
5. 所有任务都要包含：描述、输入、输出、依赖关系、预估工时、优先级、风险、验收标准

**任务层级结构要求**：
- **月度任务 (level: "month")**：对应里程碑，时间跨度约 2-4 周
  - title 格式："{{年月}}：{{具体目标描述}}"（例如："1月：需求分析与原型设计"）
  - description：详细描述该月要完成的核心内容（例如："完成用户需求调研，产出产品原型设计稿和PRD文档"）
  - 示例：T1 = "1月：需求分析与原型设计"
- **周度任务 (level: "week")**：月度任务的子任务，时间跨度约 1 周
  - title 格式："{{周描述}}：{{具体任务}}"（例如："第1周：用户调研"）
  - description：详细描述本周要完成的具体内容
  - 示例：T1.1 = "第1周：用户调研"，parent_task_id = "T1"
- **日度任务 (level: "day")**：周度任务的子任务，可以在 1-2 天内完成
  - title：具体可执行的任务描述
  - description：任务的详细步骤和要点
  - 示例：T1.1.1 = "设计用户调研问卷"，parent_task_id = "T1.1"

**ID 命名规则**：
- 月度任务：T1, T2, T3...
- 周度任务：T1.1, T1.2, T2.1, T2.2...
- 日度任务：T1.1.1, T1.1.2, T1.2.1...

请严格按照以下 JSON Schema 输出：
{{
  "goal": "用户目标",
  "context": "背景",
  "constraints": [
    {{"type": "time", "description": "描述", "value": "值"}}
  ],
  "assumptions": ["假设1", "假设2"],
  "open_questions": [
    {{
      "id": "Q1",
      "question": "问题",
      "critical": true,
      "reason": "原因"
    }}
  ],
  "milestones": [
    {{
      "id": "M1",
      "title": "标题",
      "description": "描述",
      "due": "YYYY-MM-DD",
      "definition_of_done": "验收标准"
    }}
  ],
  "tasks": [
    {{
      "id": "T1",
      "title": "月度任务标题",
      "description": "详细描述",
      "inputs": ["输入1"],
      "outputs": ["输出1"],
      "depends_on": [],
      "parent_task_id": null,
      "level": "month",
      "estimate_hours": 40.0,
      "priority": "P1",
      "risk": "中",
      "definition_of_done": "验收标准",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "tags": ["phase1"]
    }},
    {{
      "id": "T1.1",
      "title": "周度任务标题",
      "description": "详细描述",
      "inputs": ["输入1"],
      "outputs": ["输出1"],
      "depends_on": [],
      "parent_task_id": "T1",
      "level": "week",
      "estimate_hours": 10.0,
      "priority": "P1",
      "risk": "低",
      "definition_of_done": "验收标准",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "tags": ["week1"]
    }},
    {{
      "id": "T1.1.1",
      "title": "日度任务标题",
      "description": "详细描述",
      "inputs": ["输入1"],
      "outputs": ["输出1"],
      "depends_on": [],
      "parent_task_id": "T1.1",
      "level": "day",
      "estimate_hours": 4.0,
      "priority": "P2",
      "risk": "低",
      "definition_of_done": "验收标准",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "tags": ["design"]
    }}
  ]
}}
"""


def build_decompose_prompt(
    goal: str,
    context: str = "",
    constraints: list = None,
    rag_context: str = ""
) -> str:
    """
    构建任务拆解的完整提示词

    Args:
        goal: 用户目标
        context: 背景信息
        constraints: 约束条件列表
        rag_context: RAG 检索到的相关知识

    Returns:
        完整的提示词
    """
    constraint_str = "\n".join([f"- {c}" for c in (constraints or [])])

    prompt = DECOMPOSE_USER_PROMPT.format(
        goal=goal,
        context=context or "无",
        constraints=constraint_str or "无"
    )

    # 如果有 RAG 上下文，追加到提示词
    if rag_context:
        prompt += f"""

**参考知识**：
{rag_context}

请参考以上最佳实践来制定计划。
"""

    return prompt
