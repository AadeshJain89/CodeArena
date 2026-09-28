from datetime import date, datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user_gamification import UserGamification
from app.models.submission import Submission
from app.models.problem import Problem, ProblemDifficulty

# Deterministic XP rewards by problem difficulty
XP_REWARDS = {
    ProblemDifficulty.EASY: 10,
    ProblemDifficulty.MEDIUM: 25,
    ProblemDifficulty.HARD: 50,
    "EASY": 10,
    "MEDIUM": 25,
    "HARD": 50,
}

# Deterministic badge rules
BADGE_RULES = [
    ("FIRST_SOLVE", lambda ps, streak: ps >= 1),
    ("FIVE_SOLVES", lambda ps, streak: ps >= 5),
    ("TEN_SOLVES", lambda ps, streak: ps >= 10),
    ("THREE_DAY_STREAK", lambda ps, streak: streak >= 3),
    ("SEVEN_DAY_STREAK", lambda ps, streak: streak >= 7),
]


class GamificationService:
    @staticmethod
    def calculate_level(xp: int) -> int:
        """
        Calculate user level deterministically.
        Formula: level = 1 + floor(xp / 100)
        - 0-99 XP -> Level 1
        - 100-199 XP -> Level 2
        - 200-299 XP -> Level 3
        """
        if xp < 0:
            xp = 0
        return 1 + (xp // 100)

    async def get_or_create_user_gamification(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> UserGamification:
        """
        Fetch the single UserGamification record for user_id.
        If none exists, safely initialize a default record.
        """
        stmt = select(UserGamification).where(UserGamification.user_id == user_id)
        result = await db.execute(stmt)
        gamification = result.scalar_one_or_none()

        if gamification is None:
            gamification = UserGamification(
                user_id=user_id,
                xp=0,
                level=1,
                problems_solved=0,
                successful_submissions=0,
                current_streak=0,
                longest_streak=0,
                last_activity_date=None,
                badges=[],
            )
            db.add(gamification)
            await db.flush()

        return gamification

    async def process_submission_for_gamification(
        self,
        db: AsyncSession,
        submission: Submission,
    ) -> UserGamification:
        """
        Update user gamification stats after a submission is evaluated.

        Distinction:
        - successful_submissions: incremented for EVERY PASSED submission.
        - problems_solved: incremented ONLY on the first PASSED solve of a unique problem.
        - XP: awarded ONLY on the first PASSED solve of a unique problem.
        - Streak: tracked by calendar date. Same-day PASSED submissions do NOT increment streak again.
        """
        if submission.status != "PASSED":
            return await self.get_or_create_user_gamification(db, submission.user_id)

        gamification = await self.get_or_create_user_gamification(db, submission.user_id)

        # 1. Count every PASSED submission event
        gamification.successful_submissions += 1

        # 2. Check if this problem was already passed by this user in prior submissions
        stmt = select(func.count(Submission.id)).where(
            Submission.user_id == submission.user_id,
            Submission.problem_id == submission.problem_id,
            Submission.status == "PASSED",
            Submission.id != submission.id,
        )
        count_prev_passed = (await db.execute(stmt)).scalar_one()
        is_first_solve = (count_prev_passed == 0)

        if is_first_solve:
            gamification.problems_solved += 1

            # Determine problem difficulty and XP reward
            problem = submission.problem
            if problem is None:
                stmt_prob = select(Problem).where(Problem.id == submission.problem_id)
                res_prob = await db.execute(stmt_prob)
                problem = res_prob.scalar_one_or_none()

            diff_key = problem.difficulty if problem else "EASY"
            xp_gained = XP_REWARDS.get(diff_key, 10)
            gamification.xp += xp_gained
            gamification.level = self.calculate_level(gamification.xp)

        # 3. Streak processing based on calendar date
        activity_date: date
        if submission.created_at:
            activity_date = submission.created_at.date()
        else:
            activity_date = datetime.now(timezone.utc).date()

        last_date = gamification.last_activity_date

        if last_date is None:
            gamification.current_streak = 1
            gamification.last_activity_date = activity_date
        elif activity_date == last_date:
            # Same calendar day: streak stays unchanged
            pass
        elif activity_date == last_date + timedelta(days=1):
            # Consecutive calendar day: increment streak
            gamification.current_streak += 1
            gamification.last_activity_date = activity_date
        elif activity_date > last_date + timedelta(days=1):
            # Missed one or more days: reset streak to 1
            gamification.current_streak = 1
            gamification.last_activity_date = activity_date

        # Update longest streak
        if gamification.current_streak > gamification.longest_streak:
            gamification.longest_streak = gamification.current_streak

        # 4. Check and award achievements/badges
        current_badges = set(gamification.badges or [])
        for badge_name, rule_fn in BADGE_RULES:
            if rule_fn(gamification.problems_solved, gamification.current_streak):
                current_badges.add(badge_name)
        gamification.badges = list(current_badges)

        return gamification
