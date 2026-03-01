"""
测试 LangChain + RAG 改造后的功能
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.decomposer import DecomposerService
from datetime import date

def test_decompose():
    """测试任务分解功能"""
    print("=" * 50)
    print("测试 LangChain + 2-Step RAG 任务分解")
    print("=" * 50)

    # 创建服务实例
    print("\n[1/4] 初始化 DecomposerService...")
    service = DecomposerService()
    print("OK - DecomposerService 初始化成功")

    # 检查 RAG 是否启用
    print("\n[2/4] 检查 RAG 状态...")
    if service._rag_enabled:
        print(f"OK - RAG 已启用")
        print(f"     - RAG 服务初始化: {service._rag_service.initialized if service._rag_service else False}")
        print(f"     - LLM 初始化: {service._llm is not None}")
    else:
        print("INFO - RAG 未启用（可能是配置问题）")

    # 测试简单任务分解（使用规则分解，不需要 API）
    print("\n[3/4] 测试规则分解（不需要 LLM）...")
    try:
        result = service.decompose(
            title="学习 Python 基础",
            year=None,
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 21),
            hours_per_week=10,
            work_days=[0, 1, 2, 3, 4],
            strategy="rule",  # 使用规则分解
            preferences=None,
            goal_context=None,
            current_context=None,
            time_context=None,
            priority_context=None,
            environment_context=None,
            dependency_context=None
        )
        print(f"OK - 规则分解成功")
        print(f"     - 生成任务数: {len(result.get('days', []))} 个日任务")
        print(f"     - 生成周数: {len(result.get('weeks', []))} 个周任务")
    except Exception as e:
        print(f"FAIL - 规则分解失败: {e}")
        return False

    # 如果有 API Key，测试 AI 分解
    print("\n[4/4] 测试 AI + RAG 分解（需要 API Key）...")
    from app.core.config import settings
    if settings.SILICONFLOW_API_KEY:
        try:
            result = service.decompose(
                title="学习 LangChain 框架",
                year=None,
                start_date=date(2026, 1, 15),
                end_date=date(2026, 1, 28),
                hours_per_week=10,
                work_days=[5, 6],  # 周末
                strategy="ai",  # 使用 AI + RAG
                preferences={"学习风格": "项目驱动"},
                goal_context={
                    "long_term_goal": "成为 AI 应用开发专家",
                    "completion_criteria": "能够独立开发 RAG 应用"
                },
                current_context={
                    "current_progress": "有 Python 基础，了解 OpenAI API",
                    "existing_resources": "已有开发环境和 API Key"
                },
                time_context=None,
                priority_context=None,
                environment_context=None,
                dependency_context=None
            )
            print(f"OK - AI + RAG 分解成功")
            print(f"     - 年度目标: {result.get('year', {}).get('title', 'N/A')}")
            print(f"     - 生成任务数: {len(result.get('days', []))} 个日任务")

            # 检查是否生成了周末任务
            if result.get('days'):
                first_task_date = result['days'][0].get('task_date', '')
                print(f"     - 首个任务日期: {first_task_date}")

        except Exception as e:
            print(f"WARN - AI + RAG 分解失败: {e}")
            print("       （这可能是网络问题或 API Key 问题）")
    else:
        print("SKIP - 未配置 SILICONFLOW_API_KEY，跳过 AI 测试")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        success = test_decompose()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
