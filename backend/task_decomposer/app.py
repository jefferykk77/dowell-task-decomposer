"""
Task Decomposer V2.0
主应用入口 - 提供 FastAPI 和 CLI 接口
"""

import asyncio
import os
import json
from typing import Optional, List, Dict, Any, Callable
from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from task_decomposer.orchestrator import TaskDecomposerOrchestrator
from task_decomposer.schemas import PlanSchema

load_dotenv()


# ==================== 工具函数 ====================

def convert_time_hierarchy_to_frontend_format(time_hierarchy: dict, goal: str) -> dict:
    """
    将后端的嵌套 time_hierarchy 转换为前端期望的扁平格式

    前端期望:
    {
        "year": {...},
        "months": [...],
        "weeks": [...],
        "days": [...]
    }

    后端 time_hierarchy 格式:
    {
        "goal": str,
        "start_date": str,
        "end_date": str,
        "granularity": str,
        "total_days": int,
        "hierarchy": [...]  # 嵌套的层级结构
    }
    """
    months = []
    weeks = []
    days = []

    # 递归提取所有层级的节点
    def extract_nodes(node):
        """递归提取节点到对应层级的列表"""
        node_level = node.get('level')
        children = node.get('children', [])

        # 根据层级添加到对应列表
        if node_level == 'day':
            days.append({
                "title": node.get('title'),
                "description": node.get('description') or node.get('title', ''),
                "task_date": node.get('task_date'),
                "estimated_hours": node.get('estimated_hours', 2),
                "completed": False
            })
        elif node_level == 'week':
            weeks.append({
                "title": node.get('title'),
                "description": node.get('description') or node.get('title', ''),
                "start_date": node.get('start_date'),
                "end_date": node.get('end_date'),
                "priority": 1
            })
        elif node_level == 'month':
            months.append({
                "title": node.get('title'),
                "description": node.get('description') or node.get('title', ''),
                "start_date": node.get('start_date'),
                "end_date": node.get('end_date'),
                "priority": 1
            })
        elif node_level == 'quarter':
            # 季度可能包含 months 子节点
            pass

        # 递归处理子节点
        for child in children:
            extract_nodes(child)

    # 从 hierarchy 中提取所有节点
    for top_node in time_hierarchy.get('hierarchy', []):
        extract_nodes(top_node)

    # 如果 months 为空（当粒度为 MONTH 或更小时），需要生成 months
    if not months and time_hierarchy.get('start_date') and time_hierarchy.get('end_date'):
        try:
            start = datetime.fromisoformat(time_hierarchy['start_date']).date()
            end = datetime.fromisoformat(time_hierarchy['end_date']).date()

            # 按月拆分时间范围
            current = start
            month_index = 0
            while current <= end:
                # 计算月末
                if current.month == 12:
                    month_end = min(end, datetime(current.year, 12, 31).date())
                else:
                    month_end = min(end, (datetime(current.year, current.month + 1, 1).date() - timedelta(days=1)))

                # 查找该月内的所有周，用于生成描述
                month_weeks = [w for w in weeks if w.get('start_date') and w.get('end_date')]
                month_weeks_filtered = []
                for w in month_weeks:
                    try:
                        w_start = datetime.fromisoformat(w['start_date']).date()
                        if w_start.year == current.year and w_start.month == current.month:
                            month_weeks_filtered.append(w)
                    except:
                        pass

                # 生成更具体的描述
                month_title = f"{current.year}年{current.month}月目标"
                if month_weeks_filtered:
                    # 使用该月的周计划来生成描述
                    week_titles = [w.get('title', '') for w in month_weeks_filtered[:3] if w.get('title')]
                    description = f"{current.year}年{current.month}月重点：{'; '.join(week_titles)}"
                elif goal:
                    # 使用用户输入的目标作为描述
                    description = f"推进{goal} - {current.year}年{current.month}月关键任务"
                else:
                    description = f"{current.year}年{current.month}月目标"

                months.append({
                    "title": month_title,
                    "description": description,
                    "start_date": current.isoformat(),
                    "end_date": month_end.isoformat(),
                    "priority": 1
                })

                # 移动到下个月
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1).date()
                else:
                    current = datetime(current.year, current.month + 1, 1).date()
                month_index += 1
        except Exception as e:
            print(f"生成 months 时出错: {e}")

    # 构建 year 对象
    year = {
        "title": goal,
        "description": f"完成{goal}",
        "milestones": ["计划制定", "阶段执行", "评估总结"],
        "start_date": time_hierarchy.get('start_date'),
        "end_date": time_hierarchy.get('end_date')
    }

    return {
        "year": year,
        "months": months,
        "weeks": weeks,
        "days": days
    }


def convert_tasks_to_frontend_format(plan_dict: dict, goal: str) -> dict:
    """
    从AI生成的任务中提取层级信息，转换为前端期望的扁平格式

    优先使用AI生成的层级任务（level字段），如果AI没有生成层级任务则回退到时间层级

    Args:
        plan_dict: PlanSchema 的字典形式，包含 tasks 数组
        goal: 用户目标

    Returns:
        前端期望的扁平格式
    {
        "year": {...},
        "months": [...],
        "weeks": [...],
        "days": [...]
    }
    """
    tasks = plan_dict.get("tasks", [])
    time_hierarchy = plan_dict.get("time_hierarchy")

    # 检查是否有AI生成的层级任务
    has_hierarchical_tasks = any(t.get("level") in ["month", "week", "day"] for t in tasks)

    if has_hierarchical_tasks:
        # 从AI生成的任务中提取层级结构
        months = []
        weeks = []
        days = []

        for task in tasks:
            level = task.get("level")
            task_data = {
                "title": task.get("title", ""),
                "description": task.get("description") or task.get("title", ""),
                "start_date": task.get("start_date"),
                "end_date": task.get("end_date"),
                "task_date": task.get("start_date"),  # 对于日任务使用 start_date
                "estimated_hours": task.get("estimate_hours", 2),
                "priority": 1
            }

            if level == "month":
                months.append(task_data)
            elif level == "week":
                weeks.append(task_data)
            elif level == "day":
                days.append(task_data)
            # 对于没有level的任务，根据工时判断
            elif task.get("estimate_hours", 0) > 20:
                # 工时超过20小时的视为月度任务
                months.append(task_data)
            elif task.get("estimate_hours", 0) > 5:
                # 工时超过5小时的视为周任务
                weeks.append(task_data)
            else:
                # 其他视为日任务
                days.append(task_data)

        # 构建返回数据
        first_task = tasks[0] if tasks else {}
        last_task = tasks[-1] if tasks else {}

        year = {
            "title": goal,
            "description": f"完成{goal}",
            "milestones": [m.get("title", "") for m in plan_dict.get("milestones", [])[:3]],
            "start_date": first_task.get("start_date"),
            "end_date": last_task.get("end_date")
        }

        return {
            "year": year,
            "months": months,
            "weeks": weeks,
            "days": days
        }

    # 如果AI没有生成层级任务，使用时间层级
    elif time_hierarchy:
        return convert_time_hierarchy_to_frontend_format(time_hierarchy, goal)

    # 如果都没有，使用任务的日期范围生成基础结构
    else:
        # 简单的回退：从所有任务中提取日期范围
        return {
            "year": {
                "title": goal,
                "description": f"完成{goal}",
                "milestones": [],
                "start_date": None,
                "end_date": None
            },
            "months": [],
            "weeks": [],
            "days": []
        }



# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Task Decomposer V2.0",
    description="智能任务拆解器 - 基于LangChain的任务规划系统",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局编排器实例
_orchestrator: Optional[TaskDecomposerOrchestrator] = None


def get_orchestrator() -> TaskDecomposerOrchestrator:
    """获取编排器实例（依赖注入）"""
    global _orchestrator
    if _orchestrator is None:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API密钥未配置")

        _orchestrator = TaskDecomposerOrchestrator(
            api_key=api_key,
            api_base=os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
            model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
            enable_rag=os.getenv("ENABLE_RAG", "true").lower() == "true",
            vector_store_path=os.getenv("VECTOR_STORE_PATH", "./data/vector_store"),
            knowledge_base_path=os.getenv("KNOWLEDGE_BASE_PATH", "./data/knowledge_base")
        )

    return _orchestrator


# ==================== API 模型 ====================

class DecomposeRequest(BaseModel):
    """任务拆解请求"""
    goal: str = Field(..., description="用户目标")
    context: Optional[str] = Field(None, description="背景信息")
    constraints: Optional[List[str]] = Field(default_factory=list, description="约束条件")
    user_id: Optional[str] = Field(None, description="用户ID（用于长期记忆）")
    enable_evaluation: bool = Field(default=True, description="是否启用评估")
    include_trace: bool = Field(default=False, description="是否返回拆解过程 trace")

    # 新增：时间相关参数
    start_date: Optional[date] = Field(None, description="开始日期（用于时间粒度判断）")
    end_date: Optional[date] = Field(None, description="结束日期（用于时间粒度判断）")
    work_hours_per_day: float = Field(8.0, description="每天工作小时数")
    work_days_per_week: Optional[List[int]] = Field(default_factory=lambda: [0, 1, 2, 3, 4], description="每周工作日（0=周一, 6=周日）")


class ClarifyRequest(BaseModel):
    """澄清问题请求"""
    goal: str = Field(..., description="用户目标")
    context: Optional[str] = Field(None, description="已有上下文")


class UserPreferenceRequest(BaseModel):
    """用户偏好更新请求"""
    user_id: str = Field(..., description="用户ID")
    preferences: dict = Field(..., description="偏好字典")


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Task Decomposer V2.0 API",
        "version": "2.0.0",
        "features": [
            "智能任务拆解",
            "澄清问题生成",
            "计划质量评估",
            "RAG 知识增强",
            "用户画像记忆"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "task-decomposer-v2"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.post("/api/v2/decompose")
async def decompose_task(request: DecomposeRequest):
    """
    任务拆解接口

    工作流：路由 -> 澄清（可选）-> 拆解 -> 评估（可选）-> 输出
    """
    try:
        orchestrator = get_orchestrator()

        trace: List[Dict[str, Any]] = []
        def on_event(evt: Dict[str, Any]):
            trace.append(evt)

        result = await orchestrator.decompose_task(
            goal=request.goal,
            context=request.context or "",
            constraints=request.constraints,
            user_id=request.user_id,
            enable_evaluation=request.enable_evaluation,
            on_event=on_event if request.include_trace else None,
            start_date=request.start_date,
            end_date=request.end_date,
            work_hours_per_day=request.work_hours_per_day,
            work_days_per_week=request.work_days_per_week
        )

        payload: Dict[str, Any] = dict(result)
        if "plan" in payload and hasattr(payload["plan"], "model_dump"):
            plan_dict = payload["plan"].model_dump()

            # 转换为前端期望的扁平格式（优先使用AI生成的任务）
            plan_dict["time_hierarchy_flat"] = convert_tasks_to_frontend_format(
                plan_dict,
                request.goal
            )

            payload["plan"] = plan_dict
        if "evaluation" in payload and hasattr(payload["evaluation"], "model_dump"):
            payload["evaluation"] = payload["evaluation"].model_dump()
        if "router_result" in payload and hasattr(payload["router_result"], "model_dump"):
            payload["router_result"] = payload["router_result"].model_dump()
        if request.include_trace:
            payload["trace"] = trace
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/decompose/stream")
async def decompose_task_stream(http_request: Request, request: DecomposeRequest):
    orchestrator = get_orchestrator()
    queue: asyncio.Queue = asyncio.Queue()

    def on_event(evt: Dict[str, Any]):
        try:
            queue.put_nowait(evt)
        except Exception:
            return

    def serialize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(result)
        if "plan" in payload and hasattr(payload["plan"], "model_dump"):
            plan_dict = payload["plan"].model_dump()

            # 转换为前端期望的扁平格式（优先使用AI生成的任务）
            plan_dict["time_hierarchy_flat"] = convert_tasks_to_frontend_format(
                plan_dict,
                request.goal
            )

            payload["plan"] = plan_dict
        if "evaluation" in payload and hasattr(payload["evaluation"], "model_dump"):
            payload["evaluation"] = payload["evaluation"].model_dump()
        if "router_result" in payload and hasattr(payload["router_result"], "model_dump"):
            payload["router_result"] = payload["router_result"].model_dump()
        return payload

    async def run_decompose():
        try:
            result = await orchestrator.decompose_task(
                goal=request.goal,
                context=request.context or "",
                constraints=request.constraints,
                user_id=request.user_id,
                enable_evaluation=request.enable_evaluation,
                on_event=on_event,
                start_date=request.start_date,
                end_date=request.end_date,
                work_hours_per_day=request.work_hours_per_day,
                work_days_per_week=request.work_days_per_week
            )
            on_event({"type": "result", "ts": date.today().isoformat(), "data": serialize_result(result)})
        except Exception as e:
            on_event({"type": "error", "ts": date.today().isoformat(), "data": {"error": str(e)}})
        finally:
            try:
                queue.put_nowait(None)
            except Exception:
                return

    task = asyncio.create_task(run_decompose())

    async def event_stream():
        while True:
            if await http_request.is_disconnected():
                task.cancel()
                break
            item = await queue.get()
            if item is None:
                break
            event_type = item.get("type", "message") if isinstance(item, dict) else "message"
            data_str = json.dumps(item, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data_str}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/v2/clarify")
async def clarify_questions(request: ClarifyRequest):
    """
    生成澄清问题

    当信息不足时，生成需要向用户确认的问题
    """
    try:
        orchestrator = get_orchestrator()

        clarify_result = orchestrator._clarify_chain.run(
            goal=request.goal,
            context=request.context or ""
        )

        return clarify_result.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户画像"""
    try:
        orchestrator = get_orchestrator()
        profile = orchestrator.get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="用户不存在")

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/preferences")
async def update_preferences(request: UserPreferenceRequest):
    """更新用户偏好"""
    try:
        orchestrator = get_orchestrator()
        orchestrator.update_user_preferences(
            user_id=request.user_id,
            preferences=request.preferences
        )

        return {"status": "success", "message": "偏好已更新"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/tools")
async def list_tools():
    """列出可用工具"""
    orchestrator = get_orchestrator()
    return {"tools": orchestrator.get_available_tools()}


# ==================== 兼容旧接口 ====================

# 为了保持向后兼容，保留旧的 API 路由
# 这些路由会将请求转换为新格式并调用 V2.0 的编排器


# ==================== CLI 接口 ====================

async def cli_decompose(
    goal: str,
    context: str = "",
    constraints: List[str] = None
):
    """
    CLI 命令行接口

    使用示例：
        python task_decomposer/app.py decompose "开发一个任务管理小程序"
    """
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("错误: 请设置 SILICONFLOW_API_KEY 环境变量")
        return

    orchestrator = TaskDecomposerOrchestrator(
        api_key=api_key,
        api_base=os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
        model=os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3"),
        enable_rag=os.getenv("ENABLE_RAG", "true").lower() == "true"
    )

    print(f"\n{'='*60}")
    print(f"目标: {goal}")
    print(f"{'='*60}\n")

    result = await orchestrator.decompose_task(
        goal=goal,
        context=context,
        constraints=constraints or []
    )

    if result["status"] == "need_clarification":
        print("\n需要澄清以下问题：\n")
        for q in result["questions"]:
            print(f"- {q.get('id')}: {q.get('question')}")
    elif result["status"] == "completed":
        plan = result["plan"]
        print(f"\n{'='*60}")
        print("任务拆解完成！")
        print(f"{'='*60}\n")

        print(f"里程碑: {len(plan.milestones)} 个")
        for m in plan.milestones:
            print(f"  - [{m.id}] {m.title}: {m.description}")

        print(f"\n任务: {len(plan.tasks)} 个")
        for t in plan.tasks[:10]:  # 只显示前10个
            print(f"  - [{t.id}] {t.title} ({t.priority}, {t.estimate_hours}h)")

        if len(plan.tasks) > 10:
            print(f"  ... 还有 {len(plan.tasks) - 10} 个任务")

        if result["evaluation"]:
            eval_result = result["evaluation"]
            print(f"\n质量评分: {eval_result.overall_score}/100")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "decompose":
        # CLI 模式
        if len(sys.argv) < 3:
            print("使用方法: python app.py decompose \"你的目标\"")
            sys.exit(1)

        goal = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""

        asyncio.run(cli_decompose(goal, context))

    else:
        # 启动 FastAPI 服务器
        import uvicorn

        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))

        print(f"\n{'='*60}")
        print("Task Decomposer V2.0")
        print(f"{'='*60}")
        print(f"启动服务器: http://{host}:{port}")
        print(f"API 文档: http://{host}:{port}/docs")
        print(f"{'='*60}\n")

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=os.getenv("DEBUG", "false").lower() == "true"
        )
