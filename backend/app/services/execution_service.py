import time
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.schemas.execution import ExecutionRequest, ExecutionResponse, TestResultItem
from app.services.docker_executor import DockerExecutor


def normalize_output(text: str) -> str:
    """Normalize output by trimming trailing spaces and newlines on each line."""
    if text is None:
        return ""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


class ExecutionService:
    def __init__(self):
        self.executor = DockerExecutor()

    async def execute_code(
        self,
        request: ExecutionRequest,
        db: AsyncSession,
    ) -> ExecutionResponse:
        """Fetch problem test cases, run code inside Docker sandbox, compare outputs, and construct response."""
        # 1. Validate source code non-empty
        code = request.source_code.strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source code cannot be empty",
            )

        # 2. Validate source code max size
        if len(code.encode("utf-8")) > settings.CODE_EXECUTION_MAX_SOURCE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source code size exceeds maximum limit of {settings.CODE_EXECUTION_MAX_SOURCE_BYTES} bytes",
            )

        # 3. Validate supported language
        lang = request.language.lower().strip()
        if lang not in ["python", "cpp", "c++"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language '{request.language}'. Supported languages: 'python', 'cpp'",
            )
        if lang == "c++":
            lang = "cpp"

        # 4. Fetch Problem and Test Cases from DB
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

        test_cases: List[TestCase] = problem.test_cases
        if not test_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem '{problem.title}' has no configured test cases",
            )

        test_results: List[TestResultItem] = []
        passed_count = 0
        failed_count = 0
        total_time_ms = 0.0
        overall_status = "PASSED"

        # 5. Execute against each test case
        for idx, tc in enumerate(test_cases, start=1):
            timeout = tc.time_limit_override or settings.CODE_EXECUTION_TIMEOUT_SECONDS

            if lang == "python":
                exec_res = self.executor.execute_python(
                    source_code=code,
                    stdin_input=tc.input,
                    timeout_seconds=timeout,
                )
            else:
                exec_res = self.executor.execute_cpp(
                    source_code=code,
                    stdin_input=tc.input,
                    timeout_seconds=timeout,
                )

            exec_time = exec_res.get("execution_time_ms", 0.0)
            total_time_ms += exec_time
            exec_status = exec_res.get("status")

            if exec_status == "COMPILATION_ERROR":
                overall_status = "COMPILATION_ERROR"
                test_results.append(
                    TestResultItem(
                        test_number=idx,
                        status="COMPILATION_ERROR",
                        is_hidden=tc.is_hidden,
                        execution_time_ms=exec_time,
                        error_message=exec_res.get("stderr"),
                    )
                )
                failed_count += 1
                break  # Stop on compilation error

            elif exec_status == "TIME_LIMIT_EXCEEDED":
                if overall_status == "PASSED":
                    overall_status = "TIME_LIMIT_EXCEEDED"
                failed_count += 1
                test_results.append(
                    TestResultItem(
                        test_number=idx,
                        status="TIME_LIMIT_EXCEEDED",
                        is_hidden=tc.is_hidden,
                        execution_time_ms=exec_time,
                        error_message="Time limit exceeded" if not tc.is_hidden else None,
                    )
                )

            elif exec_status == "RUNTIME_ERROR":
                if overall_status == "PASSED":
                    overall_status = "RUNTIME_ERROR"
                failed_count += 1
                test_results.append(
                    TestResultItem(
                        test_number=idx,
                        status="RUNTIME_ERROR",
                        is_hidden=tc.is_hidden,
                        execution_time_ms=exec_time,
                        error_message=exec_res.get("stderr") if not tc.is_hidden else None,
                    )
                )

            else:
                # Compare output
                actual = normalize_output(exec_res.get("stdout", ""))
                expected = normalize_output(tc.expected_output)

                if actual == expected:
                    passed_count += 1
                    test_results.append(
                        TestResultItem(
                            test_number=idx,
                            status="PASSED",
                            is_hidden=tc.is_hidden,
                            execution_time_ms=exec_time,
                            actual_output=actual if not tc.is_hidden else None,
                            expected_output=expected if not tc.is_hidden else None,
                        )
                    )
                else:
                    failed_count += 1
                    if overall_status == "PASSED":
                        overall_status = "FAILED"
                    test_results.append(
                        TestResultItem(
                            test_number=idx,
                            status="FAILED",
                            is_hidden=tc.is_hidden,
                            execution_time_ms=exec_time,
                            actual_output=actual if not tc.is_hidden else None,
                            expected_output=expected if not tc.is_hidden else None,
                            error_message="Output mismatch" if not tc.is_hidden else None,
                        )
                    )

        return ExecutionResponse(
            status=overall_status,
            language=lang,
            total_tests=len(test_cases),
            passed_tests=passed_count,
            failed_tests=failed_count,
            execution_time_ms=round(total_time_ms, 2),
            memory_used_mb=15.0,
            test_results=test_results,
        )
