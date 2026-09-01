import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, ProjectMembership, RoleEnum


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def require_project_role(required_roles: list[RoleEnum]):
    """
    Dependency factory to check if the current user has a sufficient role in a given project_id.
    Relies on `project_id` being present in path or request body, but for path params we can extract it.
    Since path varies, we will inject a smaller dependency in the router functions themselves, or parse here.
    Actually, to keep it simple and explicit, we'll implement explicit checks in the router rather than complex
    class-based dependency factories, because projects router receives project_id dynamically.
    """
    def _require_project_role_dep(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        membership = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == current_user.id
        ).first()

        if not membership:
            raise HTTPException(status_code=403, detail="You do not have access to this project.")
        
        if membership.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges.")
            
        return membership

    return _require_project_role_dep


# Quick helpers for explicit role checking inside route logic:
def verify_project_access(db: Session, user_id: int, project_id: int, allowed_roles: list[RoleEnum] = None):
    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="You do not have access to this project.")
    
    if allowed_roles and membership.role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Requires one of roles: {[r.name for r in allowed_roles]}")

    return membership
