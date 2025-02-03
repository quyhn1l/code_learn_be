# app/routers/lessons.py
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.dependencies import get_current_user_optional
from app.schemas.quiz import QuizCreate, QuizData, QuizResponse
from database import get_db
from app.models import Enrollment, Lesson, Course, Quiz, User
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lessons", tags=["lessons"])

@router.post("/course/{course_id}", response_model=LessonResponse)
def create_lesson(
    course_id: int,
    lesson: LessonCreate,
    db: Session = Depends(get_db)
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    new_lesson = Lesson(**lesson.model_dump())
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson

@router.get("/course/{course_id}", response_model=List[LessonResponse])
def get_course_lessons(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    query = select(Lesson).where(
        Lesson.course_id == course_id
    ).order_by(Lesson.order)
    
    lessons = db.execute(query).scalars().all()
    return lessons

@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Check if user is logged in
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="You must be logged in to view lesson details"
        )

    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=404, 
            detail="Lesson not found"
        )

    # Get the course associated with this lesson
    course = db.get(Course, lesson.course_id)
    if not course:
        raise HTTPException(
            status_code=404, 
            detail="Associated course not found"
        )

    # Instructor of the course can view
    if current_user.role == 'instructor' and current_user.id == course.instructor_id:
        return lesson

    # Admin can view
    if current_user.role == 'admin':
        return lesson

    # Check if student is enrolled and approved
    enrollment = db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course.id,
            Enrollment.status.in_(["approved", "studying", "completed"])
        )
    ).scalar_one_or_none()

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled and approved to view this lesson"
        )

    return lesson

@router.patch("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: int,
    lesson_update: LessonUpdate,
    db: Session = Depends(get_db)
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    course = db.get(Course, lesson.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Associated course not found")
    old_duration = lesson.duration_seconds
        
    for key, value in lesson_update.dict(exclude_unset=True).items():
        setattr(lesson, key, value)
    
    if lesson_update.duration_seconds is not None:
        duration_diff = lesson_update.duration_seconds - old_duration
        course.duration_seconds += duration_diff
        db.add(course)
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int, 
    db: Session = Depends(get_db)
):
    """Delete a lesson and all its associated quizzes"""
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    # Get associated course to update duration
    course = db.get(Course, lesson.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Associated course not found")
    
    # Subtract lesson duration from course duration
    course.duration_seconds -= lesson.duration_seconds
    db.add(course)
    
    # Delete associated quizzes first
    quiz_query = select(Quiz).where(Quiz.lesson_id == lesson_id)
    quizzes = db.execute(quiz_query).scalars().all()
    for quiz in quizzes:
        db.delete(quiz)
        
    # Delete the lesson
    db.delete(lesson)
    db.commit()
    return None

@router.get("/{lesson_id}/quizzes", response_model=List[QuizResponse])
def get_lesson_quizzes(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """Get all quizzes for a lesson, ordered by timestamp"""
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    query = select(Quiz).where(
        Quiz.lesson_id == lesson_id
    ).order_by(Quiz.timestamp)
    
    quizzes = db.execute(query).scalars().all()
    
    # Transform quiz_data to match schema
    transformed_quizzes = []
    for quiz in quizzes:
        quiz_dict = {
            "id": quiz.id,
            "lesson_id": quiz.lesson_id,
            "timestamp": quiz.timestamp,
            "created_at": quiz.created_at,
            "updated_at": quiz.updated_at,
            "quiz_data": QuizData(
                question=quiz.quiz_data["question"],
                options=quiz.quiz_data["options"],
                correct_answer=quiz.quiz_data["correct_answer"],
                code=quiz.quiz_data.get("code"),
                language=quiz.quiz_data.get("language")
            )
        }
        transformed_quizzes.append(quiz_dict)
    
    return transformed_quizzes

@router.post("/{lesson_id}/quizzes", response_model=QuizResponse)
def create_quiz(
    lesson_id: int,
    quiz: QuizCreate,
    db: Session = Depends(get_db)
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Thay vì kiểm tra trực tiếp trong dict, ta kiểm tra qua model
    quiz_data = quiz.quiz_data
    if not quiz_data.question or not quiz_data.options or quiz_data.correct_answer is None:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields in quiz_data"
        )
    
    # Kiểm tra quiz trùng timestamp
    existing_quiz = db.execute(
        select(Quiz).where(
            Quiz.lesson_id == lesson_id,
            Quiz.timestamp == quiz.timestamp
        )
    ).first()
    
    if existing_quiz:
        raise HTTPException(
            status_code=400,
            detail=f"A quiz already exists at timestamp {quiz.timestamp}"
        )
    
    new_quiz = Quiz(
        lesson_id=quiz.lesson_id,
        timestamp=quiz.timestamp,
        quiz_data=quiz_data.dict()  # Chuyển từ Pydantic model sang dict
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    return new_quiz

@router.patch("/quizzes/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: int,
    quiz: QuizCreate,
    db: Session = Depends(get_db)
):
    """Update an existing quiz"""
    db_quiz = db.get(Quiz, quiz_id)
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Update fields
    if quiz.timestamp is not None:
        db_quiz.timestamp = quiz.timestamp
    if quiz.quiz_data is not None:
        db_quiz.quiz_data = quiz.quiz_data
    
    db_quiz.updated_at = datetime.now()
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db)
):
    """Delete a quiz"""
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    db.delete(quiz)
    db.commit()
    return None