from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional

from app.dependencies import get_current_user_optional
from app.models import Lesson, LessonProgress, Quiz, User
from app.schemas.lesson_progress import QuizResults
from database import get_db

router = APIRouter(prefix="/lesson-progress", tags=["lesson-progress"])

@router.patch("/{lesson_id}")
async def update_lesson_progress(
    lesson_id: int,
    quiz_results: QuizResults,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to update lesson progress"
        )
        
        # Get existing progress
    progress = db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id
        )
    ).scalar_one_or_none()

    if not progress:
        # Create new progress if not exists
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            quiz_completed=0,
            quiz_correct=0,
            completed=False
        )
        db.add(progress)

    # Update quiz results if new score is better
    if quiz_results.quiz_correct > progress.quiz_correct:
        progress.quiz_correct = quiz_results.quiz_correct
    progress.quiz_completed = quiz_results.quiz_completed

    # Get total number of quizzes for the lesson
    total_quizzes = db.execute(
        select(func.count(Quiz.id))
        .where(Quiz.lesson_id == lesson_id)
    ).scalar_one()
        
    COMPLETION_THRESHOLD = 1
    progress.completed = (
        progress.quiz_completed >= total_quizzes and  
        progress.quiz_correct >= total_quizzes * COMPLETION_THRESHOLD  
    )
    progress.updated_at = datetime.now()

    db.commit()
    db.refresh(progress)

    return {
        "quiz_completed": progress.quiz_completed,
        "quiz_correct": progress.quiz_correct,
        "completed": progress.completed
    }

@router.get("/course/{course_id}")
async def get_course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get progress for all lessons in a course"""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to get course progress"
        )
    
    # Get all lessons for the course
    lessons = db.execute(
        select(Lesson).where(Lesson.course_id == course_id)
    ).scalars().all()
    
    # Get progress for all lessons
    progress_dict = {}
    for lesson in lessons:
        progress = db.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == current_user.id,
                LessonProgress.lesson_id == lesson.id
            )
        ).scalar_one_or_none()
        
        if progress:
            progress_dict[lesson.id] = {
                "quiz_completed": progress.quiz_completed,
                "quiz_correct": progress.quiz_correct,
                "completed": progress.completed
            }
        else:
            progress_dict[lesson.id] = {
                "quiz_completed": 0,
                "quiz_correct": 0,
                "completed": False
            }
    
    return progress_dict