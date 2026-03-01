from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.tasks import DecomposeRequest, DecomposeResponse, AssessImpactRequest, AssessImpactResponse
from app.services.decomposer import DecomposerService
import json
from datetime import datetime

router = APIRouter()


@router.post("/decompose", response_model=DecomposeResponse)
async def decompose(req: DecomposeRequest):
    svc = DecomposerService()
    title = req.title or req.goal or "未命名任务"
    
    result = svc.decompose(
        title=title,
        year=req.year,
        start_date=req.start_date,
        end_date=req.end_date,
        hours_per_week=req.hours_per_week or 10,
        work_days=req.work_days or [0, 1, 2, 3, 4],
        strategy=req.strategy or "auto",
        preferences=req.preferences,
        goal_context=req.goal_context.dict() if req.goal_context else None,
        current_context=req.current_context.dict() if req.current_context else None,
        time_context=req.time_context.dict() if req.time_context else None,
        priority_context=req.priority_context.dict() if req.priority_context else None,
        environment_context=req.environment_context.dict() if req.environment_context else None,
        dependency_context=req.dependency_context.dict() if req.dependency_context else None,
    )
    
    return {
        "status": "completed",
        "plan": {
            "goal": title,
            "time_hierarchy_flat": result
        }
    }


@router.post("/decompose/stream")
async def decompose_stream(req: DecomposeRequest):
    async def generate():
        svc = DecomposerService()
        title = req.title or req.goal or "未命名任务"
        
        yield f'data: {json.dumps({"type": "start", "ts": datetime.now().isoformat()})}\n\n'
        
        try:
            result = svc.decompose(
                title=title,
                year=req.year,
                start_date=req.start_date,
                end_date=req.end_date,
                hours_per_week=req.hours_per_week or 10,
                work_days=req.work_days or [0, 1, 2, 3, 4],
                strategy=req.strategy or "auto",
                preferences=req.preferences,
                goal_context=req.goal_context.dict() if req.goal_context else None,
                current_context=req.current_context.dict() if req.current_context else None,
                time_context=req.time_context.dict() if req.time_context else None,
                priority_context=req.priority_context.dict() if req.priority_context else None,
                environment_context=req.environment_context.dict() if req.environment_context else None,
                dependency_context=req.dependency_context.dict() if req.dependency_context else None,
            )
            
            response_data = {
                "status": "completed",
                "plan": {
                    "goal": title,
                    "time_hierarchy_flat": result
                }
            }
            
            yield f'data: {json.dumps({"type": "result", "data": response_data})}\n\n'
            yield f'data: {json.dumps({"type": "completed", "ts": datetime.now().isoformat()})}\n\n'
            
        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "data": {"error": str(e)}})}\n\n'
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/assess-impact", response_model=AssessImpactResponse)
async def assess_impact(req: AssessImpactRequest):
    svc = DecomposerService()
    context = {
        "original_task": req.original_task.dict(),
        "updated_task": req.updated_task.dict(),
        "parent_task": req.parent_task.dict(),
        "change_type": req.change_type
    }
    result = svc.assess_impact(context)
    return result
