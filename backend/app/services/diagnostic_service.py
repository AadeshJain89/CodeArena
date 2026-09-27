from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.problem import Problem
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_assessment_question import DiagnosticAssessmentQuestion
from app.schemas.diagnostic import (
    DiagnosticQuestionItem,
    DiagnosticStartResponse,
    DiagnosticSubmitRequest,
    DiagnosticResultResponse,
    TopicResultItem,
)


def is_answer_correct(selected: str, correct_opt: str, options: List[str] = None) -> bool:
    """Evaluate selected answer against correct option securely."""
    if not selected or not correct_opt:
        return False

    sel = selected.strip().upper()
    corr = correct_opt.strip().upper()

    # Exact match (e.g. "C" == "C" or "C. O(N)" == "C. O(N)")
    if sel == corr:
        return True

    # Prefix match (e.g. "C. O(N)" starts with "C" or "C" matches "C.")
    if sel.startswith(corr) or corr.startswith(sel):
        return True

    # Letter extracted match (e.g. sel="C. O(N)" -> "C", corr="C")
    sel_letter = sel.split('.')[0].strip() if '.' in sel else sel
    corr_letter = corr.split('.')[0].strip() if '.' in corr else corr
    if sel_letter == corr_letter:
        return True

    return False


class DiagnosticService:
    async def get_diagnostic_questions(self, db: AsyncSession, limit: int = 10) -> List[Problem]:
        """Fetch diagnostic problems covering distinct topics evenly."""
        stmt = (
            select(Problem)
            .options(selectinload(Problem.topics))
            .where(Problem.is_diagnostic == True)
            .order_by(Problem.id.asc())
        )
        result = await db.execute(stmt)
        all_mcq = result.scalars().all()

        # Select 1 question per topic to ensure even topic distribution
        selected_questions: List[Problem] = []
        seen_topics = set()

        for prob in all_mcq:
            if len(selected_questions) >= limit:
                break
            topic_ids = {t.id for t in prob.topics}
            if not topic_ids.intersection(seen_topics):
                selected_questions.append(prob)
                seen_topics.update(topic_ids)

        # If fewer than limit selected, fill remaining with any diagnostic problems
        if len(selected_questions) < limit:
            selected_ids = {p.id for p in selected_questions}
            for prob in all_mcq:
                if len(selected_questions) >= limit:
                    break
                if prob.id not in selected_ids:
                    selected_questions.append(prob)

        return selected_questions

    async def start_assessment(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> DiagnosticStartResponse:
        """Create a new IN_PROGRESS diagnostic assessment, persist exact questions, and return without correct answers."""
        questions = await self.get_diagnostic_questions(db, limit=10)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No diagnostic questions available in problem bank",
            )

        assessment = DiagnosticAssessment(
            user_id=user_id,
            status="IN_PROGRESS",
            total_questions=len(questions),
            started_at=datetime.now(timezone.utc),
        )
        db.add(assessment)
        await db.flush()

        # Persist exact selected questions with order
        for idx, prob in enumerate(questions):
            assoc = DiagnosticAssessmentQuestion(
                assessment_id=assessment.id,
                problem_id=prob.id,
                question_order=idx + 1,
            )
            db.add(assoc)

        await db.commit()
        await db.refresh(assessment)

        question_items = [
            DiagnosticQuestionItem(
                problem_id=p.id,
                title=p.title,
                description=p.description,
                topic_id=p.topics[0].id if p.topics else 0,
                topic_name=p.topics[0].name if p.topics else "General",
                question_type="MCQ",
                options=p.diagnostic_options or p.options or [],
            )
            for p in questions
        ]

        return DiagnosticStartResponse(
            assessment_id=assessment.id,
            status=assessment.status,
            total_questions=assessment.total_questions,
            questions=question_items,
        )

    async def get_assessment(
        self,
        db: AsyncSession,
        user_id: int,
        assessment_id: int,
    ) -> DiagnosticResultResponse:
        """Retrieve diagnostic assessment details for the owner using persisted questions."""
        stmt = (
            select(DiagnosticAssessment)
            .options(
                selectinload(DiagnosticAssessment.assessment_questions)
                .selectinload(DiagnosticAssessmentQuestion.problem)
                .selectinload(Problem.topics),
                selectinload(DiagnosticAssessment.responses)
                .selectinload(DiagnosticResponse.problem)
                .selectinload(Problem.topics),
            )
            .where(DiagnosticAssessment.id == assessment_id)
        )
        result = await db.execute(stmt)
        assessment = result.scalar_one_or_none()

        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnostic assessment with ID {assessment_id} not found",
            )

        if assessment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this diagnostic assessment",
            )

        # Retrieve questions from persisted assessment_questions ordered by question_order
        question_items = [
            DiagnosticQuestionItem(
                problem_id=aq.problem.id,
                title=aq.problem.title,
                description=aq.problem.description,
                topic_id=aq.problem.topics[0].id if aq.problem.topics else 0,
                topic_name=aq.problem.topics[0].name if aq.problem.topics else "General",
                question_type="MCQ",
                options=aq.problem.diagnostic_options or aq.problem.options or [],
            )
            for aq in assessment.assessment_questions
        ]

        topic_results = await self.calculate_topic_results(db, assessment)

        return DiagnosticResultResponse(
            assessment_id=assessment.id,
            status=assessment.status,
            total_questions=assessment.total_questions,
            answered_questions=assessment.answered_questions,
            correct_answers=assessment.correct_answers,
            score=assessment.score,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at,
            topic_results=topic_results,
            questions=question_items,
        )

    async def calculate_topic_results(
        self,
        db: AsyncSession,
        assessment: DiagnosticAssessment,
    ) -> List[TopicResultItem]:
        """Compute topic-wise breakdown results."""
        if not assessment.responses:
            return []

        topic_stats: Dict[int, Dict[str, Any]] = {}

        for resp in assessment.responses:
            prob = resp.problem
            if not prob or not prob.topics:
                continue
            t = prob.topics[0]
            if t.id not in topic_stats:
                topic_stats[t.id] = {
                    "topic_id": t.id,
                    "topic_name": t.name,
                    "questions": 0,
                    "correct": 0,
                }
            topic_stats[t.id]["questions"] += 1
            if resp.is_correct:
                topic_stats[t.id]["correct"] += 1

        topic_results = []
        for t_id, data in topic_stats.items():
            q_cnt = data["questions"]
            c_cnt = data["correct"]
            score = round((c_cnt / q_cnt) * 100, 2) if q_cnt > 0 else 0.0
            topic_results.append(
                TopicResultItem(
                    topic_id=data["topic_id"],
                    topic_name=data["topic_name"],
                    questions=q_cnt,
                    correct=c_cnt,
                    score=score,
                )
            )

        return topic_results

    async def submit_assessment(
        self,
        db: AsyncSession,
        user_id: int,
        assessment_id: int,
        request: DiagnosticSubmitRequest,
    ) -> DiagnosticResultResponse:
        """Evaluate submitted answers against persisted questions and mark assessment COMPLETED."""
        stmt = (
            select(DiagnosticAssessment)
            .options(
                selectinload(DiagnosticAssessment.assessment_questions)
                .selectinload(DiagnosticAssessmentQuestion.problem)
            )
            .where(DiagnosticAssessment.id == assessment_id)
        )
        result = await db.execute(stmt)
        assessment = result.scalar_one_or_none()

        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnostic assessment with ID {assessment_id} not found",
            )

        if assessment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to submit this assessment",
            )

        if assessment.status == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diagnostic assessment is already completed",
            )

        persisted_questions_map = {
            aq.problem_id: aq.problem for aq in assessment.assessment_questions
        }

        # Validate submitted question IDs against persisted questions
        for ans in request.answers:
            if ans.problem_id not in persisted_questions_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question ID {ans.problem_id} does not belong to this assessment",
                )

        submitted_answers_map = {ans.problem_id: ans.selected_answer for ans in request.answers}

        correct_count = 0
        answered_count = 0

        for aq in assessment.assessment_questions:
            prob = aq.problem
            user_ans = submitted_answers_map.get(prob.id)
            if user_ans and user_ans.strip():
                answered_count += 1

            correct_opt = prob.diagnostic_correct_option or prob.correct_option or ""
            is_corr = is_answer_correct(
                user_ans, correct_opt, prob.diagnostic_options or prob.options
            )
            if is_corr:
                correct_count += 1

            diag_resp = DiagnosticResponse(
                assessment_id=assessment.id,
                problem_id=prob.id,
                selected_answer=user_ans,
                is_correct=is_corr,
            )
            db.add(diag_resp)

        total_q = len(assessment.assessment_questions)
        overall_score = round((correct_count / total_q) * 100, 2) if total_q > 0 else 0.0

        assessment.status = "COMPLETED"
        assessment.answered_questions = answered_count
        assessment.correct_answers = correct_count
        assessment.score = overall_score
        assessment.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(assessment)

        return await self.get_assessment(db, user_id=user_id, assessment_id=assessment_id)
