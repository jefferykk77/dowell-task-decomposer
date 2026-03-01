"""
任务分解服务 - 使用 LangChain 框架和 2-Step RAG
"""
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List
import calendar
import os
import json

from app.core.config import settings
from app.services.rag_service import get_rag_service, initialize_default_knowledge_base

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.chains import LLMChain
    _langchain_available = True
except ImportError:
    _langchain_available = False


class DecomposerService:
    """任务分解服务 - 使用 LangChain 和 RAG"""

    def __init__(self):
        self._llm = None
        self._rag_enabled = settings.ENABLE_RAG
        self._rag_service = None

        # 初始化 LLM
        if settings.SILICONFLOW_API_KEY and _langchain_available:
            try:
                self._llm = ChatOpenAI(
                    model=settings.SILICONFLOW_MODEL or "deepseek-ai/DeepSeek-V3",
                    openai_api_key=settings.SILICONFLOW_API_KEY,
                    openai_api_base="https://api.siliconflow.cn/v1",
                    temperature=0.3,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    model_kwargs={
                        "top_p": 0.9,
                    }
                )
                print(f"LangChain LLM 初始化成功: {settings.SILICONFLOW_MODEL}")
            except Exception as e:
                print(f"LangChain LLM 初始化失败: {e}")

        # 初始化 RAG 服务
        if self._rag_enabled:
            try:
                self._rag_service = get_rag_service()
                if self._rag_service and self._rag_service.initialized:
                    # 尝试加载已有的向量存储
                    vector_path = settings.VECTOR_STORE_PATH
                    if os.path.exists(vector_path):
                        loaded = self._rag_service.load_vector_store(vector_path)
                        if not loaded:
                            # 加载失败，创建默认知识库
                            initialize_default_knowledge_base()
                    else:
                        # 不存在，创建默认知识库
                        initialize_default_knowledge_base()
                    print("RAG 服务初始化成功")
                else:
                    print("RAG 服务初始化失败，将不使用 RAG 功能")
                    self._rag_enabled = False
            except Exception as e:
                print(f"RAG 服务初始化异常: {e}")
                self._rag_enabled = False

    def decompose(
        self,
        title: str,
        year: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        hours_per_week: int,
        work_days: List[int],
        strategy: str,
        preferences: Optional[Dict[str, Any]],
        goal_context: Optional[Dict] = None,
        current_context: Optional[Dict] = None,
        time_context: Optional[Dict] = None,
        priority_context: Optional[Dict] = None,
        environment_context: Optional[Dict] = None,
        dependency_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        任务分解主入口 - 实现 2-Step RAG
        Step 1: 使用 RAG 检索相关上下文
        Step 2: 基于检索到的上下文进行任务拆解
        """
        base_start, base_end = self._resolve_range(year, start_date, end_date)

        # 如果启用 AI 且 LLM 可用
        if strategy == "ai" and self._llm:
            try:
                return self._ai_decompose_with_rag(
                    title, base_start, base_end, preferences,
                    goal_context, current_context, time_context,
                    priority_context, environment_context, dependency_context
                )
            except Exception as e:
                print(f"AI 分解失败: {e}")
                import traceback
                traceback.print_exc()

        # 回退到规则分解
        return self._rule_decompose(title, base_start, base_end, hours_per_week, work_days)

    def _ai_decompose_with_rag(
        self,
        title: str,
        start: datetime,
        end: datetime,
        preferences: Optional[Dict[str, Any]],
        goal_context: Optional[Dict] = None,
        current_context: Optional[Dict] = None,
        time_context: Optional[Dict] = None,
        priority_context: Optional[Dict] = None,
        environment_context: Optional[Dict] = None,
        dependency_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        使用 LangChain 和 2-Step RAG 进行任务分解

        Step 1: RAG 检索
        - 基于任务标题和上下文检索相关知识
        - 构建增强的 prompt

        Step 2: LLM 生成
        - 使用 LangChain Chain 调用 LLM
        - 解析并返回结构化结果
        """
        # Step 1: RAG 检索相关上下文
        rag_context = ""
        if self._rag_enabled and self._rag_service:
            try:
                # 构建检索查询
                query = self._build_rag_query(title, goal_context, current_context)
                print(f"RAG 查询: {query}")

                # 检索相关上下文
                rag_context = self._rag_service.retrieve_context_as_string(
                    query=query,
                    top_k=settings.RAG_TOP_K,
                    score_threshold=settings.RAG_SCORE_THRESHOLD
                )

                if rag_context:
                    print(f"RAG 检索到 {len(rag_context)} 字符的相关上下文")
                else:
                    print("RAG 未检索到相关上下文")
            except Exception as e:
                print(f"RAG 检索失败: {e}")

        # Step 2: 构建增强的 Prompt（包含 RAG 上下文）
        prompt = self._build_enhanced_prompt(
            title, start, end, preferences,
            goal_context, current_context, time_context,
            priority_context, environment_context, dependency_context,
            rag_context
        )

        # Step 3: 使用 LangChain 调用 LLM
        try:
            # 创建 LangChain prompt template
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "你是一个专业项目经理，擅长将年度目标拆解为可执行的月、周、日计划。请直接返回纯 JSON 格式数据，不要包含任何 Markdown 格式（如 ```json ... ```）。确保所有属性名都使用双引号。"),
                ("human", "{input}")
            ])

            # 创建简单的 chain
            if _langchain_available:
                chain = LLMChain(llm=self._llm, prompt=prompt_template)
                response = chain.run(input=prompt)
            else:
                # 回退到直接调用
                response = self._llm.invoke(prompt).content

            print(f"AI Raw Response: {response}")

            # 解析响应
            data = self._parse_ai_response(response)

            # 标准化数据
            normalized_data = self._normalize_ai_response(data, start, end)

            # 应用调度约束
            self._apply_scheduling_constraints(normalized_data, time_context)

            return normalized_data

        except Exception as e:
            print(f"LangChain 调用失败: {e}")
            raise

    def _build_rag_query(
        self,
        title: str,
        goal_context: Optional[Dict] = None,
        current_context: Optional[Dict] = None
    ) -> str:
        """构建 RAG 检索查询"""
        query_parts = [title]

        if goal_context:
            if goal_context.get('long_term_goal'):
                query_parts.append(goal_context['long_term_goal'])
            if goal_context.get('completion_criteria'):
                query_parts.append(goal_context['completion_criteria'])

        if current_context:
            if current_context.get('current_progress'):
                query_parts.append(current_context['current_progress'])

        return " ".join(query_parts)

    def _build_enhanced_prompt(
        self,
        title: str,
        start: datetime,
        end: datetime,
        preferences: Optional[Dict[str, Any]],
        goal_context: Optional[Dict] = None,
        current_context: Optional[Dict] = None,
        time_context: Optional[Dict] = None,
        priority_context: Optional[Dict] = None,
        environment_context: Optional[Dict] = None,
        dependency_context: Optional[Dict] = None,
        rag_context: str = ""
    ) -> str:
        """构建增强的 Prompt（包含 RAG 上下文）"""
        delta = end - start
        duration_days = delta.days + 1

        if duration_days <= 7:
            structure_req = "`year` (作为根节点), `days`"
            ignore_req = "不需要生成 `months` 和 `weeks`。"
        elif duration_days <= 30:
            structure_req = "`year` (作为根节点), `weeks`, `days`"
            ignore_req = "不需要生成 `months`。"
        else:
            structure_req = "`year`, `months`, `weeks`, `days`"
            ignore_req = ""

        start_weekday = start.strftime("%A")
        calendar_context = f"**日历参考**: {start.date().isoformat()} 是 {start_weekday}。"

        prompt = f"""任务：{title}
起止时间：{start.date().isoformat()} 至 {end.date().isoformat()} (共 {duration_days} 天)
{calendar_context}

请作为一位经验丰富的项目经理，为我拆解上述任务。请拒绝使用模版化的语言（如"阶段一"、"准备工作"），而是根据任务的具体内容，生成切实可行的、具体的行动步骤。

要求：
1. **结构扁平化**：JSON 根对象必须包含 {structure_req}。{ignore_req}不要将 weeks 嵌套在 months 中，也不要将 days 嵌套在 weeks 中。
2. **字段规范**：
   - `year`: {{ "title": str, "description": str, "milestones": [str], "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}
   - `months`: [ {{ "title": "具体月份主题", "description": "具体的月度目标", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "priority": int }} ]
   - `weeks`: [ {{ "title": "具体周主题", "description": "本周核心交付物", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "priority": int }} ]
   - `days`: [ {{ "title": "具体行动", "description": "可执行的操作细节", "task_date": "YYYY-MM-DD", "estimated_hours": int, "completed": false }} ]
3. **内容逻辑**：
   - 必须覆盖从起始日期到结束日期的整个周期。
   - `days`: 对于短期任务（<14天），请生成每一天的具体任务；对于长期任务，请务必生成前两周的每日详细任务作为示例。
   - **严格遵守用户的时间可用性**：如果用户在【时间与节奏】中指定了"只有周末有空"，则 `days` 中的任务日期必须落在周六或周日。
   - **任务数量与密度**：如果用户选择了"高密度"或"多"，请务必在同一天内生成多个细分任务（例如：上午做A，下午做B），而不仅仅是每天一个任务。
   - 任务描述要具体、可落地。
   - 确保所有日期格式均为 YYYY-MM-DD。
4. **语言**：全中文。

输出为严格的 JSON 格式。

示例结构：
{{
  "year": {{...}},
  "months": [ {{...}}, {{...}} ],
  "weeks": [ {{...}}, {{...}} ],
  "days": [ {{...}}, {{...}} ]
}}
"""

        # 添加 RAG 检索到的上下文（2-Step RAG 的核心）
        if rag_context:
            prompt = f"""{prompt}

{rag_context}

请参考以上相关知识库中的最佳实践来制定任务拆解方案。
"""

        # 添加用户提供的上下文
        context_str = ""
        if goal_context:
            context_str += "\n\n**1. 目标与验收 (Goal Context)**\n"
            if goal_context.get('long_term_goal'):
                context_str += f"- 长期目标: {goal_context['long_term_goal']}\n"
            if goal_context.get('completion_criteria'):
                context_str += f"- 完成标准/证据: {goal_context['completion_criteria']}\n"
            if goal_context.get('deadline_type'):
                context_str += f"- 目标期限: {goal_context['deadline_type']}\n"
            if goal_context.get('scope_boundaries'):
                context_str += f"- 范围边界(不做什么): {goal_context['scope_boundaries']}\n"

        if current_context:
            context_str += "\n**2. 当前起点 (Current Context)**\n"
            if current_context.get('current_progress'):
                context_str += f"- 当前水平/进度: {current_context['current_progress']}\n"
            if current_context.get('existing_resources'):
                context_str += f"- 已有资源: {current_context['existing_resources']}\n"

        if time_context:
            context_str += "\n**3. 时间与节奏 (Time Context)**\n"
            if time_context.get('weekly_hours'):
                context_str += f"- 每周可投入总时长: {time_context['weekly_hours']}小时\n"
            if time_context.get('available_slots'):
                context_str += f"- 可用时段: {time_context['available_slots']}\n"
            if time_context.get('min_viable_effort'):
                context_str += f"- 最低保底投入: {time_context['min_viable_effort']}\n"

        if priority_context:
            context_str += "\n**4. 优先级取舍 (Priority Context)**\n"
            if priority_context.get('trade_off'):
                context_str += f"- 更看重: {priority_context['trade_off']}\n"
            if priority_context.get('task_density'):
                context_str += f"- 每日任务密度偏好: {priority_context['task_density']}\n"

        if environment_context:
            context_str += "\n**5. 任务环境与厌恶项 (Environment Context)**\n"
            if environment_context.get('environment'):
                context_str += f"- 任务环境: {environment_context['environment']}\n"
            if environment_context.get('aversion'):
                context_str += f"- 最容易拖延的类型: {environment_context['aversion']}\n"

        if dependency_context:
            context_str += "\n**6. 依赖与阻塞 (Dependency Context)**\n"
            if dependency_context.get('coordination'):
                context_str += f"- 需要谁配合/审批: {dependency_context['coordination']}\n"
            if dependency_context.get('resources'):
                context_str += f"- 需要的权限/材料/预算: {dependency_context['resources']}\n"
            if dependency_context.get('risks'):
                context_str += f"- 不可控风险: {dependency_context['risks']}\n"

        if context_str:
            prompt += context_str
            prompt += "\n\n**关键指令**：请务必根据上述所有上下文（包括知识库最佳实践、目标、起点、时间、优先级、环境、依赖）来定制拆解计划。"

        if preferences:
            prompt += f"\n用户其他偏好：{preferences}"

        return prompt

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应"""
        import re

        # 清理响应
        content = response.strip()

        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)

        # 尝试解析
        try:
            return json.loads(content)
        except json.JSONDecodeError as je:
            print(f"JSON 解析失败: {je}")
            # 尝试修复
            content = self._repair_json(content)
            try:
                return json.loads(content)
            except json.JSONDecodeError as je2:
                print(f"JSON 修复失败: {je2}")
                raise

    def _repair_json(self, json_str: str) -> str:
        """修复 JSON 格式错误"""
        import re

        # 清理 markdown 代码块
        json_str = re.sub(r'^```json\s*', '', json_str.strip())
        json_str = re.sub(r'\s*```$', '', json_str.strip())

        # 替换中文引号
        json_str = json_str.replace('"', '"').replace('"', '"')
        json_str = json_str.replace(''', "'").replace(''', "'")
        json_str = json_str.replace('：', ':')

        # 修复缺少逗号
        json_str = re.sub(r'\}\s*\{', '}, {', json_str)
        json_str = re.sub(r'\]\s*\[', '], [', json_str)
        json_str = re.sub(r'\}\s*"', '}, "', json_str)
        json_str = re.sub(r'\]\s*"', '], "', json_str)

        # 移除尾随逗号
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)

        return json_str

    def _normalize_ai_response(self, data: Dict[str, Any], default_start: datetime, default_end: datetime) -> Dict[str, Any]:
        """标准化 AI 响应数据"""
        normalized = {
            "year": {},
            "months": [],
            "weeks": [],
            "days": []
        }

        # 处理 Year
        if "year" in data:
            normalized["year"] = data["year"]
            for key in ["months", "weeks", "days"]:
                if key in normalized["year"]:
                    del normalized["year"][key]

        # 递归提取
        def extract_items(items, target_list_name, child_list_name):
            extracted = []
            for item in items:
                new_item = item.copy()
                children = new_item.pop(child_list_name, [])

                if "start_date" not in new_item:
                    new_item["start_date"] = default_start.date().isoformat()
                if "end_date" not in new_item and target_list_name != "days":
                    new_item["end_date"] = default_end.date().isoformat()

                if target_list_name == "days":
                    if "task_date" not in new_item:
                        new_item["task_date"] = new_item.get("start_date", default_start.date().isoformat())
                    if "completed" not in new_item:
                        new_item["completed"] = False
                    if "estimated_hours" not in new_item:
                        new_item["estimated_hours"] = 2

                extracted.append(new_item)

                if children:
                    if child_list_name == "weeks":
                        normalized["weeks"].extend(extract_items(children, "weeks", "days"))
                    elif child_list_name == "days":
                        normalized["days"].extend(extract_items(children, "days", ""))
            return extracted

        raw_months = data.get("months", [])
        if not raw_months and "months" in data.get("year", {}):
            raw_months = data["year"]["months"]

        normalized["months"] = extract_items(raw_months, "months", "weeks")

        if "weeks" in data:
            normalized["weeks"].extend(extract_items(data["weeks"], "weeks", "days"))

        if "days" in data:
            normalized["days"].extend(extract_items(data["days"], "days", ""))

        if "start_date" not in normalized["year"]:
            normalized["year"]["start_date"] = default_start.date().isoformat()
        if "end_date" not in normalized["year"]:
            normalized["year"]["end_date"] = default_end.date().isoformat()

        return normalized

    def _apply_scheduling_constraints(self, data: Dict[str, Any], time_context: Optional[Dict]) -> None:
        """应用时间约束"""
        if not time_context:
            return

        available_slots = str(time_context.get('available_slots', '')).lower()
        print(f"DEBUG: Checking constraints for available_slots='{available_slots}'")

        has_weekend_keyword = any(k in available_slots for k in ['weekend', '周末', '周六日', '六日'])
        has_weekday_keyword = any(k in available_slots for k in ['weekday', '工作日', '一至五', '1-5'])

        if has_weekend_keyword and not has_weekday_keyword:
            print("Applying STRICT WEEKEND constraint...")
            days = data.get('days', [])
            for task in days:
                task_date_str = task.get('task_date')
                if not task_date_str:
                    continue

                try:
                    current_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
                    if current_date.weekday() < 5:  # 周一到周五
                        days_until_saturday = 5 - current_date.weekday()
                        new_date = current_date + timedelta(days=days_until_saturday)

                        print(f"Rescheduling task '{task.get('title')}' from {current_date} (Weekday) to {new_date} (Saturday)")
                        task['task_date'] = new_date.isoformat()
                except ValueError:
                    pass

    def assess_impact(self, change_context: Dict[str, Any]) -> Dict[str, Any]:
        """评估任务影响（保持原有逻辑）"""
        if not self._llm:
            return {
                "impact_level": "unknown",
                "suggestion": "AI 服务不可用，无法评估影响。",
                "parent_adjustment_needed": False
            }

        # 使用 LangChain
        try:
            prompt = self._build_impact_prompt(change_context)

            if _langchain_available:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是一个敏锐的项目经理，擅长评估项目进度风险。请以 JSON 格式返回评估结果，不要包含 Markdown 标记。确保属性名为双引号。"),
                    ("human", "{input}")
                ])
                chain = LLMChain(llm=self._llm, prompt=prompt_template)
                response = chain.run(input=prompt)
            else:
                response = self._llm.invoke(prompt).content

            # 解析响应
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                response = json_match.group(0)

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                response = self._repair_json(response)
                return json.loads(response)

        except Exception as e:
            print(f"Impact Assessment Error: {e}")
            return {
                "impact_level": "unknown",
                "suggestion": "AI 评估服务暂时不可用。",
                "parent_adjustment_needed": False
            }

    def _build_impact_prompt(self, ctx: Dict[str, Any]) -> str:
        """构建影响评估 Prompt"""
        orig = ctx.get("original_task", {})
        curr = ctx.get("updated_task", {})
        parent = ctx.get("parent_task", {})

        return f"""
下级任务发生了时间变动，请评估对上级任务的影响。

**上级任务**：
- 标题：{parent.get('title', 'Unknown')}
- 描述：{parent.get('description', '')}
- 原计划：{parent.get('start_date')} 至 {parent.get('end_date')}

**变动任务（子任务）**：
- 标题：{curr.get('title', 'Unknown')}
- 原计划：{orig.get('start_date')} 至 {orig.get('end_date')}
- 新计划：{curr.get('start_date')} 至 {curr.get('end_date')}

请分析：
1. 子任务的新结束时间是否超过了上级任务的结束时间？
2. 这种变动是否会导致上级任务的目标无法按时完成？
3. 给出具体的调整建议（如"建议延长上级任务时间"或"建议压缩后续子任务时间"）。

请返回如下 JSON 格式：
{{
  "impact_level": "none" | "low" | "medium" | "high" | "critical",
  "parent_adjustment_needed": boolean,
  "suggestion": "给用户的简短建议（中文，不超过50字）",
  "recommended_parent_end_date": "YYYY-MM-DD" (仅在需要调整时提供，否则为 null)
}}
"""

    def _resolve_range(self, year: Optional[int], start_date: Optional[date], end_date: Optional[date]) -> (datetime, datetime):
        """解析时间范围"""
        now = datetime.now()
        start = datetime.combine(start_date or now.date(), datetime.min.time())

        if end_date:
            end = datetime.combine(end_date, datetime.max.time())
        elif year:
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
        else:
            end = datetime(now.year, 12, 31)

        if end < start:
            end = start + timedelta(days=1)

        return start, end

    def _rule_decompose(self, title: str, start: datetime, end: datetime, hours_per_week: int, work_days: List[int]) -> Dict[str, Any]:
        """规则分解（保持原有逻辑）"""
        months = []
        weeks = []
        days = []

        delta = end - start
        duration_days = delta.days + 1

        need_months = duration_days > 30
        need_weeks = duration_days > 7

        current = datetime(start.year, start.month, 1)
        while current <= end:
            next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = min(next_month - timedelta(days=1), end)

            month_real_start = max(current, start)
            if need_months and month_real_start <= month_end:
                months.append({
                    "title": f"第{current.month}个月",
                    "description": f"{title}执行阶段{current.month}",
                    "start_date": month_real_start.date().isoformat(),
                    "end_date": month_end.date().isoformat(),
                    "priority": 1
                })

            week_start = current
            while week_start <= month_end:
                week_end = min(week_start + timedelta(days=6), month_end)

                week_real_start = max(week_start, start)
                if need_weeks and week_real_start <= week_end:
                    iso_week = week_start.isocalendar()[1]
                    weeks.append({
                        "title": f"第{iso_week}周",
                        "description": f"{title}周计划",
                        "start_date": week_real_start.date().isoformat(),
                        "end_date": week_end.date().isoformat(),
                        "priority": 1
                    })

                allocated_hours = 0
                day_cursor = week_start
                while day_cursor <= week_end and allocated_hours < hours_per_week:
                    if day_cursor >= start and day_cursor <= end:
                        if day_cursor.weekday() in work_days:
                            remaining = hours_per_week - allocated_hours
                            day_hours = min(remaining, 2)
                            days.append({
                                "title": f"{title}每日任务",
                                "description": f"专注执行{title}",
                                "task_date": day_cursor.date().isoformat(),
                                "estimated_hours": day_hours,
                                "completed": False
                            })
                            allocated_hours += day_hours
                    day_cursor += timedelta(days=1)

                week_start = week_end + timedelta(days=1)
            current = next_month

        return {
            "year": {
                "title": title,
                "description": f"完成{title}",
                "milestones": ["计划制定", "阶段执行", "评估总结"],
                "start_date": start.date().isoformat(),
                "end_date": end.date().isoformat(),
            },
            "months": months,
            "weeks": weeks,
            "days": days,
        }
