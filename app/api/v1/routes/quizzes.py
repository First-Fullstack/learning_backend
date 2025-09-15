from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.quiz import Quiz, QuizOption, QuizAttempt
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizOut, QuizAttemptCreate, QuizAttemptOut

router = APIRouter()


@router.post("/", response_model=QuizOut, status_code=201)
def create_quiz(data: QuizCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = Quiz(course_id=data.course_id, question=data.question, is_active=data.is_active)
    db.add(quiz)
    db.flush()
    for opt in data.options:
        db.add(QuizOption(quiz_id=quiz.id, text=opt.text, is_correct=opt.is_correct))
    db.commit()
    db.refresh(quiz)
    return quiz


@router.put("/{quiz_id}", response_model=QuizOut)
def update_quiz(quiz_id: int, update: QuizUpdate, db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    data = update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(quiz, k, v)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz.is_active = False
    db.commit()
    return {"status": "disabled"}


@router.get("/", response_model=List[QuizOut])
def list_quizzes(course_id: int, db: Session = Depends(get_db)):
    return db.query(Quiz).filter(Quiz.course_id == course_id, Quiz.is_active == True).all()


@router.post("/attempt", response_model=QuizAttemptOut)
def attempt_quiz(
    attempt: QuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, attempt.quiz_id)
    option = db.get(QuizOption, attempt.selected_option_id)
    if not quiz or not option or option.quiz_id != quiz.id:
        raise HTTPException(status_code=400, detail="Invalid quiz/option")
    is_correct = option.is_correct
    rec = QuizAttempt(
        user_id=current_user.id,
        course_id=quiz.course_id,
        quiz_id=quiz.id,
        selected_option_id=option.id,
        is_correct=is_correct,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
