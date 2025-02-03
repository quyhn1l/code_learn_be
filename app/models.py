from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB



class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, sa_type=String)
    username: str = Field(min_length=3, max_length=50, sa_type=String(50))
    password_hash: str = Field(sa_type=String)
    role: str = Field(default="student", sa_type=String)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Course(SQLModel, table=True):
    __tablename__ = "courses"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=3, max_length=100, sa_type=String(100))
    slug: str = Field(sa_type=String)  
    description: str = Field(default="", sa_type=String)
    instructor_id: Optional[int] = Field(default=None)
    category: str = Field(sa_type=String)  
    level: str = Field(sa_type=String)  
    duration_seconds: int = Field(default=0)  
    status: str = Field(default="draft", sa_type=String)
    price: float = Field(default=0.0)
    rating: float = Field(default=0.0)
    enrolled_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=3, max_length=100, sa_type=String(100))
    content: str = Field(default="", sa_type=String)
    video_url: str = Field(sa_type=String, nullable=True)  
    order: int = Field(default=0)
    course_id: int = Field(default=None)
    duration_seconds: int = Field(default=0)
    is_published: bool = Field(default=False)
    has_exercise: bool = Field(default=False)
    has_project: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Quiz(SQLModel, table=True):
    __tablename__ = "quizzes"
    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(default=None)
    timestamp: int = Field(...)  # Thời điểm hiển thị trong video (giây)
    quiz_data: dict = Field(
        sa_column=Column(JSONB),
        description={
            "question": "Quiz question text",  
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Index of correct option (0-based)",
            "code": "Code snippet to show (optional)"
        }
    )
    created_at: datetime = Field(default_factory=datetime.now) 
    updated_at: datetime = Field(default_factory=datetime.now)

class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(default=None)
    course_id: int = Field(default=None)
    status: str = Field(default="active", sa_type=String)
    progress: float = Field(default=0.0)
    enrolled_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime = Field(default_factory=datetime.now)
    certificate_issued: bool = Field(default=False) 
    certificate_url: Optional[str] = Field(default=None, sa_type=String) 
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class LessonProgress(SQLModel, table=True):
    __tablename__ = "lesson_progress"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=None)
    lesson_id: int = Field(default=None)
    quiz_completed: int = Field(default=0)    # Số quiz đã làm
    quiz_correct: int = Field(default=0)      # Số quiz đúng
    completed: bool = Field(default=False)    # Đã hoàn thành chưa
    updated_at: datetime = Field(default_factory=datetime.now)
