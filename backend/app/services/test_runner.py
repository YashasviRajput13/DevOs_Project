"""
test_runner.py
==============
Controlled test execution service — Milestone 5.

Safety contract
---------------
* Only commands from ALLOWED_COMMANDS may be executed.
* subprocess is called with shell=False, explicit argv list, timeout.
* The workspace_path is validated before use.
* No LLM-supplied strings are ever passed to the shell.
* stdout/stderr are redacted for obvious secrets.
* stdout/stderr are capped at MAX_OUTPUT_CHARS characters.
* Orphaned processes are killed on timeout via proc.kill().
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.change_audit import ChangeAuditLog
from app.models.file import File
from app.models.test_execution import TestExecutionLog

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 300   # seconds
MAX_OUTPUT_CHARS = 16_000

# Secret-like pattern — redact before returning
_SECRET_RE = re.compile(
    r"""(?i)(api[_-]?key|token|password|secret|authorization|bearer|private[_-]?key)"""
    r"""[\s:='"]+([^\s'"&]{6,})""",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Allowed test commands (explicit allowlist — no arbitrary strings)
# ---------------------------------------------------------------------------

# Each entry: (executable, [fixed_args...])
# Variable parts (test file paths) are appended only after validation.

_PYTEST_BASE = ["pytest"]
_UNITTEST_BASE = ["python", "-m", "unittest"]
_NPM_TEST_BASE = ["npm", "test", "--"]
_NPM_RUN_TEST_BASE = ["npm", "run", "test"]
_JEST_BASE = ["npx", "jest"]
_VITEST_BASE = ["npx", "vitest", "run"]

ALLOWED_FRAMEWORKS: dict[str, dict[str, Any]] = {
    "pytest":    {"base": _PYTEST_BASE,    "language": "python"},
    "unittest":  {"base": _UNITTEST_BASE,  "language": "python"},
    "jest":      {"base": _JEST_BASE,      "language": "javascript"},
    "vitest":    {"base": _VITEST_BASE,    "language": "javascript"},
    "npm_test":  {"base": _NPM_TEST_BASE,  "language": "javascript"},
}

# Patterns that are NEVER allowed to appear in a test target path
_BLOCKED_TARGET_PATTERNS = re.compile(
    r"""(\.\.|/etc|/bin|/usr|rm\s|del\s|format\s|shutdown|powershell|cmd\s|bash\s|wget|curl|docker|git\s)""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

def detect_framework(files: list[File]) -> dict[str, Any]:
    """
    Inspect indexed file records (no filesystem access required) to
    determine the appropriate test framework and candidate test files.
    """
    paths = {f.path for f in files}
    path_names = {f.path.split("/")[-1].lower(): f.path for f in files}

    test_files: list[str] = [
        f.path for f in files
        if f.name.startswith("test_")
        or f.name.endswith("_test.py")
        or "/tests/" in f.path
        or "/test/" in f.path
    ]

    # Python — pytest preferred
    python_signals = {
        "pytest.ini", "pyproject.toml", "setup.cfg", "conftest.py"
    }
    if any(n in path_names for n in python_signals) or test_files:
        py_tests = [t for t in test_files if t.endswith(".py")]
        return {
            "framework": "pytest",
            "language": "python",
            "tests": py_tests[:20],
            "commands": _build_commands("pytest", py_tests[:5]),
        }

    # JavaScript / TypeScript — jest preferred
    if "package.json" in path_names:
        js_tests = [
            t for t in test_files
            if t.endswith((".js", ".ts", ".jsx", ".tsx"))
        ]
        # Check vitest config
        if any("vitest" in p for p in paths):
            return {
                "framework": "vitest",
                "language": "javascript",
                "tests": js_tests[:20],
                "commands": _build_commands("vitest", js_tests[:5]),
            }
        return {
            "framework": "jest",
            "language": "javascript",
            "tests": js_tests[:20],
            "commands": _build_commands("jest", js_tests[:5]),
        }

    return {
        "framework": None,
        "language": None,
        "tests": [],
        "commands": [],
    }


def _build_commands(framework: str, test_files: list[str]) -> list[list[str]]:
    """Build safe argv lists for the detected framework."""
    base = ALLOWED_FRAMEWORKS.get(framework, {}).get("base", [])
    if not base:
        return []
    if test_files:
        return [base + test_files]
    return [base]


# ---------------------------------------------------------------------------
# Target selection
# ---------------------------------------------------------------------------

def select_targets(
    detection: dict[str, Any],
    changed_files: list[str],
) -> list[str]:
    """
    Choose the most relevant test file(s) for the given changed files.
    Falls back to full test suite if targeted match is not confident.
    """
    all_tests = detection.get("tests", [])
    if not changed_files or not all_tests:
        return all_tests[:10]

    targeted: list[str] = []
    for changed in changed_files:
        stem = changed.split("/")[-1].replace(".py", "").replace(".ts", "").replace(".js", "")
        for test_path in all_tests:
            if stem in test_path:
                if test_path not in targeted:
                    targeted.append(test_path)

    return targeted if targeted else all_tests[:10]


# ---------------------------------------------------------------------------
# Output sanitisation
# ---------------------------------------------------------------------------

def redact_secrets(text: str) -> str:
    """Replace obvious secret values in output with [REDACTED]."""
    return _SECRET_RE.sub(r"\1=[REDACTED]", text)


def cap_output(text: str) -> str:
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + f"\n[...truncated at {MAX_OUTPUT_CHARS} chars]"
    return text


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def validate_workspace(workspace_path: str) -> Path:
    """
    Validate workspace_path is a real directory and does not escape
    via path traversal.  Raises ValueError on any violation.
    """
    p = Path(workspace_path).resolve()

    if not p.exists():
        raise ValueError(f"Workspace path does not exist: {p}")
    if not p.is_dir():
        raise ValueError(f"Workspace path is not a directory: {p}")
    # Ensure it's not pointing at system-sensitive paths
    blocked = ["/etc", "/bin", "/usr/bin", "C:\\Windows", "C:\\System32"]
    for bl in blocked:
        if str(p).startswith(bl):
            raise ValueError(f"Workspace path is in a blocked system directory: {p}")
    return p


def validate_target(target: str) -> None:
    """Raise ValueError if target contains disallowed patterns."""
    if _BLOCKED_TARGET_PATTERNS.search(target):
        raise ValueError(f"Disallowed characters/patterns in test target: {target!r}")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

class TestRunner:
    """
    Executes tests in a controlled, safe manner.
    Never executes arbitrary shell commands.
    Never runs tests without an applied (approved) plan.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(
        self,
        plan_id: str,
        project_id: int,
        repository_id: int,
        workspace_path: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Main entry point.  Returns a structured result dict.
        Persists a TestExecutionLog record regardless of outcome.
        """
        # ── 1. Verify plan was applied ──────────────────────────────
        audit = (
            self.db.query(ChangeAuditLog)
            .filter(ChangeAuditLog.plan_id == plan_id)
            .first()
        )
        if not audit:
            return self._result(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                status="blocked",
                error="Plan not found in audit log.",
            )
        if audit.status != "applied":
            return self._result(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                status="blocked",
                error=f"Cannot run tests: plan status is '{audit.status}'. "
                      "Tests may only run after a plan has been applied.",
            )

        # ── 2. Validate workspace ───────────────────────────────────
        try:
            workspace = validate_workspace(workspace_path)
        except ValueError as exc:
            return self._result(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                status="blocked",
                error=str(exc),
            )

        # ── 3. Detect framework from indexed files ──────────────────
        files: list[File] = (
            self.db.query(File)
            .filter(File.repository_id == repository_id)
            .all()
        )

        if not files:
            return self._result(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                status="not_available",
                error="Repository has no indexed files.",
            )

        detection = detect_framework(files)
        framework = detection.get("framework")

        if not framework or framework not in ALLOWED_FRAMEWORKS:
            return self._result(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                status="not_available",
                error="No supported test framework detected in this repository.",
                framework=framework,
            )

        # ── 4. Select targets ───────────────────────────────────────
        import json as _json
        try:
            changed_files: list[str] = _json.loads(audit.target_files or "[]")
        except Exception:
            changed_files = []

        targets = select_targets(detection, changed_files)

        # Validate each target
        safe_targets: list[str] = []
        for t in targets:
            try:
                validate_target(t)
                safe_targets.append(t)
            except ValueError as exc:
                logger.warning("Skipping unsafe test target: %s", exc)

        # ── 5. Build command ────────────────────────────────────────
        base_cmd = ALLOWED_FRAMEWORKS[framework]["base"]
        argv = base_cmd + safe_targets if safe_targets else base_cmd

        # ── 6. Execute ──────────────────────────────────────────────
        start = time.monotonic()
        stdout_text = ""
        stderr_text = ""
        exit_code: int | None = None
        status = "error"

        try:
            safe_env = {k: v for k, v in os.environ.items() if not re.search(r'(?i)(api[_-]?key|token|password|secret)', k)}
            proc = subprocess.Popen(
                argv,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,          # NEVER use shell=True
                text=True,
                env=safe_env,         # inherit safe env, stripped of secrets
            )
            try:
                stdout_text, stderr_text = proc.communicate(timeout=timeout)
                exit_code = proc.returncode
                status = "passed" if exit_code == 0 else "failed"
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                status = "timeout"

        except FileNotFoundError:
            status = "not_available"
            stderr_text = (
                f"Executable '{argv[0]}' not found in PATH. "
                "Ensure the test framework is installed in the environment."
            )
        except Exception as exc:
            status = "error"
            stderr_text = str(exc)

        duration = time.monotonic() - start

        # ── 7. Redact & cap output ──────────────────────────────────
        stdout_clean = cap_output(redact_secrets(stdout_text))
        stderr_clean = cap_output(redact_secrets(stderr_text))

        # ── 8. Parse test counts (pytest-style) ────────────────────
        tests_run, tests_failed = self._parse_pytest_summary(stdout_clean)

        # ── 9. Persist log ──────────────────────────────────────────
        self._persist(
            plan_id=plan_id,
            project_id=project_id,
            repository_id=repository_id,
            framework=framework,
            tests_selected=safe_targets,
            status=status,
            exit_code=exit_code,
            duration=duration,
            tests_run=tests_run,
            tests_failed=tests_failed,
            stdout=stdout_clean,
            stderr=stderr_clean,
        )

        return {
            "status": status,
            "framework": framework,
            "command": argv,
            "exit_code": exit_code,
            "duration_seconds": round(duration, 2),
            "stdout": stdout_clean,
            "stderr": stderr_clean,
            "tests_run": tests_run,
            "tests_failed": tests_failed,
            "workspace": str(workspace),
        }

    # ------------------------------------------------------------------
    # pytest summary parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pytest_summary(output: str) -> tuple[int | None, int | None]:
        """
        Very lightweight parser for pytest summary lines like:
        '5 passed', '3 failed, 2 passed', '1 error'
        """
        passed = failed = None
        m_passed = re.search(r"(\d+)\s+passed", output)
        m_failed = re.search(r"(\d+)\s+failed", output)
        m_error  = re.search(r"(\d+)\s+error", output)
        if m_passed:
            passed = int(m_passed.group(1))
        if m_failed:
            failed = int(m_failed.group(1))
        elif m_error:
            failed = int(m_error.group(1))
        total = (passed or 0) + (failed or 0)
        return (total if total else None), (failed if failed is not None else None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _persist(
        self,
        plan_id: str,
        project_id: int,
        repository_id: int,
        framework: str | None,
        tests_selected: list[str],
        status: str,
        exit_code: int | None,
        duration: float,
        tests_run: int | None,
        tests_failed: int | None,
        stdout: str,
        stderr: str,
    ) -> None:
        import json as _json
        try:
            record = TestExecutionLog(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                framework=framework,
                tests_selected=_json.dumps(tests_selected),
                status=status,
                exit_code=exit_code,
                duration_seconds=round(duration, 3),
                tests_run=tests_run,
                tests_failed=tests_failed,
                stdout_snippet=stdout[:4000],
                stderr_snippet=stderr[:4000],
            )
            self.db.add(record)
            self.db.commit()
        except Exception:
            logger.exception("Failed to persist test execution log for plan %s", plan_id)
            self.db.rollback()

    @staticmethod
    def _result(
        plan_id: str,
        project_id: int,
        repository_id: int,
        status: str,
        error: str = "",
        framework: str | None = None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "framework": framework,
            "command": [],
            "exit_code": None,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": error,
            "tests_run": None,
            "tests_failed": None,
            "error": error,
        }
