from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.models.course import DifficultyLevel, PublishStatus


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    title: str
    description: str
    difficulty: DifficultyLevel
    is_premium: bool = False
    video_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    status: PublishStatus = PublishStatus.draft
    category_id: Optional[int] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    is_premium: Optional[bool] = None
    video_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    status: Optional[PublishStatus] = None
    category_id: Optional[int] = None

class CourseOut(CourseBase):
    id: int
    category_name: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseFilter(BaseModel):
    category_id: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    is_premium: Optional[bool] = None


class CourseProgressOut(BaseModel):
    course_id: int
    completion_rate: int


class UserProgressOut(BaseModel):
    course_id: int
    progress_percentage: int
    current_video_id: Optional[int] = None
    started_at: datetime
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CourseDetailOut(CourseOut):
    user_progress: Optional[UserProgressOut] = None


class CourseProgressUpdateIn(BaseModel):
    current_video_id: Optional[int] = None
    watched_seconds: int
    is_completed: bool

class CourseListResponse(BaseModel):
    courses: List[CourseOut]
    total_count: int
    current_page: int
    total_pages: int
