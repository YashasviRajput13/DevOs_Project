"""
repositories.py  — API  (updated)
==================================
Endpoints for repository management plus:
  GET  /overview
  GET  /architecture
  GET  /files
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.file import File
from app.models.project import Project
from app.models.repository import Repository
from app.services.architecture import ArchitectureService
from app.services.indexer import RepositoryIndexer
from app.services.overview import RepositoryOverviewService

router = APIRouter(prefix="/api/projects", tags=["Repositories"])


class RepositoryCreate(BaseModel):
    url: HttpUrl


# ── List repositories ──────────────────────────────────────────────────────

@router.get("/{project_id}/repositories")
def list_repositories(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repos = db.query(Repository).filter(Repository.project_id == project_id).all()
    result = []
    for r in repos:
        file_count = db.query(File).filter(File.repository_id == r.id).count()
        result.append({
            "id": r.id,
            "name": r.name,
            "full_name": r.full_name,
            "url": r.url,
            "provider": r.provider,
            "default_branch": r.default_branch,
            "last_indexed_commit": r.last_indexed_commit,
            "files_count": file_count,
            "indexed": file_count > 0,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        })
    return result


# ── Add repository ─────────────────────────────────────────────────────────

@router.post("/{project_id}/repositories", status_code=201)
def add_repository(
    project_id: int,
    data: RepositoryCreate,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    github_url = str(data.url).rstrip("/")
    parts = github_url.split("/")

    if len(parts) < 2 or "github.com" not in github_url:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    owner = parts[-2]
    name = parts[-1]

    # Prevent duplicates within same project
    existing = (
        db.query(Repository)
        .filter(
            Repository.project_id == project_id,
            Repository.full_name == f"{owner}/{name}",
        )
        .first()
    )
    if existing:
        file_count = db.query(File).filter(File.repository_id == existing.id).count()
        return {
            "id": existing.id,
            "name": existing.name,
            "full_name": existing.full_name,
            "url": existing.url,
            "provider": existing.provider,
            "default_branch": existing.default_branch,
            "files_count": file_count,
            "indexed": file_count > 0,
        }

    repository = Repository(
        project_id=project_id,
        provider="github",
        owner=owner,
        name=name,
        full_name=f"{owner}/{name}",
        url=github_url,
        default_branch="main",
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)

    return {
        "id": repository.id,
        "name": repository.name,
        "full_name": repository.full_name,
        "url": repository.url,
        "provider": repository.provider,
        "default_branch": repository.default_branch,
        "files_count": 0,
        "indexed": False,
        "created_at": repository.created_at.isoformat(),
        "updated_at": repository.updated_at.isoformat(),
    }


# ── Index repository ───────────────────────────────────────────────────────

@router.post("/{project_id}/repositories/{repository_id}/index")
async def index_repository(
    project_id: int,
    repository_id: int,
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.project_id == project_id,
        )
        .first()
    )
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    indexer = RepositoryIndexer(db)
    result = await indexer.index_repository(repository)
    return result


# ── Repository files ───────────────────────────────────────────────────────

@router.get("/{project_id}/repositories/{repository_id}/files")
def list_files(
    project_id: int,
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.project_id == project_id,
        )
        .first()
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    files = (
        db.query(File).filter(File.repository_id == repository_id).all()
    )
    return {
        "repository_id": repository_id,
        "files": [
            {
                "id": f.id,
                "path": f.path,
                "name": f.name,
                "language": f.language,
                "extension": f.extension,
                "size": f.size,
            }
            for f in files
        ],
    }


# ── File content ────────────────────────────────────────────────────────────

@router.get("/{project_id}/repositories/{repository_id}/files/{file_id}")
def get_file_content(
    project_id: int,
    repository_id: int,
    file_id: int,
    db: Session = Depends(get_db),
):
    repo = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.project_id == project_id,
        )
        .first()
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    file = (
        db.query(File)
        .filter(File.id == file_id, File.repository_id == repository_id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": file.id,
        "path": file.path,
        "name": file.name,
        "language": file.language,
        "extension": file.extension,
        "size": file.size,
        "content": file.content or "",
    }


# ── Overview ────────────────────────────────────────────────────────────────

@router.get("/{project_id}/repositories/{repository_id}/overview")
def repository_overview(
    project_id: int,
    repository_id: int,
    db: Session = Depends(get_db),
):
    svc = RepositoryOverviewService(db)
    try:
        overview = svc.get_overview(project_id, repository_id)
    except ValueError as exc:
        msg = str(exc)
        if msg == "repository_not_found":
            raise HTTPException(status_code=404, detail="Repository not found")
        if msg == "repository_not_indexed":
            raise HTTPException(
                status_code=422,
                detail="Repository has not been indexed yet. "
                       "Run POST /index first.",
            )
        raise HTTPException(status_code=422, detail=msg)
    return overview


# ── Architecture ────────────────────────────────────────────────────────────

@router.get("/{project_id}/repositories/{repository_id}/architecture")
def repository_architecture(
    project_id: int,
    repository_id: int,
    db: Session = Depends(get_db),
):
    svc = ArchitectureService(db)
    try:
        arch = svc.get_architecture(project_id, repository_id)
    except ValueError as exc:
        msg = str(exc)
        if msg == "repository_not_found":
            raise HTTPException(status_code=404, detail="Repository not found")
        if msg == "repository_not_indexed":
            raise HTTPException(
                status_code=422,
                detail="Repository has not been indexed yet.",
            )
        raise HTTPException(status_code=422, detail=msg)
    return arch