from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    embedding: Mapped[list[float] | None] = mapped_column(
    JSON,
    nullable=True
)

    created_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME,
        default=_utcnow,
        nullable=False
    )

    file = relationship(
        "File",
        back_populates="chunks"
    )