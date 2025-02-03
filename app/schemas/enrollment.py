from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
class StudentInfo(BaseModel):
    id: int
    email: Optional[str]
    username: str
    model_config = ConfigDict(from_attributes=True)

class EnrollmentStatus(str, Enum):
    PENDING = "pending"     # Chờ phê duyệt
    APPROVED = "approved"   # Đã được duyệt, có thể học
    STUDYING = "studying"   # Đang học
    COMPLETED = "completed" # Đã hoàn thành
    DROPPED = "dropped"     # Đã hủy

class EnrollmentBase(BaseModel):
    course_id: int = Field(gt=0, description="Course ID must be positive")
    student_id: int = Field(gt=0, description="Student ID must be positive")

class EnrollmentCreate(EnrollmentBase):
    model_config = ConfigDict(str_strip_whitespace=True)

class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None
    progress: Optional[float] = None
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v
    
    model_config = ConfigDict(str_strip_whitespace=True)

class EnrollmentResponse(EnrollmentBase):
    id: int
    status: EnrollmentStatus
    progress: float = Field(ge=0, le=100)
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime
    certificate_issued: bool
    certificate_url: Optional[str] = None
    student: Optional[StudentInfo] = None  # Thêm trường student

    model_config = ConfigDict(from_attributes=True)

class ProgressUpdate(BaseModel):
    lesson_id: int = Field(gt=0)
    watched_duration: int = Field(ge=0, description="Duration in seconds")
    completed: bool = False

    model_config = ConfigDict(str_strip_whitespace=True)

class CourseRating(BaseModel):
    rating: float = Field(ge=0, le=5, description="Rating must be between 0 and 5")
    comment: Optional[str] = None

    @field_validator('rating')
    @classmethod
    def round_rating(cls, v: float) -> float:
        return round(v, 1)

    model_config = ConfigDict(str_strip_whitespace=True)

class EnrollmentStats(BaseModel):
    total_lessons: int = Field(ge=0)
    completed_lessons: int = Field(ge=0)
    total_duration: int = Field(ge=0, description="Duration in minutes")
    watched_duration: int = Field(ge=0, description="Duration in minutes")
    completion_percentage: float = Field(ge=0, le=100)

    @field_validator('completion_percentage')
    @classmethod
    def round_percentage(cls, v: float) -> float:
        return round(v, 2)

    model_config = ConfigDict(str_strip_whitespace=True)