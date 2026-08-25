from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search import CodeSearchService


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("")
def search_code(
    data: SearchRequest,
    db: Session = Depends(get_db),
):
    service = CodeSearchService(db)

    results = service.search(
        query=data.query,
        limit=data.limit,
    )

    return {
        "query": data.query,
        "results": results,
    }