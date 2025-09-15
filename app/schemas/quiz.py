from pydantic import BaseModel
from typing import List, Optional


class QuizOptionBase(BaseModel):
    text: str
    is_correct: bool = False


class QuizOptionCreate(QuizOptionBase):
    pass


class QuizOptionOut(QuizOptionBase):
    id: int

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    course_id: int
    question: str
    is_active: bool = True


class QuizCreate(QuizBase):
    options: List[QuizOptionCreate]


class QuizUpdate(BaseModel):
    question: Optional[str] = None
    is_active: Optional[bool] = None


class QuizOut(QuizBase):
    id: int
    options: List[QuizOptionOut]

    class Config:
        from_attributes = True


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    selected_option_id: int


class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    selected_option_id: int
    is_correct: bool
