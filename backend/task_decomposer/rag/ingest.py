"""
RAG Ingest 模块
负责文档加载、切分、嵌入和向量存储
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import os

try:
    from langchain_community.document_loaders import (
        TextLoader,
        DirectoryLoader,
        JSONLoader
    )
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    _langchain_available = True
except ImportError:
    _langchain_available = False


class RAGIngestor:
    """
    RAG 知识库加载器
    负责：加载文档 -> 切分 -> 嵌入 -> 存储
    """

    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        vector_store_path: Optional[str] = None
    ):
        """
        初始化 Ingestor

        Args:
            embedding_model: 嵌入模型实例
            chunk_size: 文档切分大小
            chunk_overlap: 切分重叠大小
            vector_store_path: 向量存储路径
        """
        self._embedding_model = embedding_model
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._vector_store_path = vector_store_path

        # 初始化文本切分器
        if _langchain_available:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
            )

    def load_text_file(self, file_path: str) -> List[Any]:
        """
        加载单个文本文件

        Args:
            file_path: 文件路径

        Returns:
            文档列表
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装")

        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()

    def load_directory(
        self,
        directory: str,
        glob_pattern: str = "**/*.txt"
    ) -> List[Any]:
        """
        加载目录下的所有文档

        Args:
            directory: 目录路径
            glob_pattern: 文件匹配模式

        Returns:
            文档列表
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装")

        loader = DirectoryLoader(
            directory,
            glob=glob_pattern,
            loader_kwargs={'encoding': 'utf-8'}
        )
        return loader.load()

    def load_json_file(
        self,
        file_path: str,
        text_content_key: str = "content"
    ) -> List[Any]:
        """
        加载 JSON 文件

        Args:
            file_path: JSON 文件路径
            text_content_key: JSON 中文本内容的字段名

        Returns:
            文档列表
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装")

        loader = JSONLoader(
            file_path,
            jq_schema=f'.[].{text_content_key}',
            text_content=False
        )
        return loader.load()

    def split_documents(self, documents: List[Any]) -> List[Any]:
        """
        切分文档

        Args:
            documents: 原始文档列表

        Returns:
            切分后的文档块列表
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装")

        return self._text_splitter.split_documents(documents)

    def create_vector_store(
        self,
        documents: List[Any],
        persist_directory: Optional[str] = None
    ) -> Any:
        """
        创建向量存储

        Args:
            documents: 文档块列表
            persist_directory: 持久化目录

        Returns:
            向量存储实例
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装")

        if not self._embedding_model:
            raise ValueError("嵌入模型未初始化")

        persist_dir = persist_directory or self._vector_store_path

        # 创建向量存储
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self._embedding_model,
            persist_directory=persist_dir
        )

        # 持久化
        if persist_dir:
            vector_store.persist()

        return vector_store

    def ingest_and_store(
        self,
        source: str,
        source_type: str = "file",
        persist: bool = True
    ) -> Any:
        """
        一站式加载和存储

        Args:
            source: 数据源（文件路径或目录）
            source_type: 数据源类型: file, directory
            persist: 是否持久化

        Returns:
            向量存储实例
        """
        # 1. 加载文档
        if source_type == "file":
            documents = self.load_text_file(source)
        elif source_type == "directory":
            documents = self.load_directory(source)
        else:
            raise ValueError(f"不支持的 source_type: {source_type}")

        print(f"加载了 {len(documents)} 个文档")

        # 2. 切分文档
        splits = self.split_documents(documents)
        print(f"切分为 {len(splits)} 个块")

        # 3. 创建向量存储
        vector_store = self.create_vector_store(
            documents=splits,
            persist_directory=self._vector_store_path if persist else None
        )

        print(f"向量存储创建成功")

        return vector_store

    def load_knowledge_base(
        self,
        kb_dir: str,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        加载完整知识库

        Args:
            kb_dir: 知识库目录
            persist: 是否持久化

        Returns:
            包含统计信息的字典
        """
        kb_path = Path(kb_dir)
        if not kb_path.exists():
            raise FileNotFoundError(f"知识库目录不存在: {kb_dir}")

        # 支持多种文件类型
        all_documents = []

        # 加载 txt 文件
        txt_files = list(kb_path.glob("**/*.txt"))
        for txt_file in txt_files:
            try:
                docs = self.load_text_file(str(txt_file))
                all_documents.extend(docs)
            except Exception as e:
                print(f"加载文件失败 {txt_file}: {e}")

        # 加载 md 文件
        md_files = list(kb_path.glob("**/*.md"))
        for md_file in md_files:
            try:
                docs = self.load_text_file(str(md_file))
                all_documents.extend(docs)
            except Exception as e:
                print(f"加载文件失败 {md_file}: {e}")

        if not all_documents:
            print(f"警告: {kb_dir} 中没有找到可加载的文档")
            return {"total_docs": 0, "total_splits": 0}

        # 切分
        splits = self.split_documents(all_documents)

        # 创建向量存储
        vector_store = self.create_vector_store(
            documents=splits,
            persist_directory=self._vector_store_path if persist else None
        )

        return {
            "total_docs": len(all_documents),
            "total_splits": len(splits),
            "vector_store": vector_store
        }
