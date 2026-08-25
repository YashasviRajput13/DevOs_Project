from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        default="github",
        nullable=False
    )

    owner: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    default_branch: Mapped[str] = mapped_column(
        String(255),
        default="main",
        nullable=False
    )

    last_indexed_commit: Mapped[str | None] = mapped_column(
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

    project = relationship(
        "Project",
        back_populates="repositories"
    )

    files = relationship(
    "File",
    back_populates="repository",
    cascade="all, delete-orphan"
)