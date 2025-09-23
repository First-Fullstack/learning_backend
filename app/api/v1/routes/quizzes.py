from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizQuestionOption, UserQuizAttempt, UserQuizAnswer
from app.schemas.quiz import QuizCreate, QuizOut, QuizAttemptCreate, QuizAttemptOut

router = APIRouter()

