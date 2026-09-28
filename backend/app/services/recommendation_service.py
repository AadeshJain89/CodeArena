from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.models.problem import Problem, ProblemDifficulty
from app.models.topic import Topic
from app.models.submission import Submission
from app.models.skill_profile import SkillProfile
from app.models.recommendation import Recommendation
from app.services.slre_service import DEFAULT_UNTESTED_SKILL, DEFAULT_UNTESTED_CONFIDENCE


# Centralized Scoring Constants
WEIGHT_SKILL_GAP: float = 30.0
WEIGHT_CONFIDENCE: float = 20.0
WEIGHT_DIFFICULTY: float = 25.0
WEIGHT_RELEVANCE: float = 15.0
WEIGHT_HISTORY: float = 10.0


def calculate_difficulty_component(skill_score: float, difficulty_str: str) -> float:
    """Calculate personalized difficulty fit score based on topic skill score."""
    diff_upper = difficulty_str.upper()
    if skill_score < 25.0:  # Low skill
        fit = {"EASY": 25.0, "MEDIUM": 10.0, "HARD": 0.0}
    elif skill_score < 45.0:  # Novice skill
        fit = {"EASY": 20.0, "MEDIUM": 22.0, "HARD": 5.0}
    elif skill_score < 65.0:  # Intermediate skill
        fit = {"EASY": 10.0, "MEDIUM": 25.0, "HARD": 15.0}
    elif skill_score < 80.0:  # Advanced skill
        fit = {"EASY": 5.0, "MEDIUM": 20.0, "HARD": 25.0}
    else:  # Expert skill
        fit = {"EASY": 0.0, "MEDIUM": 10.0, "HARD": 25.0}
    return fit.get(diff_upper, 10.0)


class RecommendationService:
    """Personalized Recommendation Engine (SLRE Recommendation Layer).

    Provides deterministic, explainable, rule-based recommendations for the Top 5
    coding problems for an authenticated user based on skill profiles, problem difficulty,
    topic relevance, and submission history.
    """

    async def get_user_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> List[Recommendation]:
        """Fetch valid top 5 recommendations for user, refreshing synchronously if stale or missing."""
        # 1. Fetch existing stored recommendations
        stmt_existing = (
            select(Recommendation)
            .options(selectinload(Recommendation.problem).selectinload(Problem.topics))
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.rank.asc())
        )
        existing_recs = (await db.execute(stmt_existing)).scalars().all()

        is_stale = False
        if existing_recs:
            # Check if any recommended problem has been PASSED since recommendations were generated
            rec_problem_ids = [r.problem_id for r in existing_recs]
            stmt_passed = select(Submission.problem_id).where(
                Submission.user_id == user_id,
                Submission.problem_id.in_(rec_problem_ids),
                Submission.status == "PASSED",
            )
            passed_problem_ids = (await db.execute(stmt_passed)).scalars().all()
            if passed_problem_ids:
                is_stale = True

            # Check if user has submitted any code after recommendations were generated
            latest_gen_at = existing_recs[0].generated_at
            stmt_new_sub = select(func.count()).select_from(Submission).where(
                Submission.user_id == user_id,
                Submission.created_at > latest_gen_at,
            )
            new_sub_count = (await db.execute(stmt_new_sub)).scalar() or 0
            if new_sub_count > 0:
                is_stale = True

        # 2. Return fresh existing recommendations if valid
        if existing_recs and not is_stale:
            return existing_recs

        # 3. Regenerate fresh recommendations synchronously
        return await self.generate_and_store_recommendations(db, user_id=user_id)

    async def generate_and_store_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> List[Recommendation]:
        """Generate deterministic top 5 recommendations, store in DB, and return them."""
        # Delete existing stored recommendations for user
        await db.execute(delete(Recommendation).where(Recommendation.user_id == user_id))
        await db.flush()

        # Fetch user passed problem IDs (must be excluded)
        stmt_passed = select(Submission.problem_id).where(
            Submission.user_id == user_id,
            Submission.status == "PASSED",
        )
        passed_ids = set((await db.execute(stmt_passed)).scalars().all())

        # Fetch candidate problems (exclude is_diagnostic == True and passed problems)
        stmt_problems = (
            select(Problem)
            .options(selectinload(Problem.topics))
            .where(
                Problem.is_diagnostic == False,
            )
            .order_by(Problem.id.asc())
        )
        all_problems = (await db.execute(stmt_problems)).scalars().all()
        candidates = [p for p in all_problems if p.id not in passed_ids]

        if not candidates:
            return []

        # Fetch user skill profiles map
        stmt_skills = select(SkillProfile).where(SkillProfile.user_id == user_id)
        user_skills = (await db.execute(stmt_skills)).scalars().all()
        skills_map = {sp.topic_id: sp for sp in user_skills}

        # Fetch user failed submission counts per problem
        stmt_failed = select(
            Submission.problem_id, func.count(Submission.id)
        ).where(
            Submission.user_id == user_id,
            Submission.status != "PASSED",
        ).group_by(Submission.problem_id)
        failed_counts = dict((await db.execute(stmt_failed)).all())

        scored_candidates = []

        for problem in candidates:
            diff_str = problem.difficulty.value if hasattr(problem.difficulty, 'value') else str(problem.difficulty)

            # Evaluate multi-topic problem: select primary topic with lowest skill score (largest gap)
            primary_topic_name = "General"
            target_skill_score = DEFAULT_UNTESTED_SKILL
            target_confidence = DEFAULT_UNTESTED_CONFIDENCE
            target_solved = 0

            if problem.topics:
                # Find topic with minimum skill_score
                min_score = 101.0
                for topic in problem.topics:
                    sp = skills_map.get(topic.id)
                    score = sp.skill_score if sp else DEFAULT_UNTESTED_SKILL
                    if score < min_score:
                        min_score = score
                        primary_topic_name = topic.name
                        target_skill_score = score
                        target_confidence = sp.confidence if sp else DEFAULT_UNTESTED_CONFIDENCE
                        target_solved = sp.problems_solved if sp else 0
            else:
                primary_topic_name = "General"

            # 1. Skill Gap Component (max 30.0)
            gap = 1.0 - (target_skill_score / 100.0)
            c_gap = WEIGHT_SKILL_GAP * max(0.0, min(1.0, gap))

            # 2. Confidence Component (max 20.0)
            c_conf = WEIGHT_CONFIDENCE * (1.0 - max(0.0, min(1.0, target_confidence)))

            # 3. Difficulty Component (max 25.0)
            c_diff = calculate_difficulty_component(target_skill_score, diff_str)

            # 4. Topic Relevance Component (max 15.0)
            c_rel = WEIGHT_RELEVANCE / (1.0 + 0.5 * target_solved)

            # 5. History Component (max 10.0)
            failed_attempts = failed_counts.get(problem.id, 0)
            if failed_attempts > 0:
                c_hist = 10.0 if failed_attempts <= 3 else 3.0
            else:
                c_hist = 5.0

            total_score = round(c_gap + c_conf + c_diff + c_rel + c_hist, 2)

            # Generate 2 to 3 explainable reasons
            reasons: List[str] = []

            # Reason 1: Skill Gap / Topic State
            if target_skill_score < 40.0:
                reasons.append(f"{primary_topic_name} is currently one of your weaker topics ({round(target_skill_score, 1)}/100).")
            elif target_solved == 0:
                reasons.append(f"This problem targets {primary_topic_name}, where you have limited solved problems.")
            else:
                reasons.append(f"Practicing {primary_topic_name} will help refine your proficiency.")

            # Reason 2: Confidence / Evidence
            if target_confidence < 0.35:
                reasons.append(f"Your evidence/confidence in {primary_topic_name} is still developing.")
            else:
                reasons.append(f"This problem will reinforce your foundation in {primary_topic_name}.")

            # Reason 3: Difficulty fit or History
            if failed_attempts > 0:
                reasons.append(f"You previously attempted this problem ({failed_attempts} failed attempt{'s' if failed_attempts > 1 else ''})—a great chance to solve it!")
            else:
                reasons.append(f"This {diff_str.capitalize()} problem matches your current skill level in {primary_topic_name}.")

            scored_candidates.append({
                "problem": problem,
                "score": total_score,
                "reasons": reasons[:3],  # Bound to 2-3 reasons
            })

        # Sort deterministically: score desc, problem_id asc
        scored_candidates.sort(key=lambda item: (-item["score"], item["problem"].id))

        # Take Top 5
        top_candidates = scored_candidates[:5]

        # Store recommendations in DB
        new_recs: List[Recommendation] = []
        gen_time = datetime.now(timezone.utc)

        for idx, item in enumerate(top_candidates, start=1):
            rec = Recommendation(
                user_id=user_id,
                problem_id=item["problem"].id,
                rank=idx,
                score=item["score"],
                reasons=item["reasons"],
                generated_at=gen_time,
            )
            rec.problem = item["problem"]
            db.add(rec)
            new_recs.append(rec)

        await db.commit()

        # Query and return fresh stored recommendations with eager loaded problem & topics
        stmt_fresh = (
            select(Recommendation)
            .options(selectinload(Recommendation.problem).selectinload(Problem.topics))
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.rank.asc())
        )
        return (await db.execute(stmt_fresh)).scalars().all()
