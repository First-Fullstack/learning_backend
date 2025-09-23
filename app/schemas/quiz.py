from pydantic import BaseModel
from typing import List, Optional


# ---------------------------
# Attempt Schemas (used by quizzes routes)
# ---------------------------
class AnswerIn(BaseModel):
    question_id: int
    selected_option_id: int


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: List[AnswerIn]


class QuizAttemptOut(BaseModel):
    id: int
    score: int
    is_passed: bool

# ---------------------------
# Option Schema
# ---------------------------
class OptionBase(BaseModel):
    option_text: str
    is_correct: bool


class OptionCreate(OptionBase):
    pass


class OptionOut(OptionBase):
    id: int

    class Config:
        from_attributes = True


# ---------------------------
# Question Schema
# ---------------------------
class QuestionBase(BaseModel):
    question_text: str
    question_type: str  # e.g., "multiple_choice", "true_false"
    options: List[OptionCreate]


class QuestionCreate(QuestionBase):
    pass


class QuestionOut(BaseModel):
    id: int
    question_text: str
    question_type: str
    options: List[OptionOut]

    class Config:
        from_attributes = True


# ---------------------------
# Quiz Schema
# ---------------------------
class QuizBase(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: Optional[int] = None
    status: str = "active"  # e.g., "active", "inactive"
    questions: List[QuestionCreate]


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    course_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: Optional[int] = None
    status: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None


class QuizOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    time_limit_minutes: Optional[int]
    passing_score_percentage: Optional[int]
    status: str
    questions: List[QuestionOut]

    class Config:
        from_attributes = True
