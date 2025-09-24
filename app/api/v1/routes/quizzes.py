from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizQuestionOption, UserQuizAttempt, UserQuizAnswer
from app.schemas.quiz import (
    QuizCreate,
    QuizOut,
    QuizAttemptCreate,
    QuizAttemptOut,
    QuizSubmissionIn,
    QuizSubmissionOut,
)

router = APIRouter()


@router.post("/{quiz_id}/submit", response_model=QuizSubmissionOut)
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmissionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        quiz = db.get(Quiz, quiz_id)
        if not quiz or quiz.status != "active":
            raise HTTPException(status_code=404, detail="Quiz not found or inactive")

        # Fetch all question IDs for the quiz
        question_rows = db.query(QuizQuestion.id).filter(QuizQuestion.quiz_id == quiz_id).all()
        question_ids = [row.id for row in question_rows]
        total_questions = len(question_ids)

        # Map correct option per question
        correct_map = {}
        if question_ids:
            rows = (
                db.query(QuizQuestionOption.question_id, QuizQuestionOption.id)
                .filter(QuizQuestionOption.question_id.in_(question_ids), QuizQuestionOption.is_correct == True)
                .all()
            )
            for qid, oid in rows:
                correct_map[qid] = oid

        correct = 0
        results = []
        for ans in payload.answers:
            qid = ans.question_id
            selected = ans.selected_option_id
            correct_option_id = correct_map.get(qid)
            is_correct = bool(correct_option_id and selected == correct_option_id)
            if is_correct:
                correct += 1
            results.append({
                "question_id": qid,
                "is_correct": is_correct,
                "correct_answer": correct_option_id or 0,
            })

        score_pct = int((correct / total_questions) * 100) if total_questions else 0
        is_passed = score_pct >= (quiz.passing_score_percentage or 0)

        return QuizSubmissionOut(
            score=score_pct,
            total_questions=total_questions,
            correct_answers=correct,
            is_passed=is_passed,
            results=results,
        )
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
