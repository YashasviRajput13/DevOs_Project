from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search import CodeSearchService


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


from app.models.user import User
from app.services.auth import get_current_user, verify_project_access

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    project_id: int | None = None


@router.post("")
def search_code(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.project_id:
        verify_project_access(db, current_user.id, data.project_id)

    service = CodeSearchService(db)

    # Note: CodeSearchService might also need updating to filter by project_id, 
    # but at the very least we verify the user has access to this project before executing.
    results = service.search(
        query=data.query,
        limit=data.limit,
        project_id=data.project_id
    )

    return {
        "query": data.query,
        "results": results,
    }