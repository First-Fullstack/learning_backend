from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.db.deps import get_db
from app.models.quiz import Quiz, QuizQuestion, QuizQuestionOption
from app.schemas.quiz import QuizCreate, QuizOut, QuizUpdate, QuizDeleteResponse
from typing import List

router = APIRouter()


@router.get("", response_model=List[QuizOut], status_code=201)
def get_quiz(db: Session = Depends(get_db)):
    try:
        quizzes = (
            db.query(Quiz)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
            .all()
        )
        return quizzes
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "error": str(e),
            }
        )


@router.post("", response_model=QuizOut, status_code=201)
def create_quiz(quiz_in: QuizCreate, db: Session = Depends(get_db)):
    try:
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

        # Reload with relationships for response serialization
        quiz = (
            db.query(Quiz)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
            .filter(Quiz.id == quiz.id)
            .first()
        )

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

@router.put("/{quiz_id}", response_model=QuizOut)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
):
    try :
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Update simple fields
        update_data = quiz_in.dict(exclude_unset=True, exclude={"questions"})
        for field, value in update_data.items():
            setattr(quiz, field, value)

        # Handle questions replacement if provided
        if quiz_in.questions is not None:
            # Delete old questions & options
            db.query(QuizQuestionOption).filter(QuizQuestionOption.question_id.in_(
                db.query(QuizQuestion.id).filter(QuizQuestion.quiz_id == quiz.id)
            )).delete(synchronize_session=False)
            db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete(synchronize_session=False)
            db.flush()

            # Insert new questions & options
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
        
        # Reload with relationships for response serialization
        quiz = (
            db.query(Quiz)
            .options(selectinload(Quiz.questions).selectinload(QuizQuestion.options))
            .filter(Quiz.id == quiz.id)
            .first()
        )
        
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

@router.delete("/{quiz_id}", response_model=QuizDeleteResponse, summary="クイズ削除（管理者用）")
def delete_quiz(
    quiz_id: int = Path(..., description="クイズID"),
    db: Session = Depends(get_db)
):
    try:
        # Check if quiz exists
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="クイズが見つかりません")
        
        # Delete quiz (cascade will handle questions and options due to relationships)
        db.delete(quiz)
        db.commit()

        return QuizDeleteResponse(message="クイズ削除成功")
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