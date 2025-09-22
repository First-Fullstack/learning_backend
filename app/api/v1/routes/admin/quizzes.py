from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.quiz import Quiz, QuizQuestion, QuizQuestionOption
from app.schemas.quiz import QuizCreate, QuizOut

router = APIRouter()


@router.post("", response_model=QuizOut, status_code=201)
def create_quiz(quiz_in: QuizCreate, db: Session = Depends(get_db)):
    # Create quiz
    quiz = Quiz(
        course_id=quiz_in.course_id,
        title=quiz_in.title,
        description=quiz_in.description,
        time_limit_minutes=quiz_in.time_limit_minutes,
        passing_score_percentage=quiz_in.passing_score_percentage,
        status=quiz_in.status,
    )
    db.add(quiz)
    db.flush()  # so we get quiz.id before commit

    # Create questions & options
    for q in quiz_in.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q.question_text,
            question_type=q.question_type,
        )
        db.add(question)
        db.flush()

        for opt in q.options:
            option = QuizQuestionOption(
                question_id=question.id,
                option_text=opt.option_text,
                is_correct=opt.is_correct,
            )
            db.add(option)

    db.commit()
    db.refresh(quiz)
    return quiz
