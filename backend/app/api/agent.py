"""
agent.py  — API
===============
POST /api/agent        – Developer Agent  (analyze, explain, plan, find bugs)
POST /api/agent/plan   – Generate a change plan with unified diff
POST /api/agent/apply  – Apply an approved plan
POST /api/agent/test   – Run controlled tests after apply
POST /api/agent/branch – Create a Git branch
POST /api/agent/commit – Stage, verify, commit approved changes
POST /api/agent/push   – Push branch to remote
POST /api/agent/pr     – Create GitHub pull request
POST /api/agent/execute – End-to-end workflow (plan only until approved)
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.change_audit import ChangeAuditLog
from app.models.repository import Repository
from app.services.agent import DeveloperAgent
from app.services.architecture import ArchitectureService
from app.services.code_modifier import CodeModifier, _PENDING_PLANS
from app.services.github import GitHubService
from app.services.git import GitService, validate_branch_name
from app.services.llm import LLMService
from app.services.test_runner import TestRunner

router = APIRouter(prefix="/api/agent", tags=["Developer Agent"])


# ── /api/agent ─────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    project_id: int
    repository_id: int
    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=20)


@router.post("")
def agent_query(data: AgentRequest, db: Session = Depends(get_db)):
    agent = DeveloperAgent(db)
    result = agent.run(
        project_id=data.project_id,
        repository_id=data.repository_id,
        query=data.query,
        limit=data.limit,
    )
    if "error" in result and result.get("intent") == "EXPLAIN":
        # Only raise HTTP error for hard errors (not found etc.)
        pass
    return result


# ── /api/agent/plan ─────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    project_id: int
    repository_id: int
    query: str = Field(min_length=1)


@router.post("/plan")
def generate_plan(data: PlanRequest, db: Session = Depends(get_db)):
    """
    Generate a change plan with unified diff.
    Does NOT apply any changes.
    """
    agent = DeveloperAgent(db)

    # Force PLAN_CHANGE intent
    from app.services.agent import classify_intent
    intent = classify_intent(data.query)

    result = agent.run(
        project_id=data.project_id,
        repository_id=data.repository_id,
        query=data.query,
        limit=8,
    )

    analysis = result.get("analysis", "")
    
    proposed_changes = []
    plan_steps = result.get("plan", {}).get("steps", [])
    for step in plan_steps:
        if step.get("file"):
            proposed_changes.append({
                "file": step.get("file"),
                "start_line": step.get("start_line"),
                "end_line": step.get("end_line"),
                "reason": step.get("reason", "Identified by Developer Agent"),
                "proposed_change": step.get("proposed_change", ""),
            })

    if not proposed_changes:
        return {
            "plan_id": None,
            "summary": analysis,
            "changes": [],
            "tests": result.get("plan", {}).get("tests", []) if "plan" in result else [],
            "risks": [],
            "message": "No specific files identified for modification. Review the analysis to determine changes manually.",
            "sources": result.get("sources", []),
        }

    modifier = CodeModifier(db)
    try:
        plan = modifier.create_plan(
            project_id=data.project_id,
            repository_id=data.repository_id,
            user_request=data.query,
            summary=analysis[:500],
            proposed_changes=proposed_changes,
            tests=result.get("plan", {}).get("tests", []) if "plan" in result else [],
            risks=[],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    plan["sources"] = result.get("sources", [])
    plan["full_analysis"] = analysis
    return plan


# ── /api/agent/apply ────────────────────────────────────────────────────────

class ApplyRequest(BaseModel):
    plan_id: str
    approved: bool


@router.post("/apply")
def apply_plan(data: ApplyRequest, db: Session = Depends(get_db)):
    """Apply or reject a pending plan. Requires explicit approved=true."""
    modifier = CodeModifier(db)
    try:
        result = modifier.apply_plan(plan_id=data.plan_id, approved=data.approved)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return result


# ── /api/agent/test ─────────────────────────────────────────────────────────

class TestRequest(BaseModel):
    plan_id: str
    project_id: int
    repository_id: int
    workspace_path: str = Field(
        description="Absolute path to the local repository checkout"
    )
    timeout: int = Field(default=300, ge=10, le=600)


@router.post("/test")
def run_tests(data: TestRequest, db: Session = Depends(get_db)):
    """Run controlled tests after an approved plan has been applied."""
    runner = TestRunner(db)
    result = runner.run(
        plan_id=data.plan_id,
        project_id=data.project_id,
        repository_id=data.repository_id,
        workspace_path=data.workspace_path,
        timeout=data.timeout,
    )
    if result["status"] == "blocked":
        raise HTTPException(status_code=403, detail=result.get("error", "Blocked"))

    if result["status"] == "failed":
        # AI FAILURE ANALYSIS
        agent = DeveloperAgent(db)
        fail_context = (
            f"The recently applied changes caused test failures in {result.get('framework')}.\n"
            f"Command: {result.get('command')}\n"
            f"Stdout: {result.get('stdout', '')[:2000]}\n"
            f"Stderr: {result.get('stderr', '')[:2000]}\n"
        )
        # We can force the LLM into generating debug analysis
        analysis_result = agent.run(
            project_id=data.project_id,
            repository_id=data.repository_id,
            query=f"Analyze this test failure:\n{fail_context}",
            limit=5,
        )
        
        result["analysis"] = analysis_result.get("analysis", "")
        result["likely_causes"] = [
            f.get("title", f.get("description", "")) 
            for f in analysis_result.get("findings", [])
        ][:5]
        result["recommendations"] = analysis_result.get("recommendations", [])
        # 'recommendations' could contain the JSON steps if it mistakenly thought PLAN_CHANGE, 
        # but the query should trigger DEBUG or ANALYZE intent.
        
        if not isinstance(result["recommendations"], list) or (
            result["recommendations"] and isinstance(result["recommendations"][0], dict)
        ):
            # Fallback if it structured it as a plan
            result["recommendations"] = ["Review the analysis text above for manual fixes."]
            
        result["sources"] = analysis_result.get("sources", [])

    return result


# ── /api/agent/branch ───────────────────────────────────────────────────────

class BranchRequest(BaseModel):
    plan_id: str
    workspace_path: str
    branch_name: str | None = None


@router.post("/branch")
def create_branch(data: BranchRequest, db: Session = Depends(get_db)):
    # Verify plan exists
    plan = _PENDING_PLANS.get(data.plan_id)
    audit = (
        db.query(ChangeAuditLog)
        .filter(ChangeAuditLog.plan_id == data.plan_id)
        .first()
    )
    if not plan and not audit:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Auto-generate branch name if not provided
    branch_name = data.branch_name
    if not branch_name:
        user_req = (audit.user_request if audit else "change")[:40]
        slug = re.sub(r"[^a-z0-9]+", "-", user_req.lower()).strip("-")
        branch_name = f"devos/{slug}"

    try:
        validate_branch_name(branch_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    git = GitService()
    try:
        result = git.create_branch(workspace=data.workspace_path, branch_name=branch_name)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Update audit log
    if audit:
        audit.branch_name = branch_name
        db.commit()

    return result


# ── /api/agent/commit ───────────────────────────────────────────────────────

class CommitRequest(BaseModel):
    plan_id: str
    workspace_path: str
    branch_name: str
    commit_message: str
    test_first: bool = True


@router.post("/commit")
def commit_changes(data: CommitRequest, db: Session = Depends(get_db)):
    audit = (
        db.query(ChangeAuditLog)
        .filter(ChangeAuditLog.plan_id == data.plan_id)
        .first()
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Plan not found in audit log")
    if audit.status != "applied":
        raise HTTPException(
            status_code=403,
            detail=f"Cannot commit: plan status is '{audit.status}'. Apply first.",
        )

    import json
    approved_files: list[str] = json.loads(audit.target_files or "[]")

    git = GitService()

    # Verify only approved files changed
    if not git.verify_only_approved_changed(data.workspace_path, approved_files):
        raise HTTPException(
            status_code=422,
            detail="Unapproved files detected in working tree. Aborting commit.",
        )

    # Optional: run tests first
    test_result = None
    if data.test_first:
        runner = TestRunner(db)
        test_result = runner.run(
            plan_id=data.plan_id,
            project_id=audit.project_id,
            repository_id=audit.repository_id,
            workspace_path=data.workspace_path,
        )
        if test_result["status"] == "failed":
            raise HTTPException(
                status_code=422,
                detail=f"Tests failed. Commit blocked. Exit code: {test_result.get('exit_code')}",
            )

    try:
        stage = git.stage_files(data.workspace_path, approved_files)
        commit = git.commit(data.workspace_path, data.commit_message)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Update audit
    audit.commit_sha = commit["commit_sha"]
    db.commit()

    return {
        "status": "committed",
        "branch": data.branch_name,
        "commit_sha": commit["commit_sha"],
        "staged_files": stage["staged"],
        "tests": test_result,
        "changed_files": approved_files,
    }


# ── /api/agent/push ─────────────────────────────────────────────────────────

class PushRequest(BaseModel):
    plan_id: str
    workspace_path: str
    branch_name: str
    remote: str = "origin"


@router.post("/push")
def push_branch(data: PushRequest, db: Session = Depends(get_db)):
    audit = (
        db.query(ChangeAuditLog)
        .filter(ChangeAuditLog.plan_id == data.plan_id)
        .first()
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not audit.commit_sha:
        raise HTTPException(status_code=403, detail="No commit found for this plan. Commit first.")

    try:
        validate_branch_name(data.branch_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    git = GitService()
    try:
        result = git.push(
            workspace=data.workspace_path,
            branch_name=data.branch_name,
            remote=data.remote,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    audit.push_status = "pushed"
    audit.branch_name = data.branch_name
    db.commit()

    return result


# ── /api/agent/pr ───────────────────────────────────────────────────────────

class PRRequest(BaseModel):
    plan_id: str
    project_id: int
    repository_id: int
    branch_name: str
    title: str
    description: str = ""


@router.post("/pr")
async def create_pr(data: PRRequest, db: Session = Depends(get_db)):
    audit = (
        db.query(ChangeAuditLog)
        .filter(ChangeAuditLog.plan_id == data.plan_id)
        .first()
    )
    if not audit:
        raise HTTPException(status_code=404, detail="Plan not found")
    if audit.push_status != "pushed":
        raise HTTPException(status_code=403, detail="Branch has not been pushed yet.")

    repo = (
        db.query(Repository)
        .filter(
            Repository.id == data.repository_id,
            Repository.project_id == data.project_id,
        )
        .first()
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        validate_branch_name(data.branch_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    github = GitHubService()
    try:
        pr = await github.create_pull_request(
            owner=repo.owner,
            repo=repo.name,
            title=data.title[:255],
            body=data.description[:65000],
            head=data.branch_name,
            base=repo.default_branch,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub PR creation failed: {exc}")

    audit.pr_number = pr.get("pr_number")
    audit.pr_url = pr.get("pr_url")
    db.commit()

    return {
        "status": "created",
        "plan_id": data.plan_id,
        "branch": data.branch_name,
        "commit_sha": audit.commit_sha,
        **pr,
    }


# ── /api/agent/execute ──────────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    project_id: int
    repository_id: int
    query: str = Field(min_length=1)
    approved: bool = False


@router.post("/execute")
def execute_workflow(data: ExecuteRequest, db: Session = Depends(get_db)):
    """
    High-level endpoint.

    approved=false  → returns analysis + plan only. NO modification.
    approved=true   → generates plan AND records it as pending approval.
                      Caller must then explicitly call /apply, /test, /commit, /push, /pr.

    IMPORTANT: Natural-language "yes" from the LLM is never treated as approval.
    Only the explicit approved=True boolean from the API caller counts.
    """
    agent = DeveloperAgent(db)
    result = agent.run(
        project_id=data.project_id,
        repository_id=data.repository_id,
        query=data.query,
        limit=8,
    )

    if not data.approved:
        return {
            "status": "plan_ready",
            "approved": False,
            "message": "Review the plan and re-submit with approved=true to proceed.",
            "query": data.query,
            "intent": result.get("intent"),
            "analysis": result.get("analysis"),
            "plan": result.get("plan"),
            "sources": result.get("sources", []),
        }

    # With approved=True: persist a plan record (still requires /apply call)
    modifier = CodeModifier(db)
    from app.models.file import File
    recommended_files = [
        s["file_path"] for s in result.get("sources", []) if s.get("file_path")
    ][:5]

    proposed_changes = []
    for fp in recommended_files:
        f = db.query(File).filter(
            File.repository_id == data.repository_id, File.path == fp
        ).first()
        if f and f.content:
            proposed_changes.append({
                "file": fp,
                "start_line": None,
                "end_line": None,
                "reason": f"Identified by agent for: {data.query[:100]}",
                "proposed_change": f.content,
            })

    if not proposed_changes:
        return {
            "status": "no_changes",
            "message": "No specific files identified for modification.",
            "analysis": result.get("analysis"),
        }

    plan = modifier.create_plan(
        project_id=data.project_id,
        repository_id=data.repository_id,
        user_request=data.query,
        summary=result.get("analysis", "")[:500],
        proposed_changes=proposed_changes,
    )

    return {
        "status": "plan_created",
        "approved": True,
        "message": "Plan created. Call POST /api/agent/apply with approved=true to apply changes.",
        "plan_id": plan["plan_id"],
        "plan": plan,
        "analysis": result.get("analysis"),
        "sources": result.get("sources", []),
    }
