"""
Task Decomposer V2.0 测试
测试新的模块化架构
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_decompose_chain():
    """测试 Decompose Chain"""
    print("\n" + "="*60)
    print("测试 Decompose Chain")
    print("="*60)

    from task_decomposer.chains import DecomposeChain
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        openai_api_key=os.getenv("SILICONFLOW_API_KEY"),
        openai_api_base="https://api.siliconflow.cn/v1",
        temperature=0.3
    )

    chain = DecomposeChain(llm=llm, enable_rag=False)

    plan = chain.run(
        goal="开发一个待办事项小程序",
        context="用于个人任务管理",
        constraints=["预算有限", "需要在一周内上线"]
    )

    print(f"\n✓ Plan 创建成功")
    print(f"  - 目标: {plan.goal}")
    print(f"  - 里程碑: {len(plan.milestones)} 个")
    print(f"  - 任务: {len(plan.tasks)} 个")
    print(f"  - 开放问题: {len(plan.open_questions)} 个")
    print(f"  - 约束: {len(plan.constraints)} 个")

    # 显示前3个任务
    print(f"\n前 3 个任务:")
    for task in plan.tasks[:3]:
        print(f"  [{task.id}] {task.title}")
        print(f"    优先级: {task.priority} | 预估: {task.estimate_hours}h")

    return plan


async def test_clarify_chain():
    """测试 Clarify Chain"""
    print("\n" + "="*60)
    print("测试 Clarify Chain")
    print("="*60)

    from task_decomposer.chains import ClarifyChain
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        openai_api_key=os.getenv("SILICONFLOW_API_KEY"),
        openai_api_base="https://api.siliconflow.cn/v1",
        temperature=0.3
    )

    chain = ClarifyChain(llm=llm)

    result = chain.run(
        goal="做一个网站",
        context="用户描述非常模糊"
    )

    print(f"\n✓ 澄清问题生成成功")
    print(f"  - 问题数量: {len(result.questions)}")
    print(f"  - 理由: {result.reasoning}")

    print(f"\n建议的问题:")
    for q in result.questions:
        print(f"  [{q.get('id')}] {q.get('question')}")
        print(f"    关键: {q.get('critical')} | 原因: {q.get('reason')}")

    return result


async def test_evaluate_chain(plan):
    """测试 Evaluate Chain"""
    print("\n" + "="*60)
    print("测试 Evaluate Chain")
    print("="*60)

    from task_decomposer.chains import EvaluateChain
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        openai_api_key=os.getenv("SILICONFLOW_API_KEY"),
        openai_api_base="https://api.siliconflow.cn/v1",
        temperature=0.3
    )

    chain = EvaluateChain(llm=llm)

    result = chain.run(plan=plan)

    print(f"\n✓ 计划评估完成")
    print(f"  - 总分: {result.overall_score}/100")
    print(f"  - 通过: {result.passed}")
    print(f"  - 需要重写: {result.rewrite_needed}")
    print(f"  - 问题数量: {len(result.issues)}")

    if result.issues:
        print(f"\n发现的问题:")
        for issue in result.issues[:3]:
            print(f"  - [{issue.severity}] {issue.description}")
            print(f"    建议: {issue.suggestion}")

    return result


async def test_router_chain():
    """测试 Router Chain"""
    print("\n" + "="*60)
    print("测试 Router Chain")
    print("="*60)

    from task_decomposer.chains import RouterChain
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        openai_api_key=os.getenv("SILICONFLOW_API_KEY"),
        openai_api_base="https://api.siliconflow.cn/v1",
        temperature=0.3
    )

    chain = RouterChain(llm=llm)

    # 测试用例
    test_cases = [
        "开发一个待办事项小程序",
        "做一个网站",
        "我最近很焦虑，事情太多了"
    ]

    for user_input in test_cases:
        result = chain.run(user_input=user_input)
        print(f"\n输入: {user_input}")
        print(f"  意图: {result.intent}")
        print(f"  置信度: {result.confidence}")
        print(f"  理由: {result.reasoning}")

    return True


async def test_memory():
    """测试 Memory 模块"""
    print("\n" + "="*60)
    print("测试 Memory 模块")
    print("="*60)

    from task_decomposer.memory import SessionStore, ProfileStore

    # 测试 Session Store
    session = SessionStore()
    session.set_goal("测试目标")
    session.set_context("测试背景")
    session.add_constraints(["约束1", "约束2"])
    session.record_answer("Q1", "用户的回答")

    print(f"\n✓ Session Store")
    print(f"  - Session ID: {session.session_id}")
    print(f"  - 目标: {session._data['goal']}")
    print(f"  - 约束: {session._data['constraints']}")
    print(f"  - 回答: {session.get_all_answers()}")

    # 测试 Profile Store
    profile = ProfileStore("test_user")
    profile.set_role("开发工程师")
    profile.set_preference("output_format", "detailed")
    profile.set_preference("include_estimates", True)

    print(f"\n✓ Profile Store")
    print(f"  - 用户ID: {profile.user_id}")
    print(f"  - 角色: {profile.get_role()}")
    print(f"  - 偏好: {profile.get_all_preferences()}")

    return True


async def test_orchestrator():
    """测试完整的编排器"""
    print("\n" + "="*60)
    print("测试 Orchestrator（完整工作流）")
    print("="*60)

    from task_decomposer.orchestrator import TaskDecomposerOrchestrator

    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("错误: 请设置 SILICONFLOW_API_KEY")
        return

    orchestrator = TaskDecomposerOrchestrator(
        api_key=api_key,
        api_base="https://api.siliconflow.cn/v1",
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        enable_rag=False  # 简化测试，暂时禁用 RAG
    )

    result = await orchestrator.decompose_task(
        goal="开发一个待办事项小程序",
        context="用于个人任务管理",
        constraints=["预算有限", "需要在一周内上线"],
        user_id="test_user",
        enable_evaluation=True
    )

    if result["status"] == "completed":
        plan = result["plan"]
        print(f"\n✓ 任务拆解完成")
        print(f"  - 目标: {plan.goal}")
        print(f"  - 里程碑: {len(plan.milestones)} 个")
        print(f"  - 任务: {len(plan.tasks)} 个")

        if result["evaluation"]:
            print(f"  - 评分: {result['evaluation'].overall_score}/100")

    return result


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Task Decomposer V2.0 测试套件")
    print("="*60)

    try:
        # 1. 测试 Decompose Chain
        plan = await test_decompose_chain()

        # 2. 测试 Clarify Chain
        await test_clarify_chain()

        # 3. 测试 Evaluate Chain
        await test_evaluate_chain(plan)

        # 4. 测试 Router Chain
        await test_router_chain()

        # 5. 测试 Memory
        await test_memory()

        # 6. 测试完整编排器
        await test_orchestrator()

        print("\n" + "="*60)
        print("✓ 所有测试完成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
