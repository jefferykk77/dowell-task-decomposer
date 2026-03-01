from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

from app.api import tasks, auth
from app.core.config import settings
from app.core.auth import get_current_user

load_dotenv()


app = FastAPI(
    title="AI任务分解器",
    description="智能任务分解和管理系统",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全中间件
security = HTTPBearer()

# 路由注册
app.include_router(auth.router, prefix="/api/v2/auth", tags=["认证"])
app.include_router(tasks.router, prefix="/api/v2", tags=["任务"])   
@app.get("/")
async def root():
    return {"message": "AI任务分解器API服务", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-task-decomposer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
