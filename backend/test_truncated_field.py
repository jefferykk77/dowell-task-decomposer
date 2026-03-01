"""
测试字段名被截断的JSON修复
"""

import json
from task_decomposer.chains.base import BaseChain


# 创建一个简单的测试实现
class TestChain(BaseChain):
    def run(self, *args, **kwargs):
        return {}


def test_field_name_truncation():
    """测试字段名被截断的情况"""
    test_chain = TestChain()

    # 测试用例：评估结果中字段名被截断
    truncated_json = '''{
  "overall_score": 82,
  "issues": [
    {
      "severity": "medium",
      "category": "completeness",
      "description": "缺乏明确的测试和质量保证环节",
      "suggestion": "增加单元测试、集成测试和代码审查任务",
      "affected_tasks": ["T5", "T8", "T10"]
    },
    {
      "severity": "medium",
      "category": "executability",
      "description": "部分任务描述过于笼统，缺乏具体验收标准",
      "suggestion": "为每个学习任务添加具体的学习目标和产出物要求",
      "affected_tasks": ["T2", "T3", "T4", "T6", "T9"]
    },
    {
      "severity": "low",
      "dependenc'''

    print("Test: Field name truncated (evaluation result)")
    print(f"Input ends with: ...{truncated_json[-50:]}")

    try:
        # 使用完整的解析流程
        result = test_chain._parse_json_response(truncated_json)
        print(f"[OK] Fixed successfully")
        print(f"  overall_score: {result.get('overall_score')}")
        print(f"  issues count: {len(result.get('issues', []))}")
        print(f"  JSON valid: {json.dumps(result, indent=2)[:300]}...")
    except Exception as e:
        print(f"[FAIL] Fix failed: {e}")
        print(f"  Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_field_name_truncation()
