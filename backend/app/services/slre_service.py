from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.topic import Topic
from app.models.problem import Problem, ProblemDifficulty
from app.models.skill_profile import SkillProfile
from app.models.diagnostic_assessment import DiagnosticAssessment
from app.models.diagnostic_response import DiagnosticResponse
from app.models.submission import Submission


# Configurable SLRE Engine Constants & Weights
POINTS_MAP: Dict[str, int] = {
    "EASY": 10,
    "MEDIUM": 25,
    "HARD": 50,
}

DIFFICULTY_BASE_RATING: Dict[str, float] = {
    "EASY": 35.0,
    "MEDIUM": 65.0,
    "HARD": 95.0,
}

DIFFICULTY_WEIGHT: Dict[str, float] = {
    "EASY": 1.0,
    "MEDIUM": 2.0,
    "HARD": 3.5,
}

# Base skill & confidence defaults
DEFAULT_UNTESTED_SKILL: float = 10.0
DEFAULT_UNTESTED_CONFIDENCE: float = 0.05
DIAGNOSTIC_CONFIDENCE_INC: float = 0.30
SUBMISSION_CONFIDENCE_INC: float = 0.15

# Configurable Attempt Factor Constants
ATTEMPT_DECAY_RATE: float = 0.15
ATTEMPT_FACTOR_MIN: float = 0.50
ATTEMPT_FACTOR_MAX: float = 1.00

# Configurable Recency Factor Constants
RECENCY_DECAY_PER_DAY: float = 0.01
RECENCY_FACTOR_MIN: float = 0.70
RECENCY_FACTOR_MAX: float = 1.00


def compute_skill_level_name(score: float) -> str:
    """Deterministically map numeric skill score (0-100) to skill level display string."""
    if score >= 80.0:
        return "EXPERT"
    elif score >= 60.0:
        return "ADVANCED"
    elif score >= 40.0:
        return "INTERMEDIATE"
    elif score >= 20.0:
        return "NOVICE"
    else:
        return "BEGINNER"


class SLREService:
    """Skill Level Recommendation Engine (SLRE) Service.

    Provides deterministic weighted rule scoring for skill estimation,
    incorporating correctness, problem difficulty, submission attempts,
    evidence confidence, and recency.
    """

    async def calculate_attempt_factor(
        self,
        db: AsyncSession,
        user_id: int,
        problem_id: int,
        current_submission: Submission,
    ) -> float:
        """Calculate attempt factor giving stronger evidence for passing with fewer failed attempts.

        Formula:
            attempt_factor = max(0.50, 1.0 / (1.0 + 0.15 * failed_attempts_count))
        Bounded in [0.50, 1.00].
        """
        stmt_failed = select(func.count()).select_from(Submission).where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
            Submission.status != "PASSED",
        )
        if current_submission and current_submission.id:
            stmt_failed = stmt_failed.where(Submission.id < current_submission.id)

        failed_count = (await db.execute(stmt_failed)).scalar() or 0
        factor = 1.0 / (1.0 + ATTEMPT_DECAY_RATE * failed_count)
        return max(ATTEMPT_FACTOR_MIN, min(ATTEMPT_FACTOR_MAX, factor))

    def calculate_recency_factor(self, submission: Submission) -> float:
        """Calculate recency factor giving higher weight to recent submission evidence.

        Formula:
            recency_factor = max(0.70, 1.0 - 0.01 * age_days)
        Bounded in [0.70, 1.00].
        """
        if not submission or not submission.created_at:
            return 1.0

        now = datetime.now(timezone.utc)
        created_at = submission.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        age_seconds = (now - created_at).total_seconds()
        age_days = max(0.0, age_seconds / 86400.0)

        factor = 1.0 - RECENCY_DECAY_PER_DAY * age_days
        return max(RECENCY_FACTOR_MIN, min(RECENCY_FACTOR_MAX, factor))

    async def initialize_skills_from_diagnostic(
        self,
        db: AsyncSession,
        user_id: int,
        assessment: DiagnosticAssessment,
    ) -> List[SkillProfile]:
        """Create or update 12 SKILL_PROFILE rows for user based on diagnostic completion.

        Behavior:
            - If profile does not exist: Creates new SKILL_PROFILE row with initial score.
            - If profile already exists: Preserves existing accumulated skill_score, skill_level,
              problems_solved, and total_points to avoid overwriting coding evidence. Updates
              confidence only if diagnostic provides higher evidence.
        """
        # Eagerly load assessment responses, problems, and topics
        stmt_ass = (
            select(DiagnosticAssessment)
            .options(
                selectinload(DiagnosticAssessment.responses)
                .selectinload(DiagnosticResponse.problem)
                .selectinload(Problem.topics)
            )
            .where(DiagnosticAssessment.id == assessment.id)
        )
        loaded_ass = (await db.execute(stmt_ass)).scalar_one_or_none()
        if loaded_ass:
            assessment = loaded_ass

        # Fetch all 12 topics
        stmt_topics = select(Topic).order_by(Topic.id.asc())
        all_topics = (await db.execute(stmt_topics)).scalars().all()

        # Group diagnostic responses by topic_id
        topic_diag_stats: Dict[int, Dict[str, int]] = {}
        if assessment.responses:
            for resp in assessment.responses:
                prob = resp.problem
                if not prob or not prob.topics:
                    continue
                t_id = prob.topics[0].id
                if t_id not in topic_diag_stats:
                    topic_diag_stats[t_id] = {"total": 0, "correct": 0}
                topic_diag_stats[t_id]["total"] += 1
                if resp.is_correct:
                    topic_diag_stats[t_id]["correct"] += 1

        updated_profiles: List[SkillProfile] = []

        for topic in all_topics:
            t_id = topic.id

            stmt_sp = select(SkillProfile).where(
                SkillProfile.user_id == user_id,
                SkillProfile.topic_id == t_id,
            )
            sp = (await db.execute(stmt_sp)).scalar_one_or_none()

            if t_id in topic_diag_stats:
                stats = topic_diag_stats[t_id]
                tot = stats["total"]
                corr = stats["correct"]
                accuracy = (corr / tot) if tot > 0 else 0.0
                init_score = round(min(100.0, max(0.0, accuracy * 65.0 + 15.0)), 2)
                init_conf = round(DIAGNOSTIC_CONFIDENCE_INC, 2)
            else:
                init_score = DEFAULT_UNTESTED_SKILL
                init_conf = DEFAULT_UNTESTED_CONFIDENCE

            level_name = compute_skill_level_name(init_score)

            if sp is None:
                # Initialize new skill profile
                sp = SkillProfile(
                    user_id=user_id,
                    topic_id=t_id,
                    skill_score=init_score,
                    skill_level=level_name,
                    confidence=init_conf,
                    problems_solved=0,
                    total_points=0,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(sp)
            else:
                # Profile exists: preserve existing accumulated skill_score, skill_level,
                # problems_solved, and total_points; update confidence if diagnostic provides higher evidence.
                sp.confidence = max(sp.confidence, init_conf)
                sp.updated_at = datetime.now(timezone.utc)

            updated_profiles.append(sp)

        await db.flush()
        return updated_profiles

    async def process_submission_for_skills(
        self,
        db: AsyncSession,
        submission: Submission,
    ) -> List[SkillProfile]:
        """Update skill profiles for the problem's topics upon coding submission evaluation.

        Idempotency:
            If submission.is_processed_for_skills is True, returns existing topic skill profiles
            without re-applying changes to problems_solved, total_points, skill_score, or confidence.
        """
        if not submission or not submission.problem_id:
            return []

        user_id = submission.user_id

        # Fetch problem with topics
        stmt_prob = (
            select(Problem)
            .options(selectinload(Problem.topics))
            .where(Problem.id == submission.problem_id)
        )
        problem = (await db.execute(stmt_prob)).scalar_one_or_none()
        if not problem:
            return []

        topics = problem.topics or []

        # Idempotency check
        if submission.is_processed_for_skills:
            existing_profiles: List[SkillProfile] = []
            for topic in topics:
                stmt_sp = select(SkillProfile).where(
                    SkillProfile.user_id == user_id,
                    SkillProfile.topic_id == topic.id,
                )
                sp = (await db.execute(stmt_sp)).scalar_one_or_none()
                if sp:
                    existing_profiles.append(sp)
            return existing_profiles

        diff_str = problem.difficulty.value if hasattr(problem.difficulty, 'value') else str(problem.difficulty)

        # Check if problem was previously solved by this user
        stmt_prev = select(Submission).where(
            Submission.user_id == user_id,
            Submission.problem_id == problem.id,
            Submission.status == "PASSED",
            Submission.id != submission.id,
        )
        prev_passed = (await db.execute(stmt_prev)).scalars().first()
        is_newly_solved = (submission.status == "PASSED" and prev_passed is None)

        attempt_factor = await self.calculate_attempt_factor(db, user_id, problem.id, submission)
        recency_factor = self.calculate_recency_factor(submission)

        updated_profiles: List[SkillProfile] = []

        for topic in topics:
            t_id = topic.id

            stmt_sp = select(SkillProfile).where(
                SkillProfile.user_id == user_id,
                SkillProfile.topic_id == t_id,
            )
            sp = (await db.execute(stmt_sp)).scalar_one_or_none()

            if sp is None:
                sp = SkillProfile(
                    user_id=user_id,
                    topic_id=t_id,
                    skill_score=DEFAULT_UNTESTED_SKILL,
                    skill_level=compute_skill_level_name(DEFAULT_UNTESTED_SKILL),
                    confidence=DEFAULT_UNTESTED_CONFIDENCE,
                    problems_solved=0,
                    total_points=0,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(sp)
                await db.flush()

            if is_newly_solved:
                sp.problems_solved += 1
                sp.total_points += POINTS_MAP.get(diff_str, 10)

            diff_rating = DIFFICULTY_BASE_RATING.get(diff_str, 35.0)
            diff_weight = DIFFICULTY_WEIGHT.get(diff_str, 1.0)

            if submission.status == "PASSED":
                learning_rate = 0.25 / (1.0 + 0.1 * sp.problems_solved)
                base_delta = (diff_rating - sp.skill_score) * learning_rate * (diff_weight / 2.0)
                min_increase = 2.0 * diff_weight if is_newly_solved else 0.5
                raw_delta = max(min_increase, base_delta) if diff_rating > sp.skill_score else base_delta

                actual_delta = raw_delta * attempt_factor * recency_factor
                sp.skill_score = round(min(100.0, max(0.0, sp.skill_score + actual_delta)), 2)
                sp.confidence = min(1.0, round(sp.confidence + SUBMISSION_CONFIDENCE_INC * recency_factor, 2))
            else:
                penalty = 1.5 * recency_factor
                sp.skill_score = round(max(0.0, sp.skill_score - penalty), 2)
                sp.confidence = min(1.0, round(sp.confidence + 0.02 * recency_factor, 2))

            sp.skill_level = compute_skill_level_name(sp.skill_score)
            sp.updated_at = datetime.now(timezone.utc)
            updated_profiles.append(sp)

        # Mark submission as processed for skills
        submission.is_processed_for_skills = True
        await db.flush()
        return updated_profiles
