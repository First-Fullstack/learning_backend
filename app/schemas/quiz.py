from pydantic import BaseModel
from typing import List, Optional


class QuizQuestionOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False
    sort_order: int = 0


class QuizQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    sort_order: int = 0
    options: List[QuizQuestionOptionCreate]


class QuizCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    time_limit_minutes: int = 0
    passing_score_percentage: int = 0
    status: str = "active"
    questions: List[QuizQuestionCreate]


class QuizOut(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: List[dict]


class QuizAttemptOut(BaseModel):
    id: int
    score: int
    is_passed: bool
