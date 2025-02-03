from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CourseBase(BaseModel):
    title: str
    description: str
    category: str
    level: str
    price: float
    duration_seconds: int = 0


class CourseCreate(CourseBase):
    instructor_id: int

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    duration_seconds: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    slug: str
    instructor_id: int
    status: str
    enrolled_count: int
    rating: float
    created_at: datetime

class StudentCourseResponse(CourseResponse):
    enrollment_status: str
    enrollment_progress: float = 0.0
    
    class Config:
        from_attributes = True