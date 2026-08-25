"""
change_audit.py  (updated)
==========================
Audit log for Developer Agent change plans, including Git workflow tracking.
Never stores API keys, secrets, or tokens.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class ChangeAuditLog(Base):
    __tablename__ = "change_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plan_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, unique=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The original user request (no secrets logged)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON-serialized plan summary
    plan_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON-serialized list of target file paths
    target_files: Mapped[str | None] = mapped_column(Text, nullable=True)

    # pending | approved | rejected | applied | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Error message if application failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Git workflow fields ─────────────────────────────────────────
    branch_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    push_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME, default=_utcnow, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME, default=_utcnow, onupdate=_utcnow, nullable=False
    )
