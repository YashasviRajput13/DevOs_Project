from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    extension: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    language: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    sha: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME,
        default=_utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False
    )

    repository = relationship(
        "Repository",
        back_populates="files"
    )

    chunks = relationship(
    "CodeChunk",
    back_populates="file",
    cascade="all, delete-orphan"
)