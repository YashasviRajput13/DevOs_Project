"""
code_modifier.py
================
Safe code modification service.

Milestone 4 — Safe Code Modification Workflow.

Only modifies File.content records in PostgreSQL (the indexed copy).
Does NOT write arbitrary filesystem paths.
Does NOT execute shell commands.
Does NOT push to GitHub.

Safety enforcement (enforced here, not trusted from caller):
- All target files must belong to the specified repository.
- Paths with ".." are rejected.
- Absolute paths are rejected.
- .env / secret files are rejected.
- .git metadata is rejected.
"""
from __future__ import annotations

import difflib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.change_audit import ChangeAuditLog
from app.models.file import File
from app.models.repository import Repository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# In-memory plan store (ephemeral — lives only for the duration of the process)
# Maps plan_id → plan dict
_PENDING_PLANS: dict[str, dict[str, Any]] = {}

_BLOCKED_PATHS = re.compile(
    r"""(\.env|\.env\.\w+|secrets?|api[_-]?key|password|token|\.git[/\\])""",
    re.IGNORECASE,
)

_MAX_PLAN_SIZE = 20  # max number of file changes per plan


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class CodeModifier:
    """
    Manages change plans and applies approved modifications.
    All operations are scoped to a single repository.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Plan creation
    # ------------------------------------------------------------------

    def create_plan(
        self,
        project_id: int,
        repository_id: int,
        user_request: str,
        summary: str,
        proposed_changes: list[dict[str, Any]],
        tests: list[str] | None = None,
        risks: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Validate and store a change plan.
        Returns a plan dict with a unique plan_id.
        """
        repo = self._get_repo(project_id, repository_id)
        if not repo:
            raise ValueError("Repository not found.")

        # Validate each change
        enriched_changes = []
        for change in proposed_changes[:_MAX_PLAN_SIZE]:
            file_path = change.get("file", "")
            self._validate_path(file_path)

            db_file = self._get_file(repository_id, file_path)
            if not db_file:
                raise ValueError(
                    f"File '{file_path}' was not found in the indexed repository. "
                    "Only indexed files may be modified."
                )

            original_content = db_file.content or ""
            proposed = change.get("proposed_change", "")
            start_line = change.get("start_line")
            end_line = change.get("end_line")

            # Generate diff
            diff = self._generate_diff(
                original=original_content,
                proposed_change=proposed,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
            )

            enriched_changes.append({
                "file": file_path,
                "file_id": db_file.id,
                "start_line": start_line,
                "end_line": end_line,
                "reason": change.get("reason", ""),
                "proposed_change": proposed,
                "diff": diff,
                "original_sha": db_file.sha,  # used to detect unexpected changes
            })

        plan_id = uuid.uuid4().hex

        plan = {
            "plan_id": plan_id,
            "project_id": project_id,
            "repository_id": repository_id,
            "user_request": user_request,
            "summary": summary,
            "changes": enriched_changes,
            "tests": tests or [],
            "risks": risks or [],
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        _PENDING_PLANS[plan_id] = plan

        # Write audit log record
        self._write_audit(
            plan_id=plan_id,
            project_id=project_id,
            repository_id=repository_id,
            user_request=user_request,
            plan_summary=summary,
            target_files=[c["file"] for c in enriched_changes],
            status="pending",
        )

        # Return a copy without internal fields not needed by the API
        return {
            "plan_id": plan_id,
            "summary": summary,
            "changes": [
                {
                    "file": c["file"],
                    "diff": c["diff"],
                    "reason": c["reason"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                }
                for c in enriched_changes
            ],
            "tests": tests or [],
            "risks": risks or [],
        }

    # ------------------------------------------------------------------
    # Apply plan
    # ------------------------------------------------------------------

    def apply_plan(self, plan_id: str, approved: bool) -> dict[str, Any]:
        """
        Apply or reject a pending plan.
        Returns a status dict.
        """
        plan = _PENDING_PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"Plan '{plan_id}' not found or has already been processed.")

        if not approved:
            plan["status"] = "cancelled"
            self._update_audit(plan_id, "cancelled")
            _PENDING_PLANS.pop(plan_id, None)
            return {
                "status": "cancelled",
                "changed_files": []
            }

        project_id = plan["project_id"]
        repository_id = plan["repository_id"]

        # -- Pre-flight validation (Atomic) --
        for change in plan["changes"]:
            file_path = change["file"]
            try:
                self._validate_path(file_path)
            except ValueError as e:
                self._update_audit(plan_id, "failed", error=str(e))
                _PENDING_PLANS.pop(plan_id, None)
                return {"status": "rejected", "reason": str(e), "changed_files": []}

            db_file = self._get_file(repository_id, file_path)
            if not db_file:
                err = f"File '{file_path}' no longer exists."
                self._update_audit(plan_id, "failed", error=err)
                _PENDING_PLANS.pop(plan_id, None)
                return {"status": "rejected", "reason": err, "changed_files": []}

            if db_file.sha != change.get("original_sha"):
                self._update_audit(plan_id, "conflict", error="File hash mismatch")
                _PENDING_PLANS.pop(plan_id, None)
                return {
                    "status": "conflict",
                    "message": "Target file changed after the plan was generated.",
                    "changed_files": []
                }

        # -- Apply changes --
        changed_files: list[str] = []
        try:
            for change in plan["changes"]:
                file_path = change["file"]
                db_file = self._get_file(repository_id, file_path)
                original_content = db_file.content or ""
                new_content = self._apply_change(
                    original=original_content,
                    proposed_change=change["proposed_change"],
                    start_line=change.get("start_line"),
                    end_line=change.get("end_line"),
                )
                db_file.content = new_content
                changed_files.append(file_path)

            self.db.commit()
            plan["status"] = "applied"
            self._update_audit(plan_id, "applied")
        except Exception as exc:
            self.db.rollback()
            plan["status"] = "failed"
            self._update_audit(plan_id, "failed", error=str(exc))
            logger.exception("Failed to apply plan %s", plan_id)
            raise
        finally:
            _PENDING_PLANS.pop(plan_id, None)

        return {
            "status": "changes_applied",
            "changed_files": changed_files,
            "tests_recommended": plan.get("tests", []),
            "tests_executed": False,
        }

    # ------------------------------------------------------------------
    # Diff generation
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_diff(
        original: str,
        proposed_change: str,
        file_path: str,
        start_line: int | None,
        end_line: int | None,
    ) -> str:
        """
        Generate a unified diff between the original file content and the
        version with the proposed_change applied to the specified line range.
        """
        lines = original.splitlines(keepends=True)
        n = len(lines)

        if start_line and end_line:
            s = max(0, start_line - 1)
            e = min(n, end_line)
            new_lines = lines[:s] + [proposed_change + "\n"] + lines[e:]
        else:
            new_lines = [proposed_change + "\n"]

        diff = difflib.unified_diff(
            lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        return "\n".join(diff)

    # ------------------------------------------------------------------
    # Change application
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_change(
        original: str,
        proposed_change: str,
        start_line: int | None,
        end_line: int | None,
    ) -> str:
        """Replace lines [start_line..end_line] with proposed_change."""
        lines = original.splitlines(keepends=True)
        n = len(lines)

        if start_line and end_line:
            s = max(0, start_line - 1)
            e = min(n, end_line)
            replacement = proposed_change if proposed_change.endswith("\n") else proposed_change + "\n"
            new_lines = lines[:s] + [replacement] + lines[e:]
        else:
            # Full replacement
            new_lines = [proposed_change]

        return "".join(new_lines)

    # ------------------------------------------------------------------
    # Safety validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_path(path: str) -> None:
        """Raise ValueError for any disallowed path."""
        if not path:
            raise ValueError("Empty file path is not allowed.")
        if path.startswith("/") or path.startswith("\\") or (len(path) > 1 and path[1] == ":"):
            raise ValueError(f"Absolute paths are not allowed: '{path}'")
        if ".." in path:
            raise ValueError(f"Path traversal is not allowed: '{path}'")
        if _BLOCKED_PATHS.search(path):
            raise ValueError(
                f"Modifications to sensitive files are blocked: '{path}'"
            )

    @staticmethod
    def _validate_content(proposed_change: str) -> None:
        """Reject changes that introduce naked secrets or forbidden executable patterns."""
        lower = proposed_change.lower()
        if "gsk_" in proposed_change or "ghp_" in proposed_change or "sk-ant" in proposed_change:
            raise ValueError("Possible API key detected in proposed change.")
        if re.search(r"(\bpassword\b|\bsecret\b|\btoken\b|\bapi_key\b)\s*=\s*['\"][a-zA-Z0-9_\-\+]{15,}['\"]", lower):
            raise ValueError("Possible hardcoded secret detected in proposed change.")
        if re.search(r"(subprocess\.run|os\.system|shell=true|\bbash\b\s+-c)", lower):
            raise ValueError("Arbitrary shell execution detected in proposed change.")

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _get_repo(self, project_id: int, repository_id: int) -> Repository | None:
        return (
            self.db.query(Repository)
            .filter(
                Repository.id == repository_id,
                Repository.project_id == project_id,
            )
            .first()
        )

    def _get_file(self, repository_id: int, file_path: str) -> File | None:
        return (
            self.db.query(File)
            .filter(
                File.repository_id == repository_id,
                File.path == file_path,
            )
            .first()
        )

    def _write_audit(
        self,
        plan_id: str,
        project_id: int,
        repository_id: int,
        user_request: str,
        plan_summary: str,
        target_files: list[str],
        status: str,
    ) -> None:
        try:
            record = ChangeAuditLog(
                plan_id=plan_id,
                project_id=project_id,
                repository_id=repository_id,
                user_request=user_request[:2000],   # cap length; no secrets
                plan_summary=plan_summary[:2000],
                target_files=json.dumps(target_files),
                status=status,
            )
            self.db.add(record)
            self.db.commit()
        except Exception:
            logger.exception("Failed to write audit log for plan %s", plan_id)
            self.db.rollback()

    def _update_audit(
        self, plan_id: str, status: str, error: str | None = None
    ) -> None:
        try:
            record = (
                self.db.query(ChangeAuditLog)
                .filter(ChangeAuditLog.plan_id == plan_id)
                .first()
            )
            if record:
                record.status = status
                if error:
                    record.error = error[:1000]
                self.db.commit()
        except Exception:
            logger.exception("Failed to update audit log for plan %s", plan_id)
            self.db.rollback()
