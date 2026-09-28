from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.topic import Topic
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.skill_profile import SkillProfile
from app.models.user_gamification import UserGamification
from app.services.gamification_service import GamificationService
from app.services.recommendation_service import RecommendationService
from app.schemas.analytics import (
    DashboardResponse,
    OverviewAnalytics,
    DiagnosticSummaryAnalytics,
    TopicSkillItemAnalytics,
    SubmissionItemAnalytics,
    SubmissionAnalytics,
    RecommendationItemAnalytics,
    RecommendationSummaryAnalytics,
    GamificationSummaryAnalytics,
)


class AnalyticsService:
    def __init__(self):
        self.gamification_service = GamificationService()
        self.recommendation_service = RecommendationService()

    async def get_user_dashboard_data(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> DashboardResponse:
        """
        Gather and aggregate all analytics and stats for the authenticated user
        from existing database records and existing services.
        """
        # 1. Fetch / initialize user gamification data
        gamification = await self.gamification_service.get_or_create_user_gamification(db, user_id=user_id)

        # 2. Fetch all user submissions (newest first) with problem details
        stmt_subs = (
            select(Submission)
            .options(selectinload(Submission.problem))
            .where(Submission.user_id == user_id)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
        )
        submissions = (await db.execute(stmt_subs)).scalars().all()

        total_submissions = len(submissions)
        passed_submissions = sum(1 for s in submissions if s.status == "PASSED")
        failed_submissions = total_submissions - passed_submissions
        success_rate = (
            round((passed_submissions / total_submissions) * 100.0, 1)
            if total_submissions > 0
            else 0.0
        )

        attempted_problem_ids = set(s.problem_id for s in submissions)
        total_problems_attempted = len(attempted_problem_ids)

        recent_submission_items: List[SubmissionItemAnalytics] = []
        for s in submissions[:10]:
            prob_title = s.problem.title if s.problem else f"Problem #{s.problem_id}"
            recent_submission_items.append(
                SubmissionItemAnalytics(
                    submission_id=s.id,
                    problem_id=s.problem_id,
                    problem_title=prob_title,
                    language=s.language,
                    status=s.status,
                    submitted_at=s.created_at,
                    execution_time_ms=s.execution_time_ms,
                )
            )

        submission_analytics = SubmissionAnalytics(
            total_submissions=total_submissions,
            passed_submissions=passed_submissions,
            failed_submissions=failed_submissions,
            success_rate=success_rate,
            recent_submissions=recent_submission_items,
        )

        # 3. Fetch latest completed diagnostic assessment
        stmt_diag = (
            select(DiagnosticAssessment)
            .where(
                DiagnosticAssessment.user_id == user_id,
                DiagnosticAssessment.status == "COMPLETED",
            )
            .order_by(DiagnosticAssessment.id.desc())
        )
        diag = (await db.execute(stmt_diag)).scalars().first()

        if diag:
            diag_analytics = DiagnosticSummaryAnalytics(
                has_completed_diagnostic=True,
                score=round(diag.score, 1),
                total_questions=diag.total_questions,
                correct_answers=diag.correct_answers,
                percentage=round(diag.score, 1),
                completed_at=diag.completed_at,
            )
        else:
            diag_analytics = DiagnosticSummaryAnalytics(
                has_completed_diagnostic=False,
                score=None,
                total_questions=None,
                correct_answers=None,
                percentage=None,
                completed_at=None,
            )

        # 4. Fetch all topics and user skill profiles
        stmt_topics = select(Topic).order_by(Topic.id.asc())
        all_topics = (await db.execute(stmt_topics)).scalars().all()

        stmt_skills = select(SkillProfile).where(SkillProfile.user_id == user_id)
        user_skills = (await db.execute(stmt_skills)).scalars().all()
        skills_map = {sp.topic_id: sp for sp in user_skills}

        topic_skill_items: List[TopicSkillItemAnalytics] = []
        for topic in all_topics:
            sp = skills_map.get(topic.id)
            if sp:
                topic_skill_items.append(
                    TopicSkillItemAnalytics(
                        topic_id=topic.id,
                        topic_name=topic.name,
                        skill_score=round(sp.skill_score, 1),
                        skill_level=sp.skill_level,
                        confidence=round(sp.confidence, 2),
                        problems_solved=sp.problems_solved,
                        total_points=sp.total_points,
                    )
                )
            else:
                topic_skill_items.append(
                    TopicSkillItemAnalytics(
                        topic_id=topic.id,
                        topic_name=topic.name,
                        skill_score=0.0,
                        skill_level="NOVICE",
                        confidence=0.0,
                        problems_solved=0,
                        total_points=0,
                    )
                )

        # 5. Fetch personalized problem recommendations
        recs = await self.recommendation_service.get_user_recommendations(db, user_id=user_id)
        rec_items: List[RecommendationItemAnalytics] = []
        for r in recs[:5]:
            prob_title = r.problem.title if r.problem else f"Problem #{r.problem_id}"
            diff_str = (
                r.problem.difficulty.value
                if hasattr(r.problem.difficulty, "value")
                else str(r.problem.difficulty)
            ) if r.problem else "EASY"

            rec_items.append(
                RecommendationItemAnalytics(
                    recommendation_id=r.recommendation_id,
                    problem_id=r.problem_id,
                    problem_title=prob_title,
                    rank=r.rank,
                    score=round(r.score, 2),
                    reasons=r.reasons or [],
                    difficulty=diff_str,
                )
            )

        recommendation_analytics = RecommendationSummaryAnalytics(
            total_recommendations=len(recs),
            recommendations=rec_items,
        )

        # 6. Gamification summary
        xp_for_next = 100 - (gamification.xp % 100)
        gamification_analytics = GamificationSummaryAnalytics(
            xp=gamification.xp,
            level=gamification.level,
            problems_solved=gamification.problems_solved,
            successful_submissions=gamification.successful_submissions,
            current_streak=gamification.current_streak,
            longest_streak=gamification.longest_streak,
            badges=gamification.badges or [],
            xp_for_next_level=xp_for_next,
            last_activity_date=gamification.last_activity_date,
        )

        # 7. Overview analytics
        overview_analytics = OverviewAnalytics(
            total_problems_attempted=total_problems_attempted,
            total_problems_solved=gamification.problems_solved,
            total_submissions=total_submissions,
            successful_submissions=passed_submissions,
            failed_submissions=failed_submissions,
            success_rate=success_rate,
            current_streak=gamification.current_streak,
            longest_streak=gamification.longest_streak,
            xp=gamification.xp,
            current_level=gamification.level,
        )

        return DashboardResponse(
            overview=overview_analytics,
            diagnostic=diag_analytics,
            skills=topic_skill_items,
            submissions=submission_analytics,
            recommendations=recommendation_analytics,
            gamification=gamification_analytics,
        )
