"""
文档生成类工具
用于生成产物
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from .base import BaseTool, ToolInput, ToolOutput


class CreateDocInput(ToolInput):
    """创建文档输入"""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    doc_type: str = Field(
        default="markdown",
        description="文档类型: markdown, text, html"
    )
    output_path: Optional[str] = Field(None, description="输出路径")


class CreateDocTool(BaseTool):
    """
    创建文档工具
    用于生成 PRD、大纲、总结等文档
    """

    name = "create_doc"
    description = "创建文档，如 PRD、大纲、总结等，支持多种格式"

    def __init__(self, default_output_dir: Optional[str] = None):
        """
        初始化文档创建工具

        Args:
            default_output_dir: 默认输出目录
        """
        self._default_output_dir = default_output_dir

    async def run(self, input_data: CreateDocInput) -> ToolOutput:
        """
        创建文档

        Args:
            input_data: 包含标题、内容的输入

        Returns:
            创建结果
        """
        try:
            title = input_data.title
            content = input_data.content
            doc_type = input_data.doc_type

            # 确定输出路径
            output_path = input_data.output_path
            if not output_path and self._default_output_dir:
                # 生成文件名
                safe_title = title.replace(" ", "_").replace("/", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "md" if doc_type == "markdown" else doc_type
                output_path = f"{self._default_output_dir}/{safe_title}_{timestamp}.{ext}"

            # 实际实现中，这里应该将文档保存到文件系统或数据库
            # 这里提供模拟实现

            result = {
                "title": title,
                "doc_type": doc_type,
                "output_path": output_path,
                "size_bytes": len(content.encode('utf-8')),
                "created_at": datetime.utcnow().isoformat()
            }

            return ToolOutput(
                success=True,
                data=result
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
                "title": {
                    "type": "string",
                    "description": "文档标题"
                },
                "content": {
                    "type": "string",
                    "description": "文档内容"
                },
                "doc_type": {
                    "type": "string",
                    "enum": ["markdown", "text", "html"],
                    "description": "文档类型"
                },
                "output_path": {
                    "type": "string",
                    "description": "输出路径（可选）"
                }
            },
            "required": ["title", "content"]
        }


class SendEmailInput(ToolInput):
    """发送邮件输入"""
    to: List[str] = Field(..., description="收件人列表")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件正文")
    cc: Optional[List[str]] = Field(None, description="抄送列表")


class SendEmailTool(BaseTool):
    """
    发送邮件工具
    用于将计划同步给同事/自己
    """

    name = "send_email"
    description = "发送邮件，将计划或文档同步给相关人员"

    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """
        初始化邮件工具

        Args:
            smtp_config: SMTP 配置
        """
        self._smtp_config = smtp_config or {}

    async def run(self, input_data: SendEmailInput) -> ToolOutput:
        """
        发送邮件

        Args:
            input_data: 包含收件人、主题、正文的输入

        Returns:
            发送结果
        """
        try:
            to = input_data.to
            subject = input_data.subject
            body = input_data.body
            cc = input_data.cc or []

            # 实际实现中，这里应该调用真实的邮件发送服务
            # 例如：SMTP, SendGrid, AWS SES
            # 这里提供模拟实现

            result = {
                "to": to,
                "cc": cc,
                "subject": subject,
                "sent_at": datetime.utcnow().isoformat(),
                "message_id": f"msg_{datetime.utcnow().timestamp()}"
            }

            return ToolOutput(
                success=True,
                data=result
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
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "收件人邮箱列表"
                },
                "subject": {
                    "type": "string",
                    "description": "邮件主题"
                },
                "body": {
                    "type": "string",
                    "description": "邮件正文"
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "抄送列表（可选）"
                }
            },
            "required": ["to", "subject", "body"]
        }
