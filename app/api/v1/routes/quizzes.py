from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizQuestionOption, UserQuizAttempt, UserQuizAnswer
from app.schemas.quiz import QuizCreate, QuizOut, QuizAttemptCreate, QuizAttemptOut

router = APIRouter()


@router.post("/", response_model=QuizOut, status_code=201)
def create_quiz(data: QuizCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = Quiz(
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        time_limit_minutes=data.time_limit_minutes,
        passing_score_percentage=data.passing_score_percentage,
        status=data.status,
    )
    db.add(quiz)
    db.flush()
    for q in data.questions:
        qq = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q.question_text,
            question_type=q.question_type,
            sort_order=q.sort_order,
        )
        db.add(qq)
        db.flush()
        for o in q.options:
            db.add(
                QuizQuestionOption(
                    question_id=qq.id,
                    option_text=o.option_text,
                    is_correct=o.is_correct,
                    sort_order=o.sort_order,
                )
            )
    db.commit()
    db.refresh(quiz)
    return quiz


@router.post("/attempt", response_model=QuizAttemptOut)
def attempt_quiz(
    attempt: QuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.get(Quiz, attempt.quiz_id)
    if not quiz or quiz.status != "active":
        raise HTTPException(status_code=400, detail="Invalid quiz")

    # Compute score
    total_questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).count()
    correct = 0
    answers = []
    for ans in attempt.answers:
        question_id = ans.get("question_id")
        selected_option_id = ans.get("selected_option_id")
        option = db.get(QuizQuestionOption, selected_option_id)
        if option and option.question_id == question_id and option.is_correct:
            correct += 1
        answers.append((question_id, selected_option_id, bool(option and option.is_correct)))

    score_pct = int((correct / total_questions) * 100) if total_questions else 0
    is_passed = score_pct >= quiz.passing_score_percentage

    rec = UserQuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score_pct,
        total_questions=total_questions,
        correct_answers=correct,
        is_passed=is_passed,
    )
    db.add(rec)
    db.flush()
    for qid, oid, is_correct in answers:
        db.add(
            UserQuizAnswer(
                attempt_id=rec.id,
                question_id=qid,
                selected_option_id=oid,
                is_correct=is_correct,
            )
        )
    db.commit()
    db.refresh(rec)
    return QuizAttemptOut(id=rec.id, score=rec.score, is_passed=rec.is_passed)
