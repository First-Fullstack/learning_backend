from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class DifficultyLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class PublishStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    courses = relationship("Course", back_populates="category")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False, default=DifficultyLevel.beginner)
    is_premium = Column(Boolean, default=False, nullable=False)
    video_url = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)
    status = Column(Enum(PublishStatus), default=PublishStatus.draft, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("Category", back_populates="courses")
    progresses = relationship("CourseProgress", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")


class CourseProgress(Base):
    __tablename__ = "course_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    completion_rate = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="progresses")
    course = relationship("Course", back_populates="progresses")
