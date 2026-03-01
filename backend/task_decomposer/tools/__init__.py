"""
Tools 模块
定义 function calling 工具
"""

from .base import BaseTool, ToolInput, ToolOutput
from .search_tools import WebSearchTool, DocSearchTool
from .document_tools import CreateDocTool, SendEmailTool

__all__ = [
    "BaseTool",
    "ToolInput",
    "ToolOutput",
    "WebSearchTool",
    "DocSearchTool",
    "CreateDocTool",
    "SendEmailTool"
]
