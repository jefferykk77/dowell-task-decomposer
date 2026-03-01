from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

class GoalContext(BaseModel):
    long_term_goal: Optional[str] = None
    completion_criteria: Optional[str] = None
    deadline_type: Optional[str] = None  # "hard" | "soft"
    scope_boundaries: Optional[str] = None

class CurrentContext(BaseModel):
    current_progress: Optional[str] = None
    existing_resources: Optional[str] = None

class TimeContext(BaseModel):
    weekly_hours: Optional[int] = None
    available_slots: Optional[str] = None
    min_viable_effort: Optional[str] = None

class PriorityContext(BaseModel):
    trade_off: Optional[str] = None  # "speed" | "quality" | "sustainable"
    task_density: Optional[str] = None  # "low" | "medium" | "high"

class EnvironmentContext(BaseModel):
    environment: Optional[str] = None
    aversion: Optional[str] = None

class DependencyContext(BaseModel):
    coordination: Optional[str] = None
    resources: Optional[str] = None
    risks: Optional[str] = None

class DecomposeRequest(BaseModel):
    # 同时支持 title 和 goal
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    goal: Optional[str] = Field(None, min_length=1, max_length=255)

    year: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[int] = 10
    work_days: Optional[List[int]] = [0, 1, 2, 3, 4]
    strategy: Optional[str] = "auto"
    preferences: Optional[Dict[str, Any]] = None

    # 前端发来的字段
    context: Optional[str] = None
    constraints: Optional[List[str]] = None
    include_trace: Optional[bool] = False

    # 原有的详细context
    goal_context: Optional[GoalContext] = None
    current_context: Optional[CurrentContext] = None
    time_context: Optional[TimeContext] = None
    priority_context: Optional[PriorityContext] = None
    environment_context: Optional[EnvironmentContext] = None
    dependency_context: Optional[DependencyContext] = None
class TimeRange(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DecomposeResponse(BaseModel):
    year: Dict[str, Any]
    months: List[Dict[str, Any]]
    weeks: List[Dict[str, Any]]
    days: List[Dict[str, Any]]

class TaskInfo(BaseModel):
    title: str
    start_date: str
    end_date: str
    description: Optional[str] = None

class AssessImpactRequest(BaseModel):
    original_task: TaskInfo
    updated_task: TaskInfo
    parent_task: TaskInfo
    change_type: str = "resize" # resize, move, etc.

class AssessImpactResponse(BaseModel):
    impact_level: str
    parent_adjustment_needed: bool
    suggestion: str
    recommended_parent_end_date: Optional[str] = None
