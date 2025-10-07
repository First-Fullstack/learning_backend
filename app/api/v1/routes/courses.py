from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.course import Course, CourseCategory, UserCourseProgress, PublishStatus, DifficultyLevel, CourseVideo
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
    CourseProgressUpdateIn,
)
from app.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz import QuizOut

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
    try:
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
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )

@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
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
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "失敗した",
                "error": str(e),
            }
        )

@router.put("/{course_id}/progress", response_model=UserProgressOut)
def update_progress(
    course_id: int,
    body: CourseProgressUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate course
        course = db.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Compute total duration seconds for the course
        total_duration_seconds = (
            db.query(func.coalesce(func.sum(CourseVideo.duration_seconds), 0)).filter(CourseVideo.course_id == course_id).scalar()
        )
        if total_duration_seconds <= 0:
            # Avoid division by zero; treat as 0% when no videos/duration
            computed_percentage = 0
        else:
            # Clamp watched_seconds to [0, total]
            watched = max(0, min(body.watched_seconds, total_duration_seconds))
            computed_percentage = int((watched / total_duration_seconds) * 100)
            if body.is_completed:
                computed_percentage = max(computed_percentage, 100)

        # Upsert progress
        progress = (
            db.query(UserCourseProgress)
            .filter(UserCourseProgress.user_id == current_user.id, UserCourseProgress.course_id == course_id)
            .first()
        )
        now = datetime.utcnow()

        # Validate current_video_id if provided; allow None/0 as null
        validated_video_id = None
        if body.current_video_id is not None and body.current_video_id != 0:
            video = db.query(CourseVideo).filter(CourseVideo.id == body.current_video_id, CourseVideo.course_id == course_id).first()
            if video:
                validated_video_id = body.current_video_id
            else:
                # If invalid, silently ignore and store NULL to avoid FK errors
                validated_video_id = None

        if progress:
            progress.current_video_id = validated_video_id
            progress.progress_percentage = computed_percentage
            progress.last_accessed_at = now
            if body.is_completed:
                progress.completed_at = now
        else:
            progress = UserCourseProgress(
                user_id=current_user.id,
                course_id=course_id,
                current_video_id=validated_video_id,
                progress_percentage=computed_percentage,
                started_at=now,
                last_accessed_at=now,
                completed_at=now if body.is_completed else None,
            )
            db.add(progress)

        db.commit()
        db.refresh(progress)

        return UserProgressOut(
            course_id=progress.course_id,
            progress_percentage=progress.progress_percentage,
            current_video_id=progress.current_video_id,
            started_at=progress.started_at,
            last_accessed_at=progress.last_accessed_at,
            completed_at=progress.completed_at,
        )
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )

@router.get("/{course_id}/quiz", response_model=QuizOut)
def get_course_quiz(course_id: int, db: Session = Depends(get_db)):
    try:
        quiz = (
            db.query(Quiz)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
            .filter(Quiz.course_id == course_id, Quiz.status == "active")
            .order_by(Quiz.id.asc())
            .first()
        )
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found for course")
        return quiz
    except Exception as e:
        db.rollback()
        # Raise HTTP 400 or 500 with a JSON message
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )
