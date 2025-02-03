from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class QuizData(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    code: Optional[str] = None
    language: Optional[str] = 'python'

class QuizBase(BaseModel):
    timestamp: int
    quiz_data: QuizData

class QuizCreate(QuizBase):
    lesson_id: int

class QuizResponse(QuizBase):
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.timestamp()
        }