"""
测试JSON修复功能
"""

import json
from task_decomposer.chains.base import BaseChain


# 创建一个简单的测试实现
class TestChain(BaseChain):
    def run(self, *args, **kwargs):
        return {}


def test_truncated_json():
    """测试截断的JSON修复"""
    test_chain = TestChain()

    # 测试用例1：截断的open_questions数组
    truncated = '''{
  "goal": "Test Goal",
  "context": "Test context",
  "constraints": [
    {"type": "time", "description": "deadline", "value": "2026-04-10"}
  ],
  "open_questions":'''

    print("Test 1: Truncated JSON at field name")
    print(f"Input: {truncated[:100]}...")

    try:
        fixed = test_chain._fix_truncated_json(truncated)
        result = json.loads(fixed)
        print(f"[OK] Fixed successfully")
        print(f"  open_questions field: {result.get('open_questions', [])}")
        print(f"  Full JSON: {json.dumps(result, indent=2)[:200]}...")
    except Exception as e:
        print(f"[FAIL] Fix failed: {e}")

    # 测试用例2：未闭合的括号
    truncated2 = '''{
  "goal": "test",
  "tasks": [
    {"id": "T1", "title": "task1"}
'''

    print("\nTest 2: Unclosed braces")
    print(f"Input: {truncated2}")

    try:
        fixed2 = test_chain._fix_truncated_json(truncated2)
        result2 = json.loads(fixed2)
        print(f"[OK] Fixed successfully")
        print(f"  tasks field: {result2.get('tasks', [])}")
    except Exception as e:
        print(f"[FAIL] Fix failed: {e}")

    # 测试用例3：从响应中提取
    response = '''Some text content

```json
{
  "goal": "test goal",
  "constraints": [
    {"type": "time", "descri'''

    print("\nTest 3: Extract from response")
    print(f"Input: {response[:100]}...")

    try:
        # 使用完整的解析流程
        result3 = test_chain._parse_json_response(response)
        print(f"[OK] Extracted successfully")
        print(f"  goal: {result3.get('goal')}")
    except Exception as e:
        print(f"[FAIL] Extract failed: {e}")


if __name__ == "__main__":
    test_truncated_json()
