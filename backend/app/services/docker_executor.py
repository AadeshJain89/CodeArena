import base64
import time
import docker
from docker.errors import DockerException, APIError
from app.core.config import settings

# Initialize Docker client lazily or globally
_docker_client = None


def get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        try:
            _docker_client = docker.from_env()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {str(e)}")
    return _docker_client


class DockerExecutor:
    """Isolated Docker container execution service for untrusted code."""

    def __init__(self):
        self.client = get_docker_client()

    def execute_python(
        self,
        source_code: str,
        stdin_input: str,
        timeout_seconds: float = None,
    ) -> dict:
        """
        Execute Python source code inside a temporary, hard-sandboxed Docker container.
        
        Security Restrictions Enforced:
        - Network disabled (--network none)
        - Memory limit (e.g. 128MB)
        - CPU limit (1.0 CPU)
        - PID limit (64 processes max)
        - Drop ALL Linux capabilities (--cap-drop ALL)
        - Prevent privilege escalation (--security-opt no-new-privileges)
        - Read-only root filesystem with tmpfs on /tmp
        - No host filesystem mounts
        - Non-root user
        """
        if timeout_seconds is None:
            timeout_seconds = settings.CODE_EXECUTION_TIMEOUT_SECONDS

        b64_code = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
        b64_stdin = base64.b64encode(stdin_input.encode("utf-8")).decode("utf-8")

        # Python wrapper runner script executed inside container
        runner_script = f"""import sys, io, base64, ast, inspect

code_str = base64.b64decode('{b64_code}').decode('utf-8')
stdin_str = base64.b64decode('{b64_stdin}').decode('utf-8')

# Redirect sys.stdin and capture sys.stdout
sys.stdin = io.StringIO(stdin_str)
stdout_buffer = io.StringIO()
sys.stdout = stdout_buffer

global_scope = {{'__name__': '__main__'}}

try:
    exec(code_str, global_scope)

    # If code produced output on stdout, use it
    output = stdout_buffer.getvalue().strip()
    
    # If no stdout produced but solve function exists, invoke solve with parsed stdin
    if not output and 'solve' in global_scope and callable(global_scope['solve']):
        solve_func = global_scope['solve']
        raw_lines = [line.strip() for line in stdin_str.strip().split('\\n') if line.strip()]
        
        parsed_args = []
        for line in raw_lines:
            try:
                # Attempt to parse line as literal int, list, etc.
                val = ast.literal_eval(line)
                parsed_args.append(val)
            except Exception:
                # Fallback to string or list of ints/strings
                parts = line.split()
                if all(p.lstrip('-').isdigit() for p in parts if p):
                    parsed_args.append([int(p) for p in parts])
                else:
                    parsed_args.append(line)
        
        # Call solve function
        res = solve_func(*parsed_args[:len(inspect.signature(solve_func).parameters)])
        if res is not None:
            if isinstance(res, (list, tuple)):
                output = " ".join(str(x) for x in res)
            elif isinstance(res, bool):
                output = str(res).lower()
            else:
                output = str(res)

    # Print final output to actual stdout
    sys.__stdout__.write(output)
    sys.__stdout__.flush()

except Exception as err:
    sys.__stderr__.write(f"{{type(err).__name__}}: {{err}}")
    sys.__stderr__.flush()
    sys.exit(1)
"""

        container = None
        start_time = time.time()

        try:
            container = self.client.containers.create(
                image=settings.PYTHON_DOCKER_IMAGE,
                command=["python3", "-c", runner_script],
                network_mode="none",  # 1. No network access
                mem_limit=f"{settings.CODE_EXECUTION_MEMORY_LIMIT_MB}m",  # 3. Memory limit
                nano_cpus=int(settings.CODE_EXECUTION_CPU_LIMIT * 1e9),  # 4. CPU limit
                pids_limit=settings.CODE_EXECUTION_PIDS_LIMIT,  # 5. PID limit
                cap_drop=["ALL"],  # 7. Drop all capabilities
                security_opt=["no-new-privileges:true"],  # 8. No privilege escalation
                read_only=True,  # 9. Read-only root filesystem
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},  # Restricted writable /tmp
                user="1000:1000",  # 2. Non-root user
                environment={},  # 16. No host environment leakage
            )

            container.start()

            # Enforce execution timeout
            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result.get("StatusCode", 1)
                timed_out = False
            except Exception:
                # Container timed out
                timed_out = True
                exit_code = -1
                try:
                    container.stop(timeout=1)
                except Exception:
                    pass

            exec_duration_ms = round((time.time() - start_time) * 1000, 2)

            if timed_out:
                return {
                    "status": "TIME_LIMIT_EXCEEDED",
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout_seconds} seconds",
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 0.0,
                    "exit_code": -1,
                }

            # Retrieve container logs (stdout and stderr separated or combined)
            stdout_logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr_logs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            # Truncate output if it exceeds max allowed output bytes
            max_bytes = settings.CODE_EXECUTION_MAX_OUTPUT_BYTES
            if len(stdout_logs.encode("utf-8")) > max_bytes:
                stdout_logs = stdout_logs[:max_bytes] + "\n[Output Truncated: Max output size exceeded]"

            if exit_code == 0:
                return {
                    "status": "SUCCESS",
                    "stdout": stdout_logs.strip(),
                    "stderr": stderr_logs.strip(),
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 15.0,  # Estimated container memory footprint
                    "exit_code": 0,
                }
            else:
                return {
                    "status": "RUNTIME_ERROR",
                    "stdout": stdout_logs.strip(),
                    "stderr": stderr_logs.strip() or "Runtime execution failed",
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 15.0,
                    "exit_code": exit_code,
                }

        finally:
            # MANDATORY CLEANUP: Always remove temporary execution container
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def execute_cpp(
        self,
        source_code: str,
        stdin_input: str,
        timeout_seconds: float = None,
    ) -> dict:
        """
        Execute C++ source code inside a temporary, hard-sandboxed Docker container.
        Compiles with g++ and executes inside container.
        """
        if timeout_seconds is None:
            timeout_seconds = settings.CODE_EXECUTION_TIMEOUT_SECONDS

        b64_code = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
        b64_stdin = base64.b64encode(stdin_input.encode("utf-8")).decode("utf-8")

        # C++ compilation and execution runner shell script
        compile_and_run_script = f"""
mkdir -p /tmp/cpp_build && cd /tmp/cpp_build
echo "{b64_code}" | base64 -d > solution.cpp
echo "{b64_stdin}" | base64 -d > input.txt

g++ -O2 solution.cpp -o solution 2> compile_err.txt
if [ $? -ne 0 ]; then
    cat compile_err.txt >&2
    exit 42
fi

./solution < input.txt
"""

        container = None
        start_time = time.time()

        try:
            container = self.client.containers.create(
                image=settings.CPP_DOCKER_IMAGE,
                command=["sh", "-c", compile_and_run_script],
                network_mode="none",
                mem_limit=f"{settings.CODE_EXECUTION_MEMORY_LIMIT_MB}m",
                nano_cpus=int(settings.CODE_EXECUTION_CPU_LIMIT * 1e9),
                pids_limit=settings.CODE_EXECUTION_PIDS_LIMIT,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "rw,exec,nosuid,size=64m"},
                user="1000:1000",
                environment={},
            )

            container.start()

            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result.get("StatusCode", 1)
                timed_out = False
            except Exception:
                timed_out = True
                exit_code = -1
                try:
                    container.stop(timeout=1)
                except Exception:
                    pass

            exec_duration_ms = round((time.time() - start_time) * 1000, 2)

            if timed_out:
                return {
                    "status": "TIME_LIMIT_EXCEEDED",
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout_seconds} seconds",
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 0.0,
                    "exit_code": -1,
                }

            stdout_logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr_logs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            if exit_code == 42:
                return {
                    "status": "COMPILATION_ERROR",
                    "stdout": "",
                    "stderr": stderr_logs.strip() or "C++ Compilation Error",
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 0.0,
                    "exit_code": 42,
                }
            elif exit_code == 0:
                return {
                    "status": "SUCCESS",
                    "stdout": stdout_logs.strip(),
                    "stderr": stderr_logs.strip(),
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 12.0,
                    "exit_code": 0,
                }
            else:
                return {
                    "status": "RUNTIME_ERROR",
                    "stdout": stdout_logs.strip(),
                    "stderr": stderr_logs.strip() or "Runtime execution failed",
                    "execution_time_ms": exec_duration_ms,
                    "memory_used_mb": 12.0,
                    "exit_code": exit_code,
                }

        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
