"""
Chain 基类
定义所有 Chain 的通用接口和功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic
import json
from datetime import datetime

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.chains import LLMChain
    from langchain.output_parsers import PydanticOutputParser
    _langchain_available = True
except ImportError:
    _langchain_available = False


T = TypeVar('T')


class BaseChain(ABC, Generic[T]):
    """
    Chain 基类
    所有具体 Chain 都应该继承这个类
    """

    def __init__(
        self,
        llm: Optional[Any] = None,
        enable_rag: bool = False,
        rag_service: Optional[Any] = None
    ):
        """
        初始化 Chain

        Args:
            llm: LangChain LLM 实例
            enable_rag: 是否启用 RAG
            rag_service: RAG 服务实例
        """
        self._llm = llm
        self._enable_rag = enable_rag
        self._rag_service = rag_service
        self._chain = None

    def _build_chain(self, system_prompt: str, user_prompt_template: str):
        """
        构建 LangChain

        Args:
            system_prompt: 系统提示词
            user_prompt_template: 用户提示词模板
        """
        if not _langchain_available:
            raise ImportError("LangChain 未安装，无法构建 Chain")

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt_template)
        ])

        self._chain = LLMChain(llm=self._llm, prompt=prompt_template)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 的 JSON 响应
        处理常见的 JSON 格式问题

        Args:
            response: LLM 原始响应

        Returns:
            解析后的字典
        """
        import re

        # 清理响应
        content = response.strip()

        # 提取 JSON（可能被包裹在 markdown 代码块中）
        # 改进：匹配最外层的完整对象
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)

        # 清理 markdown 标记
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content.strip())

        # 替换中文引号
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")

        # 修复常见的 JSON 错误
        content = self._repair_json(content)

        # 尝试修复截断的 JSON
        content = self._fix_truncated_json(content)

        # 解析
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # 如果还是失败，尝试从响应中提取并修复
            print(f"JSON解析失败，尝试修复: {str(e)}")
            print(f"问题JSON内容（前300字符）: {content[:300]}")
            content = self._extract_and_fix_json(response)
            try:
                return json.loads(content)
            except Exception as final_error:
                print(f"JSON最终解析失败，修复后的内容: {content[:500]}")
                raise ValueError(f"JSON 解析失败: {e}\n最终错误: {final_error}\n内容: {content[:500]}")

    def _repair_json(self, json_str: str) -> str:
        """
        修复 JSON 格式错误

        Args:
            json_str: 可能有问题的 JSON 字符串

        Returns:
            修复后的 JSON 字符串
        """
        import re

        original = json_str

        # 移除行内与块级注释
        json_str = re.sub(r'//.*', '', json_str)
        json_str = re.sub(r'/\*[\s\S]*?\*/', '', json_str)

        # 1. 修复单引号属性名（如 {'name': 'value'} -> {"name": "value"}）
        json_str = re.sub(r"({\s*)'([^']+)'(\s*:)", r'\1"\2"\3', json_str)
        json_str = re.sub(r"(,\s*)'([^']+)'(\s*:)", r'\1"\2"\3', json_str)

        # 2. 修复未加引号的属性名（包括中文属性名）
        # 使用更宽松的模式，但避免匹配字符串值中的内容
        # 模式1: { 后跟未加引号的属性名
        # 匹配: { + 可选空白 + 非"非:非空白字符开头 + 任意数量非":字符 + 可选空白 + :
        json_str = re.sub(
            r'({)\s*([^\s":][^":]*)\s*(:)',
            r'\1"\2"\3',
            json_str
        )

        # 模式2: , 后跟未加引号的属性名
        json_str = re.sub(
            r'(,)\s*([^\s":][^":]*)\s*(:)',
            r'\1"\2"\3',
            json_str
        )
        # 将单引号字符串值改为双引号
        json_str = re.sub(r':\s*\'([^\']*)\'', r': "\1"', json_str)
        json_str = re.sub(r'\[\s*\'([^\']*)\'\s*]', r'["\1"]', json_str)
        json_str = re.sub(r'(\s*[,{\[]\s*)\'([^\']*)\'(\s*[,}\]])', r'\1"\2"\3', json_str)

        # 3. 移除尾随逗号
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)

        # 4. 修复缺少逗号的情况
        json_str = re.sub(r'\}\s*\{', '}, {', json_str)
        json_str = re.sub(r'\]\s*\{', '], {', json_str)
        json_str = re.sub(r'\}\s*\[', '}, [', json_str)
        json_str = re.sub(r'"\}\s*\{', '"}, {', json_str)
        json_str = re.sub(r'"\]\s*\{', '"], {', json_str)

        # 调试：如果内容被修改，打印修改前后的对比
        if json_str != original:
            print(f"[JSON修复] 内容已修改")
            print(f"  原始（前100字符）: {original[:100]}")
            print(f"  修复后（前100字符）: {json_str[:100]}")

        return json_str

    def _fix_truncated_json(self, json_str: str) -> str:
        """
        尝试修复被截断的 JSON
        闭合未闭合的括号、引号等

        Args:
            json_str: 可能被截断的 JSON 字符串

        Returns:
            修复后的 JSON 字符串
        """
        import re

        # 先修复基本的格式问题
        json_str = self._repair_json(json_str)

        # 处理字段名被截断的情况（如 "dependenc" 应该是完整的字段）
        # 如果JSON在字段名中间截断，需要移除不完整的字段
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            # 检查是否有未闭合的字符串（引号数量为奇数）
            if line.count('"') % 2 == 1:
                # 字符串未闭合，可能需要修复
                # 如果这一行看起来像是字段值被截断
                if ':' in line and not line.rstrip().endswith('{') and not line.rstrip().endswith('['):
                    # 尝试闭合字符串
                    line = line + '"'

            # 移除明显截断的字段名（只有半个字段名的情况）
            # 检查是否有未完成的字段-值对
            if re.search(r'"\w+\s*:\s*"?\w*$', line.rstrip()):
                # 这一行可能在字段名或值中间截断
                # 如果不是对象或数组开始，且没有结束符，可能是截断
                if not line.rstrip().endswith('{') and not line.rstrip().endswith('[') and not line.rstrip().endswith('}'):
                    # 尝试补全常见的字符串值
                    if ':' in line and not line.rstrip().endswith('"'):
                        line = line + '"'

            cleaned_lines.append(line)

        json_str = '\n'.join(cleaned_lines)

        # 统计括号
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        # 检查是否在字段名后被截断（如 "open_questions":）
        # 这种情况需要添加空值或空数组
        if ':' in json_str and not json_str.rstrip().endswith('}') and not json_str.rstrip().endswith(']'):
            last_line = json_str.split('\n')[-1].strip()
            if last_line.endswith(':'):
                # 字段名后被截断，根据上下文决定添加什么
                if 'open_questions' in last_line or 'questions' in last_line:
                    json_str += ' []'
                elif 'tasks' in last_line or 'milestones' in last_line:
                    json_str += ' []'
                elif 'assumptions' in last_line or 'constraints' in last_line:
                    json_str += ' []'
                elif 'issues' in last_line:
                    json_str += ' []'
                else:
                    json_str += ' null'

        # 闭合缺失的括号（按照正确的顺序：先闭合括号，再闭合大括号）
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)

        return json_str

    def _extract_and_fix_json(self, response: str) -> str:
        """
        从响应中提取 JSON 并尽力修复

        Args:
            response: 原始响应

        Returns:
            修复后的 JSON 字符串
        """
        import re

        # 查找第一个 { 和最后一个 }
        first_brace = response.find('{')
        last_brace = response.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_part = response[first_brace:last_brace + 1]

            # 尝试修复常见问题
            # 1. 移除未闭合的字符串（每行末尾的未闭合引号）
            json_part = re.sub(r'"([^"]*)$', r'"\1"', json_part, flags=re.MULTILINE)

            # 2. 修复截断的字段名（如 "dependenc 后面没有内容）
            # 找到最后一个完整的行
            lines = json_part.split('\n')
            cleaned_lines = []

            for line in lines:
                # 如果这一行有未闭合的对象或数组
                if line.count('"') % 2 == 1:  # 奇数个引号
                    # 尝试闭合
                    line = line + '"'

                # 如果行末有截断的字段值（只有冒号和部分内容）
                # 例如： "severity": "medium", "category": "completeness", "dependenc
                if re.search(r'^\s*"\w+"\s*:\s*"[^"]*$', line.rstrip()):
                    # 这是完整的字段-值对，保留
                    pass
                elif re.search(r'^\s*"\w+"\s*:\s*"[^"]*$', line.rstrip()) is None and re.search(r'"\w*$', line.rstrip()):
                    # 行末有未完成的字段名，移除这一行
                    if not line.rstrip().endswith(',') and not line.rstrip().endswith('}') and not line.rstrip().endswith(']'):
                        # 如果这一行不是有效的结束，可能是截断，尝试完成它
                        if line.count(':') > 0 and '"' in line:
                            # 包含冒号和引号，可能是字段值被截断
                            line = line.rstrip()
                            if not line.endswith('"'):
                                line = line + '"'
                            if not line.endswith(','):
                                line = line + ','

                cleaned_lines.append(line)

            json_part = '\n'.join(cleaned_lines)

            # 3. 处理最后一行可能被截断的情况
            last_line = lines[-1].strip()
            if last_line and not last_line.endswith('}') and not last_line.endswith(']'):
                # 最后一行未完成，可能需要移除
                # 找到上一个完整的对象/数组结束位置
                if json_part.rstrip().endswith(','):
                    # 移除尾随逗号
                    json_part = json_part.rstrip()[:-1]

            return json_part

        return response

    def _enhance_prompt_with_rag(
        self,
        base_prompt: str,
        query: str,
        top_k: int = 3
    ) -> str:
        """
        使用 RAG 增强提示词

        Args:
            base_prompt: 基础提示词
            query: 检索查询
            top_k: 返回前 K 个结果

        Returns:
            增强后的提示词
        """
        if not self._enable_rag or not self._rag_service:
            return base_prompt

        try:
            # 检索相关上下文
            rag_context = self._rag_service.retrieve_context_as_string(
                query=query,
                top_k=top_k
            )

            if rag_context:
                return f"""{base_prompt}

**相关知识库参考**：
{rag_context}

请参考以上最佳实践来完成任务。
"""
        except Exception as e:
            print(f"RAG 增强失败: {e}")

        return base_prompt

    @abstractmethod
    def run(self, *args, **kwargs) -> T:
        """
        执行 Chain

        Returns:
            Chain 的输出结果
        """
        raise NotImplementedError("子类必须实现 run 方法")

    def validate_input(self, **kwargs) -> bool:
        """
        验证输入参数

        Returns:
            是否验证通过
        """
        return True
