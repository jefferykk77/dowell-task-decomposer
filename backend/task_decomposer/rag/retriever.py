"""
RAG Retriever 模块
负责向量检索和上下文构建
"""

from typing import List, Dict, Any, Optional
import json

try:
    from langchain_community.vectorstores import Chroma
    _langchain_available = True
except ImportError:
    _langchain_available = False


class RAGRetriever:
    """
    RAG 检索器
    负责：查询向量存储 -> 返回相关上下文
    """

    def __init__(
        self,
        vector_store: Optional[Any] = None,
        embedding_model: Optional[Any] = None,
        vector_store_path: Optional[str] = None,
        top_k: int = 3,
        score_threshold: float = 0.5
    ):
        """
        初始化 Retriever

        Args:
            vector_store: 向量存储实例
            embedding_model: 嵌入模型（用于加载向量存储）
            vector_store_path: 向量存储路径
            top_k: 返回前 K 个结果
            score_threshold: 相似度阈值
        """
        self._vector_store = vector_store
        self._embedding_model = embedding_model
        self._vector_store_path = vector_store_path
        self._top_k = top_k
        self._score_threshold = score_threshold
        self._initialized = False

        # 尝试加载向量存储
        if vector_store_path and embedding_model:
            self.load_vector_store(vector_store_path)

    def load_vector_store(self, path: str) -> bool:
        """
        加载已有的向量存储

        Args:
            path: 向量存储路径

        Returns:
            是否加载成功
        """
        if not _langchain_available:
            return False

        try:
            self._vector_store = Chroma(
                persist_directory=path,
                embedding_function=self._embedding_model
            )
            self._initialized = True
            print(f"向量存储加载成功: {path}")
            return True
        except Exception as e:
            print(f"向量存储加载失败: {e}")
            return False

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Any]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量（覆盖默认值）
            score_threshold: 相似度阈值（覆盖默认值）

        Returns:
            相关文档列表
        """
        if not self._vector_store:
            print("向量存储未初始化")
            return []

        k = top_k or self._top_k

        try:
            # 使用相似度搜索
            results = self._vector_store.similarity_search_with_score(
                query,
                k=k
            )

            # 根据阈值过滤
            threshold = score_threshold or self._score_threshold
            if threshold > 0:
                filtered_results = [
                    (doc, score)
                    for doc, score in results
                    if score <= threshold  # Chroma 使用距离，越小越相似
                ]
                return [doc for doc, _ in filtered_results]
            else:
                return [doc for doc, _ in results]

        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def retrieve_as_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        format: str = "detailed"
    ) -> str:
        """
        检索并格式化为字符串

        Args:
            query: 查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            format: 格式化方式: brief, detailed

        Returns:
            格式化的上下文字符串
        """
        docs = self.retrieve(query, top_k, score_threshold)

        if not docs:
            return ""

        if format == "brief":
            # 简洁格式
            contexts = []
            for i, doc in enumerate(docs, 1):
                contexts.append(f"{i}. {doc.page_content}")
            return "\n\n".join(contexts)

        else:
            # 详细格式（包含元数据）
            contexts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get("source", "未知来源")
                contexts.append(
                    f"[{i}] 来源: {source}\n"
                    f"内容: {doc.page_content}\n"
                )
            return "\n\n".join(contexts)

    def retrieve_context_as_string(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.5
    ) -> str:
        """
        检索上下文并返回字符串（兼容旧接口）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            格式化的上下文字符串
        """
        return self.retrieve_as_string(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            format="brief"
        )

    def retrieve_with_metadata(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        检索并返回包含元数据的结果

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            包含内容和元数据的字典列表
        """
        docs = self.retrieve(query, top_k)

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        获取检索器统计信息

        Returns:
            统计信息字典
        """
        return {
            "initialized": self._initialized,
            "vector_store_path": self._vector_store_path,
            "top_k": self._top_k,
            "score_threshold": self._score_threshold
        }
