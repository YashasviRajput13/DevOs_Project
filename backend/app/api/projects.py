"""
projects.py  — API
==================
CRUD endpoints for Projects with multi-tenant access control.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.repository import Repository
from app.models.file import File
from app.models.user import User, ProjectMembership, RoleEnum
from app.services.auth import get_current_user, verify_project_access

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


@router.post("", status_code=201)
def create_project(data: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = Project(name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Assign OWNER role context immediately
    membership = ProjectMembership(
        user_id=current_user.id,
        project_id=project.id,
        role=RoleEnum.OWNER
    )
    db.add(membership)
    db.commit()

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "role": membership.role.value if hasattr(membership.role, "value") else membership.role
    }


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(db, current_user.id, project_id, [RoleEnum.OWNER])
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None


@router.get("")
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Returns only projects where the user is a valid member
    memberships = db.query(ProjectMembership).filter(ProjectMembership.user_id == current_user.id).all()
    project_ids = [m.project_id for m in memberships]
    
    projects = db.query(Project).filter(Project.id.in_(project_ids)).order_by(Project.id.desc()).all()
    
    role_map = {m.project_id: (m.role.value if hasattr(m.role, "value") else m.role) for m in memberships}

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
            "role": role_map[p.id],
            "repositories": repo_data,
        })
    return result


@router.get("/{project_id}")
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = verify_project_access(db, current_user.id, project_id)

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
        "role": membership.role.value if hasattr(membership.role, "value") else membership.role,
        "repositories": repo_data,
    }


# ── Members & Invitations ───────────────────────────────────────────────────

import uuid
from datetime import datetime, timedelta
from app.models.user import ProjectInvitation

@router.get("/{project_id}/members")
def list_project_members(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(db, current_user.id, project_id)
    memberships = (
        db.query(ProjectMembership)
        .filter(ProjectMembership.project_id == project_id)
        .all()
    )
    result = []
    for m in memberships:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            result.append({
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": m.role.value if hasattr(m.role, "value") else m.role,
                "added_at": m.created_at.isoformat()
            })
    
    # Also fetch pending invitations if you are OWNER/ADMIN
    invitations = []
    try:
        verify_project_access(db, current_user.id, project_id, [RoleEnum.OWNER, RoleEnum.ADMIN])
        invites = db.query(ProjectInvitation).filter(ProjectInvitation.project_id == project_id, ProjectInvitation.status == "pending").all()
        for inv in invites:
            invitations.append({
                "id": inv.id,
                "token": inv.token,
                "role": inv.role.value if hasattr(inv.role, "value") else inv.role,
                "expires_at": inv.expires_at.isoformat()
            })
    except HTTPException:
        pass # Viewers/Members don't see pending invitations
        
    return {"members": result, "pending_invitations": invitations}

    
class InviteCreate(BaseModel):
    role: str = "MEMBER"

@router.post("/{project_id}/invitations", status_code=201)
def create_invitation(project_id: int, data: InviteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(db, current_user.id, project_id, [RoleEnum.OWNER, RoleEnum.ADMIN])
    
    if data.role not in [e.value for e in RoleEnum]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=7)
    
    inv = ProjectInvitation(
        project_id=project_id,
        created_by_id=current_user.id,
        token=token,
        role=RoleEnum(data.role),
        expires_at=expires
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {
        "id": inv.id,
        "token": inv.token,
        "role": inv.role.value if hasattr(inv.role, "value") else inv.role,
        "expires_at": inv.expires_at.isoformat()
    }


class InviteAccept(BaseModel):
    token: str

@router.post("/invitations/accept")
def accept_invitation(data: InviteAccept, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = db.query(ProjectInvitation).filter(ProjectInvitation.token == data.token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invalid invitation token")
    if inv.status != "pending" or inv.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired or already used")
        
    # Check if already in project
    existing = db.query(ProjectMembership).filter(ProjectMembership.project_id == inv.project_id, ProjectMembership.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already a member of this project")
        
    membership = ProjectMembership(
        user_id=current_user.id,
        project_id=inv.project_id,
        role=inv.role
    )
    db.add(membership)
    
    inv.status = "accepted"
    inv.accepted_by_id = current_user.id
    db.commit()
    
    return {"status": "success", "project_id": inv.project_id}
