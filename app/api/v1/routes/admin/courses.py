from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.deps import get_db
from app.models.course import Course, CourseCategory
from app.schemas.course import CourseOut, CourseCreate

router = APIRouter()

@router.get("", response_model=List[CourseOut])
def list_courses(
    status: Optional[str] = Query("all", description="Filter by status: all, published, draft, archived"),
    search: Optional[str] = Query(None, description="Search keyword"),
    db: Session = Depends(get_db),
):
    query = db.query(Course)

    if status and status != "all":
        query = query.filter(Course.status == status)

    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))

    courses = query.all()
    return courses
    
@router.post("", response_model=CourseOut)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    # check category exists if category_id is provided and not 0
    category = None
    if course_in.category_id and course_in.category_id > 0:
        category = db.query(CourseCategory).filter(CourseCategory.id == course_in.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    elif course_in.category_id == 0:
        # Set category_id to None if it's 0
        course_data = course_in.model_dump()
        course_data['category_id'] = None
    else:
        course_data = course_in.model_dump()

    # create course instance
    if course_in.category_id == 0:
        course = Course(**course_data)
    else:
        course = Course(**course_in.model_dump())
    
    db.add(course)
    db.commit()
    db.refresh(course)

    # attach category_name dynamically
    course.category_name = category.name if category else None

    return course

@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Attach category name dynamically if relationship is not joined
    if course.category_id:
        category = db.query(CourseCategory).filter(CourseCategory.id == course.category_id).first()
        course.category_name = category.name if category else None
    else:
        course.category_name = None

    return course