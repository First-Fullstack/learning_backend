from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import Course, CourseCategory, UserCourseProgress, PublishStatus, DifficultyLevel
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseOut,
    CategoryCreate,
    CategoryOut,
    CourseProgressOut,
)

router = APIRouter()


@router.post("/", response_model=CourseOut, status_code=201)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = Course(**course_in.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/", response_model=List[CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    category_id: Optional[int] = None,
    difficulty: Optional[DifficultyLevel] = None,
    is_premium: Optional[bool] = None,
):
    q = db.query(Course)
    if category_id is not None:
        q = q.filter(Course.category_id == category_id)
    if difficulty is not None:
        q = q.filter(Course.difficulty == difficulty)
    if is_premium is not None:
        q = q.filter(Course.is_premium == is_premium)
    q = q.filter(Course.status != PublishStatus.archived)
    return q.order_by(Course.sort_order.asc(), Course.id.desc()).all()


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.get(Course, course_id)
    if not course or course.status == PublishStatus.archived:
        raise HTTPException(status_code=404, detail="Course not found")
    progress = (
        db.query(UserCourseProgress)
        .filter(UserCourseProgress.user_id == current_user.id, UserCourseProgress.course_id == course.id)
        .first()
    )
    progress_out = (
        CourseProgressOut(course_id=course.id, completion_rate=progress.progress_percentage)
        if progress
        else None
    )
    return {"course": CourseOut.model_validate(course), "progress": progress_out}


@router.put("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, update: CourseUpdate, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    data = update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(course, k, v)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}")
def archive_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.status = PublishStatus.archived
    db.add(course)
    db.commit()
    return {"status": "archived"}


@router.patch("/{course_id}/status")
def set_status(course_id: int, status_value: PublishStatus, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.status = status_value
    db.commit()
    return {"status": course.status}


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(cat: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(CourseCategory).filter(CourseCategory.name == cat.name).first()
    if existing:
        return existing
    c = CourseCategory(name=cat.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(CourseCategory).order_by(CourseCategory.sort_order.asc(), CourseCategory.name.asc()).all()
