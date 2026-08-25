"""
projects.py  — API
==================
CRUD endpoints for Projects.
The frontend needs these to list/create projects.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.repository import Repository
from app.models.file import File

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


@router.post("", status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.id.desc()).all()
    result = []
    for p in projects:
        repos = db.query(Repository).filter(Repository.project_id == p.id).all()
        repo_data = []
        for r in repos:
            file_count = db.query(File).filter(File.repository_id == r.id).count()
            repo_data.append({
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
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
            "repositories": repo_data,
        })
    return result


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    repos = db.query(Repository).filter(Repository.project_id == project_id).all()
    repo_data = []
    for r in repos:
        file_count = db.query(File).filter(File.repository_id == r.id).count()
        repo_data.append({
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
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "repositories": repo_data,
    }
