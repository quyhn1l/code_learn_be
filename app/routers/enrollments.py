from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from database import get_db
from app.models import Course, Enrollment, User
from ..schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    CourseRating
)

router = APIRouter(
    prefix="/enrollments",
    tags=["enrollments"]
)

@router.post("/{course_id}", response_model=EnrollmentResponse)
def create_enrollment(
    course_id: int,
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db)
):
    if course_id != enrollment_data.course_id:
        raise HTTPException(
            status_code=400,
            detail="Course ID in path must match course_id in request body"
        )

    student = db.get(User, enrollment_data.student_id)
    if not student or student.role != "student":
        raise HTTPException(status_code=404, detail="Student not found")

    course = db.get(Course, course_id)
    if not course or course.status != "published":
        raise HTTPException(status_code=404, detail="Course not available")

    existing = db.execute(
        select(Enrollment).where(
            Enrollment.student_id == enrollment_data.student_id,
            Enrollment.course_id == course_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        course_id=course_id,
        status="pending",
        progress=0.0,
        enrolled_at=datetime.now(),
        last_accessed_at=datetime.now(),
        certificate_issued=False
    )
    
    course.enrolled_count += 1
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return enrollment

@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(
    enrollment_id: int,
    update_data: EnrollmentUpdate,
    db: Session = Depends(get_db)
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if update_data.status:
        enrollment.status = update_data.status
        if update_data.status == "completed":
            enrollment.completed_at = datetime.now()
            
    if update_data.progress is not None:
        enrollment.progress = update_data.progress
        enrollment.last_accessed_at = datetime.now()

    db.commit()
    db.refresh(enrollment)
    return enrollment

@router.post("/{enrollment_id}/rate")
def rate_course(
    enrollment_id: int,
    rating: CourseRating,
    db: Session = Depends(get_db)
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if enrollment.status == "dropped":
        raise HTTPException(status_code=400, detail="Cannot rate a dropped course")

    course = db.get(Course, enrollment.course_id)
    if course.rating == 0:
        course.rating = rating.rating
    else:
        course.rating = (course.rating + rating.rating) / 2

    db.commit()
    return {"message": "Rating submitted successfully"}

@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db)
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment

@router.get("/student/{student_id}", response_model=List[EnrollmentResponse])
def get_student_enrollments(
    student_id: int,
    db: Session = Depends(get_db)
):
    enrollments = db.execute(
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.enrolled_at.desc())
    ).scalars().all()
    return enrollments

@router.post("/{enrollment_id}/progress")
def update_progress(
    enrollment_id: int,
    lesson_id: int,
    progress: float,
    db: Session = Depends(get_db)
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    enrollment.progress = min(100.0, max(0.0, progress))
    enrollment.last_accessed_at = datetime.now()

    if enrollment.progress >= 100:
        enrollment.status = "completed"
        enrollment.completed_at = datetime.now()

    db.commit()
    db.refresh(enrollment)
    return {
        "message": "Progress updated successfully",
        "progress": enrollment.progress
    }

@router.get("/course/{course_id}", response_model=List[EnrollmentResponse])
def get_course_enrollments(
    course_id: int,
    db: Session = Depends(get_db)
):
    # Lấy tất cả enrollments của một khóa học
    enrollments = db.execute(
        select(Enrollment)
        .where(
            Enrollment.course_id == course_id,
            Enrollment.status == "pending"  # Chỉ lấy các enrollment đang chờ duyệt
        )
        .order_by(Enrollment.enrolled_at.desc())
    ).scalars().all()
    
    # Join với bảng User để lấy thêm thông tin học viên
    enrollment_responses = []
    for enrollment in enrollments:
        student = db.get(User, enrollment.student_id)
        enrollment_dict = enrollment.__dict__
        enrollment_dict["student"] = {
            "id": student.id,
            "username": student.username,
            "email": student.email
        }
        enrollment_responses.append(enrollment_dict)
    
    return enrollment_responses