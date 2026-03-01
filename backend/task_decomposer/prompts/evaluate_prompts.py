"""
计划评估 Chain 的提示词
"""

EVALUATE_SYSTEM_PROMPT = """你是一位质量保证专家，擅长评估项目计划的完整性和可执行性。

评估维度：
1. **完整性**：是否覆盖从需求到交付的所有关键环节？
2. **可执行性**：每个任务是否有明确的输入、输出和验收标准？
3. **依赖合理性**：任务依赖关系是否正确？是否有循环依赖？
4. **约束一致性**：是否违反时间/预算/技术限制？
5. **风险评估**：风险识别是否充分？高风险任务是否有预案？

评估标准：
- 总分 0-100 分
- < 60 分：不合格，需要大幅重写
- 60-80 分：基本合格，有改进建议
- > 80 分：优秀，可以执行
"""

EVALUATE_USER_PROMPT = """请评估以下任务计划的质量：

**计划目标**：{plan_goal}

**任务数量**：{task_count} 个任务

**里程碑数量**：{milestone_count} 个

**任务列表概要**：
{task_summary}

**约束条件**：
{constraints}

请从以下维度进行评估：
1. 完整性：是否漏掉关键步骤？
2. 可执行性：任务描述是否具体？
3. 依赖关系：是否有逻辑错误？
4. 约束一致性：是否符合限制？
5. 风险评估：高风险任务是否识别？

请按以下 JSON 格式输出：
{{
  "overall_score": 85,  // 0-100
  "issues": [
    {{
      "severity": "high",  // critical, high, medium, low
      "category": "completeness",  // 问题类别
      "description": "具体问题描述",
      "suggestion": "改进建议",
      "affected_tasks": ["T1", "T2"]
    }}
  ],
  "passed": true,
  "rewrite_needed": false,
  "rewrite_reason": null
}}
"""


def build_evaluate_prompt(plan, task_summary: str = "") -> str:
    """构建计划评估的提示词"""
    constraint_str = "\n".join([f"- {c.type}: {c.description}" for c in plan.constraints])

    return EVALUATE_USER_PROMPT.format(
        plan_goal=plan.goal,
        task_count=len(plan.tasks),
        milestone_count=len(plan.milestones),
        task_summary=task_summary,
        constraints=constraint_str or "无"
    )
