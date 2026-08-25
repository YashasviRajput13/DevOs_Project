"""
dependency.py
=============
Stores code-level relationships extracted from repository files.
Populated by CodeAnalyzer during indexing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class CodeDependency(Base):
    __tablename__ = "code_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The file that declares the dependency
    source_file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The file being depended on (nullable — may be external)
    target_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Raw module/package string (e.g. "app.services.indexer")
    target_module: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # import | function | class | api_route | model_reference
    dependency_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional: function name, class name, route path, etc.
    symbol_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Line number in source file where the dependency was detected
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME, default=_utcnow, nullable=False
    )

    # Relationships
    repository = relationship("Repository")
    source_file = relationship("File", foreign_keys=[source_file_id])
    target_file = relationship("File", foreign_keys=[target_file_id])
