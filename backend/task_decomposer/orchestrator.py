"""
Task Decomposer Orchestrator
主编排器，串联所有 Chain 实现完整的工作流
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, date

try:
    from langchain_openai import ChatOpenAI
    _langchain_available = True
except ImportError:
    _langchain_available = False

from task_decomposer.schemas import PlanSchema, DecomposeInput, RouterOutput
from task_decomposer.chains import (
    DecomposeChain,
    ClarifyChain,
    EvaluateChain,
    RouterChain
)
from task_decomposer.rag import RAGIngestor, RAGRetriever
from task_decomposer.memory import SessionStore, ProfileStore
from task_decomposer.tools import WebSearchTool, DocSearchTool


class TaskDecomposerOrchestrator:
    """
    任务拆解器主编排器
    实现完整的工作流：路由 -> 澄清 -> 拆解 -> 评估 -> 输出
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.siliconflow.cn/v1",
        model: str = "deepseek-ai/DeepSeek-V3",
        enable_rag: bool = True,
        vector_store_path: Optional[str] = None,
        knowledge_base_path: Optional[str] = None
    ):
        """
        初始化编排器

        Args:
            api_key: LLM API 密钥
            api_base: LLM API 基础 URL
            model: 模型名称
            enable_rag: 是否启用 RAG
            vector_store_path: 向量存储路径
            knowledge_base_path: 知识库文档路径
        """
        # 初始化 LLM
        if _langchain_available:
            self._llm = ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                openai_api_base=api_base,
                temperature=0.3
            )
            print(f"LLM 初始化成功: {model}")
        else:
            self._llm = None
            print("LangChain 未安装，LLM 功能不可用")

        self._enable_rag = enable_rag
        self._vector_store_path = vector_store_path

        # 初始化 RAG
        self._rag_retriever = None
        if enable_rag:
            self._setup_rag(vector_store_path, knowledge_base_path)

        # 初始化 Chains
        self._decompose_chain = DecomposeChain(
            llm=self._llm,
            enable_rag=enable_rag,
            rag_service=self._rag_retriever
        )

        self._clarify_chain = ClarifyChain(llm=self._llm)
        self._evaluate_chain = EvaluateChain(llm=self._llm)
        self._router_chain = RouterChain(llm=self._llm)

        # 初始化 Tools
        self._tools = {
            "web_search": WebSearchTool(),
            "doc_search": DocSearchTool(rag_retriever=self._rag_retriever)
        }

        print("TaskDecomposer 初始化完成")

    def _setup_rag(
        self,
        vector_store_path: Optional[str],
        knowledge_base_path: Optional[str]
    ):
        """
        设置 RAG 组件

        Args:
            vector_store_path: 向量存储路径
            knowledge_base_path: 知识库路径
        """
        try:
            # 这里简化实现，实际应该从配置读取
            from app.core.config import settings
            from app.services.rag_service import get_rag_service

            # 使用现有的 RAG 服务
            rag_service = get_rag_service()
            if rag_service and rag_service.initialized:
                self._rag_retriever = rag_service
                print("RAG 服务初始化成功")
            else:
                print("RAG 服务初始化失败")
                self._enable_rag = False

        except Exception as e:
            print(f"RAG 设置失败: {e}")
            self._enable_rag = False

    async def decompose_task(
        self,
        goal: str,
        context: str = "",
        constraints: List[str] = None,
        user_id: Optional[str] = None,
        enable_evaluation: bool = True,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        work_hours_per_day: float = 8.0,
        work_days_per_week: List[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        主入口：任务拆解

        工作流：
        1. 路由：判断需要澄清还是直接拆解
        2. 澄清（可选）：生成问题并收集回答
        3. 拆解：生成任务计划
        4. 评估（可选）：质检和改进
        5. 保存：记录到用户画像

        Args:
            goal: 用户目标
            context: 背景信息
            constraints: 约束条件
            user_id: 用户ID（用于长期记忆）
            enable_evaluation: 是否启用评估

        Returns:
            拆解结果字典
        """
        def emit(event_type: str, data: Optional[Dict[str, Any]] = None):
            if not on_event:
                return
            payload: Dict[str, Any] = {
                "type": event_type,
                "ts": datetime.utcnow().isoformat()
            }
            if data:
                payload["data"] = data
            try:
                on_event(payload)
            except Exception:
                return

        emit("start", {"goal": goal, "enable_rag": bool(self._enable_rag), "enable_evaluation": bool(enable_evaluation)})

        # 2. 澄清阶段（如果需要）
        session = SessionStore()
        session.set_goal(goal)
        session.set_context(context)
        emit("session", {"session_id": session.session_id})

        if constraints:
            session.add_constraints(constraints)

        emit("router_start", {})
        router_result = self._router_chain.run(
            user_input=f"{goal}\n{context}",
            on_event=on_event
        )
        emit("router_result", router_result.model_dump() if hasattr(router_result, "model_dump") else {"intent": router_result.intent})

        print(f"路由结果: {router_result.intent}")

        if router_result.intent == RouterChain.INTENT_CLARIFY:
            print("需要澄清问题...")
            emit("clarify_start", {})

            clarify_result = self._clarify_chain.run(
                goal=goal,
                context=context,
                on_event=on_event
            )

            session.set_current_step("clarify")
            emit("clarify_result", clarify_result.model_dump() if hasattr(clarify_result, "model_dump") else {"questions": getattr(clarify_result, "questions", [])})

            # 在实际应用中，这里应该暂停并等待用户回答
            # 这里简化处理，直接记录问题
            for q in clarify_result.questions:
                print(f"问题 {q.get('id')}: {q.get('question')}")

            # 返回需要澄清
            return {
                "status": "need_clarification",
                "questions": clarify_result.questions,
                "session_id": session.session_id
            }

        # 3. 拆解阶段
        print("开始任务拆解...")
        session.set_current_step("decompose")
        emit("decompose_start", {})

        plan = self._decompose_chain.run(
            goal=goal,
            context=context,
            constraints=constraints or [],
            on_event=on_event,
            start_date=start_date,
            end_date=end_date,
            work_hours_per_day=work_hours_per_day,
            work_days_per_week=work_days_per_week
        )
        emit("decompose_result", {"milestones": len(getattr(plan, "milestones", []) or []), "tasks": len(getattr(plan, "tasks", []) or [])})

        # 保存计划版本
        session.save_plan_version(plan, version="v1")

        # 4. 评估阶段（可选）
        if enable_evaluation:
            print("评估计划质量...")
            session.set_current_step("evaluate")
            emit("evaluate_start", {})

            eval_result = self._evaluate_chain.run(plan=plan, on_event=on_event)
            emit("evaluate_result", eval_result.model_dump() if hasattr(eval_result, "model_dump") else {"overall_score": getattr(eval_result, "overall_score", None)})

            print(f"评分: {eval_result.overall_score}/100")

            # 如果评分不理想，尝试改进
            if eval_result.rewrite_needed or eval_result.overall_score < 80:
                print("尝试改进计划...")
                plan, eval_result = self._evaluate_chain.evaluate_and_rewrite(
                    plan=plan,
                    decompose_chain=self._decompose_chain
                )
                session.save_plan_version(plan, version="v2")

        # 5. 保存到用户画像（长期记忆）
        if user_id:
            profile = ProfileStore(user_id)
            profile.add_history(
                goal=goal,
                plan=plan,
                tags=constraints or []
            )
            print(f"已保存到用户画像: {user_id}")

        session.set_current_step("completed")
        emit("completed", {"session_id": session.session_id})

        # 6. 返回结果
        return {
            "status": "completed",
            "plan": plan,
            "session_id": session.session_id,
            "evaluation": eval_result if enable_evaluation else None,
            "router_result": router_result
        }

    def get_plan_from_session(self, session_id: str) -> Optional[PlanSchema]:
        """
        从会话获取计划

        Args:
            session_id: 会话ID

        Returns:
            任务计划
        """
        # 实际实现中，应该从持久化存储加载
        # 这里简化处理
        return None

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像摘要
        """
        profile = ProfileStore(user_id)
        return profile.get_summary()

    def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            preferences: 偏好字典
        """
        profile = ProfileStore(user_id)
        for key, value in preferences.items():
            profile.set_preference(key, value)
        print(f"用户偏好已更新: {user_id}")

    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self._tools.keys())

    async def use_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self._tools:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}"
            }

        tool = self._tools[tool_name]

        # 构建输入
        from task_decomposer.tools import ToolInput
        input_class = type(f"{tool_name}Input", (ToolInput,), kwargs)
        tool_input = input_class(**kwargs)

        # 执行工具
        result = await tool.run(tool_input)

        return result.model_dump()
