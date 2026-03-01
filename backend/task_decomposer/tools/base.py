"""
Tool 基类
定义所有工具的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolInput(BaseModel):
    """工具输入基类"""
    pass


class ToolOutput(BaseModel):
    """工具输出基类"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseTool(ABC):
    """
    工具基类
    所有工具都应该继承这个类
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, input_data: ToolInput) -> ToolOutput:
        """
        执行工具

        Args:
            input_data: 工具输入

        Returns:
            ToolOutput: 工具输出
        """
        raise NotImplementedError("子类必须实现 run 方法")

    def to_openai_function(self) -> Dict[str, Any]:
        """
        转换为 OpenAI Function 格式

        Returns:
            Function 定义字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }

    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数 Schema（子类可重写）

        Returns:
            参数 Schema
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
