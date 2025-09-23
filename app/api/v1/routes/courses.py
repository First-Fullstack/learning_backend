from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

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
    CourseListResponse,
    CourseDetailOut,
    UserProgressOut,
)

router = APIRouter()


@router.get("/", response_model=CourseListResponse)
def list_courses(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None, description="カテゴリでフィルタリング"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="難易度でフィルタリング"),
    is_premium: Optional[bool] = Query(None, description="プレミアムコースでフィルタリング"),
    page: int = Query(1, description="ページ番号", ge=1),
    limit: int = Query(20, description="1ページあたりの件数", ge=1, le=100),
):
    print(difficulty)
    # Build base query with filters
    q = db.query(Course)
    if category_id is not None:
        q = q.filter(Course.category_id == category_id)
    if difficulty is not None:
        q = q.filter(Course.difficulty == difficulty)
    if is_premium is not None:
        q = q.filter(Course.is_premium == is_premium)
    q = q.filter(Course.status != PublishStatus.archived)
    
    # Get total count for pagination
    total_count = q.count()
    
    # Calculate pagination
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit  # Ceiling division
    
    # Apply pagination and ordering
    courses = q.order_by(Course.sort_order.asc(), Course.id.desc()).offset(offset).limit(limit).all()
    
    return CourseListResponse(
        courses=courses,
        total_count=total_count,
        current_page=page,
        total_pages=total_pages
    )

@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.get(Course, course_id)
    if not course or course.status == PublishStatus.archived:
        raise HTTPException(status_code=404, detail="Course not found")

    # Resolve category name if present
    category_name: Optional[str] = None
    if course.category_id:
        category = db.query(CourseCategory).filter(CourseCategory.id == course.category_id).first()
        category_name = category.name if category else None

    # Fetch user progress
    progress = (
        db.query(UserCourseProgress)
        .filter(UserCourseProgress.user_id == current_user.id, UserCourseProgress.course_id == course.id)
        .first()
    )
    user_progress: Optional[UserProgressOut] = None
    if progress:
        user_progress = UserProgressOut(
            course_id=progress.course_id,
            progress_percentage=progress.progress_percentage,
            current_video_id=progress.current_video_id,
            started_at=progress.started_at,
            last_accessed_at=progress.last_accessed_at,
            completed_at=progress.completed_at,
        )

    # Build response explicitly to inject category_name
    base = CourseOut.model_validate(course)
    return CourseDetailOut(
        id=base.id,
        title=base.title,
        description=base.description,
        difficulty=base.difficulty,
        is_premium=base.is_premium,
        video_url=base.video_url,
        thumbnail_url=base.thumbnail_url,
        status=base.status,
        category_id=base.category_id,
        category_name=category_name,
        estimated_duration_minutes=base.estimated_duration_minutes,
        created_at=base.created_at,
        updated_at=base.updated_at,
        user_progress=user_progress,
    )


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
