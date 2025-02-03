from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LessonBase(BaseModel):
    title: str
    content: str = ""
    video_url: Optional[str] = None
    order: int = 0
    has_exercise: bool = False
    has_project: bool = False
    is_published: bool = False
    duration_seconds: Optional[int] = None

class LessonCreate(LessonBase):
    course_id: int

class LessonUpdate(LessonBase):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: Optional[int] = None
    has_exercise: Optional[bool] = None
    has_project: Optional[bool] = None
    is_published: Optional[bool] = None
    duration_seconds: Optional[int] = None

class LessonResponse(LessonBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

