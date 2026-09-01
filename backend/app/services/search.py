"""
search.py (cleaned)
===================
Semantic code search over indexed CodeChunk records.
"""
import logging

import numpy as np
from sqlalchemy.orm import Session, joinedload

from app.models.chunk import CodeChunk
from app.models.file import File
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class CodeSearchService:

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def search(self, query: str, limit: int = 5, project_id: int | None = None) -> list[dict]:
        """
        Semantically search code chunks.

        Returns dicts enriched with File and Repository metadata:
            repository_name, repository_full_name, repository_url,
            file_path, file_name, language,
            content, start_line, end_line, score
        """
        logger.debug("Search query: %r (limit=%d)", query, limit)

        query_embedding = np.asarray(
            self.embedding_service.embed_text(query),
            dtype=np.float32,
        )

        base_query = (
            self.db.query(CodeChunk)
            .join(File, CodeChunk.file_id == File.id)
            .join(File.repository)
            .options(joinedload(CodeChunk.file).joinedload(File.repository))
            .filter(CodeChunk.embedding.isnot(None))
        )
        
        if project_id is not None:
             # We rely on File.repository joining already to `repositories` mapped naturally via SQLAlchemy relationships
             from app.models.repository import Repository
             base_query = base_query.filter(Repository.project_id == project_id)

        chunks = base_query.all()

        results = []
        for chunk in chunks:
            embedding = np.asarray(chunk.embedding, dtype=np.float32)
            if embedding.size == 0:
                continue

            score = float(np.dot(query_embedding, embedding))

            file_obj = chunk.file
            repo_obj = file_obj.repository if file_obj else None

            results.append({
                "chunk_id": chunk.id,
                "file_id": chunk.file_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "score": score,
                "repository_id": repo_obj.id if repo_obj else None,
                "repository_name": repo_obj.name if repo_obj else None,
                "repository_full_name": repo_obj.full_name if repo_obj else None,
                "repository_url": repo_obj.url if repo_obj else None,
                "file_path": file_obj.path if file_obj else None,
                "file_name": file_obj.name if file_obj else None,
                "language": file_obj.language if file_obj else None,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        top = results[:limit]
        logger.debug("Search returned %d results.", len(top))
        return top