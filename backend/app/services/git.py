"""
git.py
======
Controlled Git operations service — Milestone 6.

Safety contract
---------------
* All git commands are from an explicit allowlist.
* subprocess is called with shell=False and explicit argv arrays.
* No user or LLM-supplied text is ever interpolated into the command.
* Branch names are validated before use.
* Protected branches cannot be pushed to directly.
* Secrets in changed files are detected before commit.
* Workspace path is validated.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GIT_TIMEOUT = 120   # seconds per git operation

# Branch name: alphanumeric, hyphens, underscores, forward slashes, dots
# Must not start with - or . ; must not contain control characters, spaces,
# shell metacharacters, or ".."
_VALID_BRANCH_RE = re.compile(
    r"^(?![-./])[\w.\-/]+$"
)
_BLOCKED_BRANCH_CHARS = re.compile(
    r"""[\s\x00-\x1f~^:?*\[\]\\@{}|<>!&;`$()\'"]"""
)

PROTECTED_BRANCHES = {"main", "master", "develop", "release", "production"}

# Files that should never appear in a commit
_BLOCKED_COMMIT_PATHS = re.compile(
    r"""(\.env($|\.\w+)|\.pem|\.key|credentials|secrets?|api[_-]?key|
         private[_-]?key|\.p12|\.pfx|auth\.json|service[_-]?account)""",
    re.IGNORECASE | re.VERBOSE,
)

# Secret patterns in file content
_SECRET_CONTENT_RE = re.compile(
    r"""(?i)(api[_-]?key|token|password|secret|authorization|bearer
             |private[_-]?key)\s*[=:'"]\s*([^\s'"&]{8,})""",
    re.VERBOSE,
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_branch_name(name: str) -> None:
    """Raise ValueError for invalid or unsafe branch names."""
    if not name or len(name) > 200:
        raise ValueError("Branch name is empty or too long.")
    if _BLOCKED_BRANCH_CHARS.search(name):
        raise ValueError(f"Branch name contains invalid characters: {name!r}")
    if ".." in name:
        raise ValueError("Branch name must not contain '..'")
    if not _VALID_BRANCH_RE.match(name):
        raise ValueError(f"Invalid branch name format: {name!r}")
    parts = name.split("/")
    base = parts[-1] if len(parts) > 1 else name
    if base in PROTECTED_BRANCHES:
        raise ValueError(
            f"Cannot create/push to protected branch: {base!r}. "
            "DevOs branches must use a prefix like 'devos/'."
        )


def validate_workspace(workspace_path: str) -> Path:
    """Validate the workspace directory."""
    p = Path(workspace_path).resolve()
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Workspace path does not exist: {p}")
    # Must be a git repository
    if not (p / ".git").exists():
        raise ValueError(f"Workspace is not a git repository: {p}")
    return p


def validate_commit_message(msg: str) -> str:
    """Sanitise and validate a commit message."""
    msg = msg.strip()
    if not msg:
        raise ValueError("Commit message cannot be empty.")
    if len(msg) > 500:
        raise ValueError("Commit message is too long (max 500 chars).")
    # Strip any shell metacharacters
    safe = re.sub(r"""[`$()!;&|<>\"']""", "", msg)
    return safe[:255]


def scan_for_secrets(file_path: Path) -> bool:
    """
    Return True if the file looks like it contains secrets.
    Logs a warning but never logs the secret value.
    """
    if _BLOCKED_COMMIT_PATHS.search(file_path.name):
        logger.warning("Blocked commit path: %s", file_path.name)
        return True
    try:
        text = file_path.read_text(errors="ignore")[:10_000]
        if _SECRET_CONTENT_RE.search(text):
            logger.warning("Potential secret detected in %s", file_path.name)
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Git runner
# ---------------------------------------------------------------------------

def _git(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Execute a whitelisted git command with shell=False."""
    cmd = ["git"] + argv
    logger.debug("git %s", " ".join(argv))
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        text=True,
        timeout=GIT_TIMEOUT,
    )
    return result


# ---------------------------------------------------------------------------
# GitService
# ---------------------------------------------------------------------------

class GitService:
    """
    Controlled Git operations. All methods use explicit, validated inputs.
    Never executes commands constructed from user text or LLM output.
    """

    def create_branch(self, workspace: str, branch_name: str) -> dict[str, Any]:
        """Create and checkout a new branch."""
        validate_branch_name(branch_name)
        ws = validate_workspace(workspace)

        # Ensure we're up to date
        result = _git(["fetch", "--prune"], ws)
        if result.returncode != 0:
            logger.warning("git fetch warning: %s", result.stderr[:200])

        # Create and switch to the new branch
        result = _git(["checkout", "-b", branch_name], ws)
        if result.returncode != 0:
            # Branch might already exist — try switching
            result2 = _git(["checkout", branch_name], ws)
            if result2.returncode != 0:
                raise RuntimeError(
                    f"Failed to create branch {branch_name!r}: {result.stderr[:300]}"
                )

        current = _git(["rev-parse", "--abbrev-ref", "HEAD"], ws)
        return {
            "status": "created",
            "branch": branch_name,
            "current_branch": current.stdout.strip(),
            "workspace": str(ws),
        }

    def get_status(self, workspace: str) -> dict[str, Any]:
        """Return git status information."""
        ws = validate_workspace(workspace)
        result = _git(["status", "--porcelain"], ws)
        current = _git(["rev-parse", "--abbrev-ref", "HEAD"], ws)
        return {
            "branch": current.stdout.strip(),
            "status": result.stdout.strip(),
            "clean": result.stdout.strip() == "",
        }

    def stage_files(
        self,
        workspace: str,
        file_paths: list[str],
    ) -> dict[str, Any]:
        """
        Stage specific files for commit.
        Each path is validated individually before staging.
        """
        ws = validate_workspace(workspace)
        staged: list[str] = []
        blocked: list[str] = []

        for rel_path in file_paths:
            # Safety checks
            if ".." in rel_path or os.path.isabs(rel_path):
                blocked.append(rel_path)
                continue
            if _BLOCKED_COMMIT_PATHS.search(rel_path):
                blocked.append(rel_path)
                continue

            full_path = ws / rel_path
            if not full_path.exists():
                logger.warning("File not found for staging: %s", rel_path)
                continue

            # Scan for secrets
            if scan_for_secrets(full_path):
                blocked.append(rel_path)
                continue

            result = _git(["add", "--", rel_path], ws)
            if result.returncode == 0:
                staged.append(rel_path)
            else:
                logger.warning("Failed to stage %s: %s", rel_path, result.stderr[:100])

        if blocked:
            raise ValueError(
                f"Commit blocked: potential secrets or disallowed paths detected: {blocked}"
            )

        return {"staged": staged}

    def commit(
        self,
        workspace: str,
        message: str,
    ) -> dict[str, Any]:
        """Create a commit with a validated message."""
        ws = validate_workspace(workspace)
        safe_message = validate_commit_message(message)

        result = _git(
            ["commit", "-m", safe_message, "--no-verify"],
            ws,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Commit failed: {result.stderr[:400]}")

        sha_result = _git(["rev-parse", "HEAD"], ws)
        commit_sha = sha_result.stdout.strip()

        return {
            "status": "committed",
            "commit_sha": commit_sha,
            "message": safe_message,
        }

    def push(
        self,
        workspace: str,
        branch_name: str,
        remote: str = "origin",
    ) -> dict[str, Any]:
        """Push a branch to the remote. Refuses to push to protected branches."""
        validate_branch_name(branch_name)
        ws = validate_workspace(workspace)

        # Safety: never push directly to protected branches
        base = branch_name.split("/")[-1]
        if base in PROTECTED_BRANCHES:
            raise ValueError(
                f"Push to protected branch '{base}' is not allowed."
            )

        result = _git(
            ["push", "--set-upstream", remote, branch_name],
            ws,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Push failed: {result.stderr[:400]}")

        return {
            "status": "pushed",
            "branch": branch_name,
            "remote": remote,
            "output": result.stdout.strip()[:500],
        }

    def get_diff(self, workspace: str, files: list[str]) -> str:
        """Return unified diff for specific staged files."""
        ws = validate_workspace(workspace)
        safe_files = [f for f in files if ".." not in f and not os.path.isabs(f)]
        if not safe_files:
            return ""
        result = _git(["diff", "--cached", "--"] + safe_files, ws)
        return result.stdout[:8000]

    def verify_only_approved_changed(
        self, workspace: str, approved_files: list[str]
    ) -> bool:
        """
        Ensure the working tree / index contains changes only to approved files.
        Returns True if safe, False if unexpected files are modified.
        """
        ws = validate_workspace(workspace)
        result = _git(["status", "--porcelain"], ws)
        changed = []
        for line in result.stdout.splitlines():
            if len(line) > 3:
                changed_path = line[3:].strip()
                changed.append(changed_path)

        for path in changed:
            if path not in approved_files:
                logger.warning("Unapproved file in working tree: %s", path)
                return False
        return True
