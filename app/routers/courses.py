from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_
from typing import List, Optional
from slugify import slugify  
from sqlalchemy import text
import logging

from app.dependencies import get_current_user_optional
from database import get_db
from app.models import Course, Enrollment,  User
from ..schemas.course import CourseCreate, CourseResponse, CourseUpdate, StudentCourseResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/courses",
    tags=["courses"]
)

@router.post("/", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db)
):
    instructor = db.get(User, course.instructor_id)
    if not instructor or instructor.role != 'instructor':
        raise HTTPException(403, "Only instructors can create courses")

    slug = slugify(course.title)

    new_course = Course(
        title=course.title,
        slug=slug,
        description=course.description,
        instructor_id=course.instructor_id,
        category=course.category,
        level=course.level,
        price=course.price,
        status='draft'
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@router.get("/", response_model=List[StudentCourseResponse])
def get_courses(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        # Base query
        query = select(Course)
        
        # Instructor filter
        if current_user and current_user.role == 'instructor':
            query = query.where(Course.instructor_id == current_user.id)
        else:
            query = query.where(Course.status == "published")

        # Apply filters
        if keyword:
            query = query.where(
                or_(
                    Course.title.contains(keyword),
                    Course.description.contains(keyword)
                )
            )
        if category:
            query = query.where(Course.category == category)
        if level:
            query = query.where(Course.level == level)
        if status and current_user and current_user.role == 'instructor':
            query = query.where(Course.status == status)

        courses = db.execute(query).scalars().all()
        
        # Format response
        response_courses = []
        for course in courses:
            course_data = course.__dict__.copy()
            
            # Default enrollment info
            enrollment_info = {
                "enrollment_status": "not_enrolled",
                "enrollment_progress": 0
            }
            
            # Add enrollment info for students
            if current_user and current_user.role == 'student':
                try:
                    enrollment_query = text("""
                        SELECT status, progress 
                        FROM enrollments 
                        WHERE student_id = :student_id 
                        AND course_id = :course_id
                    """)
                    
                    enrollment = db.execute(
                        enrollment_query,
                        {
                            "student_id": current_user.id,
                            "course_id": course.id
                        }
                    ).first()
                    
                    if enrollment:
                        enrollment_info.update({
                            "enrollment_status": enrollment.status,
                            "enrollment_progress": enrollment.progress
                        })
                except Exception as e:
                    logger.error(f"Error querying enrollment: {e}")
                    # Keep default values if query fails
            
            course_data.update(enrollment_info)
            response_courses.append(course_data)

        return response_courses
        
    except Exception as e:
        logger.error(f"Error in get_courses: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        # Kiểm tra user đã đăng nhập chưa
        if not current_user:
            raise HTTPException(
                status_code=401, 
                detail="You must be logged in to view course details"
            )

        course = db.get(Course, course_id)
        if not course:
            raise HTTPException(404, "Course not found")

        # Instructor của khóa học có thể xem
        if current_user.role == 'instructor' and current_user.id == course.instructor_id:
            return course

        # Admin có thể xem
        if current_user.role == 'admin':
            return course

        # Kiểm tra student đã đăng ký và được phép học 
        enrollment = db.execute(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course_id,
                Enrollment.status.in_(["approved", "studying", "completed"])
            )
        ).first()

        if not enrollment:
            raise HTTPException(
                status_code=403,
                detail="You must be enrolled and approved to view this course"
            )

        return course

    except Exception as e:
        logger.error(f"Error in get_course: {e}")
        raise HTTPException(500, "Internal server error")

@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    try:
        # Get the course
        course = db.get(Course, course_id)
        if not course:
            raise HTTPException(404, "Course not found")
            
        # Check permissions
        if not current_user or current_user.id != course.instructor_id:
            raise HTTPException(403, "Only course instructor can update course")

        # Validate status change
        if course_update.status and course_update.status not in ['draft', 'published']:
            raise HTTPException(400, "Invalid status value")

        # Update course fields
        for field, value in course_update.dict(exclude_unset=True).items():
            setattr(course, field, value)

        db.commit()
        db.refresh(course)
        return course

    except Exception as e:
        logger.error(f"Error in update_course: {e}")
        raise HTTPException(500, "Internal server error")