"""
test_execution.py
=================
Model for structured test execution results tied to a change plan.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_TZ_DATETIME = DateTime(timezone=True)


class TestExecutionLog(Base):
    __tablename__ = "test_execution_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plan_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
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

    # pytest | unittest | jest | vitest | not_available
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Space-separated test target(s), e.g. "tests/test_indexer.py"
    tests_selected: Mapped[str | None] = mapped_column(Text, nullable=True)

    # passed | failed | timeout | not_available | blocked | error
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    tests_run: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tests_failed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Truncated/redacted output (no secrets)
    stdout_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        _TZ_DATETIME, default=_utcnow, nullable=False
    )
