"""
RAG 服务模块 - 用于任务拆解前的上下文检索
实现 2-step RAG 的第一步：在任务拆解前检索相关上下文
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    _langchain_available = True
except ImportError:
    _langchain_available = False

from app.core.config import settings


class RAGService:
    """RAG 服务：提供向量存储和检索功能"""

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = None
        self.initialized = False

        if not _langchain_available:
            print("LangChain 未安装，RAG 功能不可用")
            return

        try:
            self._initialize_embeddings()
            self._initialize_text_splitter()
            self.initialized = True
        except Exception as e:
            print(f"RAG 服务初始化失败: {e}")

    def _initialize_embeddings(self):
        """初始化嵌入模型"""
        # 优先使用 OpenAI Embeddings
        if settings.SILICONFLOW_API_KEY:
            try:
                # 尝试使用硅基流动的 API（兼容 OpenAI 格式）
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=settings.SILICONFLOW_API_KEY,
                    openai_api_base="https://api.siliconflow.cn/v1"
                )
                print("使用硅基流动 Embeddings")
                return
            except Exception as e:
                print(f"硅基流动 Embeddings 初始化失败: {e}")

        # 回退到本地 HuggingFace 模型
        try:
            # 使用轻量级的中文模型
            model_name = "shibing624/text2vec-base-chinese"
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print(f"使用本地 HuggingFace Embeddings: {model_name}")
        except Exception as e:
            print(f"HuggingFace Embeddings 初始化失败: {e}")
            raise

    def _initialize_text_splitter(self):
        """初始化文本分割器"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

    def create_knowledge_base(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        创建知识库

        Args:
            texts: 文本列表
            metadata: 可选的元数据列表

        Returns:
            是否成功创建
        """
        if not self.initialized:
            return False

        try:
            # 创建文档对象
            documents = []
            for i, text in enumerate(texts):
                doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
                doc_metadata.update({"index": i, "created_at": datetime.now().isoformat()})
                documents.append(Document(page_content=text, metadata=doc_metadata))

            # 分割文本
            splits = self.text_splitter.split_documents(documents)

            # 创建向量存储（使用 FAISS）
            self.vector_store = FAISS.from_documents(splits, self.embeddings)

            print(f"知识库创建成功，共 {len(splits)} 个文档块")
            return True

        except Exception as e:
            print(f"创建知识库失败: {e}")
            return False

    def add_documents(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        向现有知识库添加文档

        Args:
            texts: 文本列表
            metadata: 可选的元数据列表

        Returns:
            是否成功添加
        """
        if not self.initialized:
            return False

        try:
            # 创建文档对象
            documents = []
            for i, text in enumerate(texts):
                doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
                doc_metadata.update({"index": i, "created_at": datetime.now().isoformat()})
                documents.append(Document(page_content=text, metadata=doc_metadata))

            # 分割文本
            splits = self.text_splitter.split_documents(documents)

            # 如果向量存储不存在，创建新的
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(splits, self.embeddings)
            else:
                # 添加到现有向量存储
                self.vector_store.add_documents(splits)

            print(f"成功添加 {len(splits)} 个文档块")
            return True

        except Exception as e:
            print(f"添加文档失败: {e}")
            return False

    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        检索与查询相关的上下文

        Args:
            query: 查询文本
            top_k: 返回最相关的 k 个结果
            score_threshold: 可选的相似度阈值（0-1）

        Returns:
            检索到的文档列表，包含内容、元数据和相似度分数
        """
        if not self.initialized or self.vector_store is None:
            print("RAG 服务未初始化或知识库为空")
            return []

        try:
            # 执行相似度搜索
            if score_threshold:
                # 使用阈值过滤
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=top_k
                )
                # 过滤低于阈值的结果
                filtered_results = [
                    (doc, score) for doc, score in results
                    if score <= score_threshold  # FAISS 使用距离，越小越相似
                ]
                results = filtered_results
            else:
                # 直接返回 top_k
                results = self.vector_store.similarity_search_with_score(query, k=top_k)

            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "similarity": float(1 / (1 + score))  # 转换为相似度（0-1）
                })

            return formatted_results

        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def retrieve_context_as_string(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> str:
        """
        检索相关上下文并格式化为字符串（用于 LLM Prompt）

        Args:
            query: 查询文本
            top_k: 返回最相关的 k 个结果
            score_threshold: 可选的相似度阈值

        Returns:
            格式化的上下文字符串
        """
        results = self.retrieve_context(query, top_k, score_threshold)

        if not results:
            return ""

        formatted = "【相关知识库上下文】\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['content']}\n"
            if result['metadata']:
                formatted += f"   (来源: {result['metadata']})\n"
            formatted += f"   (相似度: {result['similarity']:.2f})\n\n"

        return formatted

    def save_vector_store(self, path: str) -> bool:
        """
        保存向量存储到磁盘

        Args:
            path: 保存路径

        Returns:
            是否成功保存
        """
        if not self.initialized or self.vector_store is None:
            return False

        try:
            self.vector_store.save_local(path)
            print(f"向量存储已保存到 {path}")
            return True
        except Exception as e:
            print(f"保存向量存储失败: {e}")
            return False

    def load_vector_store(self, path: str) -> bool:
        """
        从磁盘加载向量存储

        Args:
            path: 加载路径

        Returns:
            是否成功加载
        """
        if not self.initialized:
            return False

        try:
            self.vector_store = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
            print(f"向量存储已从 {path} 加载")
            return True
        except Exception as e:
            print(f"加载向量存储失败: {e}")
            return False


# 全局 RAG 服务实例
_rag_service_instance = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance


def initialize_default_knowledge_base():
    """
    初始化默认知识库
    包含任务管理、时间规划、学习方法等相关知识
    """
    rag_service = get_rag_service()

    if not rag_service.initialized:
        print("RAG 服务未初始化，跳过知识库创建")
        return

    # 默认知识库内容
    default_knowledge = [
        {
            "content": """任务拆解的核心原则：
1. SMART 原则：目标应该是具体的、可衡量的、可达到的、相关的、有时限的
2. 任务分解：将大任务分解为 2-4 小时可直接执行的小任务
3. 依赖关系：识别任务之间的前置和依赖关系
4. 里程碑设置：在关键节点设置可检查的里程碑
5. 缓冲时间：为不可预见的情况预留 15-20% 的缓冲时间""",
            "metadata": {"category": "task_management", "title": "任务拆解原则"}
        },
        {
            "content": """时间规划最佳实践：
1. 黄金时间：将高难度任务安排在精力最充沛的时段
2. 番茄工作法：25分钟专注工作 + 5分钟休息，每4个番茄后休息15-30分钟
3. 时间块：将相似任务集中在同一时间段完成，减少上下文切换
4. 二八定律：20%的关键任务决定80%的成果，优先处理重要且紧急的任务
5. 深度工作：每天至少预留2-4小时的深度工作时段，避免打扰""",
            "metadata": {"category": "time_management", "title": "时间规划最佳实践"}
        },
        {
            "content": """学习方法论：
1. 费曼学习法：通过教授他人来检验自己的理解程度
2. 刻意练习：专注于弱点，持续反馈和改进
3. 间隔重复：使用间隔重复算法巩固记忆（如 Anki）
4. 项目式学习：通过实际项目来学习新知识
5. 输入输出比：保持学习和实践的平衡，建议 30% 学习 + 70% 实践""",
            "metadata": {"category": "learning", "title": "学习方法论"}
        },
        {
            "content": """目标制定的 OKR 方法：
1. Objective（目标）：你想要达成什么
2. Key Results（关键结果）：如何衡量是否达成
3. OKR 设定建议：
   - 每个 O 对应 3-5 个 KR
   - KR 应该是可量化的
   - 具有挑战性但可实现
   - 季度评审和调整
4. OKR 与 KPI 的区别：OKR 关注增长和挑战，KPI 关注维持现状""",
            "metadata": {"category": "goal_setting", "title": "OKR 方法"}
        },
        {
            "content": """学习新技能的阶段规划：
1. 了解阶段（1-2周）：阅读基础资料，了解整体框架和核心概念
2. 模仿阶段（2-4周）：跟随教程和案例，模仿完成基础项目
3. 实践阶段（1-3个月）：独立完成小项目，遇到问题查资料解决
4. 深入阶段（3-6个月）：学习高级特性，优化和改进项目
5. 精通阶段（6个月+）：阅读源码、参与开源、总结最佳实践""",
            "metadata": {"category": "learning", "title": "技能学习阶段"}
        },
        {
            "content": """防止拖延的策略：
1. 两分钟原则：如果任务能在2分钟内完成，立即去做
2. 五分钟启动法：告诉自己只做5分钟，通常开始后就会继续
3. 任务分解：将大任务分解为小任务，减少心理压力
4. 环境设计：减少干扰源（如手机、社交媒体）
5. 承诺机制：向他人公开自己的目标，增加社会压力
6. 奖励机制：完成任务后给予自己适当奖励""",
            "metadata": {"category": "productivity", "title": "防止拖延策略"}
        },
        {
            "content": """项目管理的关键要素：
1. 范围管理：明确项目边界，避免范围蔓延
2. 时间管理：制定 realistic 的时间计划
3. 质量管理：定义明确的验收标准
4. 风险管理：识别潜在风险并制定应对策略
5. 沟通管理：建立定期沟通机制
6. 干系人管理：识别和管理各方期望""",
            "metadata": {"category": "project_management", "title": "项目管理要素"}
        },
        {
            "content": """高效学习路径设计：
1. 明确学习目标：具体到能够做什么（如"能够独立开发一个Web应用"）
2. 评估当前水平：识别已有知识和技能差距
3. 选择学习资源：书籍、课程、文档、社区（推荐官方文档+实战项目）
4. 制定学习计划：分解为周目标和日任务
5. 实践验证：通过项目验证学习成果
6. 持续迭代：根据学习效果调整计划""",
            "metadata": {"category": "learning", "title": "学习路径设计"}
        },
        {
            "content": """周计划制定要点：
1. 回顾上周：总结完成情况和未完成原因
2. 确定本周重点：选择1-3个最重要的目标
3. 时间分配：为不同任务类型分配时间块
4. 预留缓冲：至少预留 20% 的弹性时间
5. 每日仪式：每天早上检查今日计划，晚上回顾完成情况
6. 周末总结：评估本周成果，调整下周计划""",
            "metadata": {"category": "planning", "title": "周计划制定要点"}
        },
        {
            "content": """技术项目开发流程：
1. 需求分析：明确功能需求和技术约束
2. 技术选型：根据项目特点选择合适的技术栈
3. 架构设计：设计系统架构和模块划分
4. 原型开发：快速实现核心功能验证可行性
5. 迭代开发：按照优先级逐步实现功能
6. 测试验证：单元测试、集成测试、用户测试
7. 部署上线：准备生产环境和监控
8. 维护优化：收集反馈，持续改进""",
            "metadata": {"category": "development", "title": "技术项目开发流程"}
        }
    ]

    # 创建知识库
    texts = [item["content"] for item in default_knowledge]
    metadata = [item["metadata"] for item in default_knowledge]

    success = rag_service.create_knowledge_base(texts, metadata)

    if success:
        print("默认知识库初始化成功")

        # 尝试保存到本地
        try:
            save_path = os.path.join(os.path.dirname(__file__), "../../data/vector_store")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            rag_service.save_vector_store(save_path)
        except Exception as e:
            print(f"保存知识库失败（不影响使用）: {e}")
    else:
        print("默认知识库初始化失败")
