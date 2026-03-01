"""
Prompts 模块
存储各个 Chain 使用的提示词模板
"""

from .decompose_prompts import DECOMPOSE_SYSTEM_PROMPT, DECOMPOSE_USER_PROMPT, build_decompose_prompt
from .clarify_prompts import CLARIFY_SYSTEM_PROMPT, CLARIFY_USER_PROMPT, build_clarify_prompt
from .evaluate_prompts import EVALUATE_SYSTEM_PROMPT, EVALUATE_USER_PROMPT, build_evaluate_prompt
from .router_prompts import ROUTER_SYSTEM_PROMPT, ROUTER_USER_PROMPT, build_router_prompt

__all__ = [
    "DECOMPOSE_SYSTEM_PROMPT",
    "DECOMPOSE_USER_PROMPT",
    "build_decompose_prompt",
    "CLARIFY_SYSTEM_PROMPT",
    "CLARIFY_USER_PROMPT",
    "build_clarify_prompt",
    "EVALUATE_SYSTEM_PROMPT",
    "EVALUATE_USER_PROMPT",
    "build_evaluate_prompt",
    "ROUTER_SYSTEM_PROMPT",
    "ROUTER_USER_PROMPT",
    "build_router_prompt"
]
