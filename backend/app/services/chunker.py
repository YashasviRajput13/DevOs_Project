from sqlalchemy.orm import Session

from app.models.chunk import CodeChunk
from app.models.file import File
from app.services.embedding import EmbeddingService


class CodeChunker:

    def __init__(
        self,
        db: Session,
        chunk_size: int = 80,
        overlap: int = 10,
    ):
        self.db = db
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.embedding_service = EmbeddingService()

    def chunk_file(self, file: File) -> int:
        if not file.content:
            return 0

        self.db.query(CodeChunk).filter(
            CodeChunk.file_id == file.id
        ).delete(synchronize_session=False)

        lines = file.content.splitlines()

        if not lines:
            return 0

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(lines):
            end = min(
                start + self.chunk_size,
                len(lines)
            )

            content = "\n".join(lines[start:end])

            embedding = self.embedding_service.embed_text(
                content
            )

            chunk = CodeChunk(
                file_id=file.id,
                chunk_index=chunk_index,
                content=content,
                start_line=start + 1,
                end_line=end,
                token_count=self._estimate_tokens(content),
                embedding=embedding,
            )

            chunks.append(chunk)

            chunk_index += 1

            if end >= len(lines):
                break

            start = end - self.overlap

        self.db.add_all(chunks)

        return len(chunks)

    @staticmethod
    def _estimate_tokens(content: str) -> int:
        return max(1, len(content) // 4)