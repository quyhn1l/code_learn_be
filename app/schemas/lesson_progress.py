# schemas/lesson_progress.py
from pydantic import BaseModel, Field

class QuizResults(BaseModel):
    quiz_completed: int = Field(ge=0, description="Total number of completed quizzes")
    quiz_correct: int = Field(ge=0, description="Number of correctly answered quizzes")