from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import os

from app.core.config import settings

try:
    from openai import OpenAI
    _openai_available = True
except Exception:
    _openai_available = False

class AITaskDecomposer:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY and _openai_available:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            self.client = OpenAI()
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    def decompose_task(self, task_description: str, preferences: Optional[Dict] = None) -> Dict:
        prompt = self._build_decomposition_prompt(task_description, preferences)
        if not self.client:
            return self._fallback_decomposition(task_description)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的任务规划专家，擅长将复杂的年度目标分解为可执行的日常任务。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )
            result = response.choices[0].message.content
            return self._parse_decomposition_result(result)
        except Exception:
            return self._fallback_decomposition(task_description)

    def _build_decomposition_prompt(self, task_description: str, preferences: Optional[Dict]) -> str:
        base_prompt = (
            "请将以下年度任务分解为具体执行计划，输出JSON，字段包含year、months、weeks、days。" 
            + f"任务：{task_description}."
        )
        if preferences:
            base_prompt += " 偏好:" + json.dumps(preferences, ensure_ascii=False)
        return base_prompt

    def _parse_decomposition_result(self, ai_response: str) -> Dict:
        try:
            return json.loads(ai_response)
        except Exception:
            return self._create_default_structure()

    def _create_default_structure(self) -> Dict:
        now = datetime.now()
        months = []
        for i in range(12):
            start = now.replace(month=i + 1, day=1)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            months.append({
                "title": f"第{i+1}个月",
                "description": "阶段执行",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "priority": 1,
            })
        return {
            "year": {
                "title": "年度目标",
                "description": "计划制定与执行",
                "milestones": ["计划制定", "阶段执行", "评估总结"],
            },
            "months": months,
            "weeks": [],
            "days": [],
        }

    def _fallback_decomposition(self, task: str) -> Dict:
        now = datetime.now()
        months = []
        for i in range(12):
            start = now.replace(month=i + 1, day=1)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            months.append({
                "title": f"第{i+1}个月",
                "description": f"{task}执行阶段{i+1}",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "priority": 1,
            })
        return {
            "year": {
                "title": task,
                "description": f"完成{task}",
                "milestones": ["计划制定", "阶段执行", "评估总结"],
            },
            "months": months,
            "weeks": [],
            "days": [],
        }
