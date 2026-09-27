from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.problem import Problem
from app.models.submission import Submission
from app.models.submission_test_result import SubmissionTestResult
from app.schemas.execution import ExecutionRequest
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionSummaryResponse,
    SubmissionTestResultResponse,
)
from app.services.execution_service import ExecutionService


class SubmissionService:
    def __init__(self):
        self.execution_service = ExecutionService()

    async def create_submission(
        self,
        db: AsyncSession,
        user_id: int,
        request: SubmissionCreate,
    ) -> SubmissionResponse:
        """Evaluate submitted code, persist Submission & SubmissionTestResult records, and return response."""
        # 1. Fetch problem and test cases first
        stmt = (
            select(Problem)
            .options(selectinload(Problem.test_cases))
            .where(Problem.id == request.problem_id)
        )
        result = await db.execute(stmt)
        problem = result.scalar_one_or_none()

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem with ID {request.problem_id} not found",
            )

        # 2. Execute code via existing ExecutionService
        exec_req = ExecutionRequest(
            problem_id=request.problem_id,
            language=request.language,
            source_code=request.source_code,
        )
        exec_res = await self.execution_service.execute_code(exec_req, db)

        # 3. Create Submission record
        submission = Submission(
            user_id=user_id,
            problem_id=request.problem_id,
            language=exec_res.language,
            source_code=request.source_code,
            status=exec_res.status,
            total_tests=exec_res.total_tests,
            passed_tests=exec_res.passed_tests,
            failed_tests=exec_res.failed_tests,
            execution_time_ms=exec_res.execution_time_ms,
            memory_used_mb=exec_res.memory_used_mb,
        )
        db.add(submission)
        await db.flush()  # Obtain submission.id

        # 4. Create SubmissionTestResult records
        db_test_results: List[SubmissionTestResultResponse] = []
        test_cases_list = problem.test_cases

        for res_item in exec_res.test_results:
            tc = test_cases_list[res_item.test_number - 1]
            
            # Security check: Mask hidden test case outputs
            actual_out = res_item.actual_output if not tc.is_hidden else None
            expected_out = res_item.expected_output if not tc.is_hidden else None
            err_msg = res_item.error_message if not tc.is_hidden or res_item.status == "COMPILATION_ERROR" else None

            str_item = SubmissionTestResult(
                submission_id=submission.id,
                test_case_id=tc.test_case_id,
                status=res_item.status,
                execution_time_ms=res_item.execution_time_ms,
                actual_output=actual_out,
                expected_output=expected_out,
                error_message=err_msg,
            )
            db.add(str_item)
            await db.flush()

            db_test_results.append(
                SubmissionTestResultResponse(
                    id=str_item.id,
                    test_case_id=tc.test_case_id,
                    status=res_item.status,
                    execution_time_ms=res_item.execution_time_ms,
                    actual_output=actual_out,
                    expected_output=expected_out,
                    error_message=err_msg,
                    is_hidden=tc.is_hidden,
                )
            )

        await db.commit()
        await db.refresh(submission)

        return SubmissionResponse(
            id=submission.id,
            user_id=submission.user_id,
            problem_id=submission.problem_id,
            problem_title=problem.title,
            language=submission.language,
            source_code=submission.source_code,
            status=submission.status,
            total_tests=submission.total_tests,
            passed_tests=submission.passed_tests,
            failed_tests=submission.failed_tests,
            execution_time_ms=submission.execution_time_ms,
            memory_used_mb=submission.memory_used_mb,
            created_at=submission.created_at,
            test_results=db_test_results,
        )

    async def get_user_submissions(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> List[SubmissionSummaryResponse]:
        """Return list of authenticated user's submissions (newest first)."""
        stmt = (
            select(Submission)
            .options(selectinload(Submission.problem))
            .where(Submission.user_id == user_id)
            .order_by(Submission.created_at.desc(), Submission.id.desc())
        )
        result = await db.execute(stmt)
        submissions = result.scalars().all()

        return [
            SubmissionSummaryResponse(
                id=sub.id,
                problem_id=sub.problem_id,
                problem_title=sub.problem.title if sub.problem else f"Problem #{sub.problem_id}",
                language=sub.language,
                status=sub.status,
                passed_tests=sub.passed_tests,
                total_tests=sub.total_tests,
                execution_time_ms=sub.execution_time_ms,
                created_at=sub.created_at,
            )
            for sub in submissions
        ]

    async def get_user_submission_detail(
        self,
        db: AsyncSession,
        user_id: int,
        submission_id: int,
    ) -> SubmissionResponse:
        """Fetch submission details for authenticated user, protecting user privacy."""
        stmt = (
            select(Submission)
            .options(
                selectinload(Submission.problem),
                selectinload(Submission.test_results).selectinload(SubmissionTestResult.test_case),
            )
            .where(Submission.id == submission_id)
        )
        result = await db.execute(stmt)
        submission = result.scalar_one_or_none()

        if submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission with ID {submission_id} not found",
            )

        if submission.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this submission",
            )

        test_results_response = []
        for tr in submission.test_results:
            is_hidden = tr.test_case.is_hidden if tr.test_case else False
            test_results_response.append(
                SubmissionTestResultResponse(
                    id=tr.id,
                    test_case_id=tr.test_case_id,
                    status=tr.status,
                    execution_time_ms=tr.execution_time_ms,
                    actual_output=tr.actual_output if not is_hidden else None,
                    expected_output=tr.expected_output if not is_hidden else None,
                    error_message=tr.error_message if not is_hidden or tr.status == "COMPILATION_ERROR" else None,
                    is_hidden=is_hidden,
                )
            )

        return SubmissionResponse(
            id=submission.id,
            user_id=submission.user_id,
            problem_id=submission.problem_id,
            problem_title=submission.problem.title if submission.problem else f"Problem #{submission.problem_id}",
            language=submission.language,
            source_code=submission.source_code,
            status=submission.status,
            total_tests=submission.total_tests,
            passed_tests=submission.passed_tests,
            failed_tests=submission.failed_tests,
            execution_time_ms=submission.execution_time_ms,
            memory_used_mb=submission.memory_used_mb,
            created_at=submission.created_at,
            test_results=test_results_response,
        )
