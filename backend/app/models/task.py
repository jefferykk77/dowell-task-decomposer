from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")
    decomposition_result = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="tasks")
    decompositions = relationship("TaskDecomposition", back_populates="task", cascade="all, delete-orphan")

class TaskDecomposition(Base):
    __tablename__ = "task_decompositions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(10), nullable=False)  # year, month, week, day
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    priority = Column(Integer, default=1)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="decompositions")
    daily_tasks = relationship("DailyTask", back_populates="decomposition", cascade="all, delete-orphan")

class DailyTask(Base):
    __tablename__ = "daily_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decomposition_id = Column(UUID(as_uuid=True), ForeignKey("task_decompositions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    task_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    estimated_hours = Column(Integer, default=1)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    decomposition = relationship("TaskDecomposition", back_populates="daily_tasks")