"""
搜索类工具
用于信息补全
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput


class WebSearchInput(ToolInput):
    """网络搜索输入"""
    query: str = Field(..., description="搜索查询")


class WebSearchTool(BaseTool):
    """
    网络搜索工具
    用于搜索行业资料、最佳实践等
    """

    name = "web_search"
    description = "在互联网上搜索信息，用于获取行业资料、最佳实践、技术文档等"

    def __init__(self, search_engine: Optional[str] = None):
        """
        初始化搜索工具

        Args:
            search_engine: 搜索引擎（可选，默认使用通用搜索）
        """
        self._search_engine = search_engine

    async def run(self, input_data: WebSearchInput) -> ToolOutput:
        """
        执行网络搜索

        Args:
            input_data: 包含搜索查询的输入

        Returns:
            搜索结果
        """
        try:
            query = input_data.query

            # 实际实现中，这里应该调用真实的搜索 API
            # 例如：Google Search API, Bing Search API
            # 这里提供模拟实现

            results = {
                "query": query,
                "results": [
                    {
                        "title": f"关于 '{query}' 的最佳实践",
                        "url": "https://example.com/best-practices",
                        "snippet": "这里是搜索结果的摘要..."
                    },
                    {
                        "title": f"{query} - 完整指南",
                        "url": "https://example.com/guide",
                        "snippet": "更详细的指南内容..."
                    }
                ]
            }

            return ToolOutput(
                success=True,
                data=results
            )

        except Exception as e:
            return ToolOutput(
                success=False,
                error=str(e)
            )

    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询内容"
                }
            },
            "required": ["query"]
        }


class DocSearchInput(ToolInput):
    """文档搜索输入"""
    query: str = Field(..., description="搜索查询")
    collection: str = Field(default="default", description="文档集合名称")


class DocSearchTool(BaseTool):
    """
    文档搜索工具
    用于搜索内部知识库、文档等
    """

    name = "doc_search"
    description = "在内部知识库中搜索相关文档、流程、规范等"

    def __init__(self, rag_retriever: Optional[Any] = None):
        """
        初始化文档搜索工具

        Args:
            rag_retriever: RAG 检索器实例
        """
        self._retriever = rag_retriever

    async def run(self, input_data: DocSearchInput) -> ToolOutput:
        """
        执行文档搜索

        Args:
            input_data: 包含搜索查询的输入

        Returns:
            搜索结果
        """
        try:
            query = input_data.query

            if not self._retriever:
                return ToolOutput(
                    success=False,
                    error="RAG 检索器未初始化"
                )

            # 使用 RAG 检索
            results = self._retriever.retrieve_with_metadata(query)

            return ToolOutput(
                success=True,
                data={
                    "query": query,
                    "count": len(results),
                    "results": results
                }
            )

        except Exception as e:
            return ToolOutput(
                success=False,
                error=str(e)
            )

    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询内容"
                },
                "collection": {
                    "type": "string",
                    "description": "文档集合名称（可选）"
                }
            },
            "required": ["query"]
        }
